import os
import sys
import webbrowser
import pandas as pd
import sqlite3
import json
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify
)
from db import load_csv_to_sqlite, load_aircraft_csv_to_sqlite
from build_full_org_tree import build_full_org_tree

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-random-key"

BASE_DIR     = os.path.dirname(__file__)
UPLOAD_FOLDER= os.path.join(BASE_DIR, "uploads")
DATA_FOLDER  = os.path.join(BASE_DIR, "data")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    file = request.files.get("csv_file")
    if not file or not file.filename:
        flash("No CSV file selected", "error")
        return redirect(url_for("index"))
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    db_path = os.path.join(DATA_FOLDER, "data.db")
    try:
        load_csv_to_sqlite(path, db_file=db_path, table_name="organization")
        flash("Org CSV loaded into database", "success")
    except Exception as e:
        flash(f"Error loading org CSV: {e}", "error")
    return redirect(url_for("index"))

@app.route("/upload_aircraft", methods=["POST"])
def upload_aircraft():
    file = request.files.get("aircraft_file")
    if not file or not file.filename:
        flash("No aircraft CSV selected", "error")
        return redirect(url_for("index"))
    path = os.path.join(DATA_FOLDER, "aircraft_filtered.csv")
    file.save(path)
    db_path = os.path.join(DATA_FOLDER, "data.db")
    try:
        load_aircraft_csv_to_sqlite(path, db_file=db_path, table_name="aircraft")
        flash("Aircraft CSV loaded into database", "success")
    except Exception as e:
        flash(f"Error loading aircraft CSV: {e}", "error")
    return redirect(url_for("index"))

@app.route("/build_json", methods=["POST"])
def build_json():
    db_path   = os.path.join(DATA_FOLDER, "data.db")
    json_path = os.path.join(DATA_FOLDER, "full_org_tree.json")
    if not os.path.exists(db_path):
        flash("Database not found. Upload org CSV first.", "error")
        return redirect(url_for("index"))
    try:
        build_full_org_tree(
            db_file=db_path,
            table_name="organization",
            output_file=json_path
        )
        flash("Org tree JSON built", "success")
    except Exception as e:
        flash(f"Error building JSON: {e}", "error")
    return redirect(url_for("index"))

@app.route("/tree")
def tree():
    return render_template("tree.html")

@app.route("/data/tree.json")
def data_tree():
    json_path = os.path.join(DATA_FOLDER, "full_org_tree.json")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

@app.route("/api/aircraft")
def api_aircraft():
    # Accept either pas_list or single pas
    pas_list = []
    if 'pas_list' in request.args:
        try:
            pas_list = json.loads(request.args.get('pas_list') or "[]")
        except:
            pas_list = []
    else:
        p = request.args.get('pas','').strip()
        if p:
            pas_list = [p]

    if not pas_list:
        return jsonify([])

    db_path = os.path.join(DATA_FOLDER, "data.db")
    conn = sqlite3.connect(db_path)
    placeholders = ",".join("?" for _ in pas_list)
    sql = f"""
      SELECT
        aircraft_serial_number,
        aircraft_tail_number,
        mission_design_series,
        current_assigned_base,
        active_inventory,
        current_condition_detail,
        assigned_unit_pas,
        flights,
        landings,
        flight_time_mins
      FROM aircraft
      WHERE assigned_unit_pas IN ({placeholders})
    """
    cur = conn.execute(sql, pas_list)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/fmc_stats")
def api_fmc_stats():
    db_path = os.path.join(DATA_FOLDER, "data.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM aircraft
        WHERE UPPER(active_inventory) = 'Y'
          AND UPPER(current_condition_detail) = 'FMC'
    """)
    fmc_count = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(*) FROM aircraft
        WHERE UPPER(active_inventory) = 'Y'
          AND UPPER(current_condition_detail) != 'FMC'
    """)
    non_fmc_count = cur.fetchone()[0]
    conn.close()
    return jsonify({"fmc": fmc_count, "non_fmc": non_fmc_count})

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--open":
        webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True)
