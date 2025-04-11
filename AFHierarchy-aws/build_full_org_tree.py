import sys
import os
import sqlite3
import pandas as pd
import json
import re

# 1) Define grouping patterns: regex → group label
GROUP_PATTERNS = {
    r'AFELM.*DOD': 'AFELM DOD',
    r'U S Air Force Headquarters': 'USAF HQ',
    r'Department of Defense': 'DoD',
    # Add more patterns here...
}

def apply_grouping(name):
    """
    Map an organization_name to a grouped label if it matches any pattern,
    otherwise return the original name.
    """
    for pattern, label in GROUP_PATTERNS.items():
        if re.search(pattern, name, re.IGNORECASE):
            return label
    return name

def load_valid_pas_set(data_folder="data"):
    """
    Read aircraft_filtered.csv and collect all PAS codes that appear
    in assigned_unit_pas or in assigned_unit_hierarchy lists.
    """
    path = os.path.join(data_folder, "aircraft_filtered.csv")
    if not os.path.exists(path):
        return set()
    df = pd.read_csv(path, low_memory=False)
    valid = set()

    for _, row in df.iterrows():
        pas = str(row.get("assigned_unit_pas","")).strip()
        if pas:
            valid.add(pas)
        uh = str(row.get("assigned_unit_hierarchy","")).strip()
        parts = [p.strip() for p in uh.strip("[]").split(",") if p.strip()]
        valid.update(parts)
    return valid

def prune_by_aircraft(node, valid_pas):
    """
    Recursively prune node if neither its PAS nor any descendant PAS
    is in valid_pas. Returns True if node should be kept.
    """
    keep_children = []
    for child in node.get("Children", []):
        if prune_by_aircraft(child, valid_pas):
            keep_children.append(child)
    node["Children"] = keep_children

    # Keep this node if its PAS is valid or it has any kept children
    return (node["PAS"] in valid_pas) or bool(keep_children)

def build_tree_structure(df):
    """
    Build the raw PAS → parent_pas tree, force FR3R as root,
    and assign each node a label "<organization_no> - <grouped_name>".
    """
    # Apply grouping to organization_name
    df['grouped_name'] = df['organization_name'].astype(str).apply(apply_grouping)

    # Build a map pas → node
    node_map = {}
    for _, row in df.iterrows():
        pas           = str(row['pas']).strip()
        parent_pas    = str(row['parent_pas']).strip() if pd.notnull(row['parent_pas']) else ""
        org_no        = str(row['organization_no']).strip()
        org_label     = row['grouped_name']
        unit          = row['unit']
        label         = f"{org_no} - {unit}"
        node_map[pas] = {
            "PAS": pas,
            "label": label,
            "parent_pas": parent_pas,
            "Children": []
        }

    # Link children to parents
    for pas, node in node_map.items():
        parent = node["parent_pas"]
        if parent in node_map and pas != 'FHCC':
            node_map[parent]["Children"].append(node)

    # Force root to be FR3R
    if 'FHCC' not in node_map:
        raise KeyError("PAS 'FHCC' not found; cannot set DoD as root.")
    return node_map['FHCC']

def build_full_org_tree(db_file="data.db", table_name="organization", output_file="full_org_tree.json"):
    """
    Load data from SQLite, filter masked rows, build & prune the tree
    based on aircraft assignments, and write the JSON.
    """
    # Load org data
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query(f"""
        SELECT pas, parent_pas, organization_no, unit, organization_name
        FROM {table_name}
    """, conn)
    conn.close()

    # Filter out masked rows
    df = df[~df['organization_name'].str.contains("Data Masked", case=False, na=False)]

    # Build full tree with new labels
    root = build_tree_structure(df)

    # Load valid PAS set from aircraft data
    valid_pas = load_valid_pas_set(data_folder=os.path.dirname(db_file))

    # Prune nodes without any aircraft
    prune_by_aircraft(root, valid_pas)

    # Write JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(root, f, indent=2)
    print(f"Pruned & relabeled org tree saved to {output_file}")

def main():
    db_file = sys.argv[1] if len(sys.argv) > 1 else "data.db"
    build_full_org_tree(db_file=db_file)

if __name__ == "__main__":
    main()
