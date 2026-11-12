import streamlit as st
import requests
import os
import pandas as pd
from datetime import date

API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.title("Route Planning")

plan_date = st.date_input(
    "Planning date",
    value=date(2026, 11, 1),
    format="YYYY-MM-DD"
)

limit = st.number_input(
    "Maximum deliveries to plan",
    min_value=1,
    max_value=2000,
    value=100
)

st.write("Selected date:", plan_date.strftime("%Y-%m-%d"))

if st.button("Generate routes"):
    try:
        response = requests.post(
            f"{API}/routes/plan",
            json={
                "plan_date": plan_date.isoformat(),
                "max_deliveries": int(limit)
            },
            timeout=60
        )

        if response.ok:
            result = response.json()
            st.success(
                f'Assigned: {result["assigned"]} | '
                f'Unserved: {result["unserved"]}'
            )
            st.write("Routes:", result["routes"])
        else:
            st.error(f"API Error ({response.status_code})")
            st.code(response.text)

    except requests.RequestException as e:
        st.error(f"Cannot connect to FastAPI: {e}")

st.subheader("Existing Routes")

try:
    response = requests.get(
        f"{API}/routes/",
        params={"plan_date": plan_date.isoformat()},
        timeout=30
    )
    response.raise_for_status()

    routes = response.json()
    if routes:
        st.dataframe(pd.DataFrame(routes), use_container_width=True)
    else:
        st.info("No routes found for this date.")

except requests.RequestException as e:
    st.error(f"API error: {e}")
