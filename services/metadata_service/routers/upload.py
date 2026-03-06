from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/upload", tags=["upload"])


def _normalize_cell(value) -> str | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip()
    return normalized if normalized else None


def _has_hierarchy_gap(values: list[str | None]) -> bool:
    return any(values[i] is None and values[i + 1] is not None for i in range(len(values) - 1))


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
    if len(set(columns)) != len(columns):
        raise HTTPException(status_code=400, detail="CSV headers must be unique after trimming spaces")

    # Keep DataFrame column names aligned to cleaned headers.
    dataframe.columns = columns

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

    existing_member_rows = db.scalars(
        select(models.DimensionMember).where(models.DimensionMember.dimension_id == dimension.dimension_id)
    ).all()
    member_key_to_id = {row.member_key: row.member_id for row in existing_member_rows}

    normalized_rows: list[list[str | None]] = [
        [_normalize_cell(row[col]) for col in columns] for _, row in dataframe.iterrows()
    ]

    # Build path-based member keys and preserve display labels.
    row_member_keys: list[list[str | None]] = []
    members_created = 0

    for row_values in normalized_rows:
        path_stack: list[str] = []
        keys_for_row: list[str | None] = []

        for cell_value in row_values:
            if cell_value is None:
                keys_for_row.append(None)
                continue

            path_stack.append(cell_value)
            path_key = "/".join(path_stack)
            keys_for_row.append(path_key)

            if path_key in member_key_to_id:
                continue

            try:
                new_member = crud.create_member(
                    db,
                    schemas.DimensionMemberCreate(
                        dimension_id=dimension.dimension_id,
                        member_key=path_key,
                        member_label=cell_value,
                    ),
                )
                member_key_to_id[new_member.member_key] = new_member.member_id
                members_created += 1
            except IntegrityError:
                db.rollback()

        row_member_keys.append(keys_for_row)

    hierarchy_created = False

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
            existing_levels = db.scalars(
                select(models.HierarchyLevel)
                .where(models.HierarchyLevel.hierarchy_id == hierarchy.hierarchy_id)
                .order_by(models.HierarchyLevel.level_order)
            ).all()
            existing_level_names = [lvl.level_name for lvl in existing_levels]

            # Keep hierarchy level definition consistent with incoming CSV order.
            if existing_level_names != columns:
                try:
                    with db.begin_nested():
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
                    db.commit()
                except IntegrityError as exc:
                    db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail="Unable to update hierarchy levels for uploaded CSV structure",
                    ) from exc

            existing_relationships = {
                (rel.parent_member_id, rel.child_member_id)
                for rel in db.scalars(
                    select(models.MemberRelationship).where(
                        models.MemberRelationship.hierarchy_id == hierarchy.hierarchy_id
                    )
                ).all()
            }

            for row_values, keys_for_row in zip(normalized_rows, row_member_keys):
                # Skip rows with missing intermediate hierarchy levels (e.g. Country,,City).
                if _has_hierarchy_gap(row_values):
                    continue

                for parent_idx in range(len(columns) - 1):
                    child_idx = parent_idx + 1

                    # Build edges only across true adjacent non-empty levels.
                    if keys_for_row[parent_idx] is None or keys_for_row[child_idx] is None:
                        continue

                    parent_id = member_key_to_id.get(keys_for_row[parent_idx])
                    child_id = member_key_to_id.get(keys_for_row[child_idx])

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
