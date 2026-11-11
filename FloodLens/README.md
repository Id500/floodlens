# FLOODLENS

### NASA Satellite-Based Flood Intelligence and Risk Monitoring System

[![Flask](https://img.shields.io/badge/Backend-Flask_3.x-00f0ff?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![NASA GIBS](https://img.shields.io/badge/Satellite-NASA_GIBS_WMTS-blue?style=for-the-badge)](https://gibs.earthdata.nasa.gov/)
[![Open-Meteo](https://img.shields.io/badge/Telemetry-Open--Meteo_Weather_%26_GloFAS-0284c7?style=for-the-badge)](https://open-meteo.com/)
[![OpenCV](https://img.shields.io/badge/Vision-OpenCV_Segmentation-5c8aff?style=for-the-badge&logo=opencv)](https://opencv.org/)
[![Database](https://img.shields.io/badge/Database-SQLite_%26_SQLAlchemy-orange?style=for-the-badge&logo=sqlite)](https://www.sqlite.org/)

---

## 🌊 Overview

**FLOODLENS** is a mission-grade disaster intelligence platform that fuses **NASA GIBS Earth observation satellite layers**, **Copernicus GloFAS river routing telemetry**, **Open-Meteo precipitation forecasts**, and an **Explainable AI (XAI) multi-factor risk engine** into a unified, responsive dashboard.

Designed specifically with **Flask** (strictly no Streamlit), FLOODLENS delivers high performance, real-time spatial analytics, OpenCV-powered satellite image segmentation, and crowdsourced citizen incident reporting with complete scientific transparency.

---

## 🚀 Key Features

1. **NASA Satellite GIBS WMTS Integration**:
   - Live tile streaming from NASA GIBS (`EPSG:3857 Web Mercator`).
   - Supports **MODIS Terra False Color (Bands 7-2-1)** (water absorption / flood delineation), **VIIRS SNPP True Color**, **MODIS Terra True Color**, **VIIRS NOAA-20**, and **GPM IMERG Precipitation Rate**.
   - Dynamic observation date selection.
   - Rigorous scientific disclaimer: Distinguishes ordinary surface reflectance from calibrated flood classification and highlights optical cloud-penetration limitations.

2. **Explainable AI (XAI) Flood Risk Engine (`risk_engine.py`)**:
   - Transparent, mathematical multi-factor scoring algorithm (0 to 100 risk score).
   - Classifies risk into **LOW**, **MODERATE**, **HIGH**, and **SEVERE** tiers.
   - Dynamic weight reallocation: When a coordinate lacks a modeled major river reach, the system automatically shifts river weights to 24h rainfall accumulation, cloudburst rate, and 3-day forecast rain.
   - Natural language automated diagnosis explaining why the hazard level was assigned.
   - Zero fake data standard: Never hallucinates synthetic river numbers.

3. **OpenCV Satellite Image Analysis (`image_analysis.py`)**:
   - Image upload pipeline with support for JPG, PNG, and TIFF satellite scenes.
   - Quality checks: Laplacian variance sharpness, brightness intensity, and contrast standard deviation.
   - Dual-space spectral segmentation (HSV and LAB color channels) for water extraction.
   - Visualized output: Cyan-tinted water mask, contour boundaries, and top candidate flood zones.
   - Built-in "Load Test Satellite Image" button for immediate demonstration.

4. **Interactive Leaflet Geospatial Engine**:
   - Default focus on **Chennai, Tamil Nadu, India** (`13.0827° N, 80.2707° E`).
   - Click anywhere on the map to evaluate risk and monitor new catchments.
   - Global location search with OpenStreetMap Nominatim geocoding.
   - Multi-layer base maps (Carto Dark, Esri World Imagery, OpenStreetMap).
   - Crowdsourced flood report markers color-coded by severity.

5. **Community Flood Reporting System**:
   - Citizens can submit field observations with street landmarks, coordinates, severity levels, water depth estimations, descriptions, and optional photos.
   - Stored in SQLite via Flask-SQLAlchemy.
   - All community reports are strictly labeled as **"Unverified Citizen Report"** until confirmed by civil defense authorities.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, Flask 3.x, Flask-SQLAlchemy, Requests, Pandas, NumPy, OpenCV, Scikit-learn
- **Frontend**: HTML5, CSS3 (Dark Navy Glassmorphism), JavaScript (ES6+), Bootstrap 5, Chart.js, Leaflet.js
- **Database**: SQLite (local instance database)
- **APIs**: NASA GIBS, Open-Meteo Weather API, Open-Meteo Global Flood API, OpenStreetMap Nominatim

---

## 📁 Project Directory Structure

```text
FloodLens/
│
├── app.py                     # Main Flask application factory & API router
├── config.py                  # Application configuration & path bindings
├── requirements.txt           # Project dependencies
├── README.md                  # System documentation
├── .env.example               # Environment variable templates
│
├── modules/                   # Core business logic & integrations
│   ├── weather.py             # Open-Meteo Weather API client & caching
│   ├── flood_api.py           # Open-Meteo GloFAS river discharge client
│   ├── nasa.py                # NASA GIBS WMTS metadata & tile layer URLs
│   ├── risk_engine.py         # Explainable Multi-Factor Flood Risk Engine
│   ├── image_analysis.py      # OpenCV satellite image water segmentation
│   └── map_service.py         # Presets & Nominatim geocoding service
│
├── models/                    # Database models
│   └── report.py              # Community FloodReport SQLAlchemy model
│
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base shell with sidebar, topbar & modals
│   ├── index.html             # Command Center / Overview dashboard
│   ├── dashboard.html         # Weather Intelligence & 7-day progression
│   ├── satellite.html         # NASA GIBS satellite viewer & date picker
│   ├── risk.html              # Explainable AI risk breakdown & radar chart
│   ├── river.html             # 14-day river discharge hydrographs
│   ├── analysis.html          # OpenCV satellite image analysis tool
│   ├── map.html               # Fullscreen interactive geospatial map
│   ├── reports.html           # Community reporting feed & submission form
│   └── about.html             # Methodology, formulas & data citations
│
├── static/                    # Frontend assets
│   ├── css/
│   │   └── style.css          # Dark Navy futuristic command center styles
│   ├── js/
│   │   ├── dashboard.js       # Global state management & geocoding search
│   │   ├── charts.js          # Chart.js dark-themed configurations
│   │   └── map.js             # Leaflet GIS & NASA GIBS layer engine
│   └── images/                # Sample satellite test imagery
│
├── instance/                  # SQLite database storage
│   └── floodlens.db
│
├── uploads/                   # Uploaded images & OpenCV processed masks
│
└── tests/                     # Automated test suites
    ├── test_risk_engine.py    # Unit tests for scoring & re-weighting
    └── test_api.py            # Integration tests for pages & REST APIs
```

---

## 💻 Installation & Setup (Windows)

Open PowerShell or Command Prompt in the `FloodLens` directory:

### 1. Create Virtual Environment
```powershell
python -m venv venv
```

### 2. Activate Virtual Environment
```powershell
venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 4. Run the Application
```powershell
python app.py
```

### 5. Access FLOODLENS
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🧪 Running Automated Tests

Run the full automated test suite covering all REST endpoints, pages, OpenCV processing, and mathematical risk models:

```powershell
python -m unittest discover tests -v
```

---

## 🛰️ REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/weather?lat=...&lon=...` | Retrieves current & 7-day weather metrics from Open-Meteo |
| `GET` | `/api/flood?lat=...&lon=...` | Retrieves 14-day GloFAS river discharge hydrograph |
| `GET` | `/api/satellite?layer=...&date=...` | Retrieves NASA GIBS layer metadata & WMTS tile URLs |
| `GET` | `/api/risk?lat=...&lon=...` | Computes multi-factor explainable flood hazard score (0-100) |
| `GET` | `/api/reports?severity=...` | Fetches crowdsourced community flood reports |
| `POST` | `/api/reports` | Submits a new citizen field report with optional photo |
| `POST` | `/api/analyze-image` | Uploads satellite scene for OpenCV segmentation & diagnostics |
| `GET` | `/api/geocode?q=...` | Global location search via OpenStreetMap Nominatim |
| `GET` | `/api/presets` | Returns preset flood-prone monitoring centers |

---

## ⚖️ Scientific Disclaimer & Ethics

- **Experimental Software**: FLOODLENS is built for disaster research and hackathon demonstrations. It should be used to augment, not replace, certified national hydrometeorological warnings.
- **Optical Imagery Limitations**: Optical satellites cannot penetrate heavy storm clouds during active cyclonic deluges. Synthetic Aperture Radar (SAR / Sentinel-1) is necessary for cloud-penetrating water delineation.
- **Crowdsource Verification**: All community reports are explicitly labeled as **"Unverified"** until corroborated by authorized municipal responders.

