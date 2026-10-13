from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from src.db.session import Base


class NGSRecipientMetric(Base):
    __tablename__ = "ngs_receiving_metrics"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String(50), index=True)
    player_name = Column(String(100), index=True)
    team = Column(String(10), index=True)
    season = Column(Integer, index=True)
    week = Column(Integer, index=True)
    avg_cushion = Column(Float, nullable=True)
    avg_separation = Column(Float, nullable=True)
    avg_intended_air_yards = Column(Float, nullable=True)
    catch_percentage = Column(Float, nullable=True)
    share_of_intended_air_yards = Column(Float, nullable=True)
    targets = Column(Integer, default=0)
    receptions = Column(Integer, default=0)
    yards = Column(Integer, default=0)
    tds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class NGSPassingMetric(Base):
    __tablename__ = "ngs_passing_metrics"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String(50), index=True)
    player_name = Column(String(100), index=True)
    team = Column(String(10), index=True)
    season = Column(Integer, index=True)
    week = Column(Integer, index=True)
    avg_time_to_throw = Column(Float, nullable=True)
    avg_completed_air_yards = Column(Float, nullable=True)
    avg_intended_air_yards = Column(Float, nullable=True)
    aggressiveness_pct = Column(Float, nullable=True)
    expected_completion_pct = Column(Float, nullable=True)
    completion_pct_over_expected = Column(Float, nullable=True)
    passer_rating = Column(Float, nullable=True)
    attempts = Column(Integer, default=0)
    completions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScoutingDossier(Base):
    __tablename__ = "scouting_dossiers"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String(50), index=True)
    player_name = Column(String(100))
    season = Column(Integer)
    dossier_text = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)