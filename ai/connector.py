"""
ai/connector.py
Mission: This module provides the interface to OpenAI's GPT models for AI analysis, including functions to send prompts and receive responses with proper error handling and token tracking.
"""

import openai
from config.config import get
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

# Configure OpenAI client
openai.api_key = get("api_key_openai")

def send_to_gpt(system_message: str, user_message: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Mission: Send a message to GPT and return the response with token usage information.
    
    Returns:
        Dict with keys: 'response', 'prompt_tokens', 'completion_tokens', 'total_tokens'
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return {
            'response': response.choices[0].message.content,
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
        
    except Exception as e:
        logging.error(f"Error sending message to GPT: {e}")
        return {
            'response': f"Error: {str(e)}",
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        }

def analyze_with_gpt(data: str, analysis_type: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Mission: Perform AI analysis on data using GPT with predefined system messages.
    
    Args:
        data: The data to analyze (JSON string, text, etc.)
        analysis_type: Type of analysis ('technical_analysis', 'analysts_rating', 'news_analysis')
        model: GPT model to use
    
    Returns:
        Dict with analysis results and token usage
    """
    try:
        # Get system message for the analysis type
        system_message = get(f"{analysis_type}.system_message")
        
        if not system_message:
            logging.error(f"No system message found for analysis type: {analysis_type}")
            return {
                'response': f"Error: No system message configured for {analysis_type}",
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            }
        
        # Send to GPT
        result = send_to_gpt(system_message, data, model)
        
        logging.info(f"Completed {analysis_type} analysis with {result['total_tokens']} tokens")
        return result
        
    except Exception as e:
        logging.error(f"Error in analyze_with_gpt: {e}")
        return {
            'response': f"Error: {str(e)}",
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        } 