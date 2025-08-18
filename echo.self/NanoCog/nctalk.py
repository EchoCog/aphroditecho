#!/usr/bin/env python3
"""
NanoCog CLI Chat (nctalk.py)

An interactive command-line interface for chatting with a CogPrime-trained nanoGPT model.
Features include:
- Colorful interactive REPL 
- Normal chat and diagnostic modes
- Streaming responses with typing indicator
- Conversation history management
- Special commands (/help, /diagnostic, /reset, etc.)
- Example prompts for CogPrime exploration
"""

import os
import sys
import json
import time
import random
import argparse
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from contextlib import nullcontext

import torch
import tiktoken
import numpy as np

# Add the parent directory to sys.path to import nanoGPT modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model import GPTConfig, GPT

# Import rich for nice terminal formatting
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich library not found. Install with 'pip install rich' for better formatting.")

# --- Constants ---
NANOCOG_VERSION = "0.1.0"
DEFAULT_MAX_TOKENS = 500
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_K = 200
DEFAULT_HISTORY_SIZE = 20
EXAMPLE_PROMPTS = [
    "Explain the concept of Cognitive Synergy in the CogPrime architecture.",
    "What are the key differences between PLN and traditional logic systems?",
    "How does ECAN allocate attention in a CogPrime system?",
    "Explain the Glocal Memory principle and its advantages.",
    "Write a simple Scheme function to count the incoming links of a node.",
    "What are the main components of the AtomSpace and how do they interact?",
    "How does MOSES learn procedural knowledge in CogPrime?",
    "Explain the relationship between goals and cognitive schematics.",
    "What challenges might arise when implementing a CogPrime system?",
    "How does the 'Cognitive Equation' concept relate to pattern mining?"
]

DIAGNOSTIC_FOCUS_AREAS = [
    "attention allocation",
    "goal management",
    "pattern formation",
    "cognitive synergy",
    "procedural learning",
    "inference bottlenecks",
    "memory utilization",
    "sensory processing"
]

HELP_TEXT = """
NanoCog CLI Commands:
/help               - Show this help message
/exit, /quit        - Exit the program
/reset              - Reset the conversation history
/clear              - Clear the screen
/save <filename>    - Save conversation history to a file
/load <filename>    - Load conversation history from a file
/examples           - Show example prompts
/example <number>   - Use a specific example prompt
/diagnostic         - Enter diagnostic mode (requires AtomSpace endpoint)
/normal             - Return to normal chat mode
/info               - Show model information
/settings           - Show current settings
/set <param> <value> - Change a setting (temperature, max_tokens, top_k)
/history            - Show conversation history
/scheme             - Format next input as Scheme code

In diagnostic mode:
/connect <endpoint> - Connect to an AtomSpace endpoint
/focus <areas>      - Set focus areas for diagnostics (comma-separated)
/analyze            - Run a full diagnostic analysis
"""

# --- Model Configuration ---
class ModelConfig:
    """Configuration for the nanoGPT model."""
    def __init__(self, model_path: str, device: str = "cuda", max_tokens: int = 2048):
        """
        Initializes the ModelConfig with model path, device, and maximum token settings.
        
        Args:
            model_path: Path to the nanoGPT model checkpoint.
            device: Device identifier for model inference (e.g., "cuda" or "cpu").
            max_tokens: Maximum number of tokens for model input and generation.
        """
        self.model_path = model_path
        self.device = device
        self.max_tokens = max_tokens
        self.model = None
        self.tokenizer = None
        self.model_info = {}

    def load_model(self):
        """
        Loads the nanoGPT model checkpoint, initializes the model and tokenizer, and prepares the model for inference.
        
        Returns:
            True if the model is loaded successfully.
        
        Raises:
            RuntimeError: If loading the model or tokenizer fails.
        """
        try:
            print(f"Loading model from {self.model_path}...")
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Store model info
            self.model_info = {
                "model_args": checkpoint.get('model_args', {}),
                "config": checkpoint.get('config', {}),
                "iter_num": checkpoint.get('iter_num', 0),
                "best_val_loss": checkpoint.get('best_val_loss', float('inf')),
                "checkpoint_path": self.model_path
            }
            
            # Configure model from checkpoint
            gptconf = GPTConfig(**checkpoint['model_args'])
            self.model = GPT(gptconf)
            
            # Handle potential prefix in state dict keys
            state_dict = checkpoint['model']
            unwanted_prefix = '_orig_mod.'
            for k, v in list(state_dict.items()):
                if k.startswith(unwanted_prefix):
                    state_dict[k[len(unwanted_prefix):]] = state_dict.pop(k)
            
            self.model.load_state_dict(state_dict)
            self.model.eval()
            self.model.to(self.device)
            
            # Set up tokenizer
            self.tokenizer = tiktoken.get_encoding("gpt2")
            
            print("Model loaded successfully!")
            return True
        except Exception as e:
            print(f"Failed to load model: {str(e)}")
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def generate(self, prompt: str, max_new_tokens: int = 500, 
                 temperature: float = 0.7, top_k: int = 200,
                 callback = None):
        """
                 Generates text from the model based on the provided prompt.
                 
                 Args:
                     prompt: The input text to condition the model's generation.
                     max_new_tokens: Maximum number of tokens to generate in the response.
                     temperature: Controls randomness in sampling; higher values yield more diverse outputs.
                     top_k: Limits sampling to the top k most probable tokens at each step.
                     callback: Optional function to receive tokens as they are generated for streaming output.
                 
                 Returns:
                     The generated text as a string, or streams tokens via the callback if provided.
                 
                 Raises:
                     RuntimeError: If the model or tokenizer is not loaded.
                 """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Encode the prompt
        input_ids = self.tokenizer.encode(prompt, allowed_special={"<|endoftext|>"})
        
        # Truncate if needed to fit within context window
        if len(input_ids) > self.max_tokens - max_new_tokens:
            print(f"Warning: Prompt too long ({len(input_ids)} tokens), truncating")
            input_ids = input_ids[-(self.max_tokens - max_new_tokens):]
        
        # Convert to tensor
        x = torch.tensor(input_ids, dtype=torch.long, device=self.device)[None, ...]
        
        if callback:
            return self._stream_generate(x, max_new_tokens, temperature, top_k, callback)
        else:
            return self._batch_generate(x, max_new_tokens, temperature, top_k)
    
    def _batch_generate(self, x, max_new_tokens, temperature, top_k):
        """
        Generates text from the model in a single batch and returns the decoded output.
        
        Args:
            x: Input tensor containing tokenized prompt.
            max_new_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature for generation.
            top_k: Limits sampling to the top_k most probable tokens.
        
        Returns:
            The generated text as a string, excluding the original prompt.
        """
        with torch.no_grad():
            with torch.amp.autocast(device_type='cuda' if 'cuda' in self.device else 'cpu'):
                y = self.model.generate(
                    x, max_new_tokens, temperature=temperature, top_k=top_k
                )
                generated_text = self.tokenizer.decode(y[0].tolist())
                # Remove the prompt from the generated text
                prompt_text = self.tokenizer.decode(x[0].tolist())
                if generated_text.startswith(prompt_text):
                    generated_text = generated_text[len(prompt_text):]
                return generated_text
    
    def _stream_generate(self, x, max_new_tokens, temperature, top_k, callback):
        """
        Generates text one token at a time, invoking a callback with each new token.
        
        Args:
            x: Input tensor containing tokenized prompt.
            max_new_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature for controlling randomness.
            top_k: Limits sampling to the top_k most probable tokens.
            callback: Function called with each generated token; if it returns False, generation stops early.
        
        Returns:
            The concatenated string of all generated tokens.
        """
        generated_tokens = []
        
        with torch.no_grad():
            with torch.amp.autocast(device_type='cuda' if 'cuda' in self.device else 'cpu'):
                # Get the input sequence length to know where to start yielding new tokens
                input_len = x.shape[1]
                
                # Initialize past_key_values for more efficient generation
                past = None
                for token_index in range(max_new_tokens):
                    # Forward pass
                    if past is None:
                        # First forward pass with the full input
                        outputs = self.model(x, use_cache=True)
                        logits = outputs.logits
                        past = outputs.past_key_values
                    else:
                        # Subsequent passes with just the new token and cached past
                        outputs = self.model(
                            x[:, -1:], use_cache=True, past_key_values=past
                        )
                        logits = outputs.logits
                        past = outputs.past_key_values
                    
                    # Get logits for the next token and sample
                    next_token_logits = logits[:, -1, :]
                    
                    # Apply temperature
                    if temperature > 0:
                        next_token_logits = next_token_logits / temperature
                    
                    # Apply top-k filtering
                    if top_k > 0:
                        v, _ = torch.topk(next_token_logits, min(top_k, next_token_logits.size(-1)))
                        next_token_logits[next_token_logits < v[:, [-1]]] = float('-inf')
                    
                    # Sample from the filtered distribution
                    probs = torch.nn.functional.softmax(next_token_logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)
                    
                    # Append the new token to the input
                    x = torch.cat((x, next_token), dim=1)
                    
                    # Decode the new token
                    new_token_text = self.tokenizer.decode([next_token[0].item()])
                    generated_tokens.append(new_token_text)
                    
                    # Call the callback with the new token
                    if callback:
                        should_continue = callback(new_token_text)
                        if not should_continue:
                            break
                    
                    # Check if we've hit the end of text token
                    if next_token[0].item() == self.tokenizer.eot_token:
                        break
        
        # Return the full generated text
        return ''.join(generated_tokens)

# --- Conversation History ---
class ConversationHistory:
    """Manages the conversation history."""
    
    def __init__(self, max_history: int = DEFAULT_HISTORY_SIZE):
        """
        Initializes a new conversation history manager.
        
        Args:
            max_history: The maximum number of messages to retain in the conversation history.
        """
        self.messages = []
        self.max_history = max_history
    
    def add_message(self, role: str, content: str):
        """
        Appends a message with role and content to the conversation history.
        
        If the total number of messages exceeds the maximum history size, the oldest messages are removed to maintain the limit.
        
        Args:
            role: The sender's role, such as "user", "assistant", or "system".
            content: The message text to add.
        """
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim history if needed
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def clear(self):
        """
        Removes all messages from the conversation history.
        """
        self.messages = []
    
    def get_messages(self):
        """
        Returns all messages currently stored in the conversation history.
        """
        return self.messages
    
    def format_for_prompt(self):
        """
        Formats the conversation history into a prompt string suitable for model input.
        
        Returns:
            A string containing all messages with role-based prefixes, ending with an assistant prompt to elicit a response from the model.
        """
        prompt = ""
        for message in self.messages:
            role = message["role"].lower()
            content = message["content"]
            
            if role == "user":
                prompt += f"\nUser: {content}\n"
            elif role == "assistant":
                prompt += f"\nNanoCog: {content}\n"
            elif role == "system":
                # System messages are prepended with a special format
                prompt += f"\n# System Instruction: {content}\n"
        
        # Add the final assistant prefix to prompt the model to respond
        prompt += "\nNanoCog: "
        return prompt
    
    def save_to_file(self, filename: str):
        """
        Saves the conversation history to a JSON file with version and timestamp metadata.
        
        Args:
            filename: Path to the file where the conversation history will be saved.
        
        Returns:
            True if the conversation history was saved successfully, False otherwise.
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "version": NANOCOG_VERSION,
                    "timestamp": datetime.now().isoformat(),
                    "messages": self.messages
                }, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving conversation: {str(e)}")
            return False
    
    def load_from_file(self, filename: str):
        """
        Loads conversation history from a JSON file.
        
        Args:
            filename: Path to the JSON file containing conversation history.
        
        Returns:
            True if the conversation history was loaded successfully; False otherwise.
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "messages" in data:
                    self.messages = data["messages"]
                    return True
                else:
                    print("Error: Invalid conversation file format")
                    return False
        except Exception as e:
            print(f"Error loading conversation: {str(e)}")
            return False

# --- Diagnostic Mode ---
class DiagnosticMode:
    """Handles diagnostic mode functionality."""
    
    def __init__(self):
        """
        Initializes the DiagnosticMode instance with default focus areas and disconnected state.
        """
        self.atomspace_endpoint = None
        self.focus_areas = ["attention", "goals", "patterns", "cognitive synergy"]
        self.connected = False
    
    def connect(self, endpoint: str) -> bool:
        """
        Attempts to establish a connection to the specified AtomSpace REST API endpoint.
        
        Args:
            endpoint: The URL of the AtomSpace REST API.
        
        Returns:
            True if the connection is successful; False otherwise.
        """
        try:
            import requests
            response = requests.get(f"{endpoint}/status", timeout=5)
            response.raise_for_status()
            self.atomspace_endpoint = endpoint
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to AtomSpace at {endpoint}: {str(e)}")
            self.connected = False
            return False
    
    def get_introspection_data(self) -> Dict[str, Any]:
        """
        Retrieves mock introspection data simulating the current state of the AtomSpace.
        
        Returns:
            A dictionary containing simulated AtomSpace metrics such as atom count, active goals,
            attention summary, high STI atoms, and performance statistics. Returns an empty
            dictionary if not connected or if an error occurs.
        """
        if not self.connected or not self.atomspace_endpoint:
            return {}
        
        try:
            import requests
            
            # This is a mock implementation - in a real system, you would query
            # the actual AtomSpace REST API endpoints
            
            # For demo purposes, generate some mock data
            atom_count = random.randint(1000, 10000)
            
            # Mock active goals
            active_goals = []
            for i in range(random.randint(3, 8)):
                active_goals.append({
                    "name": f"Goal{i+1}",
                    "type": "ConceptNode",
                    "sti": random.uniform(0.5, 0.95),
                    "lti": random.uniform(0.1, 0.5),
                    "tv": [random.uniform(0.7, 0.99), random.uniform(0.6, 0.9)]
                })
            
            # Mock attention summary
            attention_summary = {
                "avg_sti": random.uniform(0.1, 0.3),
                "max_sti": random.uniform(0.8, 0.99),
                "sti_distribution": {
                    "high": random.randint(50, 200),
                    "medium": random.randint(200, 1000),
                    "low": random.randint(1000, 5000)
                },
                "atoms_with_zero_sti": random.randint(500, 2000)
            }
            
            # Mock high STI atoms
            high_sti_atoms = []
            atom_types = ["ConceptNode", "PredicateNode", "ListLink", "EvaluationLink", 
                         "HebbianLink", "InheritanceLink", "SchemaNode"]
            for i in range(random.randint(10, 30)):
                high_sti_atoms.append({
                    "handle": f"0x{random.randint(1000, 9999):x}",
                    "type": random.choice(atom_types),
                    "name": f"Atom{i+1}",
                    "sti": random.uniform(0.7, 0.99),
                    "lti": random.uniform(0.3, 0.8),
                    "incoming_count": random.randint(0, 50)
                })
            
            return {
                "timestamp": datetime.now().isoformat(),
                "atom_count": atom_count,
                "active_goals": active_goals,
                "attention_summary": attention_summary,
                "high_sti_atoms": high_sti_atoms,
                "cognitive_cycles_per_second": random.uniform(5, 50),
                "inference_steps_since_start": random.randint(1000, 100000),
                "moses_evaluations": random.randint(100, 5000),
                "pln_inference_count": random.randint(500, 10000)
            }
        except Exception as e:
            print(f"Error getting introspection data: {str(e)}")
            return {}
    
    def format_diagnostic_prompt(self, introspection_data: Dict[str, Any]) -> str:
        """
        Formats AtomSpace introspection data into a structured prompt for diagnostic analysis.
        
        Args:
            introspection_data: Dictionary containing AtomSpace state, including atom counts, goals, attention summaries, and high STI atoms.
        
        Returns:
            A formatted prompt string instructing the model to analyze the provided AtomSpace data, summarize cognitive state, identify issues, and suggest optimizations based on CogPrime principles.
        """
        # Create a summary of the data for the prompt
        summary = []
        
        # Add atom count
        summary.append(f"Total atoms: {introspection_data.get('atom_count', 'unknown')}")
        
        # Add active goals if available
        if 'active_goals' in introspection_data and introspection_data['active_goals']:
            summary.append(f"Active goals: {len(introspection_data['active_goals'])}")
            for i, goal in enumerate(introspection_data['active_goals'][:5]):  # Show top 5
                goal_name = goal.get('name', 'Unnamed')
                goal_sti = goal.get('sti', 0.0)
                summary.append(f"  Goal {i+1}: {goal_name} (STI: {goal_sti:.2f})")
        
        # Add attention summary if available
        if 'attention_summary' in introspection_data:
            att_summary = introspection_data['attention_summary']
            if isinstance(att_summary, dict):
                summary.append("Attention allocation:")
                for key, value in att_summary.items():
                    if isinstance(value, (int, float)):
                        summary.append(f"  {key}: {value}")
        
        # Add high STI atoms if available
        if 'high_sti_atoms' in introspection_data:
            high_sti = introspection_data['high_sti_atoms']
            summary.append(f"High STI atoms: {len(high_sti)}")
            atom_types = {}
            for atom in high_sti:
                atom_type = atom.get('type', 'unknown')
                atom_types[atom_type] = atom_types.get(atom_type, 0) + 1
            for atom_type, count in atom_types.items():
                summary.append(f"  {atom_type}: {count}")
        
        # Create the prompt
        prompt = f"""# System Instruction: You are NanoCog, an AI assistant specialized in CogPrime architecture and OpenCog systems. You're analyzing a live CogPrime agent's AtomSpace. Provide detailed introspective diagnostics based on the data below, focusing on: {', '.join(self.focus_areas)}.

## AtomSpace Data ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
{chr(10).join(summary)}

## Raw Data (JSON)
```json
{json.dumps(introspection_data, indent=2)}
```

## Task
Analyze the above AtomSpace data and provide:
1. A summary of the agent's current cognitive state
2. Identification of any bottlenecks or issues
3. Specific recommendations for optimization
4. Relevant CogPrime principles that apply

NanoCog (Diagnostic Analysis): 
"""
        return prompt

# --- CLI Interface ---
class NanoCogCLI:
    """Command-line interface for NanoCog."""
    
    def __init__(self, model_config: ModelConfig):
        """
        Initializes the NanoCogCLI with model configuration, conversation history, diagnostic mode, and default settings.
        
        Adds a system message describing NanoCog's role as an AI assistant specialized in CogPrime and OpenCog.
        """
        self.model_config = model_config
        self.history = ConversationHistory()
        self.diagnostic_mode = DiagnosticMode()
        self.is_diagnostic_mode = False
        self.settings = {
            "max_tokens": DEFAULT_MAX_TOKENS,
            "temperature": DEFAULT_TEMPERATURE,
            "top_k": DEFAULT_TOP_K
        }
        
        # Set up rich console if available
        self.console = Console() if RICH_AVAILABLE else None
        
        # Add a system message to the history
        self.history.add_message("system", 
            "You are NanoCog, an AI assistant specialized in CogPrime architecture and OpenCog systems. "
            "You provide accurate, helpful information about AGI concepts, CogPrime components, and "
            "OpenCog implementation details. You can also generate Scheme code for OpenCog when requested."
        )
    
    def print_welcome(self):
        """
        Displays the NanoCog welcome message with usage instructions, using enhanced formatting if available.
        """
        if RICH_AVAILABLE:
            self.console.print(Panel.fit(
                "[bold blue]NanoCog[/bold blue] [green]v" + NANOCOG_VERSION + "[/green]\n"
                "A CogPrime-aware AI assistant based on nanoGPT\n\n"
                "Type [bold yellow]/help[/bold yellow] for commands or [bold yellow]/examples[/bold yellow] for example prompts.\n"
                "Type [bold yellow]/exit[/bold yellow] to quit.",
                title="Welcome to NanoCog",
                border_style="blue"
            ))
        else:
            print("=" * 60)
            print(f"NanoCog v{NANOCOG_VERSION}")
            print("A CogPrime-aware AI assistant based on nanoGPT")
            print("=" * 60)
            print("Type /help for commands or /examples for example prompts.")
            print("Type /exit to quit.")
            print("-" * 60)
    
    def print_message(self, role: str, content: str):
        """
        Displays a message with formatting based on the sender's role.
        
        Args:
            role: The sender's role, such as 'user', 'assistant', 'system', 'error', or 'info'.
            content: The message content to display.
        """
        if RICH_AVAILABLE:
            if role.lower() == "user":
                self.console.print(f"[bold green]User:[/bold green]", end=" ")
                self.console.print(content)
            elif role.lower() == "assistant":
                self.console.print(f"[bold blue]NanoCog:[/bold blue]", end=" ")
                # Check if content has code blocks and render as markdown if so
                if "```" in content:
                    self.console.print(Markdown(content))
                else:
                    self.console.print(content)
            elif role.lower() == "system":
                self.console.print(f"[bold yellow]System:[/bold yellow] {content}")
            elif role.lower() == "error":
                self.console.print(f"[bold red]Error:[/bold red] {content}")
            elif role.lower() == "info":
                self.console.print(f"[bold cyan]Info:[/bold cyan] {content}")
        else:
            if role.lower() == "user":
                print(f"User: {content}")
            elif role.lower() == "assistant":
                print(f"NanoCog: {content}")
            elif role.lower() == "system":
                print(f"System: {content}")
            elif role.lower() == "error":
                print(f"Error: {content}")
            elif role.lower() == "info":
                print(f"Info: {content}")
    
    def handle_command(self, command: str) -> bool:
        """
        Parses and executes a CLI command entered by the user.
        
        Handles built-in commands for help, exit, conversation management, example prompts, diagnostic mode operations, model information, settings, and Scheme code input. Returns True if the command was recognized and processed; returns False if the input should be treated as a regular user message.
        """
        cmd_parts = command.strip().split(maxsplit=1)
        cmd = cmd_parts[0].lower()
        args = cmd_parts[1] if len(cmd_parts) > 1 else ""
        
        if cmd == "/help":
            if RICH_AVAILABLE:
                self.console.print(Markdown(HELP_TEXT))
            else:
                print(HELP_TEXT)
            return True
        
        elif cmd in ["/exit", "/quit"]:
            if RICH_AVAILABLE:
                self.console.print("[bold yellow]Goodbye![/bold yellow]")
            else:
                print("Goodbye!")
            sys.exit(0)
        
        elif cmd == "/reset":
            self.history.clear()
            # Add the system message back
            self.history.add_message("system", 
                "You are NanoCog, an AI assistant specialized in CogPrime architecture and OpenCog systems. "
                "You provide accurate, helpful information about AGI concepts, CogPrime components, and "
                "OpenCog implementation details. You can also generate Scheme code for OpenCog when requested."
            )
            self.print_message("system", "Conversation history has been reset.")
            return True
        
        elif cmd == "/clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_welcome()
            return True
        
        elif cmd == "/save":
            if not args:
                self.print_message("error", "Please specify a filename.")
                return True
            
            filename = args
            if not filename.endswith(".json"):
                filename += ".json"
            
            if self.history.save_to_file(filename):
                self.print_message("system", f"Conversation saved to {filename}")
            else:
                self.print_message("error", f"Failed to save conversation to {filename}")
            return True
        
        elif cmd == "/load":
            if not args:
                self.print_message("error", "Please specify a filename.")
                return True
            
            filename = args
            if not filename.endswith(".json"):
                filename += ".json"
            
            if self.history.load_from_file(filename):
                self.print_message("system", f"Conversation loaded from {filename}")
            else:
                self.print_message("error", f"Failed to load conversation from {filename}")
            return True
        
        elif cmd == "/examples":
            if RICH_AVAILABLE:
                table = Table(title="Example Prompts", box=box.ROUNDED)
                table.add_column("#", style="cyan")
                table.add_column("Prompt", style="green")
                
                for i, prompt in enumerate(EXAMPLE_PROMPTS, 1):
                    table.add_row(str(i), prompt)
                
                self.console.print(table)
                self.console.print("Use [bold yellow]/example <number>[/bold yellow] to use a specific example.")
            else:
                print("\nExample Prompts:")
                for i, prompt in enumerate(EXAMPLE_PROMPTS, 1):
                    print(f"{i}. {prompt}")
                print("\nUse /example <number> to use a specific example.")
            return True
        
        elif cmd == "/example":
            try:
                idx = int(args) - 1
                if 0 <= idx < len(EXAMPLE_PROMPTS):
                    prompt = EXAMPLE_PROMPTS[idx]
                    self.print_message("user", prompt)
                    self.history.add_message("user", prompt)
                    self.generate_response()
                else:
                    self.print_message("error", f"Example number must be between 1 and {len(EXAMPLE_PROMPTS)}")
            except ValueError:
                self.print_message("error", "Please specify a valid example number.")
            return True
        
        elif cmd == "/diagnostic":
            self.is_diagnostic_mode = True
            self.print_message("system", "Entering diagnostic mode. Use /connect <endpoint> to connect to an AtomSpace.")
            return True
        
        elif cmd == "/normal":
            self.is_diagnostic_mode = False
            self.print_message("system", "Returning to normal chat mode.")
            return True
        
        elif cmd == "/connect" and self.is_diagnostic_mode:
            if not args:
                self.print_message("error", "Please specify an endpoint URL.")
                return True
            
            endpoint = args
            if self.diagnostic_mode.connect(endpoint):
                self.print_message("system", f"Connected to AtomSpace at {endpoint}")
            else:
                self.print_message("error", f"Failed to connect to AtomSpace at {endpoint}")
            return True
        
        elif cmd == "/focus" and self.is_diagnostic_mode:
            if not args:
                self.print_message("error", "Please specify focus areas (comma-separated).")
                return True
            
            focus_areas = [area.strip() for area in args.split(",")]
            self.diagnostic_mode.focus_areas = focus_areas
            self.print_message("system", f"Focus areas set to: {', '.join(focus_areas)}")
            return True
        
        elif cmd == "/analyze" and self.is_diagnostic_mode:
            if not self.diagnostic_mode.connected:
                self.print_message("error", "Not connected to an AtomSpace. Use /connect <endpoint> first.")
                return True
            
            self.print_message("system", "Running diagnostic analysis...")
            self.run_diagnostic_analysis()
            return True
        
        elif cmd == "/info":
            self.show_model_info()
            return True
        
        elif cmd == "/settings":
            self.show_settings()
            return True
        
        elif cmd == "/set":
            if not args:
                self.print_message("error", "Please specify a parameter and value.")
                return True
            
            parts = args.split(maxsplit=1)
            if len(parts) != 2:
                self.print_message("error", "Please specify both a parameter and value.")
                return True
            
            param, value = parts
            self.update_setting(param, value)
            return True
        
        elif cmd == "/history":
            self.show_history()
            return True
        
        elif cmd == "/scheme":
            self.print_message("system", "Next input will be formatted as Scheme code. Type your code now:")
            user_input = input("> ")
            formatted_input = f"```scheme\n{user_input}\n```\nPlease explain this Scheme code and how it works in OpenCog."
            self.print_message("user", formatted_input)
            self.history.add_message("user", formatted_input)
            self.generate_response()
            return True
        
        return False
    
    def update_setting(self, param: str, value: str):
        """
        Updates a generation parameter with a new value.
        
        Args:
            param: The name of the parameter to update ("temperature", "max_tokens", or "top_k").
            value: The new value to assign to the parameter.
        
        If the parameter name is unrecognized or the value is invalid, an error message is displayed.
        """
        try:
            if param == "temperature":
                self.settings["temperature"] = float(value)
                self.print_message("system", f"Temperature set to {float(value)}")
            elif param == "max_tokens":
                self.settings["max_tokens"] = int(value)
                self.print_message("system", f"Max tokens set to {int(value)}")
            elif param == "top_k":
                self.settings["top_k"] = int(value)
                self.print_message("system", f"Top-k set to {int(value)}")
            else:
                self.print_message("error", f"Unknown parameter: {param}")
        except ValueError:
            self.print_message("error", f"Invalid value for {param}: {value}")
    
    def show_settings(self):
        """
        Displays the current generation settings for the CLI session.
        
        Shows all configurable parameters and their values, using a formatted table if rich output is available.
        """
        if RICH_AVAILABLE:
            table = Table(title="Current Settings", box=box.ROUNDED)
            table.add_column("Parameter", style="cyan")
            table.add_column("Value", style="green")
            
            for param, value in self.settings.items():
                table.add_row(param, str(value))
            
            self.console.print(table)
        else:
            print("\nCurrent Settings:")
            for param, value in self.settings.items():
                print(f"{param}: {value}")
    
    def show_model_info(self):
        """
        Displays detailed information about the currently loaded model, including architecture parameters and training metadata. If model information is unavailable, notifies the user.
        """
        if not self.model_config.model_info:
            self.print_message("error", "Model information not available.")
            return
        
        if RICH_AVAILABLE:
            table = Table(title="Model Information", box=box.ROUNDED)
            table.add_column("Parameter", style="cyan")
            table.add_column("Value", style="green")
            
            # Add model architecture info
            model_args = self.model_config.model_info.get("model_args", {})
            for param, value in model_args.items():
                table.add_row(param, str(value))
            
            # Add training info
            table.add_row("Training Iterations", str(self.model_config.model_info.get("iter_num", "Unknown")))
            table.add_row("Best Validation Loss", str(self.model_config.model_info.get("best_val_loss", "Unknown")))
            table.add_row("Checkpoint Path", self.model_config.model_info.get("checkpoint_path", "Unknown"))
            
            self.console.print(table)
        else:
            print("\nModel Information:")
            print("Model Architecture:")
            for param, value in self.model_config.model_info.get("model_args", {}).items():
                print(f"  {param}: {value}")
            
            print("\nTraining Information:")
            print(f"  Training Iterations: {self.model_config.model_info.get('iter_num', 'Unknown')}")
            print(f"  Best Validation Loss: {self.model_config.model_info.get('best_val_loss', 'Unknown')}")
            print(f"  Checkpoint Path: {self.model_config.model_info.get('checkpoint_path', 'Unknown')}")
    
    def show_history(self):
        """
        Displays the conversation history in a formatted table or plain text.
        
        If conversation history exists, shows each message with its role and truncated content.
        Uses rich formatting if available; otherwise, prints to standard output.
        """
        messages = self.history.get_messages()
        
        if not messages:
            self.print_message("system", "No conversation history.")
            return
        
        if RICH_AVAILABLE:
            table = Table(title="Conversation History", box=box.ROUNDED)
            table.add_column("#", style="cyan")
            table.add_column("Role", style="green")
            table.add_column("Content")
            
            for i, message in enumerate(messages):
                role = message["role"]
                content = message["content"]
                # Truncate long messages for display
                if len(content) > 100:
                    content = content[:97] + "..."
                
                table.add_row(str(i+1), role, content)
            
            self.console.print(table)
        else:
            print("\nConversation History:")
            for i, message in enumerate(messages):
                role = message["role"]
                content = message["content"]
                # Truncate long messages for display
                if len(content) > 100:
                    content = content[:97] + "..."
                
                print(f"{i+1}. {role}: {content}")
    
    def generate_response(self):
        """
        Generates and streams a model response based on the current conversation history.
        
        Retrieves the formatted conversation prompt, streams the model's generated response token by token to the terminal, and appends the assistant's reply to the conversation history. Returns the generated response text, or None if an error occurs.
        """
        try:
            prompt = self.history.format_for_prompt()
            
            # Set up streaming callback
            def streaming_callback(token):
                # Print the token without a newline
                """
                Handles streaming output of a generated token during model inference.
                
                Prints the provided token to the console without a newline, using rich formatting if available. Returns True to indicate continuation of streaming.
                """
                if RICH_AVAILABLE:
                    self.console.print(token, end="")
                else:
                    print(token, end="", flush=True)
                return True
            
            # Show a spinner while generating (if using rich)
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Thinking...[/bold blue]"),
                    transient=True
                ) as progress:
                    progress.add_task("Generating...", total=None)
                    # Small delay to show the spinner
                    time.sleep(0.5)
            
            # Generate the response with streaming
            response = self.model_config.generate(
                prompt=prompt,
                max_new_tokens=self.settings["max_tokens"],
                temperature=self.settings["temperature"],
                top_k=self.settings["top_k"],
                callback=streaming_callback
            )
            
            # Print a newline after streaming
            print()
            
            # Add the response to the history
            self.history.add_message("assistant", response)
            
            return response
        except Exception as e:
            self.print_message("error", f"Error generating response: {str(e)}")
            return None
    
    def run_diagnostic_analysis(self):
        """
        Performs a diagnostic analysis of the connected AtomSpace and streams the model's response.
        
        Retrieves introspection data from the AtomSpace, formats it into a diagnostic prompt, and generates an analysis using the model with streaming output. The analysis and corresponding user request are added to the conversation history. Returns the generated analysis text, or None if an error occurs.
        """
        try:
            # Get introspection data
            introspection_data = self.diagnostic_mode.get_introspection_data()
            
            if not introspection_data:
                self.print_message("error", "Failed to get introspection data.")
                return
            
            # Format the diagnostic prompt
            prompt = self.diagnostic_mode.format_diagnostic_prompt(introspection_data)
            
            # Set up streaming callback
            def streaming_callback(token):
                # Print the token without a newline
                """
                Handles streaming output of a generated token during model inference.
                
                Prints the provided token to the console without a newline, using rich formatting if available. Returns True to indicate continuation of streaming.
                """
                if RICH_AVAILABLE:
                    self.console.print(token, end="")
                else:
                    print(token, end="", flush=True)
                return True
            
            # Show a spinner while generating (if using rich)
            if RICH_AVAILABLE:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Analyzing AtomSpace...[/bold blue]"),
                    transient=True
                ) as progress:
                    progress.add_task("Analyzing...", total=None)
                    # Small delay to show the spinner
                    time.sleep(0.5)
            
            # Generate the diagnostic analysis with streaming
            analysis = self.model_config.generate(
                prompt=prompt,
                max_new_tokens=1000,  # Longer for diagnostics
                temperature=0.6,  # Lower temperature for more focused analysis
                top_k=50,  # Lower top_k for more focused analysis
                callback=streaming_callback
            )
            
            # Print a newline after streaming
            print()
            
            # Add the analysis to the history
            self.history.add_message("user", "Run a diagnostic analysis on my CogPrime agent.")
            self.history.add_message("assistant", analysis)
            
            return analysis
        except Exception as e:
            self.print_message("error", f"Error running diagnostic analysis: {str(e)}")
            return None
    
    def run(self):
        """
        Starts the interactive command-line interface loop for chatting with the model.
        
        Continuously prompts the user for input, processes commands or messages, manages conversation history, and generates model responses. Handles keyboard interrupts for graceful exit and displays error messages on exceptions.
        """
        self.print_welcome()
        
        while True:
            try:
                # Get user input
                if RICH_AVAILABLE:
                    user_input = Prompt.ask("[bold green]User[/bold green]")
                else:
                    user_input = input("User: ")
                
                # Check if it's a command
                if user_input.startswith("/"):
                    if self.handle_command(user_input):
                        continue
                
                # Add the user message to the history
                self.history.add_message("user", user_input)
                
                # Generate and print the response
                self.generate_response()
                
            except KeyboardInterrupt:
                print("\n")
                if RICH_AVAILABLE:
                    if Confirm.ask("[bold yellow]Do you want to exit?[/bold yellow]"):
                        self.print_message("system", "Goodbye!")
                        break
                    else:
                        continue
                else:
                    print("Interrupted. Type /exit to quit.")
            except Exception as e:
                self.print_message("error", f"An error occurred: {str(e)}")

# --- Main Function ---
def main():
    """
    Parses command-line arguments, loads the nanoGPT model, and starts the NanoCog interactive CLI.
    
    This function initializes the model configuration with user-specified parameters, loads the model checkpoint, and launches the NanoCog command-line interface for interactive chatting and diagnostics. Exits with an error message if the model fails to load.
    """
    parser = argparse.ArgumentParser(description="NanoCog CLI")
    parser.add_argument("--model_path", type=str, required=True, 
                        help="Path to the model checkpoint")
    parser.add_argument("--device", type=str, 
                        default="cuda" if torch.cuda.is_available() else "cpu",
                        help="Device to run the model on (cuda, cpu, mps)")
    parser.add_argument("--max_tokens", type=int, default=DEFAULT_MAX_TOKENS,
                        help="Maximum number of tokens to generate")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE,
                        help="Sampling temperature")
    parser.add_argument("--top_k", type=int, default=DEFAULT_TOP_K,
                        help="Top-k sampling parameter")
    
    args = parser.parse_args()
    
    # Create model config
    model_config = ModelConfig(
        model_path=args.model_path,
        device=args.device,
        max_tokens=2048  # Context window size
    )
    
    # Load the model
    try:
        model_config.load_model()
    except Exception as e:
        print(f"Failed to load model: {str(e)}")
        sys.exit(1)
    
    # Create and run the CLI
    cli = NanoCogCLI(model_config)
    cli.settings["max_tokens"] = args.max_tokens
    cli.settings["temperature"] = args.temperature
    cli.settings["top_k"] = args.top_k
    
    cli.run()

if __name__ == "__main__":
    main()
