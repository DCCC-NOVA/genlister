import datetime
from collections.abc import Sequence
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
    protocol: bool
    protocol_specification: str | None
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


class CombinedCSV(CSVBase):
    departments: set[str]
    total: int

    def add_info(self, row: CSVBase, department: str):
        """
        Adds information from a given row to the current instance.

        Args:
            row (CSVBase): The row containing the information to be added.
            department (str): The department associated with the row.

        This method updates the current instance with information from the given row. It adds the department to the
        departments set and updates the notes and date_added fields. If the row is the first entry for this gene,
        it initializes the notes field. For boolean fields, it updates the field if the row has a True value.
        """
        self.departments.add(department)
        if self == row:
            # First entry of this gene
            if row.notes:
                self.notes: str | None = f"{department}: {row.notes}"
            if row.protocol_specification:
                self.protocol_specification: str | None = (
                    f"{department}: {row.protocol_specification}"
                )
            return

        self.date_added: datetime.date = max((self.date_added, row.date_added))
        if row.notes:
            if self.notes:
                self.notes += f"; {department}: {row.notes}"
            else:
                self.notes = f"{department}: {row.notes}"
        if row.protocol_specification:
            if self.protocol_specification:
                self.protocol_specification += (
                    f"; {department}: {row.protocol_specification}"
                )
            else:
                self.protocol_specification = (
                    f"{department}: {row.protocol_specification}"
                )

        for col in self.type_specific_set():
            if row.model_fields[col].annotation is bool:
                # This sets the boolean field to True if the row or self is True,
                # which means for the case of e.g. behandlings_relevans, it will be
                # True if any department has this set
                setattr(self, col, getattr(row, col) or getattr(self, col))

    @classmethod
    def csv_header(cls) -> str:
        return ",".join(
            tuple(cls.defaults())
            + tuple(cls.type_specific_set())
            + ("departments", "total")
        )

    @staticmethod
    def defaults() -> Sequence[str]:
        return tuple(CSVBase.model_fields.keys())

    @classmethod
    def type_specific_set(cls) -> Sequence[str]:
        return tuple(
            set(cls.model_fields.keys())
            - set(CombinedCSV.defaults())
            - set(("departments", "total"))
        )

    @override
    def __str__(self) -> str:
        res = ""
        for name in self.defaults():
            value = getattr(self, name)
            res += f"{value},"
        for name in self.type_specific_set():
            value = getattr(self, name)
            res += f"{value},"

        res += f"{';'.join(sorted(self.departments))},"
        res += f"{len(self.departments)}/{self.total}"
        return res


class SNV(CSVBase):
    pass


class SNVCombined(SNV, CombinedCSV):
    pass


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
    TypeOfListEnum.SNV: SNV,
    TypeOfListEnum.FUSION: Fusion,
    TypeOfListEnum.GERMLINE: Germline,
}


TYPE2COMBINED: dict[TypeOfListEnum, type[CombinedCSV]] = {
    TypeOfListEnum.CNV: CNVCombined,
    TypeOfListEnum.SNV: SNVCombined,
    TypeOfListEnum.FUSION: FusionCombined,
    TypeOfListEnum.GERMLINE: GermlineCombined,
}
