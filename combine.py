import streamlit as st
import pandas as pd
import requests
from Backend import get_connection
from snowflake.connector.errors import ProgrammingError

st.set_page_config(page_title="🔎 Smart Search Portal", layout="centered")

# -------------------- Custom CSS --------------------
st.markdown("""
    <style>
    html, body, .main {
        background: linear-gradient(to right, #e0f7fa, #e1bee7);
        font-family: 'Segoe UI', sans-serif;
        color: #333;
    }
    h1, h2, h3 {
        color: #4a148c;
    }
    .stTextInput>div>div>input {
        background-color: #ffffffdd;
        border: 2px solid #ce93d8;
        border-radius: 8px;
        padding: 10px;
    }
    .stButton>button {
        background-color: #6a1b9a;
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        border-radius: 12px;
        transition: all 0.3s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #8e24aa;
        transform: scale(1.03);
    }
    .stDataFrame {
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.1);
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .section-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #4a148c;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌐 Smart Search: Records & Orders")

# -------------------- Input Section --------------------
with st.container():
    st.markdown("### 📨 User Information")
    email_input = st.text_input("📧 Enter Email", placeholder="example@domain.com")
    phone_input = st.text_input("📞 Enter Phone Number", placeholder="123-456-7890")

    if email_input and phone_input:
        st.session_state.email = email_input
        st.session_state.phone = phone_input

# -------------------- Search Records --------------------
if email_input and phone_input:
    RECORDS_API_URL = "http://localhost:8000/search"

    def search_records_from_api(email: str, phone: str):
        try:
            response = requests.post(RECORDS_API_URL, json={"email": email, "phone": phone})
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to connect to the API: {e}")
        return None

    with st.expander("🔍 Search 🔹 User Records"):
        if st.button("📂 Fetch Records"):
            with st.spinner("Looking for matching records..."):
                result_tables = search_records_from_api(email_input, phone_input)
                if not result_tables:
                    st.info("🙅 No matching records found.")
                else:
                    unified_id = None
                    combined_rows = []

                    for table_data in result_tables:
                        table_name = table_data["table_name"]
                        rows = table_data["rows"]
                        if rows:
                            df = pd.DataFrame(rows)
                            df.columns = [col.lower() for col in df.columns]
                            if table_name == "Table1" and "unified_id" in df.columns:
                                unified_id = df["unified_id"].iloc[0]

                    for table_data in result_tables:
                        table_name = table_data["table_name"]
                        rows = table_data["rows"]
                        if rows:
                            df = pd.DataFrame(rows)
                            df.columns = [col.lower() for col in df.columns]
                            df_final = pd.DataFrame({
                                "unified_id": unified_id,
                                "firstname": df.get("firstname", ""),
                                "lastname": df.get("lastname", ""),
                                "source_table": table_name
                            })
                            combined_rows.append(df_final)

                    if combined_rows:
                        final_df = pd.concat(combined_rows, ignore_index=True).drop_duplicates()
                        st.success("🎉 User records found!")
                        st.dataframe(final_df)
                        st.markdown(f"🔎 **Searched Email:** `{email_input}`")
                    else:
                        st.warning("No names found across the tables.")

# -------------------- Search Orders (via API) --------------------
if 'email' in st.session_state and 'phone' in st.session_state:
    email_input = st.session_state.email
    ORDER_API_URL = "http://localhost:8000/search_order"

    def search_orders_from_api(email: str):
        try:
            response = requests.get(ORDER_API_URL, params={"email": email})
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to connect to the API: {e}")
        return None

    with st.expander("📦 Search 🔹 Order History"):
        if st.button("🧾 Fetch Orders"):
            with st.spinner("Looking up orders..."):
                order_data = search_orders_from_api(email_input)

                if not order_data:
                    st.info("🫤 No orders found.")
                else:
                    all_matches = []
                    for table_name, rows in order_data.items():
                        if rows:
                            df = pd.DataFrame(rows)
                            df["sourcetable"] = table_name
                            all_matches.append(df)

                    if all_matches:
                        final_df = pd.concat(all_matches, ignore_index=True)
                        final_df.columns = [col.lower() for col in final_df.columns]
                        try:
                            display_df = final_df[["sourcetable", "ordernumber", "description", "orderdate"]]
                            st.success("📦 Orders found across sources!")
                            st.dataframe(display_df)
                        except KeyError:
                            st.error("Missing required columns like 'OrderNumber', 'Description', or 'OrderDate'")
                    else:
                        st.info("No valid rows found.")

# -------------------- Footer --------------------
st.markdown("""
    <hr/>
    <div style="text-align: center; font-size: 0.9rem; color: #666;">
        ⛏️ Crafted with ❤️ using <b>Streamlit</b> | © 2025 Bytepx
    </div>
""", unsafe_allow_html=True)
