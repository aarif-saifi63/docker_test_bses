from sqlalchemy import Column, String, Integer, ForeignKey
from database import Base, SessionLocal
from sqlalchemy.orm import relationship


class ActionsV(Base):
    __tablename__ = "actions_v"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    submenu_id = Column(Integer, ForeignKey("sub_menu_option_v.id", ondelete="CASCADE"), nullable=True)

    submenu = relationship("SubMenuOptionV", back_populates="actions")


    def save(self):
        """
        Save the action instance to the database.
        """
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        """
        Find a single action record by filters.
        Example: ActionsV.find_one(name="start_refund")
        """
        db = SessionLocal()
        return db.query(ActionsV).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update an action record based on filter and update queries.
        Example:
            ActionsV.update_one(
                {"id": 1},
                {"name": "updated_action_name"}
            )
        """
        db = SessionLocal()
        session = db.query(ActionsV).filter_by(**filter_query).first()
        if session:
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            db.commit()
            db.refresh(session)
            return True
        return False
