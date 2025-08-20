"""
Architecture Module for Deep Tree Echo (Echo Level)

This module represents the spatial dimension at the echo/subconscious level of the DTE architecture.
It manages the organization of workspace elements, their structural relationships, and properties.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class WorkspaceArchitecture:
    """Manages spatial organization of workspace elements and their relationships."""
    
    def __init__(self):
        """Initialize the architecture system."""
        self.elements = {}  # element_id -> element_dict
        self.root_elements = []  # list of top-level element ids
        
        # Spatial relationships
        self.element_parents = {}  # element_id -> parent_id
        self.element_children = defaultdict(list)  # parent_id -> list of child_ids
        
        # Element categorization
        self.element_types = defaultdict(list)  # type -> list of element_ids
        self.element_categories = defaultdict(list)  # category -> list of element_ids
        self.element_tags = defaultdict(list)  # tag -> list of element_ids
        
        # Element attributes
        self.element_attributes = defaultdict(dict)  # element_id -> attribute_dict
        
        # Element connections/links
        self.element_connections = defaultdict(list)  # source_id -> list of target_ids
        self.element_connection_types = {}  # (source_id, target_id) -> connection_type
        
        # Access control
        self.element_permissions = defaultdict(dict)  # element_id -> permission_dict
        
    def create_root_element(self, name: str, element_type: str, 
                          attributes: Dict[str, Any] = None) -> str:
        """Create a root-level element.
        
        Args:
            name: Name of the element
            element_type: Type of element (container, area, workspace, etc.)
            attributes: Additional attributes for the element
        
        Returns:
            ID of the created element
        """
        element_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        # Create the element
        self.elements[element_id] = {
            "id": element_id,
            "name": name,
            "type": element_type,
            "parent_id": None,
            "created_at": created_at,
            "updated_at": created_at,
            "position": (0, 0),  # Default position
            "size": (100, 100),  # Default size
            "active": True
        }
        
        # Add to root elements list
        self.root_elements.append(element_id)
        
        # Add to type categorization
        self.element_types[element_type].append(element_id)
        
        # Store attributes
        if attributes:
            self.element_attributes[element_id] = attributes
            
            # Add to categories if specified
            if "category" in attributes:
                categories = attributes["category"]
                if isinstance(categories, str):
                    categories = [categories]
                for category in categories:
                    self.element_categories[category].append(element_id)
            
            # Add tags if specified
            if "tags" in attributes:
                tags = attributes["tags"]
                if isinstance(tags, str):
                    tags = [tags]
                for tag in tags:
                    self.element_tags[tag].append(element_id)
        
        logger.info(f"Created root element '{name}' of type '{element_type}' with ID {element_id}")
        return element_id
        
    def create_element(self, name: str, parent_id: str, element_type: str,
                     position: Tuple[float, float] = None,
                     size: Tuple[float, float] = None,
                     attributes: Dict[str, Any] = None) -> str:
        """Create a new element under a parent.
        
        Args:
            name: Name of the element
            parent_id: ID of the parent element
            element_type: Type of element (container, area, workspace, etc.)
            position: Optional position as (x, y) coordinates
            size: Optional size as (width, height)
            attributes: Additional attributes for the element
        
        Returns:
            ID of the created element
        """
        if parent_id not in self.elements:
            logger.error(f"Cannot create element: parent {parent_id} not found")
            return None
            
        element_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        # Create the element
        self.elements[element_id] = {
            "id": element_id,
            "name": name,
            "type": element_type,
            "parent_id": parent_id,
            "created_at": created_at,
            "updated_at": created_at,
            "position": position or (0, 0),
            "size": size or (100, 100),
            "active": True
        }
        
        # Update parent-child relationships
        self.element_parents[element_id] = parent_id
        self.element_children[parent_id].append(element_id)
        
        # Add to type categorization
        self.element_types[element_type].append(element_id)
        
        # Store attributes
        if attributes:
            self.element_attributes[element_id] = attributes
            
            # Add to categories if specified
            if "category" in attributes:
                categories = attributes["category"]
                if isinstance(categories, str):
                    categories = [categories]
                for category in categories:
                    self.element_categories[category].append(element_id)
            
            # Add tags if specified
            if "tags" in attributes:
                tags = attributes["tags"]
                if isinstance(tags, str):
                    tags = [tags]
                for tag in tags:
                    self.element_tags[tag].append(element_id)
        
        logger.info(f"Created element '{name}' of type '{element_type}' under parent {parent_id}")
        return element_id
        
    def update_element(self, element_id: str, name: str = None, 
                     position: Tuple[float, float] = None,
                     size: Tuple[float, float] = None,
                     active: bool = None,
                     attributes: Dict[str, Any] = None) -> bool:
        """Update an existing element."""
        if element_id not in self.elements:
            logger.error(f"Cannot update element: {element_id} not found")
            return False
            
        element = self.elements[element_id]
        
        if name is not None:
            element["name"] = name
            
        if position is not None:
            element["position"] = position
            
        if size is not None:
            element["size"] = size
            
        if active is not None:
            element["active"] = active
            
        if attributes is not None:
            self.element_attributes[element_id].update(attributes)
            
        element["updated_at"] = datetime.now()
        
        logger.info(f"Updated element '{element['name']}' ({element_id})")
        return True
        
    def delete_element(self, element_id: str) -> bool:
        """Delete an element and all its children."""
        if element_id not in self.elements:
            return False
            
        # Recursively delete children first
        for child_id in list(self.element_children.get(element_id, [])):
            self.delete_element(child_id)
            
        # Remove from parent's children list
        parent_id = self.element_parents.get(element_id)
        if parent_id:
            if element_id in self.element_children[parent_id]:
                self.element_children[parent_id].remove(element_id)
                
        # Remove from root elements if it's a root
        if element_id in self.root_elements:
            self.root_elements.remove(element_id)
            
        # Remove from type categorization
        element_type = self.elements[element_id]["type"]
        if element_id in self.element_types[element_type]:
            self.element_types[element_type].remove(element_id)
            
        # Remove from categories and tags
        for category, elements in self.element_categories.items():
            if element_id in elements:
                elements.remove(element_id)
                
        for tag, elements in self.element_tags.items():
            if element_id in elements:
                elements.remove(element_id)
                
        # Remove connections
        if element_id in self.element_connections:
            del self.element_connections[element_id]
            
        # Clean up connection records pointing to this element
        for source_id, targets in self.element_connections.items():
            if element_id in targets:
                targets.remove(element_id)
                if (source_id, element_id) in self.element_connection_types:
                    del self.element_connection_types[(source_id, element_id)]
                    
        # Clean up other mappings
        if element_id in self.element_parents:
            del self.element_parents[element_id]
            
        if element_id in self.element_children:
            del self.element_children[element_id]
            
        if element_id in self.element_attributes:
            del self.element_attributes[element_id]
            
        if element_id in self.element_permissions:
            del self.element_permissions[element_id]
            
        # Finally, remove the element itself
        element_name = self.elements[element_id]["name"]
        del self.elements[element_id]
        
        logger.info(f"Deleted element '{element_name}' ({element_id})")
        return True
        
    def connect_elements(self, source_id: str, target_id: str, 
                        connection_type: str = "generic") -> bool:
        """Create a connection between two elements."""
        if source_id not in self.elements or target_id not in self.elements:
            return False
            
        if target_id not in self.element_connections[source_id]:
            self.element_connections[source_id].append(target_id)
            self.element_connection_types[(source_id, target_id)] = connection_type
            
            source_name = self.elements[source_id]["name"]
            target_name = self.elements[target_id]["name"]
            logger.info(f"Connected '{source_name}' to '{target_name}' with type '{connection_type}'")
            return True
        return False
        
    def disconnect_elements(self, source_id: str, target_id: str) -> bool:
        """Remove a connection between two elements."""
        if source_id not in self.element_connections:
            return False
            
        if target_id not in self.element_connections[source_id]:
            return False
            
        self.element_connections[source_id].remove(target_id)
        if (source_id, target_id) in self.element_connection_types:
            del self.element_connection_types[(source_id, target_id)]
            
        source_name = self.elements[source_id]["name"]
        target_name = self.elements[target_id]["name"]
        logger.info(f"Disconnected '{source_name}' from '{target_name}'")
        return True
        
    def move_element(self, element_id: str, new_parent_id: str) -> bool:
        """Move an element to a new parent."""
        if element_id not in self.elements or new_parent_id not in self.elements:
            return False
            
        # Get current parent
        current_parent_id = self.element_parents.get(element_id)
        
        # If it's a root element
        if current_parent_id is None:
            if element_id in self.root_elements:
                self.root_elements.remove(element_id)
        else:
            # Remove from current parent's children
            if element_id in self.element_children[current_parent_id]:
                self.element_children[current_parent_id].remove(element_id)
                
        # Update parent reference
        self.element_parents[element_id] = new_parent_id
        self.element_children[new_parent_id].append(element_id)
        self.elements[element_id]["parent_id"] = new_parent_id
        
        element_name = self.elements[element_id]["name"]
        new_parent_name = self.elements[new_parent_id]["name"]
        logger.info(f"Moved element '{element_name}' to new parent '{new_parent_name}'")
        return True
        
    def set_element_permission(self, element_id: str, user_id: str, 
                             permission: str) -> bool:
        """Set permission for a user on an element.
        
        Args:
            element_id: ID of the element
            user_id: ID of the user
            permission: Permission level (view, edit, admin, etc.)
        """
        if element_id not in self.elements:
            return False
            
        self.element_permissions[element_id][user_id] = permission
        return True
        
    def get_element(self, element_id: str) -> Dict[str, Any]:
        """Get an element by ID with its attributes and relationships."""
        if element_id not in self.elements:
            return None
            
        element = dict(self.elements[element_id])
        element["attributes"] = dict(self.element_attributes.get(element_id, {}))
        element["children"] = list(self.element_children.get(element_id, []))
        element["connections"] = list(self.element_connections.get(element_id, []))
        
        # Add connection types
        element["connection_details"] = []
        for target_id in element["connections"]:
            conn_type = self.element_connection_types.get((element_id, target_id), "generic")
            element["connection_details"].append({
                "target_id": target_id,
                "type": conn_type
            })
            
        return element
        
    def get_elements_by_type(self, element_type: str) -> List[str]:
        """Get all elements of a specific type."""
        return list(self.element_types.get(element_type, []))
        
    def get_elements_by_category(self, category: str) -> List[str]:
        """Get all elements in a specific category."""
        return list(self.element_categories.get(category, []))
        
    def get_elements_by_tag(self, tag: str) -> List[str]:
        """Get all elements with a specific tag."""
        return list(self.element_tags.get(tag, []))
        
    def get_architecture_state(self) -> Dict[str, Any]:
        """Get the current state of the architecture system."""
        # Count elements by type
        type_counts = {
            element_type: len(elements) 
            for element_type, elements in self.element_types.items()
        }
        
        # Count connections
        total_connections = sum(len(targets) for targets in self.element_connections.values())
        
        # Find active workspaces
        active_workspaces = [
            eid for eid, element in self.elements.items()
            if element.get("type") == "workspace" and element.get("active", False)
        ]
        
        state = {
            "element_count": len(self.elements),
            "root_element_count": len(self.root_elements),
            "connection_count": total_connections,
            "element_types": type_counts,
            "active_workspace_count": len(active_workspaces),
            "root_elements": self.root_elements,
            "categories": list(self.element_categories.keys()),
            "tags": list(self.element_tags.keys())
        }
        return state


# Create a singleton instance
workspace_architecture = WorkspaceArchitecture()

def get_architecture() -> WorkspaceArchitecture:
    """Get the workspace architecture singleton."""
    return workspace_architecture