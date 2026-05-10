"""对话管理服务。

负责对话的 CRUD 和消息持久化。
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationMessage


def create_conversation(db: Session, user_id: int, title: str = "新对话") -> Conversation:
    conversation = Conversation(user_id=user_id, title=title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversations(db: Session, user_id: int, limit: int = 20, offset: int = 0) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_conversation(db: Session, conversation_id: int, user_id: int) -> Conversation | None:
    return db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()


def delete_conversation(db: Session, conversation_id: int, user_id: int) -> bool:
    conversation = get_conversation(db, conversation_id, user_id)
    if not conversation:
        return False
    db.delete(conversation)
    db.commit()
    return True


def get_messages(db: Session, conversation_id: int) -> list[ConversationMessage]:
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at)
        .all()
    )


def save_message(db: Session, conversation_id: int, role: str, content: str) -> None:
    db.add(ConversationMessage(conversation_id=conversation_id, role=role, content=content))
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.updated_at = datetime.now()
        db.add(conversation)
    db.commit()
