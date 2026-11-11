
from pathlib import Path
from io import BytesIO
import zipfile

import pandas as pd
import requests

DATA_FILE = Path(__file__).resolve().parent.parent / "311 Service Requests 2026.zip"

DATASET_API = (
    "https://ckan0.cf.opendata.inter.prod-toronto.ca"
    "/api/3/action/package_show"
)


def get_dataset_resources():
    """Retrieve published Toronto 311 dataset resources."""
    response = requests.get(
        DATASET_API,
        params={"id": "311-service-requests-customer-initiated"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise ValueError("Toronto Open Data API returned an error.")
    return payload["result"]["resources"]


def load_toronto_311():
    """Load the uploaded ZIP, falling back to a published ZIP."""
    if DATA_FILE.exists():
        archive_bytes = DATA_FILE.read_bytes()
        resource_name = DATA_FILE.name
    else:
        resources = get_dataset_resources()
        candidates = [
            r for r in resources
            if str(r.get("url", "")).lower().split("?")[0].endswith(".zip")
            or str(r.get("format", "")).upper() == "ZIP"
        ]
        if not candidates:
            raise FileNotFoundError(
                "No local ZIP or published ZIP resource found."
            )
        resource = candidates[-1]
        response = requests.get(resource["url"], timeout=120)
        response.raise_for_status()
        archive_bytes = response.content
        resource_name = resource.get("name", "Toronto 311 ZIP")

    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        filenames = [
            n for n in archive.namelist()
            if n.lower().endswith(".csv")
            and not n.startswith("__MACOSX")
        ]
        if not filenames:
            raise ValueError("No CSV file found inside the ZIP.")

        filename = max(
            filenames,
            key=lambda n: archive.getinfo(n).file_size
        )
        with archive.open(filename) as file:
            df = pd.read_csv(file, low_memory=False)

    metadata = {
        "resource_name": resource_name,
        "filename": filename,
        "rows": len(df),
    }
    return df, metadata


def prepare_data(raw):
    """Standardize columns for the Streamlit application."""
    df = raw.copy()

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    aliases = {
        "service_type": [
            "service_type", "service_request_type",
            "service_request_name", "service_request_type_name"
        ],
        "division": [
            "division", "responsible_division",
            "service_division", "department"
        ],
        "status": [
            "status", "service_request_status",
            "status_name", "service_request_status_name"
        ],
        "created": [
            "created", "creation_date",
            "created_date", "requested_datetime",
            "service_request_created_date", "service_request_open_date"
        ],
    }

    for target, choices in aliases.items():
        if target not in df.columns:
            match = next(
                (name for name in choices if name in df.columns),
                None
            )
            if match:
                df = df.rename(columns={match: target})

    for column in ["service_type", "division", "status"]:
        if column not in df.columns:
            df[column] = "Unknown"
        df[column] = df[column].fillna("Unknown").astype(str)

    if "created" not in df.columns:
        df["created"] = pd.NaT
    else:
        df["created"] = pd.to_datetime(
            df["created"], errors="coerce"
        )

    return df
