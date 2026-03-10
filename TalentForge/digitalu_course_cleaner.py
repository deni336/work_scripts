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
PROVIDER_NAME = "DigitalU"  # Set to None to use provider from source columns

NULL_PLACEHOLDER = "N/A"
ENFORCE_ROW_COUNT_MATCH = True
VERIFY_WRITTEN_ROW_COUNT = True

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "exports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# COURSE CATALOG SCHEMA
# -----------------------------
TARGET_COLUMNS = [
    "COURSE_ID",
    "COURSE_TITLE",
    "COURSE_DESCRIPTION",
    "COURSE_URL",
    "DURATION_HOURS",
    "CATEGORY",
    "COURSE_TYPE",
    "LANGUAGE",
    "DIFFICULTY",
    "STATUS",
    "IMAGE_URL",
    "SKILL",
    "PROVIDER",
    "LOCATION",
    "FEE_VALUE",
    "SENIORITY_LIST",
    "BUSINESS_UNIT_LIST",
    "RATING",
    "RATING_COUNT",
    "JOB_FUNCTION_LIST",
    "JOB_CODE_LIST",
    "SKILL_PROFICIENCY_LIST",
    "FEE_CURRENCY",
    "PUBLISHED_TS",
]

REQUIRED_COLUMNS = [
    "COURSE_ID",
    "COURSE_TITLE",
    "COURSE_DESCRIPTION",
    "COURSE_URL",
    "STATUS",
    "PROVIDER",
]

SOURCE_CANDIDATES = {
    "COURSE_ID": ["Courses - Vendor Course Id", "COURSE_ID"],
    "COURSE_TITLE": ["Courses - Title", "COURSE_TITLE"],
    "COURSE_DESCRIPTION": ["Courses - Description", "COURSE_DESCRIPTION"],
    "COURSE_URL": ["Courses - Url", "Courses - URL", "Courses - Link", "COURSE_URL"],
    "DURATION_MINUTES": ["Courses - Duration In Minutes", "DURATION_MINUTES"],
    "CATEGORY": ["Courses - Category", "CATEGORY"],
    "COURSE_TYPE": ["Courses - Type", "Courses - Course Type", "COURSE_TYPE"],
    "LANGUAGE": ["Courses - Language", "LANGUAGE"],
    "DIFFICULTY": ["Courses - Difficulty", "DIFFICULTY"],
    "STATUS": ["Courses - Status", "STATUS"],
    "IMAGE_URL": ["Courses - Image Url", "Courses - Image URL", "IMAGE_URL"],
    "SKILL": ["Courses - Skills", "Courses - Skill", "SKILL"],
    "PROVIDER": ["Courses - Vendor Name", "Courses - Vendor Id", "PROVIDER"],
    "LOCATION": ["Courses - Location", "LOCATION"],
    "FEE_VALUE": ["Courses - Fee", "FEE_VALUE"],
    "SENIORITY_LIST": ["Courses - Seniority List", "SENIORITY_LIST"],
    "BUSINESS_UNIT_LIST": ["Courses - Business Unit List", "BUSINESS_UNIT_LIST"],
    "RATING": ["Courses - Rating", "RATING"],
    "RATING_COUNT": ["Courses - Rating Count", "RATING_COUNT"],
    "JOB_FUNCTION_LIST": ["Courses - Job Function List", "JOB_FUNCTION_LIST"],
    "JOB_CODE_LIST": ["Courses - Job Code List", "JOB_CODE_LIST"],
    "SKILL_PROFICIENCY_LIST": [
        "Courses - Skill Proficiency List",
        "SKILL_PROFICIENCY_LIST",
    ],
    "FEE_CURRENCY": ["Courses - Fee Currency", "FEE_CURRENCY"],
    "PUBLISHED_TS": [
        "Courses - Published At",
        "Courses - Published Timestamp",
        "Courses - Publish Date",
        "PUBLISHED_TS",
    ],
}

_HTML_RE = re.compile(r"<[^>]+>")


def get_first_present_column(
    df: pd.DataFrame,
    candidates: list[str],
    default: object = pd.NA,
) -> pd.Series:
    """Return the first matching source column or a default series."""
    for column in candidates:
        if column in df.columns:
            return df[column]
    return pd.Series([default] * len(df), index=df.index, dtype="object")


def strip_html(series: pd.Series) -> pd.Series:
    """Remove HTML tags and collapse whitespace."""
    text = series.fillna("").astype(str)
    text = text.str.replace(_HTML_RE, "", regex=True)
    text = text.str.replace(r"\s+", " ", regex=True).str.strip()
    return text.replace("", pd.NA)


def normalize_status(series: pd.Series) -> pd.Series:
    """Normalize to course catalog status values."""
    status = series.fillna("").astype(str).str.strip().str.upper()
    status = status.replace(
        {
            "": pd.NA,
            "COMPLETED": "ACTIVE",
            "STARTED": "ACTIVE",
            "LIVE": "ACTIVE",
            "PUBLISHED": "ACTIVE",
            "ENABLED": "ACTIVE",
            "DISABLED": "INACTIVE",
            "ARCHIVE": "INACTIVE",
        }
    )
    return status


def normalize_list(
    series: pd.Series,
    output_delimiter: str,
    split_pattern: str = r"[|,;]",
) -> pd.Series:
    """Normalize multi-value text into delimiter-separated list values."""
    normalized: list[object] = []

    for value in series.fillna("").astype(str):
        tokens: list[str] = []
        for token in re.split(split_pattern, value):
            cleaned = token.strip()
            if cleaned and cleaned not in tokens:
                tokens.append(cleaned)
        normalized.append(output_delimiter.join(tokens) if tokens else pd.NA)

    return pd.Series(normalized, index=series.index, dtype="object")


def format_timestamp(series: pd.Series) -> pd.Series:
    """Format timestamps as YYYY-MM-DDTHH:MM:SS."""
    timestamps = pd.to_datetime(series, errors="coerce")
    formatted = timestamps.dt.strftime("%Y-%m-%dT%H:%M:%S")
    return formatted.where(timestamps.notna(), pd.NA)


def normalize_empty_values(df: pd.DataFrame) -> pd.DataFrame:
    """Convert empty strings and whitespace-only values to NA."""
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
    """Ensure required fields are present by filling gaps with placeholder."""
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
    return out.fillna(placeholder)


def assert_row_count(stage: str, expected_rows: int, actual_rows: int) -> None:
    print(f"[CHECK] {stage}: expected {expected_rows:,}, actual {actual_rows:,}")
    if ENFORCE_ROW_COUNT_MATCH and expected_rows != actual_rows:
        raise ValueError(
            f"Row-count mismatch at {stage}. Expected {expected_rows:,} rows but got "
            f"{actual_rows:,}."
        )


def verify_written_rows(output_path: Path, delimiter: str, expected_rows: int) -> None:
    """Re-read output file to guarantee row count written to disk."""
    written = pd.read_csv(
        output_path,
        sep=delimiter,
        dtype=str,
        keep_default_na=False,
        low_memory=False,
    )
    assert_row_count("Written file rows", expected_rows, len(written))


def convert_to_course_catalog(df: pd.DataFrame) -> pd.DataFrame:
    """Build course-catalog rows from transcript-style source data."""
    out = pd.DataFrame(index=df.index)

    out["COURSE_ID"] = get_first_present_column(df, SOURCE_CANDIDATES["COURSE_ID"])
    out["COURSE_TITLE"] = get_first_present_column(df, SOURCE_CANDIDATES["COURSE_TITLE"])
    out["COURSE_DESCRIPTION"] = strip_html(
        get_first_present_column(df, SOURCE_CANDIDATES["COURSE_DESCRIPTION"])
    )
    out["COURSE_URL"] = get_first_present_column(
        df,
        SOURCE_CANDIDATES["COURSE_URL"],
        default="https://digitalu.af.mil/",
    )
    out["DURATION_HOURS"] = (
        pd.to_numeric(
            get_first_present_column(df, SOURCE_CANDIDATES["DURATION_MINUTES"]),
            errors="coerce",
        )
        / 60
    )
    out["CATEGORY"] = get_first_present_column(df, SOURCE_CANDIDATES["CATEGORY"])
    out["COURSE_TYPE"] = get_first_present_column(df, SOURCE_CANDIDATES["COURSE_TYPE"])
    out["LANGUAGE"] = get_first_present_column(df, SOURCE_CANDIDATES["LANGUAGE"])
    out["DIFFICULTY"] = get_first_present_column(df, SOURCE_CANDIDATES["DIFFICULTY"])
    out["STATUS"] = normalize_status(
        get_first_present_column(df, SOURCE_CANDIDATES["STATUS"], default="ACTIVE")
    )
    out["IMAGE_URL"] = get_first_present_column(df, SOURCE_CANDIDATES["IMAGE_URL"])
    out["SKILL"] = normalize_list(
        get_first_present_column(df, SOURCE_CANDIDATES["SKILL"]),
        output_delimiter="|",
    )

    if PROVIDER_NAME is None or not str(PROVIDER_NAME).strip():
        out["PROVIDER"] = get_first_present_column(df, SOURCE_CANDIDATES["PROVIDER"])
    else:
        out["PROVIDER"] = str(PROVIDER_NAME).strip()

    out["LOCATION"] = get_first_present_column(df, SOURCE_CANDIDATES["LOCATION"])
    out["FEE_VALUE"] = pd.to_numeric(
        get_first_present_column(df, SOURCE_CANDIDATES["FEE_VALUE"]),
        errors="coerce",
    )
    out["SENIORITY_LIST"] = normalize_list(
        get_first_present_column(df, SOURCE_CANDIDATES["SENIORITY_LIST"]),
        output_delimiter=",",
    )
    out["BUSINESS_UNIT_LIST"] = normalize_list(
        get_first_present_column(df, SOURCE_CANDIDATES["BUSINESS_UNIT_LIST"]),
        output_delimiter=",",
    )
    out["RATING"] = pd.to_numeric(
        get_first_present_column(df, SOURCE_CANDIDATES["RATING"]),
        errors="coerce",
    )
    out["RATING_COUNT"] = pd.to_numeric(
        get_first_present_column(df, SOURCE_CANDIDATES["RATING_COUNT"]),
        errors="coerce",
    ).astype("Int64")
    out["JOB_FUNCTION_LIST"] = normalize_list(
        get_first_present_column(df, SOURCE_CANDIDATES["JOB_FUNCTION_LIST"]),
        output_delimiter=",",
    )

    job_codes = get_first_present_column(df, SOURCE_CANDIDATES["JOB_CODE_LIST"])
    if job_codes.isna().all() and "Users - Occupational Code" in df.columns:
        job_codes = (
            df["Users - Occupational Code"].astype("string").str.split(" ", n=1).str[0]
        )
    out["JOB_CODE_LIST"] = normalize_list(job_codes, output_delimiter=",")

    out["SKILL_PROFICIENCY_LIST"] = normalize_list(
        get_first_present_column(df, SOURCE_CANDIDATES["SKILL_PROFICIENCY_LIST"]),
        output_delimiter=",",
    )
    out["FEE_CURRENCY"] = get_first_present_column(df, SOURCE_CANDIDATES["FEE_CURRENCY"])
    out["PUBLISHED_TS"] = format_timestamp(
        get_first_present_column(df, SOURCE_CANDIDATES["PUBLISHED_TS"])
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
    return f"{clean_customer}_COURSE_CATELOG_IMPORT_{date_part}.csv"


def main() -> None:
    print(f"[INFO] Reading source file: {FILE_PATH}")
    source = pd.read_csv(FILE_PATH, low_memory=False)
    input_rows = len(source)
    print(f"[INFO] Source rows: {input_rows:,}")

    courses = convert_to_course_catalog(source)
    courses = normalize_empty_values(courses)
    courses = fill_required_with_placeholder(courses, REQUIRED_COLUMNS, NULL_PLACEHOLDER)
    courses = fill_all_missing_with_placeholder(courses, NULL_PLACEHOLDER)

    transformed_rows = len(courses)
    assert_row_count("Transformed rows", input_rows, transformed_rows)

    output_name = build_output_filename(CUSTOMER_NAME)
    output_path = OUTPUT_DIR / output_name
    delimiter = delimiter_for_format(FILE_FORMAT)

    courses.to_csv(
        output_path,
        sep=delimiter,
        index=False,
        encoding="utf-8",
    )

    if VERIFY_WRITTEN_ROW_COUNT:
        verify_written_rows(output_path, delimiter, transformed_rows)

    print(f"[DONE] Wrote course catalog import: {output_path}")
    print(f"[DONE] Rows: {transformed_rows:,}")
    print(f"[DONE] Columns: {courses.columns.tolist()}")


if __name__ == "__main__":
    main()
