from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/attributes", tags=["attributes"])


@router.post("", response_model=schemas.Attribute, status_code=status.HTTP_201_CREATED)
def create_attribute(payload: schemas.AttributeCreate, db: Session = Depends(get_db)):
    if crud.get_dimension(db, payload.dimension_id) is None:
        raise HTTPException(status_code=404, detail="Dimension not found")
    try:
        return crud.create_attribute(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unable to create attribute") from exc


@router.get("", response_model=list[schemas.Attribute])
def list_attributes(dimension_id: UUID | None = Query(default=None), db: Session = Depends(get_db)):
    return crud.get_attributes(db, dimension_id)


@router.get("/{attribute_id}", response_model=schemas.Attribute)
def get_attribute(attribute_id: UUID, db: Session = Depends(get_db)):
    item = crud.get_attribute(db, attribute_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Attribute not found")
    return item


@router.delete("/{attribute_id}", response_model=schemas.Attribute)
def delete_attribute(attribute_id: UUID, db: Session = Depends(get_db)):
    item = crud.delete_attribute(db, attribute_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Attribute not found")
    return item
