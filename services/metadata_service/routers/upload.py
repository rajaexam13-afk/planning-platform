import logging
from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/upload", tags=["upload"])
logger = logging.getLogger(__name__)


def _normalize_cell(value) -> str | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip()
    return normalized if normalized else None


def _has_hierarchy_gap(values: list[str | None]) -> bool:
    for idx in range(len(values) - 1):
        if values[idx] is None and values[idx + 1] is not None:
            return True
    return False


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

    dataframe.columns = [str(col).strip() for col in dataframe.columns]
    columns = list(dataframe.columns)

    if not columns or any(not col for col in columns):
        raise HTTPException(status_code=400, detail="Invalid CSV header names")
    if len(set(columns)) != len(columns):
        raise HTTPException(status_code=400, detail="CSV headers must be unique")

    dimension_name = columns[-1]
    normalized_rows: list[list[str | None]] = [
        [_normalize_cell(row[col]) for col in columns] for _, row in dataframe.iterrows()
    ]

    rows_processed = len(dataframe)
    members_created = 0
    relationships_created = 0

    try:
        with db.begin():
            dimension = db.scalars(
                select(models.Dimension).where(models.Dimension.dimension_name == dimension_name)
            ).first()
            if dimension is None:
                dimension = models.Dimension(
                    dimension_name=dimension_name,
                    description=f"Auto-created from upload: {file.filename}",
                )
                db.add(dimension)
                db.flush()

            existing_attrs = {
                attr.attribute_name
                for attr in db.scalars(
                    select(models.Attribute).where(models.Attribute.dimension_id == dimension.dimension_id)
                ).all()
            }
            for col in columns[:-1]:
                if col in existing_attrs:
                    continue
                db.add(
                    models.Attribute(
                        dimension_id=dimension.dimension_id,
                        attribute_name=col,
                        datatype=str(dataframe[col].dtype),
                    )
                )

            hierarchy = None
            if len(columns) > 1:
                hierarchy_name = f"{dimension_name}_hierarchy"
                hierarchy = db.scalars(
                    select(models.Hierarchy).where(
                        models.Hierarchy.dimension_id == dimension.dimension_id,
                        models.Hierarchy.hierarchy_name == hierarchy_name,
                    )
                ).first()
                if hierarchy is None:
                    hierarchy = models.Hierarchy(
                        dimension_id=dimension.dimension_id,
                        hierarchy_name=hierarchy_name,
                    )
                    db.add(hierarchy)
                    db.flush()

                logger.info("Creating hierarchy levels")
                existing_level_names = [
                    level.level_name
                    for level in sorted(hierarchy.levels, key=lambda lvl: lvl.level_order)
                ]

                if existing_level_names != columns:
                    db.query(models.HierarchyLevel).filter(
                        models.HierarchyLevel.hierarchy_id == hierarchy.hierarchy_id
                    ).delete(synchronize_session=False)

                    for index, col in enumerate(columns):
                        db.add(
                            models.HierarchyLevel(
                                hierarchy_id=hierarchy.hierarchy_id,
                                level_name=col,
                                level_order=index,
                            )
                        )

                    db.flush()

            existing_members = db.scalars(
                select(models.DimensionMember).where(
                    models.DimensionMember.dimension_id == dimension.dimension_id
                )
            ).all()
            member_key_to_id = {member.member_key: member.member_id for member in existing_members}

            logger.info("Creating members")
            row_member_keys: list[list[str | None]] = []
            for row_values in normalized_rows:
                if _has_hierarchy_gap(row_values):
                    raise HTTPException(status_code=400, detail="Hierarchy gap detected")

                path_values: list[str] = []
                member_keys_for_row: list[str | None] = []

                for value in row_values:
                    if value is None:
                        member_keys_for_row.append(None)
                        continue

                    path_values.append(value)
                    path_key = "/".join(path_values)
                    member_keys_for_row.append(path_key)

                    if path_key in member_key_to_id:
                        continue

                    db_member = models.DimensionMember(
                        dimension_id=dimension.dimension_id,
                        member_key=path_key,
                        member_label=value,
                    )
                    db.add(db_member)
                    db.flush()
                    member_key_to_id[path_key] = db_member.member_id
                    members_created += 1

                row_member_keys.append(member_keys_for_row)

            if hierarchy is not None:
                logger.info("Building relationships")
                existing_relationships = {
                    (rel.parent_member_id, rel.child_member_id)
                    for rel in db.scalars(
                        select(models.MemberRelationship).where(
                            models.MemberRelationship.hierarchy_id == hierarchy.hierarchy_id
                        )
                    ).all()
                }

                for keys_for_row in row_member_keys:
                    for index in range(len(columns) - 1):
                        parent_key = keys_for_row[index]
                        child_key = keys_for_row[index + 1]

                        if parent_key is None or child_key is None:
                            continue

                        parent_id = member_key_to_id.get(parent_key)
                        child_id = member_key_to_id.get(child_key)
                        if parent_id is None or child_id is None or parent_id == child_id:
                            continue

                        edge = (parent_id, child_id)
                        if edge in existing_relationships:
                            continue

                        db.add(
                            models.MemberRelationship(
                                hierarchy_id=hierarchy.hierarchy_id,
                                parent_member_id=parent_id,
                                child_member_id=child_id,
                            )
                        )
                        existing_relationships.add(edge)
                        relationships_created += 1

    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Failed to process CSV upload") from exc

    return {
        "dimension": dimension_name,
        "rows_processed": rows_processed,
        "members_created": members_created,
        "relationships_created": relationships_created,
    }
