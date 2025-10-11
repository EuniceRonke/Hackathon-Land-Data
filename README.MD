🌍 TerraScope — AI-Powered Land Monitoring Dashboard

TerraScope is a Streamlit web app that helps detect and monitor early signs of land degradation.
It analyzes soil moisture, vegetation health, and temperature to support data-driven land management.

🚀 Live App

👉 (https://terrascope.streamlit.app/)


🧠 Overview

Land degradation threatens food security and environmental stability.
TerraScope provides a simple, visual way to track soil and vegetation data in real time — making it easier to act early.

🧩 Features

📊 Dashboard View: Real-time charts and summaries

🌱 Soil & Vegetation Data: Tracks moisture and NDVI

🌡️ Temperature Trends: Detects heat stress

📍 Interactive Map: View each plot by latitude/longitude

⚠️ Degradation Alerts: Highlights unhealthy areas automatically

🧱 Tech Stack
Layer	Tools
Frontend	Streamlit, Pydeck
Backend	Supabase
Data Handling	Pandas, NumPy
Environment	Python, Dotenv
Hosting	Streamlit Cloud
⚙️ Installation & Setup

1. Clone this repository

git clone https://github.com/your-username/hackathon-land-data.git
cd hackathon-land-data


2. Create a virtual environment

python -m venv venv
.\venv\Scripts\activate


3. Install dependencies

pip install -r requirements.txt


4. Run the app locally

streamlit run app.py

🔑 Environment Variables

Create a .env file in your root folder 

SUPABASE_URL=your_supabase_project_url

SUPABASE_KEY=your_supabase_service_key


🗺️ Database Structure (Supabase)
Column	Type	Description
id	int	Primary key

location	text	Plot name (e.g., Plot A, Plot B)

latitude	decimal	GPS latitude (°)

longitude	decimal	GPS longitude (°)

soil_moisture	float	Moisture level (%)

vegetation_index	float	NDVI (0–1)

temperature	float	Temperature in °C

timestamp	timestamps	Time of data capture


🧭 Future Enhancements

Integrate AI to predict land degradation trends

Add CSV upload/download features

Enable user roles for data entry and monitoring

Connect Google Earth Engine for satellite updates

👥 Contributors

Project Lead: Eunice Fagbemide
Assistant Developer: Eunice