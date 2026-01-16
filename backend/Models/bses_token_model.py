# from datetime import datetime
# from database import Database
# from pymongo.collection import Collection
# from bson.objectid import ObjectId

# db = Database()

# class BSES_Token:
#     collection: Collection = db.get_collection('bses_token')

#     def __init__(self, bses_jwt_token=None, bses_jwt_token_expiry=None, bses_delhiv2_token=None, bses_delhiv2_token_expiry=None):
#         self.bses_jwt_token = bses_jwt_token
#         self.bses_jwt_token_expiry = bses_jwt_token_expiry
#         self.bses_delhiv2_token = bses_delhiv2_token
#         self.bses_delhiv2_token_expiry = bses_delhiv2_token_expiry
#         self.created_at = datetime.utcnow()
#         self.updated_at = datetime.utcnow()

#     def save(self):
        
#         user_dict = {key: value for key, value in self.__dict__.items() if value is not None}
#         # user_dict = self.__dict__
#         result = self.collection.insert_one(user_dict)
#         return result.inserted_id

#     @staticmethod
#     def find(query, personalization=None):
#         return BSES_Token.collection.find(query,personalization)

#     @staticmethod
#     def find_one(query, projection=None):
#         return BSES_Token.collection.find_one(query,projection)

#     @staticmethod
#     def update(query, update_values):
#         update_values['updated_at'] = datetime.utcnow()
#         return BSES_Token.collection.update_one(query, {'$set': update_values})

#     @staticmethod
#     def find_by_user_id(user_id):
#         return BSES_Token.collection.find_one({"_id": ObjectId(user_id)},{"password": 0})
    
#     @staticmethod
#     def delete(query):
#         return BSES_Token.collection.delete_one(query)

#     @staticmethod
#     def update_one(filter_query, update_query):
#         try:
#             print(filter_query,'----------------------',update_query,'++++++++++++++++++++++++++++++++++')
#             result = BSES_Token.collection.update_one(filter_query, update_query)
#             return result.modified_count > 0
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             return False


from sqlalchemy import Column, String, DateTime
from database import Base, SessionLocal
from datetime import datetime
import uuid

class BSES_Token(Base):
    __tablename__ = "bses_token"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bses_jwt_token = Column(String, nullable=True)
    bses_jwt_token_expiry = Column(DateTime, nullable=True)
    bses_delhiv2_token = Column(String, nullable=True)
    bses_delhiv2_token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        db = SessionLocal()
        return db.query(BSES_Token).filter_by(**kwargs).first()

    @staticmethod
    def update(filter_query, update_values):
        db = SessionLocal()
        token = db.query(BSES_Token).filter_by(**filter_query).first()
        if token:
            for k, v in update_values.items():
                setattr(token, k, v)
            token.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False

    @staticmethod
    def update_one(filter_query, update_query):
        db = SessionLocal()
        session = db.query(BSES_Token).filter_by(**filter_query).first()
        if session:
            if "$push" in update_query:  # emulate Mongo's $push
                if not session.chat:
                    session.chat = []
                session.chat.append(update_query["$push"]["chat"])
            if "$set" in update_query:
                for k, v in update_query["$set"].items():
                    setattr(session, k, v)
            session.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False