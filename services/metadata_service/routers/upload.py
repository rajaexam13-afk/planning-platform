from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/dimension", status_code=status.HTTP_201_CREATED)
def upload_dimension_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported")

    try:
        content = file.file.read()
        dataframe = pd.read_csv(BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid CSV file") from exc

    if dataframe.empty:
        raise HTTPException(status_code=400, detail="CSV has no data rows")

    columns = [str(col).strip() for col in dataframe.columns]
    if len(columns) == 0 or any(not col for col in columns):
        raise HTTPException(status_code=400, detail="CSV must contain valid column names")

    dimension_name = columns[-1]

    existing_dimension = db.scalars(
        select(models.Dimension).where(models.Dimension.dimension_name == dimension_name)
    ).first()

    dimension_created = False
    if existing_dimension is None:
        try:
            dimension = crud.create_dimension(
                db,
                schemas.DimensionCreate(
                    dimension_name=dimension_name,
                    description=f"Auto-created from upload: {file.filename}",
                ),
            )
            dimension_created = True
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=400, detail="Unable to create dimension") from exc
    else:
        dimension = existing_dimension

    # Create attributes for non-key columns (all except the final dimension key column)
    existing_attrs = {
        attr.attribute_name
        for attr in db.scalars(
            select(models.Attribute).where(models.Attribute.dimension_id == dimension.dimension_id)
        ).all()
    }

    for col in columns[:-1]:
        if col in existing_attrs:
            continue
        dtype = str(dataframe[col].dtype)
        try:
            created = crud.create_attribute(
                db,
                schemas.AttributeCreate(
                    dimension_id=dimension.dimension_id,
                    attribute_name=col,
                    datatype=dtype,
                ),
            )
            existing_attrs.add(created.attribute_name)
        except IntegrityError:
            db.rollback()

    # Create members from unique values across all columns
    existing_member_rows = db.scalars(
        select(models.DimensionMember).where(models.DimensionMember.dimension_id == dimension.dimension_id)
    ).all()
    member_key_to_id = {row.member_key: row.member_id for row in existing_member_rows}

    members_created = 0
    for col in columns:
        values = dataframe[col].dropna().astype(str).str.strip()
        for value in values:
            if not value or value in member_key_to_id:
                continue
            try:
                new_member = crud.create_member(
                    db,
                    schemas.DimensionMemberCreate(dimension_id=dimension.dimension_id, member_key=value),
                )
                member_key_to_id[new_member.member_key] = new_member.member_id
                members_created += 1
            except IntegrityError:
                db.rollback()

    hierarchy_created = False

    # Build hierarchy only when multiple columns exist
    if len(columns) > 1:
        hierarchy_name = f"{dimension_name}_hierarchy"

        hierarchy = db.scalars(
            select(models.Hierarchy).where(
                models.Hierarchy.dimension_id == dimension.dimension_id,
                models.Hierarchy.hierarchy_name == hierarchy_name,
            )
        ).first()

        if hierarchy is None:
            try:
                hierarchy = crud.create_hierarchy(
                    db,
                    schemas.HierarchyCreate(
                        dimension_id=dimension.dimension_id,
                        hierarchy_name=hierarchy_name,
                    ),
                )
                hierarchy_created = True
            except IntegrityError:
                db.rollback()
                hierarchy = db.scalars(
                    select(models.Hierarchy).where(
                        models.Hierarchy.dimension_id == dimension.dimension_id,
                        models.Hierarchy.hierarchy_name == hierarchy_name,
                    )
                ).first()

        if hierarchy is not None:
            existing_level_names = {
                lvl.level_name
                for lvl in db.scalars(
                    select(models.HierarchyLevel).where(models.HierarchyLevel.hierarchy_id == hierarchy.hierarchy_id)
                ).all()
            }

            for index, col in enumerate(columns, start=1):
                if col in existing_level_names:
                    continue
                try:
                    crud.create_hierarchy_level(
                        db,
                        schemas.HierarchyLevelCreate(
                            hierarchy_id=hierarchy.hierarchy_id,
                            level_name=col,
                            level_order=index,
                        ),
                    )
                    existing_level_names.add(col)
                except IntegrityError:
                    db.rollback()

            existing_relationships = {
                (rel.parent_member_id, rel.child_member_id)
                for rel in db.scalars(
                    select(models.MemberRelationship).where(
                        models.MemberRelationship.hierarchy_id == hierarchy.hierarchy_id
                    )
                ).all()
            }

            for _, row in dataframe.iterrows():
                chain_values = [str(row[col]).strip() for col in columns if pd.notna(row[col]) and str(row[col]).strip()]
                if len(chain_values) < 2:
                    continue
                for parent_val, child_val in zip(chain_values, chain_values[1:]):
                    parent_id = member_key_to_id.get(parent_val)
                    child_id = member_key_to_id.get(child_val)
                    if parent_id is None or child_id is None or parent_id == child_id:
                        continue
                    edge = (parent_id, child_id)
                    if edge in existing_relationships:
                        continue
                    try:
                        crud.create_member_relationship(
                            db,
                            schemas.MemberRelationshipCreate(
                                hierarchy_id=hierarchy.hierarchy_id,
                                parent_member_id=parent_id,
                                child_member_id=child_id,
                            ),
                        )
                        existing_relationships.add(edge)
                    except IntegrityError:
                        db.rollback()

    return {
        "dimension_created": dimension_created,
        "members_created": members_created,
        "hierarchy_created": hierarchy_created,
    }
