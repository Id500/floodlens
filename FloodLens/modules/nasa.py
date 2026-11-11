from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Supported NASA GIBS Web Mercator (EPSG:3857) Imagery Layers
GIBS_LAYERS = {
    "MODIS_Terra_CorrectedReflectance_Bands721": {
        "name": "MODIS Terra (False Color - Bands 7-2-1)",
        "instrument": "MODIS / Terra",
        "format": "jpg",
        "matrix_set": "GoogleMapsCompatible_Level9",
        "description": "False color composite optimized for distinguishing water from land. Flooded areas and standing water appear deep black or dark blue; healthy vegetation is bright green.",
        "best_for": "Hydrological observation & surface water contrast",
        "transparent": False
    },
    "VIIRS_SNPP_CorrectedReflectance_TrueColor": {
        "name": "VIIRS SNPP (True Color)",
        "instrument": "VIIRS / Suomi NPP",
        "format": "jpg",
        "matrix_set": "GoogleMapsCompatible_Level9",
        "description": "Natural color imagery closest to what the human eye would see. High resolution (375m-750m) Earth observation.",
        "best_for": "Visual landscape assessment, storm cloud patterns",
        "transparent": False
    },
    "MODIS_Terra_CorrectedReflectance_TrueColor": {
        "name": "MODIS Terra (True Color)",
        "instrument": "MODIS / Terra",
        "format": "jpg",
        "matrix_set": "GoogleMapsCompatible_Level9",
        "description": "Daily global true-color coverage from NASA's flagship Terra satellite.",
        "best_for": "Cloud system tracking and daytime context",
        "transparent": False
    },
    "VIIRS_NOAA20_CorrectedReflectance_TrueColor": {
        "name": "VIIRS NOAA-20 (True Color)",
        "instrument": "VIIRS / NOAA-20 (JPSS-1)",
        "format": "jpg",
        "matrix_set": "GoogleMapsCompatible_Level9",
        "description": "Afternoon orbit true color imagery from the Joint Polar Satellite System.",
        "best_for": "Recent afternoon visual conditions",
        "transparent": False
    },
    "IMERG_Precipitation_Rate": {
        "name": "GPM IMERG Precipitation Rate",
        "instrument": "GPM / Dual-frequency Precipitation Radar & Microwave Imager",
        "format": "png",
        "matrix_set": "GoogleMapsCompatible_Level6",
        "description": "NASA Global Precipitation Measurement (GPM) multi-satellite merged precipitation estimates.",
        "best_for": "Rainfall intensity and tropical storm tracking",
        "transparent": True
    }
}

def get_default_imagery_date() -> str:
    """
    Return safe default imagery date (yesterday).
    GIBS high-resolution optical imagery typically takes 3 to 12 hours to mosaic and ingest globally.
    """
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

def get_gibs_tile_url(layer_id: str, date_str: str) -> str:
    """Generate dynamic GIBS WMTS tile template URL for Leaflet."""
    layer = GIBS_LAYERS.get(layer_id, GIBS_LAYERS["MODIS_Terra_CorrectedReflectance_Bands721"])
    fmt = layer["format"]
    matrix = layer["matrix_set"]
    return f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{layer_id}/default/{date_str}/{matrix}/{{z}}/{{y}}/{{x}}.{fmt}"

def get_satellite_metadata(selected_layer: str = None, selected_date: str = None) -> Dict[str, Any]:
    """Retrieve configuration, layer listings, and scientific guidance."""
    date_str = selected_date if selected_date else get_default_imagery_date()
    current_layer_id = selected_layer if selected_layer in GIBS_LAYERS else "MODIS_Terra_CorrectedReflectance_Bands721"

    tile_url = get_gibs_tile_url(current_layer_id, date_str)

    available_layers = [
        {
            "id": k,
            "name": v["name"],
            "instrument": v["instrument"],
            "description": v["description"],
            "best_for": v["best_for"],
            "tile_url": get_gibs_tile_url(k, date_str)
        }
        for k, v in GIBS_LAYERS.items()
    ]

    return {
        "selected_layer": current_layer_id,
        "selected_date": date_str,
        "tile_url": tile_url,
        "layers": available_layers,
        "active_layer_meta": GIBS_LAYERS.get(current_layer_id),
        "scientific_disclaimer": (
            "IMPORTANT SCIENTIFIC CONTEXT: NASA GIBS provides optical and multispectral satellite imagery. "
            "Optical sensors cannot penetrate heavy storm cloud cover. The presence of water or dark pixels "
            "in true or false-color imagery DOES NOT alone prove emergency flooding without calibrated "
            "hydrological analysis or Synthetic Aperture Radar (SAR / Sentinel-1) cross-referencing."
        ),
        "data_sources": {
            "GIBS": "https://gibs.earthdata.nasa.gov/",
            "Earthdata": "https://www.earthdata.nasa.gov/",
            "NASA_GPM": "https://gpm.nasa.gov/data",
            "wmts_endpoint": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/wmts.cgi",
            "get_capabilities": "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/wmts.cgi?SERVICE=WMTS&REQUEST=GetCapabilities",
            "api_docs": "https://nasa-gibs.github.io/gibs-api-docs/access-basics/"
        },
        "leaflet_snippet": f"const nasaSatellite = L.tileLayer('{tile_url}', {{\\n  attribution: 'NASA GIBS',\\n  maxZoom: 9,\\n  opacity: 0.85\\n}});\\nnasaSatellite.addTo(map);"
    }
