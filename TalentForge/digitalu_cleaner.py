from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from html import unescape

import pandas as pd

# -----------------------------
# CONFIG
# -----------------------------
FILE_PATH = Path("digital_U/Digital U_USAF Completion Data.csv")
CUSTOMER_NAME = "CUSTOMERNAME"  # Update before running
FILE_FORMAT = "CSV"  # Supported: CSV or PIPE

NULL_PLACEHOLDER = "N/A"
ENFORCE_ROW_COUNT_MATCH = True
VERIFY_WRITTEN_ROW_COUNT = True
MAX_ROWS_PER_FILE = 26_995

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "exports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_COLUMNS = [
    "EMPLOYEE_ID",
    "COURSE_ID",
    "COURSE_TITLE",
    "COURSE_URL",
    "COURSE_DESCRIPTION",
    "PROVIDER",
    "STATUS",
    "COMPLETION_DATE",
    "DURATION_HOURS",
]

REQUIRED_COLUMNS = [
    "COURSE_ID",
    "STATUS",
]

SOURCE_CANDIDATES = {
    "EMPLOYEE_ID": ["Users - Dod Id", "EMPLOYEE_ID"],
    "COURSE_ID": ["Courses - Vendor Course Id", "COURSE_ID"],
    "COURSE_TITLE": ["Courses - Title", "COURSE_TITLE"],
    "COURSE_URL": ["Courses - Url", "Courses - URL", "Courses - Link", "COURSE_URL"],
    "COURSE_DESCRIPTION": ["Courses - Description", "COURSE_DESCRIPTION"],
    "PROVIDER": ["Courses - Vendor Name", "Courses - Vendor Id", "PROVIDER"],
    "COMPLETION_DATE": [
        "Transcript Courses - Completed At",
        "COMPLETION_DATE",
    ],
    "STARTED_AT": [
        "Transcript Courses - Started At",
        "Transcript Courses - StartedAt",
        "Transcript Courses - Started",
        "STARTED_AT",
    ],
    "STOPPED_AT": [
        "Transcript Courses - Stopped At",
        "Transcript Courses - StoppedAt",
        "Transcript Courses - Stopped",
        "STOPPED_AT",
    ],
    "DURATION_MINUTES": ["Courses - Duration In Minutes", "DURATION_MINUTES"],
}

_HTML_RE = re.compile(r"<[^>]+>")


def get_first_present_column(
    df: pd.DataFrame,
    candidates: list[str],
    default: object = pd.NA,
) -> pd.Series:
    for column in candidates:
        if column in df.columns:
            return df[column]
    return pd.Series([default] * len(df), index=df.index, dtype="object")


def strip_html(series: pd.Series) -> pd.Series:
    text = series.fillna("").astype(str)
    text = text.str.replace(_HTML_RE, "", regex=True)
    text = text.str.replace(r"\s+", " ", regex=True).str.strip()
    # Unescape HTML entities (e.g. &rsquo;, &#8217;)
    text = text.map(lambda s: unescape(s) if s and isinstance(s, str) else s)
    return text.replace("", pd.NA)


def format_timestamp(series: pd.Series) -> pd.Series:
    s = series.fillna("").astype(str).str.strip()

    # Try parsing numeric unix epoch seconds first (common in some dumps)
    is_unix = s.str.match(r"^\d{9,}$")
    parsed = pd.Series(pd.NaT, index=s.index)
    if is_unix.any():
        try:
            parsed.loc[is_unix] = pd.to_datetime(s[is_unix].astype('int64'), unit='s', errors='coerce')
        except Exception:
            parsed.loc[is_unix] = pd.to_datetime(s[is_unix], errors='coerce')

    # Parse remaining values with flexible parser
    remaining = ~is_unix
    if remaining.any():
        parsed.loc[remaining] = pd.to_datetime(s[remaining], errors='coerce')

    formatted = parsed.dt.strftime("%Y-%m-%dT%H:%M:%S")
    return formatted.where(parsed.notna(), pd.NA)


def parse_duration_minutes(series: pd.Series) -> pd.Series:
    """Return duration in minutes (float). Handles numeric minutes or mm:ss / hh:mm:ss strings."""
    def _parse(val):
        if pd.isna(val):
            return pd.NA
        s = str(val).strip()
        if s == "":
            return pd.NA
        # If already numeric (minutes)
        try:
            return float(s)
        except Exception:
            pass

        # mm:ss or hh:mm:ss
        if ":" in s:
            parts = [p for p in s.split(":") if p != ""]
            try:
                parts = [float(p) for p in parts]
            except Exception:
                return pd.NA
            # seconds only last part
            if len(parts) == 2:
                minutes, seconds = parts
                return minutes + seconds / 60.0
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return hours * 60.0 + minutes + seconds / 60.0
        return pd.NA

    return series.map(_parse)


def normalize_empty_values(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in out.columns:
        if pd.api.types.is_object_dtype(out[column]) or pd.api.types.is_string_dtype(
            out[column]
        ):
            as_text = out[column].astype("string").str.strip()
            out[column] = as_text.replace("", pd.NA)
    return out


def fill_required_with_placeholder(
    df: pd.DataFrame,
    required_columns: list[str],
    placeholder: str,
) -> pd.DataFrame:
    out = df.copy()
    for column in required_columns:
        missing_mask = out[column].isna() | out[column].astype(str).str.strip().eq("")
        missing_count = int(missing_mask.sum())
        if missing_count:
            print(
                f"[WARN] Column {column} had {missing_count:,} missing value(s); "
                f"filled with {placeholder}."
            )
            out.loc[missing_mask, column] = placeholder
    return out


def drop_rows_missing_employee_id(df: pd.DataFrame) -> pd.DataFrame:
    missing_mask = df["EMPLOYEE_ID"].isna() | df["EMPLOYEE_ID"].astype(str).str.strip().eq("")
    missing_count = int(missing_mask.sum())
    if missing_count:
        print(
            f"[INFO] Dropping {missing_count:,} row(s) with missing EMPLOYEE_ID/DODID."
        )
        return df.loc[~missing_mask].copy()
    return df


def assert_row_count(stage: str, expected_rows: int, actual_rows: int) -> None:
    print(f"[CHECK] {stage}: expected {expected_rows:,}, actual {actual_rows:,}")
    if ENFORCE_ROW_COUNT_MATCH and expected_rows != actual_rows:
        raise ValueError(
            f"Row-count mismatch at {stage}. Expected {expected_rows:,} rows but got "
            f"{actual_rows:,}."
        )


def verify_written_rows(
    output_paths: list[Path],
    delimiter: str,
    expected_rows: int,
    max_rows_per_file: int,
) -> None:
    total_written = 0
    for output_path in output_paths:
        written = pd.read_csv(
            output_path,
            sep=delimiter,
            dtype=str,
            keep_default_na=False,
            low_memory=False,
        )
        rows_in_file = len(written)
        if rows_in_file > max_rows_per_file:
            raise ValueError(
                f"Batch file {output_path.name} has {rows_in_file:,} rows, which exceeds "
                f"the configured limit of {max_rows_per_file:,}."
            )
        total_written += rows_in_file

    assert_row_count("Written file rows (all batches)", expected_rows, total_written)


def convert_to_attendance(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)

    out["EMPLOYEE_ID"] = get_first_present_column(df, SOURCE_CANDIDATES["EMPLOYEE_ID"])
    out["COURSE_ID"] = get_first_present_column(df, SOURCE_CANDIDATES["COURSE_ID"])
    out["COURSE_TITLE"] = get_first_present_column(df, SOURCE_CANDIDATES["COURSE_TITLE"])
    out["COURSE_URL"] = get_first_present_column(
        df,
        SOURCE_CANDIDATES["COURSE_URL"],
        default="https://digitalu.af.mil/",
    )
    out["COURSE_DESCRIPTION"] = strip_html(
        get_first_present_column(df, SOURCE_CANDIDATES["COURSE_DESCRIPTION"])
    )
    out["PROVIDER"] = get_first_present_column(df, SOURCE_CANDIDATES["PROVIDER"])

    # Timestamps: prefer explicit completion, otherwise stopped, otherwise blank.
    completion_source = get_first_present_column(df, SOURCE_CANDIDATES["COMPLETION_DATE"])
    started_source = get_first_present_column(df, SOURCE_CANDIDATES["STARTED_AT"])
    stopped_source = get_first_present_column(df, SOURCE_CANDIDATES["STOPPED_AT"])

    chosen_completion = completion_source.fillna("")
    fallback_mask = chosen_completion.astype(str).str.strip().eq("")
    chosen_completion.loc[fallback_mask] = stopped_source.loc[fallback_mask].fillna("")

    completed_mask = chosen_completion.astype(str).str.strip().ne("")
    out["STATUS"] = completed_mask.map({True: "COMPLETED", False: "STARTED"})
    out["COMPLETION_DATE"] = format_timestamp(chosen_completion)

    duration_raw = get_first_present_column(df, SOURCE_CANDIDATES["DURATION_MINUTES"])
    duration_minutes = parse_duration_minutes(duration_raw)
    out["DURATION_HOURS"] = pd.to_numeric(duration_minutes, errors="coerce") / 60

    for column in TARGET_COLUMNS:
        if column not in out.columns:
            out[column] = pd.NA

    return out[TARGET_COLUMNS]


def delimiter_for_format(file_format: str) -> str:
    normalized = file_format.strip().upper()
    if normalized == "CSV":
        return ","
    if normalized == "PIPE":
        return "|"
    raise ValueError("FILE_FORMAT must be either 'CSV' or 'PIPE'.")


def build_output_stem(customer_name: str) -> str:
    date_part = datetime.now().strftime("%Y%m%d")
    clean_customer = customer_name.strip().upper()
    return f"{clean_customer}_ATTENDANCE_DATA_IMPORT_{date_part}"


def write_batched_output(
    df: pd.DataFrame,
    output_stem: str,
    output_dir: Path,
    delimiter: str,
    max_rows_per_file: int,
) -> list[Path]:
    output_paths: list[Path] = []
    total_rows = len(df)
    total_batches = max(1, (total_rows + max_rows_per_file - 1) // max_rows_per_file)

    for batch_index in range(total_batches):
        start_row = batch_index * max_rows_per_file
        end_row = start_row + max_rows_per_file
        batch = df.iloc[start_row:end_row]

        if total_batches == 1:
            filename = f"{output_stem}.csv"
        else:
            filename = f"{output_stem}_PART_{batch_index + 1:03d}.csv"

        output_path = output_dir / filename
        batch.to_csv(
            output_path,
            sep=delimiter,
            index=False,
            encoding="utf-8",
        )

        rows_in_batch = len(batch)
        if rows_in_batch > max_rows_per_file:
            raise ValueError(
                f"Batch file {filename} has {rows_in_batch:,} rows, which exceeds "
                f"{max_rows_per_file:,}."
            )

        output_paths.append(output_path)
        print(f"[DONE] Wrote batch {batch_index + 1}/{total_batches}: {output_path}")
        print(f"[DONE] Batch rows: {rows_in_batch:,}")

    return output_paths


def main() -> None:
    print(f"[INFO] Reading source file: {FILE_PATH}")
    source = pd.read_csv(FILE_PATH, low_memory=False)
    input_rows = len(source)
    print(f"[INFO] Source rows: {input_rows:,}")

    attendance = convert_to_attendance(source)
    attendance = normalize_empty_values(attendance)
    attendance = drop_rows_missing_employee_id(attendance)
    attendance = fill_required_with_placeholder(
        attendance, REQUIRED_COLUMNS, NULL_PLACEHOLDER
    )

    transformed_rows = len(attendance)
    dropped_rows = input_rows - transformed_rows
    print(f"[INFO] Transformed rows: {transformed_rows:,}")
    print(f"[INFO] Dropped rows missing EMPLOYEE_ID/DODID: {dropped_rows:,}")

    output_stem = build_output_stem(CUSTOMER_NAME)
    delimiter = delimiter_for_format(FILE_FORMAT)

    output_paths = write_batched_output(
        attendance,
        output_stem=output_stem,
        output_dir=OUTPUT_DIR,
        delimiter=delimiter,
        max_rows_per_file=MAX_ROWS_PER_FILE,
    )

    if VERIFY_WRITTEN_ROW_COUNT:
        verify_written_rows(
            output_paths,
            delimiter=delimiter,
            expected_rows=transformed_rows,
            max_rows_per_file=MAX_ROWS_PER_FILE,
        )

    print(f"[DONE] Wrote attendance import files: {len(output_paths)}")
    print(f"[DONE] Rows: {transformed_rows:,}")
    print(f"[DONE] Columns: {attendance.columns.tolist()}")


if __name__ == "__main__":
    main()
