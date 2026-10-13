from typing import Any, Dict, List
from sqlalchemy.orm import Session
from src.analytics.metrics import calculate_receiver_efficiency
from src.db.models import NGSRecipientMetric


def simulate_coverage_matchups(player_id: str, db: Session) -> Dict[str, Any]:
    """Simulates receiver separation and route win probability against NFL defensive coverages."""
    receivers = calculate_receiver_efficiency(db=db, min_targets=5)
    matched = next((r for r in receivers if str(r["player_id"]) == str(player_id)), None)

    if not matched:
        record = (
            db.query(NGSRecipientMetric)
            .filter(NGSRecipientMetric.player_id == str(player_id))
            .first()
        )
        if not record:
            return {"error": "Player not found"}
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

    cushion = float(matched["cushion"])
    separation = float(matched["separation"])
    air_yards = float(matched["air_yards"])
    rsi = float(matched["route_separation_index"])

    # 1. Cover 1 (Press-Man)
    c1_mult = 1.20 if (cushion < 5.5 and separation >= 2.8) else (0.80 if cushion >= 6.5 else 0.94)
    c1_sep = round(separation * c1_mult, 2)
    c1_win = round(min(97.0, max(25.0, (c1_sep / 3.0) * 65.0 + (rsi * 7.5))), 1)

    # 2. Cover 2 (Two-High Zone / Cloud)
    c2_mult = 1.16 if (air_yards < 10.0 and separation >= 3.0) else (0.76 if air_yards > 13.0 else 0.90)
    c2_sep = round(separation * c2_mult, 2)
    c2_win = round(min(97.0, max(25.0, (c2_sep / 3.0) * 60.0 + (5.0 if air_yards < 10 else -10.0))), 1)

    # 3. Cover 3 (Single-High Deep Thirds)
    c3_mult = 1.18 if (air_yards >= 11.5 and rsi >= 1.2) else (0.86 if air_yards < 7.0 else 0.98)
    c3_sep = round(separation * c3_mult, 2)
    c3_win = round(min(97.0, max(25.0, (c3_sep / 3.0) * 62.0 + (rsi * 6.5))), 1)

    # 4. Cover 4 (Quarters / Match)
    c4_mult = 1.14 if rsi >= 1.4 else (0.78 if separation < 2.5 else 0.88)
    c4_sep = round(separation * c4_mult, 2)
    c4_win = round(min(97.0, max(25.0, (c4_sep / 3.0) * 60.0 + (rsi * 8.5))), 1)

    # 5. Cover 6 (Split Field Quarter-Quarter-Half)
    c6_mult = 1.10 if (separation >= 3.0 and rsi >= 1.1) else 0.86
    c6_sep = round(separation * c6_mult, 2)
    c6_win = round(min(97.0, max(25.0, (c6_sep / 3.0) * 61.0)), 1)

    schemes = [
        {
            "scheme": "Cover 1 (Press-Man)",
            "projected_separation": c1_sep,
            "baseline_diff": round(c1_sep - separation, 2),
            "win_rate": c1_win,
            "leverage_rating": "OFFENSIVE ADVANTAGE" if c1_win >= 65 else ("NEUTRAL" if c1_win >= 50 else "DEFENSIVE LOCKDOWN"),
            "coaching_mandate": "Punishes single coverage on isolated boundary stems." if c1_win >= 65 else "Jam at LOS to disrupt release timing; vulnerable to physical press.",
        },
        {
            "scheme": "Cover 2 (Two-High Zone)",
            "projected_separation": c2_sep,
            "baseline_diff": round(c2_sep - separation, 2),
            "win_rate": c2_win,
            "leverage_rating": "OFFENSIVE ADVANTAGE" if c2_win >= 65 else ("NEUTRAL" if c2_win >= 50 else "DEFENSIVE LOCKDOWN"),
            "coaching_mandate": "Exploits soft underneath hook/curl voids against cloud corners." if c2_win >= 65 else "Bracket over top with half-field safety; caps deep route stems.",
        },
        {
            "scheme": "Cover 3 (Single-High Zone)",
            "projected_separation": c3_sep,
            "baseline_diff": round(c3_sep - separation, 2),
            "win_rate": c3_win,
            "leverage_rating": "OFFENSIVE ADVANTAGE" if c3_win >= 65 else ("NEUTRAL" if c3_win >= 50 else "DEFENSIVE LOCKDOWN"),
            "coaching_mandate": "Stresses deep third divider seam routes with vertical acceleration." if c3_win >= 65 else "Keep safety deep in post; squeeze curl/flat windows.",
        },
        {
            "scheme": "Cover 4 (Quarters / Match)",
            "projected_separation": c4_sep,
            "baseline_diff": round(c4_sep - separation, 2),
            "win_rate": c4_win,
            "leverage_rating": "OFFENSIVE ADVANTAGE" if c4_win >= 65 else ("NEUTRAL" if c4_win >= 50 else "DEFENSIVE LOCKDOWN"),
            "coaching_mandate": "Bypasses quarters match leverage via decisive stem breaks." if c4_win >= 65 else "Reroute with safety match triggers; boundary cushion limits separation.",
        },
        {
            "scheme": "Cover 6 (Split Field)",
            "projected_separation": c6_sep,
            "baseline_diff": round(c6_sep - separation, 2),
            "win_rate": c6_win,
            "leverage_rating": "OFFENSIVE ADVANTAGE" if c6_win >= 65 else ("NEUTRAL" if c6_win >= 50 else "DEFENSIVE LOCKDOWN"),
            "coaching_mandate": "Identifies weak-side boundary void against single corner leverage." if c6_win >= 65 else "Roll half-field safety to strong side to eliminate target window.",
        },
    ]

    return {
        "player_id": matched["player_id"],
        "player_name": matched["player_name"],
        "team": matched["team"],
        "baseline_separation": separation,
        "baseline_cushion": cushion,
        "air_yards": air_yards,
        "route_separation_index": rsi,
        "schemes": schemes,
    }