from typing import List, Dict, Union, Any, Optional
from .llm import BedrockLLM
from .tools import CommandExecutor
import json
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

class ReactAgent:
    def __init__(self):
        self.llm = BedrockLLM()
        self.executor = CommandExecutor()
        self.conversation_history: List[Dict] = []
#        self.current_context: Dict[str, Any] = {}
        self.console = Console()

    def _display_thought(self, thought: str):
        """Display the agent's thought process"""
        self.console.print("\n")
        self.console.print(Panel(
            Markdown(f"💭 **Thought Process**\n\n{thought}"),
            border_style="blue",
            title="Reasoning Step",
            expand=True
        ))

    def _display_action(self, action: str):
        """Display the action being taken"""
        self.console.print("\n")
        self.console.print(Panel(
            Markdown(f"⚡ **Executing Command**\n\n```bash\n{action}\n```"),
            border_style="yellow",
            title="Action",
            expand=True
        ))

    def _display_observation(self, observation: str):
        """Display the observation from the action"""
        # Split observation into command and result
        parts = observation.split("\n\nResult:\n", 1)
        if len(parts) == 2:
            command, result = parts
            formatted_content = (
                f"**Command Executed:**\n```bash\n{command.replace('Command executed: ', '')}\n```\n\n"
                f"**Output:**\n```json\n{result}\n```"
            )
        else:
            formatted_content = f"```\n{observation}\n```"

        self.console.print("\n")
        self.console.print(Panel(
            Markdown(formatted_content),
            border_style="green",
            title="Observation",
            expand=True
        ))

    def _display_final_answer(self, answer: str):
        """Display the final answer"""
        self.console.print("\n")
        self.console.print(Panel(
            Markdown(f"🎯 **Conclusion**\n\n{answer}"),
            border_style="red",
            title="Final Answer",
            expand=True
        ))

    def _parse_llm_response(self, response: str) -> Dict[str, str]:
        """Parse the LLM response into components"""
        components = {
            'thought': [],
            'action': '',
            'final_answer': ''
        }
        
        current_section = None
        current_content = []
        
        # Split response into lines and process each line
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Thought:'):
                # If we were building another section, save it
                if current_section and current_content:
                    if current_section == 'thought':
                        components['thought'].append('\n'.join(current_content))
                    else:
                        components[current_section] = '\n'.join(current_content)
                current_section = 'thought'
                current_content = [line[8:].strip()]
            elif line.startswith('Action:'):
                # Save any previous section
                if current_section == 'thought' and current_content:
                    components['thought'].append('\n'.join(current_content))
                elif current_section and current_content:
                    components[current_section] = '\n'.join(current_content)
                current_section = 'action'
                current_content = [line[7:].strip()]
            elif line.startswith('Final Answer:'):
                # Save any previous section
                if current_section == 'thought' and current_content:
                    components['thought'].append('\n'.join(current_content))
                elif current_section and current_content:
                    components[current_section] = '\n'.join(current_content)
                current_section = 'final_answer'
                current_content = [line[13:].strip()]
            elif current_section:
                current_content.append(line)
        
        # Save the last section being built
        if current_section and current_content:
            if current_section == 'thought':
                components['thought'].append('\n'.join(current_content))
            else:
                components[current_section] = '\n'.join(current_content)
        
        # Convert thought list to string if needed
        if components['thought']:
            components['thought'] = components['thought'][0] if len(components['thought']) == 1 else '\n'.join(components['thought'])
        else:
            components['thought'] = ''
            
        return components

#    def _update_context(self, action_result: str, success: bool):
        """Update the current context with new information"""
        if success and action_result:
            try:
                # Try to parse as JSON for AWS CLI output
                result_json = json.loads(action_result)
                
                # 如果是嵌套列表，拍平它
                if isinstance(result_json, list):
                    flattened = [
                        item 
                        for sublist in result_json 
                        for subsublist in sublist 
                        for item in subsublist
                    ]
                    self.current_context['last_result'] = flattened
                else:
                    self.current_context['last_result'] = result_json
                    
            except json.JSONDecodeError:
                # Store as plain text if not JSON
                self.current_context['last_result'] = action_result
    
    async def process_query(self, query: str) -> str:
        """
        Process a user query through the ReAct loop
        
        Args:
            query: User's question about the cloud environment
            
        Returns:
            Final answer to the user's question
        """
        # Create new conversation entry
        conversation_entry = {
            'user_input': query,
            'thoughts': [],
            'actions': [],
            'observations': []
        }

        final_answer = None
        max_iterations = 30
        iteration = 0
        current_prompt = query

        while not final_answer and iteration < max_iterations:
            # Generate next thought and action
            response = await self.llm.generate_thought(
                query=current_prompt,
                history=self.conversation_history
            )
            
            # Handle reasoning
            if response['reasoning']:
                self._display_thought(response['reasoning'])
                conversation_entry['thoughts'].append(response['reasoning'])
            
            # Parse action response
            components = self._parse_llm_response(response['action'])
            
            # If we have a final answer, break the loop
            if components['final_answer']:
                final_answer = components['final_answer']
                self._display_final_answer(final_answer)
                break
            
            # Handle actions
            actions = [components['action']] if components['action'] else []
            observations = []
            
            for action in actions:
                if not action.strip():
                    continue
                    
                self._display_action(action)
                conversation_entry['actions'].append(action)
                
                # Execute the command
                output, success = self.executor.execute_command(action)
                
                # Format the output for display
                if success:
                    try:
                        # Try to parse and pretty print JSON output
                        json_output = json.loads(output)
                        formatted_output = json.dumps(json_output, indent=2)
                    except json.JSONDecodeError:
                        # If not JSON, use raw output
                        formatted_output = output
                else:
                    formatted_output = f"Command failed:\n{output}"
                
                # Create detailed observation
                observation = f"Observation:\n{formatted_output}"
                
                # Display and store observation
                self._display_observation(observation)
                conversation_entry['observations'].append(observation)
                
                # Update context with new information
 #               self._update_context(output, success)
                
                observations.append(observation)

            # Update the prompt for next iteration with all observations
            # current_prompt = "\n\n".join(observations)

            iteration += 1

            # Store conversation entry
            self.conversation_history.append(conversation_entry)
        
        return final_answer or "I apologize, but I was unable to reach a conclusive answer within the allowed iterations."
