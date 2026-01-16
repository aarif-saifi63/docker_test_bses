from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from database import Base, SessionLocal
from sqlalchemy.dialects.postgresql import ARRAY



class IntentV(Base):
    __tablename__ = "intent_v"

    id = Column(Integer, primary_key=True)
    # submenu_id = Column(ARRAY(Integer), nullable=False)  # list of submenu IDs
    submenu_id = Column(ARRAY(Integer), nullable=True)  # ✅ FIXED
    name = Column(String, nullable=False)

    # ✅ Relationship to examples (with cascade)
    examples = relationship(
        "IntentExampleV",
        back_populates="intent",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # ✅ Manual relationship to SubMenuOptionV
    submenus = relationship(
        "SubMenuOptionV",
        primaryjoin="foreign(SubMenuOptionV.id) == any_(IntentV.submenu_id)",
        viewonly=True
    )

    def save(self):
        """
        Save the intent instance to the database.
        """
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    # @staticmethod
    # def find_one(**kwargs):
    #     """
    #     Find a single intent record by filters.
    #     Example: IntentV.find_one(name="billing_inquiry")
    #     """
    #     db = SessionLocal()
    #     return db.query(IntentV).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update an intent record based on filter and update queries.
        Example:
            IntentV.update_one(
                {"id": 1},
                {"name": "updated_billing_inquiry"}
            )
        """
        db = SessionLocal()
        session = db.query(IntentV).filter_by(**filter_query).first()
        if session:
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            db.commit()
            db.refresh(session)
            return True
        return False
    
    @staticmethod
    def find(search=None, page=1, limit=10):
        with SessionLocal() as db:
            query = db.query(IntentV)
            if search:
                query = query.filter(IntentV.name.ilike(f"%{search}%"))
            total = query.count()
            results = query.order_by(IntentV.id.desc()).offset((page - 1) * limit).limit(limit).all()
            return results, total

    @staticmethod
    def find_one(**kwargs):
        with SessionLocal() as db:
            return db.query(IntentV).filter_by(**kwargs).first()

    @staticmethod
    def find_by_id(intent_id):
        with SessionLocal() as db:
            return db.query(IntentV).filter_by(id=intent_id).first()

    @staticmethod
    def update(intent_id, update_values):
        with SessionLocal() as db:
            intent = db.query(IntentV).filter_by(id=intent_id).first()
            if intent:
                for key, value in update_values.items():
                    setattr(intent, key, value)
                db.commit()
                return True
            return False

    @staticmethod
    def delete(intent_id):
        with SessionLocal() as db:
            intent = db.query(IntentV).filter_by(id=intent_id).first()
            if intent:
                db.delete(intent)
                db.commit()
                return True
            return False
