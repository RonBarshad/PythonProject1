"""
notifications/email_sender.py
Mission: Send email messages to users. This module connects to an SMTP server and can send emails to users by their email address.

Requirements:
- Set your SMTP server, port, sender email, and password in environment variables or config.
- The recipient email must be a valid email address.

Usage:
    python notifications/email_sender.py
"""

import smtplib
import re
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import mysql.connector
from datetime import datetime, timedelta
from config.config import get
import json
from typing import List, Optional
import base64


# SMTP configuration (set these as environment variables or replace with your values)
SMTP_SERVER = get("smtp_server")
SMTP_PORT = get("smtp_port")
SMTP_USER = get("smtp_user")
SMTP_PASSWORD = get("smtp_password")
SENDER_EMAIL = SMTP_USER


def send_email(recipient_email: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> bool:
    """
    Send an email to a user with optional file attachments.
    Args:
        recipient_email (str): The recipient's email address.
        subject (str): The email subject.
        body (str): The email body (plain text).
        attachments (list): List of file paths to attach (optional).
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(body)
    
    # Add attachments if provided
    if attachments:
        for file_path in attachments:
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                    file_name = file_path.split("/")[-1]  # Get just the filename
                    msg.add_attachment(file_data, maintype='image', subtype='png', filename=file_name)
                print(f"Attached file: {file_path}")
            except Exception as e:
                print(f"Failed to attach file {file_path}: {e}")
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_html_email_with_inline_images(recipient_email: str, subject: str, html_body: str, image_paths: Optional[List[str]] = None) -> bool:
    """
    Send an HTML email with inline images embedded in the body.
    
    Args:
        recipient_email (str): The recipient's email address.
        subject (str): The email subject.
        html_body (str): The HTML email body (can include <img> tags).
        image_paths (list): List of image file paths to embed inline.
        
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    try:
        # Create the root message
        msg = MIMEMultipart('related')
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = subject
        
        # Create the HTML part
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Add inline images if provided
        if image_paths:
            for i, image_path in enumerate(image_paths):
                try:
                    with open(image_path, "rb") as f:
                        img_data = f.read()
                    
                    # Create image part
                    img = MIMEImage(img_data)
                    img.add_header('Content-ID', f'<image_{i}>')
                    img.add_header('Content-Disposition', 'inline', filename=image_path.split("/")[-1])
                    msg.attach(img)
                    
                    print(f"Embedded image: {image_path}")
                except Exception as e:
                    print(f"Failed to embed image {image_path}: {e}")
        
        # Send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            
        print(f"HTML email sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send HTML email: {e}")
        return False


def send_stock_analysis_email_with_charts(recipient_email: str, tickers: list = None, days: int = 60) -> bool:
    """
    Send a professional HTML email with stock analysis and inline candlestick charts.
    
    This function:
    1. Gets analysis data for each ticker
    2. Generates candlestick charts for each ticker (in memory, no files saved)
    3. Creates a professional HTML email with inline images and analysis text
    4. Sends the email with embedded charts
    
    Args:
        recipient_email (str): The recipient's email address
        tickers (list): List of ticker symbols to analyze (if None, uses user's tickers from DB)
        days (int): Number of days for the charts (default: 60)
        
    Returns:
        bool: True if email sent successfully, False otherwise
        
    Example:
        >>> send_stock_analysis_email_with_charts("user@example.com", ["AAPL", "MSFT"])
        >>> send_stock_analysis_email_with_charts("user@example.com")  # Uses user's tickers from DB
    """
    try:
        from graphs.candlestick_chart import generate_candlestick_chart
        
        # Get analysis data and tickers
        if tickers is None:
            # Get user's tickers and analysis from database
            analyses = get_yesterdays_ticker_analyses_for_user(recipient_email)
            if not analyses:
                print(f"No analysis data found for {recipient_email}")
                return False
        else:
            # For specific tickers, we'll create placeholder analysis
            analyses = [(ticker, f"Analysis for {ticker} - {days} day candlestick chart", "N/A") for ticker in tickers]
        
        if not analyses:
            print(f"No analysis data found for {recipient_email}")
            return False
        
        # Extract tickers from analyses
        tickers = [analysis[0] for analysis in analyses]
        print(f"send_stock_analysis_email_with_charts: Tickers: {tickers}")
        
        # Email setup
        subject = f"Stock Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Create HTML body with analysis data
        html_body = _create_stock_analysis_html_body_with_analysis(analyses, days)
        
        # Generate charts and collect image data
        image_data_list = []
        for ticker in tickers:
            image_data = generate_candlestick_chart(ticker, days)
            if image_data:
                image_data_list.append(image_data)
                print(f"Generated chart for {ticker}")
            else:
                print(f"Failed to generate chart for {ticker}")
        
        # Send the email with image data
        success = send_html_email_with_inline_image_data(recipient_email, subject, html_body, image_data_list)
        
        if success:
            print(f"✅ Stock analysis email sent successfully to {recipient_email}")
            return True
        else:
            print(f"❌ Failed to send stock analysis email to {recipient_email}")
            return False
            
    except Exception as e:
        print(f"Error sending stock analysis email: {e}")
        return False


def send_html_email_with_inline_image_data(recipient_email: str, subject: str, html_body: str, image_data_list: Optional[List[bytes]] = None) -> bool:
    """
    Send an HTML email with inline images using image data (no files saved to disk).
    
    Args:
        recipient_email (str): The recipient's email address.
        subject (str): The email subject.
        html_body (str): The HTML email body (can include <img> tags).
        image_data_list (list): List of image data as bytes to embed inline.
        
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    try:
        # Create the root message
        msg = MIMEMultipart('related')
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = subject
        
        # Create the HTML part
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Add inline images if provided
        if image_data_list:
            for i, image_data in enumerate(image_data_list):
                try:
                    # Create image part directly from bytes
                    img = MIMEImage(image_data)
                    img.add_header('Content-ID', f'<image_{i}>')
                    img.add_header('Content-Disposition', 'inline', filename=f'chart_{i}.png')
                    msg.attach(img)
                    
                    print(f"Embedded image {i+1} from memory")
                except Exception as e:
                    print(f"Failed to embed image {i+1}: {e}")
        
        # Send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            
        print(f"HTML email sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send HTML email: {e}")
        return False


def _format_analysis_text_for_display(raw_analysis_text: str) -> str:
    """
    Format raw analysis text from database into user-friendly HTML display format.
    
    This function transforms raw GPT output with bracketed fields into a clean,
    readable HTML format with proper titles and sections.
    
    Args:
        raw_analysis_text (str): Raw analysis text from database (may contain <TA>, <CN>, etc.)
        
    Returns:
        str: Formatted HTML analysis text ready for display
    """
    if not raw_analysis_text or raw_analysis_text.strip() == "":
        return "<p>No analysis content available.</p>"
    
    # Define the field mappings
    field_mappings = {
        'TA': 'Technical Analysis',
        'CN': 'Company News',
        'WN': 'World News',
        'IC': 'Industry Changes',
        'COMP': 'Competitors',
        'LEGAL': 'Legal',
        'FIN': 'Financial'
    }
    
    # Initialize the formatted sections
    formatted_sections = []
    
    # Extract content from each bracketed field
    for field_code, field_title in field_mappings.items():
        # Pattern to match the field content: <FIELD_CODE>content</FIELD_CODE> or <FIELD_CODE>content
        pattern = rf'<{field_code}>(.*?)(?:</{field_code}>|(?=<[A-Z]+>|$))'
        match = re.search(pattern, raw_analysis_text, re.DOTALL)
        
        if match:
            content = match.group(1).strip()
            # Skip if content is just "No significant data."
            if content.lower() != "«no significant data.»":
                # Convert line breaks to HTML <br> tags and wrap in paragraph
                content_html = content.replace('\n', '<br>')
                formatted_sections.append(f'<h4 style="color: #007bff; margin: 15px 0 5px 0;">{field_title}</h4><p style="margin: 0 0 15px 0; line-height: 1.6;">{content_html}</p>')
        else:
            # If field not found, try alternative pattern without closing tag
            alt_pattern = rf'<{field_code}>(.*?)(?=<[A-Z]+>|$)'
            alt_match = re.search(alt_pattern, raw_analysis_text, re.DOTALL)
            if alt_match:
                content = alt_match.group(1).strip()
                if content.lower() != "«no significant data.»":
                    # Convert line breaks to HTML <br> tags and wrap in paragraph
                    content_html = content.replace('\n', '<br>')
                    formatted_sections.append(f'<h4 style="color: #007bff; margin: 15px 0 5px 0;">{field_title}</h4><p style="margin: 0 0 15px 0; line-height: 1.6;">{content_html}</p>')
    
    # If no sections were found, return the original content as HTML
    if not formatted_sections:
        # Convert line breaks to HTML <br> tags and wrap in paragraph
        content_html = raw_analysis_text.replace('\n', '<br>')
        return f'<p style="line-height: 1.6;">{content_html}</p>'
    
    # Join all sections (no need for extra spacing since we have proper HTML margins)
    return "".join(formatted_sections)


def _create_stock_analysis_html_body_with_analysis(analyses: list, days: int) -> str:
    """
    Create the HTML body for stock analysis email with actual analysis data.
    
    Args:
        analyses (list): List of (ticker, analysis_text, grade) tuples
        days (int): Number of days for charts
        
    Returns:
        str: Complete HTML body
    """
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 20px; 
            }}
            .ticker-section {{ 
                margin: 20px 0; 
                padding: 15px; 
                border: 1px solid #ddd; 
                border-radius: 5px; 
            }}
            .ticker-name {{ 
                font-size: 18px; 
                font-weight: bold; 
                color: #333; 
            }}
            .analysis {{ 
                margin: 10px 0; 
                line-height: 1.5; 
            }}
            .grade {{ 
                font-weight: bold; 
                color: #007bff; 
            }}
            .chart-image {{ 
                margin: 10px 0; 
                text-align: center; 
            }}
            .chart-image img {{ 
                max-width: 100%; 
                height: auto; 
                border: 1px solid #ccc; 
            }}
        </style>
    </head>
    <body>
        <h2>Stock Analysis Report</h2>
        <p>Hello, here are your daily stock analyses with charts:</p>
    """
    
    # Add ticker sections with actual analysis data
    for i, (ticker, analysis_text, grade) in enumerate(analyses):
        # Format the analysis text for display
        print(f"_create_stock_analysis_html_body_with_analysis: analysis_text: {analysis_text}")
        formatted_analysis = _format_analysis_text_for_display(analysis_text)
        print(f"_create_stock_analysis_html_body_with_analysis: formatted_analysis: {formatted_analysis}")
        
        html_body += f"""
        <div class="ticker-section">
            <div class="ticker-name">{ticker}</div>
            <div class="analysis">{formatted_analysis}</div>
            <div class="grade">Grade: {grade}</div>
            <div class="chart-image">
                <img src="cid:image_{i}" alt="{ticker} Chart">
            </div>
        </div>
        """
    
    html_body += """
    </body>
    </html>
    """
    
    return html_body


def _create_stock_analysis_html_body(tickers: list, days: int) -> str:
    """
    Create the HTML body for stock analysis email (legacy function).
    
    Args:
        tickers (list): List of ticker symbols
        days (int): Number of days for charts
        
    Returns:
        str: Complete HTML body
    """
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 20px; 
            }}
            .ticker-section {{ 
                margin: 20px 0; 
                padding: 15px; 
                border: 1px solid #ddd; 
                border-radius: 5px; 
            }}
            .ticker-name {{ 
                font-size: 18px; 
                font-weight: bold; 
                color: #333; 
            }}
            .analysis {{ 
                margin: 10px 0; 
                line-height: 1.5; 
            }}
            .grade {{ 
                font-weight: bold; 
                color: #007bff; 
            }}
            .chart-image {{ 
                margin: 10px 0; 
                text-align: center; 
            }}
            .chart-image img {{ 
                max-width: 100%; 
                height: auto; 
                border: 1px solid #ccc; 
            }}
        </style>
    </head>
    <body>
        <h2>Stock Analysis Report</h2>
        <p>Hello, here are your daily stock analyses with charts:</p>
    """
    
    # Add ticker sections
    for i, ticker in enumerate(tickers):
        html_body += f"""
        <div class="ticker-section">
            <div class="ticker-name">{ticker}</div>
            <div class="analysis">Analysis for {ticker} - {days} day candlestick chart</div>
            <div class="grade">Chart Type: Candlestick (OHLCV)</div>
            <div class="chart-image">
                <img src="cid:image_{i}" alt="{ticker} Chart">
            </div>
        </div>
        """
    
    html_body += """
    </body>
    </html>
    """
    
    return html_body


def get_yesterdays_ticker_analyses_for_user(email: str):
    """
    Pull all relevant data about yesterday's tickers related to a user's email.
    Args:
        email (str): The user's email address.
    Returns:
        List of (ticker, analysis_text) tuples for yesterday.
    """
    # Get DB credentials
    creds = {
        'host': get("database.host"),
        'user': get("database.user"),
        'password': get("database.password"),
        'database': get("database.name")
    }
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()
        # 1. Get user's tickers
        cursor.execute("SELECT tickers FROM fact_users_data_table WHERE email=%s", (email,))
        row = cursor.fetchone()
        if not row or not row[0]:
            print(f"No tickers found for user {email}")
            return []
        tickers_str = str(row[0])
        tickers = [t.strip() for t in tickers_str.split(",") if t.strip()]
        # 2. For each ticker, get yesterday's analysis
        yesterday = (datetime.now() - timedelta(days=1)).date()
        results = []
        for ticker in tickers:
            cursor.execute(
                """
                SELECT text_analysis, grade FROM self_ai_analysis_ticker
                WHERE company_ticker=%s AND analysis_event_date=%s and test_ind=0
                ORDER BY insertion_time DESC LIMIT 1
                """,
                (ticker, yesterday)
            )
            analysis_row = cursor.fetchone()
            if analysis_row and analysis_row[0]:
                results.append((ticker, analysis_row[0], analysis_row[1]))
        return results
    except Exception as e:
        print(f"DB error: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()



