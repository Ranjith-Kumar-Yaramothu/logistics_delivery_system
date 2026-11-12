import streamlit as st, requests, os
API=os.getenv("API_BASE_URL","http://127.0.0.1:8000")
st.title("Route Exceptions")
route_id=st.text_input("Route ID")
if st.button("Detect anomalies") and route_id:
    r=requests.get(f"{API}/routes/{route_id}/anomalies")
    if r.ok: st.json(r.json())
    else: st.error(r.text)
if st.button("Simulate route") and route_id:
    r=requests.post(f"{API}/routes/{route_id}/simulate")
    if r.ok: st.json(r.json())
    else: st.error(r.text)
