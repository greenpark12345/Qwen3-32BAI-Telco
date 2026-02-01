#!/usr/bin/env python3
"""
AI API Client Module
Responsible for calling OpenRouter API for problem solving
"""

import re
import time
import requests
import threading

from .config_loader import get_config
from .prompts import NONSTANDARD_TELECOM_SYSTEM, NON_TELECOM_SYSTEM

# Thread lock
print_lock = threading.Lock()


def call_ai_api(system_prompt, user_prompt, max_retries=5):
    """
    Call AI API with enhanced retry mechanism
    
    Args:
        system_prompt: System prompt text
        user_prompt: User prompt text
        max_retries: Maximum retry attempts
        
    Returns:
        tuple: (response_content, success)
    """
    config = get_config()
    
    headers = {
        "Authorization": f"Bearer {config['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
    }
    
    payload = {
        "model": config['MODEL'],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 10000 
    }
    
    # Retryable error types
    retryable_errors = [
        'SSL', 'SSLError', 'UNEXPECTED_EOF', 'EOF occurred',
        'ConnectionReset', 'ConnectionError', 'Timeout',
        'Response ended prematurely', 'Max retries exceeded',
        'RemoteDisconnected', 'ChunkedEncodingError'
    ]
    
    last_error = None
    for attempt in range(max_retries):
        try:
            print(f"    Calling API (attempt {attempt+1}/{max_retries})...")
            response = requests.post(
                config['API_URL'], 
                headers=headers, 
                json=payload, 
                timeout=(15, 90)  # (connection timeout, read timeout) - reduced
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return content, True
            elif response.status_code == 429:
                # Rate limited
                wait_time = 15 * (attempt + 1)
                print(f"    Rate limited, waiting {wait_time}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            elif response.status_code >= 500:
                # Server error
                wait_time = 10 * (attempt + 1)
                print(f"    Server error {response.status_code}, retrying in {wait_time}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"    HTTP {response.status_code}: {response.text[:200]}")
                time.sleep(5)
                
        except requests.exceptions.Timeout as e:
            last_error = str(e)
            wait_time = 8 * (attempt + 1)
            print(f"    Timeout, retrying in {wait_time}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait_time)
        except requests.exceptions.ConnectionError as e:
            last_error = str(e)
            wait_time = 12 * (attempt + 1)
            print(f"    Connection error, retrying in {wait_time}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait_time)
        except Exception as e:
            last_error = str(e)
            error_str = str(e)
            is_retryable = any(err in error_str for err in retryable_errors)
            if is_retryable:
                wait_time = 10 * (attempt + 1)
                print(f"    Retryable error: {error_str[:100]}, retrying in {wait_time}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"    Non-retryable exception: {e}")
                time.sleep(5)
    
    print(f"    All {max_retries} retries failed. Last error: {last_error}")
    return None, False


def extract_ai_answer(response_text, valid_options):
    """
    Extract answer from AI response
    
    Args:
        response_text: AI response text
        valid_options: List of valid options
        
    Returns:
        str: Extracted answer
    """
    if not response_text:
        return valid_options[0] if valid_options else "1"
    
    response_text = response_text.strip()
    
    # 1. If response is a single option, return directly
    if response_text in valid_options:
        return response_text
    
    # 2. Try to match boxed format
    patterns = [
        r'\\boxed\{([^}]+)\}',
        r'boxed\{([^}]+)\}',
        r'Final Answer[:\s]*([A-Z]?\d+|[A-I])',
        r'The answer is[:\s]*([A-Z]?\d+|[A-I])',
        r'Answer[:\s]*([A-I])',
        r'Option[:\s]*([A-I])',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            ans = match.group(1).strip()
            if ans in valid_options:
                return ans
            for opt in valid_options:
                if ans in opt or opt in ans:
                    return opt
    
    # 3. Find option at the beginning of response
    first_line = response_text.split('\n')[0].strip()
    for opt in valid_options:
        if first_line.startswith(opt):
            return opt
    
    # 4. Find option in full text
    for opt in valid_options:
        if re.search(rf'\b{re.escape(opt)}\b', response_text):
            return opt
    
    return valid_options[0] if valid_options else "1"


def build_free_prompt(question, options):
    """
    Build AI prompt
    
    Args:
        question: Question text
        options: Option list
        
    Returns:
        tuple: (system_prompt, user_prompt)
    """
    # Determine question type
    is_telecom = ('RSRP' in question or 'SINR' in question or 'PCI' in question or
                  'Drive Test Data' in question or 'Serving RSRP' in question or 
                  'Throughput' in question or 'throughput' in question)
    
    if is_telecom:
        system_prompt = NONSTANDARD_TELECOM_SYSTEM
    else:
        system_prompt = NON_TELECOM_SYSTEM
    
    user_prompt = f"""{question[:5000]}

Available options: {', '.join(options)}

Output ONLY the option letter:"""
    return system_prompt, user_prompt


def process_ai_task(task):
    """
    Process a single AI task
    
    Args:
        task: Task dictionary containing qid, question, options, rule_answer
        
    Returns:
        dict: Result dictionary
    """
    qid = task['qid']
    question = task['question']
    options = task['options']
    rule_answer = task['rule_answer']
    
    system_prompt, user_prompt = build_free_prompt(question, options)
    
    response, success = call_ai_api(system_prompt, user_prompt)
    
    if success and response:
        ai_answer = extract_ai_answer(response, options)
        
        with print_lock:
            print(f"  [{qid}] AI answer: {ai_answer}")
        
        return {
            'qid': qid,
            'ai_answer': ai_answer,
            'ai_success': True,
            'rule_answer': rule_answer,
        }
    else:
        with print_lock:
            print(f"  [{qid}] AI failed, using rule answer: {rule_answer}")
        
        return {
            'qid': qid,
            'ai_answer': rule_answer,
            'ai_success': False,
            'rule_answer': rule_answer,
        }
