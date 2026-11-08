from datetime import date
import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from database import init_db, get_db
from services import calc_next_due, monitor

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-before-deployment")
init_db()

@app.template_filter("money")
def money(value): return f"₹{float(value):,.2f}"

@app.context_processor
def inject_today(): return {"today": date.today()}

def fetch_policy(pid):
    with get_db() as db: row=db.execute("SELECT * FROM policies WHERE id=?", (pid,)).fetchone()
    if row is None: abort(404)
    return row

@app.get("/")
def dashboard():
    with get_db() as db:
        policies=db.execute("SELECT * FROM policies ORDER BY next_due_date LIMIT 8").fetchall()
        counts=db.execute("SELECT COUNT(*) total, SUM(status='Active') active, SUM(status='Due Soon') due_soon, SUM(status='Grace Period') grace, SUM(status='Lapsed') lapsed, SUM(paid_up=1) paid_up FROM policies").fetchone()
        notices=db.execute("SELECT n.*,p.policy_number FROM notifications n JOIN policies p ON p.id=n.policy_id ORDER BY n.id DESC LIMIT 6").fetchall()
    return render_template('dashboard.html', policies=policies, counts=counts, notices=notices)

@app.route('/policies/new', methods=['GET','POST'])
def create_policy():
    if request.method=='POST':
        try:
            d=request.form; number=d['policy_number'].strip(); name=d['customer_name'].strip()
            premium=float(d['premium_amount']); freq=d['frequency']; start=date.fromisoformat(d['start_date'])
            last=date.fromisoformat(d['last_payment_date']); grace=int(d['grace_period'])
            if not number or not name or premium<=0 or freq not in ('monthly','yearly') or grace<0: raise ValueError('Please provide valid policy details.')
            due=calc_next_due(last,freq)
            with get_db() as db:
                db.execute('INSERT INTO policies(policy_number,customer_name,customer_email,customer_phone,premium_amount,frequency,start_date,last_payment_date,next_due_date,grace_period,status,paid_up) VALUES(?,?,?,?,?,?,?,?,?,?,?,0)',(number,name,d.get('customer_email','').strip(),d.get('customer_phone','').strip(),premium,freq,start.isoformat(),last.isoformat(),due.isoformat(),grace,'Active'))
            flash('Policy created successfully.','success'); return redirect(url_for('all_policies'))
        except Exception as e:
            flash('Could not save policy: '+('Policy number already exists.' if 'UNIQUE' in str(e) else str(e)), 'error')
    return render_template('policy_form.html', policy=None)

@app.route('/policies/<int:pid>/edit', methods=['GET','POST'])
def edit_policy(pid):
    p=fetch_policy(pid)
    if request.method=='POST':
        try:
            d=request.form; number=d['policy_number'].strip(); name=d['customer_name'].strip(); premium=float(d['premium_amount']); freq=d['frequency']
            start=date.fromisoformat(d['start_date']); last=date.fromisoformat(d['last_payment_date']); grace=int(d['grace_period'])
            if not number or not name or premium<=0 or freq not in ('monthly','yearly') or grace<0: raise ValueError('Please provide valid values.')
            due=calc_next_due(last,freq)
            with get_db() as db:
                db.execute('UPDATE policies SET policy_number=?,customer_name=?,customer_email=?,customer_phone=?,premium_amount=?,frequency=?,start_date=?,last_payment_date=?,next_due_date=?,grace_period=? WHERE id=?',(number,name,d.get('customer_email','').strip(),d.get('customer_phone','').strip(),premium,freq,start.isoformat(),last.isoformat(),due.isoformat(),grace,pid))
            flash('Policy updated.','success'); return redirect(url_for('all_policies'))
        except Exception as e: flash('Could not update policy: '+('Policy number already exists.' if 'UNIQUE' in str(e) else str(e)),'error')
    return render_template('policy_form.html', policy=p)

@app.get('/policies')
def all_policies():
    with get_db() as db: policies=db.execute('SELECT * FROM policies ORDER BY next_due_date').fetchall()
    return render_template('policies.html', policies=policies, heading='All Policies')

@app.get('/reminders')
def reminders():
    with get_db() as db:
        notices=db.execute("SELECT n.*,p.policy_number,p.customer_name,p.next_due_date,p.status FROM notifications n JOIN policies p ON p.id=n.policy_id WHERE p.paid_up=0 ORDER BY n.id DESC").fetchall()
        due=db.execute("SELECT * FROM policies WHERE status IN ('Due Soon','Grace Period') AND paid_up=0 ORDER BY next_due_date").fetchall()
    return render_template('reminders.html', notices=notices, due=due)

@app.get('/lapsed')
def lapsed_policies():
    with get_db() as db: policies=db.execute("SELECT * FROM policies WHERE status='Lapsed' AND paid_up=0 ORDER BY next_due_date").fetchall()
    return render_template('policies.html', policies=policies, heading='Lapsed Policies')

@app.post('/policies/<int:pid>/pay')
def record_payment(pid):
    p=fetch_policy(pid)
    if p['paid_up']: flash('Paid-Up policies do not require premium payments.','error')
    else:
        paid=date.fromisoformat(request.form.get('payment_date') or date.today().isoformat())
        due=calc_next_due(paid,p['frequency'])
        with get_db() as db:
            db.execute("UPDATE policies SET last_payment_date=?,next_due_date=?,status='Active' WHERE id=?",(paid.isoformat(),due.isoformat(),pid))
            db.execute("DELETE FROM notifications WHERE policy_id=?",(pid,))
        flash(f'Payment recorded. Next due date: {due.isoformat()}.','success')
    return redirect(request.referrer or url_for('all_policies'))

@app.post('/policies/<int:pid>/paid-up')
def mark_paid_up(pid):
    fetch_policy(pid)
    with get_db() as db:
        db.execute("UPDATE policies SET paid_up=1,status='Paid-Up' WHERE id=?",(pid,)); db.execute('DELETE FROM notifications WHERE policy_id=?',(pid,))
    flash('Policy marked Paid-Up. It is excluded from reminders and lapse checks.','success'); return redirect(request.referrer or url_for('all_policies'))

@app.post('/policies/<int:pid>/delete')
def delete_policy(pid):
    fetch_policy(pid)
    with get_db() as db: db.execute('DELETE FROM policies WHERE id=?',(pid,))
    flash('Policy deleted.','success'); return redirect(url_for('all_policies'))

@app.post('/monitor')
def run_monitor():
    result=monitor()
    flash(f"Monitoring complete: {result['checked']} checked; {result['reminders']} new reminders; {result['lapsed']} lapsed.",'success')
    return redirect(request.referrer or url_for('dashboard'))

@app.get('/health')
def health(): return {'status':'ok','application':'Insurance Premium Notifier'}

if __name__=='__main__': app.run(debug=os.environ.get('FLASK_DEBUG')=='1')
