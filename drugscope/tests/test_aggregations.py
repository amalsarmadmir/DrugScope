import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from tabulate import tabulate

from drugscope.aggregator import (
    no_of_serious_reports,
    sex_percentage,
    age_demographics,
    top_n_reactions,
    top_patient_outcomes,
    top_interacting_drugs,
    run_aggregations_for_report,
    run_aggregations_for_output,
)


class TestDrugSafetyAggregations(unittest.TestCase):

    def setUp(self):
        """Set up mock data structures representing SafetyReportModel instances."""
        # Setup Mock Report 1: Serious, Male, Age 45, Reaction: Rash (Fatal), Drug: Aspirin
        self.mock_report_1 = MagicMock()
        self.mock_report_1.is_serious_code = "1"
        self.mock_report_1.patient.sex_code = "1"
        self.mock_report_1.patient.standardized_age = 45.0

        reaction_1 = MagicMock(term="Rash", outcome_label="Fatal")
        self.mock_report_1.patient.reactions = [reaction_1]

        drug_1a = MagicMock(medicinal_product="DrugX", role="Suspect")
        drug_1b = MagicMock(medicinal_product="Aspirin", role="Concomitant")
        self.mock_report_1.patient.drugs = [drug_1a, drug_1b]

        # Setup Mock Report 2: Non-Serious, Female, Age 70, Reaction: Nausea (Recovered), Drug: Metformin
        self.mock_report_2 = MagicMock()
        self.mock_report_2.is_serious_code = "2"
        self.mock_report_2.patient.sex_code = "2"
        self.mock_report_2.patient.standardized_age = 70.0

        reaction_2 = MagicMock(term="Nausea", outcome_label="Recovered")
        reaction_3 = MagicMock(
            term="Rash", outcome_label="Recovered"
        )  # Rash repeated
        self.mock_report_2.patient.reactions = [reaction_2, reaction_3]

        drug_2a = MagicMock(medicinal_product="DrugX", role="Suspect")
        drug_2b = MagicMock(medicinal_product="Metformin", role="Concomitant")
        self.mock_report_2.patient.drugs = [drug_2a, drug_2b]

        # Group reports for happy path testing
        self.reports = [self.mock_report_1, self.mock_report_2]

    ## --- TEST INDIVIDUAL AGGREGATIONS ---

    def test_no_of_serious_reports(self):
        # Happy path: 1 serious out of 2 reports
        s_pct, ns_pct, s_count, t_count = no_of_serious_reports(self.reports)
        self.assertEqual(s_count, 1)
        self.assertEqual(t_count, 2)
        self.assertAlmostEqual(s_pct, 50.0)
        self.assertAlmostEqual(ns_pct, 50.0)

        # Edge Case: Empty list
        s_pct, ns_pct, s_count, t_count = no_of_serious_reports([])
        self.assertEqual((s_pct, ns_pct, s_count, t_count), (0.0, 0.0, 0, 0))

    def test_sex_percentage(self):
        # Happy path: 1 Male, 1 Female
        m_pct, f_pct = sex_percentage(self.reports)
        self.assertAlmostEqual(m_pct, 50.0)
        self.assertAlmostEqual(f_pct, 50.0)

        # Edge case: Empty list
        m_pct, f_pct = sex_percentage([])
        self.assertEqual((m_pct, f_pct), (0.0, 0.0))

    def test_age_demographics(self):
        # Happy Path: Ages 45 (Adult) and 70 (Geriatric). Average = 57.5
        df_summary, avg_age = age_demographics(self.reports)

        self.assertAlmostEqual(avg_age, 57.5)
        self.assertIn("Adults 18-64", df_summary["Age_Group"].values)
        self.assertIn("Geriatrics 65+", df_summary["Age_Group"].values)

        # Confirm exact percentages per group
        adult_row = df_summary[df_summary["Age_Group"] == "Adults 18-64"]
        self.assertEqual(adult_row["Count"].values[0], 1)
        self.assertAlmostEqual(adult_row["Percentage"].values[0], 50.0)

        # Edge Case: Missing or None ages
        mock_report_none_age = MagicMock()
        mock_report_none_age.patient.standardized_age = None
        df_empty, avg_empty = age_demographics([mock_report_none_age])
        self.assertEqual(avg_empty, 0.0)

    def test_top_n_reactions(self):
        # Happy path: "Rash" appears twice, "Nausea" appears once
        reactions = top_n_reactions(self.reports, n=1)

        self.assertEqual(len(reactions), 1)
        # result shape is itertuples named 'Reaction' -> tuple fields: Reactions, Count
        self.assertEqual(reactions[0].Reactions, "Rash")
        self.assertEqual(reactions[0].Count, 2)

    def test_top_patient_outcomes(self):
        # Happy path evaluation
        df_outcomes = top_patient_outcomes(self.reports)

        self.assertEqual(df_outcomes.iloc[0]["Outcome"], "Recovered")
        self.assertEqual(df_outcomes.iloc[0]["Count"], 2)  # 2 'Recovered' terms

    def test_top_interacting_drugs(self):
        # Exclude 'DrugX' (the suspect) and evaluate concurrent drugs
        df_drugs = top_interacting_drugs(self.reports, drug_name="DrugX")

        # Resulting drugs should only be Concomitant variants (Aspirin, Metformin)
        drug_names = df_drugs["Drug"].tolist()
        self.assertIn("Aspirin", drug_names)
        self.assertIn("Metformin", drug_names)
        self.assertNotIn("DrugX", drug_names)

    ## --- TEST PIPELINES ---

    def test_run_aggregations_for_report(self):
        """Validates that the pipeline accurately maps out RunResultsDict dictionary types."""
        result = run_aggregations_for_report(self.reports, "DrugX")

        self.assertEqual(result["drug_name"], "DrugX")
        self.assertEqual(result["total_reports"], 2)
        self.assertEqual(result["seriousness"]["serious_count"], 1)
        self.assertIsInstance(result["age_demographics"]["cohorts"], pd.DataFrame)
        self.assertIsInstance(result["top_reactions"], list)

    @patch("drugscope.utilities.helper.print_reactions_chart")
    @patch("builtins.print")
    def test_run_aggregations_for_output(self, mock_print, mock_print_reactions_chart):
        """Tests terminal print orchestration (ensures nothing crashes during tabulate)."""
        # Execute the printing pipeline runner
        try:
            run_aggregations_for_output(self.reports, "DrugX")
        except Exception as e:
            self.fail(f"run_aggregations_for_output raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()