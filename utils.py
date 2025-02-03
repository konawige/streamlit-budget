# Fetch the CSV file from S3
from io import BytesIO, StringIO
import streamlit as st
import pandas as pd
from botocore.exceptions import NoCredentialsError, ClientError

BUCKET_NAME = 'wikomexpensetracker'
FILE_KEY_BUDGET = 'shared/budget_2025.xlsx'
FILENAME_RBC_CHEQUE_STAGING = 'rbc_checking_5336995.csv'

cleanedCol = ['Date', 'Name', 'Account', 'Type', 'Category',
              'Sub Category', 'Amount', 'Description', 'To Ignore']
listRBCCol = ['Type de compte', 'Numéro du compte', "Date de l'opération", "Numéro du chèque",
              "Description 1", "Description 2", "CAD", "USD"]
listNBCCol = ['Date', 'Description', "Categorie", "Debit",
              "Credit", "Solde"]

listNBCColCredit = ['Date', 'Numero de Carte', "Description", "Categorie", "Debit",
                    "Credit"]
listScotiaCol = ['Filtre', 'Date', 'Description',
                 'Sous-description', 'Type d’opération', 'Montant', 'Solde']


@st.cache_data
def load_budget_sheet(_s3, bucket_name, key_file_budget, sheet_name):
    """
    Load a budget sheet from an S3 bucket.

    Parameters:
    _s3 (boto3.client): The S3 client object.
    bucket_name (str): The name of the S3 bucket.
    key_file_budget (str): The key (path) to the budget file in the S3 bucket.
    sheet_name (str): The name of the sheet within the Excel file to load.

    Returns:
    pandas.DataFrame: The loaded budget sheet as a DataFrame.
    """
    obj = _s3.get_object(Bucket=bucket_name, Key=key_file_budget)
    data = obj['Body'].read()
    df = pd.read_excel(BytesIO(data), sheet_name=sheet_name)
    return df


def read_csv_from_s3(s3_client, bucket, file_key):
    """
    Reads a CSV file from an S3 bucket and returns its content as a string.

    Parameters:
    s3_client (boto3.client): The S3 client object.
    BUCKET_NAME (str): The name of the S3 bucket.
    file_key (str): The key (path) of the file in the S3 bucket.

    Returns:
    str: The content of the CSV file as a string.
    """
    try:
        obj = s3_client.get_object(Bucket=bucket, Key=file_key)
    except ClientError as e:
        return None

    data = obj['Body'].read().decode('utf-8')
    return data


def set_category(s3, bucket_name, file_key_budget):
    df_cat = load_budget_sheet(
        s3, bucket_name, file_key_budget, "Listes de recherche")
    df_sub_cat = load_budget_sheet(
        s3, bucket_name, file_key_budget, "Détails budget")
    categories = df_cat['Recherche catégorie budget'].unique()
    category_dict = {}
    for category in categories:
        sub_categories = df_sub_cat[df_sub_cat['Catégorie'] == category]['Description'].unique()

        # Add a default sub category to all categories
        sub_categories = [category + ' - Autre'] + list(sub_categories)
        category_dict[category] = sub_categories

    return categories, category_dict


def parse_rbc_data(data):
    nb_col = data.shape[1]
    if nb_col != len(listRBCCol):
        return 101, pd.DataFrame()
    if 'Type de compte' in list(data.columns):
        data['Type de compte'] = data['Type de compte'].astype(
            str).replace(to_replace='Chèques', value='Checking')
        data['Type de compte'] = data['Type de compte'].astype(
            str).replace(to_replace='MasterCard', value='Credit Card')
        data = data.rename(columns={'Type de compte': 'Account'})

    else:
        return 102, pd.DataFrame()
    if "Date de l'opération" in list(data.columns):
        data = data.rename(columns={"Date de l'opération": 'Date'})
        #Date is in format mm/dd/yyyy. Set it to yyyy-mm-dd
        data['Date'] = pd.to_datetime(data['Date'], format='%m/%d/%Y').dt.strftime('%Y-%m-%d')
    else:
        return 102, pd.DataFrame()

    if 'Description 1' in list(data.columns) and 'Description 2' in list(data.columns):
        # data['Description'] = data['Description 1'].astype(str) + ' / '+ data['Description 2'].astype(str)
        # Create a new column 'Description' based on the values of 'Description 1' and 'Description 2'
        data['Description'] = data.apply(
            lambda row: ' / '.join(filter(pd.notna, [row['Description 1'], row['Description 2']])), axis=1)
    else:
        return 102, pd.DataFrame()

    if 'CAD' in list(data.columns):
        data = data.rename(columns={"CAD": 'Amount'})
    else:
        return 102, pd.DataFrame()

    # create new column type on the amount sign
    data['Type'] = data['Amount'].apply(
        lambda x: 'expense' if x < 0 else 'credit')

    # Absolute value on amount
    data['Amount'] = data['Amount'].abs()

    # Add reminding clean columns. Name is based on the file name, Category is set to "", and To Ignore is set to False
    data['Name'] = 'RBC'
    data['Category'] = ''
    data['Sub Category'] = ''
    data['To Ignore'] = False

    data = data[cleanedCol]
    return 100, data


def parse_bnc_data(data):
    nbCol = data.shape[1]
    if nbCol != len(listNBCCol):
        return 101, pd.DataFrame()

    if not 'Date' in list(data.columns):
        return 102, pd.DataFrame()

    if "Debit" in list(data.columns) and "Credit" in list(data.columns):
        data['Debit'] = data['Debit'].astype(str).str.extract(r'(\d+[.]?\d*)', expand=True).astype(float)
        data['Credit'] = data['Credit'].astype(str).str.extract(r'(\d+[.]?\d*)', expand=True).astype(float)
        data['Amount'] = data['Debit'] + data['Credit']
        # create new column type
        data['Type'] = data['Debit'].apply(lambda x: 'expense' if x > 0 else 'credit')

    else:
        return 102, pd.DataFrame()

    if 'Description' in list(data.columns) and 'Categorie' in list(data.columns):
        data['Description'] = data['Description'].astype(str) + ' / '+ data['Categorie'].astype(str)
    else:
        return 102, pd.DataFrame()

    data['Account'] = 'Checking'

    # Add reminding clean columns. Name is based on the file name, Category is set to "", and To Ignore is set to False
    data['Name'] = 'NBC'
    data['Category'] = ''
    data['Sub Category'] = ''
    data['To Ignore'] = False

    data = data[cleanedCol]

    return 100, data


def parse_bnc_credit_data(data):
    nbCol = data.shape[1]
    if nbCol != len(listNBCColCredit):
        return 101, pd.DataFrame()

    if not 'Date' in list(data.columns):
        return 102, pd.DataFrame()

    if "Debit" in list(data.columns) and "Credit" in list(data.columns):
        data['Debit'] = data['Debit'].astype(str).str.extract(r'(\d+[.]?\d*)', expand=True).astype(float)
        data['Credit'] = data['Credit'].astype(str).str.extract(r'(\d+[.]?\d*)', expand=True).astype(float)
        data['Amount'] = data['Debit'] + data['Credit']
        # create new column type
        data['Type'] = data['Debit'].apply(lambda x: 'expense' if x > 0 else 'credit')

    else:
        return 102, pd.DataFrame()

    if 'Description' in list(data.columns) and 'Categorie' in list(data.columns):
        data['Description'] = data['Description'].astype(str) + ' / ' + data['Categorie'].astype(str)
    else:
        return 102, pd.DataFrame()

    data['Account'] = 'Credit Card'

    # Add reminding clean columns. Name is based on the file name, Category is set to "", and To Ignore is set to False
    data['Name'] = 'NBC'
    data['Category'] = ''
    data['Sub Category'] = ''
    data['To Ignore'] = False

    data = data[cleanedCol]

    return 100, data


def parse_scotia_data(data, type_account):
    nbCol = data.shape[1]
    if nbCol != len(listScotiaCol):
        return 101, pd.DataFrame()

    if not 'Date' in list(data.columns):
        return 102, pd.DataFrame()
    # Convert to datetime in format yyyy-mm-dd. display only the date
    # data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')

    if "Type d’opération" in list(data.columns):
        # create new column type
        data['Type'] = data['Type d’opération'].apply(lambda x: 'expense' if x == 'Débit' else 'credit')

    else:
        return 102, pd.DataFrame()

    if 'Description' in list(data.columns) and 'Sous-description' in list(data.columns):
        data['Description'] = data['Description'].astype(str) + ' / ' + data['Sous-description'].astype(str)
    else:
        return 102, pd.DataFrame()

    if "Montant" in list(data.columns):
        # create new column type
        data['Amount'] = data['Montant'].astype(float).abs()

    else:
        return 102, pd.DataFrame()

    data['Account'] = type_account

    # Add reminding clean columns. Name is based on the file name, Category is set to "", and To Ignore is set to False
    data['Name'] = 'Scotia'
    data['Category'] = ''
    data['Sub Category'] = ''
    data['To Ignore'] = False

    data = data[cleanedCol]

    return 100, data

def update_category(df, index, category):
    df.at[index, 'Category'] = category


def update_sub_category(df, index, sub_category):
    df.at[index, 'Sub Category'] = sub_category


def update_ignore(df, index, ignore):
    df.at[index, 'To Ignore'] = ignore


def display_category_form(df, categories, category_dict, s3, file_key):
    categories = [''] + list(categories)

    def create_table(row):
        index = row.name
        with st.container(border=True):
            cols = st.columns((1, 2, 2, 2, 2, 2, 2, 2))
            cols[0].write(f"{index + 1}")
            cols[1].write(row['Date'])
            cols[2].write(row['Amount'])
            cols[3].write(row['Type'])
            cols[4].write(row['Description'])
            # onchange: set category in dataframe
            category = cols[5].selectbox(
                'Category', categories, key=f'category_{index}',
                on_change=lambda: update_category(df, index, st.session_state[f'category_{index}']))
            sub_category = cols[6].selectbox(
                'Sub Category', category_dict[category] if category != "" else [], key=f'sub_category_{index}',
                on_change=lambda: update_sub_category(df, index, st.session_state[f'sub_category_{index}']))
            ignore = cols[7].checkbox('To Ignore', key=f'ignore_{index}',
                                      on_change=lambda: update_ignore(df, index, st.session_state[f'ignore_{index}'])
                                      )

            return row

    df.apply(create_table, axis=1)
    submit_button = st.button('Save transactions')
    if submit_button:
        # keep data with to ignore set to False
        df_to_keep = df[df['To Ignore'] == False]
        # check that all categories are set and subcategories are set
        # use filter to check empty string for category and subcategory
        if df_to_keep[['Category', 'Sub Category']].map(lambda x: x == '' or x is None).any().any():
            st.warning('Please categorize all transactions before saving.')
            # display the dataframe with the missing categories
            st.write(df_to_keep[df_to_keep['Category'] is None or df_to_keep['Sub Category'] is None])
        else:
            # remove columns to ignore
            df_to_keep = df_to_keep.drop(columns=['To Ignore'])
            st.write('Saving transactions...')
            append_output_data(df_to_keep, s3, BUCKET_NAME, file_key)
            st.write('Transactions saved successfully.')
            st.session_state.form_data = None
            # do like a f5 update
            st.rerun()



def stage_data(df_new_data, s3_client, bucket, object_name):
    try:
        # Check if the object exists
        s3_client.head_object(Bucket=bucket, Key=object_name)
        file_exists = True
    except ClientError:
        file_exists = False

    if file_exists:
        body_staging = read_csv_from_s3(s3_client, bucket, object_name)
        df_staging = pd.read_csv(StringIO(body_staging), index_col=False)

        # Append df_new_data to df_staging
        df_staging = pd.concat([df_staging, df_new_data], ignore_index=True)

        # remove duplicates
        df_staging = df_staging.drop_duplicates()

        # create csv buffer
        csv_buffer = df_staging.to_csv(index=False)
    else:
        csv_buffer = df_new_data.to_csv(index=False)
    try:
        # Upload the CSV to S3
        s3_client.put_object(Bucket=bucket, Key=object_name, Body=csv_buffer)
        print(f"DataFrame uploaded to {bucket}/{object_name}")
    except NoCredentialsError:
        print("Credentials not available")


def append_output_data(df_new_data, s3_client, bucket, object_name):
    try:
        # Check if the object exists
        s3_client.head_object(Bucket=bucket, Key=object_name)
        file_exists = True
    except ClientError:
        file_exists = False

    if file_exists:
        body_output = read_csv_from_s3(s3_client,bucket, object_name)
        df_output = pd.read_csv(StringIO(body_output), index_col=False)

        # Append df_new_data to df_output
        df_output = pd.concat([df_output, df_new_data], ignore_index=True)

        # remove duplicates -- Not sure i need to do this
        df_output = df_output.drop_duplicates()

        # create csv buffer
        csv_buffer = df_output.to_csv(index=False)
    else:
        csv_buffer = df_new_data.to_csv(index=False)
    try:
        # Upload the CSV to S3
        s3_client.put_object(Bucket=bucket, Key=object_name, Body=csv_buffer)
        print(f"DataFrame uploaded to {bucket}/{object_name}")
    except NoCredentialsError:
        print("Credentials not available")
