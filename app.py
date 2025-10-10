import streamlit as st
from supabase import create_client, Client
import pandas as pd
import os

# No dotenv needed — Streamlit Secrets will provide these
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase credentials not set. Please add SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets.")
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    st.title("🌍 Land Data Viewer")

    try:
        response = supabase.table("land_data").select("*").execute()
        df = pd.DataFrame(response.data)

        if df.empty:
            st.warning("No data found in Supabase table.")
        else:
            st.success("✅ Successfully fetched data from Supabase!")
            st.dataframe(df)

            # --- Alert Logic ---
            low_moisture = df["soil_moisture"].mean() < 30
            high_temp = df["temperature"].mean() > 35
            low_vegetation = df["vegetation_index"].mean() < 0.3

            if low_moisture or high_temp or low_vegetation:
                st.markdown(
                    "<h2 style='color:red;'>⚠️ WARNING: Possible Land Degradation Detected!</h2>",
                    unsafe_allow_html=True,
                )
                if low_moisture:
                    st.error("Soil moisture levels are critically low.")
                if high_temp:
                    st.error("Temperature levels are too high.")
                if low_vegetation:
                    st.error("Vegetation index is below healthy levels.")
            else:
                st.success("✅ Land conditions appear stable.")

    except Exception as e:
        st.error(f"❌ Failed to fetch data: {e}")
