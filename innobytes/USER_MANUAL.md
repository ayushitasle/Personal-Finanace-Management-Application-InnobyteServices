# Personal Finance Management Application User Manual

## Installation

1. Ensure you have Python 3.6 or higher installed on your system.
2. Download the `finance_app.py` file.
3. Install required libraries by running: `pip install flask`

## Usage

The application now uses a web-based interface powered by Flask. To start the application:

1. Open a terminal or command prompt.
2. Navigate to the directory containing `finance_app.py`.
3. Run the command: `python finance_app.py`
4. Open a web browser and go to `http://localhost:5000`

## Features

### Register
- Click on the "Register" link on the login page.
- Enter a username and password.
- Click "Register" to create your account.

### Login
- Enter your username and password on the login page.
- Click "Login" to access your account.

### Add Transaction
- Click on "Add Transaction" in the navigation menu.
- Enter the transaction details:
  - Amount
  - Category
  - Date (in YYYY-MM-DD format)
  - Type (income or expense)
- Click "Add Transaction" to save.

### List Transactions
- Click on "List Transactions" in the navigation menu to view all your transactions.

### Generate Report
- Click on "Generate Report" in the navigation menu.
- Enter a start date and end date (in YYYY-MM-DD format).
- Click "Generate Report" to view your financial summary for the specified period.

### Set Budget
- Click on "Set Budget" in the navigation menu.
- Enter a category and budget amount.
- Click "Set Budget" to save.

### Logout
- Click on "Logout" in the navigation menu to end your session.

## Notes

- The application will warn you when you exceed your budget for a category.
- All financial data is stored locally in a SQLite database file named 'finance.db'.
- Ensure you log out after each session, especially if using a shared computer.

## Troubleshooting

- If you encounter any issues, try restarting the application.
- Ensure you have the latest version of Flask installed.
- Check that port 5000 is not being used by another application.

For further assistance, please contact the application support team.
