import os
import subprocess
import sys

# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INCOMING_DIR = os.path.join(BASE_DIR, "sortedSurveys")
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")

# Use the patched sdaps checkout (adds OCR-training capture/export support)
# rather than the system-wide "sdaps" (an unpatched v1.9.13 install).
SDAPS = [sys.executable, os.path.expanduser("~/PaperQuestionnaires/sdaps/sdaps.py")]

print("🚀 Starting SDAPS recognition...")

# =========================
# LOOP THROUGH FOLDERS
# =========================
for folder_name in os.listdir(INCOMING_DIR):
    folder_path = os.path.join(INCOMING_DIR, folder_name)

    if not os.path.isdir(folder_path):
        continue

    print(f"\n📁 Processing: {folder_name}")

    project_path = os.path.join(PROJECTS_DIR, folder_name)

    if not os.path.exists(project_path):
        print(f"❌ No project found for {folder_name}, skipping")
        continue

    images = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith((".jpg", ".png", ".pdf"))
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

    print(f"✅ Done: {folder_name}")

print("\n🎉 Recognition complete. Ready for human review in the SDAPS GUI.")
