from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

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
    "EMPLOYEE_ID",
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
    return text.replace("", pd.NA)


def format_timestamp(series: pd.Series) -> pd.Series:
    timestamps = pd.to_datetime(series, errors="coerce")
    formatted = timestamps.dt.strftime("%Y-%m-%dT%H:%M:%S")
    return formatted.where(timestamps.notna(), pd.NA)


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


def fill_all_missing_with_placeholder(df: pd.DataFrame, placeholder: str) -> pd.DataFrame:
    out = df.copy()
    missing_total = int(out.isna().sum().sum())
    if missing_total:
        print(
            f"[INFO] Filling {missing_total:,} remaining missing cell(s) with {placeholder}."
        )

    for column in out.columns:
        missing_mask = out[column].isna()
        if not missing_mask.any():
            continue
        # Nullable numeric dtypes (e.g., Int64/Float64) reject string assignment.
        if pd.api.types.is_numeric_dtype(out[column]) or pd.api.types.is_bool_dtype(
            out[column]
        ):
            out[column] = out[column].astype("object")
        out.loc[missing_mask, column] = placeholder

    return out


def assert_row_count(stage: str, expected_rows: int, actual_rows: int) -> None:
    print(f"[CHECK] {stage}: expected {expected_rows:,}, actual {actual_rows:,}")
    if ENFORCE_ROW_COUNT_MATCH and expected_rows != actual_rows:
        raise ValueError(
            f"Row-count mismatch at {stage}. Expected {expected_rows:,} rows but got "
            f"{actual_rows:,}."
        )


def verify_written_rows(output_path: Path, delimiter: str, expected_rows: int) -> None:
    written = pd.read_csv(
        output_path,
        sep=delimiter,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )
    assert_row_count("Written file rows", expected_rows, len(written))


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

    completion_source = get_first_present_column(df, SOURCE_CANDIDATES["COMPLETION_DATE"])
    completed_mask = completion_source.notna() & completion_source.astype(str).str.strip().ne(
        ""
    )
    out["STATUS"] = completed_mask.map({True: "COMPLETED", False: "STARTED"})
    out["COMPLETION_DATE"] = format_timestamp(completion_source)

    out["DURATION_HOURS"] = (
        pd.to_numeric(
            get_first_present_column(df, SOURCE_CANDIDATES["DURATION_MINUTES"]),
            errors="coerce",
        )
        / 60
    )

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


def build_output_filename(customer_name: str) -> str:
    date_part = datetime.now().strftime("%Y%m%d")
    clean_customer = customer_name.strip().upper()
    return f"{clean_customer}_ATTENDANCE_DATA_IMPORT_{date_part}.csv"


def main() -> None:
    print(f"[INFO] Reading source file: {FILE_PATH}")
    source = pd.read_csv(FILE_PATH, low_memory=False)
    input_rows = len(source)
    print(f"[INFO] Source rows: {input_rows:,}")

    attendance = convert_to_attendance(source)
    attendance = normalize_empty_values(attendance)
    attendance = fill_required_with_placeholder(
        attendance, REQUIRED_COLUMNS, NULL_PLACEHOLDER
    )
    attendance = fill_all_missing_with_placeholder(attendance, NULL_PLACEHOLDER)

    transformed_rows = len(attendance)
    assert_row_count("Transformed rows", input_rows, transformed_rows)

    output_name = build_output_filename(CUSTOMER_NAME)
    output_path = OUTPUT_DIR / output_name
    delimiter = delimiter_for_format(FILE_FORMAT)

    attendance.to_csv(
        output_path,
        sep=delimiter,
        index=False,
        encoding="utf-8",
    )

    if VERIFY_WRITTEN_ROW_COUNT:
        verify_written_rows(output_path, delimiter, transformed_rows)

    print(f"[DONE] Wrote attendance import: {output_path}")
    print(f"[DONE] Rows: {transformed_rows:,}")
    print(f"[DONE] Columns: {attendance.columns.tolist()}")


if __name__ == "__main__":
    main()
