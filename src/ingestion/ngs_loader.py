import nfl_data_py as nfl
import pandas as pd
from sqlalchemy.orm import Session
from src.db.models import NGSPassingMetric, NGSRecipientMetric
from src.db.session import SessionLocal, init_db


def safe_float(val, default=0.0):
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val, default=0):
    if val is None or pd.isna(val):
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def ingest_receiving_ngs(season: int = 2024, db: Session = None):
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        print(f"--> [1/2] Fetching {season} NGS receiving data...", flush=True)
        df = nfl.import_ngs_data(stat_type="receiving", years=[season])

        if df is None or df.empty:
            print(f"No receiving data returned for {season}.", flush=True)
            return 0

        db.query(NGSRecipientMetric).filter(NGSRecipientMetric.season == season).delete()

        records = []
        for _, row in df.iterrows():
            player_id = str(row.get("player_gsis_id") or row.get("player_id") or "UNKNOWN")
            player_name = str(row.get("player_display_name") or "Unknown")
            team = str(row.get("team_abbr") or "FA")
            week = safe_int(row.get("week"), 0)

            metric = NGSRecipientMetric(
                player_id=player_id,
                player_name=player_name,
                team=team,
                season=season,
                week=week,
                avg_cushion=safe_float(row.get("avg_cushion")),
                avg_separation=safe_float(row.get("avg_separation")),
                avg_intended_air_yards=safe_float(row.get("avg_intended_air_yards")),
                catch_percentage=safe_float(row.get("catch_percentage")),
                share_of_intended_air_yards=safe_float(row.get("percent_share_of_intended_air_yards")),
                targets=safe_int(row.get("targets")),
                receptions=safe_int(row.get("receptions")),
                yards=safe_int(row.get("yards")),
                tds=safe_int(row.get("rec_touchdowns")),
            )
            records.append(metric)

        db.bulk_save_objects(records)
        db.commit()
        print(f"--> Ingested {len(records)} receiving records for {season}.", flush=True)
        return len(records)
    except Exception as e:
        db.rollback()
        print(f"Error ingesting receiving data: {e}", flush=True)
        raise
    finally:
        if close_session:
            db.close()


def ingest_passing_ngs(season: int = 2024, db: Session = None):
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        print(f"--> [2/2] Fetching {season} NGS passing data...", flush=True)
        df = nfl.import_ngs_data(stat_type="passing", years=[season])

        if df is None or df.empty:
            print(f"No passing data returned for {season}.", flush=True)
            return 0

        db.query(NGSPassingMetric).filter(NGSPassingMetric.season == season).delete()

        records = []
        for _, row in df.iterrows():
            player_id = str(row.get("player_gsis_id") or row.get("player_id") or "UNKNOWN")
            player_name = str(row.get("player_display_name") or "Unknown")
            team = str(row.get("team_abbr") or "FA")
            week = safe_int(row.get("week"), 0)

            metric = NGSPassingMetric(
                player_id=player_id,
                player_name=player_name,
                team=team,
                season=season,
                week=week,
                avg_time_to_throw=safe_float(row.get("avg_time_to_throw")),
                avg_completed_air_yards=safe_float(row.get("avg_completed_air_yards")),
                avg_intended_air_yards=safe_float(row.get("avg_intended_air_yards")),
                aggressiveness_pct=safe_float(row.get("aggressiveness")),
                expected_completion_pct=safe_float(row.get("expected_completion_percentage")),
                completion_pct_over_expected=safe_float(row.get("completion_percentage_above_expectation")),
                passer_rating=safe_float(row.get("passer_rating")),
                attempts=safe_int(row.get("attempts")),
                completions=safe_int(row.get("completions")),
            )
            records.append(metric)

        db.bulk_save_objects(records)
        db.commit()
        print(f"--> Ingested {len(records)} passing records for {season}.", flush=True)
        return len(records)
    except Exception as e:
        db.rollback()
        print(f"Error ingesting passing data: {e}", flush=True)
        raise
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    init_db()
    ingest_receiving_ngs(2024)
    ingest_passing_ngs(2024)
    print("Ingestion pipeline finished successfully!", flush=True)