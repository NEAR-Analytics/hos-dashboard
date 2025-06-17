import streamlit as st
st.set_page_config(layout="wide")
import plotly.express as px
import time
import pandas as pd
import datetime

from data_manager.clickhouse_data import _execute_query



net_flows_data = _execute_query('inflows_by_exchange')
net_flows_data['day_'] = pd.to_datetime(net_flows_data['day_']).dt.date

#st.dataframe(net_flows_data)
st.title('Net Flows')
st.caption(f"Last updated: {net_flows_data['day_'].max().strftime('%Y-%m-%d')}")

st.subheader('CEXs')
# Add filters
exchange_names = net_flows_data['exchange_name'].unique()
symbols = net_flows_data['symbol'].unique()

# Add 'None' option to exchange names
exchange_names = ['None'] + list(exchange_names)

# Set default date range
today = datetime.date.today()
first_day_of_year = datetime.date(today.year, 1, 1)

# Add filters in a single row
col1, col2, col3, col4 = st.columns(4)

with col1:
    selected_exchange = st.selectbox('Select Exchange', options=exchange_names, index=0)

with col2:
    selected_symbol = st.selectbox('Select Symbol', options=symbols, index=symbols.tolist().index('wNEAR'))

with col3:
    time_periods = {
        '7d': 7,
        '14d': 14,
        '30d': 30,
        '60d': 60,
        '90d': 90,
        '180d': 180
    }
    selected_period = st.selectbox('Select Time Period', options=list(time_periods.keys()), index=1)
    
with col4:
    selected_date_range = st.date_input(
        'Custom Date Range',
        value=[
            today - datetime.timedelta(days=time_periods[selected_period]) + datetime.timedelta(days=1),
            today
        ]
    )

# Filter data based on selections
if selected_exchange == 'None':
    filtered_data = net_flows_data[
        (net_flows_data['symbol'] == selected_symbol) &
        (net_flows_data['day_'].between(selected_date_range[0], selected_date_range[1]))
    ]
else:
    filtered_data = net_flows_data[
        (net_flows_data['exchange_name'] == selected_exchange) &
        (net_flows_data['symbol'] == selected_symbol) &
        (net_flows_data['day_'].between(selected_date_range[0], selected_date_range[1]))
    ]

# Ensure the y-axis columns are present and numeric
filtered_data['inbound_volume'] = pd.to_numeric(filtered_data['inbound_volume'], errors='coerce')
filtered_data['outbound_volume'] = pd.to_numeric(filtered_data['outbound_volume'], errors='coerce')

# Add metric widgets
net_flows = filtered_data['net_volume'].sum()
inflow = filtered_data['inbound_volume'].sum()
outflow = filtered_data['outbound_volume'].sum()

# Convert metrics to millions
net_flows_millions = net_flows / 1_000_000
inflow_millions = inflow / 1_000_000
outflow_millions = outflow / 1_000_000

# Display metrics horizontally
col1, col2, col3 = st.columns(3)

# Calculate previous period metrics
prev_start_date = selected_date_range[0] - datetime.timedelta(days=time_periods[selected_period])
prev_end_date = selected_date_range[0]

prev_filtered_data = net_flows_data[
    (net_flows_data['symbol'] == selected_symbol) &
    (net_flows_data['day_'].between(prev_start_date, prev_end_date))
]

prev_net_flows = prev_filtered_data['net_volume'].sum() / 1_000_000
prev_inflow = prev_filtered_data['inbound_volume'].sum() / 1_000_000
prev_outflow = prev_filtered_data['outbound_volume'].sum() / 1_000_000

# Calculate percentage changes
net_flows_pct = ((net_flows_millions - prev_net_flows) / abs(prev_net_flows) * 100) if prev_net_flows != 0 else 0
inflow_pct = ((inflow_millions - prev_inflow) / prev_inflow * 100) if prev_inflow != 0 else 0
outflow_pct = ((outflow_millions - prev_outflow) / prev_outflow * 100) if prev_outflow != 0 else 0

with col1:
    st.metric(
        label='Net Flows (M)', 
        value=f"{net_flows_millions:.2f}",
        delta=f"{net_flows_pct:.1f}%"
    )

with col2:
    st.metric(
        label='Inflow (M)', 
        value=f"{inflow_millions:.2f}",
        delta=f"{inflow_pct:.1f}%"
    )

with col3:
    st.metric(
        label='Outflow (M)', 
        value=f"{outflow_millions:.2f}",
        delta=f"{outflow_pct:.1f}%"
    )
st.caption("vs previous period")

# Add Plotly plot
# Create stacked bar chart
# Separate positive and negative data
positive_data = filtered_data[filtered_data['net_volume'] >= 0].copy()
negative_data = filtered_data[filtered_data['net_volume'] < 0].copy()

# Ensure consistent coloring across positive and negative bars for the same exchange
all_exchanges = sorted(filtered_data['exchange_name'].unique())
# Using a Plotly qualitative color sequence
colors_list = px.colors.qualitative.Plotly 
color_discrete_map = {
    exchange: colors_list[i % len(colors_list)]
    for i, exchange in enumerate(all_exchanges)
}
daily_totals = filtered_data.groupby('day_')['net_volume'].sum().reset_index()

# Add toggle button for exchange view
show_exchanges = st.toggle('Show Exchange Breakdown', value=False)

if show_exchanges:
    # 1. Create the initial figure with positive data
    fig = px.bar(
        positive_data,
        x='day_',
        y='net_volume',
        color='exchange_name',
        title='Daily Inflows and Outflows by Exchange',
        labels={'net_volume': 'Net Volume', 'day_': 'Date'},
        barmode='stack',
        color_discrete_map=color_discrete_map
    )

    # 2. Create a temporary figure for negative data
    negative_fig_temp = px.bar(
        negative_data,
        x='day_',
        y='net_volume',
        color='exchange_name',
        barmode='stack',
        color_discrete_map=color_discrete_map
    )

    # 3. Add all traces from the negative data figure to the main figure
    legend_entries_added_names = {trace.name for trace in fig.data}

    for trace in negative_fig_temp.data:
        if trace.name in legend_entries_added_names:
            trace.showlegend = False
        else:
            trace.showlegend = True 
            legend_entries_added_names.add(trace.name)
        fig.add_trace(trace)

    # 4. Calculate daily totals for the sum line
    

    # 5. Add line trace for total net flow
    fig.add_scatter(
        x=daily_totals['day_'],
        y=daily_totals['net_volume'],
        mode='lines+markers',
        name='Total Net Flow',
        line=dict(color='rgba(255, 255, 255, 0.9)', width=2.5),
        marker=dict(size=8, color='rgba(255, 255, 255, 0.9)', line=dict(width=1, color='black'))
    )

    # 6. Update layout for overall appearance and correct stacking behavior
    fig.update_layout(
        barmode='relative',
        xaxis_title='Date',
        yaxis_title='Net Volume',
        legend_title_text='Exchange Name',
        font=dict(color='white'),
        xaxis=dict(
            type='category',
            categoryorder='category ascending'  # This ensures dates are ordered correctly
        )
    )
else:
    # Create simplified view with just total bars
    fig = px.bar(
        daily_totals,
        x='day_',
        y='net_volume',
        title='Daily Total Net Flows',
        labels={'net_volume': 'Net Volume', 'day_': 'Date'},
        color='net_volume',
        color_continuous_scale=['red', 'white', 'green'],
        color_continuous_midpoint=0
    )
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Net Volume',
        font=dict(color='white'),
        xaxis=dict(
            type='category',
            categoryorder='category ascending'
        ),
        showlegend=False
    )

st.plotly_chart(fig, use_container_width=True)

with st.expander("Net Flow Statistics (Last 365 days)", expanded=False):
    st.subheader("Net Flow Distribution")
    wnear_net_flows = net_flows_data[net_flows_data['symbol'] == 'wNEAR']
    wnear_net_flows = wnear_net_flows[wnear_net_flows['day_'] >= datetime.date.today() - datetime.timedelta(days=365)]
    # Aggregate net flows by day
    daily_net_flows = wnear_net_flows.groupby('day_')['net_volume'].sum().reset_index()
    
    # Create histogram of daily aggregated flows
    daily_hist_fig = px.histogram(
        daily_net_flows,
        x='net_volume',
        nbins=50,
        title='Distribution of Daily Net Flows',
        labels={'net_volume': 'Daily Net Volume', 'count': 'Frequency'},
        color_discrete_sequence=['rgba(255, 255, 255, 0.7)']
    )
    
    daily_hist_fig.update_layout(
        xaxis_title='Daily Net Volume',
        yaxis_title='Frequency',
        font=dict(color='white'),
        showlegend=False
    )
    
    st.plotly_chart(daily_hist_fig, use_container_width=True)
    
    # Calculate and display statistics for daily aggregated flows
    daily_stats = daily_net_flows['net_volume'].describe()
    daily_stats_df = pd.DataFrame({
        'Statistic': ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
        'Value': [
            f"{daily_stats['count']:,.0f}",
            f"{daily_stats['mean']:,.2f}",
            f"{daily_stats['std']:,.2f}",
            f"{daily_stats['min']:,.2f}",
            f"{daily_stats['25%']:,.2f}",
            f"{daily_stats['50%']:,.2f}",
            f"{daily_stats['75%']:,.2f}",
            f"{daily_stats['max']:,.2f}"
        ]
    })
    
    st.dataframe(daily_stats_df, hide_index=True)
    
    # Create histogram
    hist_fig = px.histogram(
        wnear_net_flows,
        x='net_volume',
        nbins=50,
        title='Distribution of Net Flows by Exchange',
        labels={'net_volume': 'Net Volume', 'count': 'Frequency'},
        color_discrete_sequence=['rgba(255, 255, 255, 0.7)']
    )
    
    hist_fig.update_layout(
        xaxis_title='Net Volume',
        yaxis_title='Frequency',
        font=dict(color='white'),
        showlegend=False
    )
    
    st.plotly_chart(hist_fig, use_container_width=True)
    
    # Calculate and display statistics
    stats = wnear_net_flows['net_volume'].describe()
    stats_df = pd.DataFrame({
        'Statistic': ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
        'Value': [
            f"{stats['count']:,.0f}",
            f"{stats['mean']:,.2f}",
            f"{stats['std']:,.2f}",
            f"{stats['min']:,.2f}",
            f"{stats['25%']:,.2f}",
            f"{stats['50%']:,.2f}",
            f"{stats['75%']:,.2f}",
            f"{stats['max']:,.2f}"
        ]
    })
    
    st.dataframe(stats_df, hide_index=True)

with st.expander("Raw Data", expanded=False):
    st.markdown('#### Raw Data')
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_exchange = st.multiselect(
            'Filter by Exchange',
            options=sorted(net_flows_data['exchange_name'].unique()),
            default=[]
        )
    
    with col2:
        selected_symbol = st.multiselect(
            'Filter by Symbol',
            options=sorted(net_flows_data['symbol'].unique()),
            default=[]
        )
    
    with col3:
        date_range = st.date_input(
            'Filter by Date Range',
            value=(
                net_flows_data['day_'].min(),
                net_flows_data['day_'].max()
            ),
            min_value=net_flows_data['day_'].min(),
            max_value=net_flows_data['day_'].max()
        )
    
    # Apply filters
    filtered_raw_data = net_flows_data.copy()
    if selected_exchange:
        filtered_raw_data = filtered_raw_data[filtered_raw_data['exchange'].isin(selected_exchange)]
    if selected_symbol:
        filtered_raw_data = filtered_raw_data[filtered_raw_data['symbol'].isin(selected_symbol)]
    if len(date_range) == 2:
        filtered_raw_data = filtered_raw_data[
            (filtered_raw_data['day_'] >= date_range[0]) &
            (filtered_raw_data['day_'] <= date_range[1])
        ]
    st.dataframe(filtered_raw_data)
    
    # Add download buttons in a single row
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label='Download Raw Data as CSV',
            data=filtered_raw_data.to_csv(index=False),
            file_name='raw_data.csv',
            mime='text/csv'
        )

    with col2:
        st.download_button(
            label='Download Filtered Data as CSV',
            data=filtered_data.to_csv(index=False),
            file_name='filtered_data.csv',
            mime='text/csv'
        )







#st.subheader('NEAR Intents')


#st.subheader('Bridges')

