from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, object]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["ipguard-api"])
    version: str = Field(examples=["1.0.0"])


class DatabaseHealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    database: str = Field(examples=["postgresql"])
    latency_ms: float = Field(examples=[1.24])


class SystemInfoResponse(BaseModel):
    name: str = Field(examples=["IPGuard"])
    version: str = Field(examples=["1.0.0"])
    environment: str = Field(examples=["development"])
    api_version: str = Field(examples=["v1"])
    database_engine: str = Field(examples=["postgresql"])
