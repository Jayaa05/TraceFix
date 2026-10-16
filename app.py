
import html
import streamlit as st
from tools import investigate_incident


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="TraceFix | Incident Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# GLOBAL STYLING
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --ink: #152238;
    --muted: #65758b;
    --teal: #087f72;
    --teal-dark: #06675e;
    --line: #e0e7ef;
    --canvas: #f4f7fb;
}

.stApp,
[data-testid="stAppViewContainer"] {
    background: var(--canvas) !important;
    color: var(--ink) !important;
    font-family: 'DM Sans', sans-serif !important;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3, h4 {
    font-family: 'Manrope', sans-serif !important;
    color: var(--ink) !important;
}

p, label, li {
    color: var(--ink);
}

[data-testid="stCaptionContainer"] p {
    color: var(--muted) !important;
}

.block-container {
    max-width: 1440px;
    padding-top: 1.8rem;
    padding-bottom: 2.5rem;
}

header[data-testid="stHeader"] {
    background: var(--canvas) !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid var(--line);
}

section[data-testid="stSidebar"] > div {
    background: #ffffff !important;
    padding-top: 1.5rem;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4 {
    color: var(--ink) !important;
}

section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: var(--muted) !important;
}

/* Input */
div[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: var(--ink) !important;
    border: 1px solid #d2dce8 !important;
    border-radius: 9px !important;
    min-height: 43px;
}

div[data-testid="stTextInput"] input:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 2px rgba(8,127,114,0.12) !important;
}

/* Buttons */
div.stButton > button {
    background: var(--teal) !important;
    color: #ffffff !important;
    border: 1px solid var(--teal) !important;
    border-radius: 10px !important;
    min-height: 44px;
    font-weight: 700 !important;
}

div.stButton > button:hover {
    background: var(--teal-dark) !important;
    border-color: var(--teal-dark) !important;
    color: #ffffff !important;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 3px 12px rgba(21,34,56,0.035);
}

div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] p {
    color: var(--muted) !important;
    font-weight: 600;
}

div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] > div {
    color: var(--ink) !important;
    font-weight: 800;
}

/* Runbook expander */
div[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    overflow: hidden;
}

div[data-testid="stExpander"] details,
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: #ffffff !important;
    color: #152238 !important;
}

div[data-testid="stExpander"] summary:hover {
    background: #f4f7fb !important;
}

div[data-testid="stAlert"] {
    border-radius: 12px;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# REUSABLE HTML HELPERS
# =========================================================
def render_html(content):
    """Render HTML as HTML, not as a Markdown code block."""
    st.html(content)


def render_panel(title, body=""):
    safe_title = html.escape(str(title))
    render_html(f"""
    <div style="
        background:#ffffff;
        border:1px solid #e0e7ef;
        border-radius:15px;
        padding:20px;
        margin-bottom:14px;
        box-shadow:0 3px 12px rgba(21,34,56,0.025);
    ">
        <div style="
            font-family:Manrope,sans-serif;
            font-size:17px;
            font-weight:800;
            color:#152238;
            margin-bottom:10px;
        ">{safe_title}</div>
        {body}
    </div>
    """)


def render_path_card(path):
    safe_path = html.escape(" → ".join(str(node) for node in path))
    render_html(f"""
    <div style="
        background:#ffffff;
        border:1px solid #dce6ef;
        border-radius:12px;
        padding:16px 18px;
        margin:10px 0;
        box-shadow:0 3px 10px rgba(21,34,56,0.03);
    ">
        <div style="
            color:#65758b;
            font-size:10px;
            font-weight:800;
            letter-spacing:1px;
            margin-bottom:8px;
        ">DEPENDENCY PATH</div>
        <div style="
            color:#087f72;
            font-size:14px;
            font-weight:700;
            line-height:1.8;
            overflow-wrap:anywhere;
        ">{safe_path}</div>
    </div>
    """)


def render_dependency_map(paths):
    """Build the visual map from paths returned by FalkorDB."""
    valid_paths = [path for path in paths if path]

    if not valid_paths:
        st.info("No dependency paths are available to visualize.")
        return

    unique_nodes = {
        str(node)
        for path in valid_paths
        for node in path
    }

    map_html = []

    for path in valid_paths:
        map_html.append("""
        <div style="
            display:flex;
            flex-wrap:wrap;
            align-items:center;
            gap:8px;
            margin:14px 0;
        ">
        """)

        for index, node in enumerate(path):
            safe_node = html.escape(str(node))
            is_target = index == len(path) - 1

            if is_target:
                background = "#fff4e5"
                border = "#f0c28b"
                color = "#94500d"
                label = "Incident target"
            else:
                background = "#e8f7f3"
                border = "#b9e4d8"
                color = "#086c5d"
                label = "Dependent service"

            map_html.append(f"""
            <div style="
                display:flex;
                flex-direction:column;
                gap:4px;
                align-items:center;
                justify-content:center;
                padding:11px 12px;
                border-radius:10px;
                min-width:110px;
                max-width:100%;
                background:{background};
                border:1px solid {border};
                color:{color};
            ">
                <span style="
                    font-size:13px;
                    font-weight:700;
                    overflow-wrap:anywhere;
                    text-align:center;
                ">{safe_node}</span>
                <span style="font-size:10px">{label}</span>
            </div>
            """)

            if index < len(path) - 1:
                map_html.append("""
                <span style="
                    color:#087f72;
                    font-size:20px;
                    font-weight:800;
                ">→</span>
                """)

        map_html.append("</div>")

    render_html("".join(map_html))

    st.caption(
        f"{len(unique_nodes)} unique nodes across "
        f"{len(valid_paths)} dependency path(s)."
    )


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    render_html("""
    <div style="
        font-family:Manrope,sans-serif;
        font-size:29px;
        font-weight:800;
        color:#152238;
    ">◈ TraceFix</div>
    """)

    st.caption("INCIDENT INTELLIGENCE")
    st.divider()

    st.markdown("#### New investigation")

    incident_id = st.text_input(
        "Incident ID",
        value="INC-001",
        placeholder="e.g. INC-001",
    )

    run = st.button(
        "Run investigation  →",
        type="primary",
        use_container_width=True,
    )

    st.divider()
    st.markdown("#### Technology")
    st.markdown("◈  FalkorDB graph database")
    st.markdown("✳  AI-assisted investigation")

    render_html("""
    <div style="
        margin-top:20px;
        padding:12px;
        background:#e8f7f3;
        border-radius:10px;
        color:#087064;
        font-size:12px;
        font-weight:700;
    ">BUILT FOR GRAPH HACKS 2026</div>
    """)

    st.caption("WeMakeDevs · Context for AI Agents")


# =========================================================
# HERO HEADER
# =========================================================
render_html("""
<div style="
    background:linear-gradient(120deg,#ffffff 0%,#e9f8f3 100%);
    border:1px solid #d5ebe4;
    border-radius:20px;
    padding:30px 32px;
    margin-bottom:24px;
    box-shadow:0 5px 20px rgba(21,34,56,0.025);
">
    <div style="
        display:inline-block;
        background:#d9f2e9;
        color:#07695d;
        padding:7px 11px;
        border-radius:7px;
        font-size:10px;
        font-weight:800;
        letter-spacing:1.1px;
        margin-bottom:15px;
    ">BUILT FOR GRAPH HACKS 2026</div>

    <div style="
        color:#087f72;
        font-size:11px;
        text-transform:uppercase;
        letter-spacing:1.7px;
        font-weight:800;
    ">GRAPH-POWERED OPERATIONS</div>

    <h1 style="
        font-family:Manrope,sans-serif;
        color:#152238;
        font-size:clamp(30px,3vw,43px);
        margin:10px 0;
        font-weight:800;
        line-height:1.2;
    ">Incident Intelligence</h1>

    <p style="
        color:#65758b;
        font-size:15px;
        margin:10px 0 0 0;
        line-height:1.7;
    ">
        Trace dependencies. Understand potential blast radius.
        Respond with evidence.
    </p>
</div>
""")


# =========================================================
# MAIN INVESTIGATION
# =========================================================
if run:
    if not incident_id.strip():
        st.warning("Please enter an incident ID.")

    else:
        with st.spinner(
            "Traversing graph relationships and collecting evidence..."
        ):
            try:
                result = investigate_incident(incident_id.strip())
            except Exception as exc:
                st.error(
                    "Investigation failed. Check your FalkorDB connection "
                    "and application logs."
                )
                with st.expander("Technical details"):
                    st.code(str(exc))
                st.stop()

        # Safely handle an unknown incident.
        if (
            not result
            or result.get("error")
            or not result.get("incident")
        ):
            st.error(f"Incident {incident_id.strip()} was not found.")
            st.info(
                "No affected services, dependency paths, or runbooks can be "
                "confirmed for this incident."
            )

        else:
            incident = result["incident"]

            direct = result.get("direct_dependents", []) or []
            indirect = result.get("indirect_dependents", []) or []
            paths = result.get("dependency_chains", []) or []
            runbooks = result.get("runbooks", []) or []

            affected = result.get("affected_services", []) or []
            if not affected:
                affected = list(dict.fromkeys(direct + indirect))

            safe_title = html.escape(
                str(incident.get("title", "Incident details"))
            )
            safe_id = html.escape(incident_id.strip())

            # -------------------------------------------------
            # INVESTIGATION REPORT
            # -------------------------------------------------
            render_html(f"""
            <div style="
                background:#ffffff;
                border:1px solid #e0e7ef;
                border-radius:15px;
                padding:24px 22px;
                margin:0 0 16px 0;
                box-shadow:0 3px 12px rgba(21,34,56,0.025);
            ">
                <div style="
                    color:#087f72;
                    font-size:11px;
                    text-transform:uppercase;
                    letter-spacing:1.7px;
                    font-weight:800;
                ">INVESTIGATION REPORT</div>

                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    gap:12px;
                    flex-wrap:wrap;
                    margin-top:12px;
                ">
                    <div style="
                        font-family:Manrope,sans-serif;
                        color:#152238;
                        font-size:21px;
                        font-weight:800;
                    ">{safe_title}</div>

                    <span style="
                        display:inline-block;
                        background:#e2f6e9;
                        color:#176c43;
                        padding:6px 10px;
                        border-radius:30px;
                        font-size:11px;
                        font-weight:800;
                    ">✓ Analysis complete</span>
                </div>

                <div style="
                    color:#65758b;
                    font-size:13px;
                    margin-top:12px;
                ">
                    Incident ID: {safe_id}
                    &nbsp;·&nbsp; Potential impact assessment
                </div>
            </div>
            """)

            # -------------------------------------------------
            # SUMMARY METRICS
            # -------------------------------------------------
            col1, col2, col3 = st.columns(3)

            col1.metric("Potentially affected", len(affected))
            col2.metric("Direct dependents", len(direct))
            col3.metric("Indirect dependents", len(indirect))

            # -------------------------------------------------
            # IMPACT ANALYSIS
            # -------------------------------------------------
            st.markdown("## Impact analysis")

            left, right = st.columns([0.95, 1.2], gap="large")

            with left:
                render_html("""
                <div style="
                    background:#ffffff;
                    border:1px solid #e0e7ef;
                    border-radius:15px;
                    padding:20px;
                    margin-bottom:14px;
                ">
                    <div style="
                        font-family:Manrope,sans-serif;
                        color:#152238;
                        font-size:17px;
                        font-weight:800;
                    ">Affected services</div>
                </div>
                """)

                st.markdown("**Direct dependents**")
                if direct:
                    for service in direct:
                        st.markdown(f"🟠 **{html.escape(str(service))}**")
                else:
                    st.caption("No direct dependents identified.")

                st.markdown("**Indirect dependents**")
                if indirect:
                    for service in indirect:
                        st.markdown(f"🟡 **{html.escape(str(service))}**")
                else:
                    st.caption("No indirect dependents identified.")

                st.caption(
                    "Graph relationships indicate potential impact, "
                    "not confirmed service failures."
                )

            with right:
                render_html("""
                <div style="
                    background:#ffffff;
                    border:1px solid #e0e7ef;
                    border-radius:15px;
                    padding:20px;
                    margin-bottom:14px;
                ">
                    <div style="
                        font-family:Manrope,sans-serif;
                        color:#152238;
                        font-size:17px;
                        font-weight:800;
                        margin-bottom:8px;
                    ">Dependency map</div>
                    <p style="
                        color:#65758b;
                        font-size:13px;
                        line-height:1.6;
                        margin:0;
                    ">Generated from dependency paths returned by FalkorDB.</p>
                </div>
                """)

                render_dependency_map(paths)

            # -------------------------------------------------
            # DEPENDENCY PATHS
            # -------------------------------------------------
            st.markdown("## Dependency paths")

            if paths:
                for path in paths:
                    if path:
                        render_path_card(path)
            else:
                st.info("No dependency paths were returned.")

            # -------------------------------------------------
            # RUNBOOK
            # -------------------------------------------------
            st.markdown("## Runbook & response guidance")

            if runbooks:
                for runbook in runbooks:
                    runbook_id = str(runbook.get("id", "Runbook"))
                    runbook_title = str(
                        runbook.get("title", "Troubleshooting steps")
                    )
                    safe_runbook_id = html.escape(runbook_id)
                    safe_runbook_title = html.escape(runbook_title)

                    with st.expander(
                        f"{runbook_id} · {runbook_title}",
                        expanded=True,
                    ):
                        st.write(
                            runbook.get("steps", "No steps recorded.")
                        )
            else:
                st.info("No linked runbooks were found.")

            # -------------------------------------------------
            # EVIDENCE AND CONFIDENCE
            # -------------------------------------------------
            st.markdown("## Evidence & confidence")

            st.warning(
                "Potential impact is inferred from stored graph relationships. "
                "Confirm actual failures and root cause using logs, metrics, "
                "or traces before drawing conclusions."
            )

            st.caption(
                "Evidence sources: incident records, service dependencies, "
                "and linked runbooks in FalkorDB."
            )


# =========================================================
# EMPTY STATE
# =========================================================
else:
    render_html("""
    <div style="
        background:#ffffff;
        border:1px solid #e0e7ef;
        border-radius:15px;
        padding:22px;
        margin-bottom:16px;
    ">
        <div style="
            font-family:Manrope,sans-serif;
            color:#152238;
            font-size:18px;
            font-weight:800;
            margin-bottom:8px;
        ">Ready to investigate?</div>
        <p style="
            color:#65758b;
            font-size:14px;
            line-height:1.7;
            margin:0;
        ">
            Enter an incident ID in the sidebar to inspect connected services,
            dependency paths, and troubleshooting guidance.
        </p>
    </div>
    """)

    col1, col2 = st.columns(2)

    with col1:
        render_html("""
        <div style="
            background:#ffffff;
            border:1px solid #e0e7ef;
            border-radius:14px;
            padding:20px;
        ">
            <div style="
                color:#087f72;
                font-size:10px;
                font-weight:800;
                letter-spacing:1.2px;
            ">EXAMPLE 01</div>
            <div style="
                color:#152238;
                font-family:Manrope,sans-serif;
                font-size:17px;
                font-weight:800;
                margin:9px 0;
            ">Known incident</div>
            <code>INC-001</code>
            <p style="color:#65758b;font-size:13px;line-height:1.6">
                Explore the sample database connection incident.
            </p>
        </div>
        """)

    with col2:
        render_html("""
        <div style="
            background:#ffffff;
            border:1px solid #e0e7ef;
            border-radius:14px;
            padding:20px;
        ">
            <div style="
                color:#087f72;
                font-size:10px;
                font-weight:800;
                letter-spacing:1.2px;
            ">EXAMPLE 02</div>
            <div style="
                color:#152238;
                font-family:Manrope,sans-serif;
                font-size:17px;
                font-weight:800;
                margin:9px 0;
            ">Unknown incident</div>
            <code>INC-999</code>
            <p style="color:#65758b;font-size:13px;line-height:1.6">
                Check that missing incidents are handled without fabricated evidence.
            </p>
        </div>
        """)


# =========================================================
# FOOTER
# =========================================================
st.divider()

st.markdown(
    "<p style='text-align:center;color:#718096;font-size:12px'>"
    "TraceFix · Explainable incident investigation · "
    "Built for Graph Hacks 2026</p>",
    unsafe_allow_html=True,
)
