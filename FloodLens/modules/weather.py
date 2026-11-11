import time
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Simple in-memory cache to respect API rate limits
_WEATHER_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 300  # 5 minutes

WEATHER_CODE_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm: Slight or moderate",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

def get_weather_description(code: int) -> str:
    """Return friendly weather condition from WMO code."""
    return WEATHER_CODE_DESCRIPTIONS.get(code, "Cloudy / Variable")

def fetch_weather_data(lat: float, lon: float, timeout: int = 10) -> Dict[str, Any]:
    """
    Fetch comprehensive meteorological data from Open-Meteo Forecast API.
    Handles caching, timeouts, and detailed error tracking.
    """
    cache_key = f"{round(lat, 3)}_{round(lon, 3)}"
    now = time.time()
    
    if cache_key in _WEATHER_CACHE:
        entry = _WEATHER_CACHE[cache_key]
        if now - entry['timestamp'] < CACHE_TTL:
            return entry['data']

    endpoint = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "is_day",
            "precipitation",
            "rain",
            "weather_code",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m"
        ],
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "rain",
            "weather_code",
            "wind_speed_10m"
        ],
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_hours",
            "precipitation_probability_max",
            "wind_speed_10m_max"
        ],
        "timezone": "auto"
    }

    try:
        response = requests.get(endpoint, params=params, timeout=timeout)
        response.raise_for_status()
        raw_data = response.json()
        
        parsed = _process_weather_data(raw_data, lat, lon)
        
        # Cache clean response
        _WEATHER_CACHE[cache_key] = {
            'timestamp': now,
            'data': parsed
        }
        return parsed
    except requests.exceptions.Timeout:
        logger.error(f"Weather API timeout for coords ({lat}, {lon})")
        raise RuntimeError("Weather service timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API error: {e}")
        raise RuntimeError(f"Failed to fetch weather data: {str(e)}")

def _process_weather_data(raw: Dict[str, Any], lat: float, lon: float) -> Dict[str, Any]:
    """Process raw Open-Meteo response into clean domain models."""
    current = raw.get("current", {})
    hourly = raw.get("hourly", {})
    daily = raw.get("daily", {})
    
    weather_code = current.get("weather_code", 0)
    weather_desc = get_weather_description(weather_code)
    
    # Calculate 24-hour and 48-hour precipitation accumulation from hourly forecast
    hourly_precip = hourly.get("precipitation", [])
    hourly_times = hourly.get("time", [])
    
    # Next 24 hours of hourly precipitation
    next_24h_precip = hourly_precip[:24] if hourly_precip else []
    precip_24h_accum = round(sum(next_24h_precip), 2) if next_24h_precip else 0.0
    
    # Next 48 hours
    next_48h_precip = hourly_precip[:48] if len(hourly_precip) >= 48 else hourly_precip
    precip_48h_accum = round(sum(next_48h_precip), 2) if next_48h_precip else 0.0

    # Peak hourly rain rate in next 24h
    peak_hourly_intensity = max(next_24h_precip) if next_24h_precip else 0.0

    # 7-day total rainfall
    daily_precip_sums = daily.get("precipitation_sum", [])
    total_7day_rainfall = round(sum(daily_precip_sums), 2) if daily_precip_sums else 0.0

    # Structure 7-day daily forecast
    daily_forecasts = []
    daily_times = daily.get("time", [])
    t_max = daily.get("temperature_2m_max", [])
    t_min = daily.get("temperature_2m_min", [])
    p_sum = daily.get("precipitation_sum", [])
    p_prob = daily.get("precipitation_probability_max", [])
    w_code = daily.get("weather_code", [])
    w_speed = daily.get("wind_speed_10m_max", [])

    for i in range(min(7, len(daily_times))):
        code_val = w_code[i] if i < len(w_code) else 0
        daily_forecasts.append({
            "date": daily_times[i] if i < len(daily_times) else "",
            "temp_max": t_max[i] if i < len(t_max) else None,
            "temp_min": t_min[i] if i < len(t_min) else None,
            "precipitation_sum": p_sum[i] if i < len(p_sum) else 0.0,
            "precipitation_probability_max": p_prob[i] if i < len(p_prob) else 0,
            "wind_speed_max": w_speed[i] if i < len(w_speed) else None,
            "weather_code": code_val,
            "description": get_weather_description(code_val)
        })

    # Prepare 24-hour hourly charts data
    chart_hours = hourly_times[:24] if hourly_times else []
    chart_temps = hourly.get("temperature_2m", [])[:24]
    chart_precip = next_24h_precip
    chart_prob = hourly.get("precipitation_probability", [])[:24]
    chart_humidity = hourly.get("relative_humidity_2m", [])[:24]
    chart_wind = hourly.get("wind_speed_10m", [])[:24]

    # Friendly formatted hour labels (e.g., '14:00')
    formatted_hour_labels = [h.split("T")[-1][:5] if "T" in h else h for h in chart_hours]

    return {
        "latitude": lat,
        "longitude": lon,
        "timezone": raw.get("timezone", "UTC"),
        "current": {
            "temperature": current.get("temperature_2m", 0.0),
            "apparent_temperature": current.get("apparent_temperature", 0.0),
            "humidity": current.get("relative_humidity_2m", 0),
            "precipitation": current.get("precipitation", 0.0),
            "rain": current.get("rain", 0.0),
            "wind_speed": current.get("wind_speed_10m", 0.0),
            "wind_direction": current.get("wind_direction_10m", 0),
            "wind_gusts": current.get("wind_gusts_10m", 0.0),
            "pressure": current.get("surface_pressure", 1013.25),
            "weather_code": weather_code,
            "weather_description": weather_desc,
            "is_day": current.get("is_day", 1)
        },
        "metrics": {
            "precip_24h_accum": precip_24h_accum,
            "precip_48h_accum": precip_48h_accum,
            "peak_hourly_intensity": peak_hourly_intensity,
            "total_7day_rainfall": total_7day_rainfall
        },
        "hourly_chart": {
            "labels": formatted_hour_labels,
            "full_timestamps": chart_hours,
            "temperatures": chart_temps,
            "precipitations": chart_precip,
            "precipitation_probabilities": chart_prob,
            "humidity": chart_humidity,
            "wind_speeds": chart_wind
        },
        "daily_forecast": daily_forecasts
    }

