import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

# Configuration for the Streamlit page
st.set_page_config(
    page_title="Solar Panel Cleaning Business Model",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create a class to handle currency conversion
class CurrencyConverter:
    def __init__(self):
        self.base_url = "https://api.exchangerate-api.com/v4/latest/USD"
        self.rates = self._get_rates()
    
    def _get_rates(self):
        """Fetch latest currency rates from the API with error handling"""
        try:
            response = requests.get(self.base_url)
            if response.status_code == 200:
                return response.json()['rates']
            else:
                # Fallback rates if API fails
                return {'USD': 1, 'INR': 83.0, 'AED': 3.67}
        except:
            # Fallback rates if API fails
            print("catcjh")
            return {'USD': 1, 'INR': 83.0, 'AED': 3.67}
    
    def convert(self, amount, from_currency, to_currency):
        """Convert amount between currencies"""
        if from_currency == to_currency:
            return amount
        usd_amount = amount / self.rates[from_currency]
        return usd_amount * self.rates[to_currency]

# Create a class for weather impact calculations
class WeatherImpact:
    def __init__(self):
        self.impact_factors = {
            'temperature': {
                'low': 0.95,    # Below 20°C
                'medium': 1.0,   # 20-35°C
                'high': 0.90    # Above 35°C
            },
            'dust': {
                'low': 1.0,
                'medium': 0.85,
                'high': 0.70
            },
            'humidity': {
                'low': 1.0,
                'medium': 0.95,
                'high': 0.90
            }
        }
    
    def calculate_efficiency(self, temp_level, dust_level, humidity_level):
        """Calculate efficiency based on weather conditions"""
        return (self.impact_factors['temperature'][temp_level] * 
                self.impact_factors['dust'][dust_level] * 
                self.impact_factors['humidity'][humidity_level])
# Business Logic Class for Financial Calculations
class SolarCleaningBusinessModel:
    def __init__(self, mw_capacity, land_per_mw=4.5):
        self.mw_capacity = mw_capacity
        self.land_per_mw = land_per_mw
        self.panels_per_mw = 2500  # Standard 400W panels
        self.currency_converter = CurrencyConverter()
        self.weather_impact = WeatherImpact()

    def calculate_basic_metrics(self):
        """Calculate fundamental project metrics"""
        total_land = self.mw_capacity * self.land_per_mw
        total_panels = self.mw_capacity * self.panels_per_mw
        return {
            'total_land': total_land,
            'total_panels': total_panels
        }

    def calculate_cleaning_requirements(self, cleaning_rate, working_hours, efficiency, cleaning_frequency):
        """Calculate number of machines needed based on cleaning parameters"""
        metrics = self.calculate_basic_metrics()
        panels_per_day = cleaning_rate * 60 * working_hours * efficiency
        days_per_cleaning = 30 / cleaning_frequency  # Assuming monthly frequency
        required_machines = np.ceil(metrics['total_panels'] / (panels_per_day * days_per_cleaning))
        return required_machines

    def calculate_costs(self, machine_cost, required_machines, efficiency, currency='USD'):
        """Calculate initial and operational costs"""
        # Initial investment
        i=1
        if currency=="USD":
            i=1
        elif currency=="INR":
            i=83
        else:
            i=3.67
        equipment_cost = machine_cost * required_machines *i
        infrastructure_cost = equipment_cost * 0.2 
        total_investment = (equipment_cost + infrastructure_cost) 

        # Operating costs (monthly)
        operator_cost_per_machine = 250  # USD per month
        maintenance_cost_per_machine = machine_cost * 0.00625 # 0.75% annually
        monthly_opex = (operator_cost_per_machine + maintenance_cost_per_machine/12) * required_machines * i

        return {
            'equipment_cost': equipment_cost,
            'infrastructure_cost': infrastructure_cost,
            'total_investment': total_investment,
            'monthly_opex': monthly_opex
        }
class ServicePricing:
    def __init__(self, costs, market_data):
        self.costs = costs
        self.market_data = market_data
        
    def calculate_monthly_service_fee(self):
        """Calculate monthly service fee based on multiple factors"""
        # Base costs
        monthly_opex = self.costs['monthly_opex']
        
        # Equipment depreciation (assuming 5-year lifecycle)
        monthly_depreciation = self.costs['total_investment'] / (5 * 12)
        
        # Calculate value-based component
        power_improvement_value = self.calculate_power_improvement_value()
        
        # Market-based component
        market_rate_component = self.get_market_rate_component()
        
        # Calculate total fee
        base_cost = monthly_opex + monthly_depreciation
        profit_margin = 0.3  # 30% profit margin
        competitive_adjustment = 0.95  # 5% discount to market
        
        service_fee = (base_cost / (1 - profit_margin)) * competitive_adjustment
        
        # Ensure fee is competitive and valuable to customer
        min_fee = base_cost * 1.2  # Minimum 20% margin
        max_fee = min(power_improvement_value * 0.5, market_rate_component * 1.1)
        
        return np.clip(service_fee, min_fee, max_fee)
    
    def calculate_power_improvement_value(self):
        """Calculate the value of improved power generation"""
        # Assuming 15% improvement in power generation
        improved_generation = self.market_data['mw_capacity'] * 24 * 30 * 0.15  # MWh per month
        power_price = self.market_data['power_price']  # Price per MWh
        return improved_generation * power_price
    
    def get_market_rate_component(self):
        """Get market-based pricing component"""
        # Based on competitive analysis
        return self.market_data['market_cleaning_rate'] * self.market_data['total_panels']
def calculate_business_metrics(model, costs, market_data):
    """Calculate business metrics including service pricing"""
    service_pricing = ServicePricing(costs, market_data)
    monthly_service_fee = service_pricing.calculate_monthly_service_fee()
    
    return {
        'monthly_service_fee': monthly_service_fee,
        'annual_revenue': monthly_service_fee * 12,
        'monthly_profit': monthly_service_fee - costs['monthly_opex'],
        'roi': (monthly_service_fee * 12) / costs['total_investment']
    }
    
# Streamlit Interface
def main():
    st.title("Solar Panel Cleaning Business Model Simulator")
    # Create sidebar for input parameters

    with st.sidebar:
        st.header("Input Parameters")
        
        # Project Scale
        mw_capacity = st.slider("Solar Farm Capacity (MW)", 1, 1000, 100)
        cleaning_frequency = st.slider("Cleanings per Month", 1, 4, 2)
        
        # Equipment Parameters
        st.subheader("Equipment Parameters")
        cleaning_rate = st.number_input("Cleaning Rate (panels/minute)", 1, 50, 10)
        working_hours = st.number_input("Working Hours per Day", 1, 24, 8)
        efficiency = st.slider("Operational Efficiency (%)", 0, 100, 70) / 100
        machine_cost = st.number_input("Machine Cost (USD)", 5000, 10000000, 15000)
        
        # Weather Impact
        st.subheader("Weather Conditions")
        temperature_level = st.select_slider("Temperature Level", 
                                          options=['low', 'medium', 'high'],
                                          value='medium')
        dust_level = st.select_slider("Dust Level",
                                    options=['low', 'medium', 'high'],
                                    value='medium')
        humidity_level = st.select_slider("Humidity Level",
                                        options=['low', 'medium', 'high'],
                                        value='medium')
        
        # Currency Selection
        currency = st.selectbox("Display Currency", ['USD', 'INR', 'AED'])

    # Initialize business model
    model = SolarCleaningBusinessModel(mw_capacity)
    weather = WeatherImpact()
    
    # Calculate weather-adjusted efficiency
    weather_efficiency = weather.calculate_efficiency(temperature_level, dust_level, humidity_level)
    adjusted_efficiency = efficiency * weather_efficiency

    # Calculate requirements and costs
    required_machines = model.calculate_cleaning_requirements(
        cleaning_rate, working_hours, adjusted_efficiency, cleaning_frequency
    )
    
    costs = model.calculate_costs(machine_cost, required_machines, adjusted_efficiency,currency=currency)
        # Create market_data dictionary using model's methods
    basic_metrics = model.calculate_basic_metrics()
    market_data = {
        'mw_capacity': mw_capacity,
        'power_price': 60,  # USD per MWh
        'market_cleaning_rate': 0.3,  # USD per panel
        'total_panels': basic_metrics['total_panels']
    }

    # Calculate business metrics using ServicePricing
    business_metrics = calculate_business_metrics(model, costs, market_data)
    monthly_service_fee = business_metrics['monthly_service_fee']
    # Display Results in Two Columns
    col1, col2 = st.columns(2)
    l="$"
    if currency == "USD":
        l = "$"
    elif currency=="INR":
        l="Rs"
    else:
        l="AED"

    with col1:
        st.header("Purchase Model")
        st.metric("Required Machines", f"{int(required_machines)}")
        
        st.metric("Initial Investment", f"{l} {costs['total_investment']:,.2f}")
        st.metric("Monthly Operating Cost", f"{l} {costs['monthly_opex']:,.2f}")

    with col2:
        st.header("Service Model")
        monthly_service_fee = costs['monthly_opex'] * 2  # Example markup
        st.metric("Monthly Service Fee", f"{l} {monthly_service_fee:,.2f}")
        st.metric("Annual Service Revenue", f"{l} {monthly_service_fee * 12:,.2f}")

    # Create visualization for 5-year projection
    create_projections(costs, monthly_service_fee)

def create_projections(costs, monthly_service_fee):
    """Create comparative visualizations for purchase vs service model"""
    st.header("5-Year Financial Projections")
    
    # Generate monthly data for 5 years
    months = range(60)
    purchase_costs = [costs['total_investment'] + (costs['monthly_opex'] * m) for m in months]
    service_costs = [monthly_service_fee * m for m in months]
    
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Month': months,
        'Purchase Model (Cumulative Cost)': purchase_costs,
        'Service Model (Cumulative Cost)': service_costs
    })
    
    # Create line chart
    fig = px.line(df, x='Month', y=['Purchase Model (Cumulative Cost)', 
                                   'Service Model (Cumulative Cost)'],
                  title='Cumulative Cost Comparison')
    st.plotly_chart(fig, use_container_width=True)
        
if __name__ == "__main__":
    main()