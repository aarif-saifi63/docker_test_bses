from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY
from database import Base, SessionLocal


class SubmenuFallbackV(Base):
    __tablename__ = "submenu_fallback_v"

    id = Column(Integer, primary_key=True)
    category = Column(String, nullable=False, unique=True)  # e.g., "faqs", "payment_history"
    intent_names = Column(Text, nullable=False)  # Comma-separated list of intent names
    initial_msg = Column(Text, nullable=False)  # Initial fallback message (English)
    final_msg = Column(Text, nullable=False)  # Final fallback message (English)
    user_type = Column(ARRAY(String), nullable=True)  # Array of user types (e.g., ['new_consumer', 'registered_consumer'])
    language = Column(String(50), nullable=True)  # Language of the fallback message

    def save(self):
        """
        Save the submenu fallback instance to the database.
        """
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
            return self.id
        finally:
            db.close()

    @staticmethod
    def find_one(**kwargs):
        """
        Find a single submenu fallback record by filters.
        Example: SubmenuFallbackV.find_one(category="faqs")
        """
        db = SessionLocal()
        try:
            return db.query(SubmenuFallbackV).filter_by(**kwargs).first()
        finally:
            db.close()

    @staticmethod
    def find_all():
        """
        Find all submenu fallback records.
        Returns a list of all submenu fallback configurations.
        """
        db = SessionLocal()
        try:
            return db.query(SubmenuFallbackV).all()
        finally:
            db.close()

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update a submenu fallback record based on filter and update queries.
        Example:
            SubmenuFallbackV.update_one(
                {"category": "faqs"},
                {"initial_msg": "updated message"}
            )
        """
        db = SessionLocal()
        try:
            record = db.query(SubmenuFallbackV).filter_by(**filter_query).first()
            if record:
                for k, v in update_query.items():
                    if hasattr(record, k):
                        setattr(record, k, v)
                db.commit()
                db.refresh(record)
                return True
            return False
        finally:
            db.close()

    def get_intents_list(self):
        """
        Parse the comma-separated intent names into a list.
        """
        if self.intent_names:
            return [intent.strip() for intent in self.intent_names.split(',')]
        return []

    def to_dict(self):
        """
        Convert the record to a dictionary format.
        """
        return {
            "category": self.category,
            "intents": self.get_intents_list(),
            "initial_msg": self.initial_msg,
            "final_msg": self.final_msg,
            "user_type": self.user_type,
            "language": self.language
        }
