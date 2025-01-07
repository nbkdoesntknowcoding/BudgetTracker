import streamlit as st
import pandas as pd
import plotly.express as px
# import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

if 'current_round' not in st.session_state:
    st.session_state.current_round = 'Initial Round'

st.title("Company Cap Table Analysis")

rounds_data = {
    'Initial Round': {
        'shares': {
            'Nischay BK': 500,
            'Subha': 500
        },
        'share_price': 10,
        'investment': 0
    },
    'Team Round': {
        'shares': {
            'Nischay BK': 500,
            'Subha': 500,
            'Ayesha': 83,
            'Jason': 83,
            'Varun': 83,
            'Boppl Pvt Ltd': 416
        },
        'share_price': 10,
        'investment': 0
    },
    'F&F Round': {
        'investment': 2500000,
        'ownership': 0.05
    },
    'VC Round': {
        'investment': 50000000,
        'ownership': 0.10
    }
}

def calculate_new_shares(target_ownership, existing_shares):
    return round((target_ownership / (1 - target_ownership)) * existing_shares)

def calculate_round_details():
    team_shares = rounds_data['Team Round']['shares']
    team_total = sum(team_shares.values())
    
    ff_new_shares = calculate_new_shares(rounds_data['F&F Round']['ownership'], team_total)
    ff_share_price = round(rounds_data['F&F Round']['investment'] / ff_new_shares)
    
    ff_shares = team_shares.copy()
    ff_shares['Friends & Family'] = ff_new_shares
    rounds_data['F&F Round']['shares'] = ff_shares
    rounds_data['F&F Round']['share_price'] = ff_share_price
    
    ff_total = sum(ff_shares.values())
    vc_new_shares = calculate_new_shares(rounds_data['VC Round']['ownership'], ff_total)
    vc_share_price = round(rounds_data['VC Round']['investment'] / vc_new_shares)
    
    vc_shares = ff_shares.copy()
    vc_shares['VC Investment'] = vc_new_shares
    rounds_data['VC Round']['shares'] = vc_shares
    rounds_data['VC Round']['share_price'] = vc_share_price

calculate_round_details()

selected_round = st.selectbox('Select Round', list(rounds_data.keys()))

round_data = rounds_data[selected_round]
total_shares = sum(round_data['shares'].values())
share_price = round_data['share_price']
valuation = total_shares * share_price

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Share Price", f"₹{share_price:,}")
with col2:
    st.metric("Total Shares", f"{total_shares:,}")
with col3:
    st.metric("Valuation", f"₹{valuation:,}")
with col4:
    st.metric("Investment", f"₹{round_data.get('investment', 0):,}")

df = pd.DataFrame([
    {
        'Shareholder': shareholder,
        'Shares': shares,
        'Percentage': round((shares/total_shares) * 100, 2),
        'Value': shares * share_price
    }
    for shareholder, shares in round_data['shares'].items()
])

st.subheader("Shareholding Details")
st.dataframe(
    df.style.format({
        'Shares': '{:,.0f}',
        'Percentage': '{:.2f}%',
        'Value': '₹{:,.2f}'
    }),
    use_container_width=True
)

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

if selected_round != 'Initial Round':
    st.subheader("Dilution from Previous Round")
    prev_round = list(rounds_data.keys())[list(rounds_data.keys()).index(selected_round) - 1]
    prev_data = rounds_data[prev_round]
    prev_total = sum(prev_data['shares'].values())
    
    dilution_data = []
    for shareholder, shares in prev_data['shares'].items():
        prev_percentage = (shares / prev_total) * 100
        current_percentage = (round_data['shares'].get(shareholder, 0) / total_shares) * 100
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

if __name__ == "__main__":
    pass