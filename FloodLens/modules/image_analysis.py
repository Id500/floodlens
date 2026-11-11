import os
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import cv2

def analyze_satellite_image(input_image_path: str, output_image_path: str) -> Dict[str, Any]:
    """
    Experimental satellite & aerial image analysis using OpenCV.
    
    Performs:
    1. Image quality diagnostics (sharpness, contrast, brightness, resolution)
    2. Multi-spectral / color-space water segmentation
    3. Morphological filtering & contour extraction
    4. Highlighted water mask overlay generation
    5. Surface area estimation and scientific confidence assessment
    """
    # Windows path safe read with numpy
    img_array = np.fromfile(input_image_path, dtype=np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Could not decode image file. Ensure valid JPG, PNG, or TIFF format.")

    height, width, channels = image.shape
    total_pixels = height * width

    # 1. Quality Diagnostics
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Sharpness via Laplacian variance
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    sharpness_status = "Crisp" if laplacian_var > 120 else ("Moderate" if laplacian_var > 40 else "Blurry / Soft")
    
    # Brightness (mean pixel intensity)
    mean_brightness = float(np.mean(gray))
    brightness_status = "Optimal"
    if mean_brightness < 45:
        brightness_status = "Under-exposed / Night or Shadow"
    elif mean_brightness > 210:
        brightness_status = "Over-exposed / High Cloud Glare"

    # Contrast (standard deviation of intensity)
    contrast_std = float(np.std(gray))
    contrast_status = "High" if contrast_std > 50 else ("Moderate" if contrast_std > 25 else "Low Contrast")

    # Overall image quality score (0 - 100)
    q_score = 50.0
    if laplacian_var > 100: q_score += 25.0
    elif laplacian_var > 40: q_score += 15.0
    
    if 60 <= mean_brightness <= 180: q_score += 15.0
    else: q_score += 5.0
    
    if contrast_std > 40: q_score += 10.0
    
    quality_score = min(100.0, round(q_score, 1))

    # 2. Experimental Water Detection Segmentation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Deep water / False Color dark water signature (low brightness, blue-cyan hues)
    # HSV: Hue (85 - 135 for blue/cyan), Saturation (30 - 255), Value (20 - 160)
    lower_deep_water = np.array([80, 30, 20])
    upper_deep_water = np.array([135, 255, 175])
    mask_deep = cv2.inRange(hsv, lower_deep_water, upper_deep_water)

    # In False-Color (Bands 7-2-1), deep water bodies and fresh floods appear very dark (V < 50, low R)
    b, g, r = cv2.split(image)
    dark_water_mask = (gray < 55) & (b >= r)
    dark_water_mask = (dark_water_mask.astype(np.uint8)) * 255

    # Turbid / muddy flood water signature (brownish/ochre hues, low-medium saturation)
    lower_turbid = np.array([10, 30, 40])
    upper_turbid = np.array([30, 180, 150])
    mask_turbid = cv2.inRange(hsv, lower_turbid, upper_turbid)

    # Blue-ratio index: In true color, water exhibits higher Blue-to-Red ratio
    blue_ratio = np.divide(b.astype(np.float32) + 1.0, r.astype(np.float32) + 1.0)
    water_ratio_mask = ((blue_ratio > 1.25) & (gray < 160)).astype(np.uint8) * 255

    # Combine water evidence masks
    combined_mask = cv2.bitwise_or(mask_deep, dark_water_mask)
    combined_mask = cv2.bitwise_or(combined_mask, cv2.bitwise_and(mask_turbid, water_ratio_mask))

    # 3. Morphological Filtering to eliminate single-pixel noise and connect water bodies
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    
    # Remove noise
    cleaned_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel_small, iterations=1)
    # Bridge small gaps in river channels
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel_large, iterations=2)

    # 4. Contour Extraction & Filtering
    contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    min_area_threshold = max(20, int(total_pixels * 0.0001))  # 0.01% of image or 20 pixels
    significant_contours = [c for c in contours if cv2.contourArea(c) >= min_area_threshold]

    # Rebuild mask from significant contours only
    final_water_mask = np.zeros((height, width), dtype=np.uint8)
    cv2.drawContours(final_water_mask, significant_contours, -1, 255, thickness=cv2.FILLED)

    water_pixel_count = int(np.sum(final_water_mask > 0))
    water_coverage_pct = round((water_pixel_count / total_pixels) * 100.0, 2)

    # 5. Visualized Output Generation
    annotated = image.copy()
    
    # Translucent cyan tint on water mask: BGR (240, 190, 40) -> vibrant azure
    water_tint = np.zeros_like(image, dtype=np.uint8)
    water_tint[final_water_mask > 0] = [235, 180, 30]
    
    # Alpha blend: 70% original, 30% water tint
    cv2.addWeighted(water_tint, 0.45, annotated, 0.75, 0, annotated)

    # Draw vibrant contour boundaries around candidate zones
    cv2.drawContours(annotated, significant_contours, -1, (255, 230, 0), thickness=2)

    # Highlight top 5 largest water regions with bounding boxes & ID
    sorted_contours = sorted(significant_contours, key=cv2.contourArea, reverse=True)[:5]
    for idx, cnt in enumerate(sorted_contours):
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 255), 1)
        label = f"W-{idx+1} ({round((cv2.contourArea(cnt)/total_pixels)*100, 2)}%)"
        cv2.putText(
            annotated, label, (x, max(15, y - 5)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA
        )

    # Save output using cv2.imencode for Windows path safety
    output_dir = Path(output_image_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ext = Path(output_image_path).suffix.lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        ext = '.jpg'
    
    success, encoded_img = cv2.imencode(ext, annotated)
    if success:
        with open(output_image_path, "wb") as f:
            f.write(encoded_img.tobytes())
    else:
        cv2.imwrite(output_image_path, annotated)

    # Determine scientific confidence
    if quality_score >= 75 and 1.0 <= water_coverage_pct <= 65.0:
        cv_confidence = "Moderate - Optical Spectral Match"
    elif quality_score < 50:
        cv_confidence = "Low - Degraded Image Quality / Glare"
    else:
        cv_confidence = "Heuristic - Manual Verification Required"

    return {
        "success": True,
        "image_dimensions": {
            "width": width,
            "height": height,
            "total_pixels": total_pixels,
            "megapixels": round(total_pixels / 1_000_000.0, 2)
        },
        "quality_diagnostics": {
            "quality_score": quality_score,
            "sharpness_var": round(laplacian_var, 1),
            "sharpness_status": sharpness_status,
            "brightness_mean": round(mean_brightness, 1),
            "brightness_status": brightness_status,
            "contrast_std": round(contrast_std, 1),
            "contrast_status": contrast_status
        },
        "water_detection": {
            "water_coverage_percentage": water_coverage_pct,
            "water_pixel_count": water_pixel_count,
            "detected_regions_count": len(significant_contours),
            "top_regions_detected": len(sorted_contours),
            "confidence_label": cv_confidence
        },
        "output_image_filename": Path(output_image_path).name,
        "scientific_disclaimer": (
            "EXPERIMENTAL COMPUTER VISION SEGMENTATION: This analysis utilizes OpenCV spectral heuristics "
            "and HSV color segmentation. It does NOT constitute scientifically certified flood extent mapping. "
            "Optical imagery is vulnerable to cloud shadows, asphalt, and terrain shade misclassification. "
            "Certified disaster management requires Synthetic Aperture Radar (SAR / Sentinel-1) or calibrated ground-truth."
        )
    }

