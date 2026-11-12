
import os
import requests
import streamlit as st

API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Data Exports",
    page_icon="📥",
    layout="wide"
)

st.title("Data Export Center")
st.caption("Download logistics operational data and analytics reports.")

st.divider()


def get_export(endpoint):
    try:
        response = requests.get(
            f"{API}{endpoint}",
            timeout=120
        )
        response.raise_for_status()
        return response.content, None

    except requests.RequestException as error:
        return None, str(error)


exports = [
    {
        "title": "Deliveries",
        "description": "Download all delivery records.",
        "endpoint": "/exports/deliveries.csv",
        "filename": "deliveries.csv",
        "mime": "text/csv"
    },
    {
        "title": "Routes",
        "description": "Download planned and completed routes.",
        "endpoint": "/exports/routes.csv",
        "filename": "routes.csv",
        "mime": "text/csv"
    },
    {
        "title": "Route Stops",
        "description": "Download route stop sequences and timings.",
        "endpoint": "/exports/route-stops.csv",
        "filename": "route_stops.csv",
        "mime": "text/csv"
    },
    {
        "title": "Anomaly Report",
        "description": "Download detected route anomalies.",
        "endpoint": "/exports/anomalies.csv",
        "filename": "anomaly_report.csv",
        "mime": "text/csv"
    },
    {
        "title": "Analytics Workbook",
        "description": "Download the Excel workbook containing summary, delivery, route, stop and outcome sheets.",
        "endpoint": "/exports/analytics.xlsx",
        "filename": "logistics_analytics.xlsx",
        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
]

st.subheader("Available Downloads")

for start in range(0, len(exports), 2):
    columns = st.columns(2)

    for column, item in zip(columns, exports[start:start + 2]):
        with column:
            with st.container(border=True):
                st.subheader(item["title"])
                st.write(item["description"])

                file_data, error = get_export(item["endpoint"])

                if error:
                    st.error("Export failed.")
                    st.caption(error)
                else:
                    st.download_button(
                        label=f"Download {item['title']}",
                        data=file_data,
                        file_name=item["filename"],
                        mime=item["mime"],
                        use_container_width=True,
                        key=f"download_{item['filename']}"
                    )

st.divider()

st.caption(
    "Intelligent Logistics & Delivery Route Optimization System | "
    "Powered by FastAPI, Streamlit and MySQL"
)
