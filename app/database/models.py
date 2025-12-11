from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, JSON, Boolean
from app.database.db import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    recurrence_type = Column(String, nullable=False)
    time_to_send = Column(String, nullable=False)
    days_of_week = Column(JSON, nullable=True)
    day_of_month = Column(Integer, nullable=True)
    specific_datetime = Column(DateTime, nullable=True)
    delivery_method = Column(String, default="telegram")
    contact = Column(String, nullable=True)
    active = Column(Boolean, default=True)

class Help(Base):
    __tablename__ = "help"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    text = Column(Text, nullable=False)
    recurrence_type = Column(String, nullable=False) 
    contact = Column(String, nullable=True)