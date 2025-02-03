import boto3
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from io import StringIO
import os
import plotly.express as px

from utils import BUCKET_NAME, read_csv_from_s3

st.set_page_config(page_title="Trend", page_icon=":moneybag:", layout="wide")
st.markdown("# Sommaire")
st.sidebar.header("Accueil")

# Load environment variables from .env file
load_dotenv()

# AWS credentials and bucket information
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
is_prod = True if os.getenv('PRODUCTION_ENV') == '1' else False

ENV_FOLDER = 'prod' if is_prod else 'local'
FILE_KEY_OUTPUT = '/output/combined_transactions.csv'
FILE_KEY_BUDGET = 'shared/budget_2025.xlsx'

# Initialize a session using Amazon S3
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

# Load output data
body_output = read_csv_from_s3(s3, BUCKET_NAME, ENV_FOLDER+FILE_KEY_OUTPUT)
if body_output is None:
    st.error('No data available. Please import transactions first.')
    st.stop()



df_output = pd.read_csv(StringIO(body_output), index_col=False)
# Ensure the Date column is in datetime format
df_output['Date'] = pd.to_datetime(df_output['Date'], errors='coerce')


# Create a bar chart showing expenses and credit for each month
df_output['Month'] = df_output['Date'].dt.to_period('M').astype(str)  # Convert Period to string
monthly_summary = df_output.groupby(['Month', 'Type'])['Amount'].sum().reset_index()
fig_summary = px.bar(monthly_summary, x='Month', y='Amount', color='Type', barmode='group', title='Revenus vs Depenses par mois')


# display side by side on nice box values for the total expenses and total credits for the current month
current_month = df_output['Month'].max()
total_expenses = df_output[(df_output['Type'] == 'expense') & (df_output['Month'] == current_month)]['Amount'].sum()
total_credits = df_output[(df_output['Type'] == 'credit') & (df_output['Month'] == current_month)]['Amount'].sum()


# show in a table the total expenses and total credits for the current month
current_month_summary = df_output[df_output['Month'] == current_month].pivot_table(columns='Type', values='Amount', aggfunc='sum').reset_index(drop=True)

col1, col2 = st.columns((1,2))
with col1:
    st.markdown(f"## Mois courant: {current_month}")
    col11, col12 = st.columns(2)
    col11.metric("Revenus", current_month_summary["credit"])
    col12.metric("Depenses", current_month_summary["expense"])

with col2:
    st.plotly_chart(fig_summary)



# Display the charts side by side
col1, col2 = st.columns(2)
with col1:
    # Filter by month and year
    selected_month = st.selectbox('Select a Month', df_output['Month'].unique())
    filtered_data = df_output[df_output['Month'] == selected_month]
    # Create a bar chart for expense distribution by category
    category_distribution = filtered_data[filtered_data['Type'] == 'expense'].groupby('Category')[
        'Amount'].sum().reset_index().sort_values(by='Amount', ascending=True)
    fig_category = px.bar(category_distribution, x='Amount', y='Category', orientation='h',
                          title='Expense Distribution by Category')
    st.plotly_chart(fig_category)
with col2:
    # Create a bar chart for sub-category distribution within a selected category
    selected_category = st.selectbox('Select a Category', category_distribution['Category'].unique())
    sub_category_distribution = \
    filtered_data[(filtered_data['Type'] == 'expense') & (filtered_data['Category'] == selected_category)].groupby(
        'Sub Category')['Amount'].sum().reset_index()
    fig_sub_category = px.bar(sub_category_distribution, x='Sub Category', y='Amount',
                              title=f'Expense Distribution in {selected_category}')
    st.plotly_chart(fig_sub_category)


# Display the data in Streamlit
st.title('Transactions consolidées')
st.dataframe(df_output)