import streamlit as st, requests, os, pandas as pd
API=os.getenv("API_BASE_URL","http://127.0.0.1:8000")
st.title("Delivery Management")
status=st.selectbox("Status",["All","PENDING","ASSIGNED"])
try:
    params={} if status=="All" else {"status":status}
    data=requests.get(f"{API}/deliveries/",params=params).json()
    st.dataframe(pd.DataFrame(data),use_container_width=True)
except Exception as e: st.error(f"API error: {e}")
