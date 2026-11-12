import streamlit as st, requests, os, pandas as pd
API=os.getenv("API_BASE_URL","http://127.0.0.1:8000")
st.title("Master Data")
try:
    sites=requests.get(f"{API}/sites/").json()
    vehicles=requests.get(f"{API}/vehicles/").json()
    c1,c2=st.columns(2)
    c1.metric("Customer sites",len(sites))
    c2.metric("Vehicles",len(vehicles))
    st.subheader("Customer sites")
    st.dataframe(pd.DataFrame(sites),use_container_width=True)
    st.subheader("Vehicles")
    st.dataframe(pd.DataFrame(vehicles),use_container_width=True)
except Exception as e: st.error(f"API error: {e}")
