from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CurrentUserOut
from app.schemas.hotword import HotwordCreate, HotwordOut
from app.services.hotword_service import create_hotword, delete_hotword, get_hotword, list_hotwords
from .auth import get_current_user

router = APIRouter(prefix="/hotwords", tags=["hotwords"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[HotwordOut])
def list_hotwords_api(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> list[HotwordOut]:
    return [HotwordOut.model_validate(item) for item in list_hotwords(db, current_user.id)]


@router.post("", response_model=HotwordOut, status_code=status.HTTP_201_CREATED)
def create_hotword_api(
    payload: HotwordCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> HotwordOut:
    try:
        return HotwordOut.model_validate(create_hotword(db, current_user.id, payload))
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Hotword already exists") from exc


@router.delete("/{hotword_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hotword_api(
    hotword_id: Annotated[int, Path(ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[CurrentUserOut, Depends(get_current_user)],
) -> None:
    hotword = get_hotword(db, current_user.id, hotword_id)
    if hotword is None:
        raise HTTPException(status_code=404, detail="Hotword not found")
    delete_hotword(db, hotword)
