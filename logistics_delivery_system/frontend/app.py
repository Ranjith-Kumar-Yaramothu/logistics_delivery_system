
import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Logistics Control Tower",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown("""
<style>
    .stApp {
        background-color: #F5F7FB;
    }

    [data-testid="stSidebar"] {
        background-color: #101D35;
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    .main-title {
        font-size: 30px;
        font-weight: 750;
        color: #142B4A;
        margin-bottom: 3px;
    }

    .sub-title {
        color: #64748B;
        font-size: 14px;
        margin-bottom: 22px;
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E5EAF2;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #142B4A;
        font-weight: 750;
    }

    .section-heading {
        color: #142B4A;
        font-size: 19px;
        font-weight: 700;
        margin-top: 12px;
        margin-bottom: 10px;
    }

    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #E5EAF2;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown("# 🚚 Logistics")
    st.caption("INTELLIGENT CONTROL TOWER")
    st.divider()

    st.markdown("### Navigation")
    st.caption("Use the page links above to navigate between Dashboard, Master Data, Deliveries, Route Planning, Exceptions and Analytics.")

    st.divider()

    st.markdown("### System")
    st.caption("Backend API")
    st.code(API, language=None)

    st.caption("Project: Delivery Route Optimization")

# --------------------------------------------------
# API HELPER
# --------------------------------------------------

def get_api_data(endpoint):
    try:
        response = requests.get(
            f"{API}{endpoint}",
            timeout=10
        )
        response.raise_for_status()
        return response.json(), None

    except requests.RequestException as error:
        return None, str(error)

# --------------------------------------------------
# HEADER
# --------------------------------------------------

header_left, header_right = st.columns([5, 1])

with header_left:
    st.markdown(
        '<div class="main-title">Intelligent Logistics Control Tower</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sub-title">Monitor delivery operations, fleet performance and route execution.</div>',
        unsafe_allow_html=True
    )

with header_right:
    if st.button("↻ Refresh", use_container_width=True):
        st.rerun()

st.divider()

# --------------------------------------------------
# FETCH LIVE DATA
# --------------------------------------------------

overview, overview_error = get_api_data("/analytics/overview")
delivery_summary, summary_error = get_api_data("/deliveries/summary")
routes, routes_error = get_api_data("/routes/")

# --------------------------------------------------
# API STATUS
# --------------------------------------------------

if overview_error:
    st.error("Backend API connection failed.")
    st.code(overview_error)
    st.info(
        "Start FastAPI in a separate PowerShell terminal using: "
        "python -m uvicorn backend.main:app --reload"
    )
    st.stop()

st.success("Backend API connected successfully.")

# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">Operations Overview</div>',
    unsafe_allow_html=True
)

total = overview.get("total_deliveries", 0)
assigned = overview.get("assigned_deliveries", 0)
route_count = overview.get("routes", 0)
distance = overview.get("planned_distance_km", 0)
assignment_rate = overview.get("assignment_rate_pct", 0)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Total Deliveries",
        f"{total:,}"
    )

with c2:
    st.metric(
        "Assigned Deliveries",
        f"{assigned:,}"
    )

with c3:
    st.metric(
        "Total Routes",
        f"{route_count:,}"
    )

with c4:
    st.metric(
        "Planned Distance",
        f"{distance:,.2f} km"
    )

st.write("")

# --------------------------------------------------
# ASSIGNMENT PERFORMANCE
# --------------------------------------------------

left, right = st.columns([2, 1])

with left:
    st.markdown(
        '<div class="section-heading">Assignment Performance</div>',
        unsafe_allow_html=True
    )

    st.progress(
        min(max(float(assignment_rate) / 100, 0.0), 1.0)
    )

    st.markdown(
        f"**{assignment_rate}%** of deliveries assigned"
    )

with right:
    st.markdown(
        '<div class="section-heading">Delivery Summary</div>',
        unsafe_allow_html=True
    )

    if summary_error:
        st.warning("Delivery summary is currently unavailable.")
    elif isinstance(delivery_summary, dict):
        st.write(f"**Status categories:** {len(delivery_summary)}")
        st.write(f"**Total deliveries:** {sum(delivery_summary.values())}")
    else:
        st.info("No delivery summary available.")

st.divider()

# --------------------------------------------------
# DELIVERY STATUS CHART
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">Delivery Status Distribution</div>',
    unsafe_allow_html=True
)

chart_left, chart_right = st.columns(2)

with chart_left:
    if summary_error:
        st.warning("Could not load delivery status chart.")
    elif isinstance(delivery_summary, dict) and delivery_summary:
        delivery_df = pd.DataFrame(
            list(delivery_summary.items()),
            columns=["Status", "Deliveries"]
        )

        fig = px.pie(
            delivery_df,
            names="Status",
            values="Deliveries",
            hole=0.58,
            title="Deliveries by Status"
        )

        fig.update_layout(
            template="plotly_white",
            height=350,
            margin=dict(l=20, r=20, t=55, b=20),
            legend_title_text="Delivery Status"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
    else:
        st.info("No delivery status data available.")

# --------------------------------------------------
# ROUTE STATUS CHART
# --------------------------------------------------

with chart_right:
    if routes_error:
        st.warning("Could not load route information.")
    elif isinstance(routes, list) and routes:
        route_df = pd.DataFrame(routes)

        if "status" in route_df.columns:
            status_df = (
                route_df["status"]
                .fillna("UNKNOWN")
                .value_counts()
                .rename_axis("Status")
                .reset_index(name="Routes")
            )

            fig = px.bar(
                status_df,
                x="Status",
                y="Routes",
                title="Routes by Status",
                text="Routes"
            )

            fig.update_layout(
                template="plotly_white",
                height=350,
                margin=dict(l=20, r=20, t=55, b=20),
                showlegend=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )
        else:
            st.info("Route status field is not available.")
    else:
        st.info("No routes available.")

st.divider()

# --------------------------------------------------
# RECENT ROUTES
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">Route Records</div>',
    unsafe_allow_html=True
)

if routes_error:
    st.warning("Route records could not be loaded.")
elif isinstance(routes, list) and routes:
    route_df = pd.DataFrame(routes)

    preferred_columns = [
        "route_id",
        "vehicle_id",
        "driver_id",
        "route_date",
        "status",
        "planned_distance_km",
        "planned_duration_minutes"
    ]

    display_columns = [
        col for col in preferred_columns
        if col in route_df.columns
    ]

    if display_columns:
        st.dataframe(
            route_df[display_columns],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.dataframe(
            route_df,
            use_container_width=True,
            hide_index=True
        )
else:
    st.info("No route records found. Generate routes from Route Planning.")

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Intelligent Logistics & Delivery Route Optimization System | "
    "Powered by Python, Streamlit, FastAPI and MySQL"
)
