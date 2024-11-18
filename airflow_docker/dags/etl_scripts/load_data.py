import pandas as pd
import logging

def run_query(query_statement, sql_connection):
    logging.info(f"Running Query: {query_statement}")
    query_output = pd.read_sql(query_statement, sql_connection)
    logging.info(f"Query Result:\n{query_output}")

def load_to_csv(df, csv_path):
    df.to_csv(csv_path)

def load_data(df, sql_connection, csv_path, table_name):
    logging.info(f"Loading data into table {table_name}")
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)
    load_to_csv(df,csv_path)
    query_statement = f"SELECT * FROM {table_name} WHERE GDP_USD_billions >= 100"
    run_query(query_statement, sql_connection)
    sql_connection.close()
