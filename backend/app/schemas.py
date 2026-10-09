"""Request bodies validated by FastAPI."""

from pydantic import BaseModel, Field, model_validator


class RepairSelection(BaseModel):
    """The repair chosen for one detected damage type."""

    damage_type: str = Field(min_length=1, max_length=64)
    method_id: int | None = Field(default=None, description="repair_methods.id; null when excluded")
    quantity: int = Field(default=1, ge=1, le=20, description="Panels, dents, lamps or tyres to repair")
    excluded: bool = Field(default=False, description="Not repaired, e.g. a false detection")
    note: str = Field(default="", max_length=300)

    @model_validator(mode="after")
    def _method_or_excluded(self):
        if self.excluded and self.method_id is not None:
            raise ValueError("an excluded damage type cannot also have a repair method")
        if not self.excluded and self.method_id is None:
            raise ValueError("choose a repair method or mark the damage type as excluded")
        return self


class ReportRequest(BaseModel):
    analysis_id: str = Field(min_length=1, max_length=64)
    selections: list[RepairSelection] = Field(default_factory=list, max_length=20)
