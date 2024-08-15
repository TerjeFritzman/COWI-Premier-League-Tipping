import streamlit as st
import pandas as pd
import requests
from predictions import predictions_data

from config import API_football_API_Key

# Set page configuration to use wide layout
st.set_page_config(layout='wide')

# Define the points system based on ranking
points_system = {
    1: 10,
    2: 6,
    3: 5,
    4: 4,
    5: 3,
    6: 2,
    7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1,
    18: 2,
    19: 3,
    20: 4
}

# Function to get live Premier League table from API-Football
def get_live_table(season="2024"):
    url = "https://v3.football.api-sports.io/standings"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": API_football_API_Key  # Your actual API key
    }
    params = {
        "league": "39",  # Premier League ID
        "season": season  # Current season
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        # Check if 'response' key exists and is not empty
        if 'response' in data and len(data['response']) > 0:
            standings = data['response'][0]['league']['standings'][0]
            table = pd.DataFrame(standings)
            table = table[['rank', 'team', 'points', 'all']]
            table.columns = ['Position', 'Team', 'Points', 'All']
            table['Team'] = table['Team'].apply(lambda x: x['name'])
            table['Played'] = table['All'].apply(lambda x: x['played'])
            table['Won'] = table['All'].apply(lambda x: x['win'])
            table['Draw'] = table['All'].apply(lambda x: x['draw'])
            table['Lost'] = table['All'].apply(lambda x: x['lose'])
            table = table[['Position', 'Team', 'Played', 'Won', 'Draw', 'Lost', 'Points']]
            return table
        else:
            st.error("No standings data available.")
            return pd.DataFrame()
    else:
        st.error("Failed to fetch data.")
        return pd.DataFrame()

# Convert predictions to DataFrame
predictions_df = pd.DataFrame(predictions_data)

# Function to calculate points for each prediction
def calculate_points(predictions, live_table):
    points = 0
    for position, team in enumerate(predictions, start=1):
        matching_row = live_table[live_table['Team'] == team]
        if not matching_row.empty:
            actual_position = matching_row['Position'].values[0]
            if actual_position == position:
                points += points_system.get(position, 0)
    return points

# Streamlit app
st.title('Premier League Tabell 2024-2025')

# Create two columns
col1, col2 = st.columns([1, 2])

# Display live table in the first column
with col1:
    st.header('Nåværende stilling')
    live_table = get_live_table(season="2024")
    if not live_table.empty:
        st.dataframe(live_table.set_index('Position'), height=738, width=600)        
        with st.expander("Trykk her for å se poengsystemet"):
            # Create a DataFrame from the points_system dictionary
            points_system_df = pd.DataFrame(list(points_system.items()), columns=['Posisjon', 'Poeng'])
            # Create a new DataFrame with just the 'Poeng' column
            points_only_df = points_system_df[['Poeng']].copy()
            # Set a custom index
            points_only_df.index = list(range(1, len(points_only_df) + 1))
            # Rename the index column
            points_only_df.index.name = 'Index'
            # Display the table
            st.table(points_only_df)
    else:
        st.write("No data to display.")

# Display predictions and points in the second column
with col2:
    st.header('Tippinger & Poeng')

    # Calculate points for each participant
    points_data = {name: calculate_points(predictions, live_table) for name, predictions in predictions_df.items()}
    points_df = pd.DataFrame.from_dict(points_data, orient='index', columns=['Sum poeng'])

    # Calculate the number of matching teams for each column
    matching_teams = predictions_df.apply(lambda col: sum(col[:len(live_table['Team'])] == live_table['Team']), axis=0)
    matching_teams_df = pd.DataFrame(matching_teams).T
    matching_teams_df.index = ["# Riktig"]

    # Concatenate the predictions, correct predictions, and points
    full_predictions_df = pd.concat([predictions_df, matching_teams_df, points_df.T])

    # Reintroduce the custom index numbers
    custom_index = list(range(1, 21)) + ["# Riktig", "Sum poeng"]
    full_predictions_df.index = custom_index

    # Add padding to the index labels to make them wider
    def pad_index(index):
        return [f"{str(val): <10}" for val in index]

    # Apply the style to the full dataframe (including the matching row)
    def highlight_matching_teams(s):
        min_length = min(len(s), len(live_table['Team']))
        return ['background-color: green' if s.iloc[i] == live_table['Team'].iloc[i] else '' for i in range(min_length)] + [''] * (len(s) - min_length)

    # Pad the custom index values to make them wider
    custom_index = pad_index(list(range(1, 21)) + ["# Riktig", "Sum poeng"])
    full_predictions_df.index = custom_index

    styled_full_predictions_df = full_predictions_df.style.apply(highlight_matching_teams, axis=0)

    st.dataframe(styled_full_predictions_df, height=738+34+34+1, width=1500)
