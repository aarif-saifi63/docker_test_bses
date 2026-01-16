from sqlalchemy import Column, String, Integer
from database import Base, SessionLocal


class FallbackV(Base):
    __tablename__ = "fallback_v"

    id = Column(Integer, primary_key=True)
    initial_msg = Column(String, nullable=False)
    final_msg = Column(String, nullable=False)  # removed ForeignKey and relation

    def save(self):
        """
        Save the fallback instance to the database.
        """
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        """
        Find a single fallback record by filters.
        Example: FallbackV.find_one(id=1)
        """
        db = SessionLocal()
        return db.query(FallbackV).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update a fallback record based on filter and update queries.
        Example:
            FallbackV.update_one(
                {"id": 1},
                {"initial_msg": "updated message"}
            )
        """
        db = SessionLocal()
        record = db.query(FallbackV).filter_by(**filter_query).first()
        if record:
            for k, v in update_query.items():
                if hasattr(record, k):
                    setattr(record, k, v)
            db.commit()
            db.refresh(record)
            return True
        return False