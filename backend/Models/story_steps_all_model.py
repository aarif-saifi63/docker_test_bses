from sqlalchemy import Column, String, Integer, ForeignKey
from database import Base, SessionLocal
from sqlalchemy.orm import relationship


class StoryStepsAll(Base):
    __tablename__ = "story_steps_all"

    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("story.id", ondelete="CASCADE"), nullable=False)
    intent = Column(String, nullable=True)
    action = Column(String, nullable=True)

    # ✅ Relationship back to Story
    story = relationship("Story", back_populates="story_steps")

    def save(self):
        """
        Save the story step instance to the database.
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
        Find a single story step record by filters.
        Example: StoryStepsAll.find_one(story_id=1)
        """
        db = SessionLocal()
        try:
            return db.query(StoryStepsAll).filter_by(**kwargs).first()

        finally:
            db.close()
    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update a story step record based on filter and update queries.
        Example:
            StoryStepsAll.update_one(
                {"id": 1},
                {"intent": "billing_inquiry", "action": "send_invoice"}
            )
        """
        db = SessionLocal()
        try:
            session = db.query(StoryStepsAll).filter_by(**filter_query).first()
            if session:
                for k, v in update_query.items():
                    if hasattr(session, k):
                        setattr(session, k, v)
                db.commit()
                db.refresh(session)
                return True
            return False

        finally:
            db.close()