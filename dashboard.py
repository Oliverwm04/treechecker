import pandas as pd
import os

def generate_dashboard():
    log_file = 'outputs/master_audit_log.csv'
    
    # 1. Verification Check
    if not os.path.exists(log_file):
        print("❌ No audit log found. Run some batch tests first!")
        return

    # 2. Load Data (Ensures the file isn't locked by Excel)
    try:
        df = pd.read_csv(log_file)
    except PermissionError:
        print("❌ CLOSE EXCEL! Dashboard cannot read the log while it's open.")
        return

    # 3. Calculate Analytics
    total_audits = len(df)
    compliant_count = len(df[df['Legal_Verdict'] == 'COMPLIANT'])
    non_compliant_count = len(df[df['Legal_Verdict'] == 'NON_COMPLIANT'])
    pass_rate = (compliant_count / total_audits) * 100 if total_audits > 0 else 0
    total_area_lost = df['Area_m2'].sum()

    # 4. Print Executive Summary
    print("-" * 50)
    print("📊 2026 GLOBAL EUDR COMPLIANCE DASHBOARD")
    print("-" * 50)
    print(f"Total Plots Audited:  {total_audits}")
    print(f"Compliant Plots:      {compliant_count} (Safe ✅)")
    print(f"Non-Compliant Plots:  {non_compliant_count} (At Risk 🚨)")
    print(f"Overall Pass Rate:    {pass_rate:.1f}%")
    print(f"Total Illegal Loss:   {total_area_lost:,.2f} m2")
    print("-" * 50)
    
    # 5. Risk Identification
    if non_compliant_count > 0:
        print("\n🔥 CRITICAL RISKS (Highest Deforestation):")
        risks = df[df['Legal_Verdict'] == 'NON_COMPLIANT'].sort_values(by='Area_m2', ascending=False)
        print(risks[['Audit_ID', 'Area_m2']].head())
    print("-" * 50)

if __name__ == "__main__":
    generate_dashboard()