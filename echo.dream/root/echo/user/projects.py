"""
Projects Module for Deep Tree Echo

This module handles the spatial dimension of the user level, providing
container/category/project structures for organizing user content.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)

class UserProjects:
    """Manages user projects, categories, and containers."""
    
    def __init__(self):
        """Initialize the projects manager."""
        self.user_id = "default_user"
        
        # Data stores
        self.containers = {}  # container_id -> container data
        self.categories = {}  # category_id -> category data
        self.projects = {}  # project_id -> project data
        self.resources = {}  # resource_id -> resource data
        
        # Relationship mappings
        self.container_categories = {}  # container_id -> [category_ids]
        self.category_projects = {}  # category_id -> [project_ids]
        self.project_resources = {}  # project_id -> [resource_ids]
        
        logger.info("User projects module initialized")
        
    def create_container(self, name: str, description: str = None,
                      tags: List[str] = None, attributes: Dict[str, Any] = None) -> str:
        """Create a top-level container for organizing projects.
        
        Args:
            name: The name of the container
            description: Optional description
            tags: Optional list of tags
            attributes: Optional additional attributes
            
        Returns:
            The ID of the created container
        """
        container_id = str(uuid.uuid4())
        
        self.containers[container_id] = {
            "id": container_id,
            "name": name,
            "user_id": self.user_id,
            "description": description or f"Container: {name}",
            "tags": tags or [],
            "attributes": attributes or {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        self.container_categories[container_id] = []
        
        logger.info(f"Created project container '{name}' with ID {container_id}")
        return container_id
        
    def create_category(self, name: str, parent_id: str,
                     description: str = None, tags: List[str] = None,
                     attributes: Dict[str, Any] = None) -> str:
        """Create a category within a container.
        
        Args:
            name: The name of the category
            parent_id: The ID of the parent container
            description: Optional description
            tags: Optional list of tags
            attributes: Optional additional attributes
            
        Returns:
            The ID of the created category
        """
        if parent_id not in self.containers:
            logger.error(f"Container {parent_id} not found")
            return None
            
        category_id = str(uuid.uuid4())
        
        self.categories[category_id] = {
            "id": category_id,
            "name": name,
            "parent_id": parent_id,
            "user_id": self.user_id,
            "description": description or f"Category: {name}",
            "tags": tags or [],
            "attributes": attributes or {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Add to parent container
        self.container_categories[parent_id].append(category_id)
        
        # Initialize project list
        self.category_projects[category_id] = []
        
        logger.info(f"Created project category '{name}' in container '{self.containers[parent_id]['name']}'")
        return category_id
        
    def create_project(self, name: str, category_id: str,
                    description: str = None, status: str = "active",
                    priority: str = "medium", tags: List[str] = None,
                    attributes: Dict[str, Any] = None) -> str:
        """Create a project within a category.
        
        Args:
            name: The name of the project
            category_id: The ID of the parent category
            description: Optional description
            status: Project status (active, inactive, completed, etc.)
            priority: Project priority (low, medium, high, etc.)
            tags: Optional list of tags
            attributes: Optional additional attributes
            
        Returns:
            The ID of the created project
        """
        if category_id not in self.categories:
            logger.error(f"Category {category_id} not found")
            return None
            
        project_id = str(uuid.uuid4())
        
        self.projects[project_id] = {
            "id": project_id,
            "name": name,
            "category_id": category_id,
            "user_id": self.user_id,
            "description": description or f"Project: {name}",
            "status": status,
            "priority": priority,
            "progress": 0.0,
            "tags": tags or [],
            "attributes": attributes or {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "start_date": None,
            "end_date": None,
            "completed_at": None
        }
        
        # Add to parent category
        self.category_projects[category_id].append(project_id)
        
        # Initialize resource list
        self.project_resources[project_id] = []
        
        logger.info(f"Created project '{name}' in category '{self.categories[category_id]['name']}'")
        return project_id
        
    def add_project_resource(self, project_id: str, name: str,
                          resource_type: str, location: str = None,
                          description: str = None, attributes: Dict[str, Any] = None) -> str:
        """Add a resource to a project.
        
        Args:
            project_id: The ID of the parent project
            name: The name of the resource
            resource_type: Type of resource (document, file, link, etc.)
            location: Location or path to the resource
            description: Optional description
            attributes: Optional additional attributes
            
        Returns:
            The ID of the created resource
        """
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return None
            
        resource_id = str(uuid.uuid4())
        
        self.resources[resource_id] = {
            "id": resource_id,
            "name": name,
            "project_id": project_id,
            "user_id": self.user_id,
            "resource_type": resource_type,
            "location": location,
            "description": description or f"Resource: {name}",
            "attributes": attributes or {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Add to parent project
        self.project_resources[project_id].append(resource_id)
        
        logger.info(f"Added resource '{name}' to project '{self.projects[project_id]['name']}'")
        return resource_id
        
    def update_project_status(self, project_id: str, status: str) -> bool:
        """Update the status of a project.
        
        Args:
            project_id: The ID of the project
            status: New status (active, inactive, completed, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return False
            
        old_status = self.projects[project_id]["status"]
        self.projects[project_id]["status"] = status
        self.projects[project_id]["updated_at"] = datetime.now()
        
        # If marked as completed, set completed timestamp
        if status == "completed" and old_status != "completed":
            self.projects[project_id]["completed_at"] = datetime.now()
        elif status != "completed" and old_status == "completed":
            self.projects[project_id]["completed_at"] = None
            
        logger.info(f"Updated project '{self.projects[project_id]['name']}' status to '{status}'")
        return True
        
    def update_project_progress(self, project_id: str, progress: float) -> bool:
        """Update the progress of a project.
        
        Args:
            project_id: The ID of the project
            progress: Progress value between 0.0 and 1.0
            
        Returns:
            True if successful, False otherwise
        """
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return False
            
        progress = max(0.0, min(1.0, progress))  # Clamp between 0 and 1
        self.projects[project_id]["progress"] = progress
        self.projects[project_id]["updated_at"] = datetime.now()
        
        logger.info(f"Updated project '{self.projects[project_id]['name']}' progress to {progress:.1%}")
        return True
        
    def get_container(self, container_id: str) -> Dict[str, Any]:
        """Get container details by ID."""
        if container_id not in self.containers:
            logger.error(f"Container {container_id} not found")
            return None
            
        return self.containers[container_id]
        
    def get_category(self, category_id: str) -> Dict[str, Any]:
        """Get category details by ID."""
        if category_id not in self.categories:
            logger.error(f"Category {category_id} not found")
            return None
            
        return self.categories[category_id]
        
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details by ID."""
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return None
            
        return self.projects[project_id]
        
    def get_resource(self, resource_id: str) -> Dict[str, Any]:
        """Get resource details by ID."""
        if resource_id not in self.resources:
            logger.error(f"Resource {resource_id} not found")
            return None
            
        return self.resources[resource_id]
        
    def get_container_categories(self, container_id: str) -> List[Dict[str, Any]]:
        """Get all categories within a container."""
        if container_id not in self.containers:
            logger.error(f"Container {container_id} not found")
            return []
            
        category_ids = self.container_categories.get(container_id, [])
        return [self.categories[cat_id] for cat_id in category_ids if cat_id in self.categories]
        
    def get_category_projects(self, category_id: str) -> List[Dict[str, Any]]:
        """Get all projects within a category."""
        if category_id not in self.categories:
            logger.error(f"Category {category_id} not found")
            return []
            
        project_ids = self.category_projects.get(category_id, [])
        return [self.projects[proj_id] for proj_id in project_ids if proj_id in self.projects]
        
    def get_project_resources(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all resources within a project."""
        if project_id not in self.projects:
            logger.error(f"Project {project_id} not found")
            return []
            
        resource_ids = self.project_resources.get(project_id, [])
        return [self.resources[res_id] for res_id in resource_ids if res_id in self.resources]
        
    def get_projects_state(self) -> Dict[str, Any]:
        """Get a summary of the projects system state."""
        return {
            "container_count": len(self.containers),
            "category_count": len(self.categories),
            "project_count": len(self.projects),
            "resource_count": len(self.resources),
            "active_projects": sum(1 for p in self.projects.values() if p["status"] == "active"),
            "completed_projects": sum(1 for p in self.projects.values() if p["status"] == "completed"),
            "high_priority_projects": sum(1 for p in self.projects.values() if p["priority"] == "high"),
            "updated_at": datetime.now()
        }
        
    # Search and filter functions
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """Search for projects by name or description."""
        query = query.lower()
        results = []
        
        for project in self.projects.values():
            if query in project["name"].lower() or (project["description"] and query in project["description"].lower()):
                results.append(project)
                
        return results
        
    def find_projects_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Find projects with a specific tag."""
        tag = tag.lower()
        return [p for p in self.projects.values() if tag in [t.lower() for t in p["tags"]]]
        
    def find_projects_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Find projects with a specific status."""
        return [p for p in self.projects.values() if p["status"] == status]


# Create singleton instance
_projects_instance = UserProjects()

def get_projects() -> UserProjects:
    """Get the Projects instance."""
    return _projects_instance