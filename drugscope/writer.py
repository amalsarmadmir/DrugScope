import json
import csv
from pathlib import Path

class ReportExporter:
    def __init__(self, run_results: dict):
        self.res = run_results

    def to_json(self, output_path: Path) -> None:
        """Converts DataFrames and structured records into standard JSON"""
        # Formulate a clean JSON serialization payload
        json_payload = {
            "metadata": {
                "search_term": self.res["drug_name"],
                "total_reports_evaluated": self.res["total_reports"]
            },
            "severity_metrics": self.res["seriousness"],
            "gender_demographics": self.res["sex_distribution"],
            "age_demographics": {
                "average_age": round(self.res["age_demographics"]["average_age"], 2),
                # Convert Pandas DataFrame into a JSON-compatible list of dicts
                "cohort_distribution": self.res["age_demographics"]["cohorts"].to_dict(orient="records")
            },
            # Map native tuple arrays into a structured dictionary format
            "top_adverse_reactions": [
                {"reaction_term": rx[0], "report_count": rx[1]} for rx in self.res["top_reactions"]
            ],
            "top_clinical_outcomes": self.res["top_outcomes"].to_dict(orient="records"),
            "top_concomitant_drugs": self.res["top_interacting_drugs"].to_dict(orient="records")
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_payload, f, indent=4, ensure_ascii=False)

    def to_csv(self, output_path: Path) -> None:
        """Flattens DataFrames, tuples, and variables into rows"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Metric_Group", "Sub_Category", "Name_or_Label", "Value"])

            # 1. Base Variables Metadata
            writer.writerow(["Metadata", "Search", "target_drug", self.res["drug_name"]])
            writer.writerow(["Metadata", "Search", "total_reports", self.res["total_reports"]])

            # 2. Severity Block
            sev = self.res["seriousness"]
            writer.writerow(["Metrics", "Severity", "serious_count", sev["serious_count"]])
            writer.writerow(["Metrics", "Severity", "serious_pct", f"{sev['serious_percentage']:.1f}%"])
            writer.writerow(["Metrics", "Severity", "non_serious_pct", f"{sev['non_serious_percentage']:.1f}%"])

            # 3. Sex Breakdown Block
            sex = self.res["sex_distribution"]
            writer.writerow(["Metrics", "Gender", "male_pct", f"{sex['male_percentage']:.1f}%"])
            writer.writerow(["Metrics", "Gender", "female_pct", f"{sex['female_percentage']:.1f}%"])

            # 4. Age Data Extraction From Dataframe
            writer.writerow(["Metrics", "Age", "average_age", f"{self.res['age_demographics']['average_age']:.1f}"])
            for row in self.res["age_demographics"]["cohorts"].itertuples(index=False):
                writer.writerow(["Age_Cohort", str(row.Age_Group), "count", row.Count])
                writer.writerow(["Age_Cohort", str(row.Age_Group), "percentage", f"{row.Percentage:.1f}%"])

            # 5. Extract Top Reactions List of Tuples
            for idx, rx in enumerate(self.res["top_reactions"], 1):
                writer.writerow(["Top_Adverse_Reactions", f"Rank_{idx}", rx[0], rx[1]])

            # 6. Extract Clinical Outcomes DataFrame Rows
            for idx, row in enumerate(self.res["top_outcomes"].itertuples(index=False), 1):
                writer.writerow(["Clinical_Outcomes", f"Rank_{idx}", row.Outcome, f"{row.Percentage:.1f}% (n={row.Count})"])

            # 7. Extract Interacting Drugs DataFrame Rows
            for idx, row in enumerate(self.res["top_interacting_drugs"].itertuples(index=False), 1):
                writer.writerow(["Concomitant_Medications", f"Rank_{idx}", row.Drug, row.Count])