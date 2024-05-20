import datetime
from pydantic import BaseModel

class VictronDataCreate(BaseModel):
    email: str
    password: str
    portal_id: str
    price_to_compare: float
    user_email: str

class VictronDataShow(BaseModel):
    id: int | None
    email: str | None
    password: str | None
    portal_id: str | None
    price_to_compare: float | None

    # to convert the non dict User obj to JSON
    class Config:
        from_attributes = True

class VictronScheduleShow(BaseModel):
    id: int | None
    schedule_time: str | None
    duration: int | None
    schedult_id: str | None
    update_time: datetime.datetime | None

class UserEmail(BaseModel):
    user_email: str

class NordPoolDataCreate(BaseModel):
    last_update_time: str
    min_price: float
    max_price: float
    avg_price: float

class NordPoolDataShow(BaseModel):
    id: int | None
    last_update_time: datetime.datetime | None
    min_price: float | None
    max_price: float | None
    avg_price: float | None

    # to convert the non dict User obj to JSON
    class Config:
        from_attributes = True

class NordPoolPricesCreate(BaseModel):
    data: str

class NordPoolPricesShow(BaseModel):
    id: int | None
    start_time: datetime.datetime | None
    end_time: datetime.datetime | None
    price: float | None

    # to convert the non dict User obj to JSON
    class Config:
        from_attributes = True

class NordPoolDataFilter(BaseModel):
    compare_to: float | None = None
    period: int | None = None

class NordPoolDataPeriod(BaseModel):
    range: bool | None = None