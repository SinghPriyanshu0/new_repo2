import streamlit as st
import pandas as pd
from Backend import get_connection
from snowflake.connector.errors import ProgrammingError

st.set_page_config(page_title="Search Orders by Email", layout="centered")
st.title("📦 Search Orders in Snowflake by Email")

# Input field
email_input = st.text_input("Enter Email to Search")

def search_records(email):
    all_matches = []

    try:
        conn = get_connection()
        cur = conn.cursor()
        schema_name = 'SC'
        tables = ['Order1', 'Order2', 'Order3']

        for table in tables:
            query = f"""
                SELECT * FROM {schema_name}.{table}
                WHERE Email = %s
            """
            cur.execute(query, (email,))
            rows = cur.fetchall()
            if rows:
                colnames = [desc[0] for desc in cur.description]
                df = pd.DataFrame(rows, columns=colnames)
                df["SourceTable"] = table
                all_matches.append(df)

        cur.close()
        conn.close()
    except ProgrammingError as e:
        st.error(f"❌ Programming error: {e}")
    except Exception as e:
        st.error(f"❌ Failed to search: {e}")
    
    if all_matches:
        return pd.concat(all_matches, ignore_index=True)
    else:
        return None

# Search action
if st.button("Search"):
    if not email_input:
        st.warning("Please enter an email address.")
    else:
        with st.spinner("🔍 Searching..."):
            final_result = search_records(email_input)
            if final_result is None or final_result.empty:
                st.info("No matching records found in Order1, Order2, or Order3.")
            else:
                # Normalize column names to lowercase for safe selection
                final_result.columns = [col.lower() for col in final_result.columns]

                # Try to select only the required columns
                try:
                    display_df = final_result[["sourcetable", "ordernumber", "description", "orderdate"]]
                    st.subheader("✅ Match found in one or more tables")
                    st.dataframe(display_df)
                except KeyError as e:
                    st.error("❌ Required columns not found: 'OrderNumber', 'Description', 'OrderDate'")
