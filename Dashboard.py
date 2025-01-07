import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import json
from login import login_form, logout

# Configure page
st.set_page_config(
    page_title="Acolyte CXO Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check authentication
if not st.session_state.get('authenticated', False):
    st.title("Acolyte CXO Dashboard")
    login_form()
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        **Logged in as:**  
        {st.session_state.user_name}  
        {st.session_state.user_email}
        """)
        
        if st.button("Logout"):
            logout()
    st.title("Welcome to Acolyte CXO Dashboard")
    # ... rest of your dashboard code ...
    # Helper functions
    def format_indian_currency(amount):
        """Convert number to Indian currency format with lakhs and crores"""
        if amount >= 10000000:  # 1 Crore
            return f"₹{amount/10000000:.2f}Cr"
        elif amount >= 100000:  # 1 Lakh
            return f"₹{amount/100000:.2f}L"
        elif amount >= 1000:    # 1 Thousand
            return f"₹{amount/1000:.2f}"
        else:
            return f"₹{amount:.2f}"

    def calculate_burn_rate():
        total_q1 = sum(st.session_state.financial_data['budget']['Q1_2025'].values())
        return total_q1 / 90  # Daily burn rate for Q1

    def calculate_runway(total_funding=2500000):  # 25L F&F round
        daily_burn = calculate_burn_rate()
        return total_funding / daily_burn if daily_burn > 0 else 0

    def calculate_runway_with_buffer(total_funding=2500000, buffer=500000):
        """Calculate runway considering minimum buffer"""
        usable_funding = total_funding - buffer
        daily_burn = calculate_burn_rate()
        return usable_funding / daily_burn if daily_burn > 0 else 0

    def calculate_cac():
        try:
            total_spent = sum(st.session_state.financial_data['budget']['Q1_2025'].values())
            total_users = (st.session_state.financial_data['users']['institutional'] + 
                        st.session_state.financial_data['users']['digital'])
            return total_spent / total_users if total_users > 0 else 0
        except Exception:
            return 0
    def create_growth_trajectory_data():
        dates = pd.date_range(start='2025-01-01', end='2025-03-31', freq='D')
        
        # Weekly target calculation
        weekly_targets = []
        current_trajectory = []
        base_weekly_increment = 20  # Starting with 20 users per week
        
        cumulative_users = 0
        for i, date in enumerate(dates):
            week = (date - datetime(2025, 1, 1)).days // 7
            
            # Weekly target increases over time
            if week < 4:
                target = 20
            elif week < 8:
                target = 30
            else:
                target = 40
                
            weekly_targets.append(target)
            
            # Create stepped growth for current trajectory
            if i % 7 == 0:  # At the start of each week
                cumulative_users += target
            current_trajectory.append(cumulative_users)
        
        return pd.DataFrame({
            'Date': dates,
            'Weekly_Target': [20] * len(dates),  # Constant target line
            'Current_Trajectory': current_trajectory,
            'First_Buffer': [175] * len(dates),
            'Second_Buffer': [250] * len(dates)
        })

    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = {
            'budget': {
                'Q1_2025': {
                    'developer_costs': 150000,
                    'marketing_spends': 150000,
                    'aws_ai_model': 74700,
                    'aws_other': 50000,
                    'sales_budget': 160000,
                    'variable_costs': 40300
                },
                'Q2_2025': {
                    'developer_costs': 300000,
                    'marketing_spends': 300000,
                    'aws_ai_model': 149400,
                    'aws_other': 100000,
                    'sales_budget': 320000,
                    'variable_costs': 80600
                }
            },
            'users': {
                'institutional': 0,
                'digital': 0,
                'weekly_targets': {
                    'week1-4': 20,
                    'week5-8': 30,
                    'week9-12': 40
                }
            },
            'partnerships': {
                'active': 0,
                'pipeline': [],
                'total_potential_users': 0
            },
            'metrics': {
                'cac': 0,
                'burn_rate': 0,
                'runway_days': 0,
                'institutional_cac': 827,
                'digital_cac': 3720
            }
        }

    # Navigation
    pages = ['Dashboard Overview', 'Financial Strategy', 'Partnership Tracker', 'User Analytics','Financial Projections','Investor Dashboard','Cap Table']
    page = st.sidebar.radio('Navigation', pages)

    if page == 'Dashboard Overview':
        st.title('Acolyte CXO Dashboard')
        
        # Top KPI Cards with Enhanced Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        burn_rate = calculate_burn_rate()
        runway = calculate_runway()
        runway_with_buffer = calculate_runway_with_buffer()
        cac = calculate_cac()
        total_users = (st.session_state.financial_data['users']['institutional'] + 
                    st.session_state.financial_data['users']['digital'])
        
        with col1:
            st.metric(
                "Daily Burn Rate(In Thousands)",
                format_indian_currency(burn_rate),
                f"{runway:.0f} days runway"
            )
            st.caption(f"Buffer Adjusted: {runway_with_buffer:.0f} days")
        
        with col2:
            st.metric(
                "Total Users",
                f"{total_users}",
                f"Target: {st.session_state.financial_data['users']['weekly_targets']['week1-4']} weekly"
            )
            st.caption(f"CAC: {format_indian_currency(cac)}")
        
        with col3:
            active_partnerships = st.session_state.financial_data['partnerships']['active']
            st.metric(
                "Active Partnerships",
                f"{active_partnerships}",  # Display just the number
                "Target: 15-20"
            )
            # Add pipeline info as caption if needed
            pipeline_count = len(st.session_state.financial_data['partnerships']['pipeline'])
            st.caption(f"Pipeline: {pipeline_count} opportunities")
        
        with col4:
            total_budget = 2500000  # 25L F&F round
            used_budget = sum(st.session_state.financial_data['budget']['Q1_2025'].values())
            utilization = (used_budget/total_budget)*100
            st.metric(
                "Budget Utilization",
                f"{utilization:.1f}%",
                format_indian_currency(total_budget - used_budget) + " remaining"
            )

    # Budget Overview in Dashboard Overview page
        st.header("Budget Overview")
        col1, col2 = st.columns(2)
        
        with col1:
            # Current Q1 Budget Pie Chart
            current_budget = st.session_state.financial_data['budget']['Q1_2025']
            budget_df = pd.DataFrame({
                'Category': current_budget.keys(),
                'Amount': current_budget.values(),
                'Percentage': [v/sum(current_budget.values())*100 for v in current_budget.values()]
            })
            budget_df['Amount_Formatted'] = budget_df['Amount'].apply(format_indian_currency)
            
            fig = px.pie(budget_df, values='Amount', names='Category',
                        title='Q1 2025 Budget Distribution')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show detailed breakdown
            st.dataframe(budget_df[['Category', 'Amount_Formatted', 'Percentage']].style.format({
                'Percentage': '{:.1f}%'
            }))
        
        with col2:
            # Budget Utilization Gauge
            total_budget = 2500000  # 25L F&F round
            used_budget = sum(current_budget.values())
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = (used_budget/total_budget)*100,
                title = {'text': f"Budget Utilization"},
                delta = {'reference': 80},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 80
                    },
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"},
                        {'range': [80, 100], 'color': "red"}
                    ]
                }
            ))
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            # Key metrics
            st.metric("Total Budget", format_indian_currency(total_budget))
            st.metric("Used Budget", format_indian_currency(used_budget))
            st.metric("Remaining Budget", format_indian_currency(total_budget - used_budget))

                
        # Additional Budget Analysis
        st.header("Additional Budget Analysis")
        
        # Risk Analysis
        st.subheader("Risk Analysis")
        risk_col1, risk_col2 = st.columns(2)
        
        with risk_col1:
            st.metric("Expected Monthly Burn Q2", "₹4.17L")
            st.metric("Best Case Burn", "₹3.75L", "-10%")
            st.metric("Worst Case Burn", "₹4.58L", "+10%")
        
        with risk_col2:
            st.metric("Expected Runway", "7 months")
            st.metric("Best Case Runway", "8 months", "+1 month")
            st.metric("Worst Case Runway", "6 months", "-1 month")

        # Seed Round Allocation
        st.subheader("Seed Round Allocation Plan")
        seed_col1, seed_col2, seed_col3 = st.columns(3)
        
        with seed_col1:
            st.metric("Product Development", "₹2.00Cr", "40%")
        with seed_col2:
            st.metric("Market Expansion", "₹1.75Cr", "35%")
        with seed_col3:
            st.metric("Operations", "₹1.25Cr", "25%")

        # Budget Control Triggers
        st.subheader("Budget Control Triggers")
        trigger_data = pd.DataFrame({
            'Trigger Level': ['Warning', 'Critical Review', 'Emergency Measures'],
            'Monthly Spend': ['110%', '120%', '130%'],
            'Action Required': [
                'Review and Optimize',
                'Freeze Non-Essential Spending',
                'Implement Emergency Measures'
            ]
        })
        st.dataframe(trigger_data)

        # User Growth Analysis
        st.header("User Growth Analysis")
        growth_tab1, growth_tab2 = st.tabs(["Growth Trajectory", "Channel Analysis"])
        
        with growth_tab1:
            growth_data = create_growth_trajectory_data()
            
            fig = go.Figure()
            
            # Add weekly target line
            fig.add_trace(go.Scatter(
                x=growth_data['Date'],
                y=growth_data['Weekly_Target'],
                name='Weekly Target',
                line=dict(color='blue', width=1)
            ))
            
            # Add current trajectory
            fig.add_trace(go.Scatter(
                x=growth_data['Date'],
                y=growth_data['Current_Trajectory'],
                name='Current Trajectory',
                line=dict(color='lightblue', width=2)
            ))
            
            # Add buffer release lines
            fig.add_hline(y=175, line_dash="dash", 
                        annotation_text="First Buffer Release",
                        line_color="gray")
            fig.add_hline(y=250, line_dash="dash", 
                        annotation_text="Second Buffer Release",
                        line_color="gray")
            
            fig.update_layout(
                title='User Growth vs Target',
                xaxis_title='Date',
                yaxis_title='Users',
                yaxis_range=[0, 500],
                showlegend=True,
                template="plotly_dark"
            )
            
            st.plotly_chart(fig, use_container_width=True)

    elif page == 'Financial Strategy':
        st.title('Financial Strategy')
        
        # F&F Round Overview
        st.header("Friends & Family Round (Q1 2025)")
        ff_col1, ff_col2, ff_col3 = st.columns(3)
        
        with ff_col1:
            st.metric("Target Raise", "₹25L", "5% Equity")
            st.metric("Pre-money Valuation", "₹5Cr", None)
            
        with ff_col2:
            st.metric("Confirmed Investment", "₹12-15L", "As of Nov 2024")
            st.metric("Round Timeline", "Dec 15 - Jan 5", "2024-25")
            
        with ff_col3:
            st.metric("Minimum Investment", "₹50K", "Per Investor")
            st.metric("Buffer Reserve", "₹5L", "20% of Round")

        # Budget Analysis
        st.header("Budget Analysis")
        budget_tabs = st.tabs(["Current Budget", "Quarter Comparison", "Projections","Cap Table & Dilution"])
        with budget_tabs[0]:  # Current Budget
            col1, col2 = st.columns(2)
            
            with col1:
                # Current Q1 Budget Pie Chart
                current_budget = st.session_state.financial_data['budget']['Q1_2025']
                budget_df = pd.DataFrame({
                    'Category': current_budget.keys(),
                    'Amount': current_budget.values(),
                    'Percentage': [v/sum(current_budget.values())*100 for v in current_budget.values()]
                })
                budget_df['Amount_Formatted'] = budget_df['Amount'].apply(format_indian_currency)
                
                fig = px.pie(budget_df, values='Amount', names='Category',
                            title='Q1 2025 Budget Distribution')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                # Show detailed breakdown
                st.dataframe(budget_df[['Category', 'Amount_Formatted', 'Percentage']].style.format({
                    'Percentage': '{:.1f}%'
                }))
            
            with col2:
                # Budget Utilization Gauge
                total_budget = 2500000  # 25L F&F round
                used_budget = sum(current_budget.values())
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = (used_budget/total_budget)*100,
                    title = {'text': f"Budget Utilization"},
                    delta = {'reference': 80},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 80
                        },
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "gray"},
                            {'range': [80, 100], 'color': "red"}
                        ]
                    }
                ))
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                # Key metrics
                st.metric("Total Budget", format_indian_currency(total_budget))
                st.metric("Used Budget", format_indian_currency(used_budget))
                st.metric("Remaining Budget", format_indian_currency(total_budget - used_budget))

        with budget_tabs[1]:  # Quarter Comparison
            st.subheader("Q1 vs Q2 Comparison")
            
            q1_budget = st.session_state.financial_data['budget']['Q1_2025']
            q2_budget = st.session_state.financial_data['budget']['Q2_2025']
            
            comparison_df = pd.DataFrame({
                'Category': q1_budget.keys(),
                'Q1_Amount': q1_budget.values(),
                'Q2_Amount': q2_budget.values()
            })
            comparison_df['Growth'] = ((comparison_df['Q2_Amount'] - comparison_df['Q1_Amount']) / 
                                    comparison_df['Q1_Amount'] * 100)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart comparison
                fig = px.bar(comparison_df, x='Category',
                            y=['Q1_Amount', 'Q2_Amount'],
                            title='Quarter-over-Quarter Comparison',
                            barmode='group')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Growth metrics
                for idx, row in comparison_df.iterrows():
                    st.metric(
                        row['Category'].replace('_', ' ').title(),
                        format_indian_currency(row['Q2_Amount']),
                        f"{row['Growth']:+.1f}%"
                    )

        with budget_tabs[2]:  # Projections
            col1, col2 = st.columns(2)
            
            with col1:
                # Q2 Projected Budget Distribution
                q2_df = pd.DataFrame({
                    'Category': q2_budget.keys(),
                    'Amount': q2_budget.values(),
                    'Percentage': [v/sum(q2_budget.values())*100 for v in q2_budget.values()]
                })
                
                fig = px.pie(q2_df, values='Amount', names='Category',
                            title='Q2 2025 Projected Budget Distribution')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Quarter-over-Quarter comparison
                fig = px.bar(comparison_df, x='Category',
                            y=['Q1_Amount', 'Q2_Amount'],
                            title='Budget Growth Comparison',
                            barmode='group')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

            # Budget Growth Analysis
            st.subheader("Budget Growth Analysis")
            growth_df = comparison_df.copy()
            growth_df['Q1_Amount'] = growth_df['Q1_Amount'].apply(format_indian_currency)
            growth_df['Q2_Amount'] = growth_df['Q2_Amount'].apply(format_indian_currency)
            growth_df['Growth'] = growth_df['Growth'].apply(lambda x: f"{x:+.1f}%")
            st.dataframe(growth_df)

            # Key Budget Insights
            st.subheader("Key Budget Insights")
            insight_col1, insight_col2 = st.columns(2)
            
            with insight_col1:
                q1_total = sum(q1_budget.values())
                q2_total = sum(q2_budget.values())
                st.metric("Q1 Total Budget", format_indian_currency(q1_total))
                st.metric("Q2 Projected Budget", format_indian_currency(q2_total),
                        f"{((q2_total-q1_total)/q1_total)*100:+.1f}%")
            
            with insight_col2:
                st.metric("Monthly Burn Q1", format_indian_currency(q1_total/3))
                st.metric("Projected Monthly Burn Q2", format_indian_currency(q2_total/3),
                        f"{((q2_total-q1_total)/q1_total)*100:+.1f}%")
                
        with budget_tabs[3]:  # Cap Table & Dilution
            st.header("Cap Table & Dilution Analysis")
        
        # Define cap table data structure
        cap_table_data = {
            'initial': {
                'valuation': 10000,  # Initial 1000 shares at ₹10
                'share_value': 10,
                'shareholders': {
                    'Nischay BK': {'shares': 500, 'type': 'Ordinary'},
                    'Subha': {'shares': 500, 'type': 'Ordinary'}
                }
            },
            'post_team': {
                'valuation': 16650,  # 1665 shares at ₹10
                'share_value': 10,
                'shareholders': {
                    'Nischay BK': {'shares': 500, 'type': 'Ordinary'},
                    'Subha': {'shares': 500, 'type': 'Ordinary'},
                    'Boppl Pvt Ltd': {'shares': 416, 'type': 'Ordinary'},
                    'Ayesha': {'shares': 83, 'type': 'Ordinary'},
                    'Jason': {'shares': 83, 'type': 'Ordinary'},
                    'Varun': {'shares': 83, 'type': 'Ordinary'}
                }
            },
            'post_ff': {
                'valuation': 2500000,  # F&F round of 25L
                'share_value': 28409,  # 25L/88 new shares
                'shareholders': {
                    'Nischay BK': {'shares': 500, 'type': 'Ordinary'},
                    'Subha': {'shares': 500, 'type': 'Ordinary'},
                    'Boppl Pvt Ltd': {'shares': 416, 'type': 'Ordinary'},
                    'Ayesha': {'shares': 83, 'type': 'Ordinary'},
                    'Jason': {'shares': 83, 'type': 'Ordinary'},
                    'Varun': {'shares': 83, 'type': 'Ordinary'},
                    'F&F Investors': {'shares': 88, 'type': 'Preferred'}
                }
            },
            'post_seed': {
                'valuation': 50000000,  # 5Cr investment for 10%
                'share_value': 256410,  # 5Cr/195 new shares
                'shareholders': {
                    'Nischay BK': {'shares': 500, 'type': 'Ordinary'},
                    'Subha': {'shares': 500, 'type': 'Ordinary'},
                    'Boppl Pvt Ltd': {'shares': 416, 'type': 'Ordinary'},
                    'Ayesha': {'shares': 83, 'type': 'Ordinary'},
                    'Jason': {'shares': 83, 'type': 'Ordinary'},
                    'Varun': {'shares': 83, 'type': 'Ordinary'},
                    'F&F Investors': {'shares': 88, 'type': 'Preferred'},
                    'VC Investment': {'shares': 195, 'type': 'Preferred'}
                }
            }
        }

        
        # Function to calculate ownership percentages and values
        def calculate_cap_table_metrics(round_data):
            total_shares = sum(shareholder['shares'] for shareholder in round_data['shareholders'].values())
            metrics = []
            
            for name, data in round_data['shareholders'].items():
                current_shares = data['shares']
                percentage = (current_shares / total_shares) * 100
                value = current_shares * round_data['share_value']
                fully_diluted_value = value if round_data['valuation'] >= 2500000 else value * (2500000 / round_data['valuation'])
                
                metrics.append({
                    'Shareholder': name,
                    'Shares': current_shares,
                    'Type': data['type'],
                    'Percentage': percentage,
                    'Current Value': value,
                    'Fully Diluted Value': fully_diluted_value if name not in ['F&F Investors', 'VC Investment'] else value
                })
            
            metrics_df = pd.DataFrame(metrics)
            metrics_df = metrics_df.sort_values('Shares', ascending=False)
            return metrics_df
        
        # Create nested tabs for different rounds
        round_tabs = st.tabs(["Initial Round", "Team Round", "F&F Round", "Seed Round"])
        
        # Display cap table for each round
        for tab, (round_name, round_data) in zip(round_tabs, cap_table_data.items()):
            with tab:
                # Create three columns for metrics
                metric_cols = st.columns(3)
                
                with metric_cols[0]:
                    st.metric("Valuation", format_indian_currency(round_data['valuation']))
                with metric_cols[1]:
                    st.metric("Share Value", format_indian_currency(round_data['share_value']))
                with metric_cols[2]:
                    total_shares = sum(shareholder['shares'] for shareholder in round_data['shareholders'].values())
                    st.metric("Total Shares", f"{total_shares:,}")
                
                # Calculate and display detailed cap table
                df = calculate_cap_table_metrics(round_data)
                
                # Display ownership table and chart side by side
                table_col, chart_col = st.columns([3, 2])
                
                with table_col:
                    st.dataframe(df.style.format({
                        'Shares': '{:,.0f}',
                        'Percentage': '{:.2f}%',
                        'Value': lambda x: format_indian_currency(x)
                    }), use_container_width=True)
                
                with chart_col:
                    fig = px.pie(df, values='Shares', names='Shareholder',
                               title=f'Ownership Distribution - {round_name.replace("_", " ").title()}')
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
            # Dilution Analysis
        st.subheader("Founder Dilution Analysis")
        
        # Calculate founder dilution across rounds
        founder_dilution = []
        for round_name, round_data in cap_table_data.items():
            total_shares = sum(shareholder['shares'] for shareholder in round_data['shareholders'].values())
            founder_shares = round_data['shareholders']['You']['shares'] + round_data['shareholders']['Subha']['shares']
            founder_percentage = (founder_shares / total_shares) * 100
            founder_dilution.append({
                'Round': round_name.replace('_', ' ').title(),
                'Founder Ownership': founder_percentage
            })
        
        # Create dilution visualization
        dilution_df = pd.DataFrame(founder_dilution)
        fig = px.line(dilution_df, x='Round', y='Founder Ownership',
                     title='Founder Ownership Dilution',
                     markers=True)
        fig.update_layout(
            template="plotly_dark",
            yaxis_title="Founder Ownership (%)"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Available Capital Analysis
        st.subheader("Available Capital Analysis")
        authorized_shares = 10000
        used_shares = sum(shareholder_data['shares'] for shareholder_data in 
                 cap_table_data['post_seed']['shareholders'].values())
        remaining_shares = authorized_shares - used_shares
        
        capital_cols = st.columns(2)
        
        with capital_cols[0]:
            st.metric("Authorized Shares", f"{authorized_shares:,}")
            st.metric("Used Shares", f"{used_shares:,}")
            st.metric("Available Shares", f"{remaining_shares:,}")
        
        with capital_cols[1]:
            remaining_capital_df = pd.DataFrame({
                'Category': ['Used Shares', 'Available Shares'],
                'Shares': [used_shares, remaining_shares]
            })
            
            fig = px.pie(remaining_capital_df, values='Shares', names='Category',
                        title='Authorized Capital Utilization')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        # Success Buffer Strategy
        st.header("Success Buffer Release Strategy")
        buffer_col1, buffer_col2, buffer_col3 = st.columns(3)
        
        total_users = (st.session_state.financial_data['users']['institutional'] + 
                    st.session_state.financial_data['users']['digital'])
        
        with buffer_col1:
            st.subheader("Initial Operating Budget")
            st.metric("Amount", "₹1.46L", "Immediately Available")
            st.markdown("""
            - Partnership Development: ₹50K
            - Onboarding Resources: ₹30K
            - Operations & Engagement: ₹66K
            """)
        
        with buffer_col2:
            st.subheader("First Buffer Release")
            progress1 = (total_users/175 * 100) if total_users <= 175 else 100
            st.metric("Target", "175 Users", f"Current: {total_users}")
            st.metric("Release Amount", "₹20K", "At 175 users")
            st.progress(progress1/100, f"Progress: {progress1:.1f}%")
        
        with buffer_col3:
            st.subheader("Second Buffer Release")
            progress2 = (total_users/250 * 100) if total_users <= 250 else 100
            st.metric("Target", "250 Users", f"Current: {total_users}")
            st.metric("Release Amount", "₹20K", "At 250 users")
            st.progress(progress2/100, f"Progress: {progress2:.1f}%")

        # Risk Management
        st.header("Risk Management & Contingency")
        
        # Risk Scenarios
        risk_col1, risk_col2, risk_col3 = st.columns(3)
        
        with risk_col1:
            st.subheader("Best Case")
            st.metric("Monthly Burn", format_indian_currency(q2_total/3 * 0.9))
            st.metric("Runway", "8 months")
            st.markdown("- Optimal resource utilization\n- High user conversion\n- Early partnerships")
        
        with risk_col2:
            st.subheader("Expected Case")
            st.metric("Monthly Burn", format_indian_currency(q2_total/3))
            st.metric("Runway", "7 months")
            st.markdown("- Planned resource allocation\n- Target user acquisition\n- Regular partnership closure")
        
        with risk_col3:
            st.subheader("Worst Case")
            st.metric("Monthly Burn", format_indian_currency(q2_total/3 * 1.1))
            st.metric("Runway", "6 months")
            st.markdown("- Higher resource needs\n- Slower user growth\n- Delayed partnerships")

        # Budget Control Triggers
        st.subheader("Budget Control Triggers")
        triggers_df = pd.DataFrame({
            'Trigger Level': ['Warning', 'Critical Review', 'Emergency Measures'],
            'Monthly Spend': ['110%', '120%', '130%'],
            'Action Required': [
                'Review and Optimize',
                'Freeze Non-Essential Spending',
                'Implement Emergency Measures'
            ],
            'Impact Level': ['Low', 'Medium', 'High']
        })
        st.dataframe(triggers_df, use_container_width=True)

        # Seed Round Planning
        st.header("Seed Round Planning")
        seed_col1, seed_col2 = st.columns(2)
        
        with seed_col1:
            st.subheader("Target Metrics")
            st.metric("Target Raise", "₹5Cr")
            st.metric("Target Timeline", "End of Q2 2025")
            st.metric("User Target", "1000 active users")
            
        with seed_col2:
            st.subheader("Allocation Plan")
            seed_allocation = {
                'Product Development': 40,
                'Market Expansion': 35,
                'Operations': 25
            }
            
            fig = px.pie(
                values=list(seed_allocation.values()),
                names=list(seed_allocation.keys()),
                title='Planned Seed Round Allocation'
            )
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    elif page == 'Partnership Tracker':
        st.title('Partnership Tracker')
        
        # Add new partnership form
        st.header("Add New Partnership")
        with st.form("new_partnership"):
            col1, col2 = st.columns(2)
            
            with col1:
                institution_name = st.text_input("Institution Name")
                potential_students = st.number_input("Potential Students", min_value=0)
                stage = st.selectbox("Stage", ["Initial Contact", "In Discussion", 
                                            "Agreement Phase", "Active"])
            with col2:
                contact_person = st.text_input("Contact Person")
                expected_closure = st.date_input("Expected Closure Date")
                notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("Add Partnership")
            if submitted:
                new_partnership = {
                    'name': institution_name,
                    'potential_students': potential_students,
                    'stage': stage,
                    'contact': contact_person,
                    'expected_closure': str(expected_closure),
                    'notes': notes,
                    'date_added': str(datetime.now().date())
                }
                st.session_state.financial_data['partnerships']['pipeline'].append(new_partnership)
                if stage == 'Active':
                    st.session_state.financial_data['partnerships']['active'] += 1
                st.session_state.financial_data['partnerships']['total_potential_users'] += potential_students
                st.success(f"Partnership with {institution_name} added successfully!")

        # Partnership Overview
        st.header("Partnership Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Active Partnerships", 
                    st.session_state.financial_data['partnerships']['active'],
                    "Target: 15-20")
        
        with col2:
            pipeline_count = len(st.session_state.financial_data['partnerships']['pipeline'])
            st.metric("Pipeline Opportunities", pipeline_count)
        
        with col3:
            total_potential = st.session_state.financial_data['partnerships']['total_potential_users']
            st.metric("Potential Users", total_potential)

        # Partnership Pipeline
        if len(st.session_state.financial_data['partnerships']['pipeline']) > 0:
            st.header("Partnership Pipeline")
            
            # Convert pipeline data to DataFrame
            pipeline_df = pd.DataFrame(st.session_state.financial_data['partnerships']['pipeline'])
            
            # Stage-wise analysis
            st.subheader("Pipeline Analysis")
            if not pipeline_df.empty:
                # Create pipeline visualization
                fig = px.bar(pipeline_df, 
                            x='stage', 
                            y='potential_students',
                            title='Potential Users by Stage',
                            color='stage')
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed pipeline table
                st.subheader("Pipeline Details")
                display_columns = ['name', 'stage', 'potential_students', 
                                'expected_closure', 'contact', 'notes']
                if all(col in pipeline_df.columns for col in display_columns):
                    st.dataframe(pipeline_df[display_columns].sort_values('expected_closure'),
                            use_container_width=True)

        # Pipeline Health Metrics
        st.header("Pipeline Health")
        health_col1, health_col2 = st.columns(2)
        
        with health_col1:
            if st.session_state.financial_data['partnerships']['active'] > 0:
                progress = (st.session_state.financial_data['partnerships']['active'] / 15) * 100
                st.metric("Progress to Target", f"{progress:.1f}%", "Target: 15 partnerships")
                st.progress(min(progress/100, 1.0))
        
        with health_col2:
            avg_users = (st.session_state.financial_data['partnerships']['total_potential_users'] / 
                        max(pipeline_count, 1))
            st.metric("Avg Users per Partnership", f"{avg_users:.0f}", "Target: 50 per partnership")

        # Add export functionality for partnerships data
        if st.button("Export Partnership Data"):
            partnership_data = pd.DataFrame(st.session_state.financial_data['partnerships']['pipeline'])
            st.download_button(
                label="Download Partnership Data as CSV",
                data=partnership_data.to_csv(index=False),
                file_name="partnership_pipeline.csv",
                mime="text/csv"
            )
            
        elif page == 'User Analytics':
            st.title('User Analytics')
        
        # User Overview
        st.header("User Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Institutional Users", 
                    st.session_state.financial_data['users']['institutional'],
                    "75% of Total Target")
        with col2:
            st.metric("Digital Users",
                    st.session_state.financial_data['users']['digital'],
                    "25% of Total Target")
        with col3:
            total_users = (st.session_state.financial_data['users']['institutional'] + 
                        st.session_state.financial_data['users']['digital'])
            st.metric("Total Users", total_users)
        with col4:
            cac = calculate_cac()
            st.metric("Overall CAC", format_indian_currency(cac))

        # Growth Analysis
        st.header("Growth Analysis")
        growth_tabs = st.tabs(["Growth Trajectory", "Channel Performance", "CAC Analysis"])
        
        with growth_tabs[0]:
            growth_data = create_growth_trajectory_data()  # Using the same function
            
            fig = go.Figure()
            
            # Add weekly target line
            fig.add_trace(go.Scatter(
                x=growth_data['Date'],
                y=growth_data['Weekly_Target'],
                name='Weekly Target',
                line=dict(color='blue', width=1)
            ))
            
            # Add current trajectory
            fig.add_trace(go.Scatter(
                x=growth_data['Date'],
                y=growth_data['Current_Trajectory'],
                name='Current Trajectory',
                line=dict(color='lightblue', width=2)
            ))
            
            # Add buffer release lines
            fig.add_hline(y=175, line_dash="dash", 
                        annotation_text="First Buffer Release",
                        line_color="gray")
            fig.add_hline(y=250, line_dash="dash", 
                        annotation_text="Second Buffer Release",
                        line_color="gray")
            
            fig.update_layout(
                title='User Growth Trajectory',
                xaxis_title='Date',
                yaxis_title='Users',
                yaxis_range=[0, 500],
                showlegend=True,
                template="plotly_dark"
            )
            
            st.plotly_chart(fig, use_container_width=True)

        with growth_tabs[1]:
            col1, col2 = st.columns(2)
            
            with col1:
                channel_data = pd.DataFrame({
                    'Channel': ['Institutional', 'Digital'],
                    'Users': [st.session_state.financial_data['users']['institutional'],
                            st.session_state.financial_data['users']['digital']],
                    'Target_Split': [75, 25]
                })
                
                fig = px.pie(channel_data, values='Users', names='Channel',
                            title='Current User Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(channel_data, x='Channel', y=['Users', 'Target_Split'],
                            title='Channel Performance vs Target',
                            barmode='group')
                st.plotly_chart(fig, use_container_width=True)

        with growth_tabs[2]:
            col1, col2 = st.columns(2)
            
            with col1:
                cac_data = pd.DataFrame({
                    'Channel': ['Institutional', 'Digital'],
                    'Current_CAC': [st.session_state.financial_data['metrics']['institutional_cac'],
                                st.session_state.financial_data['metrics']['digital_cac']],
                    'Target_CAC': [1000, 2000]
                })
                
                fig = px.bar(cac_data, x='Channel', y=['Current_CAC', 'Target_CAC'],
                            title='CAC Performance vs Target',
                            barmode='group')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # CAC Trend (simulated data for demonstration)
                cac_trend = pd.DataFrame({
                    'Week': range(1, 13),
                    'Institutional_CAC': [827] * 12,
                    'Digital_CAC': [3720] * 12
                })
                
                fig = px.line(cac_trend, x='Week', y=['Institutional_CAC', 'Digital_CAC'],
                            title='CAC Trend by Channel')
                st.plotly_chart(fig, use_container_width=True)
            st.subheader("CAC Analysis & Breakdown")
        
        # Input Section for CAC Parameters
        st.write("#### CAC Input Parameters")
        input_col1, input_col2 = st.columns(2)
        
        with input_col1:
            # Marketing Costs
            st.write("Marketing Costs")
            digital_marketing = st.number_input("Digital Marketing Budget (₹)", 
                                            value=150000, step=10000, key="digital_mkt")
            content_creation = st.number_input("Content Creation Cost (₹)", 
                                            value=30000, step=5000, key="content")
            events_cost = st.number_input("Events & Workshops Cost (₹)", 
                                        value=50000, step=5000, key="events")
            
        with input_col2:
            # Sales Costs
            st.write("Sales Costs")
            sales_team = st.number_input("Sales Team Cost (₹)", 
                                    value=160000, step=10000, key="sales")
            travel_cost = st.number_input("Travel & Meeting Cost (₹)", 
                                        value=25000, step=5000, key="travel")
            tools_cost = st.number_input("Sales Tools & Software (₹)", 
                                    value=15000, step=5000, key="tools")

        # User Acquisition Inputs
        st.write("#### User Acquisition Data")
        acq_col1, acq_col2 = st.columns(2)
        
        with acq_col1:
            institutional_users = st.number_input("Institutional Users", 
                                                value=st.session_state.financial_data['users']['institutional'],
                                                key="inst_users")
            inst_target = st.number_input("Institutional User Target", value=175, key="inst_target")
            
        with acq_col2:
            digital_users = st.number_input("Digital Users", 
                                        value=st.session_state.financial_data['users']['digital'],
                                        key="digital_users")
            digital_target = st.number_input("Digital User Target", value=75, key="digital_target")

        # CAC Calculations
        total_marketing = digital_marketing + content_creation + events_cost
        total_sales = sales_team + travel_cost + tools_cost
        total_cost = total_marketing + total_sales
        
        # Channel-wise cost allocation
        institutional_cost_ratio = 0.7  # 70% cost allocated to institutional
        digital_cost_ratio = 0.3       # 30% cost allocated to digital
        
        institutional_cost = total_cost * institutional_cost_ratio
        digital_cost = total_cost * digital_cost_ratio
        
        # Calculate CACs
        inst_cac = (institutional_cost / institutional_users) if institutional_users > 0 else 0
        digital_cac = (digital_cost / digital_users) if digital_users > 0 else 0
        overall_cac = (total_cost / (institutional_users + digital_users)) if (institutional_users + digital_users) > 0 else 0

        # Display CAC Metrics
        st.write("#### CAC Metrics")
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("Institutional CAC", 
                    format_indian_currency(inst_cac),
                    f"Target: {format_indian_currency(1000)}")
            
        with metric_col2:
            st.metric("Digital CAC", 
                    format_indian_currency(digital_cac),
                    f"Target: {format_indian_currency(2000)}")
            
        with metric_col3:
            st.metric("Overall CAC", 
                    format_indian_currency(overall_cac),
                    f"Target: {format_indian_currency(1500)}")

        # Detailed Breakdown
        st.write("#### Cost Breakdown")
        breakdown_col1, breakdown_col2 = st.columns(2)
        
        with breakdown_col1:
            # Marketing costs breakdown
            marketing_data = pd.DataFrame({
                'Category': ['Digital Marketing', 'Content Creation', 'Events'],
                'Amount': [digital_marketing, content_creation, events_cost],
                'Percentage': [
                    digital_marketing/total_cost*100,
                    content_creation/total_cost*100,
                    events_cost/total_cost*100
                ]
            })
            marketing_data['Amount_Formatted'] = marketing_data['Amount'].apply(format_indian_currency)
            
            fig = px.pie(marketing_data, values='Amount', names='Category',
                        title='Marketing Cost Distribution')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
        with breakdown_col2:
            # Sales costs breakdown
            sales_data = pd.DataFrame({
                'Category': ['Sales Team', 'Travel & Meetings', 'Tools & Software'],
                'Amount': [sales_team, travel_cost, tools_cost],
                'Percentage': [
                    sales_team/total_cost*100,
                    travel_cost/total_cost*100,
                    tools_cost/total_cost*100
                ]
            })
            sales_data['Amount_Formatted'] = sales_data['Amount'].apply(format_indian_currency)
            
            fig = px.pie(sales_data, values='Amount', names='Category',
                        title='Sales Cost Distribution')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        # Efficiency Metrics
        st.write("#### Efficiency Metrics")
        efficiency_col1, efficiency_col2 = st.columns(2)
        
        with efficiency_col1:
            # Cost per channel metrics
            channel_costs = pd.DataFrame({
                'Channel': ['Institutional', 'Digital'],
                'Allocated Cost': [institutional_cost, digital_cost],
                'Users Acquired': [institutional_users, digital_users],
                'CAC': [inst_cac, digital_cac],
                'Target CAC': [1000, 2000]
            })
            channel_costs['Efficiency'] = (channel_costs['Target CAC'] - channel_costs['CAC']) / channel_costs['Target CAC'] * 100
            
            st.dataframe(channel_costs.style.format({
                'Allocated Cost': lambda x: format_indian_currency(x),
                'CAC': lambda x: format_indian_currency(x),
                'Target CAC': lambda x: format_indian_currency(x),
                'Efficiency': '{:.1f}%'
            }))
            
        with efficiency_col2:
            # Progress to targets
            progress_data = pd.DataFrame({
                'Metric': ['Institutional Users', 'Digital Users'],
                'Current': [institutional_users, digital_users],
                'Target': [inst_target, digital_target],
                'Progress': [institutional_users/inst_target*100, digital_users/digital_target*100]
            })
            
            fig = px.bar(progress_data, x='Metric', y=['Current', 'Target'],
                        title='Progress to User Targets',
                        barmode='group')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        # Recommendations based on calculations
        st.write("#### Recommendations")
        recommendations = []
        
        if inst_cac > 1000:
            recommendations.append("⚠️ Institutional CAC above target - Review partnership acquisition strategy")
        if digital_cac > 2000:
            recommendations.append("⚠️ Digital CAC above target - Optimize marketing spend")
        if institutional_users/inst_target < 0.5:
            recommendations.append("📊 Accelerate institutional user acquisition to meet targets")
        if digital_users/digital_target < 0.5:
            recommendations.append("📊 Boost digital marketing efforts to improve user acquisition")
        
        for rec in recommendations:
            st.write(rec)

        # User Retention Analysis
        st.header("Retention Analysis")
        retention_col1, retention_col2 = st.columns(2)
        
        with retention_col1:
            retention_data = pd.DataFrame({
                'Week': ['Week 1', 'Week 2', 'Month 1'],
                'Target': [90, 80, 70],
                'Actual': [92, 85, 75]
            })
            
            fig = px.bar(retention_data, x='Week', y=['Target', 'Actual'],
                        title='Retention Performance',
                        barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        
        with retention_col2:
            st.metric("Week 1 Retention", "92%", "+2% vs Target")
            st.metric("Week 2 Retention", "85%", "+5% vs Target")
            st.metric("Month 1 Retention", "75%", "+5% vs Target")
    elif page == 'User Analytics':
        st.title('User Analytics')
        
        # Key Metrics Overview
        st.header("User Overview")
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        # Calculate metrics
        total_users = (st.session_state.financial_data['users']['institutional'] + 
                    st.session_state.financial_data['users']['digital'])
        weekly_target = st.session_state.financial_data['users']['weekly_targets']['week1-4']
        institutional_pct = (st.session_state.financial_data['users']['institutional'] / total_users * 100) if total_users > 0 else 0
        digital_pct = (st.session_state.financial_data['users']['digital'] / total_users * 100) if total_users > 0 else 0
        
        with metric_col1:
            st.metric(
                "Total Users",
                total_users,
                f"Target: {weekly_target} weekly"
            )
        
        with metric_col2:
            st.metric(
                "Institutional Users",
                st.session_state.financial_data['users']['institutional'],
                f"{institutional_pct:.1f}% of total"
            )
        
        with metric_col3:
            st.metric(
                "Digital Users",
                st.session_state.financial_data['users']['digital'],
                f"{digital_pct:.1f}% of total"
            )
        
        with metric_col4:
            buffer_progress = (total_users/175 * 100) if total_users <= 175 else (total_users/250 * 100)
            st.metric(
                "Buffer Progress",
                f"{buffer_progress:.1f}%",
                f"Next: {'250' if total_users > 175 else '175'} users"
            )

        # User Growth Analysis
        st.header("Growth Analysis")
        growth_tabs = st.tabs(["Growth Trajectory", "Channel Performance", "Acquisition Metrics"])
        
        with growth_tabs[0]:
            col1, col2 = st.columns([2,1])
            with col1:
                # Growth trajectory chart
                growth_data = create_growth_trajectory_data()  # from previous implementation
                fig = px.line(growth_data, x='Date', y=['Weekly_Target', 'Current_Trajectory'],
                            title='User Growth Trajectory')
                fig.add_hline(y=175, line_dash="dash", annotation_text="First Buffer Release")
                fig.add_hline(y=250, line_dash="dash", annotation_text="Second Buffer Release")
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Weekly targets
                st.subheader("Weekly Targets")
                st.metric("Weeks 1-4", f"{weekly_target} users/week")
                st.metric("Weeks 5-8", f"{st.session_state.financial_data['users']['weekly_targets']['week5-8']} users/week")
                st.metric("Weeks 9-12", f"{st.session_state.financial_data['users']['weekly_targets']['week9-12']} users/week")

            with growth_tabs[1]:  # Channel Performance
                st.subheader("Channel Distribution & Performance")
                channel_col1, channel_col2 = st.columns(2)
            
            with channel_col1:
                # Channel distribution pie chart
                channel_data = pd.DataFrame({
                    'Channel': ['Institutional', 'Digital'],
                    'Users': [st.session_state.financial_data['users']['institutional'],
                            st.session_state.financial_data['users']['digital']]
                })
                fig = px.pie(channel_data, values='Users', names='Channel',
                            title='User Distribution by Channel')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                # Channel metrics below pie chart
                st.metric("Institutional Target", "75%", f"{institutional_pct:.1f}% current")
                st.metric("Digital Target", "25%", f"{digital_pct:.1f}% current")
            
            with channel_col2:
                # CAC by channel
                cac_data = pd.DataFrame({
                    'Channel': ['Institutional', 'Digital'],
                    'Current CAC': [st.session_state.financial_data['metrics']['institutional_cac'],
                                st.session_state.financial_data['metrics']['digital_cac']],
                    'Target CAC': [1000, 2000]
                })
                fig = px.bar(cac_data, x='Channel', y=['Current CAC', 'Target CAC'],
                            title='CAC by Channel',
                            barmode='group')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            # Channel health indicators (full width below)
            st.subheader("Channel Health Metrics")
            channel_health = pd.DataFrame({
                'Channel': ['Institutional', 'Digital'],
                'Current %': [institutional_pct, digital_pct],
                'Target %': [75, 25],
                'Current CAC': [format_indian_currency(st.session_state.financial_data['metrics']['institutional_cac']),
                            format_indian_currency(st.session_state.financial_data['metrics']['digital_cac'])],
                'Target CAC': ['₹1,000', '₹2,000'],
                'Status': ['On Track' if abs(institutional_pct-75) < 10 else 'Needs Attention',
                        'On Track' if abs(digital_pct-25) < 10 else 'Needs Attention']
            })
            st.dataframe(channel_health, use_container_width=True)

        with growth_tabs[2]:  # Acquisition Metrics
                st.subheader("Acquisition Performance")
                acq_col1, acq_col2 = st.columns(2)
            
        with acq_col1:
                # Acquisition Rate Metrics
                weekly_acquisition = pd.DataFrame({
                    'Week': list(range(1, 13)),
                    'Target': [weekly_target] * 12,
                    'Actual': [total_users/12] * 12  # Simplified for demonstration
                })
                fig = px.line(weekly_acquisition, x='Week', y=['Target', 'Actual'],
                            title='Weekly Acquisition Rate')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
        with acq_col2:
                st.subheader("Acquisition Efficiency")
                active_partnerships = st.session_state.financial_data['partnerships']['active']
                
                efficiency_metrics = {
                    'Weekly Acquisition Rate': f"{total_users/12:.1f} users/week",
                    'Users per Partnership': f"{total_users/max(active_partnerships, 1):.1f}",
                    'Conversion Rate': "15%",
                    'Growth Rate MoM': "25%"
                }
                for metric, value in efficiency_metrics.items():
                    st.metric(metric, value)
            
            # Acquisition Funnel (full width below)
        st.subheader("Acquisition Funnel")
        funnel_data = pd.DataFrame({
                'Stage': ['Leads', 'Trials', 'Active Users', 'Retained Users'],
                'Count': [1000, 500, 250, 200],
                'Conversion': ['100%', '50%', '25%', '20%']
            })
        st.dataframe(funnel_data, use_container_width=True)

        # Retention Analysis
        st.header("Retention Analysis")
        retention_col1, retention_col2 = st.columns(2)
        
        with retention_col1:
            # Retention metrics
            retention_data = pd.DataFrame({
                'Period': ['Week 1', 'Week 2', 'Month 1'],
                'Target': [90, 80, 70],
                'Actual': [92, 85, 75]
            })
            fig = px.bar(retention_data, x='Period', y=['Target', 'Actual'],
                        title='Retention Performance',
                        barmode='group')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        
        with retention_col2:
            st.subheader("Retention Metrics")
            st.metric("Week 1 Retention", "92%", "+2% vs Target")
            st.metric("Week 2 Retention", "85%", "+5% vs Target")
            st.metric("Month 1 Retention", "75%", "+5% vs Target")
            
            # Retention health indicator
            retention_health = pd.DataFrame({
                'Period': ['Week 1', 'Week 2', 'Month 1'],
                'Status': ['Excellent', 'Good', 'Good'],
                'Action Required': ['Maintain', 'Monitor', 'Monitor']
            })
            st.dataframe(retention_health)

        # User Engagement Metrics
            st.header("Engagement Metrics")
            engagement_cols = st.columns(4)
            
            engagement_metrics = {
                'Daily Active Users': f"{total_users * 0.6:.0f}",
                'Weekly Active Users': f"{total_users * 0.8:.0f}",
                'Average Session Time': "25 mins",
                'Feature Adoption': "75%"
            }
            
            for i, (metric, value) in enumerate(engagement_metrics.items()):
                with engagement_cols[i]:
                    st.metric(metric, value)

            # Action Items and Recommendations
            st.header("Recommendations")
            recommendations = []
            
            if total_users < weekly_target:
                recommendations.append("🎯 Increase acquisition efforts to meet weekly target")
            if institutional_pct < 70:
                recommendations.append("🏫 Focus on institutional partnerships to improve channel mix")
            if digital_pct < 20:
                recommendations.append("💻 Boost digital marketing efforts")
            if buffer_progress < 90:
                recommendations.append("💰 Accelerate growth to reach next buffer release")
            
            for rec in recommendations:
                st.write(rec)
        st.header("MVP Feedback Matrix")
        feedback_tabs = st.tabs(["Matrix Overview", "Upload Feedback", "Progress Tracking"])
        
        # Initialize session state for feedback data if not exists
        if 'feedback_data' not in st.session_state:
            st.session_state.feedback_data = []
            
        with feedback_tabs[0]:
            # Define the scoring criteria
            scoring_criteria = {
                "User Engagement (40%)": {
                    "Daily Active Usage": {
                        "Excellent (10p)": ">30 mins daily",
                        "Good (7p)": "15-30 mins daily",
                        "Needs Improvement (3p)": "<15 mins daily"
                    },
                    "Feature Utilization": {
                        "Excellent (10p)": ">3 features daily",
                        "Good (7p)": "2-3 features daily",
                        "Needs Improvement (3p)": "1 feature daily"
                    },
                    "AI Token Utilization": {
                        "Excellent (10p)": "80-100% used",
                        "Good (7p)": "50-79% used",
                        "Needs Improvement (3p)": "<50% used"
                    },
                    "Content Creation": {
                        "Excellent (10p)": ">5 notes/PDF",
                        "Good (7p)": "3-5 notes/PDF",
                        "Needs Improvement (3p)": "<3 notes/PDF"
                    }
                },
                "User Experience (30%)": {
                    "In-App Feedback": {
                        "Excellent (10p)": ">80% positive",
                        "Good (7p)": "60-80% positive",
                        "Needs Improvement (3p)": "<60% positive"
                    },
                    "Google Form Responses": {
                        "Excellent (10p)": ">80% satisfaction",
                        "Good (7p)": "60-80% satisfaction",
                        "Needs Improvement (3p)": "<60% satisfaction"
                    },
                    "Physical Interaction": {
                        "Excellent (10p)": "Predominantly positive",
                        "Good (7p)": "Mixed feedback",
                        "Needs Improvement (3p)": "Predominantly negative"
                    }
                },
                "Technical Performance (20%)": {
                    "App Stability": {
                        "Excellent (10p)": "<1% crash rate",
                        "Good (7p)": "1-3% crash rate",
                        "Needs Improvement (3p)": ">3% crash rate"
                    },
                    "Response Time": {
                        "Excellent (10p)": "<2 sec average",
                        "Good (7p)": "2-4 sec average",
                        "Needs Improvement (3p)": ">4 sec average"
                    }
                },
                "Learning Impact (10%)": {
                    "Learning Efficiency": {
                        "Excellent (10p)": ">80% report improvement",
                        "Good (7p)": "60-80% report improvement",
                        "Needs Improvement (3p)": "<60% report improvement"
                    }
                }
            }
            
            # Display scoring criteria in an expandable section
            with st.expander("View Scoring Criteria", expanded=True):
                for category, metrics in scoring_criteria.items():
                    st.markdown(f"### {category}")
                    for metric, criteria in metrics.items():
                        st.markdown(f"#### {metric}")
                        for level, description in criteria.items():
                            st.markdown(f"- {level}: {description}")
        
        with feedback_tabs[1]:
            # File upload for feedback data
            st.subheader("Upload Feedback Data")
            uploaded_file = st.file_uploader("Upload Feedback CSV", type=['csv'])
            
            if uploaded_file is not None:
                try:
                    feedback_df = pd.read_csv(uploaded_file)
                    st.success("Feedback data uploaded successfully!")
                    st.session_state.feedback_data.extend(feedback_df.to_dict('records'))
                    st.dataframe(feedback_df)
                except Exception as e:
                    st.error(f"Error uploading file: {str(e)}")
            
            # Manual feedback input
            st.subheader("Manual Feedback Entry")
            
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category", list(scoring_criteria.keys()))
            with col2:
                if category:
                    metric = st.selectbox("Metric", list(scoring_criteria[category].keys()))
            
            if category and metric:
                score = st.slider("Score", 0, 10, 5)
                notes = st.text_area("Additional Notes")
                
                if st.button("Add Feedback"):
                    new_feedback = {
                        'category': category,
                        'metric': metric,
                        'score': score,
                        'notes': notes,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    st.session_state.feedback_data.append(new_feedback)
                    st.success("Feedback added successfully!")
        
        with feedback_tabs[2]:
            if len(st.session_state.feedback_data) > 0:
                # Convert feedback to DataFrame
                feedback_df = pd.DataFrame(st.session_state.feedback_data)
                
                # Overall progress visualization
                st.subheader("Progress Overview")
                
                # Score evolution over time
                fig = px.line(feedback_df, x='timestamp', y='score',
                            color='category', 
                            title='Score Evolution Over Time')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                # Category-wise performance
                avg_scores = feedback_df.groupby('category')['score'].mean().reset_index()
                fig = px.bar(avg_scores, x='category', y='score',
                            title='Average Scores by Category')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                # Success criteria tracking
                total_score = avg_scores['score'].mean()
                score_status = "🟢" if total_score >= 8 else "🟡" if total_score >= 6 else "🔴"
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Overall Score", f"{score_status} {total_score:.1f}/10")
                with col2:
                    st.metric("Total Feedback Count", len(feedback_df))
                
                # Detailed feedback table
                st.subheader("Feedback History")
                st.dataframe(feedback_df.sort_values('timestamp', ascending=False))
                
                # Export functionality
                if st.button("Export Feedback Data"):
                    csv = feedback_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="mvp_feedback_data.csv",
                        mime="text/csv"
                    )
            else:
                st.info("No feedback data available yet. Please upload data or add manual feedback.")

    elif page == 'Financial Projections':
        st.title("Financial Projections 2025")
    
    # Scenarios Selection
        scenario = st.radio(
            "Select Scenario",
            ["Conservative", "Base Case", "Aggressive"],
            horizontal=True
        )
        
        # Scenario Multipliers
        multipliers = {
            "Conservative": 0.7,
            "Base Case": 1.0,
            "Aggressive": 1.3
        }
        
        # Base Revenue Data
        lt_base_revenue= {
            'Q2': 1822000,
            'Q3': 4515000,
            'Q4': 7468000
        }
        lt_market_data = pd.DataFrame({
            'Year': ['2025', '2026', '2027'],
            'Total_Market': [870000, 1000500, 1150575],
            'Our_Users': [5000, 25000, 100000],
            'Market_Share': [0.6, 2.9, 11.5]
        })

        lt_revenue_mix = pd.DataFrame({
            'Year': ['2025', '2026', '2027'],
            'Student_Plans': [26, 35, 45],
            'Institutional': [74, 65, 55]
        })

        lt_cost_structure = pd.DataFrame({
            'Year': ['2025', '2026', '2027'],
            'Development': [40, 35, 30],
            'Marketing': [25, 20, 15],
            'Infrastructure': [15, 25, 35],
            'Admin_Support': [20, 20, 20]
        })

        lt_team_growth = pd.DataFrame({
            'Year': ['2025', '2026', '2027'],
            'Development': [8, 20, 40],
            'Sales': [5, 15, 25],
            'Support': [4, 10, 20],
            'Admin': [3, 5, 15]
        })

        lt_profitability_metrics = pd.DataFrame({
            'Year': ['2025', '2026', '2027'],
            'Gross_Margin': [31.4, 44.6, 66.5],
            'Operating_Margin': [15.2, 25.8, 35.6],
            'EBITDA_Margin': [10.5, 20.4, 30.2]
        })

        lt_benchmark_data = pd.DataFrame({
            'Metric': ['CAC', 'LTV', 'Gross Margin', 'Growth Rate'],
            'Acolyte': [1200, 9984, 55, 147.8],
            'Competitor A': [2500, 12000, 45, 100],
            'Competitor B': [1800, 8000, 50, 120],
            'Industry Avg': [2000, 10000, 48, 110]
        })

        lt_scenario_data = pd.DataFrame({
            'Metric': ['Revenue 2027', 'Users 2027', 'Market Share 2027', 'Gross Margin 2027'],
            'Conservative': [70000000, 70000, 8.1, 45],
            'Base Case': [100000000, 100000, 11.5, 55],
            'Aggressive': [130000000, 130000, 15.0, 65]
        })

        # Create quarters for growth metrics
        quarters = pd.date_range(start='2025-04-01', end='2027-12-31', freq='Q')
        revenue_growth = [None, 147.8, 65.4, 45.0, 40.0, 35.0, 32.0, 30.0, 28.0, 25.0, 22.0]
        user_growth = [None, 150.0, 75.0, 50.0, 45.0, 40.0, 35.0, 32.0, 30.0, 28.0, 25.0]

        lt_growth_metrics = pd.DataFrame({
            'Quarter': quarters,
            'Revenue_Growth': revenue_growth,
            'User_Growth': user_growth
        })
        quarterly_data = pd.DataFrame({
                    'Quarter': ['Q2 2025', 'Q3 2025', 'Q4 2025'],
                    'Revenue': [
                        lt_base_revenue['Q2'] * multipliers[scenario],
                        lt_base_revenue['Q3'] * multipliers[scenario],
                        lt_base_revenue['Q4'] * multipliers[scenario]
                    ]
                })

        # Create sensitivity data
        sensitivity_range = [-20, -10, 0, 10, 20]
        base_revenue_2027 = 100000000 
        lt_sensitivity_data = pd.DataFrame({
            'Change_%': sensitivity_range,
            'Revenue_Impact': [base_revenue_2027* (1 + x/100) for x in sensitivity_range],
            'Margin_Impact': [55 + (x/2) for x in sensitivity_range]
        })
        # Revenue Projections Section
        st.header("Revenue Projections")
        
        # Quarterly Revenue Breakdown
        revenue_tabs = st.tabs(["Quarterly Overview", "Monthly Breakdown", "Revenue Streams"])
    
        with revenue_tabs[0]:
            col1, col2 = st.columns(2)
            
            with col1:
                # Create quarterly data correctly

                
                fig = px.bar(quarterly_data, x='Quarter', y='Revenue',
                            title=f'Quarterly Revenue Projection ({scenario})')
                fig.update_traces(text=[format_indian_currency(x) for x in quarterly_data['Revenue']],
                                textposition='auto')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True, key="quarterly_revenue_chart")
            
            with col2:
                total_revenue = (lt_base_revenue['Q2'] + lt_base_revenue['Q3'] + lt_base_revenue['Q4']) * multipliers[scenario]
                avg_monthly_revenue = total_revenue / 9  # 9 months
                
                st.metric("Total Projected Revenue 2025", 
                        format_indian_currency(total_revenue))
                st.metric("Average Monthly Revenue", 
                        format_indian_currency(avg_monthly_revenue))
                q2_revenue = 1822000
                q3_revenue = 4515000
                q4_revenue = 7468000

                growth_q2_q3 = ((q3_revenue - q2_revenue)/q2_revenue * 100)
                growth_q3_q4 = ((q4_revenue - q3_revenue)/q3_revenue * 100)
                st.metric("Q2 to Q3 Growth", f"{growth_q2_q3:.1f}%")
                st.metric("Q3 to Q4 Growth", f"{growth_q3_q4:.1f}%")
        
        with revenue_tabs[1]:
            # Monthly Revenue Breakdown
            monthly_data = pd.DataFrame({
                'Month': pd.date_range(start='2025-04-01', end='2025-12-31', freq='M'),
                'Student_Basic': [24950, 49900, 74850, 90000, 150000, 210000, 249500, 249500, 249500],
                'Student_Pro': [24975, 49950, 74925, 90000, 150000, 210000, 249750, 249750, 249750],
                'Student_Premium': [11992, 25483, 37475, 45000, 75000, 105000, 150000, 150000, 150000],
                'Institutional': [0, 630000, 630000, 945000, 945000, 945000, 1260000, 1260000, 1260000]
            })
            
            # Apply scenario multiplier
            for col in ['Student_Basic', 'Student_Pro', 'Student_Premium', 'Institutional']:
                monthly_data[col] = monthly_data[col] * multipliers[scenario]
            
            monthly_data['Total'] = monthly_data[['Student_Basic', 'Student_Pro', 
                                                'Student_Premium', 'Institutional']].sum(axis=1)
            
            fig = px.line(monthly_data, x='Month', 
                        y=['Student_Basic', 'Student_Pro', 'Student_Premium', 'Institutional'],
                        title='Monthly Revenue by Stream')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            # Monthly data table
            st.dataframe(monthly_data.style.format({
                'Student_Basic': format_indian_currency,
                'Student_Pro': format_indian_currency,
                'Student_Premium': format_indian_currency,
                'Institutional': format_indian_currency,
                'Total': format_indian_currency
            }))
        
        with revenue_tabs[2]:
            # Revenue Distribution
            revenue_streams = pd.DataFrame({
                'Stream': ['Student Basic', 'Student Pro', 'Student Premium', 'Institutional'],
                'Q4_Revenue': [749000, 749000, 450000, 5520000]
            })
            
            revenue_streams['Q4_Revenue'] = revenue_streams['Q4_Revenue'] * multipliers[scenario]
            
            fig = px.pie(revenue_streams, values='Q4_Revenue', names='Stream',
                        title='Q4 2025 Revenue Distribution')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        
        # Cost Analysis Section
        st.header("Cost Analysis")
        
        cost_tabs = st.tabs(["Cost Structure", "Margins", "CAC Analysis"])
        
        with cost_tabs[0]:
            # Quarterly Cost Breakdown
            quarterly_costs = pd.DataFrame({
                'Category': ['AWS & Infrastructure', 'Sales & Marketing', 
                            'Development', 'Support', 'Other Operating'],
                'Q2_2025': [224000, 310000, 300000, 150000, 266000],
                'Q3_2025': [448000, 620000, 600000, 300000, 532000],
                'Q4_2025': [448000, 620000, 600000, 300000, 532000]
            })
            
            fig = px.bar(quarterly_costs, x='Category',
                        y=['Q2_2025', 'Q3_2025', 'Q4_2025'],
                        title='Quarterly Cost Structure',
                        barmode='group')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        
        with cost_tabs[1]:
            # Margin Analysis
            col1, col2 = st.columns(2)
            
            with col1:
                margin_data = pd.DataFrame({
                    'Quarter': ['Q2 2025', 'Q3 2025', 'Q4 2025'],
                    'Revenue': [v * multipliers[scenario] for v in lt_base_revenue.values()],
                    'Costs': [1250000, 2500000, 2500000]
                })
                margin_data['Margin'] = (margin_data['Revenue'] - margin_data['Costs']) / margin_data['Revenue'] * 100
                
                fig = go.Figure()
                fig.add_trace(go.Bar(name='Revenue', x=margin_data['Quarter'], y=margin_data['Revenue']))
                fig.add_trace(go.Bar(name='Costs', x=margin_data['Quarter'], y=margin_data['Costs']))
                fig.update_layout(title='Revenue vs Costs', barmode='group', template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.line(margin_data, x='Quarter', y='Margin',
                            title='Gross Margin %')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        
        with cost_tabs[2]:
            # CAC Analysis
            cac_data = pd.DataFrame({
                'Channel': ['Institutional', 'Individual'],
                'CAC': [80000, 1200],
                'Average Revenue': [630000, 832]  # Per year for institutional, per month for individual
            })
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Customer Acquisition Costs")
                st.dataframe(cac_data.style.format({
                    'CAC': format_indian_currency,
                    'Average Revenue': format_indian_currency
                }))
            
            with col2:
                # CAC Payback Period
                cac_data['Months_to_Payback'] = cac_data.apply(
                    lambda x: x['CAC']/(x['Average Revenue']/12 if x['Channel'] == 'Institutional' else x['Average Revenue']),
                    axis=1
                )
                fig = px.bar(cac_data, x='Channel', y='Months_to_Payback',
                            title='CAC Payback Period (Months)')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        
        # Cash Flow Section
        st.header("Cash Flow Projections")
        
        quarters = ['Q2 2025', 'Q3 2025', 'Q4 2025']
        cash_flow_data = pd.DataFrame({
            'Quarter': quarters,
            'Operating Inflow': [v * multipliers[scenario] for v in lt_base_revenue.values()],
            'Operating Costs': [1250000, 2500000, 2500000],
            'Working Capital': [200000, 400000, 600000]
        })
        
        cash_flow_data['Net Cash Flow'] = (cash_flow_data['Operating Inflow'] - 
                                        cash_flow_data['Operating Costs'] - 
                                        cash_flow_data['Working Capital'])
        
        fig = go.Figure()
        fig.add_trace(go.Waterfall(
            name="Cash Flow", orientation="v",
            measure=["relative", "relative", "relative"],
            x=quarters,
            y=cash_flow_data['Net Cash Flow'],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        
        fig.update_layout(title='Quarterly Net Cash Flow',
                        showlegend=True,
                        template="plotly_dark")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed cash flow table
        st.dataframe(cash_flow_data.style.format({
            'Operating Inflow': format_indian_currency,
            'Operating Costs': format_indian_currency,
            'Working Capital': format_indian_currency,
            'Net Cash Flow': format_indian_currency
        }))
        st.markdown("---")
        st.header("Long-term Financial Analysis (2025-2027)")
    
        # Create tabs for long-term analysis
        longterm_tabs = st.tabs([
            "Key Assumptions",
            "Scenario Analysis",
            "Competitive Analysis",
            "Financial Metrics",
            "Sensitivity Analysis"
        ])
        
        with longterm_tabs[0]:
            # Key Assumptions Section
            assumption_tabs = st.tabs(["Market & Growth", "Revenue", "Costs", "Operational"])
    
        with assumption_tabs[0]:  # Market & Growth
            st.markdown("""
            ### Market & Growth Assumptions
            
            1. Market Size
            - Current medical/dental students: 8.7L
            - Annual market growth: 15%
            - New admissions per year: ~1.2L
            
            2. Market Penetration
            - 2025: 0.6% (5,000 users)
            - 2026: 2.9% (25,000 users)
            - 2027: 11.5% (100,000 users)
            
            3. Geographic Expansion
            - 2025: South India focus
            - 2026: Pan-India expansion
            - 2027: Tier 2/3 city penetration
            """)
            
            # Market Growth Visualization

            fig = px.bar(lt_market_data, x='Year', y=['Total_Market', 'Our_Users'],
                        title='Market Size vs Our Users',
                        barmode='overlay')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_market_growth_chart")
        
        with assumption_tabs[1]:  # Revenue
            st.markdown("""
            ### Revenue Assumptions
            
            1. Subscription Plans
            - Basic: ₹499/month or ₹4,999/year
            - Pro: ₹999/month or ₹9,999/year
            - Premium: ₹1,499/month or ₹14,999/year
            
            2. Conversion Rates
            - Free to Paid: 15% → 20% → 25%
            - Monthly to Annual: 70% → 75% → 80%
            - Basic to Pro: 30% → 35% → 40%
            
            3. Institutional Pricing
            - Tier 1: ₹3,500 per student/year
            - Tier 2: ₹3,000 per student/year
            - Tier 3: ₹2,500 per student/year
            """)
            fig = px.bar(lt_revenue_mix, x='Year', y=['Student_Plans', 'Institutional'],
                        title='Revenue Mix Evolution (%)',
                        barmode='stack')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_revenue_mix_chart")
        
        with assumption_tabs[2]:  # Costs
            st.markdown("""
            ### Cost Assumptions
            
            1. Fixed Costs
            - Development Team: 40% of operating costs
            - Infrastructure: 15% of operating costs
            - Admin & Support: 20% of operating costs
            
            2. Variable Costs
            - Customer Acquisition: ₹1,200 per individual user
            - Institutional Acquisition: ₹80,000 per institution
            - Server Costs: ₹15 per active user/month
            
            3. Marketing Spend
            - 2025: 25% of revenue
            - 2026: 20% of revenue
            - 2027: 15% of revenue
            """)
            
            # Cost Structure Evolution
            fig = px.area(lt_cost_structure, x='Year', 
                        y=['Development', 'Marketing', 'Infrastructure', 'Admin_Support'],
                        title='Cost Structure Evolution (%)')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_cost_structure_chart")
        
        with assumption_tabs[3]:  # Operational
            st.markdown("""
            ### Operational Assumptions
            
            1. Team Size
            - 2025: 15-20 people
            - 2026: 40-50 people
            - 2027: 80-100 people
            
            2. Infrastructure Scaling
            - AWS Reserved Instances
            - Multi-region deployment
            - Auto-scaling implementation
            
            3. Customer Support
            - Response Time: < 4 hours
            - Resolution Time: < 24 hours
            - Support Staff Ratio: 1:1000 users
            """)
            
            # Team Growth
            fig = px.bar(lt_team_growth, x='Year',
                        y=['Development', 'Sales', 'Support', 'Admin'],
                        title='Team Size Evolution',
                        barmode='stack')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_team_growth_chart")
            
        with longterm_tabs[1]:
            st.markdown("""
            ### Revenue Assumptions
            
            1. Subscription Plans
            - Basic: ₹499/month or ₹4,999/year
            - Pro: ₹999/month or ₹9,999/year
            - Premium: ₹1,499/month or ₹14,999/year
            
            2. Conversion Rates
            - Free to Paid: 15% → 20% → 25%
            - Monthly to Annual: 70% → 75% → 80%
            - Basic to Pro: 30% → 35% → 40%
            
            3. Institutional Pricing
            - Tier 1: ₹3,500 per student/year
            - Tier 2: ₹3,000 per student/year
            - Tier 3: ₹2,500 per student/year
            """)
            
            # Revenue Mix Evolution
            fig = px.bar(lt_revenue_mix, x='Year', y=['Student_Plans', 'Institutional'],
                        title='Revenue Mix Evolution (%)',
                        barmode='stack')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_revenue_mix_chart_1")
        
        with longterm_tabs[2]:
            st.markdown("""
            ### Cost Assumptions
            
            1. Fixed Costs
            - Development Team: 40% of operating costs
            - Infrastructure: 15% of operating costs
            - Admin & Support: 20% of operating costs
            
            2. Variable Costs
            - Customer Acquisition: ₹1,200 per individual user
            - Institutional Acquisition: ₹80,000 per institution
            - Server Costs: ₹15 per active user/month
            
            3. Marketing Spend
            - 2025: 25% of revenue
            - 2026: 20% of revenue
            - 2027: 15% of revenue
            """)
            
            # Cost Structure Evolution
            fig = px.area(lt_cost_structure, x='Year', 
                        y=['Development', 'Marketing', 'Infrastructure', 'Admin_Support'],
                        title='Cost Structure Evolution (%)')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_cost_structure_chart_1")
        
        with longterm_tabs[3]:
            st.markdown("""
            ### Operational Assumptions
            
            1. Team Size
            - 2025: 15-20 people
            - 2026: 40-50 people
            - 2027: 80-100 people
            
            2. Infrastructure Scaling
            - AWS Reserved Instances
            - Multi-region deployment
            - Auto-scaling implementation
            
            3. Customer Support
            - Response Time: < 4 hours
            - Resolution Time: < 24 hours
            - Support Staff Ratio: 1:1000 users
            """)
            
            # Team Growth
            fig = px.bar(lt_team_growth, x='Year',
                        y=['Development', 'Sales', 'Support', 'Admin'],
                        title='Team Size Evolution',
                        barmode='stack')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_team_growth_chart_1")
        
        # 2. Scenario Analysis
        st.subheader("Scenario Analysis")
        
        scenarios = st.selectbox(
            "Select Scenario",
            ["Conservative", "Base Case", "Aggressive"]
        )
        
        scenario_multipliers = {
            "Conservative": 0.7,
            "Base Case": 1.0,
            "Aggressive": 1.3
        }
        
        scenario_data = pd.DataFrame({
        'Metric': ['Revenue 2027', 'Users 2027', 'Market Share 2027', 'Gross Margin 2027'],
        'Conservative': [70000000, 70000, 8.1, 45],
        'Base Case': [100000000, 100000, 11.5, 55],
        'Aggressive': [130000000, 130000, 15.0, 65]
    }).set_index('Metric')  # Set Metric as index
    
        col1, col2 = st.columns(2)
        
        with col1:
            # Scenario Comparison
            fig = px.bar(lt_scenario_data, x='Metric',
                        y=[scenario for scenario in scenario_multipliers.keys()],
                        title='Scenario Comparison',
                        barmode='group')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_scenario_comparison_chart")
        
        with col2:
            # Selected Scenario Details
            st.metric("Revenue 2027", 
                    format_indian_currency(scenario_data.loc['Revenue 2027', scenarios]))
            st.metric("Users 2027", 
                    f"{scenario_data.loc['Users 2027', scenarios]:,.0f}")
            st.metric("Market Share 2027", 
                    f"{scenario_data.loc['Market Share 2027', scenarios]}%")
            st.metric("Gross Margin 2027", 
                    f"{scenario_data.loc['Gross Margin 2027', scenarios]}%")
            
            # 3. Competitive Benchmarks
            st.subheader("Competitive Benchmarks")
        
        benchmark_data = pd.DataFrame({
            'Metric': ['CAC', 'LTV', 'Gross Margin', 'Growth Rate'],
            'Acolyte': [1200, 9984, 55, 147.8],
            'Competitor A': [2500, 12000, 45, 100],
            'Competitor B': [1800, 8000, 50, 120],
            'Industry Avg': [2000, 10000, 48, 110]
        })
        
        fig = px.bar(benchmark_data, x='Metric',
                    y=['Acolyte', 'Competitor A', 'Competitor B', 'Industry Avg'],
                    title='Competitive Benchmark Comparison',
                    barmode='group')
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        # 4. Financial Metrics
        st.subheader("Key Financial Metrics")
        
        metric_tabs = st.tabs(["Profitability", "Efficiency", "Growth", "Valuation"])
        
        with metric_tabs[0]:
            # Profitability Metrics
            fig = px.line(lt_profitability_metrics, x='Year',
                        y=['Gross_Margin', 'Operating_Margin', 'EBITDA_Margin'],
                        title='Margin Evolution (%)')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_profitability_chart_1")
        
        with metric_tabs[1]:
            # Efficiency Metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("CAC Payback Period", "2.4 months")
                st.metric("LTV/CAC Ratio", "8.32")
            
            with col2:
                st.metric("Revenue per Employee", "₹12.5L")
                st.metric("Operating Leverage", "1.5x")
        
            with metric_tabs[2]:
                # Growth Metrics
                # Create date range
                quarters = pd.date_range(start='2025-04-01', end='2027-12-31', freq='Q')
                
                # Create growth rates list matching the length of quarters
                revenue_growth = [None, 147.8, 65.4] + [40] * (len(quarters) - 3)
                user_growth = [None, 150, 75] + [45] * (len(quarters) - 3)
                
                # Create DataFrame with matching lengths
                growth_metrics = pd.DataFrame({
                    'Quarter': quarters,
                    'Revenue_Growth': revenue_growth[:len(quarters)],
                    'User_Growth': user_growth[:len(quarters)]
                })
                
                fig = px.line(lt_growth_metrics, x='Quarter',
                            y=['Revenue_Growth', 'User_Growth'],
                            title='Growth Rates (%)')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True, key="lt_growth_metrics_chart")
        
        with metric_tabs[3]:
            # Valuation Metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Revenue Multiple", "10x")
                st.metric("ARR Multiple", "12x")
            
            with col2:
                st.metric("Growth Adjusted Multiple", "0.8x")
                st.metric("Rule of 40 Score", "85")
        
        # 5. Sensitivity Analysis
        st.subheader("Sensitivity Analysis")
        
        sensitivity_var = st.selectbox(
            "Select Variable for Sensitivity",
            ["User Growth Rate", "Pricing", "CAC", "Conversion Rate"]
        )
        
        # Create sensitivity matrix
        # For sensitivity analysis, use a base revenue value instead of the dictionary
        base_revenue_2027 = 100000000  # Base case 2027 revenue
        # Create sensitivity data using the base_revenue_2027 value
        sensitivity_range = [-20, -10, 0, 10, 20]
        lt_sensitivity_data = pd.DataFrame({
            'Change_%': sensitivity_range,
            'Revenue_Impact': [base_revenue_2027 * (1 + x/100) for x in sensitivity_range],
            'Margin_Impact': [55 + (x/2) for x in sensitivity_range]   
        })     
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(lt_sensitivity_data, x='Change_%',
                        y='Revenue_Impact',
                        title=f'Revenue Sensitivity to {sensitivity_var}')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_revenue_sensitivity_chart")
        
        with col2:
            fig = px.line(lt_sensitivity_data, x='Change_%',
                        y='Margin_Impact',
                        title=f'Margin Sensitivity to {sensitivity_var}')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True, key="lt_margin_sensitivity_chart")
        st.header("Medical Student Market Analysis")
    
        market_tabs = st.tabs(["Current Numbers", "Projections", "Market Opportunity"])
        
        with market_tabs[0]:
            # Current Numbers Analysis
            col1, col2, col3 = st.columns(3)
            
            current_metrics = {
                'total_colleges': 778,
                'annual_intake': 128275,
                'total_students': 705512  # 5.5 years * annual intake
            }
            
            with col1:
                st.metric("Total Medical Colleges", 
                        f"{current_metrics['total_colleges']:,}",
                        "Active Institutions")
            with col2:
                st.metric("Annual Intake", 
                        f"{current_metrics['annual_intake']:,}",
                        "Current Capacity")
            with col3:
                st.metric("Total Medical Students", 
                        f"{current_metrics['total_students']:,}",
                        "Across All Years")
                
            # Current Distribution Chart
            current_data = pd.DataFrame({
                'Category': ['MBBS Year 1', 'MBBS Year 2', 'MBBS Year 3', 
                            'MBBS Year 4', 'Internship'],
                'Students': [128275, 128275, 128275, 128275, 192412]  # 1.5x for internship
            })
            
            fig = px.bar(current_data, x='Category', y='Students',
                        title='Current Student Distribution',
                        color='Category')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        
        with market_tabs[1]:
            # Future Projections
            projection_data = pd.DataFrame({
                'Year': [2024, 2025, 2026, 2027],
                'Annual_Intake': [128275, 140000, 152000, 165000],
                'Total_Students': [705512, 770000, 836000, 907500],
                'Growth_Rate': [0, 9.1, 8.6, 8.5]
            })
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Growth Trajectory
                fig = px.line(projection_data, x='Year',
                            y=['Annual_Intake', 'Total_Students'],
                            title='Student Growth Projection')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Year-wise Metrics
                for _, row in projection_data.iterrows():
                    st.metric(
                        f"{row['Year']} Projections",
                        f"Total: {row['Total_Students']:,.0f}",
                        f"Intake: {row['Annual_Intake']:,.0f}"
                    )
            
            # Detailed Projections Table
            st.subheader("Detailed Projections")
            st.dataframe(projection_data.style.format({
                'Annual_Intake': '{:,.0f}',
                'Total_Students': '{:,.0f}',
                'Growth_Rate': '{:.1f}%'
            }))
        
        with market_tabs[2]:
            # Market Opportunity Analysis
            col1, col2 = st.columns(2)
            
            with col1:
                # Target Market Share
                market_share = pd.DataFrame({
                    'Year': [2025, 2026, 2027],
                    'Total_Market': [770000, 836000, 907500],
                    'Our_Target': [5000, 25000, 100000],
                    'Market_Share': [0.65, 2.99, 11.02]
                })
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=market_share['Year'],
                    y=market_share['Total_Market'],
                    name='Total Market'
                ))
                fig.add_trace(go.Bar(
                    x=market_share['Year'],
                    y=market_share['Our_Target'],
                    name='Our Target'
                ))
                fig.update_layout(
                    title='Market Size vs Our Target',
                    template="plotly_dark",
                    barmode='group'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Market Share Metrics
                for _, row in market_share.iterrows():
                    st.metric(
                        f"{row['Year']} Market Share",
                        f"{row['Market_Share']:.2f}%",
                        f"{row['Our_Target']:,.0f} users"
                    )
            
            # Market Segmentation
            st.subheader("Market Segmentation")
            segments = pd.DataFrame({
                'Segment': ['Total Available Market', 'Serviceable Available Market', 'Serviceable Obtainable Market'],
                'Students': [907500, 589875, 100000],
                'Percentage': [100, 65, 11.02]
            })
            
            fig = px.funnel(segments, x='Students', y='Segment',
                        title='Market Segmentation 2027')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        # Key Insights
        st.header("Key Market Insights")
        insights_col1, insights_col2 = st.columns(2)
        
        with insights_col1:
            st.markdown("""
            ### Market Growth
            - Current annual intake of 128,275 students
            - Projected to reach 165,000 by 2027
            - Steady growth rate of ~9% annually
            - Total student base growing to 907,500 by 2027
            """)
        
        with insights_col2:
            st.markdown("""
            ### Market Opportunity
            - Target market share of 11% by 2027
            - Focus on institutional partnerships
            - Digital channel complementing growth
            - Clear path to 100,000 users
            """)
        
        
    elif page == 'Investor Dashboard':
        st.title("Investor Dashboard")
        
        # Key Investment Metrics
        st.header("Investment Highlights")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Valuation",
                "₹5Cr",
                "Pre-money"
            )
        with col2:
            st.metric(
                "Target Raise",
                "₹25L",
                "5% Equity"
            )
        with col3:
            st.metric(
                "Monthly Burn",
                "₹2.08L",
                "Current"
            )
        with col4:
            st.metric(
                "Runway",
                "360 days",
                "With F&F Round"
            )

        # Market Opportunity
        st.header("Market Opportunity")
        market_col1, market_col2 = st.columns(2)
        
        with market_col1:
            # Total Addressable Market
            tam_data = pd.DataFrame({
                'Market': ['Total Available', 'Serviceable Available', 'Serviceable Obtainable'],
                'Value_Cr': [52, 33.7, 3.37],
                'Users': [870000, 565500, 56550]
            })
            
            fig = px.funnel(tam_data, x='Value_Cr', y='Market',
                        title='Market Size (₹ Crores)')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        
        with market_col2:
            # User Growth Potential
            target_users = pd.DataFrame({
                'Year': ['2025', '2026', '2027'],
                'Users': [5000, 25000, 100000],
                'Market_Share': [0.57, 2.87, 11.49]  # Percentage of TAM
            })
            
            fig = px.bar(target_users, x='Year', y='Users',
                        title='Projected User Base Growth')
            fig.add_trace(go.Scatter(x=target_users['Year'], 
                                    y=target_users['Market_Share'],
                                    name='Market Share %',
                                    yaxis='y2'))
            fig.update_layout(
                template="plotly_dark",
                yaxis2=dict(
                    title='Market Share %',
                    overlaying='y',
                    side='right'
                )
            )
            st.plotly_chart(fig, use_container_width=True)

        # Growth Metrics
        st.header("Growth Metrics")
        metrics_tab1, metrics_tab2 = st.tabs(["Revenue Growth", "Unit Economics"])
        
        with metrics_tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Revenue Projection
                rev_projection = pd.DataFrame({
                    'Quarter': ['Q2 2025', 'Q3 2025', 'Q4 2025'],
                    'Revenue': [1822000, 4515000, 7468000],
                    'Growth': ['Base', '147.8%', '65.4%']
                })
                
                fig = px.line(rev_projection, x='Quarter', y='Revenue',
                            title='Revenue Growth Trajectory')
                fig.update_traces(mode='lines+markers')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                # Revenue Distribution
                revenue_streams = pd.DataFrame({
                    'Stream': ['Student Plans', 'Institutional'],
                    'Share': [26, 74]
                })
                
                fig = px.pie(revenue_streams, values='Share', names='Stream',
                            title='Revenue Distribution Q4 2025')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        
        with metrics_tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                # Unit Economics
                st.subheader("Customer Acquisition Cost (CAC)")
                cac_data = pd.DataFrame({
                    'Channel': ['Institutional', 'Individual'],
                    'CAC': [80000, 1200],
                    'LTV': [630000, 9984],  # Annual revenue for institutional, yearly for individual
                    'LTV_CAC_Ratio': [7.87, 8.32]
                })
                
                fig = px.bar(cac_data, x='Channel', y='LTV_CAC_Ratio',
                            title='LTV/CAC Ratio by Channel')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Margins
                margins_data = pd.DataFrame({
                    'Quarter': ['Q2 2025', 'Q3 2025', 'Q4 2025'],
                    'Gross_Margin': [31.4, 44.6, 66.5]
                })
                
                fig = px.line(margins_data, x='Quarter', y='Gross_Margin',
                            title='Gross Margin Evolution (%)')
                fig.update_traces(mode='lines+markers')
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

        # Investment Use
        st.header("Use of Funds")
        fund_use = pd.DataFrame({
            'Category': ['Product Development', 'Market Expansion', 'Team & Operations', 'Working Capital'],
            'Percentage': [40, 35, 15, 10],
            'Amount': [2000000, 1750000, 750000, 500000]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(fund_use, values='Percentage', names='Category',
                        title='Fund Allocation')
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Detailed Fund Allocation")
            st.dataframe(fund_use.style.format({
                'Percentage': '{:.1f}%',
                'Amount': lambda x: format_indian_currency(x)
            }))

        # Key Milestones
        st.header("Key Milestones & Timeline")
        
        milestones = pd.DataFrame({
            'Timeline': ['Q2 2025', 'Q3 2025', 'Q4 2025'],
            'Users': [350, 1000, 5000],
            'Partnerships': ['5-7', '10-12', '15-20'],
            'Revenue Target': [1822000, 4515000, 7468000],
            'Key Achievement': ['Product Launch', 'Market Expansion', 'Break-even']
        })
        
        st.dataframe(milestones.style.format({
            'Users': '{:,.0f}',
            'Revenue Target': lambda x: format_indian_currency(x)
        }), use_container_width=True)

        # Risk Management
        st.header("Risk Management")
        
        risk_data = pd.DataFrame({
            'Risk Category': ['Market Adoption', 'Competition', 'Technology', 'Regulatory'],
            'Mitigation Strategy': [
                'Strategic partnerships with leading institutions',
                'Strong product differentiation and first-mover advantage',
                'Robust architecture and continuous innovation',
                'Compliance-first approach and legal advisory'
            ],
            'Impact Level': ['Medium', 'Low', 'Low', 'Low'],
            'Status': ['Managed', 'Monitored', 'Managed', 'Monitored']
        })
        
        st.dataframe(risk_data, use_container_width=True)
        # Add data input functionality
        if st.sidebar.checkbox('Show Data Input'):
            st.sidebar.subheader('Update Metrics')
            
            # Update user counts
            new_inst_users = st.sidebar.number_input('Institutional Users', 
                                                value=st.session_state.financial_data['users']['institutional'])
            new_digital_users = st.sidebar.number_input('Digital Users', 
                                                    value=st.session_state.financial_data['users']['digital'])
            
            # Update partnerships
            new_partnerships = st.sidebar.number_input('Active Partnerships', 
                                                    value=st.session_state.financial_data['partnerships']['active'])
            
        if st.sidebar.button('Update Metrics'):
            st.session_state.financial_data['users']['institutional'] = new_inst_users
            st.session_state.financial_data['users']['digital'] = new_digital_users
            st.session_state.financial_data['partnerships']['active'] = new_partnerships
            st.sidebar.success('Metrics updated successfully!')

        # Export/Import Data
        if st.sidebar.button("Export Data"):
            st.sidebar.download_button(
                label="Download JSON",
                data=json.dumps(st.session_state.financial_data, indent=2),
                file_name="acolyte_dashboard_data.json",
                mime="application/json"
            )
        
        uploaded_file = st.sidebar.file_uploader("Import Data (JSON)")
        if uploaded_file is not None:
            try:
                st.session_state.financial_data = json.load(uploaded_file)
                st.sidebar.success("Data imported successfully!")
            except Exception as e:
                st.sidebar.error(f"Error importing data: {str(e)}")
    
    elif page == 'Cap Table':
        st.title("Company Cap Table Analysis")
        
        # Define rounds data with comprehensive structure
        rounds_data = {
            'Initial Round': {
                'shares': {
                    'Nischay BK': {'shares': 500, 'type': 'Ordinary'},
                    'Subha': {'shares': 500, 'type': 'Ordinary'}
                },
                'share_price': 10,
                'investment': 0,
                'valuation': 10000
            },
            'Team Round': {
                'shares': {
                    'Nischay BK': {'shares': 500, 'type': 'Ordinary'},
                    'Subha': {'shares': 500, 'type': 'Ordinary'},
                    'Ayesha': {'shares': 83, 'type': 'Ordinary'},
                    'Jason': {'shares': 83, 'type': 'Ordinary'},
                    'Varun': {'shares': 83, 'type': 'Ordinary'},
                    'Boppl Pvt Ltd': {'shares': 416, 'type': 'Ordinary'}
                },
                'share_price': 10,
                'investment': 0,
                'valuation': 16650
            },
            'F&F Round': {
                'investment': 2500000,
                'ownership': 0.05,
                'share_price': 28409
            },
            'VC Round': {
                'investment': 50000000,
                'ownership': 0.10,
                'share_price': 256410
            }
        }

        def calculate_new_shares(target_ownership, existing_shares):
            """Calculate new shares to be issued based on target ownership percentage"""
            return round((target_ownership / (1 - target_ownership)) * existing_shares)

        def calculate_round_details():
            """Calculate share distributions for F&F and VC rounds"""
            # Calculate F&F Round details
            team_total = sum(holder['shares'] for holder in rounds_data['Team Round']['shares'].values())
            ff_new_shares = calculate_new_shares(rounds_data['F&F Round']['ownership'], team_total)
            
            ff_shares = {name: {'shares': data['shares'], 'type': data['type']} 
                        for name, data in rounds_data['Team Round']['shares'].items()}
            ff_shares['Friends & Family'] = {'shares': ff_new_shares, 'type': 'Preferred'}
            rounds_data['F&F Round']['shares'] = ff_shares
            
            # Calculate VC Round details
            ff_total = sum(holder['shares'] for holder in ff_shares.values())
            vc_new_shares = calculate_new_shares(rounds_data['VC Round']['ownership'], ff_total)
            
            vc_shares = {name: {'shares': data['shares'], 'type': data['type']} 
                        for name, data in ff_shares.items()}
            vc_shares['VC Investment'] = {'shares': vc_new_shares, 'type': 'Preferred'}
            rounds_data['VC Round']['shares'] = vc_shares

        # Calculate all round details
        calculate_round_details()

        # Round selection
        selected_round = st.selectbox('Select Round', list(rounds_data.keys()))
        round_data = rounds_data[selected_round]

        # Calculate key metrics
        total_shares = sum(holder['shares'] for holder in round_data['shares'].values())
        share_price = round_data['share_price']
        valuation = total_shares * share_price

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Share Price", f"₹{share_price:,}")
        with col2:
            st.metric("Total Shares", f"{total_shares:,}")
        with col3:
            st.metric("Valuation", f"₹{valuation:,}")
        with col4:
            st.metric("Investment", f"₹{round_data.get('investment', 0):,}")

        # Create shareholding details DataFrame
        df = pd.DataFrame([
            {
                'Shareholder': shareholder,
                'Type': data['type'],
                'Shares': data['shares'],
                'Percentage': round((data['shares']/total_shares) * 100, 2),
                'Value': data['shares'] * share_price
            }
            for shareholder, data in round_data['shares'].items()
        ])

        # Display shareholding details
        st.subheader("Shareholding Details")
        st.dataframe(
            df.style.format({
                'Shares': '{:,.0f}',
                'Percentage': '{:.2f}%',
                'Value': '₹{:,.2f}'
            }),
            use_container_width=True
        )

        # Visualization section
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Ownership Distribution")
            fig = px.pie(df, values='Shares', names='Shareholder',
                        title=f'{selected_round} Ownership Distribution',
                        color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Key Statistics")
            st.info(f"""
            • Total Shareholders: {len(df)}
            • Largest Shareholder: {df.iloc[df['Shares'].argmax()]['Shareholder']}
            • Average Holding: {df['Percentage'].mean():.2f}%
            • Total Value: ₹{valuation:,}
            """)

        # Dilution analysis
        if selected_round != 'Initial Round':
            st.subheader("Dilution from Previous Round")
            prev_round = list(rounds_data.keys())[list(rounds_data.keys()).index(selected_round) - 1]
            prev_data = rounds_data[prev_round]
            prev_total = sum(holder['shares'] for holder in prev_data['shares'].values())
            
            dilution_data = []
            for shareholder, data in prev_data['shares'].items():
                prev_percentage = (data['shares'] / prev_total) * 100
                current_percentage = (round_data['shares'].get(shareholder, {'shares': 0})['shares'] / total_shares) * 100
                dilution_data.append({
                    'Shareholder': shareholder,
                    'Previous %': prev_percentage,
                    'Current %': current_percentage,
                    'Change': current_percentage - prev_percentage
                })
            
            dilution_df = pd.DataFrame(dilution_data)
            st.dataframe(
                dilution_df.style.format({
                    'Previous %': '{:.2f}%',
                    'Current %': '{:.2f}%',
                    'Change': '{:+.2f}%'
                }).background_gradient(subset=['Change'], cmap='RdYlGn', vmin=-10, vmax=10),
                use_container_width=True
            )
# Footer
st.markdown("---")
st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")    