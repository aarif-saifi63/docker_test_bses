from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base, SessionLocal

class PermissionMatrix(Base):
    __tablename__ = "permission_matrix"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module = Column(String(100), nullable=False)
    crud_action = Column(String(50), nullable=False)  
    permission_name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255))
    label = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __init__(self, module, crud_action, permission_name, description=None, label=None):
        self.module = module
        self.crud_action = crud_action
        self.permission_name = permission_name
        self.description = description
        self.label = label

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find(**filters):
        db = SessionLocal()
        return db.query(PermissionMatrix).filter_by(**filters).order_by(PermissionMatrix.id.desc()).all()

    @staticmethod
    def find_one(**filters):
        db = SessionLocal()
        return db.query(PermissionMatrix).filter_by(**filters).first()

    @staticmethod
    def find_by_id(permission_id):
        db = SessionLocal()
        return db.query(PermissionMatrix).filter_by(id=permission_id).first()

    @staticmethod
    def update(permission_id, update_values):
        db = SessionLocal()
        permission = db.query(PermissionMatrix).filter_by(id=permission_id).first()
        if permission:
            for key, value in update_values.items():
                setattr(permission, key, value)
            db.commit()
            return True
        return False

    @staticmethod
    def delete(permission_id):
        db = SessionLocal()
        permission = db.query(PermissionMatrix).filter_by(id=permission_id).first()
        if permission:
            db.delete(permission)
            db.commit()
            return True
        return False
