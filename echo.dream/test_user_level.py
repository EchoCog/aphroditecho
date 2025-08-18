"""
Test script for the user level components of the Deep Tree Echo (DTE) system.

This script tests the functionality of the three user level components:
- Projects (spatial dimension)
- Timelines (temporal dimension)
- Topics (causal dimension)
"""

import logging
from datetime import datetime, timedelta
from root.echo.user import get_projects, get_timelines, get_topics

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_projects():
    """Test the Projects component (spatial dimension)."""
    logger.info("Testing Projects component (spatial dimension)...")
    
    # Get the projects instance
    projects = get_projects()
    
    # Create a container
    container_id = projects.create_container(
        name="Research Projects",
        description="Container for all research-related projects",
        tags=["research", "academic"]
    )
    
    # Create a category within the container
    category_id = projects.create_category(
        name="Cognitive Computing",
        parent_id=container_id,
        description="Projects related to cognitive computing research",
        tags=["ai", "cognitive"]
    )
    
    # Create a project within the category
    project_id = projects.create_project(
        name="Deep Tree Echo",
        category_id=category_id,
        description="Recursive computational thinking platform",
        status="active",
        priority="high",
        tags=["recursive", "consciousness"]
    )
    
    # Add resources to the project
    resource1_id = projects.add_project_resource(
        project_id=project_id,
        name="Architecture Diagram",
        resource_type="document",
        location="diagrams/architecture.svg",
        description="Visual representation of the DTE architecture"
    )
    
    resource2_id = projects.add_project_resource(
        project_id=project_id,
        name="Research Paper",
        resource_type="document",
        location="papers/dte_recursive_thinking.pdf",
        description="Academic paper on recursive thinking"
    )
    
    # Update project progress
    projects.update_project_progress(project_id, 0.75)
    
    # Get the project details
    project = projects.get_project(project_id)
    
    # Get all resources for the project
    resources = projects.get_project_resources(project_id)
    
    # Print project state
    logger.info(f"Project '{project['name']}' progress: {project['progress']:.0%}")
    logger.info(f"Project has {len(resources)} resources")
    
    # Get summary of projects system state
    state = projects.get_projects_state()
    logger.info(f"Projects system state: {state}")
    
    logger.info("Projects component tests completed successfully.")
    return True

def test_timelines():
    """Test the Timelines component (temporal dimension)."""
    logger.info("Testing Timelines component (temporal dimension)...")
    
    # Get the timelines instance
    timelines = get_timelines()
    
    # Create a timeline
    timeline_id = timelines.create_timeline(
        name="DTE Development",
        timeline_type="project",
        description="Timeline for Deep Tree Echo development",
        tags=["development", "planning"]
    )
    
    # Create phases within the timeline
    phase1_id = timelines.create_phase(
        timeline_id=timeline_id,
        name="Planning Phase",
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now() - timedelta(days=15),
        phase_type="planning"
    )
    
    phase2_id = timelines.create_phase(
        timeline_id=timeline_id,
        name="Development Phase",
        start_date=datetime.now() - timedelta(days=14),
        end_date=datetime.now() + timedelta(days=30),
        phase_type="development"
    )
    
    # Add events to the timeline
    event1_id = timelines.add_event(
        timeline_id=timeline_id,
        title="Project Kickoff",
        timestamp=datetime.now() - timedelta(days=30),
        event_type="milestone",
        phase_id=phase1_id
    )
    
    event2_id = timelines.add_event(
        timeline_id=timeline_id,
        title="Architecture Design",
        timestamp=datetime.now() - timedelta(days=25),
        duration=timedelta(days=5),
        phase_id=phase1_id
    )
    
    event3_id = timelines.add_event(
        timeline_id=timeline_id,
        title="User Level Implementation",
        timestamp=datetime.now() - timedelta(days=10),
        duration=timedelta(days=5),
        phase_id=phase2_id
    )
    
    # Add a reminder for an event
    reminder_id = timelines.add_reminder(
        event_id=event3_id,
        remind_at=datetime.now() + timedelta(days=1),
        description="Final code review for user level"
    )
    
    # Get events in a time range
    events = timelines.get_events_in_timerange(
        start_time=datetime.now() - timedelta(days=15),
        end_time=datetime.now() + timedelta(days=15)
    )
    
    # Print timeline info
    logger.info(f"Timeline '{timelines.get_timeline(timeline_id)['name']}' has {len(events)} events in the last/next 15 days")
    
    # Get upcoming events
    upcoming = timelines.get_upcoming_events(days=30)
    logger.info(f"There are {len(upcoming)} upcoming events in the next 30 days")
    
    # Get summary of timelines system state
    state = timelines.get_timelines_state()
    logger.info(f"Timelines system state: {state}")
    
    logger.info("Timelines component tests completed successfully.")
    return True

def test_topics():
    """Test the Topics component (causal dimension)."""
    logger.info("Testing Topics component (causal dimension)...")
    
    # Get the topics instance
    topics = get_topics()
    
    # Create a forum
    forum_id = topics.create_forum(
        name="DTE Discussion",
        forum_type="discussion",
        description="Forum for discussing the Deep Tree Echo project",
        visibility="public",
        tags=["deep-tree-echo", "discussion"]
    )
    
    # Create threads within the forum
    thread1_id = topics.create_thread(
        forum_id=forum_id,
        title="Architecture Design Patterns",
        content="What design patterns are most suitable for implementing recursive consciousness?",
        thread_type="discussion",
        tags=["architecture", "design-patterns"]
    )
    
    thread2_id = topics.create_thread(
        forum_id=forum_id,
        title="Optimizing Memory Systems",
        content="How can we optimize the different memory types in the system?",
        thread_type="question",
        tags=["memory", "optimization"]
    )
    
    # Add messages to threads
    message1_id = topics.add_message(
        thread_id=thread1_id,
        content="I think the Composite pattern would be ideal for representing recursive structures."
    )
    
    message2_id = topics.add_message(
        thread_id=thread1_id,
        content="The Observer pattern could also be useful for implementing the consciousness stream.",
        parent_message_id=message1_id
    )
    
    message3_id = topics.add_message(
        thread_id=thread2_id,
        content="We should consider using different storage strategies for different memory types."
    )
    
    # Add reactions to messages
    reaction1_id = topics.add_reaction(
        message_id=message1_id,
        reaction_type="like"
    )
    
    reaction2_id = topics.add_reaction(
        message_id=message3_id,
        reaction_type="heart"
    )
    
    # Mark a message as an answer in a question thread
    topics.mark_as_answer(message3_id, True)
    
    # Get thread messages
    thread1_messages = topics.get_thread_messages(thread1_id)
    thread2_messages = topics.get_thread_messages(thread2_id)
    
    # Print topic info
    logger.info(f"Thread '{topics.get_thread(thread1_id)['title']}' has {len(thread1_messages)} messages")
    logger.info(f"Thread '{topics.get_thread(thread2_id)['title']}' has {len(thread2_messages)} messages")
    
    # Get message reactions
    reactions = topics.get_message_reactions(message1_id)
    logger.info(f"Message has {sum(reactions.values())} reactions")
    
    # Get hierarchical view of thread messages
    hierarchical_messages = topics.get_thread_messages(thread1_id, hierarchical=True)
    logger.info(f"Hierarchical view generated with {len(hierarchical_messages)} root messages")
    
    # Get forum threads
    threads = topics.get_forum_threads(forum_id)
    logger.info(f"Forum '{topics.get_forum(forum_id)['name']}' has {len(threads)} threads")
    
    # Get summary of topics system state
    state = topics.get_topics_state()
    logger.info(f"Topics system state: {state}")
    
    logger.info("Topics component tests completed successfully.")
    return True

def main():
    """Run all user level component tests."""
    logger.info("Starting user level component tests...")
    
    try:
        # Test Projects (spatial dimension)
        test_projects()
        
        # Test Timelines (temporal dimension)
        test_timelines()
        
        # Test Topics (causal dimension)
        test_topics()
        
        logger.info("All user level component tests completed successfully.")
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()