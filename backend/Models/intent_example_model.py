from sqlalchemy import Column, String, Integer, ForeignKey
from database import Base, SessionLocal
from sqlalchemy.orm import relationship


class IntentExampleV(Base):
    __tablename__ = "intent_examples_v"

    id = Column(Integer, primary_key=True)
    example = Column(String, nullable=False)
    intent_id = Column(Integer, ForeignKey("intent_v.id", ondelete="CASCADE"), nullable=False)

    intent = relationship("IntentV", back_populates="examples")

    def save(self):
        """
        Save the intent example instance to the database.
        """
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        """
        Find a single intent example record by filters.
        Example: IntentExampleV.find_one(example="Show my bill")
        """
        db = SessionLocal()
        return db.query(IntentExampleV).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update an intent example record based on filter and update queries.
        Example:
            IntentExampleV.update_one(
                {"id": 1},
                {"example": "Updated example text"}
            )
        """
        db = SessionLocal()
        session = db.query(IntentExampleV).filter_by(**filter_query).first()
        if session:
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            db.commit()
            db.refresh(session)
            return True
        return False
    
    @staticmethod
    def find_by_intent(intent_id):
        with SessionLocal() as db:
            return db.query(IntentExampleV).filter_by(intent_id=intent_id).all()

    @staticmethod
    def find_one(example_id):
        with SessionLocal() as db:
            return db.query(IntentExampleV).filter_by(id=example_id).first()

    @staticmethod
    def update(example_id, update_values):
        with SessionLocal() as db:
            example = db.query(IntentExampleV).filter_by(id=example_id).first()
            if example:
                for key, value in update_values.items():
                    setattr(example, key, value)
                db.commit()
                return True
            return False

    @staticmethod
    def delete(example_id):
        with SessionLocal() as db:
            example = db.query(IntentExampleV).filter_by(id=example_id).first()
            if example:
                db.delete(example)
                db.commit()
                return True
            return False

    @staticmethod
    def delete_by_intent(intent_id):
        with SessionLocal() as db:
            db.query(IntentExampleV).filter_by(intent_id=intent_id).delete()
            db.commit()

    @staticmethod
    def find_by_example(intent_id, example_text):
        """
        Find a single intent example record by intent_id and example text.
        Example:
            IntentExampleV.find_by_example(1, "Book a hotel")
        """
        with SessionLocal() as db:
            return (
                db.query(IntentExampleV)
                .filter_by(intent_id=intent_id, example=example_text)
                .first()
            )