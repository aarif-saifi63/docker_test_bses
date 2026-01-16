from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base, SessionLocal


class MenuOptionV(Base):
    __tablename__ = "menu_option_v"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    lang = Column(String)
    is_visible = Column(Boolean, default=True)
    menu_sequence = Column(Integer)
    icon_path = Column(String, nullable=True)
    menu_sequence = Column(Integer)  

    # Relationship: delete all submenus when menu is deleted
    submenus = relationship(
        "SubMenuOptionV",
        back_populates="menu",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def save(self):
        """
        Save the menu option instance to the database.
        """
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        """
        Find a single menu option record by filters.
        Example: MenuOptionV.find_one(name="Billing", user_id=1)
        """
        db = SessionLocal()
        return db.query(MenuOptionV).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update a menu option record based on filter and update queries.
        Example:
            MenuOptionV.update_one(
                {"id": 1},
                {"is_visible": False}
            )
        """
        db = SessionLocal()
        session = db.query(MenuOptionV).filter_by(**filter_query).first()
        if session:
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            db.commit()
            db.refresh(session)
            return True
        return False
