import time
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

_FLOOD_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 300  # 5 minutes

def fetch_river_discharge(lat: float, lon: float, timeout: int = 10) -> Dict[str, Any]:
    """
    Fetch river discharge data from Open-Meteo Global Flood API (based on GloFAS model).
    Handles coordinates with or without major river basins gracefully without fabricating fake data.
    """
    cache_key = f"{round(lat, 3)}_{round(lon, 3)}"
    now = time.time()

    if cache_key in _FLOOD_CACHE:
        entry = _FLOOD_CACHE[cache_key]
        if now - entry['timestamp'] < CACHE_TTL:
            return entry['data']

    endpoint = "https://flood-api.open-meteo.com/v1/flood"
    params = {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "daily": [
            "river_discharge",
            "river_discharge_mean",
            "river_discharge_median",
            "river_discharge_max",
            "river_discharge_min"
        ],
        "forecast_days": 7,
        "past_days": 7
    }

    try:
        response = requests.get(endpoint, params=params, timeout=timeout)
        if response.status_code != 200:
            logger.warning(f"Flood API returned {response.status_code} for ({lat}, {lon})")
            return _empty_river_response(lat, lon, "No river discharge model data available at this location.")

        raw = response.json()
        parsed = _process_flood_data(raw, lat, lon)

        _FLOOD_CACHE[cache_key] = {
            'timestamp': now,
            'data': parsed
        }
        return parsed

    except requests.exceptions.Timeout:
        logger.warning(f"Flood API timeout for ({lat}, {lon})")
        return _empty_river_response(lat, lon, "Flood discharge service timed out.")
    except Exception as e:
        logger.error(f"Error fetching river discharge: {e}")
        return _empty_river_response(lat, lon, f"River discharge data unavailable: {str(e)}")

def _process_flood_data(raw: Dict[str, Any], lat: float, lon: float) -> Dict[str, Any]:
    """Parse raw GloFAS flood discharge response."""
    daily = raw.get("daily", {})
    times = daily.get("time", [])
    discharge_series = daily.get("river_discharge", [])
    discharge_mean = daily.get("river_discharge_mean", [])
    discharge_max = daily.get("river_discharge_max", [])
    discharge_min = daily.get("river_discharge_min", [])

    # Check if all discharge values are None, empty, or strictly non-existent
    valid_discharge = [v for v in discharge_series if v is not None]

    if not valid_discharge or len(valid_discharge) == 0:
        return _empty_river_response(
            lat, lon, 
            "No river discharge monitoring station found within immediate drainage basin."
        )

    # Current discharge (approx today index = around index 7 due to 7 past days)
    today_index = min(7, len(discharge_series) - 1) if discharge_series else 0
    current_discharge = discharge_series[today_index] if today_index < len(discharge_series) else valid_discharge[-1]
    
    # Calculate statistics from available values
    peak_forecast = max(valid_discharge)
    historical_mean = (sum(discharge_mean) / len(discharge_mean)) if discharge_mean and any(v is not None for v in discharge_mean) else None
    
    # Ratio of peak discharge to historical mean
    anomaly_ratio = None
    if historical_mean and historical_mean > 0:
        anomaly_ratio = round(peak_forecast / historical_mean, 2)

    return {
        "has_river_data": True,
        "latitude": lat,
        "longitude": lon,
        "current_discharge_m3s": round(current_discharge, 2) if current_discharge is not None else None,
        "peak_forecast_m3s": round(peak_forecast, 2) if peak_forecast is not None else None,
        "historical_mean_m3s": round(historical_mean, 2) if historical_mean is not None else None,
        "anomaly_ratio": anomaly_ratio,
        "discharge_unit": "m³/s",
        "message": "GloFAS river discharge hydrograph available for catchment area.",
        "chart_data": {
            "dates": times,
            "discharge": [round(v, 2) if v is not None else None for v in discharge_series],
            "discharge_mean": [round(v, 2) if v is not None else None for v in discharge_mean],
            "discharge_max": [round(v, 2) if v is not None else None for v in discharge_max],
            "discharge_min": [round(v, 2) if v is not None else None for v in discharge_min]
        }
    }

def _empty_river_response(lat: float, lon: float, reason: str) -> Dict[str, Any]:
    """Graceful empty response for coordinates without a modeled river reach."""
    return {
        "has_river_data": False,
        "latitude": lat,
        "longitude": lon,
        "current_discharge_m3s": None,
        "peak_forecast_m3s": None,
        "historical_mean_m3s": None,
        "anomaly_ratio": None,
        "discharge_unit": "m³/s",
        "message": reason,
        "chart_data": {
            "dates": [],
            "discharge": [],
            "discharge_mean": [],
            "discharge_max": [],
            "discharge_min": []
        }
    }

