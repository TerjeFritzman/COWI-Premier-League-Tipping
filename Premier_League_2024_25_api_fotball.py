import streamlit as st
import pandas as pd
import requests

from predictions import predictions_data

# Set page configuration to use wide layout
st.set_page_config(layout='wide')

# Try to get API key from Streamlit secrets (for online), else from config.py (for local)
try:
    API_football_API_Key = st.secrets['API_football_API_Key']
except Exception:
    from config import API_football_API_Key


# Define the new range-based points system

# Helper to get the range for a position
def get_range_for_position(pos):
    if pos == 1:
        return "1"
    elif pos == 2:
        return "2"
    elif pos == 3:
        return "3"
    elif pos == 4:
        return "4"
    elif pos == 5:
        return "5"
    elif 6 <= pos <= 9:
        return "6-9"
    elif 10 <= pos <= 13:
        return "10-13"
    elif 14 <= pos <= 17:
        return "14-17"
    elif 18 <= pos <= 19:
        return "18-19"
    elif pos == 20:
        return "20"
    else:
        return None


# Helper to get points for a position
def get_points_for_position(pos):
    if pos == 1:
        return 10
    elif pos == 2:
        return 8
    elif pos == 3:
        return 6
    elif pos == 4:
        return 5
    elif pos == 5:
        return 4
    elif 6 <= pos <= 9:
        return 3
    elif 10 <= pos <= 13:
        return 2
    elif 14 <= pos <= 17:
        return 1
    elif 18 <= pos <= 19:
        return 4
    elif pos == 20:
        return 6
    else:
        return 0

# Function to get live Premier League table from API-Football
# @st.cache_data(ttl=3600)  # Cache data for 1 hour (3600 seconds)
def get_live_table():
    url = "https://api.football-data.org/v4/competitions/PL/standings"
    headers = {
        "X-Auth-Token": API_football_API_Key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        # Check if standings data exists
        if 'standings' in data and len(data['standings']) > 0:
            # Find the standings for the league table (type: TOTAL)
            league_table = None
            for s in data['standings']:
                if s.get('type') == 'TOTAL':
                    league_table = s.get('table')
                    break
            if league_table:
                table = pd.DataFrame(league_table)
                # Extract team name and stats
                table['Team'] = table['team'].apply(lambda x: x['name'])
                table['Position'] = table['position']
                table['Played'] = table['playedGames']
                table['Won'] = table['won']
                table['Draw'] = table['draw']
                table['Lost'] = table['lost']
                table['Goals For'] = table['goalsFor']
                table['Goals Against'] = table['goalsAgainst']
                table['+/-'] = table['Goals For'] - table['Goals Against']
                table['Points'] = table['points']
                # Rearrange columns
                table = table[['Position', 'Team', 'Played', 'Won', 'Draw', 'Lost', '+/-', 'Points']]
                return table
            else:
                st.error("No league table data available.")
                return pd.DataFrame()
        else:
            st.error("No standings data available.")
            return pd.DataFrame()
    else:
        st.error(f"Failed to fetch data. Status code: {response.status_code}")
        return pd.DataFrame()

# Convert predictions to DataFrame
predictions_df = pd.DataFrame(predictions_data)

# Function to calculate points for each prediction
def calculate_points(predictions, live_table):
    points = 0
    for predicted_position, team in enumerate(predictions, start=1):
        matching_row = live_table[live_table['Team'] == team]
        if not matching_row.empty:
            actual_position = matching_row['Position'].values[0]
            predicted_range = get_range_for_position(predicted_position)
            actual_range = get_range_for_position(actual_position)
            if predicted_position == actual_position:
                # Exact match: award full points for that position
                points += get_points_for_position(actual_position)
            elif predicted_range == actual_range:
                # In-range match: award range points
                points += get_points_for_position(actual_position)
    return points

# Streamlit app
st.title('Premier League Tabell')

# Create two columns
col1, col2 = st.columns([1, 2])

# Display live table in the first column
with col1:
    st.header('Nåværende stilling')
    live_table = get_live_table()
    if not live_table.empty:
        st.dataframe(live_table.set_index('Position'), height=738, width=600) 
    else:
        st.write("No data to display.")

# Display predictions and points in the second column
with col2:
    st.header('Tippinger & Poeng')

    # Calculate points for each participant
    points_data = {name: calculate_points(predictions, live_table) for name, predictions in predictions_df.items()}
    points_df = pd.DataFrame.from_dict(points_data, orient='index', columns=['Sum poeng'])


    # Calculate the number of exact and in-range matches for each column
    def count_correct_and_inrange(col):
        exact = 0
        inrange = 0
        for i, predicted_team in enumerate(col[:len(live_table['Team'])]):
            actual_team = live_table['Team'].iloc[i]
            matching_row = live_table[live_table['Team'] == predicted_team]
            if not matching_row.empty:
                actual_position = matching_row['Position'].values[0]
                predicted_range = get_range_for_position(i+1)
                actual_range = get_range_for_position(actual_position)
                if predicted_team == actual_team:
                    exact += 1
                elif predicted_range == actual_range:
                    inrange += 1
        return f"{exact} / {inrange}" if inrange > 0 else str(exact)

    matching_teams = predictions_df.apply(count_correct_and_inrange, axis=0)
    matching_teams_df = pd.DataFrame(matching_teams).T
    matching_teams_df.index = ["# Riktig (eksakt / i range)"]

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
        styles = []
        for i in range(min_length):
            predicted_team = s.iloc[i]
            actual_team = live_table['Team'].iloc[i]
            # Find actual position of predicted team
            matching_row = live_table[live_table['Team'] == predicted_team]
            if not matching_row.empty:
                actual_position = matching_row['Position'].values[0]
                predicted_range = get_range_for_position(i+1)
                actual_range = get_range_for_position(actual_position)
                if predicted_team == actual_team:
                    # Darker green for exact match, white text
                    styles.append('background-color: #14532d; color: #fff')  # very dark green
                elif predicted_range == actual_range:
                    # Slightly darker green for in-range, white text
                    styles.append('background-color: #238a4b; color: #fff')
                else:
                    styles.append('')
            else:
                styles.append('')
        styles += [''] * (len(s) - min_length)
        return styles

    # Pad the custom index values to make them wider
    custom_index = pad_index(list(range(1, 21)) + ["# Riktig", "Sum poeng"])
    full_predictions_df.index = custom_index

    styled_full_predictions_df = full_predictions_df.style.apply(highlight_matching_teams, axis=0)

    st.dataframe(styled_full_predictions_df, height=738+34+34+1, width=1500)

    # Create a column for expanders to align them horizontally
    expander_col1, expander_col2 = st.columns([1, 1])

    with expander_col1:
        with st.expander("Trykk for å se Sammenlagt Rangering"):
            st.header('Sammenlagt Rangering')

            # Rank participants by points in descending order
            standings_df = points_df.sort_values(by='Sum poeng', ascending=False).reset_index()
            standings_df.index += 1  # Start index from 1 for ranks
            standings_df.columns = ['Navn', 'Sum poeng']

            st.table(standings_df)

    with expander_col2:
        with st.expander("Trykk her for å se Poengsystemet"):
            st.header('Poengsystem')
            # Manually create the new range-based points system table
            points_table = [
                ("1", 10),
                ("2", 8),
                ("3", 6),
                ("4", 5),
                ("5", 4),
                ("6-9", 3),
                ("10-13", 2),
                ("14-17", 1),
                ("18-19", 4),
                ("20", 6),
            ]
            points_system_df = pd.DataFrame(points_table, columns=["Plassering", "Poeng"])
            st.dataframe(points_system_df, hide_index=True, use_container_width=True)
