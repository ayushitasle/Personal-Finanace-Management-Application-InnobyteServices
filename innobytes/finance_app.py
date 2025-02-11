import hashlib
import datetime
import sqlite3
import os
import csv
import colorama
from colorama import Fore, Back, Style
import time

colorama.init(autoreset=True)

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = self._hash_password(password)
        self.transactions = []
        self.budgets = {}

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self._hash_password(password) == self.password

    def set_budget(self, category, amount):
        self.budgets[category] = amount

    def get_budget(self, category):
        return self.budgets.get(category, 0)

class Transaction:
    def __init__(self, amount, category, date, transaction_type):
        self.amount = amount
        self.category = category
        self.date = date
        self.transaction_type = transaction_type  # 'income' or 'expense'

class FinanceApp:
    def __init__(self, db_name='finance.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.current_user = None
        self.setup_database()

    def setup_database(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users
                            (username TEXT PRIMARY KEY, password TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS transactions
                            (username TEXT, amount REAL, category TEXT, date TEXT, type TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS budgets
                            (username TEXT, category TEXT, amount REAL)''')
        self.conn.commit()

    def register_user(self, username, password):
        try:
            user = User(username, password)
            self.cursor.execute("INSERT INTO users VALUES (?, ?)", (username, user.password))
            self.conn.commit()
            print("User registered successfully.")
            return True
        except sqlite3.IntegrityError:
            print("Username already exists.")
            return False

    def login(self, username, password):
        self.cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        if result and result[0] == User(username, password).password:
            self.current_user = User(username, password)
            self._load_user_data()
            print(f"Welcome, {username}!")
            return True
        print("Invalid username or password.")
        return False

    def _load_user_data(self):
        # Load transactions
        self.cursor.execute("SELECT amount, category, date, type FROM transactions WHERE username = ?", (self.current_user.username,))
        for row in self.cursor.fetchall():
            self.current_user.transactions.append(Transaction(*row))
        
        # Load budgets
        self.cursor.execute("SELECT category, amount FROM budgets WHERE username = ?", (self.current_user.username,))
        for category, amount in self.cursor.fetchall():
            self.current_user.budgets[category] = amount

    def add_transaction(self, amount, category, date, transaction_type):
        if not self.current_user:
            print("Please log in first.")
            return
        transaction = Transaction(amount, category, date, transaction_type)
        self.current_user.transactions.append(transaction)
        self.cursor.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
                            (self.current_user.username, amount, category, date.isoformat(), transaction_type))
        self.conn.commit()
        print("Transaction added successfully.")
        self._check_budget(category)

    def _check_budget(self, category):
        budget = self.current_user.get_budget(category)
        if budget > 0:
            total_expenses = sum(t.amount for t in self.current_user.transactions 
                                 if t.category == category and t.transaction_type == 'expense' 
                                 and t.date.strftime('%Y-%m') == datetime.date.today().strftime('%Y-%m'))
            if total_expenses > budget:
                print(f"Warning: You have exceeded your budget for {category}!")

    def update_transaction(self, index, amount, category, date, transaction_type):
        if not self.current_user:
            print("Please log in first.")
            return
        if 0 <= index < len(self.current_user.transactions):
            old_transaction = self.current_user.transactions[index]
            new_transaction = Transaction(amount, category, date, transaction_type)
            self.current_user.transactions[index] = new_transaction
            self.cursor.execute("""UPDATE transactions 
                                SET amount = ?, category = ?, date = ?, type = ?
                                WHERE username = ? AND amount = ? AND category = ? AND date = ? AND type = ?""",
                                (amount, category, date.isoformat(), transaction_type,
                                 self.current_user.username, old_transaction.amount, old_transaction.category,
                                 old_transaction.date.isoformat(), old_transaction.transaction_type))
            self.conn.commit()
            print("Transaction updated successfully.")
            self._check_budget(category)
        else:
            print("Invalid transaction index.")

    def delete_transaction(self, index):
        if not self.current_user:
            print("Please log in first.")
            return
        if 0 <= index < len(self.current_user.transactions):
            transaction = self.current_user.transactions[index]
            del self.current_user.transactions[index]
            self.cursor.execute("""DELETE FROM transactions 
                                WHERE username = ? AND amount = ? AND category = ? AND date = ? AND type = ?""",
                                (self.current_user.username, transaction.amount, transaction.category,
                                 transaction.date.isoformat(), transaction.transaction_type))
            self.conn.commit()
            print("Transaction deleted successfully.")
        else:
            print("Invalid transaction index.")

    def generate_report(self, start_date, end_date):
        if not self.current_user:
            print("Please log in first.")
            return
        
        total_income = 0
        total_expenses = 0
        category_expenses = {}
        
        for transaction in self.current_user.transactions:
            if start_date <= transaction.date <= end_date:
                if transaction.transaction_type == 'income':
                    total_income += transaction.amount
                else:
                    total_expenses += transaction.amount
                    category_expenses[transaction.category] = category_expenses.get(transaction.category, 0) + transaction.amount
        
        savings = total_income - total_expenses
        print(f"\nFinancial Report ({start_date} to {end_date}):")
        print(f"Total Income: ${total_income:.2f}")
        print(f"Total Expenses: ${total_expenses:.2f}")
        print(f"Savings: ${savings:.2f}")
        
        print("\nExpense Breakdown by Category:")
        for category, amount in category_expenses.items():
            print(f"{category}: ${amount:.2f} ({amount/total_expenses*100:.1f}%)")
            budget = self.current_user.get_budget(category)
            if budget > 0:
                print(f"  Budget: ${budget:.2f} ({'Over' if amount > budget else 'Under'} by ${abs(budget - amount):.2f})")

    def list_transactions(self):
        if not self.current_user:
            print("Please log in first.")
            return
        if not self.current_user.transactions:
            print("No transactions found.")
            return
        for i, t in enumerate(self.current_user.transactions):
            print(f"{i}: {t.date} - {t.category} - ${t.amount:.2f} ({t.transaction_type})")

    def set_budget(self, category, amount):
        if not self.current_user:
            print("Please log in first.")
            return
        self.current_user.set_budget(category, amount)
        self.cursor.execute("INSERT OR REPLACE INTO budgets VALUES (?, ?, ?)",
                            (self.current_user.username, category, amount))
        self.conn.commit()
        print(f"Budget set for {category}: ${amount:.2f}")

    def backup_data(self, filename):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['username', 'amount', 'category', 'date', 'type'])
            self.cursor.execute("SELECT * FROM transactions")
            writer.writerows(self.cursor.fetchall())
        print(f"Data backed up to {filename}")

    def restore_data(self, filename):
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header row
            self.cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)", reader)
        self.conn.commit()
        print(f"Data restored from {filename}")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_logo():
    logo = """
    ███████╗██╗███╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗
    ██╔════╝██║████╗  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝
    █████╗  ██║██╔██╗ ██║███████║██╔██╗ ██║██║     █████╗  
    ██╔══╝  ██║██║╚██╗██║██╔══██║██║╚██╗██║██║     ██╔══╝  
    ██║     ██║██║ ╚████║██║  ██║██║ ╚████║╚██████╗███████╗
    ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
    """
    print(Fore.CYAN + logo)
    print(Fore.YELLOW + "Personal Finance Management System".center(60))
    print(Fore.YELLOW + "=" * 60)

def print_menu():
    print(Fore.GREEN + "\nMenu Options:")
    print(Fore.YELLOW + "1. Register")
    print(Fore.YELLOW + "2. Login")
    print(Fore.YELLOW + "3. Add Transaction")
    print(Fore.YELLOW + "4. Update Transaction")
    print(Fore.YELLOW + "5. Delete Transaction")
    print(Fore.YELLOW + "6. List Transactions")
    print(Fore.YELLOW + "7. Generate Report")
    print(Fore.YELLOW + "8. Set Budget")
    print(Fore.YELLOW + "9. Backup Data")
    print(Fore.YELLOW + "10. Restore Data")
    print(Fore.RED + "11. Exit")

def animate_text(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.03)
    print()

def main():
    db_name = 'finance.db'
    app = FinanceApp(db_name)
    print(Fore.GREEN + f"Data is being stored in '{db_name}'" + Style.RESET_ALL)
    
    while True:
        clear_screen()
        print_logo()
        print_menu()
        
        choice = input(Fore.CYAN + "\nEnter your choice (1-11): " + Style.RESET_ALL)
        
        if choice == '1':
            clear_screen()
            print_logo()
            print(Fore.GREEN + "=== User Registration ===")
            username = input(Fore.YELLOW + "Enter username: " + Style.RESET_ALL)
            password = input(Fore.YELLOW + "Enter password: " + Style.RESET_ALL)
            if app.register_user(username, password):
                animate_text(Fore.GREEN + "Registration successful! Please log in.")
            else:
                animate_text(Fore.RED + "Registration failed. Username may already exist.")
            input(Fore.CYAN + "Press Enter to continue...")
        
        elif choice == '2':
            clear_screen()
            print_logo()
            print(Fore.GREEN + "=== User Login ===")
            username = input(Fore.YELLOW + "Enter username: " + Style.RESET_ALL)
            password = input(Fore.YELLOW + "Enter password: " + Style.RESET_ALL)
            if app.login(username, password):
                animate_text(Fore.GREEN + f"Welcome back, {username}!")
            else:
                animate_text(Fore.RED + "Login failed. Please check your credentials.")
            input(Fore.CYAN + "Press Enter to continue...")
        
        elif choice == '3':
            if not app.current_user:
                print(Fore.RED + "Please log in first.")
                input(Fore.CYAN + "Press Enter to continue...")
                continue
            amount = float(input(Fore.YELLOW + "Enter amount: " + Style.RESET_ALL))
            category = input(Fore.YELLOW + "Enter category: " + Style.RESET_ALL)
            date = datetime.datetime.strptime(input(Fore.YELLOW + "Enter date (YYYY-MM-DD): " + Style.RESET_ALL), "%Y-%m-%d").date()
            transaction_type = input(Fore.YELLOW + "Enter type (income/expense): " + Style.RESET_ALL).lower()
            app.add_transaction(amount, category, date, transaction_type)
            input(Fore.CYAN + "Press Enter to continue...")
        
        elif choice == '4':
            if not app.current_user:
                print(Fore.RED + "Please log in first.")
                input(Fore.CYAN + "Press Enter to continue...")
                continue
            app.list_transactions()
            index = int(input(Fore.YELLOW + "Enter the index of the transaction to update: " + Style.RESET_ALL))
            amount = float(input(Fore.YELLOW + "Enter new amount: " + Style.RESET_ALL))
            category = input(Fore.YELLOW + "Enter new category: " + Style.RESET_ALL)
            date = datetime.datetime.strptime(input(Fore.YELLOW + "Enter new date (YYYY-MM-DD): " + Style.RESET_ALL), "%Y-%m-%d").date()
            transaction_type = input(Fore.YELLOW + "Enter new type (income/expense): " + Style.RESET_ALL).lower()
            app.update_transaction(index, amount, category, date, transaction_type)
            input(Fore.CYAN + "Press Enter to continue...")
        
        elif choice == '5':
            if not app.current_user:
                print(Fore.RED + "Please log in first.")
                input(Fore.CYAN + "Press Enter to continue...")
                continue
            app.list_transactions()
            index = int(input(Fore.YELLOW + "Enter the index of the transaction to delete: " + Style.RESET_ALL))
            app.delete_transaction(index)
            input(Fore.CYAN + "Press Enter to continue...")
        
        elif choice == '6':
            app.list_transactions()
            input(Fore.CYAN + "Press Enter to continue...")
        
        elif choice == '7':
            if not app.current_user:
                print(Fore.RED + "Please log in first.")
                input(Fore.CYAN + "Press Enter to continue...")
                continue
            start_date = datetime.datetime.strptime(input(Fore.YELLOW + "Enter start date (YYYY-MM-DD): " + Style.RESET_ALL), "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(input(Fore.YELLOW + "Enter end date (YYYY-MM-DD): " + Style.RESET_ALL), "%Y-%m-%d").date()
            app.generate_report(start_date, end_date)
            input(Fore.CYAN + "Press Enter to continue...")
        
        elif choice == '8':
            if not app.current_user:
                print(Fore.RED + "Please log in first.")
                input(Fore.CYAN + "Press Enter to continue...")
                continue
            category = input(Fore.YELLOW + "Enter category: " + Style.RESET_ALL)
            amount = float(input(Fore.YELLOW + "Enter budget amount: " + Style.RESET_ALL))
            app.set_budget(category, amount)
            input(Fore.CYAN + "Press Enter to continue...")
        
        elif choice == '9':
            filename = input(Fore.YELLOW + "Enter filename for backup: " + Style.RESET_ALL)
            app.backup_data(filename)
            input(Fore.CYAN + "Press Enter to continue...")
        
        elif choice == '10':
            filename = input(Fore.YELLOW + "Enter filename to restore from: " + Style.RESET_ALL)
            app.restore_data(filename)
            input(Fore.CYAN + "Press Enter to continue...")
        
        elif choice == '11':
            clear_screen()
            print_logo()
            animate_text(Fore.GREEN + "Thank you for using the Personal Finance Management App. Goodbye!")
            break
        
        else:
            print(Fore.RED + "Invalid choice. Please try again.")
            input(Fore.CYAN + "Press Enter to continue...")

if __name__ == "__main__":
    main()