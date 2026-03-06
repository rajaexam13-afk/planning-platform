from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class HierarchyBase(BaseModel):
    dimension_id: UUID
    hierarchy_name: str


class HierarchyCreate(HierarchyBase):
    pass


class Hierarchy(HierarchyBase):
    hierarchy_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HierarchyLevelBase(BaseModel):
    hierarchy_id: UUID
    level_name: str
    level_order: int = Field(ge=1)


class HierarchyLevelCreate(HierarchyLevelBase):
    pass


class HierarchyLevel(HierarchyLevelBase):
    level_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberRelationshipBase(BaseModel):
    hierarchy_id: UUID
    parent_member_id: UUID
    child_member_id: UUID


class MemberRelationshipCreate(MemberRelationshipBase):
    pass


class MemberRelationship(MemberRelationshipBase):
    relationship_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Backward-compatible aliases for older imports
DimensionRead = Dimension
AttributeRead = Attribute
DimensionMemberRead = DimensionMember
