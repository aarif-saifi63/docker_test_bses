import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Text,
    DateTime,
    func,
    Index,
)
from database import Base, SessionLocal
from sqlalchemy.dialects.postgresql import UUID


class UtterMessage(Base):
    __tablename__ = "utter_messages"

    # Primary Key (integer for indexing)
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique UUID (auto-generated, human-safe for APIs)
    uid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    action_name = Column(String(128), nullable=False)  # e.g. "action_register_consumer_options_english"
    class_name = Column(String(128), nullable=False)
    language = Column(String(8), nullable=False, default="en")  # 'en', 'hi', etc.
    sequence = Column(Integer, nullable=False, default=0)  # ordering of messages
    text = Column(Text, nullable=False)  # actual utterance text
    message_type = Column(String(32), nullable=False, default="text")  # new column
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # __table_args__ = (
    #     Index("ix_utter_action_lang", "action_name", "language"),
    # )

    __table_args__ = (
        Index("ix_utter_action_lang_sequence", "action_name", "language", "sequence", unique=True),
    )



    def to_dict(self):
        return {
            "id": self.id,
            "uid": str(self.uid),
            "action_name": self.action_name,
            "class_name": self.class_name,
            "language": self.language,
            "sequence": self.sequence,
            "text": self.text,
            "message_type": self.message_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # ---------- CRUD Helper Methods ----------

    def save(self):
        """
        Save the UtterMessage instance to the database.
        """
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.uid  # Return UUID (useful for API references)

    @staticmethod
    def find_one(**kwargs):
        """
        Find a single UtterMessage record by filters.
        Example: UtterMessage.find_one(action_name="action_greet", language="en")
        """
        db = SessionLocal()
        return db.query(UtterMessage).filter_by(**kwargs).first()

    @staticmethod
    def find_all(**kwargs):
        """
        Find all UtterMessage records matching filters.
        Example: UtterMessage.find_all(language="en")
        """
        db = SessionLocal()
        return (
            db.query(UtterMessage)
            .filter_by(**kwargs)
            .order_by(UtterMessage.sequence)
            .all()
        )

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update a record based on filter and update queries.
        Example:
            UtterMessage.update_one(
                {"uid": "uuid-here"},
                {"text": "Updated message", "message_type": "text"}
            )
        """
        db = SessionLocal()
        record = db.query(UtterMessage).filter_by(**filter_query).first()
        if record:
            for k, v in update_query.items():
                if hasattr(record, k):
                    setattr(record, k, v)
            db.commit()
            db.refresh(record)
            return True
        return False

    @staticmethod
    def delete_one(**kwargs):
        """
        Delete a single UtterMessage record.
        Example: UtterMessage.delete_one(uid="uuid-here")
        """
        db = SessionLocal()
        record = db.query(UtterMessage).filter_by(**kwargs).first()
        if record:
            db.delete(record)
            db.commit()
            return True
        return False
