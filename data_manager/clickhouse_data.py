
from backend.clickhouse import get_ch_client, ch_execute_query
import streamlit as st
import pandas as pd

@st.cache_data
def load_market_share_data(
    category_id = '6433de7df79a2653906cd680'):
    # default to L1 category
    org = "NF"
    client = get_ch_client(org)
    params = {'param1': category_id}
    res = ch_execute_query(
            client,
            'queries/cmc_cohort.sql',
            params = params)
    res = res.dropna(subset=['time_period'])
    res.sort_values(by='date', inplace=True)
    return res

def load_total_market_cap():
    org = "NF"
    client = get_ch_client(org)
    res = ch_execute_query(
            client,
            'queries/cmc_total_market_cap.sql')
    res = res.dropna(subset=['time_period'])
    res['name'] = 'Total Crypto Market'
    res['symbol'] = 'TOTAL'
    res.sort_values(by='date', inplace=True)
    return res

def _execute_query(query_file, params=None):
    """Helper function to execute a query with standard parameters"""
    client = get_ch_client("NF")
    return ch_execute_query(client, f'queries/{query_file}.sql', params=params)

