"""CSV/Excel file parsing with pandas and column type detection."""
import io
import logging
from typing import Optional
import pandas as pd

from src.exceptions import InvalidFileTypeError, FileTooLargeError

logger = logging.getLogger("deskforge.datasources.csv")

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB


def detect_column_type(series: pd.Series) -> str:
    """Detect the type of a pandas column."""
    non_null = series.dropna()
    if len(non_null) == 0:
        return "text"

    # Check boolean
    if non_null.dtype == bool or set(non_null.unique()).issubset({True, False, 0, 1, "true", "false", "yes", "no"}):
        return "boolean"

    # Check numeric
    if pd.api.types.is_numeric_dtype(non_null):
        if pd.api.types.is_integer_dtype(non_null):
            return "number"
        return "number"

    # Check date
    try:
        pd.to_datetime(non_null.head(100), format="mixed")
        return "date"
    except (ValueError, TypeError):
        pass

    # Check email
    sample = non_null.head(50).astype(str)
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if sample.str.match(email_pattern).mean() > 0.8:
        return "email"

    # Check URL
    url_pattern = r"^https?://"
    if sample.str.match(url_pattern).mean() > 0.8:
        return "url"

    return "text"


def parse_csv(content: bytes, filename: str) -> tuple[pd.DataFrame, dict]:
    """Parse CSV/Excel file and detect column types."""
    ext = _get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError()

    if len(content) > MAX_FILE_SIZE:
        raise FileTooLargeError()

    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8", on_bad_lines="skip")
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        logger.error(f"File parse error: {e}")
        raise InvalidFileTypeError()

    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]
    # Disambiguate duplicate columns
    seen = {}
    new_cols = []
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    df.columns = new_cols

    # Detect types
    column_schemas = []
    for col in df.columns:
        col_type = detect_column_type(df[col])
        sample_values = df[col].dropna().head(5).tolist()
        column_schemas.append({
            "name": col,
            "type": col_type,
            "nullable": bool(df[col].isna().any()),
            "sample_values": [str(v) for v in sample_values],
        })

    return df, {
        "columns": column_schemas,
        "row_count": len(df),
    }


def get_preview(df: pd.DataFrame, rows: int = 20) -> list[dict]:
    """Get first N rows as list of dicts."""
    preview_df = df.head(rows).copy()
    # Convert all values to strings for preview
    for col in preview_df.columns:
        preview_df[col] = preview_df[col].astype(str).replace("nan", None)
    return preview_df.to_dict(orient="records")


def df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts."""
    return df.to_dict(orient="records")


def _get_extension(filename: str) -> str:
    """Get lowercase file extension."""
    if "." in filename:
        return "." + filename.rsplit(".", 1)[1].lower()
    return ""
