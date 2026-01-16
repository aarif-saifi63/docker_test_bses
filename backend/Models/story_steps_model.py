from sqlalchemy import Column, String, Integer
from database import Base, SessionLocal


class StorySteps(Base):
    __tablename__ = "story_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    step_order = Column(Integer, nullable=False)
    step_type = Column(String(50), nullable=False)  # intent, action, slot
    step_name = Column(String(255), nullable=False)
    slot_value = Column(String(255), nullable=True)

    def save(self):
        """
        Save the story step instance to the database.
        """
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        """
        Find a single story step record by filters.
        Example: StorySteps.find_one(user_id=1, step_order=1)
        """
        db = SessionLocal()
        return db.query(StorySteps).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update a story step record based on filter and update queries.
        Example:
            StorySteps.update_one(
                {"id": 1},
                {"step_name": "updated_step_name", "slot_value": "new_value"}
            )
        """
        db = SessionLocal()
        session = db.query(StorySteps).filter_by(**filter_query).first()
        if session:
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            db.commit()
            db.refresh(session)
            return True
        return False
