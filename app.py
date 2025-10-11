import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client
import os
from datetime import datetime
from dotenv import load_dotenv
import pydeck as pdk

# Load environment variables
load_dotenv()

# Initialize connection
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

st.set_page_config(page_title="LandWatch AI Dashboard", layout="wide")

# Title
st.title("🌍 LandWatch AI Dashboard")
st.markdown("AI-powered land degradation monitoring system — SDG 15: Life on Land")

# Fetch data from Supabase
@st.cache_data(ttl=60)
def get_data():
    try:
        data = supabase.table("land_data").select("*").execute()
        df = pd.DataFrame(data.data)
        return df
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

df = get_data()

if df.empty:
    st.warning("No data available from Supabase.")
    st.stop()

# Ensure correct columns exist
required_cols = ['id', 'location', 'soil_moisture', 'vegetation_index', 'temperature', 'latitude', 'longitude', 'timestamp']
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing columns in Supabase: {missing}")
    st.stop()

# Convert timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Sidebar filters
st.sidebar.header("Filters")
selected_location = st.sidebar.selectbox("Select Plot", options=["All"] + sorted(df['location'].unique().tolist()))

if selected_location != "All":
    df = df[df['location'] == selected_location]

# KPI Metrics
avg_moisture = df['soil_moisture'].mean()
avg_vegetation = df['vegetation_index'].mean()
avg_temp = df['temperature'].mean()

col1, col2, col3 = st.columns(3)
col1.metric("Avg Soil Moisture", f"{avg_moisture:.2f}")
col2.metric("Avg Vegetation Index", f"{avg_vegetation:.2f}")
col3.metric("Avg Temperature (°C)", f"{avg_temp:.1f}")

# Map Visualization
st.subheader("🗺 Land Health Map")
st.map(df[['latitude', 'longitude']], zoom=6)

# Advanced Map (Colored markers)
st.subheader("Detailed Map View")

df["status"] = np.where(
    (df["soil_moisture"] < 30) | (df["vegetation_index"] < 0.4),
    "Degraded",
    "Healthy"
)

# Define map color by status
df["color"] = df["status"].map({"Healthy": [0, 200, 0], "Degraded": [200, 0, 0]})

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df,
    get_position='[longitude, latitude]',
    get_color='color',
    get_radius=80000,
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=df["latitude"].mean(),
    longitude=df["longitude"].mean(),
    zoom=5,
    pitch=0,
)

r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{location}\nStatus: {status}"})
st.pydeck_chart(r)

# Alerts
st.subheader("⚠️ Alerts & Recommendations")

if avg_moisture < 30:
    st.error("Low soil moisture detected — consider irrigation.")
if avg_vegetation < 0.4:
    st.warning("Vegetation health declining — check for pests or drought.")
if avg_temp > 35:
    st.warning("High temperature — risk of heat stress.")
if (avg_moisture >= 30) and (avg_vegetation >= 0.4) and (avg_temp <= 35):
    st.success("All parameters are stable. Land is healthy.")

# Data Table
st.subheader("📊 Data Table")
st.dataframe(df[['location', 'soil_moisture', 'vegetation_index', 'temperature', 'latitude', 'longitude', 'timestamp']])

# Footer
st.markdown("---")
st.markdown("**LandWatch AI** — Early detection for a sustainable planet 🌱")
