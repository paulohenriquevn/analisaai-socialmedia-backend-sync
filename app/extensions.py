from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from app.config.database import Base

# Create a db object to mimic Flask-SQLAlchemy's db.Model
class DB:
    Model = Base
    Column = Column
    Integer = Integer
    String = String
    Boolean = Boolean
    DateTime = DateTime
    ForeignKey = ForeignKey
    Table = Table
    relationship = relationship
    backref = backref

# Export db object
db = DB