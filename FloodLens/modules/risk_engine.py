from typing import Dict, Any, List, Optional
import math

def calculate_flood_risk(weather_data: Dict[str, Any], flood_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explainable Multi-Factor Flood Risk Engine.
    
    Combines precipitation accumulation, rainfall intensity, short-term forecasting,
    antecedent soil saturation trends, and river discharge anomalies into a transparent,
    normalized risk index from 0 to 100.
    
    Dynamically adjusts factor weighting when river monitoring is unavailable.
    """
    # Extract weather metrics
    metrics = weather_data.get("metrics", {})
    current_weather = weather_data.get("current", {})
    daily_forecast = weather_data.get("daily_forecast", [])
    
    precip_24h = metrics.get("precip_24h_accum", 0.0)
    precip_48h = metrics.get("precip_48h_accum", 0.0)
    peak_intensity = metrics.get("peak_hourly_intensity", 0.0)
    total_7d_rain = metrics.get("total_7day_rainfall", 0.0)
    
    # 3-day forecast rainfall sum
    forecast_3d_rain = sum(d.get("precipitation_sum", 0.0) for d in daily_forecast[:3])
    
    # Extract river metrics
    has_river = flood_data.get("has_river_data", False)
    anomaly_ratio = flood_data.get("anomaly_ratio")
    current_discharge = flood_data.get("current_discharge_m3s")
    historical_mean = flood_data.get("historical_mean_m3s")
    
    # Normalize individual components to 0 - 100 scale
    score_24h = _normalize_24h_accumulation(precip_24h)
    score_intensity = _normalize_rain_intensity(peak_intensity)
    score_forecast = _normalize_forecast_rain(forecast_3d_rain)
    score_trend = _normalize_antecedent_trend(total_7d_rain)
    
    # Dynamic weighting depending on river data presence
    factors: List[Dict[str, Any]] = []
    
    if has_river and anomaly_ratio is not None:
        score_river = _normalize_river_discharge(anomaly_ratio, current_discharge, historical_mean)
        weights = {
            "precip_24h": 0.25,
            "forecast_rain": 0.25,
            "rain_intensity": 0.15,
            "river_discharge": 0.25,
            "antecedent_saturation": 0.10
        }
        confidence = "HIGH (Multi-Sensor Hydrometeorological Suite)"
        confidence_level = "High"
        river_status_note = f"River discharge modeled at {current_discharge} m³/s ({anomaly_ratio}x historical baseline)."
    else:
        score_river = 0.0
        weights = {
            "precip_24h": 0.35,
            "forecast_rain": 0.35,
            "rain_intensity": 0.20,
            "river_discharge": 0.00,
            "antecedent_saturation": 0.10
        }
        confidence = "MODERATE (Surface Pluvial Model - River Station Absent)"
        confidence_level = "Moderate"
        river_status_note = "No river discharge station nearby. Pluvial drainage and runoff weights automatically elevated."

    # Compute final score
    composite_score = (
        (score_24h * weights["precip_24h"]) +
        (score_forecast * weights["forecast_rain"]) +
        (score_intensity * weights["rain_intensity"]) +
        (score_river * weights["river_discharge"]) +
        (score_trend * weights["antecedent_saturation"])
    )
    
    # Clamp to [0, 100]
    composite_score = round(max(0.0, min(100.0, composite_score)), 1)
    
    # Determine risk category
    category, color_hex, badge_class = _categorize_risk(composite_score)
    
    # Construct transparent factor attribution
    factors.append({
        "name": "24-Hour Rainfall Accumulation",
        "raw_value": f"{round(precip_24h, 1)} mm",
        "factor_score": round(score_24h, 1),
        "weight_percent": int(weights["precip_24h"] * 100),
        "weighted_points": round(score_24h * weights["precip_24h"], 1),
        "description": "Short-term runoff volume exceeding local storm drainage thresholds."
    })
    factors.append({
        "name": "3-Day Rainfall Forecast",
        "raw_value": f"{round(forecast_3d_rain, 1)} mm",
        "factor_score": round(score_forecast, 1),
        "weight_percent": int(weights["forecast_rain"] * 100),
        "weighted_points": round(score_forecast * weights["forecast_rain"], 1),
        "description": "Incoming precipitation burden likely to compound existing ponding."
    })
    factors.append({
        "name": "Peak Hourly Rain Intensity",
        "raw_value": f"{round(peak_intensity, 1)} mm/h",
        "factor_score": round(score_intensity, 1),
        "weight_percent": int(weights["rain_intensity"] * 100),
        "weighted_points": round(score_intensity * weights["rain_intensity"], 1),
        "description": "Instantaneous cloudburst rate that triggers flash flooding in urban catchments."
    })
    factors.append({
        "name": "River Discharge Anomaly",
        "raw_value": f"{anomaly_ratio}x baseline" if anomaly_ratio else "N/A (Re-weighted)",
        "factor_score": round(score_river, 1),
        "weight_percent": int(weights["river_discharge"] * 100),
        "weighted_points": round(score_river * weights["river_discharge"], 1),
        "description": "GloFAS river channel discharge relative to historical seasonal median."
    })
    factors.append({
        "name": "7-Day Antecedent Saturation",
        "raw_value": f"{round(total_7d_rain, 1)} mm",
        "factor_score": round(score_trend, 1),
        "weight_percent": int(weights["antecedent_saturation"] * 100),
        "weighted_points": round(score_trend * weights["antecedent_saturation"], 1),
        "description": "Soil moisture memory proxy indicating reduced natural infiltration capacity."
    })
    
    # Generate human-readable narrative explanation
    explanation = _generate_explanation(
        composite_score, category, precip_24h, peak_intensity, 
        forecast_3d_rain, total_7d_rain, has_river, anomaly_ratio
    )
    
    # Actionable safety guidance
    recommendations = _get_safety_recommendations(category)

    return {
        "risk_score": composite_score,
        "classification": category,
        "color_hex": color_hex,
        "badge_class": badge_class,
        "confidence": confidence,
        "confidence_level": confidence_level,
        "river_status_note": river_status_note,
        "contributing_factors": factors,
        "weights_applied": {k: int(v * 100) for k, v in weights.items()},
        "explanation": explanation,
        "recommendations": recommendations,
        "methodology": (
            "Multi-Factor Weighted Hydrological Scoring: Transparent algorithm balancing "
            "pluvial precipitation, flash storm intensity, upstream discharge anomalies, "
            "and ground saturation. Not an unverified black-box neural network."
        )
    }

def _normalize_24h_accumulation(val: float) -> float:
    """Normalize 24-hour rainfall (mm) to 0-100 scale."""
    if val <= 5.0:
        return (val / 5.0) * 10.0
    elif val <= 25.0:
        return 10.0 + ((val - 5.0) / 20.0) * 25.0
    elif val <= 65.0:
        return 35.0 + ((val - 25.0) / 40.0) * 35.0
    elif val <= 130.0:
        return 70.0 + ((val - 65.0) / 65.0) * 20.0
    else:
        return min(100.0, 90.0 + ((val - 130.0) / 70.0) * 10.0)

def _normalize_rain_intensity(val: float) -> float:
    """Normalize peak hourly rain rate (mm/h) to 0-100."""
    if val <= 1.0:
        return (val / 1.0) * 10.0
    elif val <= 5.0:
        return 10.0 + ((val - 1.0) / 4.0) * 25.0
    elif val <= 15.0:
        return 35.0 + ((val - 5.0) / 10.0) * 35.0
    elif val <= 30.0:
        return 70.0 + ((val - 15.0) / 15.0) * 20.0
    else:
        return min(100.0, 90.0 + ((val - 30.0) / 20.0) * 10.0)

def _normalize_forecast_rain(val: float) -> float:
    """Normalize 3-day forecasted rainfall (mm) to 0-100."""
    if val <= 10.0:
        return (val / 10.0) * 15.0
    elif val <= 40.0:
        return 15.0 + ((val - 10.0) / 30.0) * 30.0
    elif val <= 100.0:
        return 45.0 + ((val - 40.0) / 60.0) * 35.0
    elif val <= 200.0:
        return 80.0 + ((val - 100.0) / 100.0) * 15.0
    else:
        return min(100.0, 95.0 + ((val - 200.0) / 100.0) * 5.0)

def _normalize_river_discharge(ratio: float, current: Optional[float], mean: Optional[float]) -> float:
    """Normalize river discharge anomaly ratio to 0-100 scale."""
    if ratio is None or ratio <= 0.8:
        return 10.0
    elif ratio <= 1.2:
        return 10.0 + ((ratio - 0.8) / 0.4) * 20.0
    elif ratio <= 2.0:
        return 30.0 + ((ratio - 1.2) / 0.8) * 35.0
    elif ratio <= 3.5:
        return 65.0 + ((ratio - 2.0) / 1.5) * 25.0
    else:
        return min(100.0, 90.0 + ((ratio - 3.5) / 2.0) * 10.0)

def _normalize_antecedent_trend(val: float) -> float:
    """Normalize 7-day cumulative rainfall (mm) as a soil saturation index."""
    if val <= 15.0:
        return (val / 15.0) * 15.0
    elif val <= 50.0:
        return 15.0 + ((val - 15.0) / 35.0) * 30.0
    elif val <= 120.0:
        return 45.0 + ((val - 50.0) / 70.0) * 35.0
    else:
        return min(100.0, 80.0 + ((val - 120.0) / 100.0) * 20.0)

def _categorize_risk(score: float):
    """Categorize 0-100 score into severity levels."""
    if score < 25.0:
        return "LOW", "#10b981", "badge-low"  # Emerald green
    elif score < 50.0:
        return "MODERATE", "#f59e0b", "badge-moderate"  # Amber
    elif score < 75.0:
        return "HIGH", "#f97316", "badge-high"  # Orange
    else:
        return "SEVERE", "#ef4444", "badge-severe"  # Crimson red

def _generate_explanation(
    score: float, category: str, precip_24h: float, 
    peak_intensity: float, forecast_3d: float, total_7d: float,
    has_river: bool, anomaly_ratio: Optional[float]
) -> str:
    """Synthesize transparent, natural-language explanation of risk factors."""
    narrative = []
    
    if category == "LOW":
        narrative.append(
            f"Overall flood risk is currently LOW (Score: {score}/100). "
            f"Ground conditions are generally stable with 24-hour rainfall at {precip_24h:.1f} mm "
            f"and peak rainfall intensity remaining within normal urban drainage thresholds ({peak_intensity:.1f} mm/h)."
        )
    elif category == "MODERATE":
        narrative.append(
            f"Overall flood risk is evaluated at MODERATE (Score: {score}/100). "
            f"Recent precipitation ({precip_24h:.1f} mm in 24h) and expected showers ({forecast_3d:.1f} mm over 3 days) "
            f"may produce localized waterlogging in poorly drained low-lying areas and underpasses."
        )
    elif category == "HIGH":
        narrative.append(
            f"Elevated flood risk warning: HIGH (Score: {score}/100). "
            f"Significant rainfall accumulation ({precip_24h:.1f} mm in 24h) coupled with upcoming precipitation "
            f"({forecast_3d:.1f} mm) is straining surface drainage capacities."
        )
    else:  # SEVERE
        narrative.append(
            f"CRITICAL FLOOD ALERT: SEVERE RISK (Score: {score}/100). "
            f"Extreme hydrometeorological pressure detected with {precip_24h:.1f} mm recent rainfall "
            f"and torrential peak intensities reaching {peak_intensity:.1f} mm/h. "
            f"Severe inundation of roadways, residential zones, and riverbank corridors is imminent or underway."
        )

    # River narrative
    if has_river and anomaly_ratio:
        if anomaly_ratio > 1.5:
            narrative.append(
                f"Catchment river discharge is critically high, running at {anomaly_ratio:.1f}x seasonal median. "
                "Channel overflow risk is elevated."
            )
        else:
            narrative.append(
                f"Monitored river discharge is stable at {anomaly_ratio:.1f}x baseline, keeping riverine flooding subordinate to pluvial drainage."
            )
    else:
        narrative.append(
            "This location has no modeled major river channel; calculations prioritize surface runoff and pluvial drainage dynamics."
        )

    # Soil saturation narrative
    if total_7d > 80.0:
        narrative.append(
            f"Antecedent soil saturation is high ({total_7d:.1f} mm in past 7 days), "
            "significantly reducing natural ground absorption and accelerating surface runoff."
        )
    else:
        narrative.append(
            f"Antecedent 7-day rainfall ({total_7d:.1f} mm) indicates moderate soil absorption buffer remains."
        )

    return " ".join(narrative)

def _get_safety_recommendations(category: str) -> List[str]:
    """Provide tailored civil protection advisories based on category."""
    if category == "LOW":
        return [
            "Normal civil activity; standard routine drainage monitoring.",
            "Inspect neighborhood storm drains and clean debris proactively.",
            "Stay informed of regular weather forecast updates."
        ]
    elif category == "MODERATE":
        return [
            "Avoid parking vehicles in subterranean basements or known depression zones.",
            "Exercise caution near roadside ditches, culverts, and under construction trenches.",
            "Monitor local municipal civic alerts and civic flood advisory boards."
        ]
    elif category == "HIGH":
        return [
            "Keep emergency battery lights, first-aid, potable water, and power banks charged.",
            "Avoid non-essential vehicular travel through flooded underpasses or low causeways.",
            "Residents in ground-floor flood-prone zones should elevate valuable electrical appliances.",
            "Follow community reports and municipal evacuation notices closely."
        ]
    else:  # SEVERE
        return [
            "IMMEDIATE ACTION: Move to higher floors or designated civil relief shelters if in low-lying zones.",
            "DO NOT drive or walk into flowing water. 'Turn Around, Don't Drown.' 15 cm of moving water can sweep cars.",
            "Disconnect electrical mains if water enters property to prevent electrocution.",
            "Keep emergency contact lines accessible: Fire, Police, Disaster Response (NDRF/SDRF/911/112)."
        ]

