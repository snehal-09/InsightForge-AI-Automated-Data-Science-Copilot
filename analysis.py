"""
Analysis engine: computes dataset statistics and renders chart images.
All computation is done with pandas / numpy / matplotlib / seaborn —
no LLM involvement, so results are deterministic and reproducible.
"""
import base64
import io
import warnings
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

sns.set_theme(style="darkgrid", rc={
    "axes.facecolor": "#12141c",
    "figure.facecolor": "#12141c",
    "axes.edgecolor": "#3a3f58",
    "axes.labelcolor": "#e7e9f3",
    "text.color": "#e7e9f3",
    "xtick.color": "#a7acc9",
    "ytick.color": "#a7acc9",
    "grid.color": "#262a3d",
})
ACCENT = "#7c6cff"
ACCENT2 = "#22d3c4"
PALETTE = ["#7c6cff", "#22d3c4", "#ff6ec7", "#ffb454", "#5ac8fa", "#ff6b6b"]

MAX_CHART_COLUMNS = 8  # cap so huge datasets don't generate hundreds of charts


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _basic_overview(df: pd.DataFrame) -> dict[str, Any]:
    n_rows, n_cols = df.shape
    dup_count = int(df.duplicated().sum())
    missing_total = int(df.isna().sum().sum())
    missing_pct = round((missing_total / (n_rows * n_cols)) * 100, 2) if n_rows and n_cols else 0.0
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    return {
        "rows": n_rows,
        "columns": n_cols,
        "duplicate_rows": dup_count,
        "missing_cells": missing_total,
        "missing_pct": missing_pct,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "datetime_columns": datetime_cols,
        "memory_kb": round(df.memory_usage(deep=True).sum() / 1024, 1),
    }


def _column_table(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    n = len(df)
    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        rows.append({
            "name": col,
            "dtype": str(s.dtype),
            "missing": missing,
            "missing_pct": round((missing / n) * 100, 1) if n else 0.0,
            "unique": int(s.nunique(dropna=True)),
        })
    return rows


def _missing_values_chart(df: pd.DataFrame) -> str | None:
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if missing.empty:
        return None
    missing = missing.head(20)
    fig, ax = plt.subplots(figsize=(8, max(3, 0.35 * len(missing))))
    ax.barh(missing.index[::-1], missing.values[::-1], color=ACCENT2)
    ax.set_xlabel("Missing values")
    ax.set_title("Missing Values by Column", fontsize=13, weight="bold")
    return _fig_to_base64(fig)


def _numeric_histograms(df: pd.DataFrame, numeric_cols: list[str]) -> list[dict[str, str]]:
    charts = []
    cols = numeric_cols[:MAX_CHART_COLUMNS]
    for i, col in enumerate(cols):
        data = df[col].dropna()
        if data.empty:
            continue
        fig, ax = plt.subplots(figsize=(5, 3.5))
        ax.hist(data, bins=30, color=PALETTE[i % len(PALETTE)], edgecolor="#12141c")
        ax.set_title(f"Distribution: {col}", fontsize=11, weight="bold")
        ax.set_xlabel(col)
        ax.set_ylabel("Frequency")
        charts.append({"title": f"Distribution of {col}", "image": _fig_to_base64(fig)})
    return charts


def _correlation_heatmap(df: pd.DataFrame, numeric_cols: list[str]) -> str | None:
    if len(numeric_cols) < 2:
        return None
    corr = df[numeric_cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(max(5, 0.6 * len(numeric_cols)), max(4, 0.6 * len(numeric_cols))))
    sns.heatmap(corr, annot=len(numeric_cols) <= 12, fmt=".2f", cmap="mako", center=0,
                linewidths=0.5, linecolor="#12141c", ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title("Correlation Heatmap", fontsize=13, weight="bold")
    return _fig_to_base64(fig)


def _categorical_bars(df: pd.DataFrame, categorical_cols: list[str]) -> list[dict[str, str]]:
    charts = []
    cols = [c for c in categorical_cols if df[c].nunique(dropna=True) <= 30][:MAX_CHART_COLUMNS]
    for i, col in enumerate(cols):
        counts = df[col].value_counts().head(15)
        if counts.empty:
            continue
        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        ax.barh(counts.index.astype(str)[::-1], counts.values[::-1], color=PALETTE[i % len(PALETTE)])
        ax.set_title(f"Top categories: {col}", fontsize=11, weight="bold")
        ax.set_xlabel("Count")
        charts.append({"title": f"Top categories in {col}", "image": _fig_to_base64(fig)})
    return charts


def _boxplots(df: pd.DataFrame, numeric_cols: list[str]) -> str | None:
    cols = numeric_cols[:MAX_CHART_COLUMNS]
    if not cols:
        return None
    # normalize scale isn't needed since we show one box per subplot grid via seaborn boxenplot on melted data (scaled)
    fig, ax = plt.subplots(figsize=(max(6, 1.1 * len(cols)), 4))
    data = df[cols].copy()
    # z-score normalize purely for comparable visual scale
    data = (data - data.mean()) / data.std(ddof=0).replace(0, 1)
    sns.boxplot(data=data, palette=PALETTE, ax=ax)
    ax.set_title("Outlier Overview (standardized scale)", fontsize=13, weight="bold")
    ax.tick_params(axis="x", rotation=30)
    return _fig_to_base64(fig)


def run_full_analysis(df: pd.DataFrame) -> dict[str, Any]:
    overview = _basic_overview(df)
    columns_table = _column_table(df)

    numeric_cols = overview["numeric_columns"]
    categorical_cols = overview["categorical_columns"]

    charts: list[dict[str, str]] = []

    missing_chart = _missing_values_chart(df)
    if missing_chart:
        charts.append({"title": "Missing Values Overview", "image": missing_chart})

    corr_chart = _correlation_heatmap(df, numeric_cols)
    if corr_chart:
        charts.append({"title": "Correlation Heatmap", "image": corr_chart})

    box_chart = _boxplots(df, numeric_cols)
    if box_chart:
        charts.append({"title": "Outlier Overview", "image": box_chart})

    charts.extend(_numeric_histograms(df, numeric_cols))
    charts.extend(_categorical_bars(df, categorical_cols))

    describe = df.describe(include="all").fillna("").astype(str).to_dict()

    insights = _rule_based_insights(df, overview, columns_table)

    return {
        "overview": overview,
        "columns": columns_table,
        "describe": describe,
        "charts": charts,
        "insights": insights,
    }


def _rule_based_insights(df: pd.DataFrame, overview: dict, columns_table: list[dict]) -> list[str]:
    notes = []
    if overview["duplicate_rows"] > 0:
        notes.append(f"Found {overview['duplicate_rows']} duplicate rows — consider dropping them before modeling.")
    high_missing = [c for c in columns_table if c["missing_pct"] > 40]
    if high_missing:
        names = ", ".join(c["name"] for c in high_missing[:5])
        notes.append(f"Columns with >40% missing values: {names}. Consider dropping or imputing carefully.")
    high_card = [c for c in columns_table if c["dtype"] == "object" and c["unique"] > 0.9 * overview["rows"] and overview["rows"] > 20]
    if high_card:
        names = ", ".join(c["name"] for c in high_card[:5])
        notes.append(f"High-cardinality text columns detected: {names}. These may be identifiers rather than features.")
    if overview["missing_pct"] == 0 and overview["duplicate_rows"] == 0:
        notes.append("No missing values or duplicate rows detected — the dataset looks clean overall.")
    if len(overview["numeric_columns"]) >= 2:
        notes.append("Multiple numeric columns found — a correlation heatmap and outlier overview are included below.")
    if not notes:
        notes.append("Dataset loaded successfully. Review the charts below for a full visual breakdown.")
    return notes
