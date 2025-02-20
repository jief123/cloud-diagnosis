import boto3
import json
import logging
from typing import List, Dict, Any
from botocore.config import Config




config = Config(
    retries = dict(
        max_attempts = 100,  # 最大重试次数
        mode = 'standard'   # 自适应重试模式
    )
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class BedrockLLM:
    def __init__(self):
        # Initialize boto3 session with cross-region configuration
        self.client = boto3.client(
            'bedrock-runtime',
            config=config,
            region_name='us-east-1'  # Bedrock's primary region for cross-region inference
        )
        self.modelid = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        #self.modelid = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

    def _create_system_prompt(self) -> List[Dict]:
        return [{
            "text": """
            You are a infrastructure operator agent. Your goal is to help users understand their cloud & Services environment.

            AVAILABLE TOOLS:

            Basic bash commands for system information, on basic shell can use ssh command to logging into remote server and check aws enviroment with
            AWS CLI commands (e.g., aws ec2 describe-instances, aws cloudwatch get-metric-data)
            RESPONSE FORMAT:
            You should provide ONE Thought and ONE Action at a time, then wait for user's response before proceeding.
            Follow this exact format:

            Thought: [Your detailed reasoning about what information you need and why]
            Action: [The exact command to execute]


            If you don't have any other action to take, please Follow this exact format:
            Final Answer: [Clear, concise conclusion based on the observations]

            IMPORTANT RULES:

            NEVER skip the Thought and Action steps - they are required
            All AWS CLI command should be generate json output with --output json
            Include necessary parameters like --region for AWS commands
            Use --query parameter to filter AWS CLI output when possible
            Be explicit about what you're checking and why
            If an error occurs, explain it in your reasoning and try an alternative approach"""
        }]
    
    def _create_messages(self, query: str, history: List[Dict]) -> List[Dict]:
        messages = []
        
        # 如果是第一次查询，只添加用户问题
        if not history:
            messages.append({
                "role": "user",
                "content": [{"text": query}]
            })
            return messages
        
        # 处理历史记录
        for entry in history:
            # 添加用户原始查询
            messages.append({
                "role": "user",
                "content": [{"text": entry['user_input']}]
            })
            
            # 逐个添加 thought + action 和对应的 observation
            for i in range(len(entry['actions'])):
                # 添加 thought + action
                assistant_content = ""
                if i < len(entry['thoughts']):  # 确保thought存在
                    assistant_content += f"Thought: {entry['thoughts'][i]}\n"
                assistant_content += f"Action: {entry['actions'][i]}"
                
                messages.append({
                    "role": "assistant",
                    "content": [{"text": assistant_content}]
                })
                
                # 添加对应的 observation
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
    
    async def generate_thought(self, query: str, history: List[Dict]) -> str:
        try:
            system_prompts = self._create_system_prompt()
            messages = self._create_messages(query, history)     

            response = self.client.converse(
                modelId=self.modelid,
                messages=messages,
                system=system_prompts,
                inferenceConfig={"temperature": 0.7},
                additionalModelRequestFields={"top_k": 200}
            )
            
            # Log token usage
            token_usage = response['usage']
            logger.info("Input tokens: %s", token_usage['inputTokens'])
            logger.info("Output tokens: %s", token_usage['outputTokens'])
            logger.info("Total tokens: %s", token_usage['totalTokens'])
            logger.info("Stop reason: %s", response['stopReason'])
            
            output_message = response['output']['message']
            completion = output_message['content'][0]['text']
            
            # Ensure response starts with a thought
 #           if not completion.strip().startswith('Thought:'):
 #               thought = "I need to check the EC2 instances in the specified region. I'll use the describe-instances command to get this information."
  #              action = "aws ec2 describe-instances --region us-east-1 --query 'Reservations[].Instances[]' --output json"
  #              return f"Thought: {thought}\nAction: {action}"
            
            return completion
            
        except Exception as e:
            logger.error("Error accessing AWS Bedrock: %s", str(e))
            return f"Thought: There was an error accessing AWS Bedrock: {str(e)}\nFinal Answer: I apologize, but I encountered an error while trying to process your request. Please ensure AWS credentials are properly configured and try again."
