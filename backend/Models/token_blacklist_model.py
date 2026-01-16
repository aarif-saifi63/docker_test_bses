from sqlalchemy import Column, Integer, Text, DateTime
from database import Base

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<TokenBlacklist id={self.id} expires_at={self.expires_at}>"
