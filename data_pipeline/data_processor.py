import logging

import pandas as pd


logger = logging.getLogger(__name__)


def remove_duplicates(df):
    """Remove duplicate rows and log how many rows were removed."""
    rows_before = len(df)
    cleaned_df = df.drop_duplicates()
    logger.debug("remove_duplicates: %d -> %d rows", rows_before, len(cleaned_df))
    return cleaned_df


def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    if axis == "rows":
        cleaned_df = df.dropna(axis=0)
        logger.debug("handle_missing: %d -> %d rows", len(df), len(cleaned_df))
    elif axis == "columns":
        cleaned_df = df.dropna(axis=1)
        logger.debug(
            "handle_missing: %d -> %d columns", len(df.columns), len(cleaned_df.columns)
        )
    else:
        logger.error("Unsupported missing-value axis: %s", axis)
        raise ValueError(f"Unsupported missing-value axis: {axis}")

    return cleaned_df


def remove_outliers(df, columns, method, threshold):
    """Remove rows with outliers in configured numeric columns."""
    method = method.lower()
    if method not in {"iqr", "zscore"}:
        logger.error("Unsupported outlier method: %s", method)
        raise ValueError(f"Unsupported outlier method: {method}")

    cleaned_df = df.copy()
    for column in columns:
        if column not in cleaned_df.columns:
            logger.warning("Column not found: %s", column)
            continue

        series = cleaned_df[column]
        if not pd.api.types.is_numeric_dtype(series):
            logger.warning("Column is not numeric: %s", column)
            continue

        if method == "iqr":
            first_quartile = series.quantile(0.25)
            third_quartile = series.quantile(0.75)
            interquartile_range = third_quartile - first_quartile
            lower_bound = first_quartile - threshold * interquartile_range
            upper_bound = third_quartile + threshold * interquartile_range
            outliers = (series < lower_bound) | (series > upper_bound)
        else:
            standard_deviation = series.std()
            if pd.isna(standard_deviation) or standard_deviation == 0:
                outliers = pd.Series(False, index=series.index)
            else:
                z_scores = (series - series.mean()) / standard_deviation
                outliers = z_scores.abs() > threshold

        rows_before = len(cleaned_df)
        cleaned_df = cleaned_df.loc[~outliers]
        rows_removed = rows_before - len(cleaned_df)
        logger.debug(
            "%s: method=%s, threshold=%s, removed=%d",
            column,
            method,
            threshold,
            rows_removed,
        )

    return cleaned_df


def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    processing = config["processing"]
    processed_df = df.copy()

    if processing["remove_duplicates"]:
        processed_df = remove_duplicates(processed_df)

    missing_config = processing["missing"]
    if missing_config["enabled"]:
        processed_df = handle_missing(
            processed_df, axis=missing_config["axis"]
        )

    outlier_config = processing["outliers"]
    if outlier_config["enabled"]:
        processed_df = remove_outliers(
            processed_df,
            columns=outlier_config["columns"],
            method=outlier_config["method"],
            threshold=outlier_config["threshold"],
        )

    return processed_df


def create_cleaning_report(df_before, df_after):
    """Return row and column counts before and after cleaning."""
    rows_before = len(df_before)
    rows_after = len(df_after)
    columns_before = len(df_before.columns)
    columns_after = len(df_after.columns)

    return {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_before - rows_after,
        "columns_before": columns_before,
        "columns_after": columns_after,
        "columns_removed": columns_before - columns_after,
    }
