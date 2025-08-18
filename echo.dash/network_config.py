#!/usr/bin/env python3
import os
import json
import logging
import requests
from pathlib import Path
import socket
import netifaces
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamNetwork:
    """Manages network configuration for the distributed team"""
    
    TEAM_ROLES = {
        'LEADER': {
            'name': 'Deep Tree Echo',
            'ports': [8000, 8001],  # API and WebSocket
            'protocols': ['http', 'ws']
        },
        'SCIENTIST': {
            'name': 'Marduk',
            'ports': [8010, 8011],  # Experiment API and Data Stream
            'protocols': ['http', 'grpc']
        },
        'EXPLORER': {
            'name': 'Unicorn Forest',
            'ports': [8020, 8021],  # Generation API and Events
            'protocols': ['http', 'ws']
        },
        'ATOMSPACE': {
            'name': 'ZoneCog',
            'ports': [8030, 8031],  # AtomSpace API and Query
            'protocols': ['http', 'grpc']
        },
        'SWARM': {
            'name': 'Kaw-Aii',
            'ports': [8040, 8041],  # Swarm API and P2P
            'protocols': ['http', 'p2p']
        },
        'SHARED': {
            'name': 'Team Hub',
            'ports': [8050, 8051],  # Collaboration API and Events
            'protocols': ['http', 'ws']
        }
    }

    def __init__(self):
        self.config_dir = Path('/opt/deepecho/network')
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'network.yaml'
        self.role = os.environ.get('TEAM_ROLE', 'LEADER')
        self.network_config = self._load_config()

    def _load_config(self):
        """Load or create network configuration"""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return yaml.safe_load(f)
        return self._create_default_config()

    def _create_default_config(self):
        """Create default network configuration"""
        config = {
            'team': {
                role: {
                    'name': info['name'],
                    'host': '',  # Will be set by Nettica
                    'ports': info['ports'],
                    'protocols': info['protocols'],
                    'status': 'offline'
                }
                for role, info in self.TEAM_ROLES.items()
            },
            'networks': {
                'primary': {
                    'type': 'nettica',
                    'subnet': '10.0.0.0/24',
                    'gateway': '10.0.0.1'
                },
                'collaboration': {
                    'type': 'nettica',
                    'subnet': '10.0.1.0/24',
                    'gateway': '10.0.1.1'
                }
            },
            'routes': {
                'LEADER': ['SCIENTIST', 'EXPLORER', 'ATOMSPACE', 'SWARM', 'SHARED'],
                'SCIENTIST': ['LEADER', 'ATOMSPACE', 'SHARED'],
                'EXPLORER': ['LEADER', 'SHARED'],
                'ATOMSPACE': ['LEADER', 'SCIENTIST', 'SHARED'],
                'SWARM': ['LEADER', 'SHARED'],
                'SHARED': ['*']  # Connected to all
            }
        }
        
        self._save_config(config)
        return config

    def _save_config(self, config):
        """Save network configuration"""
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

    def get_team_member_info(self, role):
        """Get network information for a team member"""
        return self.network_config['team'].get(role)

    def update_host(self, role, host):
        """Update host information for a team member"""
        if role in self.network_config['team']:
            self.network_config['team'][role]['host'] = host
            self.network_config['team'][role]['status'] = 'online'
            self._save_config(self.network_config)

    def get_routes(self):
        """Get network routes for current role"""
        return self.network_config['routes'].get(self.role, [])

    def generate_nettica_config(self):
        """Generate Nettica network configuration"""
        nettica_config = {
            'name': f'deep-tree-echo-{self.role.lower()}',
            'description': f'Network for {self.TEAM_ROLES[self.role]["name"]}',
            'ingress': {
                'enabled': True,
                'ports': self.TEAM_ROLES[self.role]['ports']
            },
            'egress': {
                'enabled': True,
                'routes': [
                    {
                        'destination': self.network_config['team'][route]['host'],
                        'ports': self.network_config['team'][route]['ports']
                    }
                    for route in self.get_routes()
                    if self.network_config['team'][route]['host']
                ]
            },
            'networks': self.network_config['networks']
        }
        
        nettica_file = self.config_dir / 'nettica.yaml'
        with open(nettica_file, 'w') as f:
            yaml.dump(nettica_config, f, default_flow_style=False)
        
        return nettica_file

    def setup_network(self):
        """Initialize network setup"""
        logger.info(f"Setting up network for {self.TEAM_ROLES[self.role]['name']}")
        
        # Generate Nettica configuration
        nettica_config = self.generate_nettica_config()
        logger.info(f"Generated Nettica configuration at {nettica_config}")
        
        # Get network interfaces
        interfaces = netifaces.interfaces()
        logger.info(f"Available network interfaces: {interfaces}")
        
        # Setup network routes
        routes = self.get_routes()
        logger.info(f"Configured routes to: {routes}")
        
        return {
            'role': self.role,
            'name': self.TEAM_ROLES[self.role]['name'],
            'ports': self.TEAM_ROLES[self.role]['ports'],
            'routes': routes,
            'config_file': str(nettica_config)
        }

    def check_connectivity(self, target_role):
        """Check connectivity to another team member"""
        target = self.network_config['team'].get(target_role)
        if not target or not target['host']:
            return False
            
        for port in target['ports']:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((target['host'], port))
                sock.close()
                if result == 0:
                    return True
            except:
                continue
        return False

    def get_network_status(self):
        """Get status of all network connections"""
        status = {
            'role': self.role,
            'name': self.TEAM_ROLES[self.role]['name'],
            'connections': {}
        }
        
        for route in self.get_routes():
            status['connections'][route] = {
                'name': self.TEAM_ROLES[route]['name'],
                'connected': self.check_connectivity(route),
                'host': self.network_config['team'][route]['host']
            }
            
        return status
