import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# --- Add the project root to the Python path ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from scripts.inventory_management import read_inventory
from models.predictive_model import predict_usage

# --- Page Configuration ---
st.set_page_config(
    page_title="EasyJet Engineering Tool Inventory",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- User Authentication ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{name}* ')

    # --- Load Data ---
    @st.cache_data
    def load_data():
        df = read_inventory()
        df['Next_Maintenance'] = pd.to_datetime(df['Next_Maintenance'])
        df['Last_Calibration'] = pd.to_datetime(df['Last_Calibration'])
        return df

    inventory_df = load_data()

    # --- Styling ---
    def get_row_style(row):
        """Applies styling to rows based on conditions."""
        style = ''
        if row['Next_Maintenance'] < datetime.now() + pd.Timedelta(days=30):
            style += 'background-color: #FFDDC1;'  # Orange for calibration due soon
        if row['Usage_Frequency'] > 40:
            style += 'font-weight: bold; color: #D32F2F;'  # Red and bold for high-demand
        if row['Checked_Out_By'] != 'None':
            style += 'font-style: italic;' # Italic for checked out items
        return [style] * len(row)

    # --- Dashboard UI ---
    # Header
    st.title("✈️ EasyJet Engineering Malta – Tool Inventory Dashboard")
    st.markdown("**Real-time tracking and predictive insights for tool management.**")

    # --- Sidebar ---
    st.sidebar.header("Filters & Actions")

    # Location Filter
    location_filter = st.sidebar.multiselect(
        'Filter by Location:',
        options=inventory_df['Location'].unique(),
        default=inventory_df['Location'].unique()
    )

    # Status Filter
    status_filter = st.sidebar.selectbox(
        'Filter by Status:',
        options=['All', 'Available', 'Checked Out']
    )

    # Filtered DataFrame
    df_filtered = inventory_df[inventory_df['Location'].isin(location_filter)]
    if status_filter == 'Available':
        df_filtered = df_filtered[df_filtered['Checked_Out_By'] == 'None']
    elif status_filter == 'Checked Out':
        df_filtered = df_filtered[df_filtered['Checked_Out_By'] != 'None']

    # --- Main Content ---

    # Key Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tools", f"{len(df_filtered)}")
    col2.metric("Tools Checked Out", f"{len(df_filtered[df_filtered['Checked_Out_By'] != 'None'])}")
    col3.metric("Calibration Due Soon", f"{len(df_filtered[df_filtered['Next_Maintenance'] < datetime.now() + pd.Timedelta(days=30)])}")

    st.markdown("### Full Inventory Details")

    # Display stylized dataframe
    st.dataframe(
        df_filtered.style.apply(get_row_style, axis=1),
        height=500,
        use_container_width=True
    )

    # --- Charts & Predictions ---
    st.markdown("### Analytics & Predictions")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Tool Distribution by Location")
        location_counts = df_filtered['Location'].value_counts()
        st.bar_chart(location_counts)

    with col2:
        st.subheader("Usage Frequency Distribution")
        usage_counts = df_filtered['Usage_Frequency'].value_counts()
        st.area_chart(usage_counts)

    # --- Missing & High-Demand Tools ---
    st.sidebar.markdown("---" )
    st.sidebar.header("⚠️ Alerts")

    # High-Demand Tools
    st.sidebar.subheader("High-Demand Tools (Usage > 40)")
    high_demand_tools = inventory_df[inventory_df['Usage_Frequency'] > 40]
    if not high_demand_tools.empty:
        st.sidebar.table(high_demand_tools[['Tool_ID', 'Box_Name', 'Usage_Frequency']])
    else:
        st.sidebar.info("No high-demand tools at the moment.")

    # Missing Tools
    st.sidebar.subheader("Checked Out / Missing Tools")
    missing_tools = inventory_df[inventory_df['Checked_Out_By'] != 'None']
    if not missing_tools.empty:
        st.sidebar.table(missing_tools[['Tool_ID', 'Box_Name', 'Checked_Out_By']])
    else:
        st.sidebar.info("All tools are currently checked in.")

    # --- How to Use ---
    st.sidebar.markdown("---" )
    st.sidebar.info(
        "**How to use this dashboard:**\n"
        "- Use the filters to narrow down the inventory view.\n"
        "- Rows in **orange** indicate upcoming calibration.\n"
        "- Text in **red** signifies a high-demand tool.\n"
        "- *Italicized* rows show tools that are currently checked out."
    )

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')