from sqlalchemy import Column, String, Integer, ForeignKey
from database import Base, SessionLocal
from sqlalchemy.orm import relationship

class Story(Base):
    __tablename__ = "story"

    id = Column(Integer, primary_key=True)
    story_name = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    submenu_id = Column(Integer, ForeignKey("sub_menu_option_v.id", ondelete="CASCADE"), nullable=True)

    submenu = relationship("SubMenuOptionV", back_populates="stories")

    # ✅ Relationship to StoryStepsAll
    story_steps = relationship(
        "StoryStepsAll",
        back_populates="story",
        cascade="all, delete-orphan",
        passive_deletes=True
    )



    def save(self):
        """
        Save the story instance to the database.
        """
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        """
        Find a single story record by filters.
        Example: Story.find_one(story_name="refund_flow")
        """
        db = SessionLocal()
        return db.query(Story).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update a story record based on filter and update queries.
        Example:
            Story.update_one(
                {"id": 1},
                {"story_name": "updated_story_name"}
            )
        """
        db = SessionLocal()
        session = db.query(Story).filter_by(**filter_query).first()
        if session:
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            db.commit()
            db.refresh(session)
            return True
        return False
