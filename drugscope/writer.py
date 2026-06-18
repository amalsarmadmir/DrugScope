import json
import csv
from pathlib import Path
from drugscope.types import RunResultsDict


class ReportExporter:
    def __init__(self, run_results: RunResultsDict):
        self.results = run_results

    def to_json(self, output_path: Path) -> None:
        """Converts DataFrames and structured records into standard JSON"""
        json_payload = {
            "metadata": {
                "search_term": self.results["drug_name"],
                "total_reports_evaluated": self.results["total_reports"],
            },
            "severity_metrics": self.results["seriousness"],
            "gender_demographics": self.results["sex_distribution"],
            "age_demographics": {
                "average_age": round(
                    self.results["age_demographics"]["average_age"], 2
                ),
                "cohort_distribution": self.results["age_demographics"][
                    "cohorts"
                ].to_dict(orient="records"),
            },
            "top_adverse_reactions": [
                {"reaction_term": rx.Reactions, "report_count": rx.Count}
                for rx in self.results["top_reactions"]
            ],
            "top_clinical_outcomes": self.results["top_outcomes"].to_dict(
                orient="records"
            ),
            "top_concomitant_drugs": self.results["top_interacting_drugs"].to_dict(
                orient="records"
            ),
        }
        output_dir = Path("outputs")
        output_path = output_dir / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_payload, f, indent=4, ensure_ascii=False)

    def to_csv(self, output_path: Path) -> None:
        """Flattens DataFrames, tuples, and variables into rows"""
        output_dir = Path("outputs")
        output_path = output_dir / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric_Group", "Sub_Category", "Name_or_Label", "Value"])

            writer.writerow(
                ["Metadata", "Search", "target_drug", self.results["drug_name"]]
            )
            writer.writerow(
                ["Metadata", "Search", "total_reports", self.results["total_reports"]]
            )

            sev = self.results["seriousness"]
            writer.writerow(
                ["Metrics", "Severity", "serious_count", sev["serious_count"]]
            )
            writer.writerow(
                [
                    "Metrics",
                    "Severity",
                    "serious_pct",
                    f"{sev['serious_percentage']:.1f}%",
                ]
            )
            writer.writerow(
                [
                    "Metrics",
                    "Severity",
                    "non_serious_pct",
                    f"{sev['non_serious_percentage']:.1f}%",
                ]
            )

            sex = self.results["sex_distribution"]
            writer.writerow(
                ["Metrics", "Gender", "male_pct", f"{sex['male_percentage']:.1f}%"]
            )
            writer.writerow(
                ["Metrics", "Gender", "female_pct", f"{sex['female_percentage']:.1f}%"]
            )

            writer.writerow(
                [
                    "Metrics",
                    "Age",
                    "average_age",
                    f"{self.results['age_demographics']['average_age']:.1f}",
                ]
            )
            for row in self.results["age_demographics"]["cohorts"].itertuples(
                index=False
            ):
                writer.writerow(["Age_Cohort", str(row.Age_Group), "count", row.Count])
                writer.writerow(
                    [
                        "Age_Cohort",
                        str(row.Age_Group),
                        "percentage",
                        f"{row.Percentage:.1f}%",
                    ]
                )

            for idx, rx in enumerate(self.results["top_reactions"], 1):
                writer.writerow(
                    ["Top_Adverse_Reactions", f"Rank_{idx}", rx.Reactions, rx.Count]
                )

            for idx, row in enumerate(
                self.results["top_outcomes"].itertuples(index=False), 1
            ):
                writer.writerow(
                    [
                        "Clinical_Outcomes",
                        f"Rank_{idx}",
                        row.Outcome,
                        f"{row.Percentage:.1f}% (n={row.Count})",
                    ]
                )

            for idx, row in enumerate(
                self.results["top_interacting_drugs"].itertuples(index=False), 1
            ):
                writer.writerow(
                    ["Concomitant_Medications", f"Rank_{idx}", row.Drug, row.Count]
                )
