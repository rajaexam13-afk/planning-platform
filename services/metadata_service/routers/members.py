from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/members", tags=["members"])


@router.post("", response_model=schemas.DimensionMember, status_code=status.HTTP_201_CREATED)
def create_member(payload: schemas.DimensionMemberCreate, db: Session = Depends(get_db)):
    if crud.get_dimension(db, payload.dimension_id) is None:
        raise HTTPException(status_code=404, detail="Dimension not found")
    try:
        return crud.create_member(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unable to create member") from exc


@router.get("", response_model=list[schemas.DimensionMember])
def list_members(dimension_id: UUID | None = Query(default=None), db: Session = Depends(get_db)):
    return crud.get_members(db, dimension_id)


@router.get("/{member_id}", response_model=schemas.DimensionMember)
def get_member(member_id: UUID, db: Session = Depends(get_db)):
    item = crud.get_member(db, member_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return item


@router.delete("/{member_id}", response_model=schemas.DimensionMember)
def delete_member(member_id: UUID, db: Session = Depends(get_db)):
    item = crud.delete_member(db, member_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return item
