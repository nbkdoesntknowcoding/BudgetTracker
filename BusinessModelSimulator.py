import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Solar Panel Cleaning Business Model",
    layout="wide",
    initial_sidebar_state="expanded"
)

def calculate_base_metrics(capacity_mw=100):
    """Calculate base business metrics"""
    # Plant Metrics
    panels_per_mw = 3000
    total_panels = capacity_mw * panels_per_mw
    
    # Current Manual Cleaning Costs
    cost_per_panel_clean = 3.5  # INR
    cleanings_per_month = 2
    monthly_cleaning_cost = total_panels * cleanings_per_month * cost_per_panel_clean
    annual_cleaning_cost = monthly_cleaning_cost * 12
    
    # Generation Impact
    capacity_factor = 0.20
    annual_hours = 8760
    current_generation = capacity_mw * annual_hours * capacity_factor  # MWh
    power_price = 4  # INR/kWh
    current_revenue = current_generation * power_price * 1000  # Convert to kWh
    
    efficiency_improvement = 0.25  # 25% improvement
    improved_generation = current_generation * (1 + efficiency_improvement)
    improved_revenue = improved_generation * power_price * 1000
    
    # Convert to USD (approximate conversion)
    usd_conversion = 82
    annual_cleaning_usd = annual_cleaning_cost / usd_conversion
    revenue_improvement_usd = (improved_revenue - current_revenue) / usd_conversion
    
    return {
        'total_panels': total_panels,
        'annual_cleaning_usd': annual_cleaning_usd,
        'current_generation': current_generation,
        'improved_generation': improved_generation,
        'additional_generation': improved_generation - current_generation,
        'revenue_improvement_usd': revenue_improvement_usd
    }

def create_efficiency_waterfall(current_gen, improved_gen, power_price_usd=0.048):
    """Create waterfall chart showing efficiency impact"""
    current_value = current_gen * power_price_usd * 1000
    improved_value = improved_gen * power_price_usd * 1000
    
    fig = go.Figure(go.Waterfall(
        name="20MW Plant Example", 
        orientation="v",
        measure=["relative", "relative", "total"],
        x=["Current Revenue", "Efficiency Gain", "Improved Revenue"],
        y=[current_value/1e6, (improved_value-current_value)/1e6, 0],
        text=[f"${current_value/1e6:,.1f}M", f"+${(improved_value-current_value)/1e6:,.1f}M", 
              f"${improved_value/1e6:,.1f}M"],
        textposition="outside",
        decreasing={"marker":{"color":"#FF6B6B"}},
        increasing={"marker":{"color":"#4ECDC4"}},
        totals={"marker":{"color":"#45B7D1"}}
    ))
    
    fig.update_layout(
        title={"text": "Annual Revenue Impact", "x": 0.5},
        showlegend=False,
        height=400,
        yaxis_title="Revenue (Millions USD)",
        plot_bgcolor='white'
    )
    
    return fig

def create_model_comparison(annual_cleaning_cost, total_investment, annual_opex, service_revenue):
    """Create bar chart comparing business models"""
    models = ['Current Manual', 'Product Model', 'Service Model']
    costs = [annual_cleaning_cost, annual_opex, annual_opex]
    savings = [0, 
              annual_cleaning_cost - annual_opex,
              service_revenue - annual_opex]
    
    fig = go.Figure(data=[
        go.Bar(name='Cost', x=models, y=costs, marker_color='#FF6B6B'),
        go.Bar(name='Net Benefit', x=models, y=savings, marker_color='#4ECDC4')
    ])
    
    fig.update_layout(
        barmode='relative',
        title={"text": "Annual Cost & Benefit Comparison", "x": 0.5},
        height=400,
        yaxis_title="USD",
        plot_bgcolor='white'
    )
    
    return fig

def create_roi_chart(investment, monthly_benefit, service_monthly_profit):
    """Create ROI comparison chart"""
    months = list(range(24))
    product_roi = [-investment + (monthly_benefit * m) for m in months]
    service_roi = [service_monthly_profit * m for m in months]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=months,
        y=product_roi,
        name="Product Model",
        line=dict(color='#4ECDC4', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=months,
        y=service_roi,
        name="Service Model",
        line=dict(color='#45B7D1', width=3, dash='dot')
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title={"text": "24-Month Return on Investment", "x": 0.5},
        xaxis_title="Months",
        yaxis_title="Cumulative Return (USD)",
        height=400,
        plot_bgcolor='white'
    )
    
    return fig

def main():
    st.title("Solar Panel Cleaning Business Model Story 🌞")
    
    # Calculate base metrics
    metrics = calculate_base_metrics()
    
    # Basic Plant Information
    st.header("1. Understanding the Scale 📏")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Solar Panels", f"{metrics['total_panels']:,.0f}")
        st.markdown("These panels need cleaning twice a month")
        
    with col2:
        st.metric("Current Annual Cleaning Cost", f"${metrics['annual_cleaning_usd']:,.0f}")
        st.markdown("Current spending on manual cleaning")
    
    # Efficiency Impact
    st.header("2. Value Creation Potential 💰")
    efficiency_chart = create_efficiency_waterfall(
        metrics['current_generation'],
        metrics['improved_generation']
    )
    st.plotly_chart(efficiency_chart, use_container_width=True)
    
    # Business Model Comparison
    st.header("3. Business Model Comparison 📊")
    
    # Calculate model metrics
    machines_needed = 7
    cost_per_machine = 15000
    infrastructure_cost = 20000
    total_investment = (machines_needed * cost_per_machine) + infrastructure_cost
    annual_opex = total_investment * 0.0075 + (machines_needed * 3000)  # Maintenance + Operators
    
    # Service model calculations
    service_revenue = metrics['revenue_improvement_usd'] * 0.6  # 60% of value created
    
    comparison_chart = create_model_comparison(
        metrics['annual_cleaning_usd'],
        total_investment,
        annual_opex,
        service_revenue
    )
    st.plotly_chart(comparison_chart, use_container_width=True)
    
    # ROI Timeline
    st.header("4. Return on Investment Timeline 📈")
    monthly_benefit = metrics['annual_cleaning_usd'] / 12
    service_monthly_profit = (service_revenue - annual_opex) / 12
    
    roi_chart = create_roi_chart(
        total_investment,
        monthly_benefit,
        service_monthly_profit
    )
    st.plotly_chart(roi_chart, use_container_width=True)
    
    # Key Metrics
    st.header("5. Key Investment Metrics 🎯")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        payback_months = total_investment / monthly_benefit
        st.metric("Product Model Payback", f"{payback_months:.1f} months")
        
    with col2:
        service_roi = (service_monthly_profit * 12 / total_investment) * 100
        st.metric("Service Model ROI", f"{service_roi:.1f}%")
        
    with col3:
        st.metric("Annual Value Created", f"${metrics['revenue_improvement_usd']:,.0f}")
    
    # Key Insights
    st.header("6. Key Insights 💡")
    st.write("""
    1. **Significant Value Creation**: Our solution generates substantial additional revenue through improved efficiency
    2. **Quick Payback**: Product model investment recovered in less than a year
    3. **Attractive Service Model**: Generate consistent profits while removing client investment barrier
    4. **Sustainable Solution**: Reduces water usage and manual labor while improving solar farm efficiency
    """)

if __name__ == "__main__":
    main()