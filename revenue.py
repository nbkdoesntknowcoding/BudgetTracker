import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Acolyte Financial Metrics Dashboard",
    layout="wide"
)

# Function to format Indian currency
def format_indian_currency(amount):
    if amount >= 10000000:  # 1 Crore
        return f"₹{amount/10000000:.2f}Cr"
    elif amount >= 100000:  # 1 Lakh
        return f"₹{amount/100000:.2f}L"
    else:
        return f"₹{amount:,.0f}"

# Create quarterly revenue data
quarters = ['Q2 2025', 'Q3 2025', 'Q4 2025']
institutional_revenue = [2700000, 13500000, 27000000]  # Quarterly totals
individual_revenue = [867450, 2602350, 5204700]  # Quarterly totals

revenue_data = pd.DataFrame({
    'Quarter': quarters,
    'Institutional_Revenue': institutional_revenue,
    'Individual_Revenue': individual_revenue
})
revenue_data['Total_Revenue'] = revenue_data['Institutional_Revenue'] + revenue_data['Individual_Revenue']

# Dashboard Layout
st.title("Acolyte Financial Metrics Dashboard")

# Top Level Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Q4 2025 Revenue",
        format_indian_currency(revenue_data['Total_Revenue'].iloc[-1]),
        "Q4 Target"
    )

with col2:
    arr = revenue_data['Total_Revenue'].iloc[-1] * 4  # Annualized Q4 revenue
    st.metric(
        "ARR Run Rate",
        format_indian_currency(arr)
    )

with col3:
    st.metric(
        "Total Customers",
        "10,500",
        "9,000 Institutional + 1,500 Individual"
    )

with col4:
    q4_mrr = revenue_data['Total_Revenue'].iloc[-1] / 3  # Monthly average for Q4
    blended_arpu = q4_mrr / 10500
    st.metric(
        "Blended ARPU",
        format_indian_currency(blended_arpu)
    )

# Revenue Growth Chart
st.subheader("Quarterly Revenue Growth")
fig = go.Figure()
fig.add_trace(go.Bar(
    x=revenue_data['Quarter'],
    y=revenue_data['Institutional_Revenue'],
    name='Institutional Revenue'
))
fig.add_trace(go.Bar(
    x=revenue_data['Quarter'],
    y=revenue_data['Individual_Revenue'],
    name='Individual Revenue'
))
fig.update_layout(
    barmode='stack',
    title='Quarterly Revenue Breakdown',
    xaxis_title='Quarter',
    yaxis_title='Revenue (₹)'
)
st.plotly_chart(fig, use_container_width=True)

# Revenue Mix
st.subheader("Revenue Mix Analysis")
mix_col1, mix_col2 = st.columns(2)

with mix_col1:
    # Q4 Revenue Mix
    revenue_mix = pd.DataFrame({
        'Segment': ['Institutional', 'Individual'],
        'Revenue': [revenue_data['Institutional_Revenue'].iloc[-1], 
                   revenue_data['Individual_Revenue'].iloc[-1]]
    })
    fig = px.pie(revenue_mix, values='Revenue', names='Segment',
                 title='Q4 2025 Revenue Mix')
    st.plotly_chart(fig, use_container_width=True)

with mix_col2:
    # Quarter over Quarter Growth
    qoq_growth = ((revenue_data['Total_Revenue'].iloc[-1] / 
                   revenue_data['Total_Revenue'].iloc[0]) - 1) * 100
    st.metric("Q2 to Q4 Growth", f"{qoq_growth:.1f}%")
    st.metric("Q4 2025 MRR", format_indian_currency(q4_mrr))

# Unit Economics
st.subheader("Unit Economics")
unit_col1, unit_col2 = st.columns(2)

with unit_col1:
    st.metric("Institutional ARPU", "₹1,000", "Pro Plan")
    st.metric("Institutional CAC", "₹80,000", "Per Institution")
    st.metric("Institutional LTV", "₹36L", 
             "Based on 300 students × ₹1,000 × 12 months")

with unit_col2:
    st.metric("Individual Avg ARPU", "₹1,156", 
             "Blended across all plans")
    st.metric("Individual CAC", "₹1,200", "Per Student")
    st.metric("Individual LTV", "₹13,872", 
             "Based on 12 months retention")

# Growth Metrics
st.subheader("Growth Metrics")
growth_col1, growth_col2 = st.columns(2)

with growth_col1:
    # Growth Rates
    q2_to_q3_growth = ((revenue_data['Total_Revenue'].iloc[1] / 
                        revenue_data['Total_Revenue'].iloc[0]) - 1) * 100
    q3_to_q4_growth = ((revenue_data['Total_Revenue'].iloc[2] / 
                        revenue_data['Total_Revenue'].iloc[1]) - 1) * 100
    
    st.metric("Q2 to Q3 Growth", f"{q2_to_q3_growth:.1f}%")
    st.metric("Q3 to Q4 Growth", f"{q3_to_q4_growth:.1f}%")

with growth_col2:
    st.metric("Net Revenue Retention", "115%")
    st.metric("Gross Revenue Retention", "90%")

# Quarterly Revenue Table
st.subheader("Quarterly Revenue Breakdown")
revenue_data_display = revenue_data.copy()
for col in ['Institutional_Revenue', 'Individual_Revenue', 'Total_Revenue']:
    revenue_data_display[col] = revenue_data_display[col].apply(format_indian_currency)
st.dataframe(revenue_data_display)