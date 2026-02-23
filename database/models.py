from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), index=True)
    description = Column(String(100))
    subtasks = Column(String(500) ) 