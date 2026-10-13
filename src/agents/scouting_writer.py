import logging
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

load_dotenv()
logger = logging.getLogger(__name__)

PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gemini-3.8-flash")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gemini-2.0-flash")
MODEL_CANDIDATES = [PRIMARY_MODEL, FALLBACK_MODEL]


class ScoutingAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not configured in .env")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _call_resilient_llm(self, prompt: str) -> Optional[str]:
        for model_name in MODEL_CANDIDATES:
            try:
                logger.info(f"Dispatching prompt to {model_name}...")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text
            except (APIError, Exception) as err:
                logger.warning(f"Model {model_name} unavailable ({err.__class__.__name__}). Attempting fallback...")

        logger.warning("All LLM candidate models exhausted. Activating analytical heuristic engine.")
        return None

    def embed_text(self, text: str) -> List[float]:
        """Generates 768-dimensional float vectors for Neon pgvector."""
        if not text or not text.strip():
            return []

        try:
            res = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=text.strip(),
                config=types.EmbedContentConfig(output_dimensionality=768),
            )
            if hasattr(res, "embeddings") and res.embeddings:
                return [float(x) for x in res.embeddings[0].values][:768]
            elif hasattr(res, "embedding") and res.embedding:
                return [float(x) for x in res.embedding.values][:768]
        except Exception:
            try:
                res = self.client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=text.strip(),
                )
                if hasattr(res, "embeddings") and res.embeddings:
                    return [float(x) for x in res.embeddings[0].values][:768]
                elif hasattr(res, "embedding") and res.embedding:
                    return [float(x) for x in res.embedding.values][:768]
            except Exception as e:
                logger.error(f"Vector embedding failed: {e}")

        return []

    def _synthesize_analytical_receiver_dossier(self, player_name: str, metrics: Dict[str, Any]) -> str:
        """Rules-based NFL scouting synthesizer activated during 429 quota limits."""
        cushion = metrics.get("cushion", 0.0)
        separation = metrics.get("separation", 0.0)
        rsi = metrics.get("route_separation_index", 0.0)
        air_yards = metrics.get("air_yards", 0.0)
        catch_pct = metrics.get("catch_pct", 0.0)
        targets = metrics.get("targets", 0)

        vertical_archetype = air_yards > 11.5
        slot_archetype = cushion > 6.0 and separation > 3.0

        if vertical_archetype:
            archetype_desc = "Explosive vertical burner pushing boundary safeties deep. Wins with pure straight-line acceleration and late-phase separation."
            vuln_desc = "Vulnerable to two-high shell (Cover 2 / Cover 4) with safety bracket help over the top."
            mandate_desc = "Bail technique at snap; do not allow clean outside release. Safety must favor his third on play-action."
        elif slot_archetype:
            archetype_desc = "High-efficiency slot technician who exploits soft cushions and off-coverage leverage with sharp interior cuts."
            vuln_desc = "Vulnerable to physical press-man at the line of scrimmage and congested nickel zone underneath."
            mandate_desc = "Play tight press-man inside; eliminate clean free release into horizontal crossing routes."
        else:
            archetype_desc = "Balanced possession pass-catcher operating effectively on intermediate dig, out, and curl routes."
            vuln_desc = "Can be contained with disciplined Cover 3 match principles."
            mandate_desc = "Disrupt timing on 5-to-7 yard stems and contest physical catch radius at target point."

        return f"""### Tactical Scouting Dossier: {player_name}
*(Synthesized via Spatial Tracking Telemetry & NFL Coaching Heuristics)*

**1. Separation & Route Profile:**
- **Tracking Profile:** Cushion: {cushion:.2f} yds | Separation: {separation:.2f} yds | RSI: {rsi:.2f} | Air Yards: {air_yards:.1f} yds | Catch%: {catch_pct:.1f}% ({targets} targets)
- **Profile Analysis:** {archetype_desc}

**2. Coverage Vulnerabilities:**
- {vuln_desc}

**3. Defensive Game Plan Mandate:**
- {mandate_desc}
"""

    def _synthesize_analytical_qb_dossier(self, player_name: str, metrics: Dict[str, Any]) -> str:
        """Rules-based NFL pressure synthesizer activated during 429 quota limits."""
        ttt = metrics.get("time_to_throw", 0.0)
        agg = metrics.get("aggressiveness", 0.0)
        cpoe = metrics.get("cpoe", 0.0)
        rating = metrics.get("passer_rating", 0.0)
        risk = metrics.get("pressure_risk_index", 0.0)

        holding_ball = ttt > 2.8

        if holding_ball:
            mech_desc = f"Deliberate pocket passer averaging {ttt:.2f}s release. Extends plays outside the pocket but invites strip-sacks."
            vuln_desc = f"Vulnerable to delayed blitz packages and boundary edge stunts (Pressure Risk Index: {risk:.2f})."
            mandate_desc = "Collapse the pocket through coordinated edge contain rush; do not flush him into open scramble lanes."
        else:
            mech_desc = f"Quick-strike rhythm distributor operating on timing ({ttt:.2f}s time to throw). Attacks quick slants and boundary screens."
            vuln_desc = "Struggles when first read is disrupted by rolled coverage or interior jam on tight ends."
            mandate_desc = "Disguise post-snap coverages; drop seven into underneath zone to force him off his initial rhythm throw."

        return f"""### Tactical Scouting Dossier: {player_name}
*(Synthesized via Passing Pressure Telemetry & NFL Front-Seven Heuristics)*

**1. Pocket Timing & Release Mechanics:**
- **Tracking Profile:** TTT: {ttt:.2f}s | Tight Window: {agg:.1f}% | CPOE: {cpoe:.1f}% | Passer Rating: {rating:.1f}
- **Mechanics Analysis:** {mech_desc}

**2. Pressure Vulnerability:**
- {vuln_desc}

**3. Rush Scheme Mandate:**
- {mandate_desc}
"""

    def generate_receiver_dossier(self, player_name: str, metrics: Dict[str, Any]) -> str:
        prompt = f"""
You are an NFL Defensive Coordinator preparing a weekly game plan.
Analyze the following Next Gen Stats tracking profile for wide receiver {player_name}:
- Average Cushion: {metrics.get('cushion', 0.0):.2f} yards
- Average Separation at Target: {metrics.get('separation', 0.0):.2f} yards
- Route Separation Index (RSI): {metrics.get('route_separation_index', 0.0):.2f}
- Cushion Delta: {metrics.get('cushion_delta', 0.0):.2f} yards
- Catch % Over Expected: {metrics.get('catch_pct', 0.0):.1f}%
- Intended Air Yard Depth: {metrics.get('air_yards', 0.0):.1f} yards
- Target Volume: {metrics.get('targets', 0)} targets

Provide a sharp, 3-section scouting dossier in Markdown:
1. **Separation & Route Profile**
2. **Coverage Vulnerabilities**
3. **Defensive Game Plan Mandate**
"""
        llm_result = self._call_resilient_llm(prompt)
        if llm_result:
            return llm_result
        return self._synthesize_analytical_receiver_dossier(player_name, metrics)

    def generate_qb_pressure_dossier(self, player_name: str, metrics: Dict[str, Any]) -> str:
        prompt = f"""
You are an NFL Defensive Coordinator designing a blitz package and front-seven game plan.
Analyze the following Next Gen Stats tracking metrics for quarterback {player_name}:
- Average Time to Throw (TTT): {metrics.get('time_to_throw', 0.0):.2f} seconds
- Aggressiveness %: {metrics.get('aggressiveness', 0.0):.1f}%
- CPOE: {metrics.get('cpoe', 0.0):.1f}%
- Passer Rating: {metrics.get('passer_rating', 0.0):.1f}
- Pass Rush Pressure Exposure Index: {metrics.get('pressure_risk_index', 0.0):.2f}

Provide a sharp, 3-section scouting dossier in Markdown:
1. **Pocket Timing & Release Mechanics**
2. **Pressure Vulnerability**
3. **Rush Scheme Mandate**
"""
        llm_result = self._call_resilient_llm(prompt)
        if llm_result:
            return llm_result
        return self._synthesize_analytical_qb_dossier(player_name, metrics)