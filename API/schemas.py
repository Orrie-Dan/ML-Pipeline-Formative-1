from datetime import datetime

from pydantic import BaseModel


class EnergyRecordBase(BaseModel):
    datetime: datetime
    pjme_mw: float
    hour: int
    day: int
    month: int
    year: int
    dayofweek: int


class EnergyRecordInput(EnergyRecordBase):
    pass


class EnergyRecordUpdateInput(EnergyRecordBase):
    pass