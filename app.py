import os
import time
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", API_URL)

st.set_page_config(
    page_title="Apex-NGS | NFL Tracking Intelligence",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------- MODERN PRO-ANALYTICS CSS -----------------
st.markdown(
    """
    <style>
        /* Hide left sidebar and collapse toggle completely */
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
        }
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 1440px !important;
        }
        /* Executive Hero Banner */
        .apex-hero {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.85) 100%);
            border: 1px solid rgba(56, 189, 248, 0.22);
            border-radius: 16px;
            padding: 1.4rem 1.8rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        }
        .apex-badge {
            display: inline-block;
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.35);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            margin-bottom: 0.45rem;
        }
        .apex-title {
            font-size: 1.95rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #f8fafc;
            margin: 0;
            line-height: 1.2;
        }
        .apex-subtitle {
            color: #94a3b8;
            font-size: 0.95rem;
            margin-top: 0.35rem;
            margin-bottom: 0;
        }
        /* Metric Cards */
        div[data-testid="stMetric"] {
            background: rgba(30, 41, 59, 0.55);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 12px;
            padding: 0.85rem 1.1rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
        }
        /* Modern Pill Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: rgba(15, 23, 42, 0.6);
            padding: 6px;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.12);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(56, 189, 248, 0.16) !important;
            color: #38bdf8 !important;
            border-bottom: none !important;
        }
        /* Panel Card Container */
        .dossier-box {
            background: rgba(15, 23, 42, 0.75);
            border-left: 4px solid #38bdf8;
            border-radius: 10px;
            padding: 1.2rem 1.4rem;
            margin-top: 0.75rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def fetch_api_json(path: str, retries: int = 5, delay: float = 0.6) -> dict:
    """Resilient GET helper that waits for FastAPI startup on cold F5 launches."""
    for attempt in range(retries):
        try:
            res = httpx.get(f"{API_URL}{path}", timeout=10.0)
            if res.status_code == 200:
                return res.json()
        except Exception:
            if attempt < retries - 1:
                time.sleep(delay)
    return {}


# ----------------- HEADER & COMPACT FILTER POPOVER -----------------
hdr_left, hdr_right = st.columns([5, 1])

with hdr_left:
    st.markdown(
        """
        <div class="apex-hero">
            <div class="apex-badge">● LIVE NGS TELEMETRY &bull; PGVECTOR AI ENGINE</div>
            <h1 class="apex-title">🏈 Apex-NGS Tactical Intelligence</h1>
            <p class="apex-subtitle">
                Next Gen Stats spatial tracking, multi-scheme coverage simulation, and Gemini-synthesized scouting dossiers.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with hdr_right:
    st.markdown("<div style='height: 18px'></div>", unsafe_allow_html=True)
    with st.popover("⚙️ Cohort Filters", use_container_width=True):
        st.caption("Adjust minimum volume thresholds for league cohorts:")
        min_targets = st.slider("Min WR Targets", min_value=5, max_value=80, value=25, step=5)
        min_attempts = st.slider("Min QB Pass Attempts", min_value=10, max_value=150, value=30, step=10)

# Fetch core cohorts with automatic startup retry
rec_payload = fetch_api_json(f"/api/analytics/receivers?min_targets={min_targets}")
df_rec = pd.DataFrame(rec_payload.get("data", []))

qb_payload = fetch_api_json(f"/api/analytics/qbs?min_attempts={min_attempts}")
df_qb = pd.DataFrame(qb_payload.get("data", []))

# ----------------- TOP-LEVEL KPI SUMMARY RIBBON -----------------
if not df_rec.empty and not df_qb.empty:
    top_wr = df_rec.sort_values("route_separation_index", ascending=False).iloc[0]
    top_sep = df_rec.sort_values("separation", ascending=False).iloc[0]
    top_qb = df_qb.sort_values("passer_rating", ascending=False).iloc[0]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Active Skill Cohort",
        f"{len(df_rec)} WRs / {len(df_qb)} QBs",
        delta=f"≥{min_targets} Tgt | ≥{min_attempts} Att",
        delta_color="off",
    )
    k2.metric(
        "Top Route Separation Index",
        f"{top_wr['player_name']} ({top_wr['team']})",
        delta=f"{top_wr['route_separation_index']:.2f} RSI",
    )
    k3.metric(
        "League Separation Leader",
        f"{top_sep['player_name']} ({top_sep['team']})",
        delta=f"{top_sep['separation']:.2f} yds avg",
    )
    k4.metric(
        "Top Passer Efficiency",
        f"{top_qb['player_name']} ({top_qb['team']})",
        delta=f"{top_qb['passer_rating']:.1f} RTG",
    )
    st.markdown("<div style='height: 6px'></div>", unsafe_allow_html=True)

# ----------------- NAVIGATION TABS -----------------
tabs = st.tabs([
    "📡 WR Route Separation",
    "🎯 Head-to-Head Radar",
    "🛡️ Coverage Matchup Simulator",
    "⚡ QB Pressure Exposure",
    "🧠 Semantic Vector Search",
    "🖥️ System Telemetry",
])

# ----------------- TAB 1: RECEIVERS -----------------
with tabs[0]:
    if not df_rec.empty:
        col1, col2 = st.columns([1.85, 1.15], gap="large")

        with col1:
            st.markdown("#### Spatial Cushion vs. Target Separation")
            st.caption("Bubble size reflects total targets; color encodes composite Route Separation Index (RSI). Dashed lines mark cohort averages.")

            avg_cushion = df_rec["cushion"].mean()
            avg_sep = df_rec["separation"].mean()

            fig = px.scatter(
                df_rec,
                x="cushion",
                y="separation",
                size="targets",
                color="route_separation_index",
                hover_name="player_name",
                hover_data={
                    "team": True,
                    "targets": True,
                    "receptions": True,
                    "catch_pct": ":.1f",
                    "air_yards": ":.1f",
                    "cushion": ":.2f",
                    "separation": ":.2f",
                    "route_separation_index": ":.2f",
                },
                color_continuous_scale="Turbo",
                labels={
                    "cushion": "Avg Pre-Snap Cushion (Yards)",
                    "separation": "Avg Target Separation (Yards)",
                    "route_separation_index": "RSI",
                },
            )
            fig.add_vline(x=avg_cushion, line_dash="dot", line_color="rgba(148,163,184,0.45)", annotation_text="Avg Cushion")
            fig.add_hline(y=avg_sep, line_dash="dot", line_color="rgba(148,163,184,0.45)", annotation_text="Avg Separation")
            fig.update_traces(marker=dict(line=dict(width=1, color="rgba(255,255,255,0.35)")))
            fig.update_layout(
                template="plotly_dark",
                height=520,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,23,42,0.45)",
                margin=dict(l=15, r=15, t=25, b=15),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Player Telemetry & AI Dossier")
            player_list = sorted(df_rec["player_name"].unique())
            selected_player = st.selectbox("Select Target Receiver", player_list, key="wr_select")

            matches = df_rec[df_rec["player_name"] == selected_player]
            if not matches.empty:
                selected_row = matches.iloc[0]

                m1, m2 = st.columns(2)
                m1.metric("Avg Separation", f"{selected_row['separation']:.2f} yds")
                m2.metric("RSI Score", f"{selected_row['route_separation_index']:.2f}")

                m3, m4 = st.columns(2)
                m3.metric("Pre-Snap Cushion", f"{selected_row['cushion']:.2f} yds")
                m4.metric("Catch Rate", f"{selected_row['catch_pct']:.1f}%", delta=f"{selected_row['targets']} Tgts", delta_color="off")

                pdf_url = f"{EXTERNAL_API_URL}/api/scout/export-pdf/{selected_row['player_id']}"
                btn_c1, btn_c2 = st.columns(2)
                with btn_c1:
                    gen_wr = st.button("✨ Synthesize AI Dossier", type="primary", use_container_width=True)
                with btn_c2:
                    st.link_button("📄 Export PDF Report", url=pdf_url, use_container_width=True)

                if gen_wr:
                    with st.spinner(f"Synthesizing tactical scouting profile for {selected_player}..."):
                        try:
                            dossier_res = httpx.post(f"{API_URL}/api/scout/receiver/{selected_row['player_id']}", timeout=45.0)
                            if dossier_res.status_code == 200:
                                st.markdown(
                                    f"<div class='dossier-box'>{dossier_res.json()['dossier']}</div>",
                                    unsafe_allow_html=True,
                                )
                                st.toast("Dossier synthesized and indexed in pgvector!", icon="✅")
                            else:
                                st.error("Failed to generate dossier.")
                        except httpx.TimeoutException:
                            st.error("Request timed out waiting for Gemini API.")
                        except Exception as e:
                            st.error(f"Error: {e}")

        with st.expander("📊 View Full Receiver Tracking Leaderboard"):
            st.dataframe(
                df_rec[["player_name", "team", "targets", "receptions", "catch_pct", "cushion", "separation", "air_yards", "route_separation_index"]]
                .sort_values("route_separation_index", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.warning("No receiving records returned. Ensure the FastAPI backend is running on port 8000.")

# ----------------- TAB 2: RADAR PROFILE -----------------
with tabs[1]:
    top_r1, top_r2 = st.columns([2, 1])
    with top_r1:
        st.markdown("#### Head-to-Head Percentile Benchmarking")
        st.caption("Compare two players directly across 0th–100th league percentile distributions.")
    with top_r2:
        pos_choice = st.radio("Position Cohort", ["Wide Receivers / TEs", "Quarterbacks"], horizontal=True)

    active_df = df_rec if pos_choice == "Wide Receivers / TEs" else df_qb

    if not active_df.empty:
        col_a, col_b = st.columns(2)
        player_names = sorted(active_df["player_name"].unique())

        with col_a:
            p1_name = st.selectbox("Primary Player (Cyan)", player_names, index=0, key=f"p1_{pos_choice}")
        with col_b:
            p2_name = st.selectbox("Comparison Player (Amber)", player_names, index=min(1, len(player_names) - 1), key=f"p2_{pos_choice}")

        p1_row = active_df[active_df["player_name"] == p1_name].iloc[0]
        p2_row = active_df[active_df["player_name"] == p2_name].iloc[0]

        try:
            r1 = httpx.get(f"{API_URL}/api/analytics/player-percentiles/{p1_row['player_id']}", timeout=10.0).json()
            r2 = httpx.get(f"{API_URL}/api/analytics/player-percentiles/{p2_row['player_id']}", timeout=10.0).json()

            categories = r1.get("categories", [])
            keys = r1.get("keys", [])

            v1 = [r1["percentiles"][k] for k in keys]
            v2 = [r2["percentiles"][k] for k in keys]

            r_col1, r_col2 = st.columns([1.6, 1.0], gap="large")
            with r_col1:
                radar = go.Figure()
                radar.add_trace(
                    go.Scatterpolar(
                        r=v1 + [v1[0]],
                        theta=categories + [categories[0]],
                        fill="toself",
                        name=f"{p1_name} ({p1_row['team']})",
                        line=dict(color="#38bdf8", width=2.5),
                        fillcolor="rgba(56, 189, 248, 0.25)",
                    )
                )
                radar.add_trace(
                    go.Scatterpolar(
                        r=v2 + [v2[0]],
                        theta=categories + [categories[0]],
                        fill="toself",
                        name=f"{p2_name} ({p2_row['team']})",
                        line=dict(color="#f59e0b", width=2.5),
                        fillcolor="rgba(245, 158, 11, 0.22)",
                    )
                )
                radar.update_layout(
                    polar=dict(
                        bgcolor="rgba(15,23,42,0.5)",
                        radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(148,163,184,0.2)"),
                        angularaxis=dict(gridcolor="rgba(148,163,184,0.2)"),
                    ),
                    showlegend=True,
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=500,
                    margin=dict(l=40, r=40, t=40, b=40),
                )
                st.plotly_chart(radar, use_container_width=True)

            with r_col2:
                st.markdown("##### Percentile Breakdown")
                comp_df = pd.DataFrame({
                    "Metric": categories,
                    f"{p1_name}": [f"{val:.0f}th" for val in v1],
                    f"{p2_name}": [f"{val:.0f}th" for val in v2],
                    "Edge": [
                        f"{p1_name} (+{abs(a - b):.0f})" if a > b else (f"{p2_name} (+{abs(b - a):.0f})" if b > a else "Tie")
                        for a, b in zip(v1, v2)
                    ],
                })
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error rendering radar comparison: {e}")
    else:
        st.info("No data available for the selected position cohort.")

# ----------------- TAB 3: COVERAGE MATCHUP SIMULATOR -----------------
with tabs[2]:
    st.markdown("#### Defensive Coverage Scheme Matchup Simulator")
    st.caption("Spatial projection of receiver separation and route win probabilities across NFL defensive coverage shells.")

    if not df_rec.empty:
        col_m1, col_m2 = st.columns([1.05, 1.95], gap="large")
        with col_m1:
            sim_player = st.selectbox(
                "Select Receiver to Simulate",
                sorted(df_rec["player_name"].unique()),
                key="sim_wr_select",
            )
            sim_row = df_rec[df_rec["player_name"] == sim_player].iloc[0]

            s1, s2 = st.columns(2)
            s1.metric("Baseline Separation", f"{sim_row['separation']:.2f} yds")
            s2.metric("Pre-Snap Cushion", f"{sim_row['cushion']:.2f} yds")

            s3, s4 = st.columns(2)
            s3.metric("Intended Air Yards", f"{sim_row['air_yards']:.1f} yds")
            s4.metric("RSI Rating", f"{sim_row['route_separation_index']:.2f}")

            st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
            pdf_url = f"{EXTERNAL_API_URL}/api/scout/export-pdf/{sim_row['player_id']}"
            st.link_button(
                "📄 Download Executive Matchup Packet (PDF)",
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

                    fig_sim = go.Figure()
                    fig_sim.add_trace(
                        go.Bar(
                            x=df_schemes["scheme"],
                            y=[sim_res["baseline_separation"]] * len(df_schemes),
                            name="Baseline Separation",
                            marker_color="rgba(148, 163, 184, 0.35)",
                        )
                    )
                    fig_sim.add_trace(
                        go.Bar(
                            x=df_schemes["scheme"],
                            y=df_schemes["projected_separation"],
                            name="Projected Scheme Separation",
                            marker_color="#10b981",
                            text=df_schemes["win_rate"].apply(lambda w: f"{w}% Win"),
                            textposition="auto",
                        )
                    )
                    fig_sim.update_layout(
                        barmode="group",
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(15,23,42,0.45)",
                        height=380,
                        margin=dict(l=15, r=15, t=35, b=15),
                        title=f"{sim_player} ({sim_row['team']}) — Projected Separation by Coverage Shell",
                        yaxis_title="Separation (Yards)",
                    )
                    st.plotly_chart(fig_sim, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to fetch scheme simulation: {e}")
                schemes_data = []

        if schemes_data:
            st.markdown("##### Defensive Coordinator Scheme Vulnerability Matrix")
            sc_cols = st.columns(len(schemes_data))
            for idx, s in enumerate(schemes_data):
                rating = s["leverage_rating"]
                badge = "🟢" if "ADVANTAGE" in rating else ("🟡" if "NEUTRAL" in rating else "🔴")
                with sc_cols[idx]:
                    with st.container(border=True):
                        st.markdown(f"**{badge} {s['scheme']}**")
                        st.caption(rating)
                        st.metric("Projected Sep", f"{s['projected_separation']} yds", delta=f"{s['baseline_diff']} yds")
                        st.metric("Route Win Rate", f"{s['win_rate']}%")
                        st.caption(s["coaching_mandate"])
    else:
        st.info("No receiver data loaded.")

# ----------------- TAB 4: QBS & PRESSURE -----------------
with tabs[3]:
    if not df_qb.empty:
        col1, col2 = st.columns([1.85, 1.15], gap="large")

        with col1:
            st.markdown("#### Quarterback Pocket Timing vs. Tight-Window Aggressiveness")
            st.caption("Bubble size reflects pass attempts; color encodes composite Pressure Risk Index.")

            fig_qb = px.scatter(
                df_qb,
                x="time_to_throw",
                y="aggressiveness",
                size="attempts",
                color="pressure_risk_index",
                hover_name="player_name",
                hover_data={
                    "team": True,
                    "attempts": True,
                    "cpoe": ":.2f",
                    "passer_rating": ":.1f",
                    "time_to_throw": ":.2f",
                    "aggressiveness": ":.1f",
                    "pressure_risk_index": ":.2f",
                },
                color_continuous_scale="Plasma",
                labels={
                    "time_to_throw": "Avg Time to Throw (Seconds)",
                    "aggressiveness": "Tight-Window Aggressiveness (%)",
                    "pressure_risk_index": "Pressure Risk",
                },
            )
            fig_qb.add_vline(x=df_qb["time_to_throw"].mean(), line_dash="dot", line_color="rgba(148,163,184,0.45)", annotation_text="Avg TTT")
            fig_qb.add_hline(y=df_qb["aggressiveness"].mean(), line_dash="dot", line_color="rgba(148,163,184,0.45)", annotation_text="Avg Agg%")
            fig_qb.update_traces(marker=dict(line=dict(width=1, color="rgba(255,255,255,0.35)")))
            fig_qb.update_layout(
                template="plotly_dark",
                height=520,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,23,42,0.45)",
                margin=dict(l=15, r=15, t=25, b=15),
            )
            st.plotly_chart(fig_qb, use_container_width=True)

        with col2:
            st.markdown("#### QB Blitz & Pass-Rush Game Plan")
            selected_qb = st.selectbox("Select Target Quarterback", sorted(df_qb["player_name"].unique()), key="qb_select")
            row_qb = df_qb[df_qb["player_name"] == selected_qb].iloc[0]

            q1, q2 = st.columns(2)
            q1.metric("Time to Throw", f"{row_qb['time_to_throw']:.2f} s")
            q2.metric("Tight Window %", f"{row_qb['aggressiveness']:.1f}%")

            q3, q4 = st.columns(2)
            q3.metric("Passer Rating", f"{row_qb['passer_rating']:.1f}")
            q4.metric("CPOE", f"{row_qb['cpoe']:+.2f}%")

            if st.button("⚡ Synthesize Defensive Blitz Game Plan", type="primary", use_container_width=True):
                with st.spinner(f"Generating pass-rush game plan for {selected_qb}..."):
                    try:
                        dossier_res = httpx.post(f"{API_URL}/api/scout/qb/{row_qb['player_id']}", timeout=45.0)
                        if dossier_res.status_code == 200:
                            st.markdown(
                                f"<div class='dossier-box'>{dossier_res.json()['dossier']}</div>",
                                unsafe_allow_html=True,
                            )
                            st.toast("QB game plan saved and indexed in pgvector!", icon="✅")
                        else:
                            st.error("Failed to generate QB dossier.")
                    except httpx.TimeoutException:
                        st.error("Request timed out waiting for Gemini API.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        with st.expander("📊 View Full Quarterback Tracking Leaderboard"):
            st.dataframe(
                df_qb[["player_name", "team", "attempts", "time_to_throw", "aggressiveness", "cpoe", "passer_rating", "pressure_risk_index"]]
                .sort_values("passer_rating", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.warning("No quarterback records returned.")

# ----------------- TAB 5: PGVECTOR SEARCH -----------------
with tabs[4]:
    st.markdown("#### Semantic Scouting Query Engine (`pgvector`)")
    st.caption("Natural-language cosine similarity search across Gemini-embedded player tactical dossiers.")

    # Quick Archetype Presets
    st.markdown("**Quick Archetype Presets:**")
    p_cols = st.columns(4)
    preset_queries = [
        "Explosive vertical burner who beats press coverage",
        "High-volume slot technician with elite separation",
        "Quick-trigger quarterback immune to blitz pressure",
        "Aggressive downfield passer who holds the ball in the pocket",
    ]
    if "active_search_query" not in st.session_state:
        st.session_state.active_search_query = preset_queries[0]

    for idx, label in enumerate([
        "🔥 Vertical Burner WR",
        "⚡ Elite Slot Separator",
        "🎯 Quick-Trigger QB",
        "💣 Deep-Ball Gunslinger",
    ]):
        if p_cols[idx].button(label, use_container_width=True):
            st.session_state.active_search_query = preset_queries[idx]

    col_s1, col_s2, col_s3 = st.columns([3.2, 1.0, 1.0])
    with col_s1:
        search_query = st.text_input(
            "Enter tactical scenario or player archetype:",
            key="active_search_query",
            placeholder="e.g., explosive vertical receiver who creates separation against man coverage",
        )
    with col_s2:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        run_search = st.button("🔍 Search Vector Index", type="primary", use_container_width=True)
    with col_s3:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        run_batch = st.button("🚀 Re-Index Top Players", type="secondary", use_container_width=True)

    if run_batch:
        with st.spinner("Embedding and indexing player profiles into PostgreSQL pgvector..."):
            try:
                b_res = httpx.post(f"{API_URL}/api/scout/batch-index", timeout=120.0)
                if b_res.status_code == 200:
                    st.success(f"Indexed {b_res.json().get('indexed_count', 0)} players into pgvector!")
                else:
                    st.error(f"Batch indexing failed with status code {b_res.status_code}")
            except httpx.TimeoutException:
                st.warning("Batch indexing timed out at 120s limit. Players processed before timeout remain stored.")
            except Exception as e:
                st.error(f"Indexing error: {e}")

    if run_search and search_query:
        with st.spinner("Embedding query & computing cosine similarity in pgvector..."):
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
                    st.caption(f"Showing top **{len(matches)}** semantic matches across **{total_indexed}** indexed scouting dossiers:")
                    grid_a, grid_b = st.columns(2, gap="medium")
                    for idx, m in enumerate(matches):
                        target_col = grid_a if idx % 2 == 0 else grid_b
                        score_pct = m["similarity_score"] * 100
                        with target_col:
                            with st.container(border=True):
                                st.markdown(f"### 🏈 {m['player_name']}")
                                st.progress(min(max(float(m["similarity_score"]), 0.0), 1.0), text=f"Semantic Match: {score_pct:.1f}%")
                                st.markdown(m["dossier"])
                else:
                    st.warning(f"Index holds {total_indexed} records. Click '🚀 Re-Index Top Players' to populate.")
            except Exception as e:
                st.error(f"Search request failed: {e}")

# ----------------- TAB 6: TELEMETRY -----------------
with tabs[5]:
    st.markdown("#### System Infrastructure & Pipeline Telemetry")
    health_data = fetch_api_json("/health", retries=1)
    api_online = bool(health_data)

    t1, t2, t3 = st.columns(3)
    t1.metric("FastAPI Backend Status", "ONLINE 🟢" if api_online else "OFFLINE 🔴", delta=API_URL, delta_color="off")
    t2.metric("Loaded Cohort Records", f"{len(df_rec) + len(df_qb)} Players", delta=f"{len(df_rec)} WR | {len(df_qb)} QB", delta_color="off")
    t3.metric("Vector Index Dimension", "768-dim Cosine", delta="pgvector HNSW / IVFFlat", delta_color="off")

    st.json({
        "internal_backend": API_URL,
        "external_backend": EXTERNAL_API_URL,
        "api_health_response": health_data or "Unreachable",
        "database_engine": "PostgreSQL 16 + pgvector",
        "vector_search_endpoint": f"{EXTERNAL_API_URL}/api/analytics/semantic-search",
        "simulation_endpoint": f"{EXTERNAL_API_URL}/api/analytics/matchup-simulation/{{player_id}}",
        "primary_model": os.getenv("PRIMARY_MODEL", "gemini-2.5-flash"),
        "fallback_model": os.getenv("FALLBACK_MODEL", "gemini-2.0-flash"),
        "embedding_model": "gemini-embedding-001 (768-dim MRL)",
    })
