"""
User Level for Deep Tree Echo

This package contains the high level components of the DTE system,
representing the conscious/user level of the architecture.

Components:
- Projects (spatial dimension): Container/category/project structures for organizing user content
- Timelines (temporal dimension): Timeline/phase/event structures for tracking time-based elements
- Topics (causal dimension): Forum/thread/message structures for discussions and knowledge organization
"""

from root.echo.user.projects import get_projects
from root.echo.user.timelines import get_timelines
from root.echo.user.topics import get_topics

__all__ = ['get_projects', 'get_timelines', 'get_topics']