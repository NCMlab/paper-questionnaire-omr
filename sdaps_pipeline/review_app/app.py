import glob
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import time
from datetime import datetime

from flask import Flask, flash, redirect, render_template, url_for

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
CSV_OUTPUTS_DIR = os.path.join(BASE_DIR, "csv_outputs")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

# Use the patched sdaps checkout (adds OCR-training capture/export support)
# rather than the system-wide "sdaps" (an unpatched v1.9.13 install). Must be
# the system python3, not this app's venv -- "sdaps gui" needs PyGObject
# (gi), which is a system/dist-packages module not present in the venv.
SDAPS = ["/usr/bin/python3", os.path.expanduser("~/PaperQuestionnaires/sdaps/sdaps.py")]
BROADWAY_DISPLAY = ":5"

app = Flask(__name__)
app.secret_key = os.environ.get("SDAPS_REVIEW_SECRET", os.urandom(24))


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return None


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


def is_pid_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def active_session():
    """Return the active review session, dropping stale state if the
    underlying "sdaps gui" process is no longer running."""
    state = load_state()
    if state and is_pid_alive(state["pid"]):
        return state
    if state:
        clear_state()
    return None


def sheet_counts(project_path):
    """Count sheets and unverified sheets, mirroring Sheet.verified
    (sdaps/model/sheet.py): a sheet is verified if every non-ignored image
    has been marked verified in the GUI."""
    db_path = os.path.join(project_path, "survey.sqlite")
    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    try:
        rows = conn.execute("SELECT json FROM sheets").fetchall()
    finally:
        conn.close()

    total = len(rows)
    unverified = 0
    for (raw,) in rows:
        sheet = json.loads(raw)
        images = sheet.get("images", [])
        verified = all(
            img.get("verified") for img in images if not img.get("ignored")
        )
        if not verified:
            unverified += 1

    return {"total": total, "unverified": unverified}


def last_export(project):
    out_dir = os.path.join(CSV_OUTPUTS_DIR, project)
    if not os.path.isdir(out_dir):
        return None
    runs = sorted(os.listdir(out_dir), reverse=True)
    return runs[0] if runs else None


def list_projects():
    projects = []
    if not os.path.isdir(PROJECTS_DIR):
        return projects

    for name in sorted(os.listdir(PROJECTS_DIR)):
        path = os.path.join(PROJECTS_DIR, name)
        counts = sheet_counts(path)
        if counts is None:
            continue
        projects.append({
            "name": name,
            "total": counts["total"],
            "unverified": counts["unverified"],
            "last_export": last_export(name),
        })

    return projects


@app.route("/")
def dashboard():
    return render_template(
        "dashboard.html", projects=list_projects(), session=active_session())


@app.route("/review/<project>/start", methods=["POST"])
def start_review(project):
    project_path = os.path.join(PROJECTS_DIR, project)
    if not os.path.isdir(project_path):
        flash("Unknown project: %s" % project)
        return redirect(url_for("dashboard"))

    session = active_session()
    if session and session["project"] != project:
        flash('"%s" is currently being reviewed. Finish that session first.'
              % session["project"])
        return redirect(url_for("dashboard"))

    if not session:
        env = dict(os.environ)
        env["GDK_BACKEND"] = "broadway"
        env["BROADWAY_DISPLAY"] = BROADWAY_DISPLAY
        proc = subprocess.Popen(SDAPS + ["gui", project_path], env=env)
        save_state({
            "project": project,
            "pid": proc.pid,
            "started_at": datetime.now().isoformat(),
        })

    return redirect(url_for("review", project=project))


@app.route("/review/<project>")
def review(project):
    session = active_session()
    if not session or session["project"] != project:
        flash('No active review session for "%s". Start one from the '
              'dashboard.' % project)
        return redirect(url_for("dashboard"))

    return render_template("review.html", project=project)


@app.route("/review/<project>/finish", methods=["POST"])
def finish_review(project):
    session = active_session()
    if session and session["project"] == project:
        pid = session["pid"]
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass

        for _ in range(20):
            if not is_pid_alive(pid):
                break
            time.sleep(0.5)
        else:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass

        clear_state()

    project_path = os.path.join(PROJECTS_DIR, project)

    subprocess.run(SDAPS + ["export", "csv", project_path], check=False)
    subprocess.run(
        SDAPS + ["export", "ocr-training", "-f", "verified", project_path],
        check=False)

    data_files = glob.glob(os.path.join(project_path, "data_*.csv"))
    if data_files:
        latest = max(data_files, key=os.path.getmtime)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join(CSV_OUTPUTS_DIR, project, timestamp)
        os.makedirs(out_dir, exist_ok=True)
        shutil.copy(latest, os.path.join(out_dir, "%s.csv" % project))

    flash('Finished reviewing "%s" — exported CSV and OCR training data.'
          % project)
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8086, debug=False)
