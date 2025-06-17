import streamlit as st

from backend.flipside import get_fs_data

if 'data_reloader' not in st.session_state:
    st.session_state['data_reloader'] = 0

@st.cache_data
def load_inflows_by_exchange_data():
    return get_fs_data('queries/flipside/inflows_by_exchange.sql')

@st.cache_data
def load_top_movers_data():
    return get_fs_data('queries/flipside/top_movers.sql')

@st.cache_data
def load_supply_data():
    return get_fs_data('queries/flipside/supply.sql')

@st.cache_data
def load_tvl_defilama_data():
    return get_fs_data('queries/flipside/tvl_defilama.sql')

def trigger_net_flows_update():
    st.session_state['data_reloader'] += 1


