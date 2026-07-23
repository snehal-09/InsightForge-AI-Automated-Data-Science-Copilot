"""
File loading utilities.
Supports: .csv, .xlsx, .xls, .json, .parquet, .txt (tab/comma)
"""
from pathlib import Path
import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet", ".txt", ".tsv"}


def load_dataframe(file_path: Path) -> pd.DataFrame:
    ext = file_path.suffix.lower()

    if ext == ".csv":
        return pd.read_csv(file_path)
    if ext == ".tsv":
        return pd.read_csv(file_path, sep="\t")
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path)
    if ext == ".json":
        return pd.read_json(file_path)
    if ext == ".parquet":
        return pd.read_parquet(file_path)
    if ext == ".txt":
        # try comma first, fall back to whitespace
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.read_csv(file_path, delim_whitespace=True)

    raise ValueError(
        f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )


def loader_code_for(ext: str, filename: str) -> str:
    """Returns the python source line(s) used to (re)load this same file type,
    for embedding into the generated notebook."""
    ext = ext.lower()
    var = "df"
    if ext == ".csv":
        return f'{var} = pd.read_csv("{filename}")'
    if ext == ".tsv":
        return f'{var} = pd.read_csv("{filename}", sep="\\t")'
    if ext in (".xlsx", ".xls"):
        return f'{var} = pd.read_excel("{filename}")'
    if ext == ".json":
        return f'{var} = pd.read_json("{filename}")'
    if ext == ".parquet":
        return f'{var} = pd.read_parquet("{filename}")'
    if ext == ".txt":
        return f'{var} = pd.read_csv("{filename}")'
    return f'{var} = pd.read_csv("{filename}")'
