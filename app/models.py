from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class Installation(BaseModel):
    existing_model: str = Field(default='', max_length=160)
    connection: Literal['G1', 'G1.5', 'G2', 'unknown'] = 'unknown'
    length_mm: int | None = Field(default=None, ge=50, le=500)
    voltage_v: int | None = Field(default=None, ge=1, le=500)
    medium: Literal['heating_water', 'glycol', 'other', 'unknown'] = 'unknown'
    temp_c: float | None = Field(default=None, ge=-50, le=160)
    pressure_bar: float | None = Field(default=None, ge=0, le=40)
    head_m: float | None = Field(default=None, ge=0, le=50)
    flow_m3h: float | None = Field(default=None, ge=0, le=100)
    control: Literal['dp-v','dp-c','constant','autoadapt','external','unknown'] = 'unknown'
    budget_eur: float | None = Field(default=None, ge=0, le=1e7)
    labour_rate_eur: float | None = Field(default=None, ge=0, le=1e5)

class Offer(BaseModel):
    supplier_name: str = Field(default='', max_length=100)
    model_text: str = Field(default='', max_length=200)
    article_number: str = Field(default='', max_length=60)
    catalogue_id: str = Field(default='', max_length=100)
    quantity: float | None = Field(default=None, gt=0, le=10000)
    unit_price_eur: float | None = Field(default=None, ge=0, le=1e8)
    vat_basis: Literal['net','gross','unknown'] = 'unknown'
    delivery_eur: float | None = Field(default=None, ge=0, le=1e7)
    delivery_status: Literal['included','quoted','unknown'] = 'unknown'
    extras_eur: float | None = Field(default=None, ge=0, le=1e7)
    extras_status: Literal['none','entered','unknown'] = 'unknown'
    labour_hours: float | None = Field(default=None, ge=0, le=1e5)
    labour_status: Literal['none','entered','unknown'] = 'unknown'
    included_accessories: list[str] = Field(default_factory=list, max_length=20)
    excluded_accessories: list[str] = Field(default_factory=list, max_length=20)
    evidence: list[str] = Field(default_factory=list, max_length=20)
    uncertainties: list[str] = Field(default_factory=list, max_length=20)
    extra_notes: str = Field(default='', max_length=1000)
    source_text: str = Field(default='', max_length=18000)

class CompareInput(BaseModel):
    installation: Installation
    offers: list[Offer] = Field(min_length=2,max_length=2)
    vat_rate_percent: float = Field(default=19.0, ge=0, le=40)

class Extraction(BaseModel):
    supplier_name: str = ''
    model_text: str = ''
    article_number: str = ''
    quantity: float | None = None
    unit_price_eur: float | None = None
    vat_basis: Literal['net','gross','unknown'] = 'unknown'
    delivery_eur: float | None = None
    delivery_status: Literal['included','quoted','unknown'] = 'unknown'
    included_accessories: list[str] = Field(default_factory=list)
    excluded_accessories: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    extra_notes: str = ''
