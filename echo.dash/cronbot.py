import json
import base64
import os
import time
from datetime import datetime
import logging
import psutil
import threading
from queue import Queue

NOTE_FILE = "note2self.json"

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def read_note():
    try:
        with open(NOTE_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # Create a new note if the file is not found
        new_note = {"timestamp": None, "improvement": {}, "assessment": ""}
        write_note(new_note)
        return new_note
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from note file: {e}")
        return {"timestamp": None, "improvement": {}, "assessment": ""}

def write_note(note):
    with open(NOTE_FILE, 'w') as file:
        json.dump(note, file, indent=2)

def load_ai_introspection_data():
    """Load AI introspection data if available"""
    try:
        with open('ai_introspection_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.info("No AI introspection data available")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode AI introspection data: {e}")
        return None

def call_github_copilot(note, introspection_data=None):
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        logger.error("Error: GITHUB_TOKEN environment variable is missing.")
        return None

    # Enhanced query with introspection context
    base_query = "This is a summary of last cycle events. Please can you help me take a look at the repo so we can identify an item for the next incremental improvement?"
    
    if introspection_data and introspection_data.get('introspection_status') == 'success':
        files_analyzed = introspection_data.get('files_analyzed', 0)
        highest_salience = introspection_data.get('highest_salience_files', [])
        salience_summary = ', '.join([f[0] for f in highest_salience[:3]])
        
        enhanced_query = f"{base_query}\n\nAI Introspection Context:\n- Files analyzed: {files_analyzed}\n- Highest salience files: {salience_summary}\n- Use this context to provide more targeted improvement suggestions."
    else:
        enhanced_query = base_query
    
    payload = {"note": note, "query": enhanced_query}
    
    # Add introspection data to payload if available
    if introspection_data:
        payload["ai_introspection"] = introspection_data
    
    # Write the payload to a local file
    with open('.github/workflows/request_payload.json', 'w') as f:
        json.dump(payload, f, indent=2)
    
    logger.info("Enhanced payload written to .github/workflows/request_payload.json")
    return {"improvement": "example_improvement", "assessment": "example_assessment"}

def introspect_repo():
    """Enhanced repository introspection with AI analysis"""
    try:
        # Try to use the echoself introspection system
        from echoself_introspection import EchoselfIntrospection
        
        introspector = EchoselfIntrospection(".")
        introspection_prompt = introspector.inject_repo_input_into_prompt(
            current_load=0.5, 
            recent_activity=0.3
        )
        metrics = introspector.get_attention_metrics()
        
        introspection_result = {
            "status": "success",
            "introspection_prompt": introspection_prompt[:1000] + "..." if len(introspection_prompt) > 1000 else introspection_prompt,
            "attention_metrics": metrics,
            "files_analyzed": metrics.get('hypergraph_nodes', 0),
            "highest_salience_files": metrics.get('highest_salience_files', []),
            "errors": [],
            "problem_areas": []
        }
        
        # Analyze problem areas based on salience scores
        if metrics.get('highest_salience_files'):
            high_salience_files = [f[0] for f in metrics['highest_salience_files'] if f[1] > 0.8]
            introspection_result["problem_areas"] = high_salience_files
        
        logger.info(f"AI introspection completed: {introspection_result['files_analyzed']} files analyzed")
        return introspection_result
        
    except ImportError as e:
        logger.warning(f"Echoself introspection not available: {e}")
        return {
            "status": "fallback",
            "errors": ["echoself_introspection module not available"],
            "problem_areas": ["example_problem_area_1", "example_problem_area_2"]
        }
    except Exception as e:
        logger.error(f"Introspection failed: {e}")
        return {
            "status": "error",
            "errors": [str(e)],
            "problem_areas": []
        }

def apply_improvement(improvement, introspection_data=None):
    """Apply improvement with introspection context"""
    logger.info(f"Applying improvement: {improvement}")
    
    if introspection_data and introspection_data.get('introspection_status') == 'success':
        logger.info(f"Improvement applied with AI introspection context")
        logger.info(f"Files analyzed: {introspection_data.get('files_analyzed', 0)}")
        
        # Log high salience files for context
        high_salience = introspection_data.get('highest_salience_files', [])
        if high_salience:
            logger.info("High salience files for improvement context:")
            for file_path, salience in high_salience[:3]:
                logger.info(f"  - {file_path} (salience: {salience:.3f})")

def run_workflow():
    result = "success"
    return result

def monitor_resources(stop_event, resource_queue):
    while not stop_event.is_set():
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        resource_queue.put((cpu_usage, memory.percent))
        time.sleep(1)

def main():
    max_retries = 3
    retries = 0

    logger.info("Starting enhanced self-improvement cycle with AI introspection")

    # Load previous note
    previous_note = read_note()
    logger.info(f"Loaded previous note from {previous_note.get('timestamp', 'unknown')}")

    # Load AI introspection data if available
    introspection_data = load_ai_introspection_data()
    if introspection_data:
        logger.info(f"AI introspection data loaded: {introspection_data.get('introspection_status', 'unknown')}")

    # Perform repository introspection
    introspection_result = introspect_repo()
    logger.info(f"Repository introspection completed: {introspection_result['status']}")

    # Call GitHub Copilot with enhanced context
    copilot_response = call_github_copilot(previous_note, introspection_data)

    if copilot_response is None:
        logger.error("Failed to get a valid response from GitHub Copilot.")
        return

    improvement = copilot_response.get("improvement")
    assessment = copilot_response.get("assessment")

    # Apply improvement with introspection context
    apply_improvement(improvement, introspection_data)

    # Monitor resources during execution
    stop_event = threading.Event()
    resource_queue = Queue()
    resource_monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, resource_queue))
    resource_monitor_thread.start()

    # Execute workflow with retry logic
    while retries < max_retries:
        try:
            result = run_workflow()
            if result == "success":
                break
            else:
                retries += 1
                time.sleep(10)
                logger.warning(f"Workflow failed, retrying {retries}/{max_retries}")
        except Exception as e:
            logger.error(f"Error during workflow execution: {e}")
            retries += 1
            time.sleep(10)
            logger.warning(f"Retrying {retries}/{max_retries}")

    stop_event.set()
    resource_monitor_thread.join()

    # Log resource usage
    resource_usage = []
    while not resource_queue.empty():
        cpu_usage, memory_usage = resource_queue.get()
        resource_usage.append((cpu_usage, memory_usage))
        logger.info(f"CPU Usage: {cpu_usage}%, Memory Usage: {memory_usage}%")

    # Calculate average resource usage
    if resource_usage:
        avg_cpu = sum(r[0] for r in resource_usage) / len(resource_usage)
        avg_memory = sum(r[1] for r in resource_usage) / len(resource_usage)
        logger.info(f"Average CPU: {avg_cpu:.2f}%, Average Memory: {avg_memory:.2f}%")

    # Create enhanced note with introspection data
    new_note = {
        "timestamp": datetime.utcnow().isoformat(),
        "improvement": improvement,
        "assessment": assessment,
        "result": result,
        "retries": retries,
        "introspection_enhanced": introspection_data is not None,
        "introspection_status": introspection_result.get("status", "unknown"),
        "files_analyzed": introspection_result.get("files_analyzed", 0),
        "resource_usage": {
            "avg_cpu": avg_cpu if resource_usage else None,
            "avg_memory": avg_memory if resource_usage else None,
            "samples": len(resource_usage)
        }
    }

    # Add introspection data if available
    if introspection_data:
        new_note["ai_introspection"] = introspection_data

    write_note(new_note)

    logger.info(f"Enhanced self-improvement cycle complete.")
    logger.info(f"Result: {result}, Assessment: {assessment}")
    logger.info(f"Introspection enhanced: {new_note['introspection_enhanced']}")
    logger.info(f"Files analyzed: {new_note['files_analyzed']}")

if __name__ == "__main__":
    main()
