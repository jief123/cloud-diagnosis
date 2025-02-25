import boto3
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from botocore.config import Config

config = Config(
    retries = dict(
        max_attempts = 100,  # 最大重试次数
        mode = 'standard'   # 自适应重试模式
    )
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@dataclass
class ThinkingConfig:
    """Configuration for Claude's extended thinking feature"""
    type: str = "enabled"
    budget_tokens: int = 4000

class BedrockLLM:
    def __init__(self, thinking_config: Optional[ThinkingConfig] = None):
        # Initialize boto3 session with cross-region configuration
        self.client = boto3.client(
            'bedrock-runtime',
            config=config,
            region_name='us-east-1'  # Bedrock's primary region for cross-region inference
        )
        self.modelid = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        self.thinking_config = thinking_config or ThinkingConfig()
        self.max_tokens = 24000  # Default max tokens for Claude 3.7 Sonnet

    def _create_system_prompt(self) -> List[Dict]:
        return [{
            "text": """
            You are an infrastructure operator agent that helps users understand their cloud & services environment.

            RESPONSE STRUCTURE:
            After reasoning, provide exactly ONE of:
               - Action: [AWS CLI command or bash command to execute]
               - Final Answer: [If you have no action to take, please conclusion based on all observations]

            THINKING GUIDELINES:
            - Break down complex problems into steps
            - Analyze previous observations before taking new actions
            - Consider alternative approaches when errors occur
            - Explain your reasoning clearly and systematically

            COMMAND GUIDELINES:
            - Use --output json for AWS CLI commands
            - Include --region parameter for AWS commands
            - Use --query parameter to filter AWS CLI output
            - For bash commands, ensure they are safe to execute
            
            ERROR HANDLING:
            - If a command fails, use your thinking process to:
              1. Analyze the error
              2. Consider alternative approaches
              3. Explain your revised strategy
            
            Remember: Your thinking process will be preserved across turns, so focus on systematic reasoning."""
        }]
    
    def _create_messages(self, query: str, history: List[Dict]) -> List[Dict]:
        messages = []
        
        # Handle first query
        if not history:
            messages.append({
                "role": "user",
                "content": [{"text": query}]
            })
            return messages
        
        # Process history with thinking blocks
        for entry in history:
            # Add user query
            messages.append({
                "role": "user",
                "content": [{"text": entry['user_input']}]
            })
            
            # Process each interaction
            for i in range(len(entry['actions'])):
                # Create message content
                content_blocks = []
                
                # Add thought and action as text
                if i < len(entry['thoughts']):
                    content_blocks.append({
                        "text": f"Thought: {entry['thoughts'][i]}\nAction: {entry['actions'][i]}"
                    })
                else:
                    content_blocks.append({
                        "text": f"Action: {entry['actions'][i]}"
                    })
                
                messages.append({
                    "role": "assistant",
                    "content": content_blocks
                })
                
                # Add observation
                messages.append({
                    "role": "user",
                    "content": [{"text": f"Observation: {entry['observations'][i]}"}]
                })
        
        return messages

    def _create_context_messages(self, context: Dict[Any, Any]) -> List[Dict[str, Any]]:
        """创建仅包含上下文操作和观察结果的消息"""
        messages = []
        
        # 添加上下文中的操作和观察结果
        if context:
            context_message = "Previous actions and observations:\n\n"
            for action, observation in context.items():
                context_message += f"{action}\n{observation}\n\n"
            
            messages.append({
                "role": "user",
                "content": [
                    {
                        "text": context_message
                    }
                ]
            })
        
        return messages
    
    async def generate_thought(self, query: str, history: List[Dict]) -> Dict[str, str]:
        try:
            system_prompts = self._create_system_prompt()
            messages = self._create_messages(query, history)     

            request_params = {
                "modelId": self.modelid,
                "messages": messages,
                "system": system_prompts,
                "inferenceConfig": {
                    "temperature": 1,
                    "maxTokens": self.max_tokens
                },
                "additionalModelRequestFields": {
                    "anthropic_beta": ["output-128k-2025-02-19"],
                    "thinking": {
                        "type": self.thinking_config.type,
                        "budget_tokens": self.thinking_config.budget_tokens
                    }
                }
            }

            response = self.client.converse(**request_params)
            
            # Log token usage
            token_usage = response['usage']
            logger.info("Input tokens: %s", token_usage['inputTokens'])
            logger.info("Output tokens: %s", token_usage['outputTokens'])
            logger.info("Total tokens: %s", token_usage['totalTokens'])
            logger.info("Stop reason: %s", response['stopReason'])
            
            output_message = response['output']['message']
            content = output_message.get('content', [])
            
            result = {
                'reasoning': '',
                'action': ''
            }
            
            for block in content:
                if 'reasoningContent' in block:
                    # Process thinking block
                    reasoning = block['reasoningContent']
                    if isinstance(reasoning, dict) and 'reasoningText' in reasoning:
                        result['reasoning'] = reasoning['reasoningText']['text']
                    elif isinstance(reasoning, str):
                        result['reasoning'] = reasoning
                elif 'text' in block:
                    # Process action/final answer
                    result['action'] = block['text']
            
            return result
            
        except Exception as e:
            logger.error("Error accessing AWS Bedrock: %s", str(e))
            return {
                'reasoning': f"Error accessing AWS Bedrock: {str(e)}",
                'action': "Final Answer: I apologize, but I encountered an error while trying to process your request. Please ensure AWS credentials are properly configured and try again."
            }
