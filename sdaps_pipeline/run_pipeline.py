import os
import subprocess
import shutil
import glob
import sys
import datetime

# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INCOMING_DIR = os.path.join(BASE_DIR, "sortedSurveys")
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
OUTPUT_DIR = os.path.join(BASE_DIR, "csv_outputs")

# Use the patched sdaps checkout (adds OCR-training capture/export support)
# rather than the system-wide "sdaps" (an unpatched v1.9.13 install).
SDAPS = [sys.executable, os.path.expanduser("~/PaperQuestionnaires/sdaps/sdaps.py")]

print("🚀 Starting SDAPS pipeline...")

# =========================
# LOOP THROUGH FOLDERS
# =========================
for folder_name in os.listdir(INCOMING_DIR):
    folder_path = os.path.join(INCOMING_DIR, folder_name)

    if not os.path.isdir(folder_path):
        continue

    print(f"\n📁 Processing: {folder_name}")

    project_path = os.path.join(PROJECTS_DIR, folder_name)
    output_path = os.path.join(OUTPUT_DIR, folder_name)

    if not os.path.exists(project_path):
        print(f"❌ No project found for {folder_name}, skipping")
        continue

    os.makedirs(output_path, exist_ok=True)

    images = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith((".jpg", ".png",".pdf"))
    ]

    # 🚨 STOP if no images
    if not images:
        print("⚠️ No images found")
        continue

    # =========================
    # STEP 1: ADD IMAGES
    # =========================
    for img in images:
        img_path = os.path.join(folder_path, img)
        print(f"  ➕ Adding {img}")
        try:
            subprocess.run(
                SDAPS + ["add", project_path, "--convert", img_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to add {img}: {e}")
            continue

    # =========================
    # STEP 2: RECOGNIZE
    # =========================
    print("  🔍 Recognizing...")
    try:
        subprocess.run(SDAPS + ["recognize", project_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to recognize {folder_name}: {e}")
        continue

    # =========================
    # STEP 3: EXPORT CSV
    # =========================
    print("  📤 Exporting CSV...")
    try:
        subprocess.run(SDAPS + ["export", "csv", project_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to export CSV for {folder_name}: {e}")
        continue

    # =========================
    # STEP 4: GET SDAPS DATA 
    # =========================
    print("  📄 Retrieving SDAPS data...")

    data_files = glob.glob(os.path.join(project_path, "data_*.csv"))
    
    # Create a new directory for this run based on timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_output_dir = os.path.join(output_path, timestamp)
    os.makedirs(run_output_dir, exist_ok=True)

    if data_files:
        latest_file = max(data_files, key=os.path.getctime)
        # Keep the exact project name for the CSV
        destination = os.path.join(run_output_dir, f"{folder_name}.csv")

        shutil.copy(latest_file, destination)

        print(f"  ✅ Copied: {latest_file} → {destination}")
    else:
        print("  ⚠️ No data files found")

    # =========================
    # STEP 5: MOVE IMAGES
    # =========================
    print("  📦 Moving processed images...")
    for img in images:
        shutil.move(
            os.path.join(folder_path, img),
            os.path.join(run_output_dir, img)
        )

    print(f"✅ Done: {folder_name}")

print("\n🎉 Pipeline complete.")