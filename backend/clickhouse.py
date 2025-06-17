import os
from dotenv import load_dotenv
import clickhouse_connect
import pandas as pd
load_dotenv()

def get_clickhouse_config(org = "NF"):

    if org == "NF":
        # First try environment variables
        return {
            'host': os.getenv('CH_NF_HOST'),
            'username': os.getenv('CH_USERNAME'),
            'password': os.getenv('CH_NF_PSWD'),
            'port': os.getenv('CH_PORT')
        }
    elif org == "DEFUSE_LABS":
        return {
            'host': os.getenv('CH_DEFUSE_LABS_HOST'),
            'username': os.getenv('CH_USERNAME'),
            'password': os.getenv('CH_DEFUSE_LABS_PSWD'),
            'port': os.getenv('CH_PORT')
        }
    else:
        raise Exception(f"ClickHouse config for organization {org} not found")
    
def get_ch_client(org = "NF"):

    config = get_clickhouse_config(org)
    client = clickhouse_connect.get_client(**config)
    return client

def ch_execute_query(client, query_path, params = None):
    if client is None:
        raise Exception("ClickHouse client not initialized")
    
    with open(query_path, 'r') as file:
        query = file.read()
    
    if params is not None:
        query = query.format(**params)
        print(query)
    try:
        result = client.query(query)
        return pd.DataFrame(result.result_set, columns=result.column_names)
    except Exception as e:
        print(f"Error executing query: {e}")
        raise