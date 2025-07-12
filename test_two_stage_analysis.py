"""
test_two_stage_analysis.py
Mission: Test script to verify the two-stage analysis approach works correctly.
This script tests both individual AI analyses and consolidated analysis.
"""

import logging
from config.config import get
import ai.analysis_runner as ai_runner
import database.connection as db_connection
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def test_individual_analyses():
    """Test Stage 1: Individual AI analyses."""
    try:
        tickers = get("tickers")
        window = get("technical_analysis.window_day")
        
        logger.info("=" * 60)
        logger.info("TESTING STAGE 1: INDIVIDUAL AI ANALYSES")
        logger.info("=" * 60)
        
        # Insert raw data first
        logger.info("1. Inserting raw data...")
        ai_runner.insert_raw_data_only(tickers)
        
        # Run individual AI analyses
        logger.info("2. Running individual AI analyses...")
        results_df = ai_runner.run_ai_analysis_for_tickers(tickers, window)
        
        if not results_df.empty:
            logger.info(f"✅ Individual analyses completed successfully!")
            logger.info(f"   Results shape: {results_df.shape}")
            logger.info(f"   Analysis types found: {results_df['analysis_type'].unique()}")
            logger.info(f"   Tickers processed: {results_df['company_ticker'].unique()}")
            
            # Show sample results
            logger.info("\nSample results:")
            for _, row in results_df.head(3).iterrows():
                logger.info(f"   {row['company_ticker']} - {row['analysis_type']}: Grade {row['grade']}")
            
            # Insert into database
            logger.info("3. Inserting individual analysis results into database...")
            db_connection.insert_data(results_df, get("database.other_tables.ai_analysis"))
            logger.info("✅ Individual analysis results inserted into database!")
            
            return results_df
        else:
            logger.error("❌ No individual analysis results generated!")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"❌ Error in individual analyses test: {e}")
        return pd.DataFrame()

def test_consolidated_analysis():
    """Test Stage 2: Consolidated analysis."""
    try:
        tickers = get("tickers")
        window = get("technical_analysis.window_day")
        
        logger.info("=" * 60)
        logger.info("TESTING STAGE 2: CONSOLIDATED ANALYSIS")
        logger.info("=" * 60)
        
        # Run consolidated analysis
        logger.info("1. Running consolidated analysis...")
        results_df = ai_runner.run_consolidated_ai_analysis(tickers, window)
        
        if not results_df.empty:
            logger.info(f"✅ Consolidated analysis completed successfully!")
            logger.info(f"   Results shape: {results_df.shape}")
            logger.info(f"   Tickers processed: {results_df['company_ticker'].unique()}")
            
            # Show results
            logger.info("\nConsolidated analysis results:")
            for _, row in results_df.iterrows():
                logger.info(f"   {row['company_ticker']}: Grade {row['grade']} - {row['text_analysis'][:100]}...")
            
            # Insert into database
            logger.info("2. Inserting consolidated analysis results into database...")
            db_connection.insert_data(results_df, get("database.other_tables.ai_analysis"))
            logger.info("✅ Consolidated analysis results inserted into database!")
            
            return results_df
        else:
            logger.error("❌ No consolidated analysis results generated!")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"❌ Error in consolidated analysis test: {e}")
        return pd.DataFrame()

def test_complete_workflow():
    """Test the complete two-stage workflow."""
    try:
        logger.info("=" * 60)
        logger.info("TESTING COMPLETE TWO-STAGE WORKFLOW")
        logger.info("=" * 60)
        
        # Stage 1: Individual analyses
        individual_results = test_individual_analyses()
        
        if individual_results.empty:
            logger.error("❌ Stage 1 failed - cannot proceed to Stage 2")
            return False
        
        # Stage 2: Consolidated analysis
        consolidated_results = test_consolidated_analysis()
        
        if consolidated_results.empty:
            logger.error("❌ Stage 2 failed")
            return False
        
        logger.info("=" * 60)
        logger.info("✅ COMPLETE WORKFLOW TEST PASSED!")
        logger.info("=" * 60)
        logger.info(f"Individual analyses: {len(individual_results)} records")
        logger.info(f"Consolidated analyses: {len(consolidated_results)} records")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in complete workflow test: {e}")
        return False

def main():
    """Main test function."""
    try:
        logger.info("Starting two-stage analysis tests...")
        
        # Test individual analyses only
        # test_individual_analyses()
        
        # Test consolidated analysis only
        # test_consolidated_analysis()
        
        # Test complete workflow
        success = test_complete_workflow()
        
        if success:
            logger.info("🎉 All tests passed successfully!")
        else:
            logger.error("💥 Some tests failed!")
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")

if __name__ == "__main__":
    main() 