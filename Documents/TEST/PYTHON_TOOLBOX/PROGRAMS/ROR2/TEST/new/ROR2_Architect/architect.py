# [ROR2 Repo Doctor] - v3.0 (Diagnostic & Repair)
# Description: Force uploads Data/Profiles and runs deep diagnostics to find "Ghost Push" errors.

import os
import subprocess
import sys

def run_cmd(args, label):
    print(f"\n--- [STEP: {label}] ---")
    print(f"Command: {' '.join(args)}")
    try:
        # Run command and capture ALL output (stdout and stderr)
        result = subprocess.run(
            args, 
            check=False, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        if result.stdout:
            print(f"OUTPUT:\n{result.stdout.strip()}")
        if result.stderr:
            print(f"ERRORS/INFO:\n{result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"CRITICAL EXECUTION ERROR: {e}")
        return False

def check_local_files():
    print(f"\n--- [STEP: AUDIT LOCAL FILES] ---")
    data_path = os.path.join(os.getcwd(), "ROR2_Data")
    profile_path = os.path.join(data_path, "Profiles")
    
    if not os.path.exists(data_path):
        print(f"[FAIL] ROR2_Data folder is MISSING at {data_path}")
        return False
        
    print(f"[OK] ROR2_Data exists.")
    
    # Check item count
    item_count = 0
    for root, dirs, files in os.walk(data_path):
        item_count += len(files)
    print(f"[INFO] Total files in ROR2_Data: {item_count}")
    
    if not os.path.exists(profile_path):
        print(f"[WARN] Profiles folder is missing. Creating it...")
        os.makedirs(profile_path, exist_ok=True)
        # Create a dummy file to force Git to see the folder
        with open(os.path.join(profile_path, ".gitkeep"), "w") as f:
            f.write("Git keep file")
            
    print(f"[OK] Profiles folder ready.")
    return True

def main():
    print("=== RISK OF RAIN 2 REPO DOCTOR ===")
    
    # 1. Audit Files
    if not check_local_files():
        input("Press Enter to exit...")
        return

    # 2. Check Remote URL (Is it going to the right place?)
    run_cmd(["git", "remote", "-v"], "CHECK REMOTES")

    # 3. Check Current Branch
    run_cmd(["git", "branch", "-v"], "CHECK BRANCH")

    # 4. Force Add Everything (Including Profiles)
    run_cmd(["git", "add", "-f", "ROR2_Data/"], "STAGE DATA")
    run_cmd(["git", "add", "architect.py"], "STAGE SCRIPT")

    # 5. Commit
    # We use --allow-empty so it reports success even if you ran it 5 seconds ago
    run_cmd(["git", "commit", "-m", "Repo Doctor: Force Update Data & Profiles", "--allow-empty"], "COMMIT SNAPSHOT")

    # 6. The Push
    print("\n--- [STEP: PUSH TO GITHUB] ---")
    # We force push to 'main' to ensure local overrides remote
    success = run_cmd(["git", "push", "-u", "origin", "main", "--force"], "UPLINK")

    # 7. Post-Mortem Diagnostics (The info you asked for)
    print("\n\n=== DIAGNOSTIC REPORT (SEND THIS TO AI) ===")
    run_cmd(["git", "log", "-1", "--stat"], "LAST COMMIT LOG")
    run_cmd(["git", "status"], "FINAL GIT STATUS")
    
    print("\n===========================================")
    if success:
        print("VERDICT: Script finished. If 'LAST COMMIT LOG' shows files, they are on GitHub.")
    else:
        print("VERDICT: Errors detected. Check the ERRORS/INFO sections above.")
    
    input("Press Enter to close...")

if __name__ == "__main__":
    main()
