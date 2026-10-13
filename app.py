import os
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", API_URL)

st.set_page_config(
    page_title="Apex-NGS | NFL Tracking Intelligence",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏈 Apex-NGS: NFL Next Gen Tracking & Tactical AI Engine")
st.caption("Asynchronous tracking ingestion, spatial route metrics, and Gemini-powered defensive game planning.")

st.sidebar.header("Data Thresholds")
min_targets = st.sidebar.slider("Receiver Target Threshold", min_value=5, max_value=80, value=25, step=5)
min_attempts = st.sidebar.slider("QB Pass Attempt Threshold", min_value=10, max_value=150, value=30, step=10)

# Fetch core cohorts with network error shielding
try:
    res_rec = httpx.get(f"{API_URL}/api/analytics/receivers?min_targets={min_targets}", timeout=10.0)
    data_rec = res_rec.json().get("data", [])
    df_rec = pd.DataFrame(data_rec) if data_rec else pd.DataFrame()
except Exception:
    df_rec = pd.DataFrame()

try:
    res_qb = httpx.get(f"{API_URL}/api/analytics/qbs?min_attempts={min_attempts}", timeout=10.0)
    data_qb = res_qb.json().get("data", [])
    df_qb = pd.DataFrame(data_qb) if data_qb else pd.DataFrame()
except Exception:
    df_qb = pd.DataFrame()

tabs = st.tabs([
    "WR Route Separation",
    "Head-to-Head Radar Profile",
    "Coverage Matchup Simulator",
    "QB Pressure Exposure",
    "pgvector Semantic Search",
    "Pipeline Telemetry",
])

# ----------------- TAB 1: RECEIVERS -----------------
with tabs[0]:
    st.subheader("Route Separation Index & Spatial Separation")
    if not df_rec.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            fig = px.scatter(
                df_rec,
                x="cushion",
                y="separation",
                size="targets",
                color="route_separation_index",
                hover_name="player_name",
                hover_data=["team", "catch_pct", "air_yards"],
                color_continuous_scale="Viridis",
                labels={
                    "cushion": "Avg Pre-Snap Cushion (Yards)",
                    "separation": "Avg Separation at Target (Yards)",
                    "route_separation_index": "RSI Score",
                },
                title="Receiver Cushion vs. Separation Efficiency",
            )
            fig.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### Generate Tactical Scouting Dossier")
            player_list = sorted(df_rec["player_name"].unique())
            selected_player = st.selectbox("Select Target Receiver", player_list, key="wr_select")

            matches = df_rec[df_rec["player_name"] == selected_player]
            if not matches.empty:
                selected_row = matches.iloc[0]
                st.metric("Avg Separation", f"{selected_row['separation']:.2f} yds", delta=f"{selected_row.get('cushion_delta', 0.0):.2f} delta")
                st.metric("Route Separation Index", f"{selected_row['route_separation_index']:.2f}")

                if st.button("Synthesize WR Scouting Dossier", type="primary"):
                    with st.spinner("Dispatching tracking profile to Gemini..."):
                        try:
                            dossier_res = httpx.post(f"{API_URL}/api/scout/receiver/{selected_row['player_id']}", timeout=45.0)
                            if dossier_res.status_code == 200:
                                st.markdown(dossier_res.json()["dossier"])
                                st.success("Dossier synthesized and vectorized into Neon pgvector!")
                            else:
                                st.error("Failed to generate dossier.")
                        except httpx.TimeoutException:
                            st.error("Request timed out waiting for Gemini API.")
                        except Exception as e:
                            st.error(f"Error: {e}")
    else:
        st.info("No receiving records returned. Verify FastAPI backend.")

# ----------------- TAB 2: RADAR PROFILE -----------------
with tabs[1]:
    st.subheader("Head-to-Head Percentile Radar Profile")
    st.caption("Benchmark metrics against league distribution (0th - 100th percentile).")

    pos_choice = st.radio("Select Position Group", ["Wide Receivers / TEs", "Quarterbacks"], horizontal=True)
    active_df = df_rec if pos_choice == "Wide Receivers / TEs" else df_qb

    if not active_df.empty:
        col_a, col_b = st.columns(2)
        player_names = sorted(active_df["player_name"].unique())

        with col_a:
            p1_name = st.selectbox("Player A", player_names, index=0, key=f"p1_{pos_choice}")
        with col_b:
            p2_name = st.selectbox("Player B", player_names, index=min(1, len(player_names) - 1), key=f"p2_{pos_choice}")

        p1_id = active_df[active_df["player_name"] == p1_name].iloc[0]["player_id"]
        p2_id = active_df[active_df["player_name"] == p2_name].iloc[0]["player_id"]

        try:
            r1 = httpx.get(f"{API_URL}/api/analytics/player-percentiles/{p1_id}", timeout=10.0).json()
            r2 = httpx.get(f"{API_URL}/api/analytics/player-percentiles/{p2_id}", timeout=10.0).json()

            categories = r1.get("categories", [])
            keys = r1.get("keys", [])

            v1 = [r1["percentiles"][k] for k in keys]
            v2 = [r2["percentiles"][k] for k in keys]

            radar = go.Figure()
            radar.add_trace(go.Scatterpolar(r=v1 + [v1[0]], theta=categories + [categories[0]], fill="toself", name=p1_name))
            radar.add_trace(go.Scatterpolar(r=v2 + [v2[0]], theta=categories + [categories[0]], fill="toself", name=p2_name))
            radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                template="plotly_dark",
                height=550,
                title=f"{p1_name} vs. {p2_name} ({r1.get('position', '')} Percentiles)",
            )
            st.plotly_chart(radar, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering radar comparison: {e}")
    else:
        st.info("No data available for the selected position threshold.")

# ----------------- TAB 3: COVERAGE MATCHUP SIMULATOR -----------------
with tabs[2]:
    st.subheader("Coverage Scheme Matchup Simulation Engine")
    st.caption("Heuristic spatial simulation of receiver separation and route win probabilities across primary NFL defensive coverages.")

    if not df_rec.empty:
        col_m1, col_m2 = st.columns([1, 2])
        sim_player = col_m1.selectbox("Select Target Receiver for Scheme Simulation", sorted(df_rec["player_name"].unique()), key="sim_wr_select")
        player_subset = df_rec[df_rec["player_name"] == sim_player]

        if not player_subset.empty:
            sim_row = player_subset.iloc[0]

            with col_m1:
                st.metric("Baseline Separation", f"{sim_row['separation']:.2f} yds")
                st.metric("Pre-Snap Cushion", f"{sim_row['cushion']:.2f} yds")
                st.metric("Intended Air Yards", f"{sim_row['air_yards']:.1f} yds")
                st.metric("Route Separation Index", f"{sim_row['route_separation_index']:.2f}")

                # Direct browser stream link to prevent stream drops
                st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                pdf_url = f"{EXTERNAL_API_URL}/api/scout/export-pdf/{sim_row['player_id']}"
                st.link_button(
                    "📄 Export Executive Dossier (PDF)",
                    url=pdf_url,
                    help="Streams formatted scouting packet directly from FastAPI",
                    use_container_width=True,
                )

            with col_m2:
                try:
                    sim_res = httpx.get(f"{API_URL}/api/analytics/matchup-simulation/{sim_row['player_id']}", timeout=10.0).json()
                    schemes_data = sim_res.get("schemes", [])

                    if schemes_data:
                        df_schemes = pd.DataFrame(schemes_data)

                        # Separation Comparison Bar Chart
                        fig_sim = go.Figure()
                        fig_sim.add_trace(go.Bar(
                            x=df_schemes["scheme"],
                            y=[sim_res["baseline_separation"]] * len(df_schemes),
                            name="Baseline Separation",
                            marker_color="rgba(255, 255, 255, 0.3)",
                        ))
                        fig_sim.add_trace(go.Bar(
                            x=df_schemes["scheme"],
                            y=df_schemes["projected_separation"],
                            name="Projected Scheme Separation",
                            marker_color="#00CC96",
                            text=df_schemes["win_rate"].apply(lambda w: f"{w}% Win Rate"),
                            textposition="auto",
                        ))
                        fig_sim.update_layout(
                            barmode="group",
                            template="plotly_dark",
                            height=400,
                            title=f"{sim_player} Separation Across Coverage Schemes",
                            yaxis_title="Separation (Yards)",
                        )
                        st.plotly_chart(fig_sim, use_container_width=True)

                        # Coverage Scheme Vulnerability Matrix
                        st.markdown("### Defensive Scheme Vulnerability Matrix")
                        for s in schemes_data:
                            rating = s["leverage_rating"]
                            tag_color = "🟢" if "ADVANTAGE" in rating else ("🟡" if "NEUTRAL" in rating else "🔴")
                            with st.expander(f"{tag_color} {s['scheme']} — {rating} (Win Rate: {s['win_rate']}%, Separation: {s['projected_separation']} yds)"):
                                col_sub1, col_sub2 = st.columns([1, 2])
                                with col_sub1:
                                    st.metric("Projected Separation", f"{s['projected_separation']} yds", delta=f"{s['baseline_diff']} yds")
                                    st.metric("Estimated Route Win Rate", f"{s['win_rate']}%")
                                with col_sub2:
                                    st.markdown(f"**Coaching Mandate & Secondary Trigger:**\n\n{s['coaching_mandate']}")
                except Exception as e:
                    st.error(f"Failed to fetch scheme simulation: {e}")
    else:
        st.info("No receiver data loaded.")

# ----------------- TAB 4: QBS & PRESSURE -----------------
with tabs[3]:
    st.subheader("Quarterback Pressure Exposure & Pocket Timing")
    if not df_qb.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            fig_qb = px.scatter(
                df_qb,
                x="time_to_throw",
                y="aggressiveness",
                size="attempts",
                color="pressure_risk_index",
                hover_name="player_name",
                hover_data=["team", "cpoe", "passer_rating"],
                color_continuous_scale="Plasma",
                labels={
                    "time_to_throw": "Avg Time to Throw (Seconds)",
                    "aggressiveness": "Aggressiveness % (Tight Window Throws)",
                    "pressure_risk_index": "Pressure Risk Index",
                },
                title="Pocket Time vs. Tight Window Aggressiveness",
            )
            fig_qb.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig_qb, use_container_width=True)

        with col2:
            st.markdown("### QB Rush Scheme Game Plan")
            selected_qb = st.selectbox("Select Target QB", sorted(df_qb["player_name"].unique()), key="qb_select")
            row_qb = df_qb[df_qb["player_name"] == selected_qb].iloc[0]

            st.metric("Time to Throw", f"{row_qb['time_to_throw']:.2f} s")
            st.metric("Tight Window %", f"{row_qb['aggressiveness']:.1f}%")

            if st.button("Synthesize QB Blitz Game Plan", type="primary"):
                with st.spinner("Dispatching metrics to Gemini..."):
                    try:
                        dossier_res = httpx.post(f"{API_URL}/api/scout/qb/{row_qb['player_id']}", timeout=45.0)
                        if dossier_res.status_code == 200:
                            st.markdown(dossier_res.json()["dossier"])
                            st.success("QB dossier saved and indexed in pgvector!")
                    except httpx.TimeoutException:
                        st.error("Request timed out waiting for Gemini API.")
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.info("No quarterback records returned. Verify thresholds in the sidebar.")

# ----------------- TAB 5: PGVECTOR SEARCH -----------------
with tabs[4]:
    st.subheader("Semantic Scouting Query Engine (pgvector)")
    st.caption("Search across synthesized player tactical profiles using Gemini cosine embeddings.")

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search_query = st.text_input(
            "Enter tactical scenario or player archetype:",
            value="Speedy",
            placeholder="e.g. explosive vertical burner who wins downfield with speed",
        )
    with col_s2:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        if st.button("🚀 Index Top Players", type="secondary"):
            with st.spinner("Embedding and indexing players into Neon pgvector..."):
                try:
                    b_res = httpx.post(f"{API_URL}/api/scout/batch-index", timeout=120.0)
                    if b_res.status_code == 200:
                        st.success(f"Indexed {b_res.json().get('indexed_count', 0)} players into Neon pgvector!")
                    else:
                        st.error(f"Batch indexing failed with status code {b_res.status_code}")
                except httpx.TimeoutException:
                    st.warning("Batch indexing timed out at 120s limit. Any players processed before timeout remain stored.")
                except Exception as e:
                    st.error(f"Indexing error: {e}")

    if st.button("Search Vector Index", type="primary"):
        if search_query:
            with st.spinner("Embedding query & searching Neon pgvector..."):
                try:
                    s_res = httpx.post(
                        f"{API_URL}/api/analytics/semantic-search",
                        json={"query": search_query, "limit": 4},
                        timeout=15.0,
                    )
                    payload = s_res.json()
                    matches = payload.get("results", [])
                    total_indexed = payload.get("total_indexed", 0)

                    if matches:
                        st.success(f"Found {len(matches)} matching players ({total_indexed} total dossiers in index):")
                        for m in matches:
                            with st.expander(f"🏈 {m['player_name']} — Semantic Match: {m['similarity_score'] * 100:.1f}%", expanded=True):
                                st.markdown(m["dossier"])
                    else:
                        st.warning(f"Index currently holds {total_indexed} records. Click '🚀 Index Top Players' above to populate.")
                except Exception as e:
                    st.error(f"Search request failed: {e}")

# ----------------- TAB 6: TELEMETRY -----------------
with tabs[5]:
    st.subheader("System Infrastructure & Telemetry")
    st.json({
        "internal_backend": API_URL,
        "external_backend": EXTERNAL_API_URL,
        "database": "Neon PostgreSQL (Remote Cloud)",
        "vector_extension": "pgvector enabled (768 dimensions)",
        "vector_search_endpoint": f"{EXTERNAL_API_URL}/api/analytics/semantic-search",
        "simulation_endpoint": f"{EXTERNAL_API_URL}/api/analytics/matchup-simulation/{{player_id}}",
        "primary_model": os.getenv("PRIMARY_MODEL", "gemini-3.8-flash"),
        "fallback_model": os.getenv("FALLBACK_MODEL", "gemini-2.0-flash"),
        "embedding_model": "gemini-embedding-001 (768-dim MRL)",
    })