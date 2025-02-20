import subprocess
from typing import Dict, Tuple, Optional
import json
import shlex

class CommandExecutor:
    def __init__(self):
        self.last_result: Optional[Dict] = None

    def execute_command(self, command: str) -> Tuple[str, bool]:
        """
        Execute a shell command and return its output and success status.
        
        Args:
            command: The command to execute
            
        Returns:
            Tuple of (output, success)
        """
        try:
            # Split command into arguments while preserving quoted strings
            args = shlex.split(command)
            
            # Execute command and capture output
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )
            
            # Store result for context
            self.last_result = {
                'command': command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
            # Combine stdout and stderr for output
            output = result.stdout
            if result.stderr:
                output += f"\nErrors:\n{result.stderr}"
                
            return output.strip(), result.returncode == 0
            
        except subprocess.SubprocessError as e:
            error_msg = f"Command execution failed: {str(e)}"
            self.last_result = {
                'command': command,
                'error': error_msg,
                'return_code': -1
            }
            return error_msg, False
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.last_result = {
                'command': command,
                'error': error_msg,
                'return_code': -1
            }
            return error_msg, False

    def parse_aws_output(self, output: str) -> Dict:
        """
        Parse AWS CLI JSON output into a Python dictionary.
        
        Args:
            output: JSON string from AWS CLI
            
        Returns:
            Parsed dictionary or error dict
        """
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {'error': 'Failed to parse AWS CLI output as JSON', 'raw_output': output}

    def format_output(self, output: str, success: bool) -> str:
        """
        Format command output for display.
        
        Args:
            output: Command output string
            success: Whether command succeeded
            
        Returns:
            Formatted output string
        """
        status = "Success" if success else "Failed"
        return f"Command Status: {status}\n\nOutput:\n{output}"
