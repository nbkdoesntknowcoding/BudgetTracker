import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path
import calendar

class FinancialManager:
    def __init__(self):
        # Initialize data storage
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Define file paths
        self.departments_file = self.data_dir / "departments.json"
        self.expenses_file = self.data_dir / "expenses.csv"
        self.budgets_file = self.data_dir / "budgets.json"
        self.finances_file = self.data_dir / "finances.json"
        
        self.load_data()

    def load_data(self):
        """Load existing data or create new files with error handling"""
        # Load departments
        try:
            if self.departments_file.exists():
                with open(self.departments_file, 'r') as f:
                    content = f.read()
                    self.departments = json.loads(content) if content.strip() else {}
            else:
                self.departments = {}
            self.save_departments()
        except (json.JSONDecodeError, FileNotFoundError):
            self.departments = {}
            self.save_departments()

        # Load expenses
        try:
            if self.expenses_file.exists():
                self.expenses_df = pd.read_csv(self.expenses_file)
            else:
                self.expenses_df = pd.DataFrame(columns=[
                    'date', 'department', 'category', 'amount', 'description', 'submitted_by'
                ])
            self.save_expenses()
        except pd.errors.EmptyDataError:
            self.expenses_df = pd.DataFrame(columns=[
                'date', 'department', 'category', 'amount', 'description', 'submitted_by'
            ])
            self.save_expenses()

        # Load budgets
        try:
            if self.budgets_file.exists():
                with open(self.budgets_file, 'r') as f:
                    content = f.read()
                    self.budgets = json.loads(content) if content.strip() else {}
            else:
                self.budgets = {}
            self.save_budgets()
        except (json.JSONDecodeError, FileNotFoundError):
            self.budgets = {}
            self.save_budgets()

        # Load financial data
        try:
            if self.finances_file.exists():
                with open(self.finances_file, 'r') as f:
                    content = f.read()
                    self.finances = json.loads(content) if content.strip() else {
                        'cash_balance': 0,
                        'revenue_streams': {},
                        'fixed_costs': {},
                        'growth_rate': 0
                    }
            else:
                self.finances = {
                    'cash_balance': 0,
                    'revenue_streams': {},
                    'fixed_costs': {},
                    'growth_rate': 0
                }
            self.save_finances()
        except (json.JSONDecodeError, FileNotFoundError):
            self.finances = {
                'cash_balance': 0,
                'revenue_streams': {},
                'fixed_costs': {},
                'growth_rate': 0
            }
            self.save_finances()

    def save_departments(self):
        with open(self.departments_file, 'w') as f:
            json.dump(self.departments, f)

    def save_expenses(self):
        self.expenses_df.to_csv(self.expenses_file, index=False)

    def save_budgets(self):
        with open(self.budgets_file, 'w') as f:
            json.dump(self.budgets, f)

    def save_finances(self):
        with open(self.finances_file, 'w') as f:
            json.dump(self.finances, f)

    def update_cash_balance(self, amount):
        """Update company's cash balance"""
        self.finances['cash_balance'] = amount
        self.save_finances()

    def add_revenue_stream(self, name, amount, recurring=True):
        """Add or update a revenue stream"""
        self.finances['revenue_streams'][name] = {
            'amount': amount,
            'recurring': recurring
        }
        self.save_finances()

    def add_fixed_cost(self, name, amount):
        """Add or update a fixed cost"""
        self.finances['fixed_costs'][name] = amount
        self.save_finances()

    def set_growth_rate(self, rate):
        """Set monthly growth rate expectation"""
        self.finances['growth_rate'] = rate
        self.save_finances()

    def calculate_runway(self):
        """Calculate company's runway based on current finances"""
        monthly_revenue = sum(stream['amount'] for stream in self.finances['revenue_streams'].values() if stream['recurring'])
        monthly_fixed_costs = sum(self.finances['fixed_costs'].values())
        
        # Get average monthly variable costs from expenses
        if not self.expenses_df.empty:
            recent_months = 3
            self.expenses_df['date'] = pd.to_datetime(self.expenses_df['date'])
            recent_expenses = self.expenses_df[
                self.expenses_df['date'] > datetime.now() - timedelta(days=30 * recent_months)
            ]
            monthly_variable_costs = recent_expenses['amount'].sum() / recent_months
        else:
            monthly_variable_costs = 0

        total_monthly_costs = monthly_fixed_costs + monthly_variable_costs
        monthly_burn = total_monthly_costs - monthly_revenue
        
        if monthly_burn <= 0:
            return float('inf')  # Company is profitable
        
        runway_months = self.finances['cash_balance'] / monthly_burn
        return runway_months

    def calculate_financial_metrics(self):
        """Calculate key financial metrics"""
        monthly_revenue = sum(stream['amount'] for stream in self.finances['revenue_streams'].values() if stream['recurring'])
        monthly_fixed_costs = sum(self.finances['fixed_costs'].values())
        
        # Calculate average monthly expenses
        if not self.expenses_df.empty:
            recent_months = 3
            self.expenses_df['date'] = pd.to_datetime(self.expenses_df['date'])
            recent_expenses = self.expenses_df[
                self.expenses_df['date'] > datetime.now() - timedelta(days=30 * recent_months)
            ]
            monthly_variable_costs = recent_expenses['amount'].sum() / recent_months
        else:
            monthly_variable_costs = 0

        total_monthly_costs = monthly_fixed_costs + monthly_variable_costs
        
        return {
            'monthly_revenue': monthly_revenue,
            'monthly_fixed_costs': monthly_fixed_costs,
            'monthly_variable_costs': monthly_variable_costs,
            'total_monthly_costs': total_monthly_costs,
            'monthly_profit': monthly_revenue - total_monthly_costs,
            'runway_months': self.calculate_runway(),
            'cash_balance': self.finances['cash_balance']
        }

def main():
    st.set_page_config(page_title="Company Financial Manager", layout="wide")
    st.title("Company Financial Manager")
    
    # Initialize the financial manager
    financial_manager = FinancialManager()
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Select Page",
        ["Financial Overview", "Department Management", "Expense Entry", "Budget Setting", "Revenue & Costs", "Financial Projections"]
    )
    
    if page == "Financial Overview":
        st.header("Financial Overview")
        
        # Display key metrics
        metrics = financial_manager.calculate_financial_metrics()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cash Balance", f"${metrics['cash_balance']:,.2f}")
            st.metric("Monthly Revenue", f"${metrics['monthly_revenue']:,.2f}")
        with col2:
            st.metric("Monthly Costs", f"${metrics['total_monthly_costs']:,.2f}")
            st.metric("Monthly Profit", f"${metrics['monthly_profit']:,.2f}")
        with col3:
            runway = metrics['runway_months']
            runway_text = f"{runway:.1f} months" if runway != float('inf') else "∞ (Profitable)"
            st.metric("Runway", runway_text)
        
        # Financial health indicators
        st.subheader("Financial Health Indicators")
        
        # Burn rate chart
        monthly_data = []
        for i in range(-6, 1):  # Last 6 months
            date = datetime.now() + timedelta(days=30 * i)
            expenses = financial_manager.expenses_df[
                pd.to_datetime(financial_manager.expenses_df['date']).dt.month == date.month
            ]['amount'].sum()
            monthly_data.append({
                'month': date.strftime('%B %Y'),
                'expenses': expenses
            })
        
        burn_df = pd.DataFrame(monthly_data)
        fig = px.bar(burn_df, x='month', y='expenses', title="Monthly Burn Rate")
        st.plotly_chart(fig)
        
        # Department expenses breakdown
        st.subheader("Department Expenses Breakdown")
        dept_expenses = financial_manager.expenses_df.groupby('department')['amount'].sum()
        fig = px.pie(values=dept_expenses.values, names=dept_expenses.index, title="Expenses by Department")
        st.plotly_chart(fig)

    elif page == "Revenue & Costs":
        st.header("Revenue & Costs Management")
        
        # Cash balance update
        st.subheader("Update Cash Balance")
        with st.form("cash_balance_form"):
            new_balance = st.number_input("Current Cash Balance ($)", 
                                        value=financial_manager.finances['cash_balance'],
                                        min_value=0.0, 
                                        step=1000.0)
            if st.form_submit_button("Update Cash Balance"):
                financial_manager.update_cash_balance(new_balance)
                st.success("Cash balance updated successfully!")
        
        # Revenue streams
        st.subheader("Revenue Streams")
        with st.form("revenue_stream_form"):
            stream_name = st.text_input("Revenue Stream Name")
            stream_amount = st.number_input("Monthly Amount ($)", min_value=0.0, step=100.0)
            recurring = st.checkbox("Recurring Revenue", value=True)
            if st.form_submit_button("Add/Update Revenue Stream"):
                financial_manager.add_revenue_stream(stream_name, stream_amount, recurring)
                st.success("Revenue stream updated successfully!")
        
        # Display current revenue streams
        if financial_manager.finances['revenue_streams']:
            st.write("Current Revenue Streams:")
            revenue_data = []
            for name, details in financial_manager.finances['revenue_streams'].items():
                revenue_data.append({
                    'Stream': name,
                    'Amount': details['amount'],
                    'Type': 'Recurring' if details['recurring'] else 'One-time'
                })
            st.dataframe(pd.DataFrame(revenue_data))
        
        # Fixed costs
        st.subheader("Fixed Costs")
        with st.form("fixed_cost_form"):
            cost_name = st.text_input("Fixed Cost Name")
            cost_amount = st.number_input("Monthly Amount ($)", min_value=0.0, step=100.0)
            if st.form_submit_button("Add/Update Fixed Cost"):
                financial_manager.add_fixed_cost(cost_name, cost_amount)
                st.success("Fixed cost updated successfully!")
        
        # Display current fixed costs
        if financial_manager.finances['fixed_costs']:
            st.write("Current Fixed Costs:")
            cost_data = []
            for name, amount in financial_manager.finances['fixed_costs'].items():
                cost_data.append({
                    'Cost': name,
                    'Amount': amount
                })
            st.dataframe(pd.DataFrame(cost_data))

    elif page == "Financial Projections":
        st.header("Financial Projections")
        
        # Growth rate setting
        with st.form("growth_rate_form"):
            growth_rate = st.number_input(
                "Expected Monthly Growth Rate (%)", 
                value=financial_manager.finances['growth_rate'],
                min_value=-100.0,
                max_value=1000.0,
                step=0.1
            )
            if st.form_submit_button("Update Growth Rate"):
                financial_manager.set_growth_rate(growth_rate)
                st.success("Growth rate updated successfully!")
        
        # Financial projections
        st.subheader("12-Month Projections")
        metrics = financial_manager.calculate_financial_metrics()
        
        projection_data = []
        current_revenue = metrics['monthly_revenue']
        current_costs = metrics['total_monthly_costs']
        cash_balance = metrics['cash_balance']
        
        for i in range(12):
            month = (datetime.now() + timedelta(days=30 * i)).strftime('%B %Y')
            current_revenue *= (1 + growth_rate/100)
            
            projection_data.append({
                'Month': month,
                'Revenue': current_revenue,
                'Costs': current_costs,
                'Profit': current_revenue - current_costs,
                'Cash Balance': cash_balance + (current_revenue - current_costs)
            })
            
            cash_balance += (current_revenue - current_costs)
        
        df_projection = pd.DataFrame(projection_data)
        
        # Create projection charts
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_projection['Month'], y=df_projection['Revenue'],
                                mode='lines+markers', name='Revenue'))
        fig.add_trace(go.Scatter(x=df_projection['Month'], y=df_projection['Costs'],
                                mode='lines+markers', name='Costs'))
        fig.add_trace(go.Scatter(x=df_projection['Month'], y=df_projection['Cash Balance'],
                                mode='lines+markers', name='Cash Balance'))
        fig.update_layout(title="12-Month Financial Projection")
        st.plotly_chart(fig)
        
        # Display projection data
        st.write("Detailed Projections:")
        st.dataframe(df_projection.round(2))

    elif page == "Department Management":
        st.header("Department Management")
        
        # Add new department
        with st.form("new_department"):
            dept_name = st.text_input("Department Name")
            categories = st.text_input("Expense Categories (comma-separated)")
            submit_dept = st.form_submit_button("Add Department")
            
            if submit_dept and dept_name and categories:
                financial_manager.departments[dept_name] = [cat.strip() for cat in categories.split(',')]
                financial_manager.save_departments()
                st.success(f"Department {dept_name} added successfully!")
        
        # Display existing departments
        st.subheader("Existing Departments")
        for dept, cats in financial_manager.departments.items():
            st.write(f"**{dept}**")
            st.write("Categories:", ", ".join(cats))
            if st.button(f"Delete {dept}"):
                del financial_manager.departments[dept]
                financial_manager.save_departments()
                st.success(f"Department {dept} deleted successfully!")
                st.rerun()

    elif page == "Expense Entry":
        st.header("Expense Entry")
        
        # Expense entry form
        with st.form("expense_entry"):
            col1, col2 = st.columns(2)
            
            with col1:
                department = st.selectbox(
                    "Department",
                    options=list(financial_manager.departments.keys())
                )
                
                category = st.selectbox(
                    "Category",
                    options=financial_manager.departments.get(department, []) if department else []
                )
                
                date = st.date_input("Date", value=datetime.now())
                
            with col2:
                amount = st.number_input("Amount ($)", min_value=0.0, step=0.01)
                description = st.text_area("Description")
                submitted_by = st.text_input("Submitted By")
            
            submit_expense = st.form_submit_button("Submit Expense")
            
            if submit_expense and department and category:
                # Add expense to DataFrame
                new_expense = pd.DataFrame({
                    'date': [date.strftime('%Y-%m-%d')],
                    'department': [department],
                    'category': [category],
                    'amount': [amount],
                    'description': [description],
                    'submitted_by': [submitted_by]
                })
                
                financial_manager.expenses_df = pd.concat(
                    [financial_manager.expenses_df, new_expense],
                    ignore_index=True
                )
                financial_manager.save_expenses()
                st.success("Expense recorded successfully!")

        # Display recent expenses
        st.subheader("Recent Expenses")
        if not financial_manager.expenses_df.empty:
            recent_expenses = financial_manager.expenses_df.sort_values(
                'date', ascending=False
            ).head(10)
            st.dataframe(recent_expenses)
            
            # Download expenses
            csv = financial_manager.expenses_df.to_csv(index=False)
            st.download_button(
                "Download All Expenses",
                csv,
                "company_expenses.csv",
                "text/csv",
                key='download-csv'
            )

    elif page == "Budget Setting":
        st.header("Budget Setting")
        
        tab1, tab2 = st.tabs(["Set Budgets", "View Budgets"])
        
        with tab1:
            with st.form("budget_setting"):
                col1, col2 = st.columns(2)
                
                with col1:
                    dept = st.selectbox("Department", list(financial_manager.departments.keys()))
                    if dept:
                        category = st.selectbox("Category", financial_manager.departments[dept])
                    
                with col2:
                    year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)
                    month = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
                    amount = st.number_input("Budget Amount ($)", min_value=0.0, step=100.0)
                
                submit_budget = st.form_submit_button("Set Budget")
                
                if submit_budget and dept and category:
                    if dept not in financial_manager.budgets:
                        financial_manager.budgets[dept] = {}
                    
                    period = f"{year}-{month:02d}"
                    if period not in financial_manager.budgets[dept]:
                        financial_manager.budgets[dept][period] = {}
                    
                    financial_manager.budgets[dept][period][category] = amount
                    financial_manager.save_budgets()
                    st.success("Budget set successfully!")
        
        with tab2:
            # Display current budgets vs actuals
            if financial_manager.budgets:
                st.subheader("Budget vs Actual Expenses")
                
                dept = st.selectbox(
                    "Select Department",
                    options=list(financial_manager.departments.keys()),
                    key="budget_view_dept"
                )
                
                year = st.number_input(
                    "Select Year",
                    min_value=2020,
                    max_value=2030,
                    value=datetime.now().year,
                    key="budget_view_year"
                )
                
                month = st.selectbox(
                    "Select Month",
                    range(1, 13),
                    index=datetime.now().month - 1,
                    key="budget_view_month"
                )
                
                if dept:
                    period = f"{year}-{month:02d}"
                    
                    # Get budgets for selected period
                    dept_budgets = financial_manager.budgets.get(dept, {}).get(period, {})
                    
                    # Get actual expenses
                    mask = (
                        (financial_manager.expenses_df['department'] == dept) &
                        (pd.to_datetime(financial_manager.expenses_df['date']).dt.year == year) &
                        (pd.to_datetime(financial_manager.expenses_df['date']).dt.month == month)
                    )
                    actual_expenses = financial_manager.expenses_df[mask].groupby('category')['amount'].sum()
                    
                    # Create comparison dataframe
                    comparison_data = []
                    for category in financial_manager.departments[dept]:
                        budget = dept_budgets.get(category, 0)
                        actual = actual_expenses.get(category, 0)
                        
                        comparison_data.append({
                            'Category': category,
                            'Budget': budget,
                            'Actual': actual,
                            'Variance': budget - actual,
                            'Variance %': ((budget - actual) / budget * 100) if budget > 0 else 0
                        })
                    
                    df_comparison = pd.DataFrame(comparison_data)
                    
                    # Display comparison
                    st.dataframe(df_comparison.style.format({
                        'Budget': '${:,.2f}',
                        'Actual': '${:,.2f}',
                        'Variance': '${:,.2f}',
                        'Variance %': '{:.1f}%'
                    }))
                    
                    # Create budget vs actual chart
                    fig = go.Figure(data=[
                        go.Bar(name='Budget', x=df_comparison['Category'], y=df_comparison['Budget']),
                        go.Bar(name='Actual', x=df_comparison['Category'], y=df_comparison['Actual'])
                    ])
                    fig.update_layout(
                        title=f"Budget vs Actual - {calendar.month_name[month]} {year}",
                        barmode='group'
                    )
                    st.plotly_chart(fig)

if __name__ == "__main__":
    main()