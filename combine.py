import streamlit as st
import pandas as pd
import requests
from Backend import get_connection
from snowflake.connector.errors import ProgrammingError

st.set_page_config(page_title="Search Orders & Records", layout="centered")
st.title("🔍 Search Records and Orders")

# Input fields
email_input = st.text_input("Enter Email", placeholder="example@domain.com")
phone_input = st.text_input("Enter Phone Number", placeholder="123-456-7890")

if email_input and phone_input:
    st.session_state.email = email_input
    st.session_state.phone = phone_input

# -------------------- Search Records --------------------
if email_input and phone_input:
    RECORDS_API_URL = "http://localhost:8000/search"  # FastAPI endpoint for user records

    def search_records_from_api(email: str, phone: str):
        payload = {"email": email, "phone": phone}
        try:
            response = requests.post(RECORDS_API_URL, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to connect to the API: {e}")
            return None

    with st.expander("📧 Search for User Records"):
        if st.button("Search Records"):
            with st.spinner("🔍 Searching..."):
                result_tables = search_records_from_api(email_input, phone_input)

                if not result_tables:
                    st.info("No matching records found.")
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
                        st.subheader("✅ Match found in one or more tables")
                        st.dataframe(final_df)
                        st.markdown(f"**📧 Email used for search:** `{email_input}`")
                    else:
                        st.info("No first and last name found.")

# -------------------- Search Orders (via API) --------------------
if 'email' in st.session_state and 'phone' in st.session_state:
    email_input = st.session_state.email
    ORDER_API_URL = "http://localhost:8000/search_order"  # FastAPI endpoint for orders

    def search_orders_from_api(email: str):
        try:
            response = requests.get(ORDER_API_URL, params={"email": email})
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to connect to the API: {e}")
            return None

    with st.expander("📦 Search for Orders by Email"):
        if st.button("Search Orders"):
            with st.spinner("🔍 Searching Orders..."):
                order_data = search_orders_from_api(email_input)

                if not order_data:
                    st.info("No matching orders found.")
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
                            st.subheader("✅ Match found in one or more tables")
                            st.dataframe(display_df)
                        except KeyError:
                            st.error("❌ Required columns not found: 'OrderNumber', 'Description', 'OrderDate'")
                    else:
                        st.info("No valid rows found in any table.")

# -------------------- Footer --------------------
st.markdown(
    """
    <style>
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)
