# Self AI Analysis by Ticker

## Overview

The `self_ai_analysis_by_ticker.py` module provides functionality to analyze stock tickers in isolation using GPT API. It retrieves configuration data, runs AI analysis, processes the output, and stores results in the `self_ai_analysis_ticker` database table.

## Features

- **Isolated Analysis**: Analyze individual stock tickers without external dependencies
- **Configurable Weights**: Support for custom analysis weights via JSON strings
- **Multiple Analysis Types**: Support for 'day' and 'week' analysis types
- **Database Integration**: Automatic storage of results in MySQL database
- **Error Handling**: Comprehensive error handling and validation
- **Test Mode**: Support for test runs with test indicator

## Database Schema

The module stores results in the `self_ai_analysis_ticker` table with the following structure:

```sql
CREATE TABLE IF NOT EXISTS self_ai_analysis_ticker (
    insertion_time  timestamp NOT NULL,
    analysis_event_date  date NOT NULL,
    company_ticker   VARCHAR(10) NOT NULL,
    analysis_type VARCHAR(10),
    text_analysis TEXT,
    grade FLOAT,
    model VARCHAR(20),
    weights VARCHAR(400),
    prompt_tokens INT,
    execution_tokens INT,
    test_ind TINYINT UNSIGNED NOT NULL DEFAULT 0,
    test_name VARCHAR(10),
    PRIMARY KEY (insertion_time, analysis_event_date, company_ticker, analysis_type, test_ind, test_name)
);
```

## Configuration

The module uses the following configuration from `config/config.json`:

### Self Analysis Configuration
```json
{
  "self_analysis": {
    "model": "gpt-3.5-turbo",
    "day_weights_default": {
        "technical_analysis": 0.35,
        "company_news":       0.25,
        "world_news":         0.10,
        "industry_changes":   0.10,
        "competitors":        0.08,
        "legal":              0.06,
        "financial":          0.06
    },
    "week_weights_default": {
      "technical_analysis": 0.35,
      "company_news":       0.25,
      "world_news":         0.10,
      "industry_changes":   0.10,
      "competitors":        0.08,
      "legal":              0.06,
      "financial":          0.06
    },
    "daily_analysis_system_message": "...",
    "weekly_analysis_system_message": "..."
  }
}
```

## Main Function

### `self_ai_analysis_by_ticker()`

The main function that performs the complete analysis process.

#### Parameters

- `analysis_event_date` (date): Date for which analysis is performed
- `company_ticker` (str): Stock ticker symbol (e.g., "AAPL")
- `model` (str): GPT model to use (e.g., "gpt-3.5-turbo")
- `weights` (str): JSON string of weights for analysis components (optional, uses defaults if not provided)
- `analysis_type` (str): Type of analysis ('day' or 'week'), default 'day'
- `test` (str): Test indicator ('yes' or 'no'), default 'no'
- `test_name` (str, optional): Name for the test run (e.g., "example1", "validation_test")

#### Returns

Dictionary containing analysis results and status:
```python
{
    'success': bool,
    'company_ticker': str,
    'analysis_type': str,
    'text_analysis': str,
    'grade': float,
    'model': str,
    'weights': str,
    'prompt_tokens': int,
    'execution_tokens': int,
    'test_ind': int,
    'test_name': str,
    'analysis_event_date': str
}
```

#### Example Usage

```python
from datetime import date
from ai.self_ai_analysis_by_ticker import self_ai_analysis_by_ticker

# Run analysis with custom weights
result = self_ai_analysis_by_ticker(
    analysis_event_date=date(2024, 1, 15),
    company_ticker="AAPL",
    model="gpt-3.5-turbo",
    weights='{"technical_analysis": 0.5, "news_analysis": 0.3, "analysts_rating": 0.2}',
    analysis_type="day",
    test="no",
    test_name="custom_weights_test"
)

# Run analysis with default weights
result2 = self_ai_analysis_by_ticker(
    analysis_event_date=date(2024, 1, 15),
    company_ticker="MSFT",
    model="gpt-3.5-turbo",
    weights="",  # Uses default weights from config
    analysis_type="week",
    test="no",
    test_name="default_weights_test"
)

if result['success']:
    print(f"Grade: {result['grade']}")
    print(f"Analysis: {result['text_analysis']}")
    print(f"Weights Used: {result['weights']}")
else:
    print(f"Error: {result.get('error')}")
```

## Helper Functions

### `extract_system_message_and_model(analysis_type)`

Extracts system message and model from configuration based on analysis type.

### `get_weights_for_analysis(analysis_type)`

Retrieves default weights for the specified analysis type from configuration.

**Default Weights:**
- **Day Analysis**: `day_weights_default` from config
- **Week Analysis**: `week_weights_default` from config

If no weights are provided to the main function, these defaults are automatically used.

### `run_gpt_analysis(system_message, user_message, model)`

Runs GPT analysis using OpenAI API.

### `parse_gpt_output(content)`

Parses GPT output to extract text analysis and grade.

### `insert_analysis_to_database(...)`

Inserts analysis results into the database table.

## Output Processing

The module handles two types of GPT output:

1. **JSON Format**: Legacy format with 'score' and 'explanation' fields (0-1 scale)
2. **Text Format**: New structured format with grade at the end (1-10 scale)

### New System Message Output Format

The new system messages produce structured analysis in this format:
```
[Technical Analysis (≤4 sentences)] [Company-specific News (≤4)] [World News affecting the company/sector (≤4)] [Industry Changes (≤4)] [Competitors, high-level (≤4)] [Legal / Regulatory (≤4)] [Financial (≤4)] [GRADE]
```

**Example Output:**
```
Technical analysis shows strong bullish momentum with price above key moving averages and RSI in neutral territory. Company-specific news reveals positive earnings guidance and new product launches. World news indicates favorable trade policies affecting the sector. Industry changes show increased competition but also market expansion opportunities. Competitors are facing regulatory challenges while maintaining market share. Legal and regulatory environment remains stable with no significant changes. Financial metrics indicate strong cash flow and improving debt ratios. 8.5
```

### Output Parsing Logic

1. First attempts to parse as JSON (for backward compatibility)
2. If JSON parsing fails, looks for numeric grade at the very end of the entire text
3. Validates grade is in the correct range (1.0-10.0)
4. Extracts text analysis by removing the grade from the end
5. Returns grade in original 1.0-10.0 scale

**Valid Grade Examples**: 10.0, 1.0, 3.3, 4.7, 5.0, 9.9
**Invalid Grade Examples**: 10.1 (too high), 0.9 (too low), 5.22 (too many decimal places)

## Error Handling

The module includes comprehensive error handling for:

- Invalid analysis types
- Missing configuration data
- Invalid JSON weights
- Database connection errors
- GPT API errors
- Empty or invalid inputs

## Testing

Use the provided test script `test_self_ai_analysis.py` to verify functionality:

```bash
python test_self_ai_analysis.py
```

The test script includes:
- Basic functionality testing
- Week analysis testing
- Error handling validation
- Input validation testing

## Database Integration

### Connection

Uses the same database credentials as other modules:
- Host: `config.database.host`
- User: `config.database.user`
- Password: `config.database.password`
- Database: `config.database.name`

### Insertion Strategy

- Uses `INSERT ... ON DUPLICATE KEY UPDATE` for handling duplicates
- Updates existing records if primary key already exists
- Handles all data types appropriately for MySQL

## Dependencies

- `openai`: For GPT API integration
- `mysql.connector`: For database operations
- `config.config`: For configuration management
- Standard library: `json`, `logging`, `re`, `datetime`, `typing`

## Best Practices

1. **Always use test mode first**: Set `test="yes"` for initial testing
2. **Validate weights**: Ensure weights JSON is valid before running
3. **Handle errors**: Always check the `success` field in results
4. **Monitor tokens**: Track token usage for cost management
5. **Use appropriate dates**: Set `analysis_event_date` to the correct analysis date

## Troubleshooting

### Common Issues

1. **Configuration not found**: Check `config.json` has required `self_analysis` section
2. **Database connection failed**: Verify database credentials and connectivity
3. **Invalid weights JSON**: Ensure weights string is valid JSON format
4. **GPT API errors**: Check API key and model availability

### Debug Mode

Enable detailed logging by setting log level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- GPT API calls have rate limits and costs
- Database operations are optimized with batch inserts
- Token usage is tracked for cost monitoring
- Error handling prevents unnecessary API calls

## Security

- API keys are stored in configuration file
- Database credentials are retrieved securely
- Input validation prevents injection attacks
- Error messages don't expose sensitive information 