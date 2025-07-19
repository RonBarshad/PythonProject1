# Graphs Package

## Overview

The `graphs` package provides functions to generate various types of charts and graphs for stock data visualization. This package is designed to create professional-looking charts that can be easily integrated into emails or reports.

## Features

- **Candlestick Charts**: Professional candlestick charts for stock price data with OHLCV visualization
- **High-Quality Output**: Charts saved as high-resolution PNG images (300 DPI)
- **Database Integration**: Direct integration with existing database connection
- **Configurable**: Easy to customize chart appearance and data periods (1-365 days)
- **Error Handling**: Comprehensive error handling and logging
- **Email Integration**: Designed for seamless integration with email notifications
- **Professional Styling**: Clean, readable design suitable for business communications

## Installation

Make sure you have the required dependencies installed:

```bash
pip install matplotlib pandas
```

## Usage

### Candlestick Chart

Generate a candlestick chart for a stock ticker:

```python
from graphs.candlestick_chart import generate_candlestick_chart

# Generate a 60-day candlestick chart for AAPL
image_data = generate_candlestick_chart('AAPL', 60)

if image_data:
    print(f"Chart generated successfully ({len(image_data)} bytes)")
    # Use image_data directly in email or save to file if needed
    with open('chart.png', 'wb') as f:
        f.write(image_data)
else:
    print("Failed to generate chart")
```

### Function Parameters

- `ticker` (str): Stock ticker symbol (e.g., 'AAPL', 'MSFT')
- `days` (int, optional): Number of days of data to include (default: 60, max: 365)

### Output

- **Return Value**: Image data as bytes or None if failed
- **File Format**: PNG image (300 DPI) - generated in memory
- **No Disk Storage**: Images are not saved to disk, only generated in memory
- **Chart Title**: `{TICKER} Daily`

## Chart Features

### Candlestick Chart
- **Green candles**: Price closed higher than opened (bullish)
- **Red candles**: Price closed lower than opened (bearish)
- **Wicks**: Show high and low prices for each day
- **Body thickness**: Represents the difference between open and close prices
- **Professional styling**: Clean, readable design suitable for emails
- **Date formatting**: X-axis shows dates in MM/DD format with weekly intervals
- **Grid lines**: Subtle grid for better readability
- **Background**: Light gray background for better contrast
- **Title**: Clear ticker name with "Daily" suffix
- **Axis labels**: Bold, professional labeling

## Database Requirements

The charts require the following data columns in your stock data table:
- `event_date`: Date of the data point
- `open_price`: Opening price
- `high_price`: Highest price of the day
- `low_price`: Lowest price of the day
- `close_price`: Closing price
- `volume`: Trading volume

## Configuration

The package uses the existing configuration from `config/config.json`:
- Database connection settings
- Table names for stock data

## Error Handling

The functions include comprehensive error handling:
- **Input validation**: Ticker format and days range (1-365)
- **Database connection errors**: Graceful handling of connection failures
- **Missing data handling**: Proper handling when no data is found
- **Column validation**: Ensures all required OHLCV columns are present
- **Memory management**: Efficient handling of image data in memory
- **Detailed logging**: Professional logging with success/failure indicators
- **Exception recovery**: Graceful error recovery with meaningful messages

## Testing

Run the test script to verify functionality:

```bash
cd graphs
python test_candlestick.py
```

## Integration with Email System

The candlestick charts are designed to work seamlessly with the email notification system:

```python
from graphs.candlestick_chart import generate_candlestick_chart
from notifications.email_sender import send_stock_analysis_email_with_charts

# Generate charts and send email with inline images (no files saved)
success = send_stock_analysis_email_with_charts("user@example.com", days=60)
```

### Email Integration Features:
- **Inline images**: Charts are embedded directly in email body
- **Memory-based generation**: No files saved to disk, charts generated in memory
- **Professional formatting**: Clean HTML layout with CSS styling
- **Analysis integration**: Combines charts with AI analysis text
- **Automatic generation**: Charts are created on-demand for each email

## Future Enhancements

Planned features for future versions:
- Volume charts
- Technical indicators (RSI, MACD, etc.)
- Multiple timeframes
- Custom color schemes
- Interactive charts
- Export to different formats

## Dependencies

- `matplotlib`: Chart generation
- `pandas`: Data manipulation
- `database.connection`: Database access
- `config.config`: Configuration management 