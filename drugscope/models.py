from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from drugscope.utilities.helper import normalize_drug_name


class ReactionModel(BaseModel):
    meddra_version: str = Field(alias="reactionmeddraversionpt")
    term: str = Field(alias="reactionmeddrapt")
    outcome_code: Optional[str] = Field(default=None, alias="reactionoutcome")

    @property
    def outcome_label(self) -> str:
        """Translates ICH E2B outcome codes to readable strings"""
        mapping = {
            "1": "Recovered/Resolved",
            "2": "Recovering/Resolving",
            "3": "Not Recovered/Not Resolved",
            "4": "Recovered/Resolved with Sequelae",
            "5": "Fatal",
            "6": "Unknown",
        }
        return mapping.get(self.outcome_code, "Unknown")


class DrugModel(BaseModel):
    medicinal_product: str = Field(alias="medicinalproduct")
    characterization_code: str = Field(alias="drugcharacterization")
    dosage_form: Optional[str] = Field(default=None, alias="drugdosageform")
    action_code: Optional[str] = Field(default=None, alias="actiondrug")

    @field_validator("medicinal_product", mode="before")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return normalize_drug_name(v)

    @property
    def role(self) -> str:
        """Translates drug characterization codes"""
        mapping = {"1": "Suspect", "2": "Concomitant", "3": "Interacting"}
        return mapping.get(self.characterization_code, "Concomitant")


class PatientModel(BaseModel):
    age_raw: Optional[str] = Field(default=None, alias="patientonsetage")
    age_unit: Optional[str] = Field(default=None, alias="patientonsetageunit")
    sex_code: Optional[str] = Field(default=None, alias="patientsex")
    reactions: List[ReactionModel] = Field(default=[], alias="reaction")
    drugs: List[DrugModel] = Field(default=[], alias="drug")

    @property
    def standardized_age(self) -> Optional[float]:
        """Calculates age in years based on the FDA unit code"""
        if not self.age_raw or not self.age_unit:
            return None
        try:
            age = float(self.age_raw)
            # 801 = Years, 802 = Months, 803 = Weeks, 804 = Days
            if self.age_unit == "801":
                return age
            if self.age_unit == "802":
                return age / 12
            if self.age_unit == "803":
                return age / 52
            if self.age_unit == "804":
                return age / 365.25
            return age
        except ValueError:
            return None


class SafetyReportModel(BaseModel):
    report_id: str = Field(alias="safetyreportid")
    is_serious_code: str = Field(alias="serious")
    patient: PatientModel

    @property
    def is_serious(self) -> bool:
        return self.is_serious_code == "1"
