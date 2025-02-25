# Cloud Environment Diagnosis Agent

An intelligent agent that uses the ReAct (Reason-Act) pattern to diagnose and analyze cloud environments. The agent leverages AWS Bedrock's LLM capabilities to understand and respond to queries about your cloud infrastructure, executing relevant commands and providing detailed analysis.

## Features

- Interactive CLI interface with rich formatting
- ReAct pattern implementation with Claude 3.7 Sonnet's extended thinking capabilities:
  - Native thinking blocks for enhanced reasoning
  - Step-by-step reasoning with detailed thought process
  - Support for up to 128K output tokens
  - Automatic thinking budget management (default: 4,000 tokens)
  - Preservation of thinking context across interactions
- Command execution integration for cloud environment analysis
- Real-time display of:
  - Extended thinking process (💭)
  - Actions being executed (⚡)
  - Observations from commands (👁️)
  - Final conclusions (🎯)
- Color-coded output sections for better readability
- Conversation history tracking with thinking block preservation

## Prerequisites

- Python 3.8 or higher
- AWS CLI configured with appropriate credentials
- AWS Bedrock access configured with appropriate permissions
- Claude 3.7 Sonnet model access enabled in AWS Bedrock
- Required Python packages:
  - boto3 >= 1.37.0 (AWS SDK)
  - botocore >= 1.37.0
  - rich >= 13.0.0 (Terminal formatting)
  - typer >= 0.9.0 (CLI interface)
  - pydantic >= 2.0.0 (Data validation)

## Extended Thinking Configuration

The agent uses Claude 3.7 Sonnet's extended thinking capabilities for enhanced reasoning:

- Default thinking budget: 4,000 tokens
- Maximum output length: 24,000 tokens
- Thinking blocks are preserved across conversation turns
- Redacted thinking blocks are handled securely
- Thinking signatures are validated for security

You can customize the thinking configuration when initializing the agent:

```python
from agent.llm import BedrockLLM, ThinkingConfig

# Custom thinking configuration
config = ThinkingConfig(
    type="enabled",
    budget_tokens=8000  # Increase thinking budget for complex tasks
)

# Initialize agent with custom config
llm = BedrockLLM(thinking_config=config)
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cloud-diagnosis
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Ensure AWS credentials and Bedrock access are configured:
```bash
aws configure
```

## Usage

Run the diagnosis agent:
```bash
python src/main.py
```

The agent will start an interactive session where you can ask questions about your cloud environment. The agent follows a systematic approach:

1. Analyzes your query to understand the required information
2. Plans and executes relevant commands
3. Observes and interprets the results
4. Provides a comprehensive answer

Type 'exit' to quit the application.

### Testing Claude 3.7 Extended Thinking

A simple test script is provided to demonstrate Claude 3.7's extended thinking capabilities:

```bash
python src/test_claude_thinking.py
```

This standalone script shows how to:
- Configure the Bedrock converse API with extended thinking
- Process reasoning content from Claude's response
- Extract both reasoning and final answers
- Handle the nested structure of reasoning blocks

The test script is self-contained and doesn't depend on other project components, making it a good reference for understanding how to work with Claude's extended thinking feature directly.

## Example Interaction

```
What would you like to know about your cloud environment?
> Check the health of our services

💭 Thought: I should check the status of key services and their metrics

⚡ Action: aws cloudwatch list-metrics --namespace AWS/EC2 --metric-name CPUUtilization

👁️ Observation: [Command output with metrics data]

💭 Thought: Let me check the service health status as well

⚡ Action: aws health describe-events --filter '{"eventStatusCodes":["open","upcoming"]}'

🎯 Final Answer: All services are currently healthy:
- EC2 instances show normal CPU utilization (average 45%)
- No open AWS Health events or upcoming maintenance
- All monitored metrics are within expected ranges
```

## Project Structure

```
cloud-diagnosis/
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── llm.py          # AWS Bedrock LLM integration
│   │   ├── tools.py        # Command execution and output parsing
│   │   └── react.py        # ReAct pattern implementation with:
│   │                       # - Thought process management
│   │                       # - Action execution
│   │                       # - Observation handling
│   │                       # - Rich terminal output
│   ├── cli/
│   │   ├── __init__.py
│   │   └── interface.py    # Interactive CLI with Typer
│   ├── main.py             # Application entry point
│   └── test_claude_thinking.py  # Standalone test for Claude 3.7 extended thinking
├── requirements.txt        # Project dependencies
└── README.md
```

## Key Components

- **ReactAgent (react.py)**: Implements the ReAct pattern for reasoning and acting
  - Manages thought process and action execution
  - Handles command observations
  - Provides rich terminal output
  - Maintains conversation history

- **CommandExecutor (tools.py)**: Handles command execution
  - Executes shell commands safely
  - Parses command output
  - Handles errors and formatting

- **CLI Interface (interface.py)**: Provides user interaction
  - Interactive command prompt
  - Rich text formatting
  - Error handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
