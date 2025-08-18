#!/usr/bin/env python3
"""
Web-based GUI Dashboard for Deep Tree Echo System.

This module provides a Flask-based web interface for monitoring and controlling
the Deep Tree Echo system, including memory visualization, heartbeat monitoring,
activity regulation, and system metrics.
"""

# Standard library imports
import argparse
import io
import json
import logging
import random
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

# Third-party imports
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

try:
    from flask import Flask, jsonify, request, Response
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = jsonify = request = Response = None

# Local imports
try:
    from adaptive_heartbeat import AdaptiveHeartbeat
    ADAPTIVE_HEARTBEAT_AVAILABLE = True
except ImportError:
    ADAPTIVE_HEARTBEAT_AVAILABLE = False
    AdaptiveHeartbeat = None

try:
    from memory_management import HypergraphMemory
    HYPERGRAPH_MEMORY_AVAILABLE = True
except ImportError:
    HYPERGRAPH_MEMORY_AVAILABLE = False
    HypergraphMemory = None
try:
    from deep_tree_echo import DeepTreeEcho
except ImportError:
    DeepTreeEcho = None
try:
    from activity_regulation import ActivityRegulator, TaskPriority
except ImportError:
    ActivityRegulator = None
    TaskPriority = None
try:
    from chat_session_manager import session_manager
except ImportError:
    session_manager = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='web_gui.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Global variables
if FLASK_AVAILABLE:
    app = Flask(__name__)
else:
    # Create a dummy app object for import compatibility
    class DummyApp:
        def route(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def run(self, *args, **kwargs):
            print("Flask not available - cannot start web server")
    app = DummyApp()
MEMORY = None
ACTIVITY_REGULATOR = None
HEARTBEAT_SYSTEM = AdaptiveHeartbeat() if ADAPTIVE_HEARTBEAT_AVAILABLE else None
HEARTBEAT_THREAD = None

# Start the heartbeat in a separate thread
def start_heartbeat_thread():
    """Start the adaptive heartbeat system in a separate daemon thread."""
    global HEARTBEAT_THREAD
    if HEARTBEAT_SYSTEM and (HEARTBEAT_THREAD is None or not HEARTBEAT_THREAD.is_alive()):
        HEARTBEAT_THREAD = threading.Thread(target=HEARTBEAT_SYSTEM.start, daemon=True)
        HEARTBEAT_THREAD.start()
        logger.info("Started adaptive heartbeat thread")
    elif not ADAPTIVE_HEARTBEAT_AVAILABLE:
        logger.warning("Adaptive heartbeat not available - missing dependencies")

# Memory for storing historical data
SYSTEM_HISTORY = {
    'cpu': [],
    'memory': [],
    'disk': [],
    'network': [],
    'heartbeat': [],
    'timestamps': []
}

# Store heartbeat logs
HEARTBEAT_LOGS = []

# HTML Template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Echo System Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            width: 95%;
            margin: 0 auto;
            padding: 20px 0;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .tabs {
            display: flex;
            margin-top: 20px;
            border-bottom: 1px solid #ddd;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: 1px solid transparent;
            border-bottom: none;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
        }
        .tab.active {
            background-color: white;
            border-color: #ddd;
            color: #2c3e50;
            font-weight: bold;
        }
        .tab:hover:not(.active) {
            background-color: #eee;
        }
        .tab-content {
            display: none;
            background-color: white;
            padding: 20px;
            border: 1px solid #ddd;
            border-top: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .tab-content.active {
            display: block;
        }
        .status-container {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        .status-card {
            background-color: white;
            border-radius: 5px;
            padding: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            flex: 1;
            min-width: 200px;
            margin: 0 10px 10px 0;
        }
        .status-card h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .chart-container {
            background-color: white;
            border-radius: 5px;
            padding: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .chart-container h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .chart {
            width: 100%;
            height: 300px;
            margin-top: 15px;
        }
        .chart img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .control-panel {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 15px;
        }
        .control-card {
            background-color: #f9f9f9;
            border-radius: 5px;
            padding: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            flex: 1;
            min-width: 250px;
        }
        .btn {
            padding: 8px 15px;
            background-color: #2c3e50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 10px;
        }
        .btn:hover {
            background-color: #1a252f;
        }
        .btn.danger {
            background-color: #e74c3c;
        }
        .btn.danger:hover {
            background-color: #c0392b;
        }
        .btn.warning {
            background-color: #f39c12;
        }
        .btn.warning:hover {
            background-color: #d35400;
        }
        .btn.success {
            background-color: #27ae60;
        }
        .btn.success:hover {
            background-color: #2ecc71;
        }
        .slider-container {
            margin-top: 10px;
        }
        input[type="range"] {
            width: 100%;
        }
        .value-display {
            text-align: center;
            margin-top: 5px;
            font-weight: bold;
        }
        .log-entry {
            padding: 8px;
            margin-bottom: 5px;
            border-radius: 4px;
        }
        .log-entry:nth-child(odd) {
            background-color: #f9f9f9;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-good {
            background-color: #2ecc71;
        }
        .status-warning {
            background-color: #f39c12;
        }
        .status-critical {
            background-color: #e74c3c;
        }
        /* Heartbeat tab specific styles */
        .pulse-animation {
            animation: pulse 1s infinite;
            display: inline-block;
            color: #e74c3c;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.2); }
            100% { transform: scale(1); }
        }
        .heartbeat-controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        /* Chat Sessions tab specific styles */
        .session-card {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .session-card:hover {
            background-color: #e9ecef;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .session-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .session-title {
            font-weight: bold;
            color: #2c3e50;
            font-size: 16px;
        }
        .session-platform {
            background-color: #3498db;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            text-transform: uppercase;
        }
        .session-meta {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 8px;
        }
        .session-preview {
            font-size: 14px;
            color: #495057;
            max-height: 60px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .session-stats {
            display: flex;
            gap: 15px;
            margin-top: 10px;
            font-size: 12px;
            color: #6c757d;
        }
        .filter-controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .filter-control {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .filter-control label {
            font-weight: bold;
            color: #2c3e50;
        }
        .filter-control select, .filter-control input {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .session-detail {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .message-card {
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 0 8px 8px 0;
        }
        .message-card.user {
            border-left-color: #27ae60;
            background-color: #e8f5e8;
        }
        .message-card.assistant {
            border-left-color: #3498db;
            background-color: #e3f2fd;
        }
        .message-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 14px;
        }
        .message-role {
            font-weight: bold;
            text-transform: capitalize;
        }
        .message-content {
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 20px;
        }
        .pagination button {
            padding: 8px 12px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .pagination button:disabled {
            background-color: #bdc3c7;
            cursor: not-allowed;
        }
        .pagination span {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-project-diagram"></i> Echo System Dashboard</h1>
        <div>
            <span id="current-time"></span>
        </div>
    </div>

    <div class="container">
        <div class="tabs">
            <div class="tab active" data-tab="overview">Overview</div>
            <div class="tab" data-tab="resources">System Resources</div>
            <div class="tab" data-tab="heartbeat">Adaptive Heartbeat</div>
            <div class="tab" data-tab="logs">Activity Logs</div>
            <div class="tab" data-tab="network">Network</div>
            <div class="tab" data-tab="chatsessions">Chat Sessions</div>
            <div class="tab" data-tab="config">Configuration</div>
        </div>

        <!-- Overview Tab -->
        <div id="overview" class="tab-content active">
            <div class="status-container">
                <div class="status-card">
                    <h3>System Status</h3>
                    <p><strong>Status:</strong> <span id="system-status">Operational</span></p>
                    <p><strong>Uptime:</strong> <span id="system-uptime">Loading...</span></p>
                </div>
                <div class="status-card">
                    <h3>Resource Usage</h3>
                    <p><strong>CPU:</strong> <span id="cpu-usage">Loading...</span></p>
                    <p><strong>Memory:</strong> <span id="memory-usage">Loading...</span></p>
                    <p><strong>Disk:</strong> <span id="disk-usage">Loading...</span></p>
                </div>
                <div class="status-card">
                    <h3>Heartbeat Status</h3>
                    <p><strong>Rate:</strong> <span id="overview-heartbeat-rate">Loading...</span></p>
                    <p><strong>Mode:</strong> <span id="overview-heartbeat-mode">Normal</span></p>
                </div>
                <div class="status-card">
                    <h3>Recent Events</h3>
                    <div id="recent-events">Loading events...</div>
                </div>
            </div>

            <div class="chart-container">
                <h3>System Overview</h3>
                <div class="chart">
                    <img src="/chart/system_overview" alt="System Overview" id="system-overview-chart">
                </div>
            </div>
        </div>

        <!-- Resources Tab -->
        <div id="resources" class="tab-content">
            <div class="status-container">
                <div class="status-card">
                    <h3>CPU</h3>
                    <div id="cpu-detail">
                        <p><strong>Usage:</strong> <span id="cpu-percent">Loading...</span></p>
                        <p><strong>Cores:</strong> <span id="cpu-cores">Loading...</span></p>
                    </div>
                </div>
                <div class="status-card">
                    <h3>Memory</h3>
                    <div id="memory-detail">
                        <p><strong>Used:</strong> <span id="memory-used">Loading...</span></p>
                        <p><strong>Available:</strong> <span id="memory-available">Loading...</span></p>
                        <p><strong>Total:</strong> <span id="memory-total">Loading...</span></p>
                    </div>
                </div>
                <div class="status-card">
                    <h3>Disk</h3>
                    <div id="disk-detail">
                        <p><strong>Used:</strong> <span id="disk-used">Loading...</span></p>
                        <p><strong>Free:</strong> <span id="disk-free">Loading...</span></p>
                        <p><strong>Total:</strong> <span id="disk-total">Loading...</span></p>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <h3>CPU History</h3>
                <div class="chart">
                    <img src="/chart/cpu_history" alt="CPU History" id="cpu-chart">
                </div>
            </div>

            <div class="chart-container">
                <h3>Memory History</h3>
                <div class="chart">
                    <img src="/chart/memory_history" alt="Memory History" id="memory-chart">
                </div>
            </div>

            <div class="chart-container">
                <h3>Process List</h3>
                <table id="process-table">
                    <thead>
                        <tr>
                            <th>PID</th>
                            <th>Name</th>
                            <th>CPU %</th>
                            <th>Memory %</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="process-body">
                        <tr>
                            <td colspan="5">Loading processes...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Adaptive Heartbeat Tab -->
        <div id="heartbeat" class="tab-content">
            <div class="status-container">
                <div class="status-card">
                    <h3><i class="fas fa-heartbeat pulse-animation"></i> Current Heartbeat</h3>
                    <p><strong>Rate:</strong> <span id="heartbeat-rate">Loading...</span> BPM</p>
                    <p><strong>System Status:</strong> <span id="heartbeat-status">
                        <span class="status-indicator status-good"></span>Normal
                    </span></p>
                    <p><strong>Hyper Drive:</strong> <span id="hyper-drive-status">Inactive</span></p>
                </div>

                <div class="status-card">
                    <h3>System Health</h3>
                    <p><strong>CPU Usage:</strong> <span id="heartbeat-cpu">Loading...</span></p>
                    <p><strong>Last Assessment:</strong> <span id="last-assessment">Loading...</span></p>
                    <button id="force-assessment" class="btn">Force Assessment</button>
                </div>

                <div class="status-card">
                    <h3>Quick Actions</h3>
                    <button id="toggle-hyper-drive" class="btn warning">Toggle Hyper Drive</button>
                    <button id="restart-heartbeat" class="btn danger">Restart Heartbeat</button>
                </div>
            </div>

            <div class="chart-container">
                <h3>Heartbeat History</h3>
                <p>Showing heartbeat rate over time with hyper drive periods highlighted in yellow</p>
                <div class="chart">
                    <img src="/chart/heartbeat_history" alt="Heartbeat History" id="heartbeat-chart">
                </div>
            </div>

            <div class="control-panel">
                <div class="control-card">
                    <h3>Base Heartbeat Rate</h3>
                    <p>Adjust the base heartbeat rate (beats per minute)</p>
                    <div class="slider-container">
                        <input type="range" id="base-rate-slider" min="30" max="120" value="60">
                        <div class="value-display"><span id="base-rate-value">60</span> BPM</div>
                    </div>
                    <button id="update-base-rate" class="btn">Update</button>
                </div>

                <div class="control-card">
                    <h3>Hyper Drive Threshold</h3>
                    <p>Set CPU threshold for automatic Hyper Drive activation</p>
                    <div class="slider-container">
                        <input type="range" id="hyper-threshold-slider" min="60" max="95" value="90">
                        <div class="value-display"><span id="hyper-threshold-value">90</span>%</div>
                    </div>
                    <button id="update-hyper-threshold" class="btn">Update</button>
                </div>
            </div>

            <div class="chart-container">
                <h3>Recent Heartbeat Events</h3>
                <div id="heartbeat-events">
                    <p>Loading events...</p>
                </div>
            </div>
        </div>

        <!-- Logs Tab -->
        <div id="logs" class="tab-content">
            <div class="chart-container">
                <h3>System Log</h3>
                <div id="log-content">
                    <p>Loading logs...</p>
                </div>
            </div>
        </div>

        <!-- Network Tab -->
        <div id="network" class="tab-content">
            <div class="status-container">
                <div class="status-card">
                    <h3>Network Status</h3>
                    <p><strong>Status:</strong> <span id="network-status">Connected</span></p>
                </div>
                <div class="status-card">
                    <h3>Network Traffic</h3>
                    <p><strong>Sent:</strong> <span id="network-sent">Loading...</span></p>
                    <p><strong>Received:</strong> <span id="network-received">Loading...</span></p>
                </div>
                <div class="status-card">
                    <h3>Active Connections</h3>
                    <p><strong>Count:</strong> <span id="connection-count">Loading...</span></p>
                </div>
            </div>

            <div class="chart-container">
                <h3>Network History</h3>
                <div class="chart">
                    <img src="/chart/network_history" alt="Network History" id="network-chart">
                </div>
            </div>

            <div class="chart-container">
                <h3>Connection List</h3>
                <table id="connection-table">
                    <thead>
                        <tr>
                            <th>Local Address</th>
                            <th>Remote Address</th>
                            <th>Status</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody id="connection-body">
                        <tr>
                            <td colspan="4">Loading connections...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Chat Sessions Tab -->
        <div id="chatsessions" class="tab-content">
            <div class="chart-container">
                <h3>Chat Session Manager</h3>

                <!-- Statistics Summary -->
                <div class="status-container" id="chat-stats-container">
                    <div class="status-card">
                        <h4>Total Sessions</h4>
                        <p id="total-sessions">Loading...</p>
                    </div>
                    <div class="status-card">
                        <h4>Total Messages</h4>
                        <p id="total-messages">Loading...</p>
                    </div>
                    <div class="status-card">
                        <h4>Average Session Length</h4>
                        <p id="avg-session-length">Loading...</p>
                    </div>
                    <div class="status-card">
                        <h4>Active Platforms</h4>
                        <p id="active-platforms">Loading...</p>
                    </div>
                </div>

                <!-- Filters -->
                <div class="filter-controls">
                    <div class="filter-control">
                        <label for="platform-filter">Platform:</label>
                        <select id="platform-filter">
                            <option value="">All Platforms</option>
                            <option value="CHATGPT">ChatGPT</option>
                            <option value="CLAUDE">Claude</option>
                            <option value="WINDSURF">Windsurf</option>
                            <option value="BROWSER">Browser</option>
                            <option value="API">API</option>
                        </select>
                    </div>
                    <div class="filter-control">
                        <label for="days-filter">Time Range:</label>
                        <select id="days-filter">
                            <option value="7">Last 7 days</option>
                            <option value="30" selected>Last 30 days</option>
                            <option value="90">Last 90 days</option>
                            <option value="365">Last year</option>
                        </select>
                    </div>
                    <div class="filter-control">
                        <label for="search-filter">Search:</label>
                        <input type="text" id="search-filter" placeholder="Search sessions...">
                    </div>
                    <div class="filter-control">
                        <label>&nbsp;</label>
                        <button id="apply-filters" class="btn">Apply Filters</button>
                    </div>
                </div>

                <!-- Session List -->
                <div id="sessions-container">
                    <div id="sessions-list">
                        <p>Loading chat sessions...</p>
                    </div>

                    <!-- Pagination -->
                    <div class="pagination" id="pagination-container" style="display: none;">
                        <button id="prev-page" onclick="loadSessions(currentPage - 1)">Previous</button>
                        <span id="page-info">Page 1 of 1</span>
                        <button id="next-page" onclick="loadSessions(currentPage + 1)">Next</button>
                    </div>
                </div>

                <!-- Session Detail Modal (initially hidden) -->
                <div id="session-detail" class="session-detail" style="display: none;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h4 id="detail-title">Session Details</h4>
                        <button onclick="closeSessionDetail()" class="btn">Close</button>
                    </div>
                    <div id="session-info"></div>
                    <div id="session-messages"></div>
                </div>
            </div>
        </div>

        <!-- Configuration Tab -->
        <div id="config" class="tab-content">
            <div class="chart-container">
                <h3>System Configuration</h3>
                <table id="config-table">
                    <thead>
                        <tr>
                            <th>Setting</th>
                            <th>Value</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="config-body">
                        <tr>
                            <td colspan="3">Loading configuration...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Tab switching functionality
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                // Add active class to clicked tab
                this.classList.add('active');
                document.getElementById(this.dataset.tab).classList.add('active');

                // Load specific data based on tab
                const activeTab = this.dataset.tab;
                if (activeTab === 'chatsessions') {
                    loadChatStatistics();
                    loadSessions(1, {});
                }

                // Refresh charts on tab change
                updateCharts();
            });
        });

        // Current time update
        function updateCurrentTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = now.toLocaleString();
        }

        // Update charts and refresh data
        function updateCharts() {
            const activeTab = document.querySelector('.tab.active').dataset.tab;

            // Add timestamp to force refresh of images
            const timestamp = new Date().getTime();

            if (activeTab === 'overview' || activeTab === 'resources') {
                document.getElementById('cpu-chart').src = '/chart/cpu_history?' + timestamp;
                document.getElementById('memory-chart').src = '/chart/memory_history?' + timestamp;
                document.getElementById('system-overview-chart').src = '/chart/system_overview?' + timestamp;
            }

            if (activeTab === 'network') {
                document.getElementById('network-chart').src = '/chart/network_history?' + timestamp;
            }

            if (activeTab === 'heartbeat') {
                document.getElementById('heartbeat-chart').src = '/chart/heartbeat_history?' + timestamp;
            }
        }

        // Fetch and update system metrics
        function updateSystemMetrics() {
            fetch('/api/system_metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('cpu-usage').textContent = data.cpu + '%';
                    document.getElementById('cpu-percent').textContent = data.cpu + '%';
                    document.getElementById('memory-usage').textContent = data.memory + '%';
                    document.getElementById('disk-usage').textContent = data.disk + '%';
                    document.getElementById('system-uptime').textContent = data.uptime;
                    document.getElementById('cpu-cores').textContent = data.cpu_cores;
                    document.getElementById('memory-used').textContent = data.memory_used;
                    document.getElementById('memory-available').textContent = data.memory_available;
                    document.getElementById('memory-total').textContent = data.memory_total;
                    document.getElementById('disk-used').textContent = data.disk_used;
                    document.getElementById('disk-free').textContent = data.disk_free;
                    document.getElementById('disk-total').textContent = data.disk_total;

                    // Update process table
                    const processBody = document.getElementById('process-body');
                    processBody.innerHTML = '';
                    data.processes.forEach(process => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${process.pid}</td>
                            <td>${process.name}</td>
                            <td>${process.cpu}%</td>
                            <td>${process.memory}%</td>
                            <td>${process.status}</td>
                        `;
                        processBody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error fetching system metrics:', error));
        }

        // Fetch and update network metrics
        function updateNetworkMetrics() {
            fetch('/api/network_metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('network-sent').textContent = data.sent;
                    document.getElementById('network-received').textContent = data.received;
                    document.getElementById('connection-count').textContent = data.connections;

                    // Update connection table
                    const connectionBody = document.getElementById('connection-body');
                    connectionBody.innerHTML = '';
                    data.connection_list.forEach(conn => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${conn.local_address}</td>
                            <td>${conn.remote_address}</td>
                            <td>${conn.status}</td>
                            <td>${conn.type}</td>
                        `;
                        connectionBody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error fetching network metrics:', error));
        }

        // Fetch and update system logs
        function updateSystemLogs() {
            fetch('/api/system_logs')
                .then(response => response.json())
                .then(data => {
                    const logContent = document.getElementById('log-content');
                    logContent.innerHTML = '';
                    data.logs.forEach(log => {
                        const logEntry = document.createElement('div');
                        logEntry.className = 'log-entry';
                        logEntry.innerHTML = `<strong>${log.timestamp}</strong>: ${log.message}`;
                        logContent.appendChild(logEntry);
                    });
                })
                .catch(error => console.error('Error fetching system logs:', error));
        }

        // Fetch and update recent events
        function updateRecentEvents() {
            fetch('/api/recent_events')
                .then(response => response.json())
                .then(data => {
                    const eventsDiv = document.getElementById('recent-events');
                    eventsDiv.innerHTML = '';
                    data.events.forEach(event => {
                        const eventEntry = document.createElement('div');
                        eventEntry.className = 'log-entry';
                        eventEntry.innerHTML = `<strong>${event.timestamp}</strong>: ${event.message}`;
                        eventsDiv.appendChild(eventEntry);
                    });
                })
                .catch(error => console.error('Error fetching recent events:', error));
        }

        // Fetch and update heartbeat metrics
        function updateHeartbeatMetrics() {
            fetch('/api/heartbeat_metrics')
                .then(response => response.json())
                .then(data => {
                    // Update heartbeat tab
                    document.getElementById('heartbeat-rate').textContent = data.current_rate;
                    document.getElementById('heartbeat-cpu').textContent = data.cpu_usage + '%';
                    document.getElementById('hyper-drive-status').textContent = data.hyper_drive ? 'Active' : 'Inactive';

                    // Update overview tab heartbeat status
                    document.getElementById('overview-heartbeat-rate').textContent = data.current_rate + ' BPM';
                    document.getElementById('overview-heartbeat-mode').textContent = data.hyper_drive ? 'Hyper Drive' : 'Normal';

                    // Update heartbeat status indicator
                    const statusIndicator = document.getElementById('heartbeat-status');
                    if (data.health_status === 'Good') {
                        statusIndicator.innerHTML = '<span class="status-indicator status-good"></span>Normal';
                    } else if (data.health_status === 'Warning') {
                        statusIndicator.innerHTML = '<span class="status-indicator status-warning"></span>Elevated';
                    } else if (data.health_status === 'Critical') {
                        statusIndicator.innerHTML = '<span class="status-indicator status-critical"></span>Critical';
                    }

                    // Update heartbeat events
                    const eventsDiv = document.getElementById('heartbeat-events');
                    eventsDiv.innerHTML = '';
                    data.recent_logs.forEach(log => {
                        const logEntry = document.createElement('div');
                        logEntry.className = 'log-entry';
                        logEntry.innerHTML = `<strong>${log.timestamp}</strong>: ${log.message}`;
                        eventsDiv.appendChild(logEntry);
                    });
                })
                .catch(error => console.error('Error fetching heartbeat metrics:', error));
        }

        // Setup heartbeat controls
        function setupHeartbeatControls() {
            // Base rate slider
            const baseRateSlider = document.getElementById('base-rate-slider');
            const baseRateValue = document.getElementById('base-rate-value');

            baseRateSlider.addEventListener('input', () => {
                baseRateValue.textContent = baseRateSlider.value;
            });

            document.getElementById('update-base-rate').addEventListener('click', () => {
                const value = baseRateSlider.value;
                fetch(`/api/update_heartbeat_rate?value=${value}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Base heartbeat rate updated!');
                        } else {
                            alert('Error: ' + data.message);
                        }
                    })
                    .catch(error => console.error('Error updating heartbeat rate:', error));
            });

            // Hyper drive threshold slider
            const hyperThresholdSlider = document.getElementById('hyper-threshold-slider');
            const hyperThresholdValue = document.getElementById('hyper-threshold-value');

            hyperThresholdSlider.addEventListener('input', () => {
                hyperThresholdValue.textContent = hyperThresholdSlider.value;
            });

            document.getElementById('update-hyper-threshold').addEventListener('click', () => {
                const value = hyperThresholdSlider.value;
                fetch(`/api/update_hyper_threshold?value=${value}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Hyper drive threshold updated!');
                        } else {
                            alert('Error: ' + data.message);
                        }
                    })
                    .catch(error => console.error('Error updating threshold:', error));
            });

            // Toggle hyper drive button
            document.getElementById('toggle-hyper-drive').addEventListener('click', () => {
                fetch('/api/toggle_hyper_drive')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert(data.message);
                            updateHeartbeatMetrics();
                        } else {
                            alert('Error: ' + data.message);
                        }
                    })
                    .catch(error => console.error('Error toggling hyper drive:', error));
            });

            // Force assessment button
            document.getElementById('force-assessment').addEventListener('click', () => {
                fetch('/api/force_heartbeat_assessment')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('System assessment completed!');
                            updateHeartbeatMetrics();
                        } else {
                            alert('Error: ' + data.message);
                        }
                    })
                    .catch(error => console.error('Error forcing assessment:', error));
            });

            // Restart heartbeat button
            document.getElementById('restart-heartbeat').addEventListener('click', () => {
                if (confirm('Are you sure you want to restart the heartbeat system?')) {
                    fetch('/api/restart_heartbeat')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                alert('Heartbeat system restarted!');
                                updateHeartbeatMetrics();
                            } else {
                                alert('Error: ' + data.message);
                            }
                        })
                        .catch(error => console.error('Error restarting heartbeat:', error));
                }
            });
        }

        // Chat Session Management
        let currentPage = 1;
        let currentFilters = {};

        // Load chat sessions with pagination and filtering
        function loadSessions(page = 1, filters = {}) {
            currentPage = page;
            currentFilters = filters;

            const queryParams = new URLSearchParams({
                page: page,
                limit: 10,
                platform: filters.platform || '',
                days: filters.days || 30,
                search: filters.search || ''
            });

            fetch(`/api/chat_sessions?${queryParams}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displaySessions(data.sessions);
                        updatePagination(data.page, data.total, data.limit, data.has_next);
                    } else {
                        document.getElementById('sessions-list').innerHTML = `<p>Error loading sessions: ${data.error}</p>`;
                    }
                })
                .catch(error => {
                    console.error('Error loading sessions:', error);
                    document.getElementById('sessions-list').innerHTML = '<p>Error loading sessions. Chat session manager may not be available.</p>';
                });
        }

        // Display sessions in the UI
        function displaySessions(sessions) {
            const container = document.getElementById('sessions-list');

            if (!sessions || sessions.length === 0) {
                container.innerHTML = '<p>No chat sessions found.</p>';
                return;
            }

            container.innerHTML = sessions.map(session => `
                <div class="session-card" onclick="loadSessionDetail('${session.id}')">
                    <div class="session-header">
                        <div class="session-title">${session.title || 'Untitled Session'}</div>
                        <div class="session-platform">${session.platform}</div>
                    </div>
                    <div class="session-meta">
                        Started: ${new Date(session.start_time).toLocaleString()} |
                        ${session.end_time ? 'Ended: ' + new Date(session.end_time).toLocaleString() : 'Active'} |
                        Status: ${session.status}
                    </div>
                    <div class="session-preview">
                        ${session.last_message_preview || 'No messages yet'}
                    </div>
                    <div class="session-stats">
                        <span>💬 ${session.total_messages} messages</span>
                        <span>🔄 Echo: ${session.avg_echo_value ? session.avg_echo_value.toFixed(2) : 'N/A'}</span>
                        <span>⚡ Salience: ${session.avg_salience ? session.avg_salience.toFixed(2) : 'N/A'}</span>
                    </div>
                </div>
            `).join('');
        }

        // Update pagination controls
        function updatePagination(page, total, limit, hasNext) {
            const container = document.getElementById('pagination-container');
            const pageInfo = document.getElementById('page-info');
            const prevBtn = document.getElementById('prev-page');
            const nextBtn = document.getElementById('next-page');

            const totalPages = Math.ceil(total / limit);

            if (totalPages <= 1) {
                container.style.display = 'none';
                return;
            }

            container.style.display = 'flex';
            pageInfo.textContent = `Page ${page} of ${totalPages} (${total} sessions)`;

            prevBtn.disabled = page <= 1;
            nextBtn.disabled = !hasNext;
        }

        // Load detailed session view
        function loadSessionDetail(sessionId) {
            fetch(`/api/chat_session/${sessionId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displaySessionDetail(data.session);
                    } else {
                        alert('Error loading session details: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error loading session detail:', error);
                    alert('Error loading session details');
                });
        }

        // Display detailed session view
        function displaySessionDetail(session) {
            const container = document.getElementById('session-detail');
            const title = document.getElementById('detail-title');
            const info = document.getElementById('session-info');
            const messages = document.getElementById('session-messages');

            title.textContent = session.title || 'Untitled Session';

            info.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div><strong>Platform:</strong> ${session.platform}</div>
                    <div><strong>Status:</strong> ${session.status}</div>
                    <div><strong>Started:</strong> ${new Date(session.start_time).toLocaleString()}</div>
                    <div><strong>Ended:</strong> ${session.end_time ? new Date(session.end_time).toLocaleString() : 'Still active'}</div>
                    <div><strong>Messages:</strong> ${session.total_messages}</div>
                    <div><strong>Conversation ID:</strong> ${session.conversation_id || 'N/A'}</div>
                </div>
            `;

            if (session.messages && session.messages.length > 0) {
                messages.innerHTML = `
                    <h4>Messages (${session.messages.length})</h4>
                    ${session.messages.map(msg => `
                        <div class="message-card ${msg.role}">
                            <div class="message-header">
                                <div class="message-role">${msg.role}</div>
                                <div>${new Date(msg.timestamp).toLocaleString()}</div>
                            </div>
                            <div class="message-content">${msg.content}</div>
                            <div style="margin-top: 10px; font-size: 12px; color: #6c757d;">
                                Echo: ${msg.echo_value ? msg.echo_value.toFixed(3) : 'N/A'} |
                                Salience: ${msg.salience ? msg.salience.toFixed(3) : 'N/A'}
                            </div>
                        </div>
                    `).join('')}
                `;
            } else {
                messages.innerHTML = '<h4>No messages in this session</h4>';
            }

            container.style.display = 'block';
            container.scrollIntoView({ behavior: 'smooth' });
        }

        // Close session detail view
        function closeSessionDetail() {
            document.getElementById('session-detail').style.display = 'none';
        }

        // Load chat statistics
        function loadChatStatistics() {
            fetch('/api/chat_statistics')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const stats = data.statistics;
                        document.getElementById('total-sessions').textContent = stats.total_sessions || 0;
                        document.getElementById('total-messages').textContent = stats.total_messages || 0;
                        document.getElementById('avg-session-length').textContent =
                            stats.avg_session_length ? `${stats.avg_session_length.toFixed(1)} messages` : 'N/A';
                        document.getElementById('active-platforms').textContent =
                            stats.platforms_used ? stats.platforms_used.join(', ') : 'None';
                    } else {
                        console.log('Chat statistics not available:', data.error);
                    }
                })
                .catch(error => {
                    console.error('Error loading chat statistics:', error);
                });
        }

        // Setup chat session event handlers
        function setupChatSessionHandlers() {
            // Apply filters button
            document.getElementById('apply-filters').addEventListener('click', () => {
                const filters = {
                    platform: document.getElementById('platform-filter').value,
                    days: document.getElementById('days-filter').value,
                    search: document.getElementById('search-filter').value
                };
                loadSessions(1, filters);
            });

            // Search on Enter key
            document.getElementById('search-filter').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    document.getElementById('apply-filters').click();
                }
            });
        }

        // Initialize everything
        function initialize() {
            updateCurrentTime();
            updateSystemMetrics();
            updateNetworkMetrics();
            updateSystemLogs();
            updateRecentEvents();
            updateHeartbeatMetrics();
            updateCharts();
            setupHeartbeatControls();
            setupChatSessionHandlers();

            // Update time every second
            setInterval(updateCurrentTime, 1000);

            // Update metrics periodically
            setInterval(updateSystemMetrics, 5000);
            setInterval(updateNetworkMetrics, 5000);
            setInterval(updateSystemLogs, 10000);
            setInterval(updateRecentEvents, 5000);
            setInterval(updateHeartbeatMetrics, 3000);
            setInterval(updateCharts, 30000);
        }

        // Run initialization when page loads
        window.addEventListener('load', initialize);
    </script>
</body>
</html>
'''

def parse_arguments():
    """Parse command line arguments for the web GUI application."""
    parser = argparse.ArgumentParser(description="Web-based GUI Dashboard for Deep Tree Echo")
    parser.add_argument("--port", type=int, default=8080,
                        help="Port to run the web server on (default: 8080)")
    parser.add_argument("--debug", action="store_true", help="Run Flask in debug mode")
    parser.add_argument("--no-activity", action="store_true",
                        help="Disable activity monitoring system")
    return parser.parse_args()

def get_system_metrics():
    """Get current system metrics (CPU, memory, disk)"""
    try:
        # Get system metrics
        if PSUTIL_AVAILABLE:
            cpu = psutil.cpu_percent(interval=None)
            memory_usage = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
        else:
            # Provide dummy data when psutil is not available
            cpu = 25.0
            memory_usage = 35.0
            disk = 45.0

        # Try to get echo metrics if Deep Tree Echo is available
        echo_metrics = {}
        try:
            if DeepTreeEcho and hasattr(DeepTreeEcho, 'get_instance'):
                # Singleton pattern
                echo = DeepTreeEcho.get_instance()
                echo_metrics = echo.analyze_echo_patterns()
        except (ImportError, AttributeError) as e:
            logger.warning("Error getting echo metrics: %s", str(e))

        return {
            'cpu': cpu,
            'memory': memory_usage,
            'disk': disk,
            'echo_metrics': echo_metrics
        }
    except (OSError, IOError, ValueError) as e:
        logger.error("Error getting system metrics: %s", str(e))
        return {'cpu': 0, 'memory': 0, 'disk': 0}

def get_memory_stats():
    """Get memory system statistics"""
    try:
        if MEMORY is None:
            return {'node_count': 0, 'edge_count': 0, 'avg_salience': 0.0}

        return MEMORY.generate_statistics()
    except (AttributeError, TypeError) as e:
        logger.error("Error getting memory stats: %s", str(e))
        return {'error': str(e)}

def get_recent_logs(max_logs=50):
    """Get recent activity logs from all components"""
    logs = []
    try:
        logs_dir = Path('activity_logs')
        if not logs_dir.exists():
            return {'logs': []}

        for component in logs_dir.iterdir():
            if component.is_dir():
                activity_file = component / 'activity.json'
                if activity_file.exists():
                    try:
                        with open(activity_file, encoding='utf-8') as f:
                            component_logs = json.load(f)
                            logs.extend(component_logs)
                    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
                        logger.error("Error reading logs from %s: %s", activity_file, str(e))

        # Sort by timestamp, newest first
        logs.sort(key=lambda x: x.get('time', 0), reverse=True)

        # Limit to max_logs
        logs = logs[:max_logs]

        return {'logs': logs}
    except (OSError, IOError, json.JSONDecodeError) as e:
        logger.error("Error getting logs: %s", str(e))
        return {'logs': []}

def _generate_system_history_data():
    """Generate system history data for charts."""
    if PSUTIL_AVAILABLE and NUMPY_AVAILABLE:
        return {
            'timestamps': [time.time() - i * 60 for i in range(30, 0, -1)],
            'cpu': [psutil.cpu_percent() * 0.8 + 10 * np.sin(i/3) for i in range(30)],
            'memory': [psutil.virtual_memory().percent * 0.7 +
                      15 * np.sin(i/5 + 2) for i in range(30)]
        }
    else:
        # Dummy data when dependencies are not available
        import math
        return {
            'timestamps': [time.time() - i * 60 for i in range(30, 0, -1)],
            'cpu': [25.0 + 10 * math.sin(i/3) for i in range(30)],
            'memory': [35.0 + 15 * math.sin(i/5 + 2) for i in range(30)]
        }

def _configure_chart_appearance(fig, ax):
    """Configure chart appearance with consistent styling."""
    fig.patch.set_facecolor('#272741')
    ax.set_facecolor('#323250')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.tick_params(axis='x', colors='white', rotation=45)
    ax.tick_params(axis='y', colors='white')
    ax.set_ylim(0, 100)
    ax.legend(loc='upper left', facecolor='#272741', framealpha=0.8, labelcolor='white')

def generate_system_health_chart():
    """Generate chart showing system health over time"""
    if not MATPLOTLIB_AVAILABLE:
        return generate_error_image("Matplotlib not available")

    try:
        history = _generate_system_history_data()

        fig, ax = plt.subplots(figsize=(10, 6))
        _configure_chart_appearance(fig, ax)

        # Format timestamps as readable time
        labels = [time.strftime("%H:%M", time.localtime(t)) for t in history['timestamps']]

        # Plot data
        ax.plot(labels, history['cpu'], 'o-', color='#4f9cff', label='CPU Usage (%)')
        ax.plot(labels, history['memory'], 's-', color='#ff6e4a', label='Memory Usage (%)')

        # Set labels and title
        ax.set_xlabel('Time', color='white')
        ax.set_ylabel('Usage (%)', color='white')
        ax.set_title('System Resource Usage Over Time', color='white', fontsize=14)

        plt.tight_layout()

        # Convert plot to image
        img_data = io.BytesIO()
        plt.savefig(img_data, format='png', dpi=100)
        img_data.seek(0)
        plt.close(fig)

        return img_data
    except (ValueError, KeyError, AttributeError, ImportError) as e:
        logger.error("Error generating system health chart: %s", str(e))
        # Return a simple error image
        return generate_error_image("Error generating system health chart")

def generate_echo_history_chart():
    """Generate chart showing echo patterns over time"""
    if not MATPLOTLIB_AVAILABLE:
        return generate_error_image("Matplotlib not available")

    try:
        # Placeholder echo history data
        history = {
            'timestamps': [time.time() - i * 60 for i in range(30, 0, -1)],
            'avg_echo': [0.4 + 0.2 * np.sin(i/5) for i in range(30)],
            'max_echo': [0.7 + 0.15 * np.sin(i/4 + 1) for i in range(30)],
            'resonant_nodes': [10 + 5 * np.sin(i/6 + 2) for i in range(30)]
        }

        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#272741')
        ax.set_facecolor('#323250')

        # Format timestamps as readable time
        labels = [time.strftime("%H:%M", time.localtime(t)) for t in history['timestamps']]

        # Plot echo values
        ax.plot(labels, history['avg_echo'], 'o-', color='#4f9cff', label='Avg Echo')
        ax.plot(labels, history['max_echo'], 's-', color='#9c4fff', label='Max Echo')

        # Create secondary y-axis for resonant nodes
        ax2 = ax.twinx()
        ax2.plot(labels, history['resonant_nodes'], '^-', color='#ff6e4a', label='Resonant Nodes')

        # Set labels and title
        ax.set_xlabel('Time', color='white')
        ax.set_ylabel('Echo Value', color='#4f9cff')
        ax2.set_ylabel('Node Count', color='#ff6e4a')
        ax.set_title('Echo Patterns Over Time', color='white', fontsize=14)

        # Customize ticks and grid
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.tick_params(axis='x', colors='white', rotation=45)
        ax.tick_params(axis='y', colors='#4f9cff')
        ax2.tick_params(axis='y', colors='#ff6e4a')

        # Customize limits
        ax.set_ylim(0, 1)

        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left',
                 facecolor='#272741', framealpha=0.8, labelcolor='white')

        plt.tight_layout()

        # Convert plot to image
        img_data = io.BytesIO()
        plt.savefig(img_data, format='png', dpi=100)
        img_data.seek(0)
        plt.close(fig)

        return img_data
    except (ValueError, KeyError, AttributeError, ImportError) as e:
        logger.error("Error generating echo history chart: %s", str(e))
        return generate_error_image("Error generating echo history chart")

def generate_memory_graph():
    """Generate visualization of the memory system"""
    if not MATPLOTLIB_AVAILABLE or not NETWORKX_AVAILABLE:
        return generate_error_image("Matplotlib or NetworkX not available")

    try:
        # Create a sample memory graph if we don't have real data
        graph_instance = nx.DiGraph()

        # If we have a real memory system, use its data
        if MEMORY is not None:
            # Add nodes from memory system (limit to 100 for performance)
            nodes = list(MEMORY.nodes.items())[:100]
            for node_id, node in nodes:
                graph_instance.add_node(node_id,
                         content=node.content[:50],
                         salience=getattr(node, 'salience', 0.5),
                         memory_type=str(getattr(node, 'memory_type', 'unknown')),
                         size=300 + 700 * getattr(node, 'salience', 0.5))

            # Add edges between these nodes
            for edge in MEMORY.edges:
                if edge.from_id in graph_instance and edge.to_id in graph_instance:
                    graph_instance.add_edge(edge.from_id, edge.to_id,
                             weight=edge.weight)
        else:
            # Generate a random memory graph for demonstration
            for i in range(30):
                node_id = f"node_{i}"
                memory_types = ['episodic', 'semantic', 'procedural', 'working']
                graph_instance.add_node(node_id,
                         content=f"Memory node {i}",
                         salience=np.random.uniform(0.3, 0.9),
                         memory_type=np.random.choice(memory_types),
                         size=300 + 700 * np.random.uniform(0.3, 0.9))

            # Add some random edges
            for i in range(50):
                from_id = f"node_{np.random.randint(0, 30)}"
                to_id = f"node_{np.random.randint(0, 30)}"
                if from_id != to_id:
                    graph_instance.add_edge(from_id, to_id, weight=np.random.uniform(0.3, 0.9))

        # Create visualization
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('#272741')
        ax.set_facecolor('#272741')

        # Define node positions using a layout algorithm
        pos = nx.spring_layout(graph_instance)

        # Get node attributes for visualization
        node_sizes = [data.get('size', 300) for _, data in graph_instance.nodes(data=True)]

        # Color nodes by memory type
        memory_types = [data.get('memory_type', 'unknown')
                       for _, data in graph_instance.nodes(data=True)]
        unique_types = list(set(memory_types))
        color_map = plt.cm.get_cmap('tab10', len(unique_types))
        type_to_color = {t: color_map(i) for i, t in enumerate(unique_types)}
        node_colors = [type_to_color[t] for t in memory_types]

        # Draw nodes
        nodes = nx.draw_networkx_nodes(graph_instance, pos,
                                     node_size=node_sizes,
                                     node_color=node_colors,
                                     alpha=0.8, ax=ax)

        # Draw edges with color based on weight
        edge_weights = [graph_instance[u][v].get('weight', 0.5) for u, v in graph_instance.edges()]
        nx.draw_networkx_edges(graph_instance, pos,
                             edge_color=edge_weights,
                             edge_cmap=plt.cm.Blues,
                             width=1.5,
                             alpha=0.6,
                             arrows=True,
                             ax=ax,
                             arrowsize=10)

        # Create legend for memory types
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w',
                                    label=t, markerfacecolor=type_to_color[t], markersize=8)
                         for t in unique_types]
        ax.legend(handles=legend_elements, title="Memory Types",
                 loc="upper right", framealpha=0.8,
                 facecolor='#272741', labelcolor='white')

        # Add title and remove axis
        ax.set_title("Memory Hypergraph Visualization", color='white', fontsize=16)
        ax.set_axis_off()

        plt.tight_layout()

        # Convert plot to image
        img_data = io.BytesIO()
        plt.savefig(img_data, format='png', dpi=100)
        img_data.seek(0)
        plt.close(fig)

        return img_data
    except (ValueError, KeyError, AttributeError, ImportError, OSError) as e:
        logger.error("Error generating memory graph: %s", str(e))
        return generate_error_image("Error generating memory graph")

def generate_echo_network():
    """Generate visualization of the echo network"""
    try:
        # Create a network representation of the echo tree
        echo_graph = nx.DiGraph()

        # Try to get the actual echo tree
        try:
            if DeepTreeEcho:
                echo = (DeepTreeEcho() if not hasattr(DeepTreeEcho, 'get_instance')
                       else DeepTreeEcho.get_instance())
                root_node = echo.root

            # If we have a real tree, use it
            if root_node:
                # Helper to add nodes recursively
                def add_node_to_graph(node, parent_id=None):
                    node_id = id(node)
                    echo_graph.add_node(node_id,
                             echo_value=getattr(node, 'echo_value', 0.5),
                             content=getattr(node, 'content', 'Unknown'),
                             size=300 + 1000 * getattr(node, 'echo_value', 0.5))

                    if parent_id is not None:
                        echo_graph.add_edge(parent_id, node_id)

                    for child in getattr(node, 'children', []):
                        add_node_to_graph(child, node_id)

                # Add all nodes starting from root
                add_node_to_graph(root_node)
        except (ImportError, AttributeError, KeyError) as e:
            logger.warning("Could not get real echo tree, generating demo: %s", str(e))

            # If no real tree, generate a demo one
            if len(echo_graph.nodes()) == 0:
                # Create a demo tree structure
                for i in range(20):
                    echo_graph.add_node(i,
                             echo_value=np.random.uniform(0.2, 0.9),
                             content=f"Node {i}",
                             size=300 + 1000 * np.random.uniform(0.2, 0.9))

                # Create a tree-like structure
                for i in range(1, 20):
                    parent = (i - 1) // 3  # Simple formula to create a tree
                    echo_graph.add_edge(parent, i)

        # Create visualization
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor('#272741')
        ax.set_facecolor('#272741')

        if not echo_graph.nodes():
            ax.text(0.5, 0.5, "No echo network data available",
                   ha='center', va='center', color='white', fontsize=14)
            ax.set_axis_off()
        else:
            # Define node positions using a layout algorithm
            pos = nx.kamada_kawai_layout(echo_graph)

            # Get node attributes for visualization
            node_sizes = [data.get('size', 300) for _, data in echo_graph.nodes(data=True)]
            echo_values = [data.get('echo_value', 0.5) for _, data in echo_graph.nodes(data=True)]

            # Create a colormap
            cmap = plt.cm.viridis
            norm = plt.Normalize(vmin=0, vmax=1)

            # Draw nodes
            nx.draw_networkx_nodes(echo_graph, pos,
                                   node_size=node_sizes,
                                   node_color=echo_values,
                                   cmap=cmap,
                                   alpha=0.9, ax=ax)

            # Draw edges
            nx.draw_networkx_edges(echo_graph, pos,
                                 edge_color='gray',
                                 alpha=0.5,
                                 arrows=True,
                                 arrowsize=10,
                                 ax=ax)

            # Add colorbar
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, label='Echo Value')
            cbar.ax.yaxis.label.set_color('white')
            cbar.ax.tick_params(colors='white')

            # Add title and remove axis
            ax.set_title("Deep Tree Echo Visualization", color='white', fontsize=16)
            ax.set_axis_off()

        plt.tight_layout()

        # Convert plot to image
        img_data = io.BytesIO()
        plt.savefig(img_data, format='png', dpi=100)
        img_data.seek(0)
        plt.close(fig)

        return img_data
    except (ValueError, KeyError, AttributeError, ImportError, OSError) as e:
        logger.error("Error generating echo network: %s", str(e))
        return generate_error_image("Error generating echo network visualization")

def generate_error_image(error_text):
    """Generate a simple error image with text"""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#272741')
    ax.set_facecolor('#272741')

    ax.text(0.5, 0.5, error_text, ha='center', va='center', color='white', fontsize=14)
    ax.set_axis_off()

    plt.tight_layout()

    # Convert plot to image
    img_data = io.BytesIO()
    plt.savefig(img_data, format='png', dpi=100)
    img_data.seek(0)
    plt.close(fig)

    return img_data

@app.route('/api/heartbeat_metrics')
def heartbeat_metrics():
    """Return the current metrics from the adaptive heartbeat system"""
    if not HEARTBEAT_SYSTEM:
        return jsonify({
            'current_rate': 60,
            'hyper_drive': False,
            'cpu_usage': 0,
            'health_status': 'Unknown',
            'recent_logs': [],
            'error': 'Heartbeat system not available'
        })
    
    current_rate = HEARTBEAT_SYSTEM.current_heartbeat_rate
    hyper_drive = HEARTBEAT_SYSTEM.hyper_drive_active
    cpu_usage = HEARTBEAT_SYSTEM.last_cpu_usage

    # Determine health status based on heartbeat and CPU usage
    if hyper_drive:
        health_status = "Warning"
    elif cpu_usage > 80:
        health_status = "Warning"
    elif cpu_usage > 95:
        health_status = "Critical"
    else:
        health_status = "Good"

    # Get recent logs (limited to last 10)
    recent_logs = HEARTBEAT_LOGS[-10:] if HEARTBEAT_LOGS else []

    return jsonify({
        'current_rate': current_rate,
        'hyper_drive': hyper_drive,
        'cpu_usage': cpu_usage,
        'health_status': health_status,
        'recent_logs': recent_logs
    })

@app.route('/api/update_heartbeat_rate')
def update_heartbeat_rate():
    """Update the base heartbeat rate"""
    if not HEARTBEAT_SYSTEM:
        return jsonify({'success': False, 'message': 'Heartbeat system not available'})
    
    try:
        value = int(request.args.get('value', 60))
        HEARTBEAT_SYSTEM.base_heartbeat_rate = value
        log_heartbeat_event("Base heartbeat rate updated to %d BPM" % value)
        return jsonify({'success': True, 'message': 'Heartbeat rate updated to %d' % value})
    except (ValueError, TypeError) as e:
        logger.error("Error updating heartbeat rate: %s", str(e))
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/update_hyper_threshold')
def update_hyper_threshold():
    """Update the hyper drive threshold"""
    if not HEARTBEAT_SYSTEM:
        return jsonify({'success': False, 'message': 'Heartbeat system not available'})
    
    try:
        value = int(request.args.get('value', 90))
        HEARTBEAT_SYSTEM.hyper_drive_threshold = value
        log_heartbeat_event("Hyper drive threshold updated to %d%%" % value)
        return jsonify({'success': True, 'message': 'Threshold updated to %d%%' % value})
    except (ValueError, TypeError) as e:
        logger.error("Error updating hyper drive threshold: %s", str(e))
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/toggle_hyper_drive')
def toggle_hyper_drive():
    """Toggle the hyper drive mode"""
    if not HEARTBEAT_SYSTEM:
        return jsonify({'success': False, 'message': 'Heartbeat system not available'})
    
    try:
        new_state = not HEARTBEAT_SYSTEM.hyper_drive_active
        HEARTBEAT_SYSTEM.hyper_drive_active = new_state
        log_heartbeat_event("Hyper drive manually %s" % ('activated' if new_state else 'deactivated'))
        return jsonify({'success': True,
                       'message': 'Hyper drive %s' % ("activated" if new_state else "deactivated")})
    except (AttributeError, ValueError) as e:
        logger.error("Error toggling hyper drive: %s", str(e))
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/force_heartbeat_assessment')
def force_heartbeat_assessment():
    """Force the heartbeat system to perform a full assessment"""
    try:
        HEARTBEAT_SYSTEM.assess_system_state(force=True)
        log_heartbeat_event("Manual system assessment triggered")
        return jsonify({'success': True, 'message': 'Assessment completed'})
    except (AttributeError, ValueError) as e:
        logger.error("Error during system assessment: %s", str(e))
        return jsonify({'success': False, 'message': 'An internal error occurred.'})

@app.route('/api/restart_heartbeat')
def restart_heartbeat():
    """Restart the heartbeat system"""
    try:
        # Stop the current thread if it exists
        if HEARTBEAT_THREAD and HEARTBEAT_THREAD.is_alive():
            HEARTBEAT_SYSTEM.stop_heartbeat()
            HEARTBEAT_THREAD.join(timeout=2.0)

        # Reset and restart
        HEARTBEAT_SYSTEM.reset()
        start_heartbeat_thread()

        log_heartbeat_event("Heartbeat system restarted")
        return jsonify({'success': True, 'message': 'Heartbeat system restarted'})
    except (AttributeError, ImportError, ValueError) as e:
        logger.error("Error restarting heartbeat system: %s", str(e))
        return jsonify({'success': False, 'message': str(e)})

@app.route('/chart/heartbeat_history')
def heartbeat_history_chart():
    """Generate a chart showing heartbeat rate history"""
    try:
        plt.figure(figsize=(10, 4))
        plt.plot(SYSTEM_HISTORY['timestamps'][-50:],
                SYSTEM_HISTORY['heartbeat'][-50:], 'r-', linewidth=2)

        # Add visual indicators for hyper drive periods if available
        hyper_periods = HEARTBEAT_SYSTEM.get_hyper_drive_periods()
        if hyper_periods:
            for period in hyper_periods[-5:]:  # Show last 5 periods
                start, end = period
                if end == 0:  # Still active
                    end = datetime.now()
                plt.axvspan(start, end, color='yellow', alpha=0.3)

        plt.title('Heartbeat Rate History')
        plt.xlabel('Time')
        plt.ylabel('Rate (BPM)')
        plt.grid(True)
        plt.tight_layout()

        # Convert plot to PNG image
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        return Response(img.getvalue(), content_type='image/png')
    except (ImportError, AttributeError, ValueError) as e:
        logger.error("Error generating heartbeat chart: %s", str(e))
        # Return a simple error image
        return Response(generate_error_image("Error generating chart").getvalue(), content_type='image/png')

def log_heartbeat_event(message):
    """Log a heartbeat event with timestamp."""
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'message': message
    }
    HEARTBEAT_LOGS.append(log_entry)
    # Keep only the last 100 logs
    if len(HEARTBEAT_LOGS) > 100:
        HEARTBEAT_LOGS.pop(0)
    logger.info("Heartbeat event: %s", message)

def update_metrics():
    """Update system metrics for historical tracking continuously."""
    while True:
        try:
            if not PSUTIL_AVAILABLE:
                # If psutil is not available, use dummy data
                cpu_percent = 25.0
                memory_percent = 35.0
                disk_percent = 45.0
                net_usage = 10.0
            else:
                # Get current system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent

                # Get network stats (simplified)
                net_io = psutil.net_io_counters()
                net_usage = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024  # Convert to MB

            # Get current timestamp
            current_time = datetime.now()

            # Store in history
            SYSTEM_HISTORY['cpu'].append(cpu_percent)
            SYSTEM_HISTORY['memory'].append(memory_percent)
            SYSTEM_HISTORY['disk'].append(disk_percent)
            SYSTEM_HISTORY['network'].append(net_usage)
            SYSTEM_HISTORY['timestamps'].append(current_time)

            # Add heartbeat data
            if HEARTBEAT_SYSTEM:
                SYSTEM_HISTORY['heartbeat'].append(HEARTBEAT_SYSTEM.current_heartbeat_rate)
            else:
                SYSTEM_HISTORY['heartbeat'].append(60.0)  # Default heartbeat

            # Keep only the last 1000 data points to prevent memory issues
            if len(SYSTEM_HISTORY['cpu']) > 1000:
                for key in SYSTEM_HISTORY:
                    SYSTEM_HISTORY[key] = SYSTEM_HISTORY[key][-1000:]

            # Sleep for a bit
            time.sleep(2)
        except (OSError, IOError, AttributeError) as e:
            logger.error("Error in update_metrics: %s", str(e))
            time.sleep(5)  # Wait a bit longer if there was an error

# Flask routes - only define if Flask is available
@app.route('/')
def index():
    """Serve the main dashboard HTML page."""
    return HTML_TEMPLATE

@app.route('/api/system_metrics')
def api_system_metrics():
    """API endpoint to get current system metrics."""
    try:
        metrics = get_system_metrics()
        if PSUTIL_AVAILABLE:
            # Add additional metrics
            metrics.update({
                'cpu_cores': psutil.cpu_count(),
                'memory_used': _format_bytes(psutil.virtual_memory().used),
                'memory_available': _format_bytes(psutil.virtual_memory().available),
                'memory_total': _format_bytes(psutil.virtual_memory().total),
                'disk_used': _format_bytes(psutil.disk_usage('/').used),
                'disk_free': _format_bytes(psutil.disk_usage('/').free),
                'disk_total': _format_bytes(psutil.disk_usage('/').total),
                'uptime': _format_uptime(time.time() - psutil.boot_time()),
                'processes': _get_top_processes()
            })
        else:
            # Fallback values when psutil is not available
            metrics.update({
                'cpu_cores': 'Unknown',
                'memory_used': 'Unknown',
                'memory_available': 'Unknown',
                'memory_total': 'Unknown',
                'disk_used': 'Unknown',
                'disk_free': 'Unknown',
                'disk_total': 'Unknown',
                'uptime': 'Unknown',
                'processes': []
            })
        return jsonify(metrics)
    except (OSError, IOError) as e:
        logger.error("Error getting system metrics: %s", str(e))
        return jsonify({'error': str(e)})

def _format_bytes(bytes_value):
    """Format bytes value to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def _format_uptime(seconds):
    """Format uptime seconds to human readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{days}d {hours}h {minutes}m"

def _get_top_processes():
    """Get top processes by CPU usage."""
    if not PSUTIL_AVAILABLE:
        return []
    
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'][:20],  # Limit name length
                    'cpu': round(proc.info['cpu_percent'], 1),
                    'memory': round(proc.info['memory_percent'], 1),
                    'status': proc.info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        # Sort by CPU usage, highest first, limit to top 10
        return sorted(processes, key=lambda p: p['cpu'], reverse=True)[:10]
    except (OSError, IOError):
        return []

@app.route('/api/memory_stats')
def api_memory_stats():
    """API endpoint to get memory system statistics."""
    return jsonify({'stats': get_memory_stats()})

@app.route('/api/recent_logs')
def api_recent_logs():
    """API endpoint to get recent activity logs."""
    return jsonify(get_recent_logs())

@app.route('/api/system_logs')
def api_system_logs():
    """API endpoint to get system logs."""
    try:
        logs = []
        log_data = get_recent_logs()
        for log_entry in log_data.get('logs', [])[:50]:  # Limit to 50 recent logs
            logs.append({
                'timestamp': log_entry.get('time', 'Unknown'),
                'message': log_entry.get('activity', 'No message')
            })
        return jsonify({'logs': logs})
    except (KeyError, TypeError) as e:
        logger.error("Error getting system logs: %s", str(e))
        return jsonify({'logs': []})

@app.route('/api/recent_events')
def api_recent_events():
    """API endpoint to get recent events."""
    try:
        # Get recent system events 
        events = []
        if HEARTBEAT_LOGS:
            for log in HEARTBEAT_LOGS[-5:]:  # Last 5 heartbeat events
                events.append({
                    'timestamp': log.get('timestamp', 'Unknown'),
                    'message': log.get('message', 'No message')
                })
        return jsonify({'events': events})
    except (KeyError, TypeError) as e:
        logger.error("Error getting recent events: %s", str(e))
        return jsonify({'events': []})

@app.route('/api/network_metrics')
def api_network_metrics():
    """API endpoint to get network metrics."""
    try:
        if not PSUTIL_AVAILABLE:
            return jsonify({
                'sent': 'Unknown',
                'received': 'Unknown',
                'connections': 0,
                'connection_list': [],
                'error': 'psutil not available'
            })
        
        net_io = psutil.net_io_counters()
        connections = psutil.net_connections()
        
        # Format network data
        sent_mb = net_io.bytes_sent / (1024 * 1024)
        received_mb = net_io.bytes_recv / (1024 * 1024)
        
        # Get connection list (limit to 20 for performance)
        connection_list = []
        for conn in connections[:20]:
            try:
                connection_list.append({
                    'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "Unknown",
                    'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "Unknown",
                    'status': conn.status,
                    'type': conn.type.name if hasattr(conn.type, 'name') else str(conn.type)
                })
            except (AttributeError, ValueError):
                pass
        
        return jsonify({
            'sent': f"{sent_mb:.1f} MB",
            'received': f"{received_mb:.1f} MB", 
            'connections': len(connections),
            'connection_list': connection_list
        })
    except (OSError, IOError, AttributeError) as e:
        logger.error("Error getting network metrics: %s", str(e))
        return jsonify({
            'sent': 'Error',
            'received': 'Error',
            'connections': 0,
            'connection_list': [],
            'error': str(e)
        })

@app.route('/api/process_info')
def api_process_info():
    """API endpoint to get current process information."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'cpu_percent': proc.info['cpu_percent'],
                'memory_percent': proc.info['memory_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Sort by CPU usage, highest first
    processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)[:10]
    return jsonify({'processes': processes})

@app.route('/api/tasks')
def api_tasks():
    """API endpoint to get current task queue."""
    try:
        tasks = []
        if ACTIVITY_REGULATOR:
            # Convert queue to list for viewing
            queue_copy = []
            for task in list(ACTIVITY_REGULATOR.task_queue.queue):
                queue_copy.append({
                    'task_id': task.task_id,
                    'priority': (task.priority.name if hasattr(task.priority, 'name')
                                else str(task.priority)),
                    'scheduled_time': task.scheduled_time
                })
            tasks = queue_copy
        return jsonify({'tasks': tasks})
    except Exception as e:
        logger.error("Error getting tasks: %s", str(e))
        return jsonify({'tasks': [], 'error': str(e)})

@app.route('/api/add_task')
def api_add_task():
    """API endpoint to add a new task to the queue."""
    try:
        task_id = request.args.get('task_id', '')
        if not task_id or not ACTIVITY_REGULATOR:
            return jsonify({'success': False,
                       'error': 'Invalid task ID or activity regulator not available'})

        if TaskPriority:
            ACTIVITY_REGULATOR.add_task(
                task_id=task_id,
                callback=lambda: print(f"Executing {task_id}"),
                priority=TaskPriority.MEDIUM
            )
        return jsonify({'success': True})
    except Exception as e:
        logger.error("Error adding task: %s", str(e))
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update_echo_threshold')
def api_update_echo_threshold():
    """API endpoint to update the echo threshold value."""
    try:
        value = float(request.args.get('value', 0.75))

        try:
            if DeepTreeEcho:
                echo = (DeepTreeEcho() if not hasattr(DeepTreeEcho, 'get_instance')
                       else DeepTreeEcho.get_instance())
                echo.echo_threshold = value
        except Exception as e:
            logger.warning("Could not update echo threshold: %s", str(e))

        return jsonify({'success': True, 'value': value})
    except Exception as e:
        logger.error("Error updating threshold: %s", str(e))
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/inject_random_echo')
def api_inject_random_echo():
    """API endpoint to inject a random echo into the system."""
    try:
        echo = None
        try:
            if DeepTreeEcho:
                echo = (DeepTreeEcho() if not hasattr(DeepTreeEcho, 'get_instance')
                       else DeepTreeEcho.get_instance())
        except (ImportError, AttributeError) as e:
            logger.warning("Error initializing DeepTreeEcho: %s", str(e))

        # Find random nodes to use
        if echo:
            all_nodes = []

            def collect_nodes(node):
                if node:
                    all_nodes.append(node)
                    for child in getattr(node, 'children', []):
                        collect_nodes(child)

            # Collect all nodes
            collect_nodes(echo.root)

            if len(all_nodes) > 1:
                source = random.choice(all_nodes)
                target = random.choice(all_nodes)
                while source == target:
                    target = random.choice(all_nodes)

                strength = random.uniform(0.3, 0.9)
                echo.inject_echo(source, target, strength)
                return jsonify({'success': True})

        return jsonify({'success': False, 'error': 'Echo system not available'})
    except Exception as e:
        logger.error("Error in inject_random_echo: %s", str(e))
        return jsonify({'success': False, 'error': str(e)})
@app.route('/api/propagate_echoes')
def api_propagate_echoes():
    """API endpoint to propagate echoes through the system."""
    try:
        try:
            if DeepTreeEcho:
                echo = (DeepTreeEcho() if not hasattr(DeepTreeEcho, 'get_instance')
                       else DeepTreeEcho.get_instance())
                echo.propagate_echoes()
                return jsonify({'success': True})
        except Exception as e:
            logger.warning("Could not propagate echoes: %s", str(e))

        return jsonify({'success': False, 'error': 'Echo system not available'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/prune_weak_echoes')
def api_prune_weak_echoes():
    """API endpoint to prune weak echoes from the system."""
    try:
        try:
            if DeepTreeEcho:
                echo = (DeepTreeEcho() if not hasattr(DeepTreeEcho, 'get_instance')
                       else DeepTreeEcho.get_instance())
                echo.prune_weak_echoes()
                return jsonify({'success': True})
        except Exception as e:
            logger.warning("Could not prune weak echoes: %s", str(e))

        return jsonify({'success': False, 'error': 'Echo system not available'})
    except Exception as e:
        logger.error("Error in prune_weak_echoes: %s", str(e))
        return jsonify({'success': False, 'error': str(e)})

# Chat Session Management API Endpoints
@app.route('/api/chat_sessions')
def api_chat_sessions():
    """Get list of saved chat sessions with pagination and filtering"""
    try:
        sessions = []
        try:
            if session_manager:
                # Get query parameters
                page = int(request.args.get('page', 1))
                limit = int(request.args.get('limit', 20))
                platform = request.args.get('platform')
                days = int(request.args.get('days', 30))

                # Search sessions
                sessions = session_manager.search_sessions(
                    platform=platform,
                    limit=limit * page,  # Get enough for pagination
                    start_date=datetime.now() - timedelta(days=days)
                )

            # Paginate
            start = (page - 1) * limit
            end = start + limit
            paginated_sessions = sessions[start:end]

            return jsonify({
                'success': True,
                'sessions': paginated_sessions,
                'total': len(sessions),
                'page': page,
                'limit': limit,
                'has_next': end < len(sessions)
            })

        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Chat session manager not available'
            })

    except Exception as e:
        logger.error("Error getting chat sessions: %s", str(e))
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chat_session/<session_id>')
def api_chat_session_detail(session_id):
    """Get detailed information for a specific chat session"""
    try:
        try:
            if session_manager:
                session = session_manager.get_session(session_id)
                if not session:
                    return jsonify({'success': False, 'error': 'Session not found'})

            # Convert to dict format suitable for JSON
            session_data = {
                'id': session.id,
                'platform': session.platform.value,
                'title': session.title,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'status': session.status.value,
                'total_messages': session.total_messages,
                'conversation_id': session.conversation_id,
                'metadata': session.metadata,
                'messages': []
            }

            # Add messages
            for msg in session.messages:
                session_data['messages'].append({
                    'id': msg.id,
                    'timestamp': msg.timestamp,
                    'role': msg.role,
                    'content': msg.content,
                    'echo_value': msg.echo_value,
                    'salience': msg.salience,
                    'metadata': msg.metadata
                })

            return jsonify({'success': True, 'session': session_data})

        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Chat session manager not available'
            })

    except Exception as e:
        logger.error("Error getting chat session detail: %s", str(e))
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chat_statistics')
def api_chat_statistics():
    """Get chat session statistics"""
    try:
        if session_manager:
            stats = session_manager.get_statistics()
            return jsonify({'success': True, 'statistics': stats})

        return jsonify({
            'success': False,
            'error': 'Chat session manager not available'
        })
    except Exception as e:
        logger.error("Error getting chat statistics: %s", str(e))
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chart/system_health')
def chart_system_health():
    """Generate and serve system health chart image."""
    img_data = generate_system_health_chart()
    return Response(img_data.getvalue(), mimetype='image/png')

@app.route('/chart/echo_history')
def chart_echo_history():
    """Generate and serve echo history chart image."""
    img_data = generate_echo_history_chart()
    return Response(img_data.getvalue(), mimetype='image/png')

@app.route('/chart/memory_graph')
def chart_memory_graph():
    """Generate and serve memory graph visualization image."""
    img_data = generate_memory_graph()
    return Response(img_data.getvalue(), mimetype='image/png')

@app.route('/chart/echo_network')
def chart_echo_network():
    """Generate and serve echo network visualization image."""
    img_data = generate_echo_network()
    return Response(img_data.getvalue(), mimetype='image/png')

@app.route('/chart/cpu_history')
def chart_cpu_history():
    """Generate CPU history chart."""
    return _generate_history_chart('cpu', 'CPU Usage (%)', '#4f9cff')

@app.route('/chart/memory_history') 
def chart_memory_history():
    """Generate memory history chart."""
    return _generate_history_chart('memory', 'Memory Usage (%)', '#ff6e4a')

@app.route('/chart/network_history')
def chart_network_history():
    """Generate network history chart."""
    return _generate_history_chart('network', 'Network Usage (MB)', '#9c4fff')

@app.route('/chart/system_overview')
def chart_system_overview():
    """Generate system overview chart."""
    img_data = generate_system_health_chart()
    return Response(img_data.getvalue(), mimetype='image/png')

def _generate_history_chart(metric_key, ylabel, color):
    """Generate a history chart for a specific metric."""
    try:
        if not MATPLOTLIB_AVAILABLE:
            return Response(generate_error_image("Matplotlib not available").getvalue(),
                          mimetype='image/png')
        
        fig, ax = plt.subplots(figsize=(10, 4))
        _configure_chart_appearance(fig, ax)
        
        # Get recent data
        recent_data = SYSTEM_HISTORY[metric_key][-50:] if SYSTEM_HISTORY[metric_key] else [0]
        recent_times = SYSTEM_HISTORY['timestamps'][-50:] if SYSTEM_HISTORY['timestamps'] else [datetime.now()]
        
        # Format timestamps
        time_labels = [t.strftime("%H:%M") for t in recent_times]
        
        ax.plot(time_labels, recent_data, '-', color=color, linewidth=2)
        ax.set_title(f'{ylabel} History')
        ax.set_xlabel('Time')
        ax.set_ylabel(ylabel)
        
        plt.tight_layout()
        
        # Convert plot to PNG image
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=100)
        img.seek(0)
        plt.close(fig)
        
        return Response(img.getvalue(), mimetype='image/png')
    except (ValueError, KeyError, AttributeError) as e:
        logger.error("Error generating %s chart: %s", metric_key, str(e))
        return Response(generate_error_image(f"Error generating {metric_key} chart").getvalue(),
                       mimetype='image/png')


def main():
    """Main function to initialize and run the web GUI server."""
    global MEMORY, ACTIVITY_REGULATOR

    if not FLASK_AVAILABLE:
        logger.error("Flask is not available. Cannot start web server.")
        print("Error: Flask is required but not available. Please install Flask.")
        return 1

    args = parse_arguments()

    try:
        # Initialize memory system
        logger.info("Initializing memory system")
        MEMORY = HypergraphMemory(storage_dir="echo_memory")

        # Only initialize activity regulator if not disabled
        if not args.no_activity:
            logger.info("Initializing activity regulator")
            if ActivityRegulator:
                ACTIVITY_REGULATOR = ActivityRegulator()

        # Start the heartbeat system
        start_heartbeat_thread()

        # Start the metrics update thread
        metrics_thread = threading.Thread(target=update_metrics, daemon=True)
        metrics_thread.start()
        # Print server information
        print("\n" + "="*80)
        print("Deep Tree Echo Dashboard Web Server")
        print(f"Running on http://localhost:{args.port}")
        print("Also try your forwarded port URLs:")
        print(f"- http://127.0.0.1:{args.port}")
        print(f"- http://localhost:{args.port}")
        print("="*80 + "\n")

        # Start Flask server
        app.run(host='0.0.0.0', port=args.port, debug=args.debug)

    except Exception as e:
        logger.error("Error in main: %s", str(e), exc_info=True)
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
