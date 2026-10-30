import datetime
from collections.abc import Sequence
from enum import Enum
from typing import ClassVar, get_args, get_origin, override

from pydantic import BaseModel, field_validator, model_validator


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


class MekanismeEnum(Enum):
    """Mekanisme for genet. Værdierne er forkortelserne fra fusion/README.md."""

    A = "A"
    AEL = "AEL"
    AL = "AL"
    ALCL = "ALCL"
    ALL = "ALL"
    AML = "AML"
    AML_STAR = "AML*"
    APL = "APL"
    B_ALL = "B-ALL"
    B_CLL = "B-CLL"
    B_NHL = "B-NHL"
    CLL = "CLL"
    CML = "CML"
    CMML = "CMML"
    CNS = "CNS"
    D = "D"
    DFSP = "DFSP"
    DLBL = "DLBL"
    DLCL = "DLCL"
    DOM = "Dom"
    E = "E"
    F = "F"
    GIST = "GIST"
    JMML = "JMML"
    L = "L"
    M = "M"
    MALT = "MALT"
    MDS = "MDS"
    MIS = "Mis"
    MLCLS = "MLCLS"
    MM = "MM"
    MPD = "MPD"
    N = "N"
    NHL = "NHL"
    NK_T = "NK/T"
    NSCLC = "NSCLC"
    O = "O"
    PMBL = "PMBL"
    PRE_B_ALL = "pre-B ALL"
    REC = "Rec"
    S = "S"
    T = "T"
    T_ALL = "T-ALL"
    T_CLL = "T-CLL"
    TGCT = "TGCT"
    T_PLL = "T-PLL"
    FUS = "Fus"
    MUT = "Mut"
    INDEL = "Indel"
    KDD = "KDD"
    CNA = "CNA"
    EKSPRESSION = "Ekspression"
    TRUNKERING = "Trunkering"
    REARRANGEMENT = "Rearrangement"


class FunktionAfGenetEnum(Enum):
    """Funktion af genet."""

    ONKOGEN = "onkogen"
    TUMORSUPPRESSOR = "tumorsuppressor"
    UKENDT = "ukendt"
    ONKOGEN_ELLER_TS = "onkogen eller tumorsuppressor"
    ONKOGEN_ELLER_UKENDT = "onkogen eller ukendt"
    INGEN_EVIDENS = "ingen evidens"


class CSVBase(BaseModel):
    hugo_name: str
    hgnc_id: int
    protocol: bool
    protocol_specification: str | None
    date_added: datetime.date
    notes: str | None

    notes_last: ClassVar[bool] = False

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

    @model_validator(mode="before")
    @classmethod
    def split_semicolon_lists(cls, data: object) -> object:
        """Splits ';'-joined CSV strings into lists for list-annotated fields."""
        if not isinstance(data, dict):
            return data
        for name, field in cls.model_fields.items():
            value = data.get(name)
            if not isinstance(value, str):
                continue
            args = get_args(field.annotation)
            if get_origin(field.annotation) is list or any(
                get_origin(arg) is list for arg in args
            ):
                data[name] = (
                    None
                    if value == ""
                    else [v.strip() for v in value.split(";") if v.strip()]
                )
        return data

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
        self.protocol = self.protocol or row.protocol
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
    def ordered_gene_fields(cls) -> Sequence[str]:
        cols = [*cls.defaults(), *cls.type_specific_set()]
        if cls.notes_last:
            cols.remove("notes")
            cols.append("notes")
        return tuple(cols)

    @classmethod
    def csv_header(cls) -> str:
        return ",".join((*cls.ordered_gene_fields(), "departments", "total"))

    @staticmethod
    def defaults() -> Sequence[str]:
        return tuple(CSVBase.model_fields.keys())

    @classmethod
    def type_specific_set(cls) -> Sequence[str]:
        excluded = set(CombinedCSV.defaults()) | {"departments", "total"}
        return tuple(name for name in cls.model_fields if name not in excluded)

    @override
    def __str__(self) -> str:
        res = ""
        for name in self.ordered_gene_fields():
            value = getattr(self, name)
            if value is None:
                res += ","
            elif isinstance(value, list):
                res += (
                    ";".join(
                        str(v.value) if isinstance(v, Enum) else str(v) for v in value
                    )
                    + ","
                )
            elif isinstance(value, Enum):
                res += f"{value.value},"
            else:
                res += f"{value},"

        res += f"{';'.join(sorted(self.departments))},"
        res += f"{len(self.departments)}/{self.total}"
        return res


class SNV(CSVBase):
    pass


class SNVCombined(SNV, CombinedCSV):
    pass


class Fusion(CSVBase):
    notes_last: ClassVar[bool] = True

    behandlings_relevans: bool
    diagnostisk: bool
    prognostisk: bool
    funktion_af_genet: FunktionAfGenetEnum | None = None
    mekanisme: list[MekanismeEnum] | None = None

    @field_validator("funktion_af_genet", mode="before")
    @classmethod
    def empty_string_is_none(cls, value: object) -> object:
        if value == "":
            return None
        return value


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
