from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DimensionBase(BaseModel):
    dimension_name: str
    description: str | None = None


class DimensionCreate(DimensionBase):
    pass


class Dimension(DimensionBase):
    dimension_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttributeBase(BaseModel):
    dimension_id: UUID
    attribute_name: str
    datatype: str


class AttributeCreate(AttributeBase):
    pass


class Attribute(AttributeBase):
    attribute_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DimensionMemberBase(BaseModel):
    dimension_id: UUID
    member_key: str


class DimensionMemberCreate(DimensionMemberBase):
    pass


class DimensionMember(DimensionMemberBase):
    member_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
