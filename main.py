import os
import pandas as pd
import json
from sensor import run_satellite_audit
from report_gen import create_pdf_report

RISK_LEVELS = {
    "VN": "LOW", "GB": "LOW", "US": "LOW", "CN": "LOW",
    "BR": "STANDARD", "ID": "STANDARD", "ET": "STANDARD", "CD": "STANDARD", "CI": "STANDARD",
    "RU": "HIGH", "BY": "HIGH", "MM": "HIGH", "KP": "HIGH"
}

FINE_RATES = {
    "NON_COMPLIANT": 0.04,
    "LEGALLY_INCOMPLETE": 0.02,
    "DATA_GAP": 0.01,
    "COMPLIANT": 0.0
}

def calculate_financial_risk(compliance_status, eu_turnover, plot_size_ha, risk_class):
    fine_rate = FINE_RATES.get(compliance_status, 0.0)

    # Euro figure only when real turnover is supplied; otherwise exposure is reported as % only
    estimated_fine = round(eu_turnover * fine_rate, 2) if eu_turnover is not None else None

    compliance_score = {
        "NON_COMPLIANT": 50,
        "LEGALLY_INCOMPLETE": 30,
        "DATA_GAP": 20,
        "COMPLIANT": 0
    }.get(compliance_status, 0)

    size_score = min(plot_size_ha / 10, 1.0) * 30
    country_score = {"HIGH": 20, "STANDARD": 10, "LOW": 0}.get(risk_class, 10)
    financial_risk_score = round(compliance_score + size_score + country_score, 1)

    return {
        "estimated_fine": estimated_fine,
        "fine_rate_pct": fine_rate * 100,
        "financial_risk_score": financial_risk_score,
        "eu_turnover_used": eu_turnover
    }

def execute_batch_audit():
    print("🚀 2026 GLOBAL AUDIT SYSTEM ACTIVATED")

    input_file = 'coordinates_csv.xlsx'

    if not os.path.exists(input_file):
        print(f"❌ Error: '{input_file}' not found.")
        return

    df = pd.read_excel(input_file, engine='openpyxl')
    geojson_features = []

    print(f"📋 Found {len(df)} plots to audit. Processing supply chain...\n")

    for index, row in df.iterrows():
        audit_id = str(row['audit_id'])
        lat = float(row['latitude'])
        lon = float(row['longitude'])
        country = str(row['country_code']).upper()
        plot_size = float(row['hectares']) if pd.notna(row.get('hectares')) else 0.0
        supplier_name = str(row.get('supplier_name', 'Unknown Supplier'))

        # Turnover is optional: None if the column is missing or the cell is blank
        if 'eu_turnover_eur' in row and pd.notna(row['eu_turnover_eur']):
            eu_turnover = float(row['eu_turnover_eur'])
        else:
            eu_turnover = None

        # 1. RISK CLASS (EU EUDR country benchmarking; unlisted countries default to STANDARD)
        risk_class = RISK_LEVELS.get(country, "STANDARD")

        # 2. LEGAL LOGIC FIRST — so we can pass it to the sensor stamp
        if plot_size > 4:
            compliance_status = "LEGALLY_INCOMPLETE"
            sys_note = f"ACTION REQUIRED: {risk_class} risk plot > 4ha requires Polygon."
        elif plot_size <= 0:
            compliance_status = "DATA_GAP"
            sys_note = "WARNING: Plot size missing. Mandatory for verification."
        else:
            # Placeholder — will be replaced by satellite verdict below
            compliance_status = None
            sys_note = None

        # 3. SATELLITE ENGINE — pass compliance_status if already determined
        satellite_verdict, total_loss, map_path = run_satellite_audit(
            lat, lon, audit_id,
            final_verdict=compliance_status  # None if plot size is valid — sensor uses its own verdict
        )

        # 4. IF plot size was valid, use the satellite verdict
        if compliance_status is None:
            compliance_status = satellite_verdict
            sys_note = f"Point-based audit valid for {risk_class} risk smallholder."

        # 5. FINANCIAL RISK
        fin = calculate_financial_risk(compliance_status, eu_turnover, plot_size, risk_class)

        # 6. GENERATE PDF
        create_pdf_report(
            audit_id=audit_id,
            supplier_name=supplier_name,
            verdict=compliance_status,
            area_lost=total_loss,
            map_path=map_path
        )

        # 7. GEOJSON
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(lon, 6), round(lat, 6)]
            },
            "properties": {
                "Audit_ID": audit_id,
                "Country_Risk": risk_class,
                "Plot_Size_HA": plot_size,
                "Final_Verdict": compliance_status,
                "Regulatory_Note": sys_note,
                "EU_Turnover_Used_EUR": fin["eu_turnover_used"],
                "Fine_Rate_PCT": fin["fine_rate_pct"],
                "Est_EU_Fine_EUR": fin["estimated_fine"],
                "Financial_Risk_Score": fin["financial_risk_score"]
            }
        }
        geojson_features.append(feature)

        if fin["estimated_fine"] is not None:
            exposure = f"€{fin['estimated_fine']:,.0f}"
        else:
            exposure = f"{fin['fine_rate_pct']:.0f}% of EU turnover (turnover not supplied)"
        print(f"✅ {audit_id}: {compliance_status} | 🎯 Risk Score: {fin['financial_risk_score']}/100 | 💶 Est. Exposure: {exposure}")

    # 8. SAVE BATCH
    with open("compliance_batch_2026.geojson", "w") as f:
        json.dump({"type": "FeatureCollection", "features": geojson_features}, f, indent=4)

    print(f"\n✨ DONE. 'compliance_batch_2026.geojson' is ready.")

if __name__ == "__main__":
    execute_batch_audit()