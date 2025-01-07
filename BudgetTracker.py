# budget_tracker.py
"""
Budget Tracking Application

A Streamlit-based application for tracking business expenses and managing budgets.
Features:
- Bank statement import (PDF and Excel)
- Transaction management
- Budget tracking
- Financial analytics
- Expense categorization
"""

from time import sleep
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, time, timedelta
import os
from pathlib import Path
import numpy as np
from io import BytesIO
import sqlite3
from decimal import Decimal
import pdfplumber
import re

class BankStatementParser:
    """Handles parsing of bank statements in various formats"""
    
    def __init__(self):
        self.supported_banks = ['HDFC']
        
    def clean_amount(self, amount_str):
        """Clean amount strings and convert to float with enhanced error handling"""
        try:
            # Handle None or empty values
            if pd.isna(amount_str) or amount_str is None or amount_str == '':
                return 0.0
                
            # If amount is already a number, return it
            if isinstance(amount_str, (int, float)):
                return float(amount_str)
            
            # Convert to string and remove any whitespace
            amount_str = str(amount_str).strip()
            
            # Remove commas and any other non-numeric characters except decimal point
            amount_str = ''.join(c for c in amount_str if c.isdigit() or c == '.')
            
            # Convert to float
            return float(amount_str) if amount_str else 0.0
            
        except Exception as e:
            print(f"Error cleaning amount {amount_str}: {str(e)}")
            return 0.0

    def parse_date(self, date_val):
        """Parse date values from various formats"""
        try:
            # If it's already a datetime
            if isinstance(date_val, datetime):
                return date_val
                
            # If it's a string, try different formats
            if isinstance(date_val, str):
                date_str = date_val.strip()
                try:
                    # Try dd/mm/yy format
                    return datetime.strptime(date_str, '%d/%m/%y')
                except ValueError:
                    try:
                        # Try dd/mm/yyyy format
                        return datetime.strptime(date_str, '%d/%m/%Y')
                    except ValueError:
                        print(f"Could not parse date: {date_str}")
                        return None
            
            print(f"Unsupported date format: {type(date_val)} - {date_val}")
            return None
            
        except Exception as e:
            print(f"Error parsing date {date_val}: {str(e)}")
            return None

    def parse_excel_statement(self, file_content):
        """Parse HDFC bank statement in Excel format"""
        try:
            print("\nProcessing Excel file...")
            
            # Read Excel file into DataFrame
            df = pd.read_excel(BytesIO(file_content))
            print(f"Initial DataFrame shape: {df.shape}")
            
            # Find header row
            header_row = None
            for idx, row in df.iterrows():
                row_text = ' '.join(str(x).lower() for x in row.values)
                if ('date' in row_text and 'narration' in row_text and 
                    ('withdrawal' in row_text or 'debit' in row_text)):
                    header_row = idx
                    break
            
            if header_row is None:
                raise ValueError("Could not find transaction table header")
                
            # Set header and remove rows above it
            df.columns = df.iloc[header_row]
            df = df.iloc[header_row + 1:].reset_index(drop=True)
            
            # Clean column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Find required columns
            date_col = next(col for col in df.columns if 'date' in col.lower() and 'value' not in col.lower())
            narration_col = next(col for col in df.columns if 'narration' in col.lower())
            ref_col = next(col for col in df.columns if 'ref' in col.lower() or 'chq' in col.lower())
            withdrawal_col = next(col for col in df.columns if 'withdrawal' in col.lower() or 'debit' in col.lower())
            deposit_col = next(col for col in df.columns if 'deposit' in col.lower() or 'credit' in col.lower())
            balance_col = next(col for col in df.columns if 'balance' in col.lower())
            
            # Process transactions
            transactions = []
            current_description = ''
            
            for idx, row in df.iterrows():
                try:
                    # Skip summary rows
                    if 'statement summary' in str(row[narration_col]).lower():
                        break
                        
                    date_val = row[date_col]
                    if pd.isna(date_val):
                        # This might be a continuation of previous description
                        if current_description:
                            current_description += ' ' + str(row[narration_col])
                        continue
                    
                    # Parse date
                    date_obj = self.parse_date(date_val)
                    if not date_obj:
                        continue
                    
                    # Get description
                    description = (current_description + ' ' + str(row[narration_col]) 
                                 if current_description else str(row[narration_col]))
                    current_description = ''  # Reset for next transaction
                    
                    # Get amounts
                    withdrawal = self.clean_amount(row[withdrawal_col])
                    deposit = self.clean_amount(row[deposit_col])
                    balance = self.clean_amount(row[balance_col])
                    
                    # Create transaction record
                    transaction = {
                        'date': date_obj,
                        'description': description.strip(),
                        'reference': str(row[ref_col]).strip(),
                        'type': 'debit' if withdrawal > 0 else 'credit',
                        'amount': withdrawal if withdrawal > 0 else deposit,
                        'balance': balance
                    }
                    
                    print(f"Found transaction: {transaction}")  # Debug log
                    transactions.append(transaction)
                    
                except Exception as e:
                    print(f"Error processing row {idx}: {str(e)}")
                    continue
            
            if not transactions:
                raise ValueError("No valid transactions found in the statement")
            
            # Convert to DataFrame and return
            df_result = pd.DataFrame(transactions)
            print(f"Processed {len(df_result)} transactions")
            return df_result
            
        except Exception as e:
            print(f"Error processing Excel file: {str(e)}")
            raise ValueError(f"Error processing Excel statement: {str(e)}")

    def parse_pdf_statement(self, file):
        """Parse HDFC bank statement in PDF format"""
        try:
            transactions = []
            
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    
                    for table in tables:
                        if not table:
                            continue
                            
                        # Find transaction table
                        header_found = False
                        for row_idx, row in enumerate(table):
                            row = [str(cell).strip() if cell is not None else '' for cell in row]
                            row_text = ' '.join(row).lower()
                            
                            # Look for header row
                            if ('date' in row_text and 'narration' in row_text and 
                                ('withdrawal' in row_text or 'debit' in row_text)):
                                header_found = True
                                continue
                            
                            if not header_found:
                                continue
                                
                            try:
                                # Skip empty or summary rows
                                if not row[0] or 'statement summary' in ' '.join(row).lower():
                                    continue
                                
                                # Parse date
                                date_obj = self.parse_date(row[0])
                                if not date_obj:
                                    continue
                                
                                # Get amounts
                                withdrawal = self.clean_amount(row[4])
                                deposit = self.clean_amount(row[5])
                                
                                # Create transaction record
                                transaction = {
                                    'date': date_obj,
                                    'description': row[1].strip(),
                                    'reference': row[2].strip(),
                                    'type': 'debit' if withdrawal > 0 else 'credit',
                                    'amount': withdrawal if withdrawal > 0 else deposit,
                                    'balance': self.clean_amount(row[6])
                                }
                                
                                transactions.append(transaction)
                                
                            except Exception as e:
                                print(f"Error processing row: {str(e)}")
                                continue
            
            if not transactions:
                raise ValueError("No valid transactions found in the statement")
                
            return pd.DataFrame(transactions)
            
        except Exception as e:
            raise ValueError(f"Error processing PDF statement: {str(e)}")

class BudgetTracker:
    """Main class for budget and expense tracking functionality"""
    
    def __init__(self):
        """Initialize the budget tracker with database connection"""
        self.conn = sqlite3.connect('budget_tracker.db', check_same_thread=False)
        self.statement_parser = BankStatementParser()
        self.setup_database()
        
    def setup_database(self):
        """Set up the necessary database tables"""
        cursor = self.conn.cursor()
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                description TEXT NOT NULL,
                reference_no TEXT,
                type TEXT CHECK(type IN ('debit', 'credit')) NOT NULL,
                amount DECIMAL(10,2) NOT NULL DEFAULT 0,
                balance DECIMAL(10,2) NOT NULL DEFAULT 0,
                category TEXT,
                tags TEXT,
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create budgets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT CHECK(type IN ('expense', 'income', 'transfer')) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Create validated_expenses table for tracking expense validation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validated_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manual_transaction_id INTEGER NOT NULL,
                bank_transaction_id INTEGER,
                is_validated BOOLEAN NOT NULL,
                validation_date TIMESTAMP NOT NULL,
                FOREIGN KEY(manual_transaction_id) REFERENCES transactions(id),
                FOREIGN KEY(bank_transaction_id) REFERENCES transactions(id)
            )
        ''')
        # Add default categories
        default_categories = [
            ('Salary', 'income', 'Regular salary income'),
            ('Sales Revenue', 'income', 'Income from sales'),
            ('Office Supplies', 'expense', 'Office supplies and stationery'),
            ('Utilities', 'expense', 'Electricity, water, internet, etc.'),
            ('Marketing', 'expense', 'Marketing and advertising expenses'),
            ('Travel', 'expense', 'Business travel expenses'),
            ('Transfer', 'transfer', 'Internal transfers'),
            ('Other', 'expense', 'Miscellaneous expenses')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO categories (name, type, description)
            VALUES (?, ?, ?)
        ''', default_categories)
        
        self.conn.commit()
    def find_matching_transactions(self, amount, date, description=None, tolerance_days=5):
        """
        Find potential matching transactions in bank statements within a date range.
        
        This method searches for transactions that match an expense by amount and date,
        considering a tolerance window around the transaction date.
        
        Parameters:
            amount: The transaction amount to match
            date: Can be either a string 'YYYY-MM-DD' or a datetime.date object
            description: Optional transaction description to help with matching
            tolerance_days: Number of days before and after to search (default 5)
        """
        cursor = self.conn.cursor()
        
        # Handle both string and datetime.date inputs
        if isinstance(date, str):
            base_date = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            # If it's already a datetime.date object, use it directly
            base_date = date
        
        # Calculate the date range for searching
        start_date = (base_date - timedelta(days=tolerance_days)).strftime('%Y-%m-%d')
        end_date = (base_date + timedelta(days=tolerance_days)).strftime('%Y-%m-%d')
        
        # Find potential matches based on amount and date range
        query = '''
            SELECT id, date, description, amount, reference_no, source
            FROM transactions
            WHERE type = 'debit'
            AND amount = ?
            AND date BETWEEN ? AND ?
            AND source = 'bank_statement'
            AND id NOT IN (
                SELECT COALESCE(bank_transaction_id, -1)
                FROM validated_expenses 
                WHERE bank_transaction_id IS NOT NULL
            )
        '''
        
        cursor.execute(query, (amount, start_date, end_date))
        return cursor.fetchall()

    def validate_expense(self, manual_transaction_id, bank_transaction_id, is_validated):
        """
        Record the validation status of an expense against a bank statement entry.
        
        Parameters:
            manual_transaction_id (int): ID of the manually entered transaction
            bank_transaction_id (int): ID of the matching bank statement transaction
            is_validated (bool): Whether the match is accepted or declined
            
        This method records whether a manual expense matches a bank statement entry,
        helping prevent double-counting and ensuring accuracy in expense tracking.
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO validated_expenses 
                (manual_transaction_id, bank_transaction_id, is_validated, validation_date)
                VALUES (?, ?, ?, datetime('now'))
            ''', (manual_transaction_id, bank_transaction_id if is_validated else None, is_validated))
            
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
    def process_bank_statement(self, file, file_type):
        """Process uploaded bank statement"""
        try:
            # Read file content
            file_content = file.read()
            file.seek(0)  # Reset file pointer
            
            # Parse statement based on file type
            if file_type.lower() == 'pdf':
                df = self.statement_parser.parse_pdf_statement(file)
            else:
                df = self.statement_parser.parse_excel_statement(file_content)
            
            # Insert transactions into database
            cursor = self.conn.cursor()
            transactions_added = 0
            duplicates_found = 0
            
            for _, row in df.iterrows():
                # Check for duplicates
                cursor.execute('''
                    SELECT COUNT(*) FROM transactions
                    WHERE date = ? AND description = ? AND amount = ? AND type = ?
                ''', (
                    row['date'].strftime('%Y-%m-%d'),
                    row['description'],
                    float(row['amount']),
                    row['type']
                ))
                
                if cursor.fetchone()[0] == 0:
                    # No duplicate found, insert the transaction
                    cursor.execute('''
                        INSERT INTO transactions 
                        (date, description, reference_no, type, amount, balance, source)
                        VALUES (?, ?, ?, ?, ?, ?, 'bank_statement')
                    ''', (
                        row['date'].strftime('%Y-%m-%d'),
                        row['description'],
                        row['reference'],
                        row['type'],
                        float(row['amount']),
                        float(row['balance'])
                    ))
                    transactions_added += 1
                else:
                    duplicates_found += 1
            
            self.conn.commit()
            
            message = f"Successfully processed {transactions_added} new transaction(s)"
            if duplicates_found > 0:
                message += f" and skipped {duplicates_found} duplicate(s)"
            
            return True, message
            
        except Exception as e:
            return False, str(e)

    def add_manual_transaction(self, date, description, amount, category, transaction_type, reference_no=None):
        """Add a manual transaction with validation against bank statements"""
        cursor = self.conn.cursor()
        
        try:
            # Debug print statements
            print(f"Adding transaction with date: {date} (type: {type(date)})")
            print(f"Amount: {amount}, Type: {transaction_type}")
            
            # Insert the manual transaction
            cursor.execute('''
                INSERT INTO transactions 
                (date, description, reference_no, type, amount, category, source)
                VALUES (?, ?, ?, ?, ?, ?, 'manual')
            ''', (date, description, reference_no, transaction_type, amount, category))
            
            transaction_id = cursor.lastrowid
            matches = []
            
            # For debit transactions, look for matching bank entries
            if transaction_type == 'debit':
                matches = self.find_matching_transactions(amount, date, description)
                print(f"Found {len(matches)} potential matches")
            
            self.conn.commit()
            return transaction_id, matches
            
        except Exception as e:
            self.conn.rollback()
            print(f"Error in add_manual_transaction: {str(e)}")
            raise e
    def delete_manual_transaction(self, transaction_id):
        """
        Delete a manually entered transaction and its associated validations.
        
        This method will:
        1. Check if the transaction is manual
        2. Delete any associated expense validations
        3. Delete the transaction itself
        Only allows deletion of manually entered transactions for safety
        """
        cursor = self.conn.cursor()
        
        try:
            # First check if this is a manual transaction
            cursor.execute('''
                SELECT source FROM transactions 
                WHERE id = ?
            ''', (transaction_id,))
            
            result = cursor.fetchone()
            if not result or result[0] != 'manual':
                raise ValueError("Only manually entered transactions can be deleted")
            
            # Begin transaction for multiple deletions
            cursor.execute('BEGIN TRANSACTION')
            
            # Delete any associated validations first
            cursor.execute('''
                DELETE FROM validated_expenses 
                WHERE manual_transaction_id = ?
            ''', (transaction_id,))
            
            # Delete the transaction
            cursor.execute('''
                DELETE FROM transactions 
                WHERE id = ? AND source = 'manual'
            ''', (transaction_id,))
            
            # Commit the changes
            cursor.execute('COMMIT')
            return True, "Transaction deleted successfully"
            
        except Exception as e:
            # Rollback in case of any error
            cursor.execute('ROLLBACK')
            return False, f"Error deleting transaction: {str(e)}"
    def get_transactions(self, start_date=None, end_date=None, category=None, transaction_type=None):
        """Retrieve transactions with filters"""
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if category:
            query += " AND category = ?"
            params.append(category)
        if transaction_type:
            query += " AND type = ?"
            params.append(transaction_type)
            
        query += " ORDER BY date DESC, id DESC"
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_transaction_summary(self, start_date=None, end_date=None):
        """Get transaction summary including total debits, credits, and balance"""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT 
                COUNT(*) as total_transactions,
                COALESCE(SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END), 0) as total_debits,
                COALESCE(SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END), 0) as total_credits,
                COALESCE((SELECT balance FROM transactions 
                 WHERE date <= ? ORDER BY date DESC, id DESC LIMIT 1), 0) as closing_balance
            FROM transactions
            WHERE date BETWEEN ? AND ?
        '''
        
        end_date = end_date or datetime.now().date()
        start_date = start_date or (end_date - timedelta(days=30))
        
        cursor.execute(query, (end_date, start_date, end_date))
        result = cursor.fetchone()
        
        # Ensure we return valid numeric values even if the query returns None
        if result is None:
            return (0, 0.0, 0.0, 0.0)
        
        total_transactions, total_debits, total_credits, closing_balance = result
        return (
            total_transactions or 0,
            float(total_debits or 0),
            float(total_credits or 0),
            float(closing_balance or 0)
        )

    def get_category_summary(self, start_date=None, end_date=None, transaction_type=None):
        """Get summary of transactions by category with custom date range"""
        query = '''
            SELECT 
                COALESCE(category, 'Uncategorized') as category,
                SUM(amount) as total_amount,
                COUNT(*) as transaction_count
            FROM transactions
            WHERE date BETWEEN ? AND ?
        '''
        params = [start_date or '1900-01-01', end_date or '9999-12-31']
        
        if transaction_type:
            query += " AND type = ?"
            params.append(transaction_type)
            
        query += " GROUP BY category ORDER BY total_amount DESC"
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

class BudgetTrackerUI:
    """User interface class for the budget tracking application"""
    
    def __init__(self):
        """Initialize the UI with a BudgetTracker instance"""
        self.tracker = BudgetTracker()
        st.set_page_config(page_title="Budget Tracker", layout="wide")
        
    def run(self):
        """Main application entry point"""
        st.title("Budget and Expense Tracking Platform")
        
        # Sidebar navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["Dashboard", "Bank Statements", "Transactions", "Budget Management", "Analytics"]
        )
        
        if page == "Dashboard":
            self.show_dashboard()
        elif page == "Bank Statements":
            self.show_bank_statements()
        elif page == "Transactions":
            self.show_transactions()
        elif page == "Budget Management":
            self.show_budget_management()
        elif page == "Analytics":
            self.show_analytics()

    def show_dashboard(self):
        """Display the main dashboard with key metrics and recent transactions"""
        st.header("Dashboard")
        
        # Date range selector for metrics
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "From Date",
                value=datetime.now().date() - timedelta(days=30)
            )
        with col2:
            end_date = st.date_input("To Date", value=datetime.now().date())
        
        try:
            # Get and display transaction summary
            summary = self.tracker.get_transaction_summary(start_date, end_date)
            total_transactions, total_debits, total_credits, closing_balance = summary
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Transactions", f"{int(total_transactions):,}")
            with col2:
                st.metric("Total Debits", f"₹{float(total_debits):,.2f}")
            with col3:
                st.metric("Total Credits", f"₹{float(total_credits):,.2f}")
            with col4:
                st.metric("Closing Balance", f"₹{float(closing_balance):,.2f}")

            # Recent transactions section
            st.subheader("Recent Transactions")
            transactions = self.tracker.get_transactions(start_date, end_date)
            
            if transactions:
                df = pd.DataFrame(
                    transactions,
                    columns=['id', 'date', 'description', 'reference_no', 'type', 
                            'amount', 'balance', 'category', 'tags', 'source', 
                            'created_at']
                )
                
                # Format the DataFrame for display
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                df['amount'] = df.apply(lambda x: f"₹{x['amount']:,.2f}", axis=1)
                df['balance'] = df.apply(lambda x: f"₹{x['balance']:,.2f}", axis=1)
                
                # Color-code transactions based on type
                def highlight_type(row):
                    if row['type'] == 'debit':
                        return ['background-color: #ffebee'] * len(row)
                    elif row['type'] == 'credit':
                        return ['background-color: #e8f5e9'] * len(row)
                    else:
                        return ['background-color: #f5f5f5'] * len(row)
                
                styled_df = (df.style
                            .apply(highlight_type, axis=1)
                            .set_properties(**{
                            'background-color': '#f5f5f5',
                            'color': 'black',
                            'border-color': '#ddd'
                                }))
                st.dataframe(styled_df, height=400)
            else:
                st.info("No transactions found for the selected period.")
                
        except Exception as e:
            st.error(f"Error loading dashboard: {str(e)}")

    def show_bank_statements(self):
        """Handle bank statement upload and processing"""
        st.header("Bank Statement Upload")
        
        st.info("""
        Upload your HDFC bank statement in PDF or Excel format. 
        The system will automatically process and categorize the transactions.
        """)
        
        # File type selection
        file_type = st.radio(
            "Select statement format",
            options=['Excel', 'PDF'],
            format_func=lambda x: f"{x} format"
        )
        
        # File uploader based on type
        if file_type == 'PDF':
            uploaded_file = st.file_uploader(
                "Upload HDFC Bank Statement (PDF)", 
                type=['pdf']
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload HDFC Bank Statement (Excel)", 
                type=['xls', 'xlsx']
            )
        
        if uploaded_file is not None:
            with st.spinner("Processing bank statement..."):
                try:
                    success, message = self.tracker.process_bank_statement(
                        uploaded_file, 
                        'pdf' if file_type == 'PDF' else 'xls'
                    )
                    
                    if success:
                        st.success(message)
                        
                        # Show preview of processed transactions
                        st.subheader("Processed Transactions")
                        transactions = self.tracker.get_transactions(
                            datetime.now().date() - timedelta(days=7)
                        )
                        
                        if transactions:
                            df = pd.DataFrame(
                                transactions,
                                columns=['id', 'date', 'description', 'reference_no', 
                                        'type', 'amount', 'balance', 'category', 
                                        'tags', 'source', 'created_at']
                            )
                            
                            # Format the DataFrame for display
                            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                            df['amount'] = df.apply(lambda x: f"₹{x['amount']:,.2f}", axis=1)
                            df['balance'] = df.apply(lambda x: f"₹{x['balance']:,.2f}", axis=1)
                            
                            st.dataframe(df)
                        else:
                            st.info("No recent transactions found.")
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"Error processing statement: {str(e)}")

    def show_transactions(self):
        """Manual transaction entry and transaction history view"""
        st.header("Transaction Management")
        
        # Transaction entry form
        st.subheader("Add New Transaction")
        with st.form("transaction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Transaction Date")
                amount = st.number_input("Amount", min_value=0.0, step=0.01)
                transaction_type = st.selectbox(
                    "Transaction Type",
                    options=['debit', 'credit']
                )
                
            with col2:
                description = st.text_input("Description")
                category = st.selectbox(
                    "Category",
                    options=[
                        'Salary', 'Sales Revenue', 'Office Supplies',
                        'Utilities', 'Marketing', 'Travel', 'Salaries','Other'
                    ]
                )
                reference_no = st.text_input("Reference Number (Optional)")
            
            submitted = st.form_submit_button("Add Transaction")
            if submitted:
                try:
                    self.tracker.add_manual_transaction(
                        date, description, amount, category,
                        transaction_type, reference_no
                    )
                    st.success("Transaction added successfully!")
                except Exception as e:
                    st.error(f"Error adding transaction: {str(e)}")
        
        # Transaction history
        st.subheader("Transaction History")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_start_date = st.date_input(
                "From Date",
                value=datetime.now().date() - timedelta(days=30),
                key="filter_start_date"
            )
        with col2:
            filter_end_date = st.date_input(
                "To Date",
                value=datetime.now().date(),
                key="filter_end_date"
            )
        with col3:
            filter_type = st.selectbox(
                "Transaction Type",
                options=['All', 'debit', 'credit']
            )
        
        try:
            # Get filtered transactions
            transactions = self.tracker.get_transactions(
                start_date=filter_start_date,
                end_date=filter_end_date,
                transaction_type=None if filter_type == 'All' else filter_type
            )
            
            if transactions:
                df = pd.DataFrame(
                    transactions,
                    columns=['id', 'date', 'description', 'reference_no', 
                            'type', 'amount', 'balance', 'category', 
                            'tags', 'source', 'created_at']
                )
                
                # Format the DataFrame for display
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                df['amount'] = df.apply(lambda x: f"₹{x['amount']:,.2f}", axis=1)
                df['balance'] = df.apply(lambda x: f"₹{x['balance']:,.2f}", axis=1)
                st.write("Transaction History")
                for index, row in df.iterrows():
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
                        
                        with col1:
                            st.write(f"**Date:** {row['date']}")
                        with col2:
                            st.write(f"**Description:** {row['description']}")
                        with col3:
                            st.write(f"**Amount:** {row['amount']}")
                        with col4:
                            st.write(f"**Type:** {row['type']}")
                        with col5:
                            # Only show delete button for manual transactions
                            if row['source'] == 'manual':
                                if st.button('Delete', key=f"del_{row['id']}"):
                                    success, message = self.tracker.delete_manual_transaction(row['id'])
                                    if success:
                                        st.success(message)
                                        sleep(1)  # Using sleep instead of time.sleep
                                        st.rerun()  # Refresh the page to show updated data
                                    else:
                                        st.error(message)
                        
                        st.write("---")  # Divider between transactions
                # Color-code transactions
                def highlight_type(row):
                    if row['type'] == 'debit':
                        return ['background-color: #ffebee'] * len(row)
                    elif row['type'] == 'credit':
                        return ['background-color: #e8f5e9'] * len(row)
                    else:
                        return ['background-color: #f5f5f5'] * len(row)
                
                styled_df = (df.style
                            .apply(highlight_type, axis=1)
                            .set_properties(**{
                                'background-color': '#f5f5f5',
                                'color': 'black',
                        '        border-color': '#ddd'
                                }))
                st.dataframe(styled_df, height=400)
            else:
                st.info("No transactions found for the selected period.")
            if submitted:
                try:
                    # Add the transaction and get potential matches
                    transaction_id, matches = self.tracker.add_manual_transaction(
                        date.strftime('%Y-%m-%d'), description, amount, category,
                        transaction_type, reference_no
                    )
                    
                    if transaction_type == 'debit' and matches:
                        st.success("Transaction added successfully! Found potential matching bank statement entries.")
                        
                        # Display matching transactions for validation
                        st.subheader("Matching Bank Statement Entries")
                        st.write("Please validate this expense against the following potential matches:")
                        
                        for match in matches:
                            match_id, match_date, match_desc, match_amount, match_ref, match_source = match
                            
                            st.write("---")
                            col1, col2, col3 = st.columns([2, 2, 1])
                            
                            with col1:
                                st.write(f"**Date:** {match_date}")
                                st.write(f"**Amount:** ₹{match_amount:,.2f}")
                            
                            with col2:
                                st.write(f"**Description:** {match_desc}")
                                st.write(f"**Reference:** {match_ref}")
                            
                            with col3:
                                if st.button("Accept Match", key=f"accept_{match_id}"):
                                    self.tracker.validate_expense(transaction_id, match_id, True)
                                    st.success("Expense validated successfully!")
                                    st.rerun()
                                
                                if st.button("Decline", key=f"decline_{match_id}"):
                                    self.tracker.validate_expense(transaction_id, None, False)
                                    st.info("Match declined.")
                                    st.rerun()
                    else:
                        st.success("Transaction added successfully!")
                        if transaction_type == 'debit':
                            st.info("No matching bank statement entries found for this expense.")
                        
                except Exception as e:
                    st.error(f"Error adding transaction: {str(e)}")  # Show error message  
        except Exception as e:
            st.error(f"Error loading transactions: {str(e)}")

    def show_budget_management(self):
        """Budget allocation and tracking interface"""
        st.header("Budget Management")
        
        # Budget allocation form
        st.subheader("Set Budget")
        with st.form("budget_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                category = st.selectbox(
                    "Category",
                    options=[
                        'Office Supplies', 'Utilities', 'Marketing',
                        'Travel', 'Other'
                    ]
                )
                amount = st.number_input("Monthly Budget Amount", min_value=0.0)
                
            with col2:
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")
                
            submitted = st.form_submit_button("Set Budget")
            if submitted:
                try:
                    cursor = self.tracker.conn.cursor()
                    cursor.execute('''
                        INSERT INTO budgets (category, amount, start_date, end_date)
                        VALUES (?, ?, ?, ?)
                    ''', (category, amount, start_date, end_date))
                    self.tracker.conn.commit()
                    st.success("Budget set successfully!")
                except Exception as e:
                    st.error(f"Error setting budget: {str(e)}")

        # Show current budgets
        st.subheader("Current Budget Allocations")
        cursor = self.tracker.conn.cursor()
        cursor.execute('''
            SELECT category, amount, start_date, end_date
            FROM budgets
            WHERE end_date >= date('now')
            ORDER BY start_date DESC
        ''')
        budgets = cursor.fetchall()
        
        if budgets:
            df = pd.DataFrame(
                budgets,
                columns=['Category', 'Monthly Budget', 'Start Date', 'End Date']
            )
            df['Monthly Budget'] = df['Monthly Budget'].apply(
                lambda x: f"₹{x:,.2f}"
            )
            st.dataframe(df)
            
            # Budget vs Actual
            st.subheader("Budget vs Actual Spending")
            for category, budget, start_date, end_date in budgets:
                cursor.execute('''
                    SELECT SUM(amount)
                    FROM transactions
                    WHERE category = ? 
                    AND type = 'debit'
                    AND date BETWEEN ? AND ?
                ''', (category, start_date, end_date))
                
                actual_spending = cursor.fetchone()[0] or 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**{category}**")
                with col2:
                    st.write(f"Budget: ₹{budget:,.2f}")
                with col3:
                    st.write(f"Actual: ₹{actual_spending:,.2f}")
                
                # Progress bar for budget utilization
                progress = min(100, (actual_spending / budget) * 100)
                st.progress(progress / 100)
                
                # Add warning if over budget
                if actual_spending > budget:
                    st.warning(f"Over budget by ₹{(actual_spending - budget):,.2f}")
                
                st.write("---")
        else:
            st.info("No active budgets found. Add a budget using the form above.")

    def show_analytics(self):
        """Financial analytics and visualizations interface"""
        st.header("Financial Analytics")
        
        # Date range selection for analytics
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "From Date",
                value=datetime.now().date() - timedelta(days=90),
                key="analytics_start_date"
            )
        with col2:
            end_date = st.date_input(
                "To Date",
                value=datetime.now().date(),
                key="analytics_end_date"
            )

        try:
            # Get transactions for the selected period
            transactions = self.tracker.get_transactions(start_date, end_date)
            if not transactions:
                st.info("No transactions found for the selected period.")
                return

            df = pd.DataFrame(
                transactions,
                columns=['id', 'date', 'description', 'reference_no', 'type', 
                        'amount', 'balance', 'category', 'tags', 'source', 
                        'created_at']
            )
            df['date'] = pd.to_datetime(df['date'])

            # 1. Monthly Overview
            st.subheader("Monthly Overview")
            monthly_data = df.groupby([df['date'].dt.strftime('%Y-%m'), 'type'])['amount'].sum().unstack()
            
            fig = go.Figure()
            if 'debit' in monthly_data.columns:
                fig.add_trace(
                    go.Bar(
                        x=monthly_data.index,
                        y=monthly_data['debit'],
                        name='Expenses',
                        marker_color='#ff6b6b'
                    )
                )
            if 'credit' in monthly_data.columns:
                fig.add_trace(
                    go.Bar(
                        x=monthly_data.index,
                        y=monthly_data['credit'],
                        name='Income',
                        marker_color='#51cf66'
                    )
                )
                
            fig.update_layout(
                title='Monthly Income vs Expenses',
                barmode='group',
                xaxis_title='Month',
                yaxis_title='Amount (₹)',
                hovermode='x unified'
            )
            st.plotly_chart(fig)

            # 2. Category-wise Analysis
            st.subheader("Expense Distribution by Category")
            category_data = df[df['type'] == 'debit'].groupby('category')['amount'].sum()
            
            if not category_data.empty:
                fig = px.pie(
                    values=category_data.values,
                    names=category_data.index,
                    title='Expense Distribution'
                )
                st.plotly_chart(fig)
                
                # Category-wise table
                st.subheader("Category-wise Breakdown")
                category_df = pd.DataFrame({
                    'Category': category_data.index,
                    'Total Expenses': category_data.values,
                    'Percentage': (category_data.values / category_data.sum() * 100)
                })
                category_df['Total Expenses'] = category_df['Total Expenses'].apply(
                    lambda x: f"₹{x:,.2f}"
                )
                category_df['Percentage'] = category_df['Percentage'].apply(
                    lambda x: f"{x:.1f}%"
                )
                st.dataframe(category_df)

            # 3. Daily Trend Analysis
            st.subheader("Daily Transaction Trend")
            daily_data = df.groupby(['date', 'type'])['amount'].sum().unstack().fillna(0)
            
            fig = go.Figure()
            if 'debit' in daily_data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=daily_data.index,
                        y=daily_data['debit'],
                        name='Expenses',
                        line=dict(color='#ff6b6b')
                    )
                )
            if 'credit' in daily_data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=daily_data.index,
                        y=daily_data['credit'],
                        name='Income',
                        line=dict(color='#51cf66')
                    )
                )
                
            fig.update_layout(
                title='Daily Transaction Trend',
                xaxis_title='Date',
                yaxis_title='Amount (₹)',
                hovermode='x unified'
            )
            st.plotly_chart(fig)

            # 4. Balance Trend
            st.subheader("Balance Trend")
            balance_data = df.sort_values('date')[['date', 'balance']].drop_duplicates('date')
            
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=balance_data['date'],
                    y=balance_data['balance'],
                    mode='lines+markers',
                    name='Balance',
                    line=dict(color='#339af0')
                )
            )
            
            fig.update_layout(
                title='Balance Trend Over Time',
                xaxis_title='Date',
                yaxis_title='Balance (₹)',
                hovermode='x unified'
            )
            st.plotly_chart(fig)

            # 5. Key Statistics
            st.subheader("Key Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_daily_expense = df[df['type'] == 'debit']['amount'].mean()
                st.metric(
                    "Average Daily Expense",
                    f"₹{avg_daily_expense:,.2f}"
                )
                
            with col2:
                total_inflow = df[df['type'] == 'credit']['amount'].sum()
                total_outflow = df[df['type'] == 'debit']['amount'].sum()
                net_flow = total_inflow - total_outflow
                st.metric(
                    "Net Cash Flow",
                    f"₹{net_flow:,.2f}",
                    delta=f"₹{abs(net_flow):,.2f}",
                    delta_color="normal" if net_flow >= 0 else "inverse"
                )
                
            with col3:
                transaction_count = len(df)
                st.metric(
                    "Total Transactions",
                    f"{transaction_count:,}"
                )

        except Exception as e:
            st.error(f"Error generating analytics: {str(e)}")
    
# Main entry point
if __name__ == "__main__":
    app = BudgetTrackerUI()
    app.run()