import ee
import os
import requests
import pandas as pd
import datetime
from PIL import Image, ImageDraw

# Verified Project ID
PROJECT_ID = 'treechecker'

# Ensure outputs directory always exists
os.makedirs('outputs', exist_ok=True)

try:
    ee.Initialize(project=PROJECT_ID)
except Exception:
    print(f"🛰️ Authenticating Google Earth Engine for project: {PROJECT_ID}")
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)

def run_satellite_audit(lat, lon, audit_id, final_verdict=None):
    """
    Analyzes forest loss and generates a high-contrast evidence map.
    Returns: (verdict, loss_m2, map_path)
    
    final_verdict: if provided, stamps the map with the legal verdict
    (e.g. LEGALLY_INCOMPLETE) rather than the raw satellite verdict.
    """
    # 1. SET ZOOM: 5km buffer for landscape context
    plot_area = ee.Geometry.Point([lon, lat]).buffer(5000)  # 5km circle used for the analysis
    region = plot_area.bounds()  # square frame used only for the map image

    # 2. FETCH DATA: Hansen Global Forest Change (v1.13)
    gfc = ee.Image('UMD/hansen/global_forest_change_2025_v1_13')

    # 3. ANALYZE AREA: Post-2020 legal baseline
    recent_loss = gfc.select('lossyear').gte(21)
    area_image = recent_loss.multiply(ee.Image.pixelArea())
    stats = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=plot_area,
        scale=30,
        maxPixels=1e9
    )
    total_loss_m2 = stats.get('lossyear').getInfo() or 0

    # 4. VERDICT: EUDR Threshold Check
    satellite_verdict = "NON_COMPLIANT" if total_loss_m2 > 1000 else "COMPLIANT"

    # 5. VISUALIZATION: Blend Red Loss ON TOP of Green Forest
    forest_viz = gfc.select('treecover2000').visualize(
        palette=['000000', '006400'],
        min=0,
        max=100
    )
    loss_viz = gfc.select('lossyear').gte(21).selfMask().visualize(
        palette=['FF0000']
    )
    final_viz = forest_viz.blend(loss_viz)

    map_path = f"outputs/map_{audit_id}.png"
    vis_url = final_viz.getThumbURL({
        'region': region,
        'dimensions': 512,
        'format': 'png'
    })

    # 6. SAVE AND STAMP
    response = requests.get(vis_url)
    with open(map_path, 'wb') as f:
        f.write(response.content)

    # Use final legal verdict on stamp if provided, else fall back to satellite verdict
    stamp_verdict = final_verdict if final_verdict else satellite_verdict
    img = Image.open(map_path)
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), f"ID: {audit_id} | {stamp_verdict}", fill="white")
    img.save(map_path)

    # 7. LOG TO CSV
    log_to_csv(audit_id, total_loss_m2, satellite_verdict, stamp_verdict)

    return satellite_verdict, total_loss_m2, map_path

def log_to_csv(audit_id, area, satellite_verdict, legal_verdict):
    """Updates the 2026 Executive Dashboard."""
    log_file = 'outputs/master_audit_log.csv'
    df = pd.DataFrame([{
        'Date': datetime.date.today(),
        'Audit_ID': audit_id,
        'Area_m2': area,
        'Satellite_Verdict': satellite_verdict,
        'Legal_Verdict': legal_verdict
    }])
    try:
        df.to_csv(log_file, mode='a', header=not os.path.exists(log_file), index=False)
    except PermissionError:
        print(f"⚠️ Could not write to {log_file} - close it in Excel and rerun.")