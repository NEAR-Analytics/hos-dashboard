import streamlit as st
st.set_page_config(layout="wide")
import plotly.express as px
import pandas as pd
from data_manager.clickhouse_data import _execute_query
from data_manager.helper_market_cap import (
    get_total_cohort_df,
    get_market_cap_plot,
    get_market_share_plot,
    get_top_n_and_rest,
    get_top_today,
    get_diff_df
)



###### Load Data ######

l1_mkt_share = _execute_query('cmc_l1_cohort')
l1_mkt_share.dropna(subset=['time_period'], inplace=True)
l1_mkt_share.sort_values(by='date', inplace=True)

l1_total_by_period = get_total_cohort_df(l1_mkt_share)
#l1_mkt_share = pd.concat([l1_total_by_period, l1_mkt_share], ignore_index=True)

ai_mkt_cap = _execute_query('cmc_ai_cohort')
ai_mkt_cap.dropna(subset=['time_period'], inplace=True)
ai_mkt_cap.sort_values(by='date', inplace=True)

ai_total_by_period = get_total_cohort_df(ai_mkt_cap)


total_market_cap = _execute_query('cmc_total_market_cap')
total_market_cap.dropna(subset=['time_period'], inplace=True)
total_market_cap.sort_values(by='date', inplace=True)
total_market_cap['name'] = 'Total Crypto Market'
total_market_cap['symbol'] = 'TOTAL'


# Assert that all values match between the two dataframes
pd.testing.assert_frame_equal(
    ai_mkt_cap[ai_mkt_cap['name'] == 'NEAR Protocol'].reset_index(drop=True),
    l1_mkt_share[l1_mkt_share['name'] == 'NEAR Protocol'].reset_index(drop=True),
    check_dtype=False
)



# Merge with original dataframe and calculate market share
ai_market_share = ai_mkt_cap.merge(ai_total_by_period, on='time_period', suffixes=('', '_total'))
ai_market_share['market_share'] = (ai_market_share['market_cap'] / ai_market_share['market_cap_total']) * 100
ai_market_share.drop(columns=['market_cap_total'], inplace=True)
near_market_cap = ai_market_share[ai_market_share['name'] == 'NEAR Protocol']

##### Total Market Cap #####
st.title('Market Cap')
st.caption(f"Last updated: {total_market_cap['date'].max().strftime('%Y-%m-%d')}")

# Get today's values
total_crypto_cap = total_market_cap[total_market_cap['time_period'] == 'today']['market_cap'].iloc[0]
l1_total_cap = l1_total_by_period[l1_total_by_period['time_period'] == 'today']['market_cap'].iloc[0]
ai_total_cap = ai_total_by_period[ai_total_by_period['time_period'] == 'today']['market_cap'].iloc[0]
near_total_cap = near_market_cap[near_market_cap['time_period'] == 'today']['market_cap'].iloc[0]

# Convert to millions
total_crypto_cap_m = total_crypto_cap / 1_000_000
l1_total_cap_m = l1_total_cap / 1_000_000
ai_total_cap_m = ai_total_cap / 1_000_000

near_ai_market_share = near_total_cap / ai_total_cap * 100
near_l1_market_share = near_total_cap / l1_total_cap * 100

# Display metrics horizontally
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label='Total Crypto Market Cap (M)', value=f"{total_crypto_cap_m:,.0f}")
    st.metric(label = 'NEAR Market Cap (M)', value = f"{near_total_cap / 1_000_000:,.0f}")

with col2:
    ai_pct = (ai_total_cap / total_crypto_cap) * 100
    st.metric(label='AI Market Cap (M)', value=f"{ai_total_cap_m:,.0f} ({ai_pct:.1f}%)")
    st.metric(label = 'NEAR AI Market Share', value = f"{near_ai_market_share:.2f}%")

with col3:
    l1_pct = (l1_total_cap / total_crypto_cap) * 100
    st.metric(label='L1 Market Cap (M)', value=f"{l1_total_cap_m:,.0f} ({l1_pct:.1f}%)")
    st.metric(label = 'NEAR L1 Market Share', value = f"{near_l1_market_share:.2f}%")

near_mkt_cap_plot = get_market_cap_plot(near_market_cap, title = 'NEAR Protocol Market Cap')
st.plotly_chart(near_mkt_cap_plot, use_container_width=True)

# Add category toggle
category = st.radio("Select Category", ["AI", "L1"], horizontal=True)

if category == "AI":
    st.subheader('AI Market Share')
    mkt_top = get_top_n_and_rest(ai_market_share, n=10)
    totals = mkt_top.groupby('time_period')['market_cap'].sum()
    mkt_share_plot = get_market_share_plot(mkt_top, title = 'AI Market Share')
else:
    st.subheader('L1 Market Share')
    mkt_top = get_top_n_and_rest(l1_mkt_share, n=20)
    totals = mkt_top.groupby('time_period')['market_cap'].sum()
    mkt_top['market_share'] = mkt_top.apply(lambda x: (x['market_cap'] / totals[x['time_period']]) * 100, axis=1)
    mkt_share_plot = get_market_share_plot(mkt_top, title = 'L1 Market Share')

st.plotly_chart(mkt_share_plot, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    # Create pie chart
    today_data = mkt_top[mkt_top['time_period'] == 'today'].copy()
    total_cap = today_data['market_cap'].sum()
    today_data['market_share'] = today_data['market_cap'] / total_cap * 100

    fig = px.pie(
        today_data,
        values='market_cap',
        names='name',
        title=f'{category} Token Market Cap Distribution Today',
        hover_data=['market_share'],
        labels={'market_share': 'Market Share (%)', 'market_cap': 'Market Cap'}
    )

    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    selected_period_table = st.selectbox(
        'Select Time Period',
        options=mkt_top['time_period'].unique(),
        key=f'{category.lower()}_time_period_table'
    )
    st.markdown(f"#### Market Cap - {selected_period_table}")
    
    period_data = mkt_top[mkt_top['time_period'] == selected_period_table].copy()
    period_data.sort_values(by=['market_cap'], ascending=False, inplace=True)
    period_data['market_cap'] = period_data['market_cap'].apply(lambda x: '{:,.0f}'.format(x))
    period_data['market_share'] = period_data['market_share'].apply(lambda x: '{:,.2f}%'.format(x))
    period_data.index = period_data['name']
    period_data = pd.concat([period_data.loc[period_data['name'] != 'Everyone Else'], period_data.loc[period_data['name'] == 'Everyone Else']])
    period_data.drop(columns=['name'], inplace=True)
    
    st.dataframe(period_data[['symbol', 'market_cap', 'market_share']])

diff_df = get_diff_df(mkt_top)
selected_period = st.selectbox(
    'Select Time Period',
    options=diff_df['time_period'].unique(),
    key=f'{category.lower()}_time_period',
    index=2
)

filtered_diff = diff_df[diff_df['time_period'] == selected_period].sort_values('market_share_diff')

# Create horizontal bar charts
fig_share = px.bar(
    filtered_diff,
    y='name',
    x='market_share_diff',
    orientation='h',
    title=f'Market Share Difference (basis points) vs Today - {selected_period}',
    labels={'market_share_diff': 'Market Share Difference (bps)', 'name': ''},
    text=filtered_diff['market_share_diff'].round(2)
)
fig_share.update_layout(showlegend=False)
fig_share.update_traces(textposition='outside')
st.plotly_chart(fig_share, use_container_width=True)

fig_cap = px.bar(
    filtered_diff,
    y='name',
    x='market_cap_diff',
    orientation='h',
    title=f'Market Cap Difference ($) vs Today - {selected_period}',
    labels={'market_cap_diff': 'Market Cap Difference ($)', 'name': ''},
    text=filtered_diff['market_cap_diff'].apply(lambda x: f'{x / 1_000_000:,.0f}')
)
fig_cap.update_layout(showlegend=False)
fig_cap.update_traces(textposition='outside')
st.plotly_chart(fig_cap, use_container_width=True)

# Raw Data Section with Expander
with st.expander("Raw Data", expanded=False):
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('#### L1 Market Share Raw Data')
        l1_mkt_share.sort_values(by=['date', 'market_cap'], ascending=[False, False], inplace=True)
        l1_mkt_share['market_cap'] = l1_mkt_share['market_cap'].apply(lambda x: '{:,.0f}'.format(x))
        st.dataframe(l1_mkt_share)
        st.download_button(
                label='Download L1 Market Share Raw Data as CSV',
                data=l1_mkt_share.to_csv(index=False),
                file_name='l1_market_share_raw_data.csv',
                mime='text/csv'
        )

    with col2:
        st.markdown('#### AI Market Share Raw Data')
        ai_mkt_cap.sort_values(by=['date', 'market_cap'], ascending=[False, False], inplace=True)
        ai_mkt_cap['market_cap'] = ai_mkt_cap['market_cap'].apply(lambda x: '{:,.0f}'.format(x))
        st.dataframe(ai_mkt_cap)
        st.download_button(
                label='Download AI Market Share Raw Data as CSV',
                data=ai_mkt_cap.to_csv(index=False),
                file_name='ai_market_share_raw_data.csv',
                mime='text/csv'
        )
