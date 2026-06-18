from typing import TypedDict
import pandas as pd

class SeriousnessDict(TypedDict):
    serious_count: int
    serious_percentage: float
    non_serious_percentage: float

class SexDistributionDict(TypedDict):
    male_percentage: float
    female_percentage: float

class AgeDemographicsDict(TypedDict):
    average_age: float
    cohorts: pd.DataFrame  # columns: Age_Group, Count, Percentage

class RunResultsDict(TypedDict):
    drug_name: str
    total_reports: int
    seriousness: SeriousnessDict
    sex_distribution: SexDistributionDict
    age_demographics: AgeDemographicsDict
    top_reactions: list[tuple[str, int]]
    top_outcomes: pd.DataFrame    # columns: Outcome, Count, Percentage
    top_interacting_drugs: pd.DataFrame  # columns: Drug, Count