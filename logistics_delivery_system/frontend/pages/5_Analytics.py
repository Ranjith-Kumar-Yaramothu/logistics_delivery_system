
import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Operations Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("Operations Analytics")
st.caption("Delivery performance, route execution and fleet operations")

if st.button("Refresh Analytics"):
    st.rerun()

try:
    response = requests.get(
        f"{API}/analytics/overview",
        timeout=10
    )
    response.raise_for_status()

    data = response.json()

    st.success("Analytics data loaded successfully.")

    st.subheader("Delivery Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Deliveries",
        data["total_deliveries"]
    )

    c2.metric(
        "Pending",
        data["pending_deliveries"]
    )

    c3.metric(
        "Assigned",
        data["assigned_deliveries"]
    )

    c4.metric(
        "Delivered",
        data["delivered_deliveries"]
    )

    st.divider()

    st.subheader("Delivery Performance")

    left, right = st.columns(2)

    status_data = data["delivery_status"]

    df = pd.DataFrame({
        "Status": list(status_data.keys()),
        "Deliveries": list(status_data.values())
    })

    with left:
        st.plotly_chart(
            px.pie(
                df,
                names="Status",
                values="Deliveries",
                hole=0.45,
                title="Delivery Status Distribution"
            ),
            use_container_width=True
        )

    with right:
        st.metric(
            "Assignment Rate",
            f'{data["assignment_rate_pct"]}%'
        )

        st.progress(
            min(data["assignment_rate_pct"] / 100, 1.0)
        )

        st.metric(
            "Total Routes",
            data["routes"]
        )

        st.metric(
            "Completed Routes",
            data["completed_routes"]
        )

    st.divider()

    st.subheader("Route Performance")

    r1, r2 = st.columns(2)

    r1.metric(
        "Planned Distance",
        f'{data["planned_distance_km"]} km'
    )

    completion_rate = (
        data["completed_routes"] / data["routes"] * 100
        if data["routes"] else 0
    )

    r2.metric(
        "Route Completion Rate",
        f"{completion_rate:.2f}%"
    )

except requests.RequestException as e:
    st.error(f"Cannot connect to backend API: {e}")

except (KeyError, ValueError) as e:
    st.error(f"Invalid analytics response: {e}")
