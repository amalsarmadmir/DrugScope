from typing import List, Dict, Any
from drugscope.models import SafetyReportModel
import requests

BASE_URL = "https://api.fda.gov/drug/event.json"

class OpenFDAClientError(Exception):
    def __init__(self,message):
        super().__init__(message)

def fetch_adverse_events(drug_name: str, limit: int = 100) -> List[Dict[str, Any]]:

    clean_name = drug_name.strip().upper()
    search_query = f'patient.drug.medicinalproduct:"{clean_name}"'
    params = { 'search':search_query, 'limit': limit}
    
    try:
        response = requests.get(BASE_URL,params=params,timeout=10)
        if response.status_code == 404:
            raise DrugNotFoundError(f"No adverse event records found for drug: '{clean_name}'")
            
        if response.status_code == 429:
            raise OpenFDAClientError("API rate limit exceeded. Please retry shortly.")

        response.raise_for_status()
        data =response.json()
        results = data.get("results",[])
        
    except requests.exceptions.Timeout:
        raise OpenFDAClientError("The request timed out. Please check your network connection.")
        
    except requests.exceptions.ConnectionError:
        raise OpenFDAClientError("Network connection error. openFDA might be offline or unavailable.")
        
    except requests.exceptions.HTTPError as http_err:
        raise OpenFDAClientError(f"Server returned an HTTP error status: {response.status_code}")
        
    except ValueError as json_err:
        raise OpenFDAClientError("Received an invalid, malformed response payload from the API.")
    return results


def response_to_model_mapping(raw_reports:List[Dict[str, Any]]):

    parsed_reports: List[SafetyReportModel] = []

    for report_data in raw_reports:
        parsed_report = SafetyReportModel.model_validate(report_data)
        parsed_reports.append(parsed_report)
    return parsed_reports

