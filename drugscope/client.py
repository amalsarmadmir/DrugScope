from typing import List, Dict, Any
from drugscope.models import SafetyReportModel
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
# import math

BASE_URL = "https://api.fda.gov/drug/event.json"


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
def fetch_adverse_events(
    drug_name: str, limit: int = 100, pages: int = 1
) -> List[Dict[str, Any]]:

    clean_name = drug_name.strip().upper()
    search_query = f'patient.drug.medicinalproduct:"{clean_name}"'
    params = {"search": search_query, "limit": limit}

    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
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
            print(f"Page {page} processed!")
            params["page"] = page
            response = requests.get(BASE_URL, params=params, timeout=5)
            data = response.json()
            results.extend(data.get("results", []))

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
    return results


def response_to_model_mapping(
    raw_reports: List[Dict[str, Any]],
) -> List[SafetyReportModel]:

    parsed_reports: List[SafetyReportModel] = []

    for report_data in raw_reports:
        parsed_report = SafetyReportModel.model_validate(report_data)
        parsed_reports.append(parsed_report)
    return parsed_reports
