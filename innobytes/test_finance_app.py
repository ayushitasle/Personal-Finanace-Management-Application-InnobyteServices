import unittest
import os
from finance_app import FinanceApp, User, Transaction
from datetime import date

class TestFinanceApp(unittest.TestCase):
    def setUp(self):
        self.app = FinanceApp('test.db')
        self.app.register_user('testuser', 'testpass')
        self.app.login('testuser', 'testpass')

    def tearDown(self):
        self.app.conn.close()
        os.remove('test.db')

    def test_register_user(self):
        result = self.app.register_user('newuser', 'newpass')
        self.assertTrue(result)
        result = self.app.register_user('testuser', 'testpass')
        self.assertFalse(result)

    def test_login(self):
        result = self.app.login('testuser', 'testpass')
        self.assertTrue(result)
        result = self.app.login('testuser', 'wrongpass')
        self.assertFalse(result)

    def test_add_transaction(self):
        self.app.add_transaction(100, 'Food', date.today(), 'expense')
        self.assertEqual(len(self.app.current_user.transactions), 1)
        self.assertEqual(self.app.current_user.transactions[0].amount, 100)

    def test_update_transaction(self):
        self.app.add_transaction(100, 'Food', date.today(), 'expense')
        self.app.update_transaction(0, 150, 'Groceries', date.today(), 'expense')
        self.assertEqual(self.app.current_user.transactions[0].amount, 150)
        self.assertEqual(self.app.current_user.transactions[0].category, 'Groceries')

    def test_delete_transaction(self):
        self.app.add_transaction(100, 'Food', date.today(), 'expense')
        self.app.delete_transaction(0)
        self.assertEqual(len(self.app.current_user.transactions), 0)

    def test_set_budget(self):
        self.app.set_budget('Food', 200)
        self.assertEqual(self.app.current_user.get_budget('Food'), 200)

    def test_generate_report(self):
        self.app.add_transaction(100, 'Food', date.today(), 'expense')
        self.app.add_transaction(200, 'Salary', date.today(), 'income')
        report = self.app.generate_report(date.today(), date.today())
        self.assertIn('Total Income: $200.00', report)
        self.assertIn('Total Expenses: $100.00', report)
        self.assertIn('Savings: $100.00', report)

    def test_backup_restore(self):
        self.app.add_transaction(100, 'Food', date.today(), 'expense')
        self.app.backup_data('test_backup.csv')
        self.assertTrue(os.path.exists('test_backup.csv'))
        
        self.app.delete_transaction(0)
        self.assertEqual(len(self.app.current_user.transactions), 0)
        
        self.app.restore_data('test_backup.csv')
        self.assertEqual(len(self.app.current_user.transactions), 1)
        
        os.remove('test_backup.csv')

if __name__ == '__main__':
    unittest.main()