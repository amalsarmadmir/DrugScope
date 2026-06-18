from typing import List, Any
from drugscope.utilities.helper import print_reactions_chart
from drugscope.models import SafetyReportModel
import pandas as pd
from tabulate import tabulate


def no_of_serious_reports(reports: List[SafetyReportModel]) -> tuple[float, float, int, int]:
    active_count = sum(1 for report in reports if getattr(report, 'is_serious_code', None) == '1')
    total_count = len(reports)
    percentage = (active_count/total_count)*100
    return percentage, 100-percentage, active_count,total_count

def sex_percentage(reports: List[SafetyReportModel]) -> tuple[float, float]:
    male_count= sum(1 for report in reports if getattr(report.patient, 'sex_code', None) == '1')
    female_count= sum(1 for report in reports if getattr(report.patient, 'sex_code', None) == '2')
    total_count = male_count+female_count
    male_percent = (male_count/total_count)*100
    female_percent = (female_count/total_count)*100
    return male_percent, female_percent

def age_demographics(reports: List[SafetyReportModel]) -> tuple[pd.DataFrame, float]:
    age_count = sum([report.patient.standardized_age for report in reports if report.patient.standardized_age is not None ])
    average_age = age_count/len(reports)
    df = pd.DataFrame({'Age':[report.patient.standardized_age for report in reports if report.patient.standardized_age is not None ]})
    #0-17,18-64,65+
    bins = [0, 17, 64, 120]
    labels = ['Pediatrics (<18)', 'Adults 18-64', 'Geriatrics 65+']
    df['Age_Group'] = pd.cut(df['Age'], bins=bins, labels=labels, right=False)
    df_summary = df.groupby('Age_Group').agg(Count=('Age_Group', 'size'),Percentage=('Age_Group', lambda x: (len(x)/len(df)) * 100)).reset_index()
    return df_summary, average_age

def top_n_reactions(reports: List[SafetyReportModel], n: int = 5) -> list[tuple[str, int]]:
    df = pd.DataFrame({'Reactions':[r.term for report in reports for r in report.patient.reactions]})
    df_counts = df.groupby('Reactions').size().reset_index(name='Count')
    result_df = df_counts.sort_values(by='Count', ascending=False).head(n)
    result = list(result_df[['Reactions', 'Count']].itertuples(index=False, name=None))
    return result

def top_patient_outcomes(reports: List[SafetyReportModel], n: int = 3) -> pd.DataFrame:
    df = pd.DataFrame({'Outcome':[r.outcome_label for report in reports for r in report.patient.reactions]})
    df_summary = df.groupby('Outcome').agg(Count=('Outcome', 'size'),Percentage=('Outcome', lambda x: (len(x)/len(df)) * 100)).reset_index().head(n)
    return df_summary

def top_interacting_drugs(reports: List[SafetyReportModel], drug_name: str, n: int = 3) -> pd.DataFrame:
    df = pd.DataFrame({'Drug':[d.medicinal_product for report in reports for d in report.patient.drugs if (d.role != 'Suspect' and drug_name not in d.medicinal_product)]})
    df_counts = df.groupby('Drug').size().reset_index(name='Count')
    result_df = df_counts.sort_values(by='Count', ascending=False).head(n)
    return result_df

def run_aggregations_for_report(reports: List[SafetyReportModel], drug_name: str) -> dict[str, Any]:
    """Executes your original functions and organizes the output shapes"""
    serious_pct, non_serious_pct, serious_count, total_count = no_of_serious_reports(reports)
    male_pct, female_pct = sex_percentage(reports)
    age_df, avg_age = age_demographics(reports)
    reactions_list = top_n_reactions(reports, n=5)
    outcomes_df = top_patient_outcomes(reports, n=3)
    drugs_df = top_interacting_drugs(reports, drug_name, n=3)
    
    return {
        "drug_name": drug_name,
        "total_reports": total_count,
        "seriousness": {
            "serious_count": serious_count,
            "serious_percentage": serious_pct,
            "non_serious_percentage": non_serious_pct
        },
        "sex_distribution": {
            "male_percentage": male_pct,
            "female_percentage": female_pct
        },
        "age_demographics": {
            "average_age": avg_age,
            "cohorts": age_df  # DataFrame
        },
        "top_reactions": reactions_list, # List of Tuples
        "top_outcomes": outcomes_df,     # DataFrame
        "top_interacting_drugs": drugs_df # DataFrame
    }

def run_aggregations_for_output(reports: List[SafetyReportModel], drug_name: str, n: int = 5) -> None:
    print(f'=== SAFETY SUMMARY FOR: ASPIRIN ({len(reports)} Reports Evaluated) ===\n')

    print('[Severity]')
    s_per,ns_per,a_count,t_count = no_of_serious_reports(reports)
    print(f'Serious Reports: {s_per:.0f}%({a_count})')
    print(f'Non-Serious:     {ns_per:.0f}%({t_count-a_count})\n')

    res = top_n_reactions(reports)
    print_reactions_chart(res)
    print()

    print('[Patient Demographics]')
    m_per,f_per = sex_percentage(reports)
    print(f'Sex:     {m_per:.0f}% Female | {f_per:.0f}% Male')
    summary,average_age = age_demographics(reports)
    print(f'Average Age: {average_age:.2f}')
    print(tabulate(summary, headers='keys', tablefmt='psql', showindex=False),'\n')

    print('[Top Patient Outcomes]')
    outcomes = top_patient_outcomes(reports)
    print(tabulate(outcomes, headers='keys', tablefmt='psql', showindex=False),'\n')

    print('[Top Concomitant Medications]')
    meds = top_interacting_drugs(reports,drug_name)
    print(tabulate(meds, headers='keys', tablefmt='psql', showindex=False),'\n')