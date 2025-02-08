import boto3
import streamlit as st
import pandas as pd

from utils import display_category_form, listRBCCol, parse_rbc_data, FILE_KEY_BUDGET, BUCKET_NAME, set_category, \
    stage_data, listNBCCol, parse_bnc_data, listNBCColCredit, parse_bnc_credit_data, listScotiaCol, parse_scotia_data

st.set_page_config(page_title="New transactions", page_icon=":form:", layout="wide")
st.markdown("# Import new transactions")
st.sidebar.header("Import")

# validate session state has the key password_correct

if "password_correct" not in st.session_state or st.session_state["password_correct"] is  False:
    st.info("Please enter the password in the homepage to access the data.")
    st.stop()

# Access secrets
aws_access_key_id = st.secrets["credentials"]["aws_access_key_id"]
aws_secret_access_key = st.secrets["credentials"]["aws_secret_access_key"]

is_prod = True if st.secrets["env"]["production_env"] == "1" else False

ENV_FOLDER = 'prod' if is_prod else 'local'

bucket_name = "wikomexpensetracker"
file_rbc_account = "rbc_account.csv"
file_bnc_checking_009 = "bnc_check_009.csv"
file_bnc_mastercard_2110 = "bnc_mastercard_2110.csv"
file_scotia_checking_2080 = "scotia_checking_2080.csv"
FILE_OUTPUT_TRANSFORMED = "combined_transactions.csv"



# Initialize a session using Amazon S3
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

# Initialize session state for storing form data
if 'form_data' not in st.session_state:
    st.session_state.form_data = None

def parse_transaction(account, uploaded_file):
    
    if account == 'RBC':
        df = pd.read_csv(uploaded_file, names=listRBCCol, index_col=False, skiprows=1)
        # stage data
        staging_rbc_cheque_object = ENV_FOLDER + '/staging/' + file_rbc_account
        stage_data(df, s3, BUCKET_NAME, staging_rbc_cheque_object)
        return parse_rbc_data(df)
    elif account == 'NBC Cheque':
        df = pd.read_csv(uploaded_file, names=listNBCCol, index_col=False,sep=';', skiprows=1)
        # stage data
        staging_nbc_cheque_object = ENV_FOLDER + '/staging/' + file_bnc_checking_009
        stage_data(df, s3, BUCKET_NAME, staging_nbc_cheque_object)
        return parse_bnc_data(df)
    elif account == 'NBC Credit':
        df = pd.read_csv(uploaded_file, names=listNBCColCredit, index_col=False,sep=';', skiprows=1)
        # stage data
        staging_nbc_credit_object = ENV_FOLDER + '/staging/' + file_bnc_mastercard_2110
        stage_data(df, s3, BUCKET_NAME, staging_nbc_credit_object)
        return parse_bnc_credit_data(df)
    elif account == 'Scotia':
        df = pd.read_csv(uploaded_file, names=listScotiaCol, index_col=False, skiprows=1)
        # stage data
        staging_scotia_object = ENV_FOLDER + '/staging/' + file_scotia_checking_2080
        stage_data(df, s3, BUCKET_NAME, staging_scotia_object)
        return parse_scotia_data(df, 'Checking')
    else:
        pass




# Create a form to upload a file. The form should has a dropdown list to select the account

with st.form(key=f'form_import'):
    account = st.selectbox('Compte', ['RBC', 'NBC Cheque', 'NBC Credit', 'Scotia'])
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx'])
    submit_button = st.form_submit_button(label='Submit')
    if submit_button:
        st.write(f'You selected {account}')
        st.write(f'You uploaded {uploaded_file.name}')
        if uploaded_file is not None:
            (ret, parsed_data) = parse_transaction(account, uploaded_file)
            if ret != 100:
                # generate some errors and ask to verify file
                st.text("Error happened")
            else:             
                # store form data in session
                st.session_state.form_data = parsed_data
        

if st.session_state.form_data is not None:
    st.write("run the transaction logs")
    catogories, sub_categories = set_category(s3,BUCKET_NAME, FILE_KEY_BUDGET)
    # build output key file
    output_file = ENV_FOLDER + '/output/' + FILE_OUTPUT_TRANSFORMED
    display_category_form(st.session_state.form_data, catogories, sub_categories,s3,output_file)
