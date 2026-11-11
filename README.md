# 🌊 FloodLens
### NASA Satellite-Based Flood Intelligence Platform

**FloodLens** is a web-based flood intelligence platform designed to help people explore potential flood conditions using satellite imagery, rainfall information, river-discharge data, and location-based risk assessment.

The platform allows users to enter a city, town, village, or specific area and explore environmental information through an interactive map.

---

## 🚀 Key Features

- **Location-Based Search:** Search locations using city names, place names, area names, or coordinates.
- **NASA Satellite Imagery:** Visualize NASA Terra and Aqua satellite imagery through map layers.
- **Interactive Map:** Explore geographical locations using an interactive Leaflet-based map.
- **Date Selection:** Select dates to explore and compare satellite imagery.
- **Rainfall Monitoring:** Retrieve rainfall-related information for selected locations.
- **River Discharge Monitoring:** Display river-discharge information to understand changing water conditions.
- **NASA GPM Data Discovery:** Explore relevant NASA Global Precipitation Measurement datasets.
- **Flood Risk Assessment:** Generate an explainable risk score using available environmental indicators.
- **Responsive Dashboard:** Access the platform through a modern, dark-themed interface.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Mapping | Leaflet.js |
| Satellite Data | NASA GIBS |
| Weather Data | Open-Meteo API |
| Data Processing | NumPy, Pandas |
| Visualization | Interactive maps and dashboard charts |
| HTTP Requests | Requests |

## 🛰️ Data Sources

**1. NASA Global Imagery Browse Services (GIBS)**

Provides satellite imagery visualization services for exploring Earth observations.

https://nasa-gibs.github.io/gibs-api-docs/

**2. NASA Global Precipitation Measurement (GPM)**

Provides access to precipitation-related satellite datasets and information.

https://gpm.nasa.gov/

**3. Open-Meteo API**

Provides weather information, geocoding, and environmental data used by the platform.

https://open-meteo.com/

## 📁 Project Structure

```text
FloodLens/
│
├── app.py
├── requirements.txt
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   └── script.js
│   │
│   └── images/
│
└── README.md
```

*Note: Adjust this structure to match the actual files in your project.*

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.10 or later (depending on dependency compatibility)
- VS Code or another code editor
- Git (optional)
- Internet connection

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Navigate to the project directory

```bash
cd FloodLens
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

**Windows PowerShell:**

```bash
.\venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Run the application

```bash
python app.py
```

### 7. Open in your browser

```text
http://127.0.0.1:5000
```

## 🔍 How FloodLens Works

1. The user enters a geographical location.
2. The application identifies the location and retrieves its coordinates.
3. Satellite imagery is displayed using NASA imagery services.
4. Weather and river-discharge information is retrieved from available environmental data sources.
5. Environmental indicators are evaluated to produce an explainable flood-risk score.
6. Results are presented through the interactive dashboard.

## 🎯 Project Objectives

- Make satellite-based environmental information more accessible.
- Help users explore potential flood-prone conditions.
- Combine geographical information with rainfall and river-discharge indicators.
- Demonstrate how publicly available Earth observation data can support disaster awareness.
- Build an accessible geographical intelligence platform for common users.

## ⚠️ Limitations

- Satellite imagery availability depends on the selected date and data source.
- Cloud cover and satellite observation frequency can affect image interpretation.
- The risk score is an experimental assessment, not an officially validated flood prediction.
- Automated flood-water extraction and detection from satellite raster data are not yet fully implemented.
- Live API availability and data coverage may vary.

**Important:** FloodLens is an experimental educational and research project. It must not be used as a substitute for official flood warnings, emergency alerts, or government disaster-management information.

## 🔮 Future Enhancements

- Automated flood detection using satellite imagery.
- Deep learning-based flood segmentation.
- Historical flood analysis and comparison.
- Real-time flood alerts.
- More satellite data integration.
- High-resolution flood-risk mapping.
- Integration with official disaster-management datasets.

## 👨‍💻 Project Information

**Project Name:** FloodLens

**Domain:** Artificial Intelligence / Data Science / Geospatial Technology

**Backend:** Python Flask

**Application Type:** Web-Based Geospatial Intelligence Platform

## 📜 Acknowledgements

- NASA Earthdata and Global Imagery Browse Services.
- NASA Global Precipitation Measurement Mission.
- Open-Meteo for environmental data services.
- Leaflet for interactive geographical mapping.

---

⭐ If you find this project interesting, consider starring the repository!

**FloodLens – Exploring Earth. Understanding Flood Risks. Supporting Safer Communities.** 🌍
