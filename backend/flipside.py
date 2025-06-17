from flipside import Flipside
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

FLIPSIDE_API_KEY = os.environ["FLIPSIDE_API_KEY"]
FLIPSIDE_API_ENDPOINT = os.environ["FLIPSIDE_API_ENDPOINT"]


def get_fs_client():
    return Flipside(FLIPSIDE_API_KEY, FLIPSIDE_API_ENDPOINT)

def get_fs_data(query_path, page_number=1, page_size=1):
    fs_client = get_fs_client()
    with open(query_path, 'r') as f:
        query = f.read()
    query_result_set = fs_client.query(query, page_number=page_number, page_size=page_size)
    # set initial controlers
    current_page_number = 1
    page_size = 50000
    total_pages = 2 # will be replaced dynamically

    # we'll store all the page results in `all_rows`
    all_rows = []

    while current_page_number <= total_pages:
        results = fs_client.get_query_results(
            query_result_set.query_id,
            page_number=current_page_number,
            page_size=page_size
        )

        total_pages = results.page.totalPages
        if results.records:
            all_rows = all_rows + results.records
        
        current_page_number += 1

    # Convert to DataFrame
    df = pd.DataFrame(all_rows)
    # Find columns that look like dates (contain 'T00:00:00' pattern)
    date_columns = df.columns[df.apply(lambda x: x.astype(str).str.contains('T00:00:00', na=False)).any()]
    
    # Convert identified date columns to datetime then to string date format
    for col in date_columns:
        df[col] = pd.to_datetime(df[col]).dt.date
    return df