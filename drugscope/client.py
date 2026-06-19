from typing import List, Dict, Any
from drugscope.models import SafetyReportModel
import hashlib
import json
import time
from pathlib import Path
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

BASE_URL = "https://api.fda.gov/drug/event.json"
_CACHE_DIR = Path.home() / ".cache" / "drugscope"
_CACHE_TTL = 86400  # 24 hours


def _cache_path(drug_name: str, limit: int, pages: int) -> Path:
    key = hashlib.sha256(
        f"{drug_name.strip().upper()}:{limit}:{pages}".encode()
    ).hexdigest()
    return _CACHE_DIR / f"{key}.json"


def _read_cache(path: Path) -> List[Dict[str, Any]] | None:
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > _CACHE_TTL:
        return None
    with path.open() as f:
        return json.load(f)


def _write_cache(path: Path, results: List[Dict[str, Any]]) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(results, f)


class OpenFDAClientError(Exception):
    def __init__(self, message):
        super().__init__(message)


class DrugNotFoundError(OpenFDAClientError):
    pass


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    reraise=True,
)
def _get(url: str, params: dict) -> requests.Response:
    return requests.get(url, params=params, timeout=5)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    reraise=True,
)
def fetch_adverse_events(
    drug_name: str, limit: int = 100, pages: int = 1, use_cache: bool = True
) -> List[Dict[str, Any]]:

    cache_file: Path | None = (
        _cache_path(drug_name, limit, pages) if use_cache else None
    )
    if cache_file is not None:
        cached = _read_cache(cache_file)
        if cached is not None:
            print(f"Loaded {len(cached)} results from cache.")
            return cached

    clean_name = drug_name.strip().upper()
    search_query = f'patient.drug.medicinalproduct:"{clean_name}"'
    params = {"search": search_query, "limit": limit}

    response = None
    try:
        requests.get(BASE_URL, params=params, timeout=5)
        if response.status_code == 404:
            raise DrugNotFoundError(
                f"No adverse event records found for drug: '{clean_name}'"
            )

        if response.status_code == 429:
            raise OpenFDAClientError("API rate limit exceeded. Please retry shortly.")

        response.raise_for_status()

        data = response.json()
        print("Page 1 processed!")
        # total = data["meta"]["results"]["total"]
        # num_pages = math.ceil(total / limit)
        results = data.get("results", [])

        for page in range(2, pages + 1):
            params["skip"] = limit * (page - 1)
            response = _get(BASE_URL, params)
            if response.status_code == 404:
                break
            response.raise_for_status()
            results.extend(response.json().get("results", []))
            print(f"Page {page} processed!")

    except requests.exceptions.Timeout:
        raise OpenFDAClientError(
            "The request timed out. Please check your network connection."
        )

    except requests.exceptions.ConnectionError:
        raise OpenFDAClientError(
            "Network connection error. openFDA might be offline or unavailable."
        )

    except requests.exceptions.HTTPError:
        raise OpenFDAClientError(
            f"Server returned an HTTP error status: {response.status_code}"
        )

    except ValueError:
        raise OpenFDAClientError(
            "Received an invalid, malformed response payload from the API."
        )

    if cache_file is not None:
        _write_cache(cache_file, results)

    return results


def response_to_model_mapping(
    raw_reports: List[Dict[str, Any]],
) -> List[SafetyReportModel]:

    parsed_reports: List[SafetyReportModel] = []

    for report_data in raw_reports:
        parsed_report = SafetyReportModel.model_validate(report_data)
        parsed_reports.append(parsed_report)
    return parsed_reports
