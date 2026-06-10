import streamlit as st
import pandas as pd
import requests

# Configure the Streamlit page without emojis
st.set_page_config(page_title="Albion Guild Rankings", layout="wide")

# Inject Custom CSS to center text everywhere
st.markdown("""
<style>
    /* Center all headers and paragraph text */
    h1, h2, h3, h4, h5, h6, p {
        text-align: center !important;
        justify-content: center !important;
    }
    
    /* Center the contents of the block container */
    .block-container {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* Center input fields and their labels */
    .stTextInput > div[data-baseweb="input"] {
        text-align: center;
    }
    .stTextInput input {
        text-align: center !important;
    }
    
    /* Center the Tabs */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
    }
    
    /* Center selectbox text */
    div[data-baseweb="select"] {
        justify-content: center;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("Guild Member Rankings")
st.markdown("Explore the leaderboards for different statistics in the guild. Select a main category below, choose a subcategory, and use the search bar to find specific players.")

@st.cache_data(ttl=3600)
def fetch_guild_data():
    url = "https://gameinfo.albiononline.com/api/gameinfo/guilds/XwoUKN3TRGKDRXnvjbc3Rg/members"
    try:
        response = requests.get(url)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return []

def process_data(raw_data):
    if not raw_data:
        return pd.DataFrame()
        
    parsed_data = []
    
    # Map API keys to user-friendly subcategory names
    sub_keys = {
        "Total": "Total",
        "Royal": "Mainland (Royal)",
        "Outlands": "Outlands",
        "Avalon": "Avalon",
        "Hellgate": "Hellgate",
        "CorruptedDungeon": "Corrupted Dungeon",
        "Mists": "Mists"
    }
    
    for member in raw_data:
        # Base stats (Combat)
        stats = {
            "Name": member.get("Name", "Unknown"),
            "Kill Fame": member.get("KillFame", 0),
            "Death Fame": member.get("DeathFame", 0),
            "Fame Ratio": member.get("FameRatio", 0.0),
        }
        
        lifetime = member.get("LifetimeStatistics", {})
        
        # PvE Subcategories
        pve = lifetime.get("PvE", {})
        for api_key, display_name in sub_keys.items():
            stats[f"PvE - {display_name}"] = pve.get(api_key, 0)
            
        # Crafting Subcategories
        crafting = lifetime.get("Crafting", {})
        for api_key, display_name in sub_keys.items():
            stats[f"Crafting - {display_name}"] = crafting.get(api_key, 0)
            
        # Gathering Subcategories (Nested under "All")
        gathering = lifetime.get("Gathering", {}).get("All", {})
        for api_key, display_name in sub_keys.items():
            stats[f"Gathering - {display_name}"] = gathering.get(api_key, 0)
            
        parsed_data.append(stats)
        
    return pd.DataFrame(parsed_data)

# Fetch and process data
with st.spinner("Fetching data from Albion servers..."):
    raw_data = fetch_guild_data()
    df = process_data(raw_data)

if not df.empty:
    # Define our Main Categories
    tabs = st.tabs(["Combat", "PvE", "Gathering", "Crafting"])
    
    # Define which stats belong to which tab
    category_mappings = {
        "Combat": ["Kill Fame", "Death Fame", "Fame Ratio"],
        "PvE": [col for col in df.columns if col.startswith("PvE - ")],
        "Gathering": [col for col in df.columns if col.startswith("Gathering - ")],
        "Crafting": [col for col in df.columns if col.startswith("Crafting - ")]
    }

    # Function to render the UI for a specific tab
    def render_tab_content(tab_name, stat_columns):
        # Clean up names for the dropdown box (e.g. "PvE - Avalon" -> "Avalon")
        display_options = [col.split(" - ")[-1] if " - " in col else col for col in stat_columns]
        
        col1, col2 = st.columns([1, 1])
        with col1:
            selected_display = st.selectbox("Select Subcategory", display_options, key=f"select_{tab_name}")
        with col2:
            search_term = st.text_input("Search Player", key=f"search_{tab_name}")
            
        # Get the actual dataframe column name based on selection
        actual_stat_name = stat_columns[display_options.index(selected_display)]
        
        # Prepare Data
        stat_df = df[["Name", actual_stat_name]].copy()
        stat_df = stat_df.sort_values(by=actual_stat_name, ascending=False).reset_index(drop=True)
        stat_df.index = stat_df.index + 1
        stat_df = stat_df.reset_index().rename(columns={"index": "Rank"})
        
        # Filter by search
        if search_term:
            stat_df = stat_df[stat_df["Name"].str.contains(search_term, case=False, na=False)]
            
        # Format commas and center text using Pandas Styler
        format_dict = {actual_stat_name: "{:,.2f}" if "Ratio" in actual_stat_name else "{:,}"}
        
        styled_df = stat_df.style \
            .set_properties(**{'text-align': 'center'}) \
            .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}]) \
            .format(format_dict)
            
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=500
        )

    # Render each tab
    for tab, tab_name in zip(tabs, ["Combat", "PvE", "Gathering", "Crafting"]):
        with tab:
            st.subheader(f"{tab_name} Rankings")
            render_tab_content(tab_name, category_mappings[tab_name])

else:
    st.warning("No data found or failed to parse the guild data.")
