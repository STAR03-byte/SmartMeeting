from __future__ import annotations

from threading import RLock

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.hotword import Hotword
from app.schemas.hotword import HotwordCreate

_HOTWORD_CACHE: dict[int, tuple[str, ...]] = {}
_HOTWORD_CACHE_LOCK = RLock()


def _normalize_word(word: str) -> str:
    return word.strip()


def _normalize_config_hotwords() -> tuple[str, ...]:
    return tuple(
        item.strip() for item in settings.whisper_hot_words.split(",") if item.strip()
    )


def clear_hotword_cache(user_id: int | None = None) -> None:
    with _HOTWORD_CACHE_LOCK:
        if user_id is None:
            for key in list(_HOTWORD_CACHE):
                del _HOTWORD_CACHE[key]
        else:
            _ = _HOTWORD_CACHE.pop(user_id, None)


def list_hotwords(db: Session, user_id: int) -> list[Hotword]:
    return (
        db.query(Hotword)
        .filter(Hotword.user_id == user_id)
        .order_by(Hotword.id.desc())
        .all()
    )


def create_hotword(db: Session, user_id: int, payload: HotwordCreate) -> Hotword:
    word = _normalize_word(payload.word)
    hotword = Hotword(user_id=user_id, word=word)
    db.add(hotword)
    db.commit()
    db.refresh(hotword)
    clear_hotword_cache(user_id)
    return hotword


def get_hotword(db: Session, user_id: int, hotword_id: int) -> Hotword | None:
    return (
        db.query(Hotword)
        .filter(Hotword.id == hotword_id, Hotword.user_id == user_id)
        .first()
    )


def delete_hotword(db: Session, hotword: Hotword) -> None:
    user_id = hotword.user_id
    db.delete(hotword)
    db.commit()
    clear_hotword_cache(user_id)


def get_hotword_terms(db: Session, user_id: int | None) -> tuple[str, ...]:
    config_terms = _normalize_config_hotwords()
    if user_id is None:
        return config_terms

    with _HOTWORD_CACHE_LOCK:
        cached = _HOTWORD_CACHE.get(user_id)
    if cached is None:
        db_terms = tuple(
            item.word.strip()
            for item in list_hotwords(db, user_id)
            if item.word.strip()
        )
        cached = db_terms
        with _HOTWORD_CACHE_LOCK:
            _HOTWORD_CACHE[user_id] = cached

    if not config_terms:
        return cached
    if not cached:
        return config_terms
    return tuple(dict.fromkeys((*config_terms, *cached)))
