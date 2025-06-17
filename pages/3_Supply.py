import streamlit as st
st.set_page_config(layout="wide")
import plotly.express as px
import pandas as pd
import os
from data_manager.clickhouse_data import _execute_query

# Load data

tvl = _execute_query('tvl')
tvl = tvl[tvl.token == 'NEAR']
tvl['utc_date'] = pd.to_datetime(tvl['utc_date'].dt.date)
tvl_aggregated = tvl.groupby('utc_date').agg({'amount': 'sum'}).reset_index()
tvl_aggregated = tvl_aggregated.rename(columns={'amount': 'tvl'})

df = _execute_query('supply')
df['utc_date'] = pd.to_datetime(df['utc_date'])
df = pd.merge(df, tvl_aggregated, on='utc_date', how='inner')


df['total_supply'] = df['total_supply'] / 1_000_000
df['circulating_supply'] = df['circulating_supply'] / 1_000_000
df['total_staked_supply'] = df['total_staked_supply'] / 1_000_000
df['tvl'] = df['tvl'] / 1_000_000
df['total_locked_supply'] = df['total_locked_supply'] / 1_000_000

df['passive_supply'] = df['total_locked_supply'] 
df['sticky_supply'] = (df['total_staked_supply'] + df['tvl']) # + cold storage and inst storage
df['active_supply'] = (df['circulating_supply'] - df['sticky_supply']) 
df.sort_values(by='utc_date', ascending=True, inplace=True)
# TO DO Add NF Funds --> remove from where?? staked?

assert round(df['total_supply'].iloc[-1], 2) == round(df['circulating_supply'].iloc[-1] + df['total_locked_supply'].iloc[-1], 2)
assert round(df['circulating_supply'].iloc[-1], 2) == round(df['active_supply'].iloc[-1] + df['total_staked_supply'].iloc[-1] + df['tvl'].iloc[-1], 2)



st.title('NEAR Supply Analysis')
st.caption(f"Last updated: {df['utc_date'].max().strftime('%Y-%m-%d')}")

# Display metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Supply (M)", f"{df['total_supply'].iloc[-1]:,.1f}")
with col2:
    st.metric("Total Circulating Supply (M)", f"{df['circulating_supply'].iloc[-1]:,.1f}")
with col3:
    st.metric("Total Locked Supply (M)", f"{df['total_locked_supply'].iloc[-1]:,.1f}")

    

st.header('Circulating Supply')
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Circulating Supply (M)", f"{df['circulating_supply'].iloc[-1]:,.1f}")
with col2:
    st.metric("Total Staked (M)", f"{df['total_staked_supply'].iloc[-1]:,.1f}")
with col3:
    st.metric("Total TVL (M)", f"{df['tvl'].iloc[-1]:,.1f}")
with col4:
    st.metric("Total Active Supply (M)", f"{df['active_supply'].iloc[-1]:,.1f}")

# Create stacked line chart for supply distribution
supply_distribution = df[['utc_date', 'active_supply', 'total_staked_supply', 'tvl', 'total_locked_supply']].drop_duplicates()
# Filter data from 2024-01-01
supply_distribution = supply_distribution[supply_distribution['utc_date'] >= '2024-01-01']

# Add view toggle
view_type = st.radio("Select View", ["Percentage of Total", "Cumulative", "Daily Changes"], horizontal=True)

if view_type == "Percentage of Total":
    # Calculate percentages of total supply
    percentage_distribution = supply_distribution.copy()
    for col in ['active_supply', 'total_staked_supply', 'tvl', 'total_locked_supply']:
        percentage_distribution[f'{col}_pct'] = (percentage_distribution[col] / df['total_supply']) * 100
    
    # Melt the percentage columns
    percentage_distribution_melted = percentage_distribution.melt(
        id_vars=['utc_date'],
        value_vars=['active_supply_pct', 'total_staked_supply_pct', 'tvl_pct', 'total_locked_supply_pct'],
        var_name='Supply Type',
        value_name='Percentage'
    )
    
    # Clean up the Supply Type labels
    percentage_distribution_melted['Supply Type'] = percentage_distribution_melted['Supply Type'].str.replace('_pct', '')
    
    fig_supply = px.area(percentage_distribution_melted,
                        x='utc_date',
                        y='Percentage',
                        color='Supply Type',
                        title='NEAR Supply Distribution as Percentage of Total Supply',
                        color_discrete_map={
                            'total_staked_supply': '#ff7f0e',
                            'active_supply': '#1f77b4',
                            'tvl': '#2ca02c',
                            'total_locked_supply': '#9467bd'
                        })
    
    fig_supply.update_layout(
        yaxis_title="Percentage of Total Supply (%)",
        xaxis_title="Date",
        legend_title="Supply Type"
    )
elif view_type == "Cumulative":
    supply_distribution_melted = supply_distribution.melt(id_vars=['utc_date'], var_name='Supply Type', value_name='Amount')
    
    fig_supply = px.area(supply_distribution_melted, 
                         x='utc_date', 
                         y='Amount',
                         color='Supply Type',
                         title='NEAR Supply Distribution Over Time',
                         color_discrete_map={
                            'total_staked_supply': '#ff7f0e', 
                            'active_supply': '#1f77b4',
                            'tvl': '#2ca02c',
                            'total_locked_supply': '#9467bd'
                         })
    
    fig_supply.update_layout(
        yaxis_title="Supply (NEAR)",
        xaxis_title="Date",
        legend_title="Supply Type"
    )
else:  # Daily Changes
    # Calculate daily changes
    daily_changes = supply_distribution.copy()
    for col in ['active_supply', 'total_staked_supply', 'tvl', 'total_locked_supply']:
        daily_changes[f'{col}_diff'] = daily_changes[col].diff()
    
    # Melt the diff columns
    daily_changes_melted = daily_changes.melt(
        id_vars=['utc_date'],
        value_vars=['active_supply_diff', 'total_staked_supply_diff', 'tvl_diff', 'total_locked_supply_diff'],
        var_name='Supply Type',
        value_name='Daily Change'
    )
    
    # Clean up the Supply Type labels
    daily_changes_melted['Supply Type'] = daily_changes_melted['Supply Type'].str.replace('_diff', '')
    
    fig_supply = px.bar(daily_changes_melted,
                        x='utc_date',
                        y='Daily Change',
                        color='Supply Type',
                        title='Daily Changes in NEAR Supply Distribution',
                        color_discrete_map={
                            'total_staked_supply': '#ff7f0e',
                            'active_supply': '#1f77b4',
                            'tvl': '#2ca02c',
                            'total_locked_supply': '#9467bd'
                        })
    
    fig_supply.update_layout(
        yaxis_title="Daily Change (NEAR)",
        xaxis_title="Date",
        legend_title="Supply Type",
        barmode='stack'
    )

st.plotly_chart(fig_supply, use_container_width=True)

# Add cohort selector and date filters
col1, col2, col3 = st.columns(3)

with col1:
    cohort = st.selectbox(
        "Select Cohort",
        options=[7, 14, 30, 60, 90, 120],
        index=3,  # Default to 60 days
        format_func=lambda x: f"{x}d"
    )

with col3:
    end_date = st.date_input(
        "End Date",
        value=df['utc_date'].max(),
        max_value=df['utc_date'].max()
    )

with col2:
    start_date = st.date_input(
        "Start Date",
        value=end_date - pd.Timedelta(days=cohort),
        min_value=df['utc_date'].min(),
        max_value=end_date
    )



# Update start_date when cohort or end_date changes
if st.session_state.get('_end_date') != end_date or st.session_state.get('_cohort') != cohort:
    start_date = end_date - pd.Timedelta(days=cohort)
    st.session_state['_end_date'] = end_date
    st.session_state['_cohort'] = cohort

# Calculate differences
filtered_df = df[(df['utc_date'].dt.date >= start_date) & (df['utc_date'].dt.date <= end_date)]
latest_values = filtered_df.iloc[-1]
earliest_values = filtered_df.iloc[0]

differences = pd.DataFrame({
    'Metric': ['Circulating Supply', 'Emissions', 'Locked Supply', 'Staked Supply', 'TVL', 'Active Supply'],
    'Start Value': [
        earliest_values['circulating_supply'],
        earliest_values['circulating_supply'] + earliest_values['total_locked_supply'],
        earliest_values['total_locked_supply'],
        earliest_values['total_staked_supply'],
        earliest_values['tvl'],
        earliest_values['active_supply']
    ],
    'End Value': [
        latest_values['circulating_supply'],
        latest_values['circulating_supply'] + latest_values['total_locked_supply'],
        latest_values['total_locked_supply'],
        latest_values['total_staked_supply'],
        latest_values['tvl'],
        latest_values['active_supply']
    ]
})

differences['Difference'] = differences['End Value'] - differences['Start Value']
differences['Percentage Change'] = (differences['Difference'] / differences['Start Value']) * 100

# Create differences chart
fig_differences = px.bar(
    differences,
    x='Metric',
    y='Difference',
    title=f'Supply Changes Over {cohort} Days',
    text_auto='.1f',
    color='Difference',
    color_continuous_scale=['red', 'green']
)

fig_differences.update_layout(
    yaxis_title="Change in Supply (M NEAR)",
    xaxis_title="Metric",
    showlegend=False
)

st.plotly_chart(fig_differences, use_container_width=True)

# Display detailed metrics
st.subheader('Detailed Changes')
differences_display = differences.copy()
differences_display['Start Value'] = differences_display['Start Value'].map('{:,.1f}'.format)
differences_display['End Value'] = differences_display['End Value'].map('{:,.1f}'.format)
differences_display['Difference'] = differences_display['Difference'].map('{:,.1f}'.format)
differences_display['Percentage Change'] = differences_display['Percentage Change'].map('{:,.1f}%'.format)
st.dataframe(differences_display, hide_index=True)

 
tab1, tab2 = st.tabs(["Staked NEAR", "TVL"])

with tab1:
    st.header('Staked NEAR')
    st.metric("Total Staked (M)", f"{df['total_staked_supply'].iloc[-1]:,.1f}")

    # Calculate date range for last 120 days
    max_date = df['utc_date'].max()
    min_date = max_date - pd.Timedelta(days=120)
    
    # Filter data for last 120 days
    staked_daily = df[df['utc_date'] >= min_date].copy()
    
    # Calculate daily differences
    staked_daily['daily_diff'] = staked_daily['total_staked_supply'].diff()
    
    # Create toggle for view selection
    view_type = st.radio(
        "Select View:",
        ["Total Staked", "Daily Changes"],
        horizontal=True
    )
    
    if view_type == "Total Staked":
        # Create line chart for daily staked NEAR
        fig_staked_daily = px.line(
            staked_daily,
            x='utc_date',
            y='total_staked_supply',
            title='Daily Staked NEAR (Last 120 Days)',
            labels={
                'utc_date': 'Date',
                'total_staked_supply': 'Staked NEAR (M)'
            }
        )
        
        fig_staked_daily.update_layout(
            xaxis_title="Date",
            yaxis_title="Staked NEAR (M)",
            showlegend=False
        )
    else:
        # Create bar chart for daily changes
        fig_staked_daily = px.bar(
            staked_daily,
            x='utc_date',
            y='daily_diff',
            title='Daily Changes in Staked NEAR (Last 120 Days)',
            labels={
                'utc_date': 'Date',
                'daily_diff': 'Change in Staked NEAR (M)'
            },
            color='daily_diff',
            color_continuous_scale=['red', 'green']
        )
        
        fig_staked_daily.update_layout(
            xaxis_title="Date",
            yaxis_title="Change in Staked NEAR (M)",
            showlegend=False
        )
    
    st.plotly_chart(fig_staked_daily, use_container_width=True)
    
    # # Create a histogram for staked NEAR distribution
    staked_top_holders_today = _execute_query('staked_top_holders_by_date', params={'date_param': end_date})
    staked_top_holders_today = staked_top_holders_today.drop_duplicates(subset=['account_id'])
    



    # # Calculate quartiles and print them with labels for clarity
    quartile_values = staked_top_holders_today['staked'].quantile([0.25, 0.5, 0.9, 0.95, 0.99]).to_list()
    quartile_labels = ['25th percentile', '50th percentile', '90th percentile', '95th percentile', '99th percentile']
    

    # # Define bucket labels and ranges
    labels = ['0-25%', '25-50%', '50-90%', '90-95%', '95-99%', '99-100%']
    ranges = [
        (0, quartile_values[0]),
        (quartile_values[0], quartile_values[1]),
        (quartile_values[1], quartile_values[2]),
        (quartile_values[2], quartile_values[3]),
        (quartile_values[3], quartile_values[4]),
        (quartile_values[4], staked_top_holders_today['staked'].max())
    ]

    # Create buckets
    staked_top_holders_today['Bucket'] = pd.cut(staked_top_holders_today['staked'], bins=[0] + quartile_values + [staked_top_holders_today['staked'].max()], labels=labels, include_lowest=True, right=True)

    # Calculate total staked amount per bucket
    bucket_totals = staked_top_holders_today.groupby('Bucket')['staked'].sum().reset_index()
    bucket_totals['staked'] = bucket_totals['staked'] / 1_000_000  # Convert to millions
    # Calculate number of unique accounts per bucket
    bucket_accounts = staked_top_holders_today.groupby('Bucket')['account_id'].nunique().reset_index()
    bucket_accounts.columns = ['Bucket', 'num_accounts']

    # Merge with bucket_totals
    bucket_totals = bucket_totals.merge(bucket_accounts, on='Bucket')

    # Calculate percentage of total staked amount
    total_staked = staked_top_holders_today['staked'].sum() / 1_000_000
    bucket_totals['Percentage'] = (bucket_totals['staked'] / total_staked) * 100
    
    col1, col2 = st.columns(2)
    with col1:
        fig_pie = px.pie(bucket_totals, 
                        values='staked', 
                        names='Bucket',
                        title='Distribution of Staked NEAR by Quantile',
                        hover_data={'staked': ':,.1f M'})

        fig_pie.update_layout(
            legend_title="Quartile Range",
            showlegend=True
        )
        

        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:

        st.dataframe(bucket_totals)

    st.subheader('99%-100% Holders')
    st.write("* meta-pool.near and linear.near are LST providers")
    premium_stakers = staked_top_holders_today[staked_top_holders_today['Bucket'] == '99-100%'][["account_id", "staked"]]
    premium_stakers['staked'] = premium_stakers['staked'] / 1_000_000  # Convert to millions
    premium_stakers = premium_stakers.sort_values(by='staked', ascending=False)
    premium_stakers['percent_of_total'] = premium_stakers['staked'] / premium_stakers['staked'].sum() * 100
    premium_stakers['cumulative_percent'] = premium_stakers['percent_of_total'].cumsum()
    st.dataframe(premium_stakers)

with tab2:
    st.header('TVL')
    st.metric("Total TVL (M)", f"{df['tvl'].iloc[-1]:,.1f}")

    # Filter data from 2024-01-01
    tvl_historical = tvl[tvl['utc_date'] >= '2024-01-01']
    tvl_historical = tvl_historical[tvl_historical['token'] == 'NEAR']
    tvl_historical['amount'] = tvl_historical['amount'] / 1_000_000  # Convert to millions
    
    # Add view toggle
    tvl_view_type = st.radio("Select TVL View", ["Cumulative", "Daily Changes"], horizontal=True)

    if tvl_view_type == "Cumulative":
        # Group by date and sum TVL
        tvl_by_date = tvl_historical.groupby('utc_date')['amount'].sum().reset_index()
        
        fig_tvl = px.line(tvl_by_date,
                         x='utc_date',
                         y='amount',
                         title='NEAR TVL Over Time',
                         labels={'amount': 'TVL (M NEAR)', 'utc_date': 'Date'})
        
        fig_tvl.update_layout(
            yaxis_title="TVL (M NEAR)",
            xaxis_title="Date"
        )
    else:  # Daily Changes
        # Calculate daily changes
        tvl_by_date = tvl_historical.groupby('utc_date')['amount'].sum().reset_index()
        tvl_by_date['daily_change'] = tvl_by_date['amount'].diff()
        
        fig_tvl = px.bar(tvl_by_date,
                        x='utc_date',
                        y='daily_change',
                        title='Daily Changes in NEAR TVL',
                        labels={'daily_change': 'Daily Change (M NEAR)', 'utc_date': 'Date'})
        
        fig_tvl.update_layout(
            yaxis_title="Daily Change (M NEAR)",
            xaxis_title="Date"
        )

    st.plotly_chart(fig_tvl, use_container_width=True)
    
    # Create a histogram for TVL distribution

    tvl_present = tvl[tvl['utc_date'] == tvl['utc_date'].max()]
    tvl_present = tvl_present[tvl_present['token'] == 'NEAR']
    tvl_present = tvl_present[tvl_present['amount'] > 0]
    tvl_present['amount'] = tvl_present['amount'] / 1_000_000
    tvl_present = tvl_present.groupby('protocol')['amount'].sum().reset_index()
    total_row = pd.DataFrame({
        'protocol': ['Total'],
        'amount': [tvl_present['amount'].sum()]
    })
    tvl_present = pd.concat([tvl_present, total_row], ignore_index=True)
    quartiles = tvl_present['amount'].quantile([0.25, 0.5, 0.75]).to_list()
    # Define bucket labels and ranges
    labels = ['0-25%', '25-50%', '50-75%', '75-100%']
    ranges = [
        (0, quartiles[0]),
        (quartiles[0], quartiles[1]),
        (quartiles[1], quartiles[2]),
        (quartiles[2], tvl_present['amount'].max())
    ]

    # Create buckets
    tvl_present['Bucket'] = pd.cut(tvl_present['amount'], bins=[0] + quartiles + [tvl_present['amount'].max()], labels=labels, include_lowest=True, right=True)

    # Calculate total TVL per bucket
    bucket_totals = tvl_present.groupby('Bucket')['amount'].sum().reset_index()
    # Calculate number of unique accounts per bucket
    bucket_accounts = tvl_present.groupby('Bucket')['protocol'].nunique().reset_index()
    bucket_accounts.columns = ['Bucket', 'num_protocols']

    # Merge with bucket_totals
    bucket_totals = bucket_totals.merge(bucket_accounts, on='Bucket')

    # Calculate percentage of total TVL
    total_tvl = tvl_present['amount'].sum()
    bucket_totals['Percentage'] = (bucket_totals['amount'] / total_tvl) * 100
    
    col1, col2 = st.columns(2)
    with col1:
        fig_pie = px.pie(bucket_totals, 
                        values='amount', 
                        names='Bucket',
                        title='Distribution of TVL by Quantile',
                        hover_data={'amount': ':.0f'})

        fig_pie.update_layout(
            legend_title="Quartile Range",
            showlegend=True
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.dataframe(bucket_totals)

    st.subheader('75%-100% Holders')
    st.write("* Includes major DeFi protocols and DEXes")
    premium_holders = tvl_present[tvl_present['Bucket'] == '75-100%'][["protocol", "amount"]]
    premium_holders = premium_holders.sort_values(by='amount', ascending=False)
    premium_holders['percent_of_total'] = premium_holders['amount'] / premium_holders['amount'].sum() * 100
    premium_holders['cumulative_percent'] = premium_holders['percent_of_total'].cumsum()
    st.dataframe(premium_holders)



with st.expander("Raw Data", expanded=False):
    st.dataframe(df)
