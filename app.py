import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client
from geopy.geocoders import Nominatim

# --------------------------
# Load Supabase credentials
# --------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------
# Page Setup
# --------------------------
st.set_page_config(page_title="TerraScope - Land Health Monitor", layout="wide")
st.title("🌍 TerraScope - Land Health Monitoring Dashboard")

# --------------------------
# Fetch Data
# --------------------------
try:
    response = supabase.table("land_data").select("*").execute()
    data = pd.DataFrame(response.data)

    if data.empty:
        st.warning("No land data found in Supabase.")
    else:
        st.success("✅ Data fetched successfully from Supabase.")
except Exception as e:
    st.error(f"❌ Failed to fetch data: {e}")
    data = pd.DataFrame()

# --------------------------
# Function to classify health
# --------------------------
def classify_land(vegetation_index, soil_moisture, temperature):
    if vegetation_index < 0.3 or soil_moisture < 20 or temperature > 35:
        return "Degraded"
    elif vegetation_index < 0.5 or soil_moisture < 35:
        return "At Risk"
    else:
        return "Healthy"

# --------------------------
# Suggestion logic
# --------------------------
def get_suggestion(status):
    if status == "Degraded":
        return "Recommend: Reforestation or irrigation to restore soil health."
    elif status == "At Risk":
        return "Recommend: Mulching, cover crops, or moderate irrigation."
    else:
        return "Land is healthy. Maintain current practices."

# --------------------------
# Show map + alert if data exists
# --------------------------
if not data.empty:
    # Ensure numeric data
    data["latitude"] = pd.to_numeric(data["latitude"], errors="coerce")
    data["longitude"] = pd.to_numeric(data["longitude"], errors="coerce")

    # Add classification and suggestion
    data["status"] = data.apply(
        lambda row: classify_land(row["vegetation_index"], row["soil_moisture"], row["temperature"]),
        axis=1
    )
    data["suggestion"] = data["status"].apply(get_suggestion)

    # Define color
    def get_color(status):
        if status == "Degraded":
            return "red"
        elif status == "At Risk":
            return "orange"
        else:
            return "green"

    # Create Map (Centered on Africa)
    m = folium.Map(location=[9.0820, 8.6753], zoom_start=5, tiles="cartodb positron")

    # Add points
    for _, row in data.iterrows():
        if pd.notnull(row["latitude"]) and pd.notnull(row["longitude"]):
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=8,
                color=get_color(row["status"]),
                fill=True,
                fill_color=get_color(row["status"]),
                fill_opacity=0.8,
                popup=folium.Popup(
                    f"<b>Location:</b> {row['location']}<br>"
                    f"<b>Status:</b> {row['status']}<br>"
                    f"<b>Suggestion:</b> {row['suggestion']}",
                    max_width=250,
                ),
            ).add_to(m)

    # Add legend manually
    legend_html = """
    <div style="position: fixed; 
                bottom: 30px; left: 30px; width: 160px; height: 110px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius:8px; padding: 10px;">
        <b>Legend:</b><br>
        <i style="background:green; width:10px; height:10px; border-radius:50%; display:inline-block;"></i> Healthy<br>
        <i style="background:orange; width:10px; height:10px; border-radius:50%; display:inline-block;"></i> At Risk<br>
        <i style="background:red; width:10px; height:10px; border-radius:50%; display:inline-block;"></i> Degraded
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st.subheader("🗺️ Land Health Map")
    st_folium(m, width=900, height=500)

    # Show data table
    st.subheader("📋 Land Data Table")
    st.dataframe(data[["location", "latitude", "longitude", "soil_moisture",
                       "vegetation_index", "temperature", "status", "suggestion", "timestamp"]])

# --------------------------
# Data Input Form
# --------------------------
st.markdown("---")
st.subheader("🧩 Add New Land Data")

with st.form("land_form"):
    latitude = st.number_input("Latitude", format="%.6f")
    longitude = st.number_input("Longitude", format="%.6f")

    geolocator = Nominatim(user_agent="terrascope")
    location_name = ""
    if latitude and longitude:
        try:
            location_name = geolocator.reverse((latitude, longitude), timeout=10).address
        except:
            location_name = "Unknown Location"

    vegetation_index = st.slider("Vegetation Index", 0.0, 1.0, 0.5)
    soil_moisture = st.number_input("Soil Moisture (%)", 0, 100, 40)
    temperature = st.number_input("Temperature (°C)", 0, 60, 28)
    submit = st.form_submit_button("Submit Data")

    if submit:
        status = classify_land(vegetation_index, soil_moisture, temperature)
        suggestion = get_suggestion(status)

        insert_data = {
            "location": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "soil_moisture": soil_moisture,
            "vegetation_index": vegetation_index,
            "temperature": temperature,
            "status": status,
            "suggestion": suggestion,
        }

        try:
            supabase.table("land_data").insert(insert_data).execute()
            st.success("✅ Data successfully added!")
        except Exception as e:
            st.error(f"❌ Failed to add data: {e}")

# --- Footer ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center;'>
        <img src="https://app.greenweb.org/api/v3/greencheckimage/terrascope.streamlit.app?nocache=true"
             alt="This website runs on green hosting - verified by thegreenwebfoundation.org"
             width="200px" height="95px">
        <p style='font-size: 14px; color: gray;'>
            This website runs on green hosting — verified by thegreenwebfoundation.org
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
