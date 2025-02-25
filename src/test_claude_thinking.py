#!/usr/bin/env python3
"""
Simple test for Claude 3.7 Sonnet with extended thinking capabilities.
This standalone script demonstrates how to use the Bedrock converse API
with extended thinking and process the results.
"""

import boto3
import json
import logging
import asyncio
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_claude_thinking():
    """Test Claude 3.7 with extended thinking"""
    
    # Initialize Bedrock client
    client = boto3.client(
        'bedrock-runtime',
        region_name='us-east-1'
    )
    
    # Create system prompt
    system_prompt = [{
        "text": "You are a helpful assistant. When answering questions, explain your reasoning step by step."
    }]
    
    # Create user message
    messages = [{
        "role": "user",
        "content": [{"text": "9.11 and 9.2 which is larger?"}]
    }]
    
    # Create request parameters
    request_params = {
        "modelId": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "messages": messages,
        "system": system_prompt,
        "inferenceConfig": {
            "temperature": 1, # must = 1
            "maxTokens": 20000
        },
        "additionalModelRequestFields": {
            "anthropic_beta": ["output-128k-2025-02-19"],
            "thinking": {
                "type": "enabled",
                "budget_tokens": 4000
            }
        }
    }
    
    try:
        # Call Bedrock converse API
        response = client.converse(**request_params)
        
        # Log token usage
        token_usage = response['usage']
        logger.info("Input tokens: %s", token_usage['inputTokens'])
        logger.info("Output tokens: %s", token_usage['outputTokens'])
        logger.info("Total tokens: %s", token_usage['totalTokens'])
        
        # Process response
        output_message = response['output']['message']
        content = output_message.get('content', [])
        
        # Extract reasoning and answer
        reasoning = ""
        answer = ""
        
        for block in content:
            if 'reasoningContent' in block:
                # Process thinking block
                reasoning_data = block['reasoningContent']
                if isinstance(reasoning_data, dict) and 'reasoningText' in reasoning_data:
                    reasoning = reasoning_data['reasoningText']['text']
            elif 'text' in block:
                # Process answer
                answer = block['text']
        
        # Print results
        print("\n=== REASONING ===\n")
        print(reasoning)
        print("\n=== ANSWER ===\n")
        print(answer)
        
    except Exception as e:
        logger.error("Error accessing AWS Bedrock: %s", str(e))

if __name__ == "__main__":
    asyncio.run(test_claude_thinking())
