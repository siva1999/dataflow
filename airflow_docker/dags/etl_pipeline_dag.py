import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from etl_scripts.extract_data import extract_data
from etl_scripts.transform_data import transform_data
from etl_scripts.load_data import load_data
import sqlite3
import logging
import pandas as pd


# Default DAG arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'etl_pipeline',
    default_args=default_args,
    description='ETL pipeline for data flow automation',
    schedule_interval=timedelta(hours=1),  # Run every hour
    start_date=datetime(2023, 11, 16),
    catchup=False,
) as dag:
        # Tasks

        # Task 1: Extract
    def extract(**kwargs):
        url = 'https://web.archive.org/web/20230902185326/https://en.wikipedia.org/wiki/List_of_countries_by_GDP_%28nominal%29'
        table_attribs = ["Country", "GDP_USD_millions"]
        logging.info("Starting data extraction !!")
        df = extract_data(url, table_attribs)
        # Push DataFrame to XCom
        kwargs['ti'].xcom_push(key='raw_data', value=df.to_dict())

    extract_task = PythonOperator(
        task_id='extract_task',
        python_callable=extract,
    )

    # Task 2: Transform
    def transform(**kwargs):
        # Pull DataFrame from XCom
        ti = kwargs['ti']
        raw_data = ti.xcom_pull(task_ids='extract_task', key='raw_data')
        df = pd.DataFrame(raw_data)
        logging.info("Starting data transformation !!")
        transformed_df = transform_data(df)
        # Push transformed DataFrame to XCom
        ti.xcom_push(key='transformed_data', value=transformed_df.to_dict())

    transform_task = PythonOperator(
        task_id='transform_task',
        python_callable=transform
    )

    # Task 3: Load
    def load(**kwargs):
        # Pull transformed DataFrame from XCom
        ti = kwargs['ti']
        transformed_data = ti.xcom_pull(task_ids='transform_task', key='transformed_data')
        df = pd.DataFrame(transformed_data)
        db_name = 'World_Economies.db'
        csv_path = 'Countries_by_GDP.csv'
        sql_connection = sqlite3.connect(db_name)
        logging.info("Starting to load data !!")
        load_data(df, sql_connection, csv_path, table_name='Countries_by_GDP')

    load_task = PythonOperator(
        task_id='load_task',
        python_callable=load
    )

    # Set task dependencies
    extract_task >> transform_task >> load_task
