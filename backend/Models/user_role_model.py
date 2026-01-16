from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base, SessionLocal

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __init__(self, role_name, description=None):
        self.role_name = role_name
        self.description = description

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find(**filters):
        db = SessionLocal()
        return db.query(UserRole).filter_by(**filters).order_by(UserRole.id.desc()).all()

    @staticmethod
    def find_one(**filters):
        db = SessionLocal()
        return db.query(UserRole).filter_by(**filters).first()

    @staticmethod
    def find_by_id(role_id):
        db = SessionLocal()
        return db.query(UserRole).filter_by(id=role_id).first()

    @staticmethod
    def update(role_id, update_values):
        db = SessionLocal()
        role = db.query(UserRole).filter_by(id=role_id).first()
        if role:
            for key, value in update_values.items():
                setattr(role, key, value)
            db.commit()
            return True
        return False

    @staticmethod
    def delete(role_id):
        db = SessionLocal()
        role = db.query(UserRole).filter_by(id=role_id).first()
        if role:
            db.delete(role)
            db.commit()
            return True
        return False
