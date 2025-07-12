import logging
import pandas as pd
from config.config import get
import database.connection as db_connection
import database.schema as db_schema
import ai.analysis_runner as ai_runner

def test1():
    """
    === TEST: Fetch and print data for each ticker and table ===
    """
    try:
        for ticker in get("tickers"):
            table = get("database.table.daily_stock")
            window = get("technical_analysis.window_day")
            data1 = db_connection.get_data(ticker, table, window)
            print(data1)
            logging.info(f"Fetched data: {data1}")

            table = get("database.table.analyst_rating")
            data2 = db_connection.get_data(ticker, table, window)
            print(data2)
            logging.info(f"Fetched data: {data2}")

            table = get("database.table.news_rating")
            data3 = db_connection.get_data(ticker, table, window)
            print(data3)
            logging.info(f"Fetched data: {data3}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def test2():
    """
    === TEST: API connection & data insertion ===
    """
    try:
        db_connection.stock_data_brain(get("tickers"))
        logging.info("Stock data inserted successfully.")
        db_connection.analysts_data_brain(get("tickers"))
        logging.info("Analyst ratings inserted successfully.")
        db_connection.company_news_data_brain(get("tickers"))
        logging.info("Company news inserted successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def test3():
    """
    Test the db_schema module on a new table that does not exist in the DB.
    """
    import random
    table_name = f"test_table_demo_{random.randint(1000,9999)}"
    logging.info(f"Testing db_schema on table: {table_name}")

    # 1. Create a DataFrame to define the schema
    df = pd.DataFrame({
        'id': pd.Series(dtype='int64'),
        'name': pd.Series(dtype='object'),
        'created_at': pd.Series(dtype='datetime64[ns]')
    })

    # 2. Create the table
    db_schema.create_table_from_df(table_name, df)
    logging.info(f"Created table {table_name}.")

    # 3. Add a column
    db_schema.add_column(table_name, 'status', 'VARCHAR(50)')
    logging.info(f"Added column 'status' to {table_name}.")

    # 4. Rename the column
    db_schema.rename_column(table_name, 'status', 'state', 'VARCHAR(50)')
    logging.info(f"Renamed column 'status' to 'state' in {table_name}.")

    # 5. Create an index
    db_schema.create_index(table_name, f"idx_{table_name}_name", ['name'])
    logging.info(f"Created index on 'name' in {table_name}.")

    # 6. Remove the column
    db_schema.remove_column(table_name, 'state')
    logging.info(f"Removed column 'state' from {table_name}.")

    logging.info(f"db_schema test completed for table: {table_name}")

def test4():
    # Test: Run AI analysis for all tickers in config and print the results
    tickers = get("tickers")[:1]
    window = get("technical_analysis.window_day")
    ai_df = ai_runner.run_ai_analysis_for_tickers(tickers, window)
    
    print("AI analysis DataFrame:")
    print(ai_df)
    # Insert the results into the ai_analysis table
    col_map = get("ai_analysis.col_map")
    table_name = get("database.other_tables.ai_analysis")
    db_connection.insert_data(ai_df, table_name, col_map)
    logging.info(f"Inserted {len(ai_df)} rows into {table_name}.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
    test1()
    test2()
    test3() 
    test4()