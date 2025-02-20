import asyncio
import typer
from rich.console import Console
from rich.prompt import Prompt
from agent.react import ReactAgent

app = typer.Typer()
console = Console()

@app.command()
def main():
    """
    Interactive CLI for cloud environment diagnosis
    """
    console.print("[bold blue]Cloud Environment Diagnosis Agent[/bold blue]")
    console.print("Type 'exit' to quit\n")
    
    # Initialize agent
    agent = ReactAgent()
    
    async def run_agent():
        while True:
            # Get user input
            query = Prompt.ask("\n[bold green]What would you like to know about your cloud environment?[/bold green]")
            
            if query.lower() == 'exit':
                console.print("\n[bold blue]Goodbye![/bold blue]")
                break
                
            try:
                # Process query through agent
                await agent.process_query(query)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")

        
    # Run the async loop
    asyncio.run(run_agent())

if __name__ == "__main__":
    app()
