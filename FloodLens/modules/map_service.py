import requests
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

PRESET_LOCATIONS = [
    {
        "name": "Chennai, Tamil Nadu, India",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "description": "Coastal metropolis vulnerable to northeast monsoon cyclonic surges and urban inundation (Default Focus)."
    },
    {
        "name": "Mumbai, Maharashtra, India",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "description": "High-density coastal megacity prone to extreme southwest monsoon cloudbursts and high-tide river backflows."
    },
    {
        "name": "Dhaka, Bangladesh",
        "latitude": 23.8103,
        "longitude": 90.4125,
        "description": "Low-lying deltaic mega-basin susceptible to combined Brahmaputra-Meghna-Padma riverine flooding."
    },
    {
        "name": "Houston, Texas, USA",
        "latitude": 29.7604,
        "longitude": -95.3698,
        "description": "Low-relief coastal bayou system exposed to Atlantic hurricane surges and tropical storm deluges."
    },
    {
        "name": "Jakarta, Indonesia",
        "latitude": -6.2088,
        "longitude": 106.8456,
        "description": "Subsiding coastal basin intersecting 13 rivers facing severe compound pluvial-tidal inundation."
    },
    {
        "name": "New Orleans, Louisiana, USA",
        "latitude": 29.9511,
        "longitude": -90.0715,
        "description": "Below-sea-level deltaic basin protected by complex levee networks and pumping infrastructure."
    },
    {
        "name": "London (Thames Basin), UK",
        "latitude": 51.5074,
        "longitude": -0.1278,
        "description": "Tidal estuary defended by Thames Barrier with significant urban flash runoff vulnerability."
    }
]

def search_location(query: str, timeout: int = 6) -> List[Dict[str, Any]]:
    """
    Search coordinates worldwide via OpenStreetMap Nominatim API.
    Returns matched locations with latitude, longitude, and formatted name.
    """
    if not query or len(query.strip()) < 2:
        return []

    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "FloodLens-NASA-Disaster-Monitor/1.0 (academic-research-tool)"
    }
    params = {
        "q": query.strip(),
        "format": "json",
        "limit": 5,
        "addressdetails": 1
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        if response.status_code == 200:
            results = response.json()
            formatted = []
            for item in results:
                formatted.append({
                    "name": item.get("display_name", "Unknown Location"),
                    "latitude": float(item.get("lat")),
                    "longitude": float(item.get("lon")),
                    "type": item.get("type", "location")
                })
            return formatted
        return []
    except Exception as e:
        logger.warning(f"Geocoding lookup error: {e}")
        return []

