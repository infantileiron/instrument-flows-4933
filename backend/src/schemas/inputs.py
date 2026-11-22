from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


Reference = Annotated[str, StringConstraints(pattern=r'^[A-Z0-9][A-Z0-9-]{2,31}$')]
Code = Annotated[str, StringConstraints(pattern=r'^[A-Z][A-Z0-9]{0,11}$')]


class Login(Input):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=120)


class ReceiptInput(Input):
    reference: Reference
    effective_on: date
    note: str = Field(min_length=2, max_length=200)


class LoanInput(ReceiptInput):
    source: Code
    destination: Code
    instrument: Code
    quantity: int = Field(ge=1, le=500)


class ReversalInput(ReceiptInput):
    original_reference: Reference


class PlanInput(Input):
    series: str = Field(min_length=2, max_length=64)
    version: int = Field(ge=1, le=10000)
    start_on: date
    end_on: date
    instrument: Code | None = None

    @model_validator(mode='after')
    def check_period(self):
        if not 0 <= (self.end_on - self.start_on).days <= 365:
            raise ValueError('周期须正向且覆盖不超过 366 天')
        return self
