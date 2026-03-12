import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint, func
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
