from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from database import Base, SessionLocal
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    lang = Column(String)
    subsidiary_type = Column(String)

    # ✅ A user can have many menus
    # menus = relationship(
    #     "MenuOptionV",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )

    def save(self):
        """
        Save the user instance to the database.
        """
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        """
        Find a single user record by filters.
        Example: User.find_one(name="BSES Yamuna Registered English")
        """
        db = SessionLocal()
        return db.query(User).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update a user record based on filter and update queries.
        Example:
            User.update_one(
                {"name": "BSES Yamuna Registered English"},
                {"name": "BSES Yamuna Updated English"}
            )
        """
        db = SessionLocal()
        session = db.query(User).filter_by(**filter_query).first()
        if session:
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            db.commit()
            db.refresh(session)
            return True
        return False
