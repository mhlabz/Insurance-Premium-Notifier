from datetime import date, timedelta
import calendar
from database import get_db

def add_months(day, months):
    month=day.month-1+months; year=day.year+month//12; month=month%12+1
    return date(year,month,min(day.day,calendar.monthrange(year,month)[1]))

def calc_next_due(last_payment, frequency):
    if isinstance(last_payment,str): last_payment=date.fromisoformat(last_payment)
    if frequency=='monthly': return add_months(last_payment,1)
    if frequency=='yearly':
        try: return last_payment.replace(year=last_payment.year+1)
        except ValueError: return last_payment.replace(year=last_payment.year+1,day=28)
    raise ValueError('Frequency must be monthly or yearly.')

def status_for(due, grace_days, today=None):
    today=today or date.today(); due=date.fromisoformat(due) if isinstance(due,str) else due
    delta=(due-today).days; deadline=due+timedelta(days=int(grace_days))
    if delta>7: return 'Active'
    if delta>=0: return 'Due Soon'
    if today<=deadline: return 'Grace Period'
    return 'Lapsed'

def monitor(today=None):
    today=today or date.today(); checked=reminders=lapsed=0
    with get_db() as db:
        for p in db.execute('SELECT * FROM policies').fetchall():
            if p['paid_up']: continue
            checked+=1; due=date.fromisoformat(p['next_due_date']); status=status_for(due,p['grace_period'],today)
            db.execute('UPDATE policies SET status=? WHERE id=?',(status,p['id']))
            days=(due-today).days; deadline=due+timedelta(days=p['grace_period'])
            if status=='Due Soon':
                kind='due:'+due.isoformat(); message=f"Premium for policy {p['policy_number']} is due on {due.isoformat()} ({days} day(s))."
            elif status=='Grace Period':
                kind='grace:'+due.isoformat(); message=f"Premium for policy {p['policy_number']} is overdue. Grace deadline: {deadline.isoformat()}."
            elif status=='Lapsed':
                kind='lapsed:'+due.isoformat(); message=f"Policy {p['policy_number']} is LAPSED. Grace period expired on {deadline.isoformat()}."; lapsed+=1
            else: continue
            cur=db.execute('INSERT OR IGNORE INTO notifications(policy_id,message,kind,created_at) VALUES(?,?,?,?)',(p['id'],message,kind,today.isoformat()))
            reminders+=cur.rowcount
    return {'checked':checked,'reminders':reminders,'lapsed':lapsed}
