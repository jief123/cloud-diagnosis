import asyncio
import json
import logging
from agent.llm import BedrockLLM

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def test_bedrock_llm():
    print("\n=== Testing Bedrock LLM Integration ===")
    print("1. Initializing LLM client...")
    try:
        llm = BedrockLLM()
        print("✓ LLM client initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize LLM client: %s", str(e))
        return False

    # Test data
    test_query = "List all running EC2 instances in us-west-2 region"
    context = {
        "region": "us-west-2",
        "service": "EC2",
        "environment": "test"
    }
    history = []

    print("\n2. Testing model invocation...")
    logger.info("Query: %s", test_query)
    logger.info("Context: %s", json.dumps(context, indent=2))
    
    try:
        response = await llm.generate_thought(test_query, context, history)
        print("\n=== Model Response ===")
        print(response)
        print("=====================")
        logger.info("Model invocation successful")
        return True
    except Exception as e:
        logger.error("Model invocation failed: %s", str(e))
        print("\nTroubleshooting tips:")
        print("1. Verify AWS credentials are properly configured")
        print("2. Check if the model ID is correct")
        print("3. Ensure the AWS region has Bedrock access enabled")
        print("4. Verify Bedrock service quota and permissions")
        return False

if __name__ == "__main__":
    print("\nStarting Bedrock LLM integration test...")
    try:
        success = asyncio.run(test_bedrock_llm())
        print(f"\nTest {'completed successfully' if success else 'failed'}")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        print("\nTest failed due to unexpected error")
