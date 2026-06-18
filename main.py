import sys
import argparse
from pathlib import Path
from drugscope.client import fetch_adverse_events, response_to_model_mapping, OpenFDAClientError, DrugNotFoundError
from drugscope.aggregator import run_aggregations_for_report, run_aggregations_for_output
from drugscope.writer import ReportExporter
from drugscope.models import SafetyReportModel

def build_drug_scope_report(reports: list[SafetyReportModel], drug_name: str,base_file_name: str, formats: list[str]) -> None:

    if not reports:
        print("No records available to calculate aggregations.")
        return

    aggregated_results = run_aggregations_for_report(reports, drug_name)
    exporter = ReportExporter(aggregated_results)

    try:
        if 'json' in formats:
            exporter.to_json(Path(f"{base_file_name}.json"))
        if 'csv' in formats:
            exporter.to_csv(Path(f"{base_file_name}.csv"))
        print(f"Successfully generated report artifacts for: {drug_name.upper()}")
    except IOError as err:
        print(f"File Output Generation failed due to an I/O exception: {err}")


def main() -> None:
    parser = argparse.ArgumentParser(description="DrugScope adverse event report tool")
    parser.add_argument("drugname", type=str, help="Drug name to query")
    parser.add_argument("--limit", type=int, default=100, help="Max number of records to fetch")
    parser.add_argument("--output", type=str, help="Base file name for output report")
    parser.add_argument("--format", dest="formats", action="append", choices=["json", "csv"],
                        help="Output format(s): json, csv (can be specified multiple times)")
    args = parser.parse_args()

    drug = args.drugname.upper()
    
    try:
        r = fetch_adverse_events(drug, limit=args.limit)
        p_r = response_to_model_mapping(r)
    except DrugNotFoundError as e:
        print(f"No results found: {e}")
        sys.exit(1)
    except OpenFDAClientError as e:
        print(f"API error: {e}")
        sys.exit(1)

    if args.output:
        formats = args.formats or ["json", "csv"]
        run_aggregations_for_output(p_r, drug)
        build_drug_scope_report(p_r, drug, args.output, formats)
    else:
        run_aggregations_for_output(p_r, drug)


if __name__ == "__main__":
    main()