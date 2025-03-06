import datetime
from enum import Enum
from typing import override

from pydantic import BaseModel, field_validator


class TypeOfListEnum(Enum):
    GERMLINE = "germline"
    FUSION = "fusion"
    CNV = "cnv"
    SNV = "snv"


class GainLossBothEnum(Enum):
    GAIN = "gain"
    LOSS = "loss"
    BOTH = "both"
    UNKNOWN = "unknown"


class CSVBase(BaseModel):
    hugo_name: str
    hgnc_id: int
    protocol: str | None
    date_added: datetime.date
    notes: str | None

    @field_validator("hugo_name")
    def clean_name(cls, value: str) -> str:
        if " " in value:
            raise ValueError(f"Name cannot have spaces: '{value}'")
        return value

    @field_validator("hgnc_id")
    def number_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(f"HGNC must be greater than 0: '{value}'")
        return value

    @override
    def __hash__(self) -> int:
        return hash((self.hugo_name, self.hgnc_id))

    def to_csv(self) -> str:
        return ",".join((str(getattr(self, k)) for k in self.model_fields))


class CombinedCSV(CSVBase):
    departments: set[str]
    total: int

    def add_department(self, department: str):
        self.departments.add(department)

    @classmethod
    def csv_header(cls) -> str:
        defaults = (
            "hugo_name",
            "hgnc_id",
            "protocol",
            "date_added",
            "notes",
        )
        type_specific_set = tuple(
            set(cls.model_fields.keys()) - set(defaults) - set(("departments", "total"))
        )
        return ",".join(defaults + type_specific_set + ("departments", "total"))

    @override
    def __str__(self) -> str:
        seen_in = f"{len(self.departments)}/{self.total}"

        defaults = (
            "hugo_name",
            "hgnc_id",
            "protocol",
            "date_added",
            "notes",
        )
        type_specific_set = (
            self.model_fields_set - set(defaults) - set(("departments", "total"))
        )
        res = ""
        for name in defaults:
            value = getattr(self, name)
            res += f"{value},"
        for name in type_specific_set:
            value = getattr(self, name)
            res += f"{value},"

        res += f"{';'.join(sorted(self.departments))},"
        res += f"{seen_in}"
        return res


class Fusion(CSVBase):
    pass


class FusionCombined(Fusion, CombinedCSV):
    pass


class CNV(CSVBase):
    gain_loss_both: GainLossBothEnum


class CNVCombined(CNV, CombinedCSV):
    pass


class Germline(CSVBase):
    behandlings_relevans: bool


class GermlineCombined(Germline, CombinedCSV):
    pass


TYPE2VALIDATOR: dict[TypeOfListEnum, type[CSVBase]] = {
    TypeOfListEnum.CNV: CNV,
    TypeOfListEnum.FUSION: Fusion,
    TypeOfListEnum.GERMLINE: Germline,
}


TYPE2COMBINED: dict[TypeOfListEnum, type[CombinedCSV]] = {
    TypeOfListEnum.CNV: CNVCombined,
    TypeOfListEnum.FUSION: FusionCombined,
    TypeOfListEnum.GERMLINE: GermlineCombined,
}
