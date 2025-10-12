import streamlit as st
from supabase import create_client, Client
import pandas as pd
import pydeck as pdk
from datetime import datetime
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
import os

# --- Load Environment Variables ---
load_dotenv()

# --- Streamlit Page Setup ---
st.set_page_config(page_title="TerraScope", layout="wide")

# --- Connect to Supabase ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🌍 TerraScope – AI Land Health Monitor")

# --- Function to Fetch Data ---
@st.cache_data(ttl=60)
def load_data():
    response = supabase.table("land_data").select("*").execute()
    return pd.DataFrame(response.data)

# --- Fetch Data ---
try:
    df = load_data()
    if df.empty:
        st.warning("No data found in Supabase table.")
    else:
        st.success("✅ Successfully fetched data from Supabase!")
except Exception as e:
    st.error(f"❌ Failed to fetch data: {e}")
    st.stop()

# --- Sidebar Form ---
st.sidebar.header("➕ Add New Land Data")
geolocator = Nominatim(user_agent="terrascope_app")

with st.sidebar.form("data_entry_form"):
    latitude = st.number_input("Latitude", format="%.6f")
    longitude = st.number_input("Longitude", format="%.6f")

    # Auto-fill location name
    location = ""
    if latitude and longitude:
        try:
            loc = geolocator.reverse(f"{latitude}, {longitude}", language="en")
            if loc and "address" in loc.raw:
                location = loc.address.split(",")[0]
        except:
            location = "Unknown"

    location_input = st.text_input("Location", value=location)
    soil_moisture = st.number_input("Soil Moisture (%)", min_value=0.0)
    vegetation_index = st.number_input("Vegetation Index (0-1)", min_value=0.0, max_value=1.0)
    temperature = st.number_input("Temperature (°C)", min_value=-10.0, max_value=60.0)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    submit = st.form_submit_button("Submit Data")

# --- Insert into Supabase ---
if submit:
    try:
        data = {
            "location": location_input,
            "latitude": latitude,
            "longitude": longitude,
            "soil_moisture": soil_moisture,
            "vegetation_index": vegetation_index,
            "temperature": temperature,
            "timestamp": timestamp,
        }
        supabase.table("land_data").insert(data).execute()
        st.success("✅ Data added successfully! Refreshing map...")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to insert data: {e}")

# --- Data Validation ---
if not df.empty:
    # Determine status
    df["status"] = df.apply(
        lambda row: "Degraded" if (row["soil_moisture"] < 30 or row["temperature"] > 35 or row["vegetation_index"] < 0.3)
        else ("At Risk" if (30 <= row["soil_moisture"] < 40 or 33 <= row["temperature"] <= 35 or 0.3 <= row["vegetation_index"] < 0.4)
              else "Healthy"),
        axis=1
    )

    # Assign colors
    color_map = {
        "Healthy": [0, 255, 0],     # Green
        "At Risk": [255, 165, 0],   # Orange
        "Degraded": [255, 0, 0],    # Red
    }
    df["color"] = df["status"].map(color_map)

    # --- Africa Map ---
    st.subheader("🗺️ Land Health Overview (Africa)")
    view_state = pdk.ViewState(latitude=0.5, longitude=20.0, zoom=3.5, pitch=0)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_fill_color="color",
        get_radius=40000,
        pickable=True,
    )

    tooltip = {
        "html": "<b>Location:</b> {location}<br/>"
                "<b>Status:</b> {status}<br/>"
                "<b>Soil Moisture:</b> {soil_moisture}<br/>"
                "<b>Temperature:</b> {temperature}<br/>"
                "<b>Vegetation Index:</b> {vegetation_index}<br/>"
                "<b>Timestamp:</b> {timestamp}",
        "style": {"backgroundColor": "white", "color": "black"}
    }

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))

    # --- Legend (Fixed Display) ---
    st.markdown("""
    <div style="display:flex; justify-content:center; gap:30px; font-size:16px; margin-top:10px;">
        <div style="display:flex; align-items:center; gap:8px;">
            <div style="width:18px; height:18px; border-radius:50%; background:red;"></div> Degraded
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <div style="width:18px; height:18px; border-radius:50%; background:orange;"></div> At Risk
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <div style="width:18px; height:18px; border-radius:50%; background:green;"></div> Healthy
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Alerts Section ---
    st.subheader("⚠️ Alerts & Recommendations")
    degraded = df[df["status"] == "Degraded"]
    if not degraded.empty:
        for _, row in degraded.iterrows():
            st.error(f"🚨 {row['location']} - Degraded: Low soil moisture or high temperature detected!")
    else:
        st.success("✅ All monitored lands are stable.")

    # --- Data Table (Hide Color Column) ---
    st.subheader("📊 Land Data Table")
    st.dataframe(df.drop(columns=["color"]))
