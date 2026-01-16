from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from database import Base, SessionLocal
from sqlalchemy.orm import relationship



class SubMenuOptionV(Base):
    __tablename__ = "sub_menu_option_v"

    id = Column(Integer, primary_key=True)
    menu_id = Column(Integer, ForeignKey("menu_option_v.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    lang = Column(String)
    is_visible = Column(Boolean, default=True)
    icon_path = Column(String, nullable=True)
    submenu_sequence = Column(Integer)  

    menu = relationship("MenuOptionV", back_populates="submenus")


    actions = relationship("ActionsV", back_populates="submenu", cascade="all, delete-orphan", passive_deletes=True)
    utters = relationship("UtterV", back_populates="submenu", cascade="all, delete-orphan", passive_deletes=True)
    stories = relationship("Story", back_populates="submenu", cascade="all, delete-orphan", passive_deletes=True)


    # ✅ Intents (ARRAY join, viewonly)
    intents = relationship(
        "IntentV",
        primaryjoin="foreign(SubMenuOptionV.id) == any_(IntentV.submenu_id)",
        viewonly=True
    )

    def save(self):
        """
        Save the sub-menu option instance to the database.
        """
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        """
        Find a single sub-menu option record by filters.
        Example: SubMenuOptionV.find_one(name="Pay Bill", menu_id=1)
        """
        db = SessionLocal()
        return db.query(SubMenuOptionV).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        """
        Update a sub-menu option record based on filter and update queries.
        Example:
            SubMenuOptionV.update_one(
                {"id": 1},
                {"is_visible": False}
            )
        """
        db = SessionLocal()
        session = db.query(SubMenuOptionV).filter_by(**filter_query).first()
        if session:
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            db.commit()
            db.refresh(session)
            return True
        return False
    

    @classmethod
    def find_by_ids(cls, ids):
        if not ids:
            return []
        # Flatten nested arrays
        if len(ids) == 1 and isinstance(ids[0], (list, tuple)):
            ids = ids[0]
        ids = [int(i) for i in ids if i is not None]

        db = SessionLocal()
        try:
            return db.query(cls).filter(cls.id.in_(ids)).all()
        finally:
            db.close()





