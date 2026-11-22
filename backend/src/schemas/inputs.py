from datetime import date
from typing import Annotated, Literal

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


class SyncItemInput(ReceiptInput):
    kind: Literal['loan', 'reversal']
    original_reference: Reference | None = None
    source: Code | None = None
    destination: Code | None = None
    instrument: Code | None = None
    quantity: int | None = Field(default=None, ge=1, le=500)
    signer: str | None = Field(default=None, min_length=1, max_length=32)

    @model_validator(mode='after')
    def check_kind(self):
        if self.kind == 'loan':
            missing = [name for name in ('source', 'destination', 'instrument', 'quantity')
                       if getattr(self, name) is None]
            if missing:
                raise ValueError(f'签领缺少字段：{"、".join(missing)}')
            if self.original_reference:
                raise ValueError('签领不能引用原凭据编号')
        else:
            if not self.original_reference:
                raise ValueError('冲销须注明原签领编号')
            if self.original_reference == self.reference:
                raise ValueError('冲销编号不得与原签领相同')
        return self


class SyncBatchInput(Input):
    note: str = Field(default='', max_length=200)
    items: list[SyncItemInput] = Field(min_length=1, max_length=500)
