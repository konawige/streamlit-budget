import boto3
import streamlit as st
from utils import BUCKET_NAME, FILE_KEY_BUDGET, load_budget_sheet

st.set_page_config(page_title="Budget", page_icon=":moneybag:", layout="wide")
st.markdown("# Budget 2025")
st.sidebar.header("Budget 2025")

if st.session_state["password_correct"] is False:
    st.info("Please enter the password in the homepage to access the data.")
    st.stop()

# Access secrets
aws_access_key_id = st.secrets["credentials"]["aws_access_key_id"]
aws_secret_access_key = st.secrets["credentials"]["aws_secret_access_key"]




# Initialize a session using Amazon S3
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

# Load data
df_sub_cat = load_budget_sheet(s3, BUCKET_NAME, FILE_KEY_BUDGET,"Détails budget")

# Display the data in Streamlit
st.title('Repartition des dépenses')

st.dataframe(df_sub_cat)
