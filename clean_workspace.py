import os
import glob
import shutil

def purge_outputs():
    # Targets only visual/document evidence, keeps the CSV history
    patterns = [
        'outputs/*.png',
        'outputs/*.pdf',
        'outputs/*.json'
    ]
    
    print("🧹 Cleaning workspace...")
    count = 0
    
    for pattern in patterns:
        for filepath in glob.glob(pattern):
            try:
                os.remove(filepath) # Permanently deletes the file
                count += 1
            except PermissionError:
                print(f"⚠️ Could not delete {filepath} (File is open).")
            except Exception as e:
                print(f"❌ Error: {e}")

    print(f"✅ Cleanup complete. {count} temporary files removed.")
    print("📜 Note: 'master_audit_log.csv' was preserved for your records.")

if __name__ == "__main__":
    confirm = input("This will delete all PDFs and Maps in /outputs/. Continue? (y/n): ")
    if confirm.lower() == 'y':
        purge_outputs()