from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(tags=["hierarchies"])


@router.post("/hierarchies", response_model=schemas.Hierarchy, status_code=status.HTTP_201_CREATED)
def create_hierarchy(payload: schemas.HierarchyCreate, db: Session = Depends(get_db)):
    if crud.get_dimension(db, payload.dimension_id) is None:
        raise HTTPException(status_code=404, detail="Dimension not found")
    try:
        return crud.create_hierarchy(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unable to create hierarchy") from exc


@router.post("/hierarchy-levels", response_model=schemas.HierarchyLevel, status_code=status.HTTP_201_CREATED)
def create_hierarchy_level(payload: schemas.HierarchyLevelCreate, db: Session = Depends(get_db)):
    if crud.get_hierarchy(db, payload.hierarchy_id) is None:
        raise HTTPException(status_code=404, detail="Hierarchy not found")
    try:
        return crud.create_hierarchy_level(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unable to create hierarchy level") from exc


@router.post("/relationships", response_model=schemas.MemberRelationship, status_code=status.HTTP_201_CREATED)
def create_relationship(payload: schemas.MemberRelationshipCreate, db: Session = Depends(get_db)):
    hierarchy = crud.get_hierarchy(db, payload.hierarchy_id)
    if hierarchy is None:
        raise HTTPException(status_code=404, detail="Hierarchy not found")

    parent_member = crud.get_member(db, payload.parent_member_id)
    child_member = crud.get_member(db, payload.child_member_id)
    if parent_member is None or child_member is None:
        raise HTTPException(status_code=404, detail="Parent or child member not found")

    if payload.parent_member_id == payload.child_member_id:
        raise HTTPException(status_code=400, detail="Parent and child members cannot be the same")

    if parent_member.dimension_id != hierarchy.dimension_id or child_member.dimension_id != hierarchy.dimension_id:
        raise HTTPException(status_code=400, detail="Members must belong to hierarchy dimension")

    try:
        return crud.create_member_relationship(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Unable to create relationship") from exc


@router.get("/hierarchies", response_model=list[schemas.Hierarchy])
def list_hierarchies(db: Session = Depends(get_db)):
    return crud.get_hierarchies(db)


@router.get("/hierarchies/{hierarchy_id}", response_model=schemas.Hierarchy)
def get_hierarchy(hierarchy_id: UUID, db: Session = Depends(get_db)):
    hierarchy = crud.get_hierarchy(db, hierarchy_id)
    if hierarchy is None:
        raise HTTPException(status_code=404, detail="Hierarchy not found")
    return hierarchy
