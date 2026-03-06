import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class Dimension(Base):
    __tablename__ = "dimensions"

    dimension_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dimension_name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    attributes = relationship("Attribute", back_populates="dimension", cascade="all, delete-orphan")
    members = relationship("DimensionMember", back_populates="dimension", cascade="all, delete-orphan")
    hierarchies = relationship("Hierarchy", back_populates="dimension", cascade="all, delete-orphan")


class Attribute(Base):
    __tablename__ = "attributes"
    __table_args__ = (UniqueConstraint("dimension_id", "attribute_name", name="uq_attributes_dimension_name"),)

    attribute_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dimension_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dimensions.dimension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute_name = Column(String, nullable=False)
    datatype = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    dimension = relationship("Dimension", back_populates="attributes")


class DimensionMember(Base):
    __tablename__ = "dimension_members"
    __table_args__ = (UniqueConstraint("dimension_id", "member_key", name="uq_members_dimension_key"),)

    member_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dimension_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dimensions.dimension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_key = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    dimension = relationship("Dimension", back_populates="members")


class Hierarchy(Base):
    __tablename__ = "hierarchies"
    __table_args__ = (UniqueConstraint("dimension_id", "hierarchy_name", name="uq_hierarchies_dimension_name"),)

    hierarchy_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dimension_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dimensions.dimension_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hierarchy_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    dimension = relationship("Dimension", back_populates="hierarchies")
    levels = relationship("HierarchyLevel", back_populates="hierarchy", cascade="all, delete-orphan")
    relationships = relationship("MemberRelationship", back_populates="hierarchy", cascade="all, delete-orphan")


class HierarchyLevel(Base):
    __tablename__ = "hierarchy_levels"
    __table_args__ = (
        UniqueConstraint("hierarchy_id", "level_name", name="uq_hierarchy_levels_name"),
        UniqueConstraint("hierarchy_id", "level_order", name="uq_hierarchy_levels_order"),
    )

    level_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hierarchy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hierarchies.hierarchy_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level_name = Column(String, nullable=False)
    level_order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    hierarchy = relationship("Hierarchy", back_populates="levels")


class MemberRelationship(Base):
    __tablename__ = "member_relationships"
    __table_args__ = (
        UniqueConstraint(
            "hierarchy_id",
            "parent_member_id",
            "child_member_id",
            name="uq_member_relationship_path",
        ),
    )

    relationship_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hierarchy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("hierarchies.hierarchy_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_member_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dimension_members.member_id", ondelete="CASCADE"),
        nullable=False,
    )
    child_member_id = Column(
        UUID(as_uuid=True),
        ForeignKey("dimension_members.member_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    hierarchy = relationship("Hierarchy", back_populates="relationships")
    parent_member = relationship("DimensionMember", foreign_keys=[parent_member_id])
    child_member = relationship("DimensionMember", foreign_keys=[child_member_id])
