from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from Models.permission_matrix_model import PermissionMatrix
from database import Base, SessionLocal

class UserPermissionMapping(Base):
    __tablename__ = "user_permission_mapping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_details_id = Column(Integer, ForeignKey("user_details.id"), nullable=True)  
    user_role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=True)       
    permission_id = Column(Integer, ForeignKey("permission_matrix.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __init__(self, permission_id, user_details_id=None, user_role_id=None):
        self.permission_id = permission_id
        self.user_details_id = user_details_id
        self.user_role_id = user_role_id

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find(**filters):
        db = SessionLocal()
        return db.query(UserPermissionMapping).filter_by(**filters).order_by(UserPermissionMapping.id.desc()).all()

    @staticmethod
    def find_one(**filters):
        db = SessionLocal()
        return db.query(UserPermissionMapping).filter_by(**filters).first()

    @staticmethod
    def find_by_id(mapping_id):
        db = SessionLocal()
        return db.query(UserPermissionMapping).filter_by(id=mapping_id).first()

    @staticmethod
    def update(mapping_id, update_values):
        db = SessionLocal()
        mapping = db.query(UserPermissionMapping).filter_by(id=mapping_id).first()
        if mapping:
            for key, value in update_values.items():
                setattr(mapping, key, value)
            db.commit()
            return True
        return False

    @staticmethod
    def delete(mapping_id):
        db = SessionLocal()
        mapping = db.query(UserPermissionMapping).filter_by(id=mapping_id).first()
        if mapping:
            db.delete(mapping)
            db.commit()
            return True
        return False

    @staticmethod
    def get_permissions_for_user(user_details_id, role_id=None):
        """
        Returns a merged list of permissions:
        1. Role-based (default)
        2. User-specific overrides/additional
        """
        db = SessionLocal()

        # Role-based permissions
        role_permissions = []
        if role_id:
            role_permissions = (
                db.query(PermissionMatrix.permission_name, PermissionMatrix.module, PermissionMatrix.crud_action)
                .join(UserPermissionMapping, PermissionMatrix.id == UserPermissionMapping.permission_id)
                .filter(UserPermissionMapping.user_role_id == role_id)
                .all()
            )

        # User-specific permissions
        user_permissions = (
            db.query(PermissionMatrix.permission_name, PermissionMatrix.module, PermissionMatrix.crud_action)
            .join(UserPermissionMapping, PermissionMatrix.id == UserPermissionMapping.permission_id)
            .filter(UserPermissionMapping.user_details_id == user_details_id)
            .all()
        )

        # Merge role and user-specific, avoid duplicates
        merged = { (r[0], r[1], r[2]): r for r in role_permissions + user_permissions }
        return [
            {"permission_name": r[0], "module": r[1], "crud_action": r[2]}
            for r in merged.values()
        ]

    @staticmethod
    def get_permissions_by_role(role_id):
        """
        Return list of permission details for a given user role
        Each permission includes: permission_name, module, crud_action
        """
        db = SessionLocal()
        results = (
            db.query(
                PermissionMatrix.permission_name,
                PermissionMatrix.module,
                PermissionMatrix.crud_action
            )
            .join(UserPermissionMapping, PermissionMatrix.id == UserPermissionMapping.permission_id)
            .filter(UserPermissionMapping.user_role_id == role_id)
            .all()
        )
        # Convert to a structured list of dicts
        return [
            {"permission_name": r[0], "module": r[1], "crud_action": r[2]}
            for r in results
        ] if results else []
