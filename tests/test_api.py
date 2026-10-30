"""Required API tests for MP2 Part 2."""


def test_upload_csv(client, sample_csv_bytes):
    response = client.post(
        "/upload",
        files={
            "file": (
                "sample_data.csv",
                sample_csv_bytes,
                "text/csv",
            )
        },
    )
    assert response.status_code == 200
    dataset = response.json()
    assert dataset["rows"] == 6
    assert dataset["columns"] == 2
    assert isinstance(dataset["id"], int)
    assert dataset["id"] > 0


def test_process_and_retrieve(client, uploaded_dataset_id, processing_body):
    process_response = client.post(
        f"/datasets/{uploaded_dataset_id}/process",
        json=processing_body,
    )
    assert process_response.status_code == 200
    report = process_response.json()
    assert report["id"] == uploaded_dataset_id
    assert report["validation_rows_removed"] == 1
    assert report["cleaning_report"] == {
        "rows_before": 5,
        "rows_after": 3,
        "rows_removed": 2,
        "columns_before": 2,
        "columns_after": 2,
        "columns_removed": 0,
    }

    retrieve_response = client.get(f"/datasets/{uploaded_dataset_id}")
    assert retrieve_response.status_code == 200
    dataset = retrieve_response.json()
    assert dataset["total_rows"] == 3
    assert dataset["data"] == [
        {"student_id": 1, "score": 80},
        {"student_id": 2, "score": 90},
        {"student_id": 5, "score": 85},
    ]


def test_retrieve_missing_dataset(client):
    response = client.get("/datasets/999")
    assert response.status_code == 404
