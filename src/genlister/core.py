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


class Fusion(CSVBase):
    pass


class CNV(CSVBase):
    gain_loss_both: GainLossBothEnum


class Germline(CSVBase):
    behandlings_relevans: bool


TYPE2VALIDATOR: dict[TypeOfListEnum, type[CSVBase]] = {
    TypeOfListEnum.CNV: CNV,
    TypeOfListEnum.FUSION: Fusion,
    TypeOfListEnum.GERMLINE: Germline,
}
