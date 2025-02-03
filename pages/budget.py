import boto3
from dotenv import load_dotenv
import streamlit as st
import os

from utils import BUCKET_NAME, FILE_KEY_BUDGET, load_budget_sheet

st.set_page_config(page_title="Budget", page_icon=":moneybag:", layout="wide")
st.markdown("# Budget 2025")
st.sidebar.header("Budget 2025")

# Load environment variables from .env file
load_dotenv()

# AWS credentials and bucket information
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
is_prod = True if os.getenv('PRODUCTION_ENV') == '1' else False

ENV_FOLDER = 'prod' if is_prod else 'local'
FILE_KEY_OUTPUT = 'output/combined_transactions.csv'

# Initialize a session using Amazon S3
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

# Load data
df_sub_cat = load_budget_sheet(s3, BUCKET_NAME, FILE_KEY_BUDGET,"Détails budget")

# Display the data in Streamlit
st.title('Repartition des dépenses')

st.dataframe(df_sub_cat)
