from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/dimensions", tags=["dimensions"])


@router.post("", response_model=schemas.Dimension, status_code=status.HTTP_201_CREATED)
def create_dimension(payload: schemas.DimensionCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_dimension(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Dimension already exists") from exc


@router.get("", response_model=list[schemas.Dimension])
def list_dimensions(db: Session = Depends(get_db)):
    return crud.get_dimensions(db)


@router.get("/{dimension_id}", response_model=schemas.Dimension)
def get_dimension(dimension_id: UUID, db: Session = Depends(get_db)):
    item = crud.get_dimension(db, dimension_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Dimension not found")
    return item


@router.delete("/{dimension_id}", response_model=schemas.Dimension)
def delete_dimension(dimension_id: UUID, db: Session = Depends(get_db)):
    item = crud.delete_dimension(db, dimension_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Dimension not found")
    return item
