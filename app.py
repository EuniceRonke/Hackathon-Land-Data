import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- Supabase Connection ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="TerraScope Dashboard", page_icon="🌍", layout="wide")
st.title("🌍 TerraScope — Land Health Monitoring Dashboard")

# --- Fetch Data ---
try:
    response = supabase.table("land_data").select("*").execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        st.warning("No data available yet. Please add new land data.")
    else:
        # --- Clean Data ---
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp", ascending=False)

        # --- Compute Land Health Status ---
        def get_status(row):
            if row["soil_moisture"] < 30 or row["temperature"] > 35 or row["vegetation_index"] < 0.3:
                return "Degraded"
            elif row["soil_moisture"] < 50 or row["temperature"] > 32 or row["vegetation_index"] < 0.5:
                return "At Risk"
            else:
                return "Healthy"

        df["status"] = df.apply(get_status, axis=1)

        # Map color for each status
        color_map = {
            "Healthy": [46, 204, 113],      # Green
            "At Risk": [243, 156, 18],      # Orange
            "Degraded": [231, 76, 60]       # Red
        }
        df["color"] = df["status"].apply(lambda x: color_map[x])

        # --- Original Alert Logic ---
        low_moisture = df["soil_moisture"].mean() < 30
        high_temp = df["temperature"].mean() > 35
        low_vegetation = df["vegetation_index"].mean() < 0.3

        if low_moisture or high_temp or low_vegetation:
            st.markdown(
                "<h3 style='color:red;'>⚠️ WARNING: Possible Land Degradation Detected!</h3>",
                unsafe_allow_html=True
            )
            if low_moisture:
                st.error("Soil moisture levels are critically low.")
            if high_temp:
                st.error("Temperature levels are too high.")
            if low_vegetation:
                st.error("Vegetation index is below healthy levels.")
        else:
            st.success("✅ Land conditions appear stable.")

        # --- Overview Metrics ---
        st.subheader("📊 Land Health Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Avg Soil Moisture", f"{df['soil_moisture'].mean():.1f}")
        col2.metric("Avg Temperature", f"{df['temperature'].mean():.1f} °C")
        col3.metric("Avg Vegetation Index", f"{df['vegetation_index'].mean():.2f}")

        # --- Check for missing coordinates ---
        missing_coords = df[df["latitude"].isna() | df["longitude"].isna()]
        if not missing_coords.empty:
            st.warning("⚠️ Some rows are missing latitude or longitude! They will not show on the map.")
            st.dataframe(missing_coords[["location", "latitude", "longitude", "status"]])

        # --- Map with color-coded points ---
        st.subheader("🗺️ Land Map")
        try:
            import pydeck as pdk
            df_map = df.dropna(subset=["latitude", "longitude"])

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df_map,
                get_position=["longitude", "latitude"],
                get_color="color",
                get_radius=50000,
                pickable=True
            )

            tooltip = {
                "html": "<b>Location:</b> {location}<br/><b>Status:</b> {status}<br/><b>Soil Moisture:</b> {soil_moisture}<br/><b>Temperature:</b> {temperature}<br/><b>Vegetation Index:</b> {vegetation_index}<br/><b>Timestamp:</b> {timestamp}",
                "style": {"backgroundColor": "white", "color": "black"}
            }

            view_state = pdk.ViewState(
                latitude=df_map["latitude"].mean(),
                longitude=df_map["longitude"].mean(),
                zoom=6,
                pitch=0
            )

            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))

        except Exception as e:
            st.warning(f"Map display issue: {e}")

        # --- Table ---
        st.subheader("📋 Land Data Table")
        st.dataframe(df[["timestamp", "location", "latitude", "longitude", "soil_moisture", "temperature", "vegetation_index", "status"]])

except Exception as e:
    st.error(f"❌ Failed to fetch data: {e}")

# --- Sidebar: Add New Data ---
st.sidebar.header("📝 Add New Land Data")
with st.sidebar.form("data_entry_form"):
    location = st.text_input("Location name")
    latitude = st.number_input("Latitude", format="%.6f", help="Required for map plotting")
    longitude = st.number_input("Longitude", format="%.6f", help="Required for map plotting")
    soil_moisture = st.number_input("Soil Moisture", min_value=0.0)
    temperature = st.number_input("Temperature (°C)", min_value=-50.0)
    vegetation_index = st.number_input("Vegetation Index (0 to 1)", min_value=0.0, max_value=1.0)
    submitted = st.form_submit_button("Submit Data")

if submitted:
    if latitude == 0.0 or longitude == 0.0:
        st.sidebar.error("⚠️ Latitude and Longitude are required!")
    else:
        try:
            new_data = {
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "soil_moisture": soil_moisture,
                "temperature": temperature,
                "vegetation_index": vegetation_index,
                "timestamp": datetime.utcnow().isoformat()
            }
            supabase.table("land_data").insert(new_data).execute()
            st.sidebar.success("✅ Data submitted successfully!")
            st.experimental_rerun()
        except Exception as e:
            st.sidebar.error(f"❌ Error submitting data: {e}")

