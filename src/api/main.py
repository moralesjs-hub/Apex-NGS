from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.agents.scouting_writer import ScoutingAgent
from src.analytics.matchups import simulate_coverage_matchups
from src.analytics.metrics import (
    calculate_qb_pressure_profile,
    calculate_receiver_efficiency,
)
from src.db.models import NGSPassingMetric, NGSRecipientMetric, ScoutingDossier
from src.db.session import get_db
from src.services.pdf_report import generate_scouting_pdf

app = FastAPI(
    title="Apex-NGS Analytics Core",
    description="NFL Next Gen Stats Spatial Tracking & AI Scouting Intelligence Gateway",
    version="1.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_agent() -> ScoutingAgent:
    return ScoutingAgent()


class DossierResponse(BaseModel):
    player_id: str
    player_name: str
    position_type: str
    dossier: str
    indexed: bool


class SearchQuery(BaseModel):
    query: str
    limit: int = 5


@app.get("/health")
def health_check():
    return {"status": "online", "system": "Apex-NGS Core"}


@app.get("/api/analytics/receivers")
def get_receivers(min_targets: int = 15, db: Session = Depends(get_db)):
    results = calculate_receiver_efficiency(db=db, min_targets=min_targets)
    return {"count": len(results), "data": results}


@app.get("/api/analytics/qbs")
def get_qbs(min_attempts: int = 20, db: Session = Depends(get_db)):
    results = calculate_qb_pressure_profile(db=db, min_attempts=min_attempts)
    return {"count": len(results), "data": results}


@app.get("/api/analytics/player-percentiles/{player_id}")
def get_player_percentiles(player_id: str, db: Session = Depends(get_db)):
    """Computes percentile rankings across position cohort (WR or QB)."""
    receivers = calculate_receiver_efficiency(db=db, min_targets=15)
    matched_rec = next((r for r in receivers if str(r["player_id"]) == str(player_id)), None)

    if matched_rec:
        keys = ["separation", "cushion", "route_separation_index", "catch_pct", "air_yards"]
        categories = ["Separation", "Pre-Snap Cushion", "Route Sep Index", "Catch %", "Air Yards"]
        percentiles = {}
        for k in keys:
            values = sorted([float(r[k]) for r in receivers])
            val = float(matched_rec[k])
            rank = sum(1 for v in values if v <= val)
            percentiles[k] = round((rank / len(values)) * 100, 1)

        return {
            "player_id": matched_rec["player_id"],
            "player_name": matched_rec["player_name"],
            "team": matched_rec["team"],
            "position": "WR/TE",
            "categories": categories,
            "keys": keys,
            "percentiles": percentiles,
            "raw": matched_rec,
        }

    qbs = calculate_qb_pressure_profile(db=db, min_attempts=20)
    matched_qb = next((q for q in qbs if str(q["player_id"]) == str(player_id)), None)

    if matched_qb:
        keys = ["time_to_throw", "aggressiveness", "cpoe", "passer_rating", "pressure_risk_index"]
        categories = ["Time to Throw", "Aggressiveness %", "CPOE", "Passer Rating", "Pressure Risk"]
        percentiles = {}
        for k in keys:
            values = sorted([float(q[k]) for q in qbs])
            val = float(matched_qb[k])
            rank = sum(1 for v in values if v <= val)
            percentiles[k] = round((rank / len(values)) * 100, 1)

        return {
            "player_id": matched_qb["player_id"],
            "player_name": matched_qb["player_name"],
            "team": matched_qb["team"],
            "position": "QB",
            "categories": categories,
            "keys": keys,
            "percentiles": percentiles,
            "raw": matched_qb,
        }

    raise HTTPException(status_code=404, detail="Player not found in active cohort.")


@app.get("/api/analytics/matchup-simulation/{player_id}")
def get_matchup_simulation(player_id: str, db: Session = Depends(get_db)):
    """Simulates coverage scheme matchup metrics for a receiver."""
    simulation = simulate_coverage_matchups(player_id=player_id, db=db)
    if "error" in simulation:
        raise HTTPException(status_code=404, detail=simulation["error"])
    return simulation


@app.get("/api/scout/export-pdf/{player_id}")
def export_scouting_packet_pdf(player_id: str, db: Session = Depends(get_db)):
    """Generates and returns an executive 2-page PDF scouting report."""
    receivers = calculate_receiver_efficiency(db=db, min_targets=5)
    matched = next((r for r in receivers if str(r["player_id"]) == str(player_id)), None)

    if not matched:
        record = (
            db.query(NGSRecipientMetric)
            .filter(NGSRecipientMetric.player_id == str(player_id))
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Player metrics not found.")
        matched = {
            "player_id": record.player_id,
            "player_name": record.player_name,
            "team": record.team,
            "cushion": float(record.avg_cushion or 0.0),
            "separation": float(record.avg_separation or 0.0),
            "route_separation_index": round(
                (float(record.avg_separation or 0.0) / (float(record.avg_cushion or 0.0) + 0.1)), 2
            ),
            "air_yards": float(record.avg_intended_air_yards or 0.0),
            "catch_pct": float(record.catch_percentage or 0.0),
            "targets": int(record.targets or 0),
        }

    sim_res = simulate_coverage_matchups(player_id=player_id, db=db)
    dossier_record = db.query(ScoutingDossier).filter(ScoutingDossier.player_id == str(player_id)).first()

    if dossier_record and dossier_record.dossier_text:
        dossier_text = dossier_record.dossier_text
    else:
        agent = get_agent()
        dossier_text = agent.generate_receiver_dossier(player_name=matched["player_name"], metrics=matched)

    pdf_buffer = generate_scouting_pdf(
        player_data=matched,
        schemes_data=sim_res.get("schemes", []),
        dossier_text=dossier_text,
    )

    clean_name = matched["player_name"].replace(" ", "_")
    filename = f"Scouting_Dossier_{clean_name}.pdf"

    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/scout/receiver/{player_id}", response_model=DossierResponse)
def scout_receiver(player_id: str, db: Session = Depends(get_db)):
    metrics_list = calculate_receiver_efficiency(db=db, min_targets=5)
    matched = next((m for m in metrics_list if str(m["player_id"]) == str(player_id)), None)

    if not matched:
        record = (
            db.query(NGSRecipientMetric)
            .filter(NGSRecipientMetric.player_id == str(player_id))
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="Receiver not found.")
        matched = {
            "player_id": record.player_id,
            "player_name": record.player_name,
            "cushion": float(record.avg_cushion or 0.0),
            "separation": float(record.avg_separation or 0.0),
            "route_separation_index": round(
                (float(record.avg_separation or 0.0) / (float(record.avg_cushion or 0.0) + 0.1)), 2
            ),
            "cushion_delta": round(
                (float(record.avg_separation or 0.0) - float(record.avg_cushion or 0.0)), 2
            ),
            "catch_pct": float(record.catch_percentage or 0.0),
            "air_yards": float(record.avg_intended_air_yards or 0.0),
            "targets": int(record.targets or 0),
        }

    agent = get_agent()
    dossier_text = agent.generate_receiver_dossier(
        player_name=matched["player_name"], metrics=matched
    )
    vector = agent.embed_text(dossier_text)

    db.query(ScoutingDossier).filter(ScoutingDossier.player_id == matched["player_id"]).delete()
    saved = ScoutingDossier(
        player_id=matched["player_id"],
        player_name=matched["player_name"],
        season=2024,
        dossier_text=dossier_text,
        embedding=vector if vector else None,
    )
    db.add(saved)
    db.commit()

    return DossierResponse(
        player_id=matched["player_id"],
        player_name=matched["player_name"],
        position_type="WR/TE",
        dossier=dossier_text,
        indexed=bool(vector),
    )


@app.post("/api/scout/qb/{player_id}", response_model=DossierResponse)
def scout_qb(player_id: str, db: Session = Depends(get_db)):
    metrics_list = calculate_qb_pressure_profile(db=db, min_attempts=5)
    matched = next((m for m in metrics_list if str(m["player_id"]) == str(player_id)), None)

    if not matched:
        record = (
            db.query(NGSPassingMetric)
            .filter(NGSPassingMetric.player_id == str(player_id))
            .first()
        )
        if not record:
            raise HTTPException(status_code=404, detail="QB not found.")
        matched = {
            "player_id": record.player_id,
            "player_name": record.player_name,
            "time_to_throw": float(record.avg_time_to_throw or 0.0),
            "aggressiveness": float(record.aggressiveness_pct or 0.0),
            "cpoe": float(record.completion_pct_over_expected or 0.0),
            "passer_rating": float(record.passer_rating or 0.0),
            "pressure_risk_index": round(
                (float(record.avg_time_to_throw or 0.0) * (float(record.aggressiveness_pct or 0.0) / 10.0)), 2
            ),
        }

    agent = get_agent()
    dossier_text = agent.generate_qb_pressure_dossier(
        player_name=matched["player_name"], metrics=matched
    )
    vector = agent.embed_text(dossier_text)

    db.query(ScoutingDossier).filter(ScoutingDossier.player_id == matched["player_id"]).delete()
    saved = ScoutingDossier(
        player_id=matched["player_id"],
        player_name=matched["player_name"],
        season=2024,
        dossier_text=dossier_text,
        embedding=vector if vector else None,
    )
    db.add(saved)
    db.commit()

    return DossierResponse(
        player_id=matched["player_id"],
        player_name=matched["player_name"],
        position_type="QB",
        dossier=dossier_text,
        indexed=bool(vector),
    )


@app.post("/api/scout/batch-index")
def batch_index_leaders(db: Session = Depends(get_db)):
    """Indexes top 6 WRs and 4 QBs with immediate commit per player."""
    agent = get_agent()
    receivers = calculate_receiver_efficiency(db=db, min_targets=15)[:6]
    qbs = calculate_qb_pressure_profile(db=db, min_attempts=20)[:4]

    indexed_count = 0

    for r in receivers:
        profile_text = (
            f"Tactical Scouting Profile: {r['player_name']} ({r['team']}). Position: Wide Receiver. "
            f"Tracking Metrics: Separation {r['separation']:.2f} yds, Cushion {r['cushion']:.2f} yds, "
            f"Route Separation Index {r['route_separation_index']:.2f}, Intended Air Yards {r['air_yards']:.1f} yds, "
            f"Catch Rate {r['catch_pct']:.1f}%, Targets {r['targets']}. "
            f"Archetype: {'Speedy downfield vertical burner with elite acceleration and deep burst' if r['air_yards'] > 11.0 else 'High-volume separation technician winning with sharp route cuts against press coverage'}."
        )
        vec = agent.embed_text(profile_text)
        if vec:
            db.query(ScoutingDossier).filter(ScoutingDossier.player_id == r["player_id"]).delete()
            db.add(
                ScoutingDossier(
                    player_id=r["player_id"],
                    player_name=r["player_name"],
                    season=2024,
                    dossier_text=profile_text,
                    embedding=vec,
                )
            )
            db.commit()
            indexed_count += 1

    for q in qbs:
        profile_text = (
            f"Tactical Scouting Profile: {q['player_name']} ({q['team']}). Position: Quarterback. "
            f"Tracking Metrics: Time to Throw {q['time_to_throw']:.2f}s, Tight Window Aggressiveness {q['aggressiveness']:.1f}%, "
            f"Passer Rating {q['passer_rating']:.1f}, CPOE {q['cpoe']:.1f}%, Pressure Risk Index {q['pressure_risk_index']:.2f}. "
            f"Archetype: {'Deliberate pocket passer who holds football and attacks intermediate windows' if q['time_to_throw'] > 2.7 else 'Rapid rhythm distributor getting ball out under 2.5 seconds'}."
        )
        vec = agent.embed_text(profile_text)
        if vec:
            db.query(ScoutingDossier).filter(ScoutingDossier.player_id == q["player_id"]).delete()
            db.add(
                ScoutingDossier(
                    player_id=q["player_id"],
                    player_name=q["player_name"],
                    season=2024,
                    dossier_text=profile_text,
                    embedding=vec,
                )
            )
            db.commit()
            indexed_count += 1

    return {"status": "complete", "indexed_count": indexed_count}


@app.post("/api/analytics/semantic-search")
def semantic_search(payload: SearchQuery, db: Session = Depends(get_db)):
    """Executes pgvector cosine distance search natively using SQLAlchemy pgvector operator."""
    agent = get_agent()
    query_vector = agent.embed_text(payload.query)

    if not query_vector:
        raise HTTPException(status_code=400, detail="Failed to compute embedding for query.")

    total_indexed = (
        db.query(ScoutingDossier)
        .filter(ScoutingDossier.embedding.is_not(None))
        .count()
    )
    if total_indexed == 0:
        return {"results": [], "total_indexed": 0}

    dist_expr = ScoutingDossier.embedding.cosine_distance(query_vector)

    matches = (
        db.query(ScoutingDossier, dist_expr.label("distance"))
        .filter(ScoutingDossier.embedding.is_not(None))
        .order_by(dist_expr.asc())
        .limit(payload.limit)
        .all()
    )

    results = []
    for dossier, distance in matches:
        dist_val = float(distance) if distance is not None else 1.0
        similarity = max(0.0, 1.0 - dist_val)
        results.append({
            "player_id": dossier.player_id,
            "player_name": dossier.player_name,
            "season": dossier.season,
            "dossier": dossier.dossier_text,
            "similarity_score": round(similarity, 3),
        })

    return {"results": results, "total_indexed": total_indexed}