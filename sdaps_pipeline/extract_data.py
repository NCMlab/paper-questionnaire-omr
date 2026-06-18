import os
import subprocess
import shutil
import glob
import sys
import datetime
import re
import json
import pandas as pd
import requests

from crypto_utils import PUBLIC_KEY_PATH, encrypt_json, load_public_key

# =========================
# FUNCTIONS
# =========================
def get_scale_id(tex_path: str) -> str | None:
    """Return the scale_id value from \\addinfo{scale_id}{...} in a SDAPS .tex file."""
    pattern = re.compile(r'\\addinfo\{scale_id\}\{([^}]+)\}')
    with open(tex_path) as f:
        m = pattern.search(f.read())
    return m.group(1) if m else None


def get_question_vars(tex_path: str) -> dict[str, str]:
    """Return {var: question_text} for every \\question line in a SDAPS .tex file."""
    pattern = re.compile(r'\\question\[.*?var=([^,\]]+).*?\]\{([^}]*)\}', re.DOTALL)
    with open(tex_path) as f:
        return {var.strip(): text.strip() for var, text in pattern.findall(f.read())}


def get_choice_values(tex_path: str) -> dict[int, str]:
    """Return {val: label} for every \\choice[val=N]{...} in a SDAPS .tex file.

    Handles both plain labels (\\choice[val=N]{text}) and parbox-wrapped labels
    (\\choice[val=N]{\\parbox[...]{...}{\\centering text}}).
    """
    with open(tex_path) as f:
        content = f.read()

    result = {}
    # Match \choice[val=N]{...} — capture the numeric value and the raw content
    for m in re.finditer(r'\\choice\[val=(\d+)\]\{((?:[^{}]|\{[^{}]*\})*)\}', content):
        val = int(m.group(1))
        raw = m.group(2).strip()
        # Strip \parbox[opt]{width}{\centering label} wrapper if present
        parbox_m = re.search(r'\\centering\s+([^}]*)', raw)
        label = parbox_m.group(1).strip() if parbox_m else raw
        result[val] = label
    return result


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

print("🚀 Starting SDAPS data extraction...")

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
        if f.lower().endswith((".jpg", ".png", ".pdf"))
    ]

    # 🚨 STOP if no images
    if not images:
        print("⚠️ No images found")
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

    # Get the question variables from the .tex file
    questionnaire_path = os.path.join(project_path, "questionnaire.tex")
    questions = get_question_vars(questionnaire_path)
    questions_keys = questions.keys()
    questionnaire_choices = get_choice_values(questionnaire_path)

    questionnaire_id = get_scale_id(questionnaire_path)
    # Read the latest file
    data_files = glob.glob(os.path.join(project_path, "data_*.csv"))
    latest_file = max(data_files, key=os.path.getctime)
    incoming_data = pd.read_csv(latest_file)

    # Get the valid row and verified rows
    ValidVerifiedRows = ((incoming_data.verified == 1) & (incoming_data.valid == 1))
    # Buid the JSON data
    outData = []
    rowCount = 0
    for row in ValidVerifiedRows:
        if ( row ):
            tempData = {
                "AllResults":
                    {
                        "ScoreName": questionnaire_id,
                        "ShortTitle": questionnaire_id,
                    },
                "NumericResults":
                    {},
                "jatosWorkerID": incoming_data.loc[rowCount,'worker_id'],
                "jatosBatchID": incoming_data.loc[rowCount,'questionnaire_id'],
            }


            outData.append(tempData)
        rowCount += 1

    rowCount = 0
    for row in ValidVerifiedRows:
        if ( row ):

            for j in questions_keys:
                outData[rowCount]['AllResults'][questions[j]] = questionnaire_choices[incoming_data.loc[3,j]]
                outData[rowCount]['NumericResults'][j] = incoming_data.loc[3,j]
        rowCount += 1

    json_array = json.dumps(outData[1], indent=4, default=str)
    print(json_array)
    # =========================
    # How to get the data to a database?
    # =========================
    # Ideally, this should be pushed to a data database instead of trying to squeeze
    # it into the JATOS dB.

    # To get this into the JATOS dB, it also needs to pass through the scoring
    # algorithms in NCM.
    # I would need some script that runs on the JATOS server that listens to incoming data.
    # It then parses what it reads.
    # I think that the tex file needs to have the JATOS Component Name in its meta data
    # along with the questionnaire name.
    # These things need to have the same names as in the JATOS dB.


    # =========================
    # STEP 5: ENCRYPT AND SEND TO JATOS
    # =========================
    print("  🔐 Sending data to JATOS...")

    JATOS_PUBLIX_URL = "http://127.0.0.1:9000/publix/"
    JATOS_STUDY_ID = "w0F1qNBOba0"
    JATOS_QUERY = "?UsageType=DataReceive&Data={encrypted_data}"

    public_key = load_public_key(PUBLIC_KEY_PATH)

    rowCount = 0
    for row in ValidVerifiedRows:
        if (row):
            encrypted_data = encrypt_json(outData[rowCount], public_key)
            url = JATOS_PUBLIX_URL + JATOS_STUDY_ID + JATOS_QUERY.format(encrypted_data=encrypted_data)
            response = requests.get(url)
            print(f"    Row {rowCount}: status {response.status_code}")
        rowCount += 1

    # =========================
    # STEP 6: MOVE IMAGES
    # =========================
    print("  📦 Moving processed images...")
    for img in images:
        shutil.move(
            os.path.join(folder_path, img),
            os.path.join(run_output_dir, img)
        )

    print(f"✅ Done: {folder_name}")

print("\n🎉 Pipeline complete.")
