from sqlalchemy import create_engine, Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

from config import Config
from datetime import datetime

engine = create_engine(Config.DATABASE_URI)

Session = sessionmaker(bind=engine)

Base = declarative_base()


class TimestampMixin:
    created_on = Column(DateTime, default=datetime.utcnow)
    updated_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Security(Base, TimestampMixin):
    __tablename__ = 'securities'
    __table_args__ = {'schema': 'stock'}

    ticker = Column(String(5), primary_key=True, unique=True, nullable=False)
    security_name = Column(String(50), nullable=False)
    gics_sector = Column(String(50), nullable=False)
    gics_sub_industry = Column(String(100), nullable=False)
    headquarters_location = Column(String(50), nullable=False)
    date_added = Column(Date, nullable=False)
    cik = Column(Integer, nullable=False)
    year_founded = Column(Integer, nullable=False)


class Price(Base):
    __tablename__ = 'prices'
    __table_args__ = {'schema': 'stock'}

    ticker = Column(String(5), ForeignKey('stock.securities.ticker'), primary_key=True)
    utc_time = Column(DateTime(timezone=True), primary_key=True)
    price = Column(Float, nullable=False)

    security = relationship("Security", backref="prices")