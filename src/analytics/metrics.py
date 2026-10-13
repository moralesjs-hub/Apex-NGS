from typing import Any, Dict, List
import polars as pl
from sqlalchemy.orm import Session
from src.db.models import NGSPassingMetric, NGSRecipientMetric


def calculate_receiver_efficiency(db: Session, min_targets: int = 15) -> List[Dict[str, Any]]:
    """Computes Route Separation Index (RSI) and Cushion Leverage Delta. Uses season totals (week 0) if available."""
    has_week_zero = db.query(NGSRecipientMetric).filter(NGSRecipientMetric.week == 0).first() is not None
    query = db.query(NGSRecipientMetric)
    if has_week_zero:
        query = query.filter(NGSRecipientMetric.week == 0)

    records = query.filter(NGSRecipientMetric.targets >= min_targets).all()

    if not records:
        return []

    data = [
        {
            "player_id": m.player_id,
            "player_name": m.player_name,
            "team": m.team,
            "week": m.week,
            "targets": m.targets,
            "receptions": m.receptions,
            "cushion": float(m.avg_cushion or 0.0),
            "separation": float(m.avg_separation or 0.0),
            "catch_pct": float(m.catch_percentage or 0.0),
            "air_yards": float(m.avg_intended_air_yards or 0.0),
        }
        for m in records
    ]

    df = pl.DataFrame(data)

    df_calc = df.with_columns(
        (
            (pl.col("separation") / (pl.col("cushion") + 0.1))
            * (1.0 + (pl.col("air_yards") / 10.0))
        ).round(3).alias("route_separation_index"),
        (
            pl.col("separation") - pl.col("cushion")
        ).round(3).alias("cushion_delta"),
    )

    return df_calc.to_dicts()


def calculate_qb_pressure_profile(db: Session, min_attempts: int = 15) -> List[Dict[str, Any]]:
    """Computes Pass Rush Risk Profile and Tight Window Aggressiveness. Uses season totals (week 0) if available."""
    has_week_zero = db.query(NGSPassingMetric).filter(NGSPassingMetric.week == 0).first() is not None
    query = db.query(NGSPassingMetric)
    if has_week_zero:
        query = query.filter(NGSPassingMetric.week == 0)

    records = query.filter(NGSPassingMetric.attempts >= min_attempts).all()

    if not records:
        return []

    data = [
        {
            "player_id": m.player_id,
            "player_name": m.player_name,
            "team": m.team,
            "week": m.week,
            "attempts": m.attempts,
            "time_to_throw": float(m.avg_time_to_throw or 0.0),
            "aggressiveness": float(m.aggressiveness_pct or 0.0),
            "cpoe": float(m.completion_pct_over_expected or 0.0),
            "passer_rating": float(m.passer_rating or 0.0),
        }
        for m in records
    ]

    df = pl.DataFrame(data)

    df_calc = df.with_columns(
        (
            (pl.col("time_to_throw") * (pl.col("aggressiveness") / 10.0))
        ).round(3).alias("pressure_risk_index")
    )

    return df_calc.to_dicts()