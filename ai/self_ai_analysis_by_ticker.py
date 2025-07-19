"""
ai/self_ai_analysis_by_ticker.py
Mission: This module provides functions to analyze a stock ticker in isolation using GPT API.
It retrieves configuration data, runs AI analysis, processes the output, and stores results
in the self_ai_analysis_ticker database table.
"""

import json
import logging
import re
from datetime import datetime, date
from typing import Dict, Any, Tuple, Optional
import mysql.connector
from mysql.connector import Error
from openai import OpenAI
from config.config import get
from config.models_prompt import prompt_by_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')


def get_db_credentials() -> Dict[str, str]:
    """
    Mission: Retrieve database credentials from the configuration file.
    
    Returns:
        Dict[str, str]: Dictionary containing database connection parameters
    """
    return {
        'host': get("database.host"),
        'user': get("database.user"),
        'password': get("database.password"),
        'database': get("database.name")
    }


def extract_system_message_and_model(analysis_type: str, model: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Mission: Extract system message and model from config based on analysis type.
    
    Args:
        analysis_type (str): Type of analysis ('day' or 'week')
        model (str, optional): Specific model to use. If None, uses config default.
        
    Returns:
        Tuple[str, str, str]: System message, model name, and assistant rules
        
    Raises:
        ValueError: If analysis_type is not 'day' or 'week'
    """
    if analysis_type not in ['day', 'week']:
        raise ValueError(f"Invalid analysis_type: {analysis_type}. Must be 'day' or 'week'")
    
    # Get system message based on analysis type
    if analysis_type == "day":
        system_message_key = "daily_analysis_system_message"
    elif analysis_type == "week":
        system_message_key = "weekly_analysis_system_message"
    else:
        raise ValueError(f"Invalid analysis_type: {analysis_type}. Must be 'day' or 'week'")
    
    # Use provided model or get from config
    model_to_use = model if model else get("self_analysis.model")
    system_message, assistant_rules = prompt_by_model(model_to_use, analysis_type)
    
    if not system_message:
        raise ValueError(f"System message not found for analysis_type: {analysis_type}")
    
    if not model_to_use:
        raise ValueError("Model not found in configuration")
    
    return system_message, model_to_use, assistant_rules


def get_weights_for_analysis(analysis_type: str) -> Dict[str, float]:
    """
    Mission: Get weights for the specified analysis type from configuration.
    
    Args:
        analysis_type (str): Type of analysis ('day' or 'week')
        
    Returns:
        Dict[str, float]: Dictionary of weights for different analysis components
    """
    weights_key = f"{analysis_type}_weights_default"
    weights = get(f"self_analysis.{weights_key}")
    
    if not weights:
        logging.warning(f"Weights not found for {analysis_type}, using empty dict")
        return {}
    
    return weights


def run_gpt_analysis(system_message: str, user_message: str, model: str, assistant_rules: str) -> Tuple[str, int, int]:
    """
    Mission: Run GPT analysis using OpenAI API with the given system and user messages.
    
    Args:
        system_message (str): System message for GPT
        user_message (str): User message containing ticker and weights
        model (str): GPT model to use
        
    Returns:
        Tuple[str, int, int]: Content, prompt_tokens, execution_tokens
    """
    client = OpenAI(api_key=get('api_key_gpt'))
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "system", "name": "assistant_rules", "content": assistant_rules.strip()},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0,
            max_tokens=1000
        )
        
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        execution_tokens = usage.completion_tokens if usage else 0
        
        # Get the response content
        content = response.choices[0].message.content
        
        if content is None:
            return "No response received", prompt_tokens, execution_tokens
        
        return content, prompt_tokens, execution_tokens
        
    except Exception as e:
        logging.error(f"OpenAI analysis error: {e}")
        return str(e), 0, 0


def parse_gpt_output(content: str) -> Tuple[str, float]:
    """
    Mission: Parse GPT output to extract text analysis and grade.
    
    Args:
        content (str): Raw output from GPT
        
    Returns:
        Tuple[str, float]: Text analysis and grade (1.0-10.0 scale)
    """
    if not content or content.strip() == "":
        return "No analysis provided", 5.0
    
    # Try to parse as JSON first (for backward compatibility)
    try:
        parsed_response = json.loads(content)
        if isinstance(parsed_response, dict):
            score = parsed_response.get('score', 0.0)
            explanation = parsed_response.get('explanation', content)
            # Convert legacy 0-1 scale to 1-10 scale
            if 0 <= score <= 1:
                score = 1 + (score * 9)  # Convert 0-1 to 1-10
            return explanation, float(score)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # For new format: Look for a grade at the end of the text
    # The new system messages output grades from 1.0 to 10.0 at the very end
    content_stripped = content.strip()
    
    # Look for a number at the very end of the entire content (not just last line)
    # Pattern: number followed by optional whitespace at the end
    grade_match = re.search(r'(\d+\.?\d*)\s*$', content_stripped)
    if grade_match:
        try:
            grade = float(grade_match.group(1))
            # Validate grade is in the correct range (1.0-10.0)
            if 1.0 <= grade <= 10.0:
                # Remove the grade from the text analysis
                text_analysis_raw = content_stripped.replace(grade_match.group(0), '').strip()
                # Extract grade from <GRADE> tags if present
                grade_match_tag = re.search(r'<GRADE>(\d+\.?\d*)</GRADE>', text_analysis_raw)
                if grade_match_tag:
                    try:
                        extracted_grade = float(grade_match_tag.group(1))
                        if 1.0 <= extracted_grade <= 10.0:
                            grade = extracted_grade
                            # Remove <GRADE> tags from text
                            text_analysis = re.sub(r'<GRADE>\d+\.?\d*</GRADE>', '', text_analysis_raw).strip()
                        else:
                            text_analysis = text_analysis_raw
                    except ValueError:
                        text_analysis = text_analysis_raw
                else:
                    text_analysis = text_analysis_raw
                return text_analysis, grade
            else:
                logging.warning(f"Grade {grade} is outside valid range (1.0-10.0), using default")
        except ValueError:
            pass
    
    # If no valid grade found, return the full content as text analysis with default grade
    # Extract grade from <GRADE> tags if present
    grade_match_tag = re.search(r'<GRADE>(\d+\.?\d*)</GRADE>', content_stripped)
    if grade_match_tag:
        try:
            extracted_grade = float(grade_match_tag.group(1))
            if 1.0 <= extracted_grade <= 10.0:
                grade = extracted_grade
                # Remove <GRADE> tags from text
                text_analysis = re.sub(r'<GRADE>\d+\.?\d*</GRADE>', '', content_stripped).strip()
            else:
                text_analysis = content_stripped
                grade = 5.0
        except ValueError:
            text_analysis = content_stripped
            grade = 5.0
    else:
        text_analysis = content_stripped
        grade = 5.0
    return text_analysis, grade





def insert_analysis_to_database(
    analysis_event_date: date,
    company_ticker: str,
    analysis_type: str,
    text_analysis: str,
    grade: float,
    model: str,
    weights: str,
    prompt_tokens: int,
    execution_tokens: int,
    test_ind: int = 0,
    test_name: Optional[str] = None
) -> bool:
    """
    Mission: Insert analysis results into the self_ai_analysis_ticker database table.
    
    Args:
        analysis_event_date (date): Date for which analysis was performed
        company_ticker (str): Stock ticker symbol
        analysis_type (str): Type of analysis ('day' or 'week')
        text_analysis (str): Text analysis from GPT
        grade (float): Numerical grade from GPT
        model (str): GPT model used
        weights (str): JSON string of weights used
        prompt_tokens (int): Number of prompt tokens used
        execution_tokens (int): Number of execution tokens used
        test_ind (int): Test indicator (0 or 1), default 0
        
    Returns:
        bool: True if insertion successful, False otherwise
    """
    creds = get_db_credentials()
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(**creds)
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO self_ai_analysis_ticker 
        (insertion_time, analysis_event_date, company_ticker, analysis_type, 
         text_analysis, grade, model, weights, prompt_tokens, execution_tokens, test_ind, test_name)
        VALUES (current_timestamp, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        text_analysis = VALUES(text_analysis),
        grade = VALUES(grade),
        model = VALUES(model),
        weights = VALUES(weights),
        prompt_tokens = VALUES(prompt_tokens),
        execution_tokens = VALUES(execution_tokens),
        test_ind = VALUES(test_ind),
        test_name = VALUES(test_name)
        """
        
        cursor.execute(insert_query, (
            analysis_event_date,
            company_ticker,
            analysis_type,
            text_analysis,
            grade,
            model,
            weights,
            prompt_tokens,
            execution_tokens,
            test_ind,
            test_name
        ))
        
        cursor.execute(insert_query, (
            analysis_event_date,
            company_ticker,
            analysis_type,
            text_analysis,
            grade,
            model,
            weights,
            prompt_tokens,
            execution_tokens,
            test_ind,
            test_name
        ))
        
        conn.commit()
        logging.info(f"Successfully inserted analysis for {company_ticker} - {analysis_type}")
        return True
        
    except Error as e:
        logging.error(f"Database error inserting analysis: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def self_ai_analysis_by_ticker(
    analysis_event_date: date,
    company_ticker: str,
    model: str,
    weights: str = "",
    analysis_type: str = "day",
    test: str = "no",
    test_name: Optional[str] = "production"
) -> Dict[str, Any]:
    """
    Mission: Main function to analyze a stock ticker in isolation.
    
    This function performs the complete analysis process:
    1. Extracts system message and model from config
    2. Prepares user message with ticker and weights
    3. Runs GPT analysis
    4. Parses the output to extract text analysis and grade
    5. Inserts results into database
    
    Args:
        analysis_event_date (date): Date for which analysis is performed
        company_ticker (str): Stock ticker symbol (e.g., "AAPL")
        model (str): GPT model to use (e.g., "gpt-3.5-turbo")
        weights (str): JSON string of weights for analysis components
        analysis_type (str): Type of analysis ('day' or 'week')
        test (str): Test indicator ('yes' or 'no'), default 'no'
        
    Returns:
        Dict[str, Any]: Dictionary containing analysis results and status
        
    Example:
        >>> result = self_ai_analysis_by_ticker(
        ...     date(2024, 1, 15),
        ...     "AAPL",
        ...     "gpt-3.5-turbo",
        ...     '{"technical_analysis": 0.5, "news_analysis": 0.3, "analysts_rating": 0.2}',
        ...     "day",
        ...     "no"
        ... )
    """
    try:
        # Validate inputs
        if not company_ticker or not isinstance(company_ticker, str):
            raise ValueError("company_ticker must be a non-empty string")
        
        if analysis_type not in ['day', 'week']:
            raise ValueError("analysis_type must be 'day' or 'week'")
        
        if test not in ['yes', 'no']:
            raise ValueError("test must be 'yes' or 'no'")
        
        # Convert test string to integer
        test_ind = 1 if test.lower() == 'yes' else 0

        # Extract system message and model from config
        system_message, config_model, assistant_rules = extract_system_message_and_model(analysis_type)
        
        # Use provided model if specified, otherwise use config model
        # If a different model is provided, get the appropriate analysis for that model
        if model and model != config_model:
            # Get analysis configuration for the specific model
            system_message, _, assistant_rules = extract_system_message_and_model(analysis_type, model)
            model_to_use = model
        else:
            model_to_use = config_model
        
        # Parse weights string to dict, use defaults if not provided
        if weights and weights.strip():
            try:
                weights_dict = json.loads(weights)
            except json.JSONDecodeError:
                logging.warning(f"Invalid weights JSON: {weights}, using default weights")
                weights_dict = get_weights_for_analysis(analysis_type)
        else:
            # Use default weights from config
            weights_dict = get_weights_for_analysis(analysis_type)
            logging.info(f"Using default weights for {analysis_type} analysis: {weights_dict}")
        
        # Prepare user message with ticker and weights
        user_message = f"Ticker: {company_ticker}\nWeights: {json.dumps(weights_dict, indent=2)}"
        
        # Run GPT analysis
        content, prompt_tokens, execution_tokens = run_gpt_analysis(
            system_message, user_message, model_to_use, assistant_rules
        )
        
        # Parse the output
        text_analysis, grade = parse_gpt_output(content)
        
        # Clean and validate data
        if not text_analysis or text_analysis.strip() == "":
            text_analysis = "No analysis provided"
        
        # Validate grade is between 1.0 and 10.0
        if not isinstance(grade, (int, float)) or grade < 1.0 or grade > 10.0:
            grade = 5.0
        
        # Insert into database
        success = insert_analysis_to_database(
            analysis_event_date=analysis_event_date,
            company_ticker=company_ticker,
            analysis_type=analysis_type,
            text_analysis=text_analysis,
            grade=grade,
            model=model_to_use,
            weights=json.dumps(weights_dict),
            prompt_tokens=prompt_tokens,
            execution_tokens=execution_tokens,
            test_ind=test_ind,
            test_name=test_name
        )
        
        return {
            'success': success,
            'company_ticker': company_ticker,
            'analysis_type': analysis_type,
            'text_analysis': text_analysis,
            'grade': grade,
            'model': model_to_use,
            'weights': json.dumps(weights_dict),
            'prompt_tokens': prompt_tokens,
            'execution_tokens': execution_tokens,
            'test_ind': test_ind,
            'test_name': test_name,
            'analysis_event_date': str(analysis_event_date)
        }
        
    except Exception as e:
        logging.error(f"Error in self_ai_analysis_by_ticker: {e}")
        return {
            'success': False,
            'error': str(e),
            'company_ticker': company_ticker,
            'analysis_type': analysis_type,
            'test_name': test_name,
            'analysis_event_date': str(analysis_event_date) if analysis_event_date else None
        }


def run_analysis_example():
    """
    Mission: Example function to demonstrate how to use self_ai_analysis_by_ticker.
    
    This function shows how to call the main analysis function with sample data.
    """
    from datetime import date, timedelta
    
    # Example 1: With custom weights
    print("Example 1: With custom weights")
    print("-" * 50)
    analysis_event_date = date.today() - timedelta(days=1)
    company_ticker = "AAPL"
    model = "gpt-3.5-turbo"
    custom_weights = get("self_analysis.day_weights_default")
    analysis_type = "day"
    test = "yes"
    
    print(f"Ticker: {company_ticker}")
    print(f"Analysis Type: {analysis_type}")
    print(f"Model: {model}")
    print(f"Custom Weights: {custom_weights}")
    
    result1 = self_ai_analysis_by_ticker(
        analysis_event_date=analysis_event_date,
        company_ticker=company_ticker,
        model=model,
        weights=json.dumps(custom_weights),
        analysis_type=analysis_type,
        test=test,
        test_name="example1"
    )
    
    if result1['success']:
        print("✅ Analysis with custom weights completed successfully!")
        print(f"Grade: {result1['grade']}")
        print(f"Text Analysis: {result1['text_analysis'][:100]}...")
    else:
        print(f"❌ Analysis failed: {result1.get('error', 'Unknown error')}")
    
    # Example 2: Using default weights (no weights provided)
    print("\nExample 2: Using default weights")
    print("-" * 50)
    
    result2 = self_ai_analysis_by_ticker(
        analysis_event_date=analysis_event_date,
        company_ticker="MSFT",
        model=model,
        weights="",  # Empty string will use default weights
        analysis_type="week",
        test=test,
        test_name="example2"
    )
    
    if result2['success']:
        print("✅ Analysis with default weights completed successfully!")
        print(f"Grade: {result2['grade']}")
        print(f"Text Analysis: {result2['text_analysis'][:100]}...")
        print(f"Default Weights Used: {result2['weights']}")
    else:
        print(f"❌ Analysis failed: {result2.get('error', 'Unknown error')}")
    
    return result1  # Return the first result for backward compatibility


if __name__ == "__main__":
    # Run example when script is executed directly
    run_analysis_example() 