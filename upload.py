import streamlit as st
import pandas as pd
import requests

# Configure the Streamlit page
st.set_page_config(page_title="Albion Guild Rankings", page_icon="⚔️", layout="wide")

st.title("⚔️ Guild Member Rankings")
st.markdown("Explore the leaderboards for different statistics in the guild. Use the tabs to switch between stats and the search bar to find specific players.")

# Fetch data from the API and cache it for 1 hour (3600 seconds) to prevent spamming
@st.cache_data(ttl=3600)
def fetch_guild_data():
    url = "https://gameinfo.albiononline.com/api/gameinfo/guilds/XwoUKN3TRGKDRXnvjbc3Rg/members"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return []

# Process the nested JSON data into a flat Pandas DataFrame
def process_data(raw_data):
    if not raw_data:
        return pd.DataFrame()
        
    parsed_data = []
    for member in raw_data:
        # Extract base stats
        stats = {
            "Name": member.get("Name", "Unknown"),
            "Kill Fame": member.get("KillFame", 0),
            "Death Fame": member.get("DeathFame", 0),
            "Fame Ratio": member.get("FameRatio", 0.0),
        }
        
        # Safely extract nested Lifetime Statistics
        lifetime = member.get("LifetimeStatistics", {})
        
        stats["PvE Fame"] = lifetime.get("PvE", {}).get("Total", 0)
        stats["Crafting Fame"] = lifetime.get("Crafting", {}).get("Total", 0)
        
        # Gathering fame is usually nested one layer deeper under "All"
        stats["Gathering Fame"] = lifetime.get("Gathering", {}).get("All", {}).get("Total", 0)
        
        parsed_data.append(stats)
        
    return pd.DataFrame(parsed_data)

# Load and process the data
with st.spinner("Fetching data from Albion servers..."):
    raw_data = fetch_guild_data()
    df = process_data(raw_data)

if not df.empty:
    # Identify the columns that contain stats (everything except 'Name')
    stat_columns = [col for col in df.columns if col != "Name"]
    
    # Create a tab for every stat
    tabs = st.tabs(stat_columns)
    
    for tab, stat_name in zip(tabs, stat_columns):
        with tab:
            st.subheader(f"🏆 Top players by {stat_name}")
            
            # Create a layout with a search bar
            col1, col2 = st.columns([1, 3])
            with col1:
                search_term = st.text_input(f"🔍 Search Player", key=f"search_{stat_name}")
                
            # Prepare the dataframe for this specific stat
            # 1. Select Name and the specific stat
            # 2. Sort descending
            # 3. Reset index to create a clean ranking number
            stat_df = df[["Name", stat_name]].sort_values(by=stat_name, ascending=False).reset_index(drop=True)
            stat_df.index = stat_df.index + 1  # Make index 1-based instead of 0-based
            stat_df = stat_df.reset_index().rename(columns={"index": "Rank"})
            
            # Apply search filter if the user typed something
            if search_term:
                stat_df = stat_df[stat_df["Name"].str.contains(search_term, case=False, na=False)]
                
            # Formatting for better readability (adds commas to large numbers)
            if stat_name != "Fame Ratio":
                # Apply integer formatting with thousands separators for fame numbers
                column_config = {
                    stat_name: st.column_config.NumberColumn(
                        stat_name,
                        format="%d"
                    )
                }
            else:
                # Keep float formatting for Fame Ratio
                column_config = {}

            # Display the scrollable dataframe
            st.dataframe(
                stat_df,
                use_container_width=True,
                hide_index=True,
                height=500, # This height enforces the scrollable container
                column_config=column_config
            )
else:
    st.warning("No data found or failed to parse the guild data.")