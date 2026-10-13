import sys
from src.agents.scouting_writer import ScoutingAgent
from src.analytics.metrics import (
    calculate_qb_pressure_profile,
    calculate_receiver_efficiency,
)
from src.db.models import ScoutingDossier
from src.db.session import SessionLocal


def seed():
    print("\n=== POPULATING NEON PGVECTOR SCOUTING INDEX ===", flush=True)
    db = SessionLocal()
    agent = ScoutingAgent()

    receivers = calculate_receiver_efficiency(db=db, min_targets=15)[:6]
    qbs = calculate_qb_pressure_profile(db=db, min_attempts=20)[:4]

    total = len(receivers) + len(qbs)
    print(f"Targeting {len(receivers)} WRs and {len(qbs)} QBs ({total} total)...\n", flush=True)

    count = 0

    # Index Receivers
    for r in receivers:
        name = r["player_name"]
        team = r["team"]
        profile_text = (
            f"Tactical Scouting Profile: {name} ({team}). Position: Wide Receiver. "
            f"Tracking Metrics: Separation {r['separation']:.2f} yds, Cushion {r['cushion']:.2f} yds, "
            f"Route Separation Index {r['route_separation_index']:.2f}, Intended Air Yards {r['air_yards']:.1f} yds, "
            f"Catch Rate {r['catch_pct']:.1f}%, Targets {r['targets']}. "
            f"Archetype: {'Speedy downfield vertical burner with elite acceleration and deep burst' if r['air_yards'] > 11.0 else 'High-volume separation technician winning with sharp route cuts against press coverage'}. "
            f"Coverage Vulnerability: Requires deep safety bracket or aggressive press re-route."
        )

        print(f"[{count + 1}/{total}] Embedding WR: {name} ({team})...", end=" ", flush=True)
        vec = agent.embed_text(profile_text)
        if vec:
            db.query(ScoutingDossier).filter(ScoutingDossier.player_id == r["player_id"]).delete()
            dossier = ScoutingDossier(
                player_id=r["player_id"],
                player_name=name,
                season=2024,
                dossier_text=profile_text,
                embedding=vec,
            )
            db.add(dossier)
            db.commit()
            count += 1
            print(f"SAVED ({len(vec)} dims)")
        else:
            print("FAILED (no embedding returned)")

    # Index QBs
    for q in qbs:
        name = q["player_name"]
        team = q["team"]
        profile_text = (
            f"Tactical Scouting Profile: {name} ({team}). Position: Quarterback. "
            f"Tracking Metrics: Time to Throw {q['time_to_throw']:.2f}s, Tight Window Aggressiveness {q['aggressiveness']:.1f}%, "
            f"Passer Rating {q['passer_rating']:.1f}, CPOE {q['cpoe']:.1f}%, Pressure Risk Index {q['pressure_risk_index']:.2f}. "
            f"Archetype: {'Deliberate pocket passer who holds football and attacks intermediate windows' if q['time_to_throw'] > 2.7 else 'Rapid rhythm distributor getting ball out under 2.5 seconds'}. "
            f"Blitz Mandate: {'Deploy sim pressures and contain stunts' if q['pressure_risk_index'] > 3.5 else 'Drop seven into zone coverage and take away first read'}."
        )

        print(f"[{count + 1}/{total}] Embedding QB: {name} ({team})...", end=" ", flush=True)
        vec = agent.embed_text(profile_text)
        if vec:
            db.query(ScoutingDossier).filter(ScoutingDossier.player_id == q["player_id"]).delete()
            dossier = ScoutingDossier(
                player_id=q["player_id"],
                player_name=name,
                season=2024,
                dossier_text=profile_text,
                embedding=vec,
            )
            db.add(dossier)
            db.commit()
            count += 1
            print(f"SAVED ({len(vec)} dims)")
        else:
            print("FAILED (no embedding returned)")

    db.close()
    print(f"\nCompleted! {count}/{total} players indexed into Neon pgvector.\n", flush=True)


if __name__ == "__main__":
    seed()