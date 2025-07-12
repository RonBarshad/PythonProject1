# Stock Analysis Bot

A comprehensive Python application for stock analysis that combines technical analysis, analyst ratings, news sentiment, and AI-powered insights with robust data handling and production-ready features.

## 🚀 Recent Updates

### ✅ **Production-Ready Features**
- **Comprehensive NaN Handling**: Robust cleaning of all NaN-like values before database insertion
- **Safe MySQL Insertion**: Protected database operations with comprehensive error handling
- **Clean Codebase**: Removed debug messages and organized functions
- **Modular Design**: Separate functions for different analysis stages
- **Enhanced Logging**: Professional logging with success/failure indicators

### 🔧 **Technical Improvements**
- **Multi-layered NaN Cleaning**: Handles `np.nan`, `float('nan')`, string representations, and more
- **Cell-by-cell Inspection**: Final verification to ensure no problematic values remain
- **Backward Compatibility**: Maintains existing functionality while adding safety layers
- **Error Recovery**: Graceful handling of database and API failures

## Project Structure

```
PythonProject1/
├── ai/                     # AI analysis modules
│   ├── analysis_runner.py  # Main AI analysis orchestration
│   └── connector.py        # OpenAI API integration
├── config/                 # Configuration management
│   ├── config.json         # Configuration file
│   └── config.py           # Configuration loader
├── data_processing/        # Data processing modules
│   ├── analysts.py         # Analyst rating processing
│   ├── news.py            # News sentiment processing
│   └── technical.py       # Technical analysis processing
├── database/              # Database management
│   ├── connection.py      # Database connection and operations
│   ├── models.py          # Data models and utilities
│   └── schema.py          # Database schema management
├── tests/                 # Test modules
│   └── inner_test.py      # Internal testing utilities
├── utils/                 # Utility functions
│   └── helpers.py         # Helper utilities (NaN cleaning, safe insertion)
├── main.py                # Main application entry point
├── test_comprehensive_nan_cleaning.py  # Comprehensive NaN cleaning tests
├── test_nan_fix.py        # NaN handling tests
└── requirements.txt       # Python dependencies
```

## Features

### 🎯 **Two-Stage Analysis Approach**

The application uses a sophisticated two-stage analysis approach with enhanced safety features:

#### Stage 1: Individual AI Analyses
- **Purpose**: Analyze each ticker by each data source (technical, analysts, news)
- **Function**: `run_ai_analysis_for_tickers(tickers, window)`
- **Output**: DataFrame with individual analysis results for each ticker and data source
- **Database**: Results stored in `ai_analysis` table with `analysis_type` field
- **Safety**: Comprehensive NaN cleaning before database insertion

#### Stage 2: Consolidated Analysis
- **Purpose**: Analyze tickers using all analysis types together with weights
- **Function**: `run_consolidated_ai_analysis(tickers, window, model)`
- **Input**: Fetches data from `ai_analysis` table (Stage 1 results)
- **Output**: DataFrame with consolidated weighted analysis for each ticker
- **Database**: Results stored in `ai_analysis` table with `analysis_type = 'all'`
- **Safety**: Protected insertion with multi-layered NaN handling

### 📊 **Data Sources**

1. **Technical Analysis**: Stock price data with technical indicators
2. **Analyst Ratings**: Professional analyst recommendations and ratings
3. **News Sentiment**: Company news sentiment analysis

### 🤖 **AI Integration**

- OpenAI GPT models for intelligent analysis
- Configurable system messages for different analysis types
- Weighted consolidation of multiple analysis sources
- Token usage tracking and cost management
- Robust JSON response parsing with fallback handling

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your settings in `config/config.json`

## Configuration

Edit `config/config.json` to set up:

- **API Keys**: OpenAI, Alpha Vantage
- **Database**: MySQL connection details
- **Tickers**: List of stock symbols to analyze
- **Analysis Settings**: Models, system messages, weights
- **Time Windows**: Analysis periods

## Usage

### 🏃‍♂️ **Main Application**

Run the complete two-stage analysis with enhanced safety:
```bash
python main.py
```

### 🔧 **Individual Functions**

#### Run Only Individual Analyses (Stage 1)
```python
from main import run_individual_analyses_only
run_individual_analyses_only()
```

#### Run Only Consolidated Analysis (Stage 2)
```python
from main import run_consolidated_analyses_only
run_consolidated_analyses_only()
```

#### Run Only Raw Data Insertion
```python
from main import run_raw_data_only
run_raw_data_only()
```

### 🧪 **Testing**

Test the comprehensive NaN cleaning:
```bash
python test_comprehensive_nan_cleaning.py
```

Test the NaN fix functionality:
```bash
python test_nan_fix.py
```

## Database Schema

### Main Tables
- `daily_stock`: Technical stock data
- `analyst_rating`: Analyst recommendations
- `news_rating`: News sentiment data
- `ai_analysis`: AI analysis results (both individual and consolidated)

### AI Analysis Table Structure
```sql
CREATE TABLE ai_analysis (
    event_date DATETIME,
    insertion_time DATETIME,
    company_ticker VARCHAR(10),
    analysis_type VARCHAR(50),  -- 'technical_analysis', 'analysts_rating', 'news_analysis', 'all'
    wights JSON,                -- Weights used for consolidated analysis
    grade FLOAT,                -- AI analysis score (0-1)
    text_analysis TEXT,         -- AI analysis explanation
    AI_model VARCHAR(50),       -- GPT model used
    prompt_tokens INT,          -- Input tokens used
    excution_tokens INT         -- Output tokens used
);
```

## Analysis Workflow

1. **Data Collection**: Fetch raw data from APIs
2. **Stage 1 - Individual Analysis**: 
   - Analyze each ticker by each data source
   - Clean all NaN values using comprehensive cleaning
   - Store results in `ai_analysis` table using safe insertion
3. **Stage 2 - Consolidated Analysis**:
   - Fetch individual analysis results
   - Apply weighted consolidation
   - Clean all NaN values using comprehensive cleaning
   - Store final results in `ai_analysis` table using safe insertion

## Key Functions

### AI Analysis Runner (`ai/analysis_runner.py`)

- `run_ai_analysis_for_tickers()`: Stage 1 - Individual analyses
- `run_consolidated_ai_analysis()`: Stage 2 - Consolidated analysis
- `insert_raw_data_only()`: Insert raw data without AI analysis
- `_run_openai_analysis()`: Enhanced OpenAI integration with robust parsing

### Database Connection (`database/connection.py`)

- `insert_data()`: Insert DataFrames into database tables with NaN handling
- `get_data()`: Fetch data for specific tickers and tables
- `stock_data_brain()`: Process and insert stock data
- `analysts_data_brain()`: Process and insert analyst data
- `company_news_data_brain()`: Process and insert news data

### Utility Functions (`utils/helpers.py`)

- `clean_dataframe_for_mysql()`: Comprehensive NaN cleaning for all data types
- `safe_mysql_insert()`: Protected database insertion with error handling

## 🔒 **Enhanced Error Handling**

The application includes comprehensive error handling with production-ready features:

### NaN Value Handling
- **Multi-layered cleaning**: Handles all types of NaN values
- **String representations**: Cleans 'nan', 'NaN', 'NAN', 'null', 'NULL', etc.
- **Type safety**: Handles numpy NaN, Python NaN, and string representations
- **Cell-by-cell verification**: Final check to ensure no problematic values remain

### Database Safety
- **Protected insertion**: Safe MySQL insertion with comprehensive cleaning
- **Error recovery**: Graceful handling of database connection failures
- **Transaction management**: Proper rollback on errors
- **Duplicate handling**: INSERT IGNORE for duplicate prevention

### API Integration
- **Rate limiting**: Handles API rate limits gracefully
- **Response parsing**: Robust JSON parsing with fallback handling
- **Token tracking**: Monitors OpenAI token usage
- **Error logging**: Detailed error reporting for debugging

## 📝 **Enhanced Logging**

All operations are logged with professional formatting:
- **INFO**: Normal operations with clear success indicators
- **WARNING**: Non-critical issues with actionable information
- **ERROR**: Critical failures with detailed error context
- **Success Indicators**: ✅/❌ symbols for quick status identification

## 🧪 **Testing & Validation**

### Comprehensive Testing
- **NaN Cleaning Tests**: Verify all NaN types are properly handled
- **Database Insertion Tests**: Validate safe insertion functionality
- **Integration Tests**: End-to-end workflow validation
- **Error Handling Tests**: Verify graceful failure handling

### Test Scripts
- `test_comprehensive_nan_cleaning.py`: Comprehensive NaN handling validation
- `test_nan_fix.py`: Specific NaN fix functionality testing
- `test_two_stage_analysis.py`: Two-stage analysis workflow testing

## 🚀 **Production Features**

### Code Quality
- **Clean Architecture**: Modular design with clear separation of concerns
- **Type Safety**: Proper type hints and validation
- **Documentation**: Comprehensive docstrings and comments
- **Error Recovery**: Graceful handling of all failure scenarios

### Performance
- **Efficient Data Processing**: Optimized DataFrame operations
- **Memory Management**: Proper cleanup and resource management
- **Batch Operations**: Efficient database batch insertions
- **Caching**: Intelligent data caching where appropriate

### Monitoring
- **Token Usage Tracking**: Monitor OpenAI API costs
- **Performance Metrics**: Track analysis completion times
- **Error Monitoring**: Comprehensive error tracking and reporting
- **Success Rates**: Monitor analysis success rates

## Contributing

1. Follow the existing code structure and patterns
2. Add appropriate logging with success/failure indicators
3. Include comprehensive error handling
4. Test NaN handling for any new data processing
5. Update documentation for new features
6. Run comprehensive tests before submitting

## License

This project is for educational and research purposes.

---

## 🎯 **Quick Start**

1. **Setup**: Install dependencies and configure API keys
2. **Test**: Run `python test_comprehensive_nan_cleaning.py` to verify setup
3. **Run**: Execute `python main.py` for complete analysis
4. **Monitor**: Check logs for success indicators and any issues

The application is now **production-ready** with robust error handling, comprehensive data cleaning, and professional logging! 🚀 

## 🏗️ **Code Architecture & Function Relationships**

### **Main Application Flow**

```
main.py
├── main()                          # 🎯 Entry point
│   ├── ai_runner.insert_raw_data_only()     # 📊 Stage 1: Raw data insertion
│   ├── ai_runner.run_ai_analysis_for_tickers()  # 🤖 Stage 2: Individual AI analyses
│   │   ├── db_connection.get_data()         # 📥 Fetch data from DB
│   │   ├── _run_openai_analysis()           # 🧠 Run OpenAI analysis
│   │   └── safe_mysql_insert()              # 🔒 Safe DB insertion
│   └── ai_runner.run_consolidated_ai_analysis()  # 🎯 Stage 3: Consolidated analysis
│       ├── _fetch_ai_analysis_data()        # 📥 Fetch AI analysis data
│       ├── _run_openai_analysis()           # 🧠 Run consolidated OpenAI analysis
│       └── safe_mysql_insert()              # 🔒 Safe DB insertion
```

### **Module Dependencies & Data Flow**

```
📁 ai/analysis_runner.py
├── run_ai_analysis_for_tickers()
│   ├── db_connection.get_data() → 📁 database/connection.py
│   ├── _run_openai_analysis() → 🤖 OpenAI API
│   └── safe_mysql_insert() → 📁 utils/helpers.py
│
├── run_consolidated_ai_analysis()
│   ├── _fetch_ai_analysis_data() → 📁 database/connection.py
│   ├── _create_consolidated_system_message() → 📁 config/config.py
│   ├── _run_openai_analysis() → 🤖 OpenAI API
│   └── safe_mysql_insert() → 📁 utils/helpers.py
│
└── insert_raw_data_only()
    ├── stock_data_brain() → 📁 data_processing/technical.py
    ├── analysts_data_brain() → 📁 data_processing/analysts.py
    └── company_news_data_brain() → 📁 data_processing/news.py
```

### **Database Operations Flow**

```
📁 database/connection.py
├── insert_data()
│   ├── clean_dataframe_for_mysql() → 📁 utils/helpers.py
│   ├── MySQL INSERT IGNORE
│   └── Error handling & rollback
│
├── get_data()
│   ├── MySQL SELECT query
│   └── DataFrame creation
│
├── stock_data_brain()
│   ├── stocks_technical_analysis.get_stock_data() → 📁 data_processing/technical.py
│   └── insert_data()
│
├── analysts_data_brain()
│   ├── analysts_rating.avg_analyst_rating() → 📁 data_processing/analysts.py
│   └── insert_data()
│
└── company_news_data_brain()
    ├── company_news.av_get_json() → 📁 data_processing/news.py
    ├── company_news.news_to_df_single()
    ├── company_news.merge_dfs_no_dupes()
    └── insert_data()
```

### **Data Processing Pipeline**

```
📁 data_processing/
├── technical.py
│   ├── get_stock_data() → 📊 Alpha Vantage API
│   ├── Technical indicators calculation
│   └── DataFrame formatting
│
├── analysts.py
│   ├── avg_analyst_rating() → 📊 Alpha Vantage API
│   ├── Analyst rating aggregation
│   └── DataFrame formatting
│
└── news.py
    ├── av_get_json() → 📊 Alpha Vantage API
    ├── news_to_df_single() → 📰 News processing
    ├── merge_dfs_no_dupes() → 🔄 Data deduplication
    └── DataFrame formatting
```

### **AI Analysis Pipeline**

```
🤖 OpenAI Integration
├── _run_openai_analysis()
│   ├── OpenAI API call
│   ├── JSON response parsing
│   ├── parse_text_analysis_column() → 🔍 Response parsing
│   └── Score & explanation extraction
│
├── Individual Analysis
│   ├── Technical analysis → System message + Stock data
│   ├── Analyst analysis → System message + Analyst data
│   └── News analysis → System message + News data
│
└── Consolidated Analysis
    ├── Fetch individual results from DB
    ├── Weighted consolidation
    └── Final AI analysis with weights
```

### **Safety & Error Handling Flow**

```
🔒 Safety Layer
├── safe_mysql_insert()
│   ├── clean_dataframe_for_mysql() → 🧹 NaN cleaning
│   ├── Database insertion attempt
│   ├── Error handling
│   └── Success/failure reporting
│
├── clean_dataframe_for_mysql()
│   ├── Multi-layered NaN replacement
│   ├── Cell-by-cell verification
│   ├── Type safety checks
│   └── Comprehensive logging
│
└── Error Recovery
    ├── Database connection failures → Retry logic
    ├── API rate limiting → Graceful handling
    ├── Data validation → Fallback strategies
    └── AI analysis failures → Error logging
```

### **Configuration & Utilities**

```
📁 config/
├── config.py
│   ├── get() → 📄 JSON config loading
│   ├── Database credentials
│   ├── API keys
│   └── Analysis parameters
│
📁 utils/
└── helpers.py
    ├── clean_dataframe_for_mysql() → 🧹 Data cleaning
    └── safe_mysql_insert() → 🔒 Safe insertion
```

### **Function Call Hierarchy**

```
main() [main.py]
├── insert_raw_data_only() [ai/analysis_runner.py]
│   ├── stock_data_brain() [database/connection.py]
│   │   └── get_stock_data() [data_processing/technical.py]
│   ├── analysts_data_brain() [database/connection.py]
│   │   └── avg_analyst_rating() [data_processing/analysts.py]
│   └── company_news_data_brain() [database/connection.py]
│       └── av_get_json() [data_processing/news.py]
│
├── run_ai_analysis_for_tickers() [ai/analysis_runner.py]
│   ├── get_data() [database/connection.py]
│   ├── _run_openai_analysis() [ai/analysis_runner.py]
│   └── safe_mysql_insert() [utils/helpers.py]
│       └── clean_dataframe_for_mysql() [utils/helpers.py]
│
└── run_consolidated_ai_analysis() [ai/analysis_runner.py]
    ├── _fetch_ai_analysis_data() [ai/analysis_runner.py]
    ├── _run_openai_analysis() [ai/analysis_runner.py]
    └── safe_mysql_insert() [utils/helpers.py]
        └── clean_dataframe_for_mysql() [utils/helpers.py]
```

### **Data Transformation Flow**

```
Raw Data Sources
├── Alpha Vantage API → Technical Data
├── Alpha Vantage API → Analyst Data
└── Alpha Vantage API → News Data
    ↓
Data Processing Modules
├── technical.py → Technical indicators
├── analysts.py → Rating aggregation
└── news.py → Sentiment analysis
    ↓
Database Storage
├── daily_stock table
├── analyst_rating table
└── news_rating table
    ↓
AI Analysis
├── Individual analysis → ai_analysis table
└── Consolidated analysis → ai_analysis table
    ↓
Final Results
└── Weighted stock recommendations
```

This architecture ensures:
- **🔒 Safety**: Multi-layered error handling and data validation
- **📊 Efficiency**: Optimized data flow and processing
- **🧪 Testability**: Modular design for easy testing
- **📈 Scalability**: Clear separation of concerns
- **🛡️ Reliability**: Comprehensive error recovery mechanisms 