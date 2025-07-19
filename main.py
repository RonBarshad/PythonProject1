"""
main.py
Mission: This is the main entry point for the stock analysis bot application. It orchestrates the data collection, AI analysis, and database operations for stock analysis.
"""

import logging
from config.config import get
import pandas as pd
import database.models as models
import database.connection as db_connection
import ai.analysis_runner as ai_runner
from tests import inner_test
from utils.helpers import safe_mysql_insert
import ai.self_ai_analysis_by_ticker as self_ai_analysis_by_ticker
from datetime import date, timedelta
import json
import uuid
from notifications.email_sender import get_yesterdays_ticker_analyses_for_user
from datetime import datetime
from notifications.email_sender import send_email, send_html_email_with_inline_images, send_stock_analysis_email_with_charts
from users.user_manager import update_user
from graphs.candlestick_chart import generate_candlestick_chart


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

# ----------------------------- Main function -----------------------------
def test():
    """Main function to run the stock analysis bot."""
    try:
        pass



        # test_my_user()
        # update_user(
        #     user_id="426dbe30-15f3-4e0c-beff-c4418198b809",
        #     update_fields={
        #         "tickers": get("admin_tickers"),
        #         "full_name": "Ron Updated"
        #     }
        # )


        # # Test: send a test email
        # Test the new organized function
        # users = ["ron7ron7ron@gmail.com"]
        # for user in users:
        #     success = send_stock_analysis_email_with_charts(user, days=60)


        # test_my_user()

        for ticker in get("tickers")[0:6]:
            self_ai_analysis_by_ticker.self_ai_analysis_by_ticker(
                analysis_event_date=date.today() - timedelta(days=1),
                company_ticker=ticker,
                model=get("self_analysis.model"),
                analysis_type="week",
                test="yes",
                test_name="test9_week_new_prompt_gpt-4o-mini")
            print(f"Analysis for {ticker} completed")

        # for ticker in get("tickers")[0:1]:
        #     self_ai_analysis_by_ticker.self_ai_analysis_by_ticker(
        #         analysis_event_date=date.today() - timedelta(days=1),
        #         company_ticker=ticker,
        #         model=get("self_analysis.model"),
        #         weights=json.dumps(get("self_analysis.day_weights_default")),
        #         analysis_type="week",
        #         test="yes",
        #         test_name="test1_day_AAPL_2")
        #     print(f"Analysis for {ticker} completed")

        # # Get tickers from config
        # tickers = get("tickers")[:3]  # Test with first 3 tickers
        # window = get("technical_analysis.window_day")
        # logger.info(f"Starting analysis for tickers: {tickers}")
        
        # # Stage 1: Insert raw data first
        # logger.info("Stage 1: Inserting raw data...")
        # ai_runner.insert_raw_data_only(tickers)
        
        # # Stage 2: Run individual AI analyses
        # logger.info("Stage 2: Running individual AI analyses...")
        # individual_results_df = ai_runner.run_ai_analysis_for_tickers(tickers, window)
        
        # if not individual_results_df.empty:
        #     logger.info(f"Individual AI analyses completed. Results shape: {individual_results_df.shape}")
        #     # Insert individual analysis results into database using safe insertion
        #     success = safe_mysql_insert(
        #         individual_results_df, 
        #         get("database.other_tables.ai_analysis"), 
        #         get("ai_analysis.col_map")
        #     )
        #     if success:
        #         logger.info("✅ Individual analysis results inserted successfully")
        #     else:
        #         logger.error("❌ Failed to insert individual analysis results")
        # else:
        #     logger.warning("No individual AI analysis results to insert")
        
        # # Stage 3: Run consolidated analysis using the individual results
        # logger.info("Stage 3: Running consolidated analysis...")
        
        # # Run consolidated analysis that fetches from ai_analysis table and creates weighted analysis
        # consolidated_results_df = ai_runner.run_consolidated_ai_analysis(tickers, window)
        
        # if not consolidated_results_df.empty:
        #     logger.info(f"Consolidated AI analyses completed. Results shape: {consolidated_results_df.shape}")
        #     # Insert consolidated analysis results into database using safe insertion
        #     success = safe_mysql_insert(
        #         consolidated_results_df, 
        #         get("database.other_tables.ai_analysis"), 
        #         get("ai_analysis.col_map")
        #     )
        #     if success:
        #         logger.info("✅ Consolidated analysis results inserted successfully")
        #     else:
        #         logger.error("❌ Failed to insert consolidated analysis results")
        # else:
        #     logger.warning("No consolidated analysis results to insert")
        
        # logger.info("Stock analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise

# ----------------------------- Alternative main functions -----------------------------

def run_individual_analyses_only():
    """Run only the individual AI analyses (Stage 1)."""
    try:
        tickers = get("tickers")[2:4]
        window = get("technical_analysis.window_day")
        logger.info(f"Running individual AI analyses for tickers: {tickers}")
        
        # Insert raw data first
        ai_runner.insert_raw_data_only(tickers)
        
        # Run individual AI analyses
        results_df = ai_runner.run_ai_analysis_for_tickers(tickers, window)
        
        if not results_df.empty:
            logger.info(f"Individual AI analyses completed. Results shape: {results_df.shape}")
            # Insert individual analysis results into database using safe insertion
            success = safe_mysql_insert(results_df, get("database.other_tables.ai_analysis"), get("ai_analysis.col_map"))
            if success:
                logger.info("✅ Individual analysis results inserted successfully")
            else:
                logger.error("❌ Failed to insert individual analysis results")
        else:
            logger.warning("No individual AI analysis results to insert")
            
    except Exception as e:
        logger.error(f"Error in individual analyses: {e}")

def run_consolidated_analyses_only():
    """Run only the consolidated AI analyses (Stage 2)."""
    try:
        tickers = get("tickers")
        window = get("technical_analysis.window_day")
        logger.info(f"Running consolidated AI analyses for tickers: {tickers}")
        
        # Run consolidated analysis
        results_df = ai_runner.run_consolidated_ai_analysis(tickers, window)
        
        if not results_df.empty:
            logger.info(f"Consolidated AI analyses completed. Results shape: {results_df.shape}")
            # Insert consolidated analysis results into database using safe insertion
            success = safe_mysql_insert(results_df, get("database.other_tables.ai_analysis"), get("ai_analysis.col_map"))
            if success:
                logger.info("✅ Consolidated analysis results inserted successfully")
            else:
                logger.error("❌ Failed to insert consolidated analysis results")
        else:
            logger.warning("No consolidated analysis results to insert")
            
    except Exception as e:
        logger.error(f"Error in consolidated analyses: {e}")

def run_raw_data_only():
    """Run only raw data insertion without any AI analysis."""
    try:
        tickers = get("tickers")
        logger.info(f"Inserting raw data for tickers: {tickers}")
        
        ai_runner.insert_raw_data_only(tickers)
        logger.info("Raw data insertion completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in raw data insertion: {e}")

# ----------------------------- Test functions -----------------------------
def test_choose(test_number: int):
    """
    Mission: Test the schema module on a new table that does not exist in the DB.
    """
    if test_number == 1:
        inner_test.test1()
    elif test_number == 2:
        inner_test.test2()
    elif test_number == 3:
        inner_test.test3()
    elif test_number == 4:
        inner_test.test4()
    else:
        logging.error(f"Invalid test number: {test_number}")

def test_my_user():
    """
    Test inserting and updating your own user in the database.
    """
    from users.user_manager import insert_user, update_user
    import hashlib

    # Define your user info - Ron
    # full_name = "Ron Testuser"
    # email = "ron7ron7ron@gmail.com"
    # phone_number = "+972507944583"
    # password = "my_secure_password"
    # password_hash = hashlib.sha256(password.encode()).hexdigest()
    # tickers = get("admin_tickers")
    # preferences = {"theme": "dark", "notifications": True}
    
    # Ziv
    full_name = "Ziv Testuser"
    email = "ziv.shlos@gmail.com"
    phone_number = "+972544467735"
    password = "my_secure_password"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    tickers = get("admin_tickers")
    preferences = {"theme": "dark", "notifications": True}

    print("\n--- Testing Insert User ---")
    inserted = insert_user(
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        password_hash=password_hash,
        tickers=tickers,
        preferences=preferences
    )
    print(f"Insert result: {inserted}")


def main2():
    """
    Main function to run the stock analysis bot.
    """
    try:
        # TODO 1: create a prosecs which deside when to trigger the data collection  
        # TODO 2: create a prosecs which deside when to trigger the AI analysis
        # TODO 3: create a prosecs which deside when to trigger the email notification
        # TODO 4: create a prosecs which deside when to trigger the database backup
        # TODO 5: create a prosecs which deside when to trigger the database restore
        
        # 1. data collection
        data_exist = True
        if data_exist:
            run_raw_data_only()
        else: pass


        # 2. AI analysis
        for ticker in get("tickers"):
            self_ai_analysis_by_ticker.self_ai_analysis_by_ticker(
                analysis_event_date=date.today() - timedelta(days=1),
                company_ticker=ticker,
                model=get("self_analysis.model"),
                analysis_type="day",
                test="no")


        # 3. mail sending
        users = ["ron7ron7ron@gmail.com"]
        for user in users:
            success = send_stock_analysis_email_with_charts(user, days=60)
        
        
        pass
    except Exception as e:
        logger.error(f"Error in main2: {e}")


if __name__ == "__main__":
    test()
    # Uncomment the next line to test user management
    # test_my_user() 