from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas


# Dimensions

def create_dimension(db: Session, payload: schemas.DimensionCreate) -> models.Dimension:
    db_dimension = models.Dimension(**payload.model_dump())
    db.add(db_dimension)
    db.commit()
    db.refresh(db_dimension)
    return db_dimension


def get_dimensions(db: Session) -> list[models.Dimension]:
    stmt = select(models.Dimension).order_by(models.Dimension.created_at)
    return list(db.scalars(stmt).all())


def get_dimension(db: Session, dimension_id: UUID) -> models.Dimension | None:
    stmt = select(models.Dimension).where(models.Dimension.dimension_id == dimension_id)
    return db.scalars(stmt).first()


def delete_dimension(db: Session, dimension_id: UUID) -> models.Dimension | None:
    db_dimension = get_dimension(db, dimension_id)
    if db_dimension is None:
        return None
    db.delete(db_dimension)
    db.commit()
    return db_dimension


# Attributes

def create_attribute(db: Session, payload: schemas.AttributeCreate) -> models.Attribute:
    db_attribute = models.Attribute(**payload.model_dump())
    db.add(db_attribute)
    db.commit()
    db.refresh(db_attribute)
    return db_attribute


def get_attributes(db: Session, dimension_id: UUID | None = None) -> list[models.Attribute]:
    stmt = select(models.Attribute).order_by(models.Attribute.created_at)
    if dimension_id is not None:
        stmt = stmt.where(models.Attribute.dimension_id == dimension_id)
    return list(db.scalars(stmt).all())


def get_attribute(db: Session, attribute_id: UUID) -> models.Attribute | None:
    stmt = select(models.Attribute).where(models.Attribute.attribute_id == attribute_id)
    return db.scalars(stmt).first()


def delete_attribute(db: Session, attribute_id: UUID) -> models.Attribute | None:
    db_attribute = get_attribute(db, attribute_id)
    if db_attribute is None:
        return None
    db.delete(db_attribute)
    db.commit()
    return db_attribute


# Members

def create_member(db: Session, payload: schemas.DimensionMemberCreate) -> models.DimensionMember:
    db_member = models.DimensionMember(**payload.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def get_members(db: Session, dimension_id: UUID | None = None) -> list[models.DimensionMember]:
    stmt = select(models.DimensionMember).order_by(models.DimensionMember.created_at)
    if dimension_id is not None:
        stmt = stmt.where(models.DimensionMember.dimension_id == dimension_id)
    return list(db.scalars(stmt).all())


def get_member(db: Session, member_id: UUID) -> models.DimensionMember | None:
    stmt = select(models.DimensionMember).where(models.DimensionMember.member_id == member_id)
    return db.scalars(stmt).first()


def delete_member(db: Session, member_id: UUID) -> models.DimensionMember | None:
    db_member = get_member(db, member_id)
    if db_member is None:
        return None
    db.delete(db_member)
    db.commit()
    return db_member
