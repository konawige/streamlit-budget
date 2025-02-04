# Expense Tracker Dashboard

This project is an Expense Tracker Dashboard built using Streamlit, Plotly, and AWS S3. It allows users to upload transaction files, process them, and visualize the data through various charts and tables.

## Features

- Upload transaction files from different banks (RBC, NBC, Scotia)
- Process and stage transaction data
- Visualize consolidated transactions
- Display monthly expenses and credits
- Show expense distribution by category and sub-category

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/konawige/streamlit-budget.git
    cd streamlit-budget
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the root directory and add your AWS credentials and environment variables:
    ```env
    AWS_ACCESS_KEY_ID=your_access_key_id
    AWS_SECRET_ACCESS_KEY=your_secret_access_key
    PRODUCTION_ENV=1  # Set to 1 for production, 0 for local
    ```

## Usage

1. Run the Streamlit application:
    ```sh
    streamlit run app.py
    ```

2. Open your web browser and go to `http://localhost:8501` to access the dashboard.

## Project Structure

- `app.py`: Main application file for the dashboard.
- `pages/form.py`: Handles the form for uploading and processing new transactions.
- `utils.py`: Utility functions for reading data from S3, processing transactions, and more.
- `requirements.txt`: List of required Python packages.
- `.env`: Environment variables for AWS credentials and configuration.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes or improvements.