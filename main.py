"""Application entry point for the MP2 REST API."""

import io
import json
import logging
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from data_pipeline import create_cleaning_report, process_data, validate_dataframe
from src import (
    DatasetInfo,
    DatasetStorage,
    HealthResponse,
    ProcessConfig,
    ProcessingReport,
    log_requests,
    setup_logging,
)

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
app.middleware("http")(log_requests)
storage = DatasetStorage()


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
    extension = Path(file.filename or "").suffix.lower()
    if extension != ".csv":
        logger.warning("Unsupported file format: %s", extension)
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        logger.warning("Could not read CSV file %s: %s", file.filename, error)
        raise HTTPException(
            status_code=400,
            detail=f"Could not read CSV file: {error}",
        ) from error

    dataset_id = storage.save(df, file.filename)
    metadata = storage.get_metadata(dataset_id)
    logger.info(
        "Uploaded dataset: id=%s, filename=%s, rows=%s",
        dataset_id,
        file.filename,
        len(df),
    )
    return DatasetInfo(**metadata)


@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning("Dataset not found: %s", dataset_id)
        raise HTTPException(status_code=404, detail="Dataset not found.")

    records = json.loads(df.head(limit).to_json(orient="records"))
    logger.info("Retrieved dataset: id=%s, returned_rows=%s", dataset_id, len(records))
    return {"id": dataset_id, "data": records, "total_rows": len(df)}


@app.post(
    "/datasets/{dataset_id}/process",
    response_model=ProcessingReport,
)
def process_dataset(dataset_id: int, config: ProcessConfig):
    """Validate and process a stored dataset using MP1 functions."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning("Dataset not found: %s", dataset_id)
        raise HTTPException(status_code=404, detail="Dataset not found.")

    config_dict = config.model_dump()
    validation_settings = config_dict["validation"]
    missing_numeric_columns = [
        column
        for column in validation_settings["numeric_columns"]
        if column not in df.columns
    ]
    if missing_numeric_columns:
        missing_columns = ", ".join(missing_numeric_columns)
        logger.warning("Numeric columns are missing: id=%s, columns=%s", dataset_id, missing_columns)
        raise HTTPException(
            status_code=400,
            detail=f"Numeric columns are missing: {missing_columns}",
        )

    try:
        validated_df = validate_dataframe(
            df,
            required_columns=validation_settings["required_columns"],
            numeric_columns=validation_settings["numeric_columns"],
        )
        validation_rows_removed = len(df) - len(validated_df)
        validated_copy = validated_df.copy()
        processed_df = process_data(validated_df, config_dict)
        cleaning_report = create_cleaning_report(validated_copy, processed_df)
    except ValueError as error:
        logger.warning("Dataset processing failed: id=%s, error=%s", dataset_id, error)
        raise HTTPException(status_code=400, detail=str(error)) from error

    storage.update(dataset_id, processed_df)
    logger.info(
        "Processed dataset: id=%s, validation_removed=%s, rows_before=%s, rows_after=%s",
        dataset_id,
        validation_rows_removed,
        cleaning_report["rows_before"],
        cleaning_report["rows_after"],
    )
    return {
        "id": dataset_id,
        "validation_rows_removed": validation_rows_removed,
        "cleaning_report": cleaning_report,
    }
