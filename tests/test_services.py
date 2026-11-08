import unittest, tempfile, os
from datetime import date
from services import calc_next_due, status_for, add_months
class DateLogicTests(unittest.TestCase):
 def test_month_end(self): self.assertEqual(calc_next_due(date(2026,1,31),'monthly'),date(2026,2,28))
 def test_leap_year(self): self.assertEqual(calc_next_due(date(2024,2,29),'yearly'),date(2025,2,28))
 def test_monthly_31_march(self): self.assertEqual(add_months(date(2026,1,31),2),date(2026,3,31))
 def test_active(self): self.assertEqual(status_for(date(2026,12,1),30,date(2026,11,1)),'Active')
 def test_due_soon_today(self): self.assertEqual(status_for(date(2026,11,10),30,date(2026,11,6)),'Due Soon')
 def test_due_today(self): self.assertEqual(status_for(date(2026,11,6),30,date(2026,11,6)),'Due Soon')
 def test_grace_period(self): self.assertEqual(status_for(date(2026,11,1),30,date(2026,11,20)),'Grace Period')
 def test_grace_deadline_inclusive(self): self.assertEqual(status_for(date(2026,10,1),30,date(2026,10,31)),'Grace Period')
 def test_lapsed_after_deadline(self): self.assertEqual(status_for(date(2026,10,1),30,date(2026,11,1)),'Lapsed')
 def test_zero_grace(self): self.assertEqual(status_for(date(2026,11,5),0,date(2026,11,6)),'Lapsed')
 def test_invalid_frequency(self):
  with self.assertRaises(ValueError): calc_next_due(date.today(),'weekly')
if __name__=='__main__': unittest.main()
