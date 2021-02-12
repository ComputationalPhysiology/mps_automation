from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import backref, relationship

Base: DeclarativeMeta = declarative_base()


class Recording(Base):
    __tablename__ = "recording"
    id = Column(Integer, primary_key=True)
    value = Column(String, unique=True)  # path
    drug_id = Column(Integer, ForeignKey("drug.id"), nullable=True)
    dose_id = Column(Integer, ForeignKey("dose.id"), nullable=True)
    chip_id = Column(Integer, ForeignKey("chip.id"), nullable=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=True)
    pacing_id = Column(Integer, ForeignKey("pacing.id"), nullable=True)
    trace_type_id = Column(Integer, ForeignKey("trace_type.id"), nullable=True)
    analysis = Column(JSON, nullable=False, default={})


class Drug(Base):
    __tablename__ = "drug"
    id = Column(Integer, primary_key=True)
    value = Column(String)
    doses = relationship("Dose", backref=backref("drug"))
    recordings = relationship("Recording", backref=backref("drug"))


class Dose(Base):
    __tablename__ = "dose"
    id = Column(Integer, primary_key=True)
    value = Column(String)
    concentration = Column(String, nullable=True)
    drug_id = Column(Integer, ForeignKey("drug.id"), nullable=True)
    recordings = relationship("Recording", backref=backref("dose"))


class Pacing(Base):
    __tablename__ = "pacing"
    id = Column(Integer, primary_key=True)
    value = Column(String)
    recordings = relationship("Recording", backref=backref("pacing"))


class TraceType(Base):
    __tablename__ = "trace_type"
    id = Column(Integer, primary_key=True)
    value = Column(String)
    recordings = relationship("Recording", backref=backref("trace_type"))


class Chip(Base):
    __tablename__ = "chip"
    id = Column(Integer, primary_key=True)
    value = Column(String)
    recordings = relationship("Recording", backref=backref("chip"))


class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True)
    value = Column(String)
    recordings = relationship("Recording", backref=backref("media"))
