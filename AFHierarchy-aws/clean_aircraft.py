#!/usr/bin/env python3
import sys
import pandas as pd

# Columns to keep
KEEP_COLS = [
    "aircraft_serial_number",
    "aircraft_tail_number",
    "mission_design_series",
    "current_assigned_base",
    "location",
    "current_condition_detail",
    "discrepancy_lines",
    "g081_current_condition_summary",
    "assigned_unit_pas",
    "assigned_unit_hierarchy",
    "g081_total_landings",
    "g081_total_flights",
    "g081_current_aircraft_status",
    "assigned_organization_no",
    "g081_last_landing_geohash",
    "g081_current_condition_detail",
    "work_unit_code",
    "wuc_desc"
]

def main():
    if len(sys.argv) != 2:
        print("Usage: python clean_aircraft.py <path_to_aircraft_csv>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = "aircraft_filtered.csv"

    # Load full CSV
    try:
        df = pd.read_csv(input_csv, low_memory=False)
    except Exception as e:
        print(f"Error reading '{input_csv}': {e}")
        sys.exit(1)

    # Check for missing columns
    missing = [c for c in KEEP_COLS if c not in df.columns]
    if missing:
        print("Warning: the following columns were not found in the input and will be filled with NaN:")
        for c in missing:
            print("  ", c)
        # Add them as empty columns so selection won't fail
        for c in missing:
            df[c] = pd.NA

    # Select only the columns we care about
    df_filtered = df[KEEP_COLS]

    # Write out the slimmed CSV
    try:
        df_filtered.to_csv(output_csv, index=False)
        print(f"Written {len(df_filtered)} rows × {len(KEEP_COLS)} columns to '{output_csv}'")
    except Exception as e:
        print(f"Error writing '{output_csv}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
