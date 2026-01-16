
# from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
# from database import Base, SessionLocal
# from datetime import datetime
# import pytz

# IST = pytz.timezone("Asia/Kolkata")

# def current_time_ist():
#     return datetime.now(IST)

# class IntentExample(Base):
#     __tablename__ = "intent_examples_v"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     intent_id = Column(Integer, ForeignKey("intent_v.id"), nullable=False)
#     example = Column(String(255), nullable=False)
#     created_at = Column(DateTime, default=current_time_ist)
#     updated_at = Column(DateTime, default=current_time_ist, onupdate=current_time_ist)

#     def save(self):
#         with SessionLocal() as db:
#             db.add(self)
#             db.commit()
#             db.refresh(self)
#             return self.id

#     @staticmethod
#     def find_by_intent(intent_id):
#         with SessionLocal() as db:
#             return db.query(IntentExample).filter_by(intent_id=intent_id).all()

#     @staticmethod
#     def find_one(example_id):
#         with SessionLocal() as db:
#             return db.query(IntentExample).filter_by(id=example_id).first()

#     @staticmethod
#     def update(example_id, update_values):
#         with SessionLocal() as db:
#             example = db.query(IntentExample).filter_by(id=example_id).first()
#             if example:
#                 for key, value in update_values.items():
#                     setattr(example, key, value)
#                 example.updated_at = current_time_ist()
#                 db.commit()
#                 return True
#             return False

#     @staticmethod
#     def delete(example_id):
#         with SessionLocal() as db:
#             example = db.query(IntentExample).filter_by(id=example_id).first()
#             if example:
#                 db.delete(example)
#                 db.commit()
#                 return True
#             return False

#     @staticmethod
#     def delete_by_intent(intent_id):
#         with SessionLocal() as db:
#             db.query(IntentExample).filter_by(intent_id=intent_id).delete()
#             db.commit()
