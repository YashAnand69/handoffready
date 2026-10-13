from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .policy import TYPES


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CheckSpec(Payload):
    kind: Literal["presence", "count", "image_dimensions", "png_nonopaque_pixels", "pdf_pages", "literal_text", "manual"]
    types: list[str] | None = None
    comparison: Literal["exact", "at_least"] | None = None
    value: int | None = None
    distinct_bytes: bool | None = None
    width_px: int | None = None
    height_px: int | None = None
    needle: str | None = None
    instruction: str | None = None

    @model_validator(mode="after")
    def parameters(self):
        allowed = {
            "presence": {"types"}, "count": {"types", "comparison", "value", "distinct_bytes"},
            "image_dimensions": {"width_px", "height_px"}, "png_nonopaque_pixels": set(),
            "pdf_pages": {"comparison", "value"}, "literal_text": {"needle"}, "manual": {"instruction"},
        }[self.kind]
        for name in type(self).model_fields:
            if name != "kind" and getattr(self, name) is not None and name not in allowed:
                raise ValueError(f"{name} is not valid for {self.kind}")
        if self.types is not None and (not self.types or len(set(self.types)) != len(self.types) or not set(self.types) <= TYPES):
            raise ValueError("types must contain unique supported file types")
        if self.kind == "presence" and self.types is None:
            raise ValueError("presence requires types")
        if self.kind in {"count", "pdf_pages"}:
            if self.comparison is None or self.value is None or not 1 <= self.value <= (10 if self.kind == "pdf_pages" else 30):
                raise ValueError("count/page checks require a bounded value and comparison")
        if self.kind == "count" and (self.types is None or self.distinct_bytes is None):
            raise ValueError("count requires types and explicit distinct-byte semantics")
        if self.kind == "image_dimensions" and not (self.width_px is not None and self.height_px is not None and 1 <= self.width_px <= 10000 and 1 <= self.height_px <= 10000):
            raise ValueError("dimensions must be integers from 1 to 10000")
        if self.kind == "literal_text" and (not self.needle or len(self.needle) > 500):
            raise ValueError("literal text requires a nonempty needle up to 500 characters")
        if self.kind == "manual" and (not self.instruction or len(self.instruction) > 2000):
            raise ValueError("manual checks require instructions up to 2000 characters")
        return self


class SourceSpan(Payload):
    source_unit_id: str = Field(min_length=1, max_length=100)
    source_text_sha256: str = Field(min_length=64, max_length=64, pattern="^[0-9a-f]{64}$")
    start_cp: int = Field(ge=0, le=20000)
    end_cp: int = Field(ge=1, le=20000)
    quote: str = Field(min_length=1, max_length=500)


class Requirement(Payload):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=160)
    origin: Literal["model_suggested", "human_added"]
    quote: str | None = Field(default=None, max_length=500)
    source_id: str | None = Field(default=None, max_length=100)
    source_span: SourceSpan | None = None
    checks: list[CheckSpec] = Field(min_length=1, max_length=10)
    human_note: str = Field(default="", max_length=2000)


class CreateProject(Payload):
    name: str = Field(min_length=1, max_length=120)


class BriefInput(Payload):
    text: str = Field(min_length=1, max_length=20000)
    source_label: str = Field(default="Agreed brief", min_length=1, max_length=120)


class BaselineInput(Payload):
    requirements: list[Requirement] = Field(max_length=20)


class ApproveInput(Payload):
    baseline_hash: str = Field(min_length=64, max_length=64, pattern="^[0-9a-f]{64}$")
    reviewed_requirement_ids: list[str] = Field(max_length=20)

    @model_validator(mode="after")
    def bounded_ids(self):
        if any(len(value) > 100 for value in self.reviewed_requirement_ids):
            raise ValueError("Invalid requirement ID")
        return self


class RenameInput(Payload):
    display_name: str = Field(min_length=1, max_length=180)


class DecisionInput(Payload):
    file_ids: list[str] = Field(max_length=30)
    review_state: Literal["confirmed", "rejected"]
    human_disposition: Literal["unresolved", "satisfied", "needs_work", "not_applicable"]
    internal_decision_note: str = Field(default="", max_length=2000)
    client_usage_note: str = Field(default="", max_length=2000)
    input_hash: str = Field(min_length=64, max_length=64, pattern="^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def bounded_ids(self):
        if any(len(value) > 100 for value in self.file_ids):
            raise ValueError("Invalid file ID")
        return self


class ExportInput(Payload):
    acknowledge_unresolved: bool
    input_hash: str = Field(min_length=64, max_length=64, pattern="^[0-9a-f]{64}$")


class EmptyInput(Payload):
    pass
