
import streamlit as st
import requests
import pandas as pd
import os

API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Route Exceptions",
    page_icon="⚠️",
    layout="wide"
)

st.title("⚠️ Route Exceptions")
st.caption("Simulate routes and detect delivery anomalies")

st.divider()

# Fetch available routes
try:
    response = requests.get(
        f"{API}/routes/",
        timeout=10
    )
    response.raise_for_status()
    routes = response.json()

except requests.RequestException as e:
    st.error("Unable to connect to FastAPI.")
    st.code(str(e))
    st.stop()

if not routes:
    st.warning("No routes available. Generate routes first.")
    st.stop()

# Prepare route options
route_ids = [
    route["route_id"]
    for route in routes
]

selected_route = st.selectbox(
    "Select Route",
    route_ids
)

# Display selected route details
selected_data = next(
    route for route in routes
    if route["route_id"] == selected_route
)

st.subheader("Selected Route Details")

c1, c2, c3 = st.columns(3)

c1.metric("Route ID", selected_data["route_id"])
c2.metric("Vehicle ID", selected_data["vehicle_id"])
c3.metric("Driver ID", selected_data["driver_id"])

st.write("Route Status:", selected_data["status"])

st.divider()

# Route simulation
st.subheader("1. Simulate Route")

st.write(
    "Run the route simulation to generate actual arrival "
    "and departure times for its stops."
)

if st.button("Simulate Selected Route", type="primary"):
    try:
        response = requests.post(
            f"{API}/routes/{selected_route}/simulate",
            timeout=30
        )
        response.raise_for_status()

        st.success("Route simulation completed successfully.")

        st.json(response.json())

    except requests.RequestException as e:
        st.error("Route simulation failed.")
        if e.response is not None:
            st.code(e.response.text)
        else:
            st.code(str(e))

st.divider()

# Anomaly detection
st.subheader("2. Detect Anomalies")

st.write(
    "Check the selected route for capacity, timing, "
    "delivery sequence and other route exceptions."
)

if st.button("Detect Anomalies"):
    try:
        response = requests.get(
            f"{API}/routes/{selected_route}/anomalies",
            timeout=30
        )
        response.raise_for_status()

        anomalies = response.json()

        if anomalies:
            st.error(f"Detected {len(anomalies)} anomaly(s).")

            if isinstance(anomalies, list):
                st.dataframe(
                    pd.DataFrame(anomalies),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.json(anomalies)

        else:
            st.success("No anomalies detected for this route.")
            st.info(
                "The selected route passed the current "
                "anomaly detection checks."
            )

    except requests.RequestException as e:
        st.error("Anomaly detection failed.")
        if e.response is not None:
            st.code(e.response.text)
        else:
            st.code(str(e))

st.divider()

st.caption("Route Exceptions | Logistics Control Tower")
