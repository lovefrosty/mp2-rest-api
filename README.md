# MP2 REST API

This application uses FastAPI to upload, retrieve, and process CSV datasets stored in memory. `GET /health` returns the application’s status and version, while `POST /upload` accepts a CSV file and returns its dataset ID and metadata. `GET /datasets/{dataset_id}` retrieves a stored dataset with an optional row limit. Finally, `POST /datasets/{dataset_id}/process` uses the reusable MP1 functions to validate and clean the dataset, update the stored data, and return a cleaning report.
