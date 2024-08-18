import streamlit as st
import requests

from config import API_football_API_Key

BASE_URL = 'https://v3.football.api-sports.io/'

# Function to get Premier League table
def get_premier_league_table():
    url = f"{BASE_URL}standings?season=2024&league=39"  # League ID 39 is for Premier League
    headers = {
        'x-apisports-key': API_football_API_Key
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    
    # Extract the standings data
    standings = data['response'][0]['league']['standings'][0]  # Extracting the first group
    return standings

# Streamlit app layout
st.title("Premier League Table")

# Get and display Premier League table
table = get_premier_league_table()

if table:
    for team in table:
        st.write(f"{team['rank']}. {team['team']['name']} - {team['points']} pts")
else:
    st.write("Unable to retrieve the Premier League table.")

