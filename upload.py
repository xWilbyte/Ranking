import streamlit as st
import pandas as pd
import requests

# Configure the Streamlit page
st.set_page_config(page_title="Albion Guild Rankings", layout="wide")

# Inject Custom CSS to lock layout sizing, make tabs bigger, and center text
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
    
    /* Center and enlarge the Main Tabs */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 20px !important;
        font-weight: 600 !important;
        padding: 12px 28px !important;
        height: auto !important;
        border-radius: 4px;
    }
    
    /* Center selectbox text */
    div[data-baseweb="select"] {
        justify-content: center;
        text-align: center;
    }
    
    /* Custom HTML Table Container with forced static sizing */
    .custom-table-container {
        max-height: 500px;
        overflow-y: auto;
        width: 100%;
        margin-top: 25px;
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 5px;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        text-align: center;
        font-family: sans-serif;
        table-layout: fixed; /* Forces absolute adherence to column widths below */
    }
    /* Lock column proportions so the table never changes scale */
    .custom-table th:nth-child(1), .custom-table td:nth-child(1) { width: 15% !important; }
    .custom-table th:nth-child(2), .custom-table td:nth-child(2) { width: 50% !important; }
    .custom-table th:nth-child(3), .custom-table td:nth-child(3) { width: 35% !important; }

    /* Sticky header styles */
    .custom-table th {
        position: sticky;
        top: 0;
        background-color: rgba(128, 128, 128, 0.15); 
        backdrop-filter: blur(5px);
        padding: 14px;
        border-bottom: 2px solid rgba(128, 128, 128, 0.5);
        z-index: 1;
        text-align: center !important;
    }
    .custom-table td {
        padding: 12px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        text-align: center !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    /* Hover effect */
    .custom-table tr:hover {
        background-color: rgba(128, 128, 128, 0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("Running Dawn Guild Member Rankings")
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
    
    sub_keys = {
        "Total": "Total",
        "Royal": "Mainland (Royal)",
        "Outlands": "Outlands",
        "Avalon": "Avalon",
        "Hellgate": "Hellgate",
        "CorruptedDungeon": "Corrupted Dungeon",
        "Mists": "Mists"
    }
    
    gathering_resources = ["All", "Fiber", "Hide", "Ore", "Rock", "Wood"]
    
    for member in raw_data:
        stats = {"Name": member.get("Name", "Unknown")}
        
        # PvP Stats
        stats["PvP - Kill Fame"] = member.get("KillFame", 0)
        stats["PvP - Death Fame"] = member.get("DeathFame", 0)
        stats["PvP - Fame Ratio"] = member.get("FameRatio", 0.0)
        
        lifetime = member.get("LifetimeStatistics", {})
        
        # PvE Subcategories
        pve = lifetime.get("PvE", {})
        for api_key, display_name in sub_keys.items():
            stats[f"PvE - {display_name}"] = pve.get(api_key, 0)
            
        # Crafting Subcategories
        crafting = lifetime.get("Crafting", {})
        for api_key, display_name in sub_keys.items():
            stats[f"Crafting - {display_name}"] = crafting.get(api_key, 0)
            
        # Gathering Subcategories
        gathering = lifetime.get("Gathering", {})
        for res in gathering_resources:
            res_data = gathering.get(res, {})
            for api_key, display_name in sub_keys.items():
                stats[f"Gathering - {res} - {display_name}"] = res_data.get(api_key, 0)
        
        # Fishing and Farming Fame
        stats["Fishing Fame"] = lifetime.get("FishingFame", 0)
        stats["Farming Fame"] = lifetime.get("FarmingFame", 0)
        
        # Calculate Accumulated Total Fame across all primary activities
        stats["Total Fame"] = (
            stats["PvP - Kill Fame"] +
            stats["PvE - Total"] +
            stats["Crafting - Total"] +
            stats["Gathering - All - Total"] +
            stats["Fishing Fame"] +
            stats["Farming Fame"]
        )
        
        parsed_data.append(stats)
        
    return pd.DataFrame(parsed_data)

# Fetch and process data
with st.spinner("Fetching data from Albion servers..."):
    raw_data = fetch_guild_data()
    df = process_data(raw_data)

if not df.empty:
    # 7 Large Main Categories Tabs (Total moved to the far left)
    tabs = st.tabs(["Total", "PvP", "PvE", "Gathering", "Crafting", "Fishing", "Farming"])
    
    zone_options = ["Total", "Mainland (Royal)", "Outlands", "Avalon", "Hellgate", "Corrupted Dungeon", "Mists"]
    pvp_options = ["Kill Fame", "Death Fame", "Fame Ratio"]
    gathering_resources = ["All", "Fiber", "Hide", "Ore", "Rock", "Wood"]

    def render_custom_table(stat_df, stat_name):
        if "Ratio" in stat_name:
            stat_df[stat_name] = stat_df[stat_name].map("{:,.2f}".format)
        else:
            stat_df[stat_name] = stat_df[stat_name].map("{:,}".format)
            
        html_table = stat_df.to_html(index=False, classes="custom-table", escape=False)
        html_block = f'<div class="custom-table-container">{html_table}</div>'
        st.markdown(html_block, unsafe_allow_html=True)

    # --- 1. Total Tab ---
    with tabs[0]:
        st.subheader("Overall Total Fame Rankings")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            search_term = st.text_input("Search Player", key="total_search")
        # col2 and col3 left empty to maintain layout grid structural symmetry
            
        actual_stat_name = "Total Fame"
        stat_df = df[["Name", actual_stat_name]].sort_values(by=actual_stat_name, ascending=False).reset_index(drop=True)
        stat_df.index += 1
        stat_df = stat_df.reset_index().rename(columns={"index": "Rank"})
        if search_term:
            stat_df = stat_df[stat_df["Name"].str.contains(search_term, case=False, na=False)]
            
        render_custom_table(stat_df, actual_stat_name)

    # --- 2. PvP Tab ---
    with tabs[1]:
        st.subheader("PvP Rankings")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            search_term = st.text_input("Search Player", key="pvp_search")
        with col2:
            selected_sub = st.selectbox("Select Statistic", pvp_options, key="pvp_sub")
            
        actual_stat_name = f"PvP - {selected_sub}"
        stat_df = df[["Name", actual_stat_name]].sort_values(by=actual_stat_name, ascending=False).reset_index(drop=True)
        stat_df.index += 1
        stat_df = stat_df.reset_index().rename(columns={"index": "Rank"})
        if search_term:
            stat_df = stat_df[stat_df["Name"].str.contains(search_term, case=False, na=False)]
            
        render_custom_table(stat_df, actual_stat_name)

    # --- 3. PvE Tab ---
    with tabs[2]:
        st.subheader("PvE Rankings")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            search_term = st.text_input("Search Player", key="pve_search")
        with col2:
            selected_sub = st.selectbox("Select Zone", zone_options, key="pve_sub")
            
        actual_stat_name = f"PvE - {selected_sub}"
        stat_df = df[["Name", actual_stat_name]].sort_values(by=actual_stat_name, ascending=False).reset_index(drop=True)
        stat_df.index += 1
        stat_df = stat_df.reset_index().rename(columns={"index": "Rank"})
        if search_term:
            stat_df = stat_df[stat_df["Name"].str.contains(search_term, case=False, na=False)]
            
        render_custom_table(stat_df, actual_stat_name)

    # --- 4. Gathering Tab ---
    with tabs[3]:
        st.subheader("Gathering Rankings")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            search_term = st.text_input("Search Player", key="gather_search")
        with col2:
            selected_res = st.selectbox("Select Resource", gathering_resources, index=0, key="gather_res")
        with col3:
            selected_sub = st.selectbox("Select Zone", zone_options, key="gather_sub")
            
        actual_stat_name = f"Gathering - {selected_res} - {selected_sub}"
        stat_df = df[["Name", actual_stat_name]].sort_values(by=actual_stat_name, ascending=False).reset_index(drop=True)
        stat_df.index += 1
        stat_df = stat_df.reset_index().rename(columns={"index": "Rank"})
        if search_term:
            stat_df = stat_df[stat_df["Name"].str.contains(search_term, case=False, na=False)]
            
        render_custom_table(stat_df, actual_stat_name)

    # --- 5. Crafting Tab ---
    with tabs[4]:
        st.subheader("Crafting Rankings")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            search_term = st.text_input("Search Player", key="craft_search")
        with col2:
            selected_sub = st.selectbox("Select Zone", zone_options, key="craft_sub")
            
        actual_stat_name = f"Crafting - {selected_sub}"
        stat_df = df[["Name", actual_stat_name]].sort_values(by=actual_stat_name, ascending=False).reset_index(drop=True)
        stat_df.index += 1
        stat_df = stat_df.reset_index().rename(columns={"index": "Rank"})
        if search_term:
            stat_df = stat_df[stat_df["Name"].str.contains(search_term, case=False, na=False)]
            
        render_custom_table(stat_df, actual_stat_name)

    # --- 6. Fishing Tab ---
    with tabs[5]:
        st.subheader("Fishing Rankings")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            search_term = st.text_input("Search Player", key="fish_search")
            
        actual_stat_name = "Fishing Fame"
        stat_df = df[["Name", actual_stat_name]].sort_values(by=actual_stat_name, ascending=False).reset_index(drop=True)
        stat_df.index += 1
        stat_df = stat_df.reset_index().rename(columns={"index": "Rank"})
        if search_term:
            stat_df = stat_df[stat_df["Name"].str.contains(search_term, case=False, na=False)]
            
        render_custom_table(stat_df, actual_stat_name)
        
    # --- 7. Farming Tab ---
    with tabs[6]:
        st.subheader("Farming Rankings")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            search_term = st.text_input("Search Player", key="farm_search")
            
        actual_stat_name = "Farming Fame"
        stat_df = df[["Name", actual_stat_name]].sort_values(by=actual_stat_name, ascending=False).reset_index(drop=True)
        stat_df.index += 1
        stat_df = stat_df.reset_index().rename(columns={"index": "Rank"})
        if search_term:
            stat_df = stat_df[stat_df["Name"].str.contains(search_term, case=False, na=False)]
            
        render_custom_table(stat_df, actual_stat_name)

else:
    st.warning("No data found or failed to parse the guild data.")
