import pandas as pd
import plotly.express as px



###### DATA FUNCTIONS ######
def get_total_cohort_df(df):
    total_by_period = df.groupby('time_period')['market_cap'].sum().reset_index()
    total_by_period['name'] = 'Total Crypto Market'
    total_by_period['symbol'] = 'TOTAL'
    total_by_period['date'] = df.groupby('time_period')['date'].first().values
    return total_by_period

def get_top_n_and_rest(df, n=10):
    # Get top n names based on today's market cap
    top_n_names = df[df['time_period'] == 'today'].nlargest(n, 'market_cap')['name']
    
    # Create mask for top n and rest
    mask = df['name'].isin(top_n_names)
    
    # Get rest of data grouped by time period
    rest = (df[~mask]
            .groupby('time_period')
            .agg({
                'market_cap': 'sum',
                'date': 'first'
            })
            .assign(name='Everyone Else', symbol='Everyone Else')
            .reset_index())
    
    return pd.concat([df[mask], rest]).reset_index()

def get_top_today(df):
    top_today = df[df['time_period'] == 'today']
    top_today.sort_values(by=['market_cap'], ascending=False, inplace=True)
    top_today['market_cap'] = top_today['market_cap'].apply(lambda x: '{:,.0f}'.format(x))
    top_today['market_share'] = top_today['market_share'].apply(lambda x: '{:,.2f}%'.format(x))
    top_today.index = top_today['name']
    top_today = pd.concat([top_today.loc[top_today['name'] != 'Everyone Else'], top_today.loc[top_today['name'] == 'Everyone Else']])
    top_today.drop(columns=['name'], inplace=True)
    return top_today

def get_diff_df(df):
    diff_df = df[df['time_period'] != 'today']
    diff_df = diff_df.merge(df[df['time_period'] == 'today'][['name', 'market_cap', 'market_share']], on='name', how='left', suffixes=('', '_today'))
    diff_df['market_cap_diff'] = diff_df['market_cap_today'] - diff_df['market_cap']
    diff_df['market_share_diff'] = (diff_df['market_share_today'] - diff_df['market_share']) * 100 #in bps
    diff_df.drop(columns=['market_cap_today', 'market_share_today'], inplace=True)
    return diff_df


###### PLOT FUNCTIONS ######
def get_market_cap_plot(df, title = 'Market Cap'):
    df['market_cap_m'] = df['market_cap'] / 1_000_000
    fig = px.line(
        df,
        x='date',
        y='market_cap_m',
        title=title,
        labels={
            'market_cap_m': 'Market Cap (M)', 
            'date': 'Date'
        },
        hover_data=['market_cap_m']
    )
    fig.update_traces(mode='lines+markers')

    # Customize x-axis to show time periods as labels
    fig.update_layout(
        xaxis={
            'ticktext': df['time_period'],
            'tickvals': df['date'],
            'tickmode': 'array'
        }
    )
    return fig

def get_market_share_plot(df, title = 'Market Share'):
    fig = px.line(
        df,
        x='date',
        y='market_share',
        title=title,
        labels={
            'market_share': 'Market Share (%)',
            'date': 'Date'
        },
        hover_data=['market_share'],
        color='name'
    )
    fig.update_traces(mode='lines+markers')

    # Customize x-axis to show time periods as labels 
    fig.update_layout(
        xaxis={
            'ticktext': df['time_period'],
            'tickvals': df['date'],
            'tickmode': 'array'
        }
    )
    return fig
