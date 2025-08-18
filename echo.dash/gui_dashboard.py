import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkintertable import TableCanvas, TableModel
from activity_regulation import ActivityRegulator
import threading
import psutil
import os
import json
import time
import csv
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import ttkbootstrap as ttkb
from ttkbootstrap import Style
from tooltip import Tooltip
import networkx as nx
from deep_tree_echo import DeepTreeEcho, TreeNode
from ml_system import MLSystem
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from memory_management import HypergraphMemory, MemoryType  # Import memory management
import logging
from datetime import datetime

class GUIDashboard:
    def __init__(self, root, memory=None, cognitive=None, personality=None, 
                 sensory=None, activity=None, emergency=None, browser=None, ai_manager=None):
        self.root = root
        self.style = Style(theme='cosmo')
        self.root.title("Deep Tree Echo Dashboard")
        self.root.geometry("1200x800")

        # Store subsystems
        self.memory_system = memory if memory else HypergraphMemory(storage_dir="echo_memory")
        self.cognitive = cognitive
        self.personality = personality
        self.sensory = sensory
        self.emergency = emergency
        self.browser = browser
        self.ai_manager = ai_manager

        self.activity_regulator = activity if activity else ActivityRegulator()
        self.activity_thread = threading.Thread(target=self.activity_regulator.run_sync, daemon=True)
        self.activity_thread.start()

        self.echo = DeepTreeEcho()
        self.root_node = self.echo.create_tree("Deep Tree Echo Root")
        self.ml_system = MLSystem()

        self.history = {
            'timestamps': [],
            'avg_echo': [],
            'max_echo': [],
            'resonant_nodes': [],
            'cpu': [],
            'memory': []
        }

        self.create_widgets()
        self.update_system_health()
        self.update_activity_logs()
        self.update_echo_visualization()
        self.update_heartbeat_monitor()

    def log_message(self, message, level="INFO"):
        """Log a message both to the log file and optionally to the GUI"""
        logger = logging.getLogger(__name__)
        
        # Log to the appropriate level
        if level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
        elif level == "DEBUG":
            logger.debug(message)
        
        # If we have a heartbeat log UI element, also log there
        if hasattr(self, 'heartbeat_log') and self.heartbeat_log is not None:
            try:
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.heartbeat_log.config(state="normal")
                self.heartbeat_log.insert(tk.END, f"[{timestamp}] {level}: {message}\n")
                self.heartbeat_log.see(tk.END)
                self.heartbeat_log.config(state="disabled")
            except Exception:
                # Don't let UI logging errors cascade
                pass

    def create_widgets(self):
        self.tab_control = ttkb.Notebook(self.root)

        self.dashboard_tab = ttkb.Frame(self.tab_control)
        self.tab_control.add(self.dashboard_tab, text="Dashboard")

        self.system_tab = ttkb.Frame(self.tab_control)
        self.tab_control.add(self.system_tab, text="System Health")

        self.logs_tab = ttkb.Frame(self.tab_control)
        self.tab_control.add(self.logs_tab, text="Activity Logs")

        self.tasks_tab = ttkb.Frame(self.tab_control)
        self.tab_control.add(self.tasks_tab, text="Task Management")
        
        self.heartbeat_tab = ttkb.Frame(self.tab_control)
        self.tab_control.add(self.heartbeat_tab, text="Heartbeat Monitor")

        self.echo_tab = ttkb.Frame(self.tab_control)
        self.tab_control.add(self.echo_tab, text="Echo Visualization")

        self.memory_tab = ttkb.Frame(self.tab_control)  # New memory visualization tab
        self.tab_control.add(self.memory_tab, text="Memory Explorer")

        self.cognitive_tab = ttkb.Frame(self.tab_control)  # Cognitive systems tab
        self.tab_control.add(self.cognitive_tab, text="Cognitive Systems")

        self.tab_control.pack(expand=1, fill="both")
        
        self.create_dashboard_tab()
        self.create_system_tab()
        self.create_logs_tab()
        self.create_tasks_tab()
        self.create_heartbeat_tab()  # Create the new heartbeat tab
        self.create_echo_tab()
        self.create_memory_tab()
        self.create_cognitive_tab()

    def create_dashboard_tab(self):
        self.dashboard_frame = ttkb.Frame(self.dashboard_tab, padding=(10, 10))
        self.dashboard_frame.pack(expand=1, fill="both")

        self.summary_label = ttkb.Label(self.dashboard_frame, text="System Summary", font=("Helvetica", 14, "bold"))
        self.summary_label.pack(pady=10)

        self.summary_text = tk.Text(self.dashboard_frame, wrap="word", height=10, font=("Helvetica", 12))
        self.summary_text.pack(expand=1, fill="both", padx=10, pady=10)

        self.pie_chart_frame = ttkb.Frame(self.dashboard_frame, padding=(10, 10))
        self.pie_chart_frame.pack(expand=1, fill="both")

        self.update_dashboard()

    def create_system_tab(self):
        self.cpu_label = ttkb.Label(self.system_tab, text="CPU Usage: ", font=("Helvetica", 12))
        self.cpu_label.pack(pady=10)

        self.memory_label = ttkb.Label(self.system_tab, text="Memory Usage: ", font=("Helvetica", 12))
        self.memory_label.pack(pady=10)

        self.disk_label = ttkb.Label(self.system_tab, text="Disk Usage: ", font=("Helvetica", 12))
        self.disk_label.pack(pady=10)

    def create_logs_tab(self):
        self.logs_text = tk.Text(self.logs_tab, wrap="word", font=("Helvetica", 12))
        self.logs_text.pack(expand=1, fill="both", padx=10, pady=10)

        self.search_entry = ttkb.Entry(self.logs_tab, font=("Helvetica", 12))
        self.search_entry.pack(pady=10)

        self.search_button = ttkb.Button(self.logs_tab, text="Search Logs", command=self.search_logs)
        self.search_button.pack(pady=10)

        Tooltip(self.search_button, text="Click to search logs")

    def create_tasks_tab(self):
        self.task_listbox = tk.Listbox(self.tasks_tab, font=("Helvetica", 12))
        self.task_listbox.pack(expand=1, fill="both", padx=10, pady=10)

        self.add_task_entry = ttkb.Entry(self.tasks_tab, font=("Helvetica", 12))
        self.add_task_entry.pack(pady=10)

        self.add_task_button = ttkb.Button(self.tasks_tab, text="Add Task", command=self.add_task)
        self.add_task_button.pack(pady=10)

        self.remove_task_button = ttkb.Button(self.tasks_tab, text="Remove Task", command=self.remove_task)
        self.remove_task_button.pack(pady=10)

        self.prioritize_task_button = ttkb.Button(self.tasks_tab, text="Prioritize Task", command=self.prioritize_task)
        self.prioritize_task_button.pack(pady=10)

        Tooltip(self.add_task_button, text="Click to add a new task")
        Tooltip(self.remove_task_button, text="Click to remove the selected task")
        Tooltip(self.prioritize_task_button, text="Click to prioritize the selected task")

    def create_heartbeat_tab(self):
        """Create the heartbeat monitoring tab"""
        # Top status panel
        status_panel = ttk.Frame(self.heartbeat_tab)
        status_panel.pack(fill=tk.X, padx=10, pady=10)
        
        # Heartbeat rate label
        self.heartbeat_rate_label = ttk.Label(
            status_panel, 
            text="Rate: 0.00 Hz",
            font=("TkDefaultFont", 12, "bold")
        )
        self.heartbeat_rate_label.pack(side=tk.LEFT, padx=10)
        
        # Heartbeat mode label
        self.heartbeat_mode_label = ttk.Label(
            status_panel,
            text="Mode: Normal",
            font=("TkDefaultFont", 12, "bold"),
            bootstyle="info"
        )
        self.heartbeat_mode_label.pack(side=tk.LEFT, padx=10)
        
        # Active events counter
        self.active_events_label = ttk.Label(
            status_panel,
            text="Active Events: 0",
            font=("TkDefaultFont", 12)
        )
        self.active_events_label.pack(side=tk.LEFT, padx=10)

        # Control panel for buttons
        control_panel = ttk.Frame(self.heartbeat_tab)
        control_panel.pack(fill=tk.X, padx=10, pady=5)
        
        # Buttons for heartbeat controls
        hyper_btn = ttk.Button(
            control_panel, 
            text="HYPER Drive", 
            command=lambda: self.toggle_hyper_drive(True),
            bootstyle="danger"
        )
        hyper_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        normal_btn = ttk.Button(
            control_panel, 
            text="Normal Mode", 
            command=lambda: self.toggle_hyper_drive(False)
        )
        normal_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        reset_btn = ttk.Button(
            control_panel, 
            text="Reset", 
            command=self.reset_heartbeat
        )
        reset_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        clear_btn = ttk.Button(
            control_panel,
            text="Clear Logs",
            command=self.clear_heartbeat_log
        )
        clear_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # System metrics section
        metrics_panel = ttk.Frame(self.heartbeat_tab)
        metrics_panel.pack(fill=tk.X, padx=10, pady=5)
        
        # CPU usage
        ttk.Label(metrics_panel, text="CPU:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.cpu_progress = ttk.Progressbar(metrics_panel, length=150)
        self.cpu_progress.grid(row=0, column=1, padx=5, pady=5)
        self.cpu_label = ttk.Label(metrics_panel, text="0.0%")
        self.cpu_label.grid(row=0, column=2, padx=5, pady=5)
        
        # Memory usage
        ttk.Label(metrics_panel, text="Memory:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.mem_progress = ttk.Progressbar(metrics_panel, length=150)
        self.mem_progress.grid(row=1, column=1, padx=5, pady=5)
        self.mem_label = ttk.Label(metrics_panel, text="0.0%")
        self.mem_label.grid(row=1, column=2, padx=5, pady=5)
        
        # Create the heartbeat rate graph
        self.heartbeat_times = []
        self.heartbeat_rates = []
        self.start_time = None
        self.displayed_log_entries = set()
        
        graph_panel = ttk.Frame(self.heartbeat_tab)
        graph_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Use matplotlib to create a real-time graph
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        self.heartbeat_fig = Figure(figsize=(5, 2), dpi=100)
        self.heartbeat_ax = self.heartbeat_fig.add_subplot(111)
        self.heartbeat_ax.set_xlabel('Time (s)')
        self.heartbeat_ax.set_ylabel('Rate (Hz)')
        self.heartbeat_ax.set_title('Heartbeat Rate Over Time')
        self.heartbeat_ax.grid(True)
        self.heartbeat_line, = self.heartbeat_ax.plot([], [], 'b-')
        
        canvas = FigureCanvasTkAgg(self.heartbeat_fig, graph_panel)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Event log section
        log_frame = ttk.LabelFrame(self.heartbeat_tab, text="Event Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollable text widget for logs
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical")
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.heartbeat_log = tk.Text(
            log_frame,
            height=8,
            state="disabled",
            wrap=tk.WORD,
            yscrollcommand=log_scroll.set
        )
        self.heartbeat_log.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.heartbeat_log.yview)

    def create_echo_tab(self):
        self.echo_frame = ttkb.Frame(self.echo_tab, padding=(10, 10))
        self.echo_frame.pack(expand=1, fill="both")

        control_frame = ttkb.Frame(self.echo_frame)
        control_frame.pack(fill="x", pady=5)

        threshold_label = ttkb.Label(control_frame, text="Echo Threshold:")
        threshold_label.pack(side="left", padx=5)

        self.threshold_var = tk.DoubleVar(value=0.75)
        threshold_slider = ttkb.Scale(control_frame, from_=0.0, to=1.0, variable=self.threshold_var, orient="horizontal", bootstyle="success")
        threshold_slider.pack(side="left", padx=5, fill="x", expand=True)
        threshold_slider.bind("<ButtonRelease-1>", lambda e: self.update_echo_threshold())

        depth_label = ttkb.Label(control_frame, text="Max Depth:")
        depth_label.pack(side="left", padx=5)

        self.depth_var = tk.IntVar(value=5)
        depth_slider = ttkb.Scale(control_frame, from_=1, to=20, variable=self.depth_var, orient="horizontal", bootstyle="info")
        depth_slider.pack(side="left", padx=5, fill="x", expand=True)
        depth_slider.bind("<ButtonRelease-1>", lambda e: self.update_max_depth())

        action_frame = ttkb.Frame(self.echo_frame)
        action_frame.pack(fill="x", pady=5)

        inject_btn = ttkb.Button(action_frame, text="Inject Random Echo", command=self.inject_random_echo, bootstyle="outline")
        inject_btn.pack(side="left", padx=5)

        propagate_btn = ttkb.Button(action_frame, text="Propagate Echoes", command=self.manual_propagate_echoes, bootstyle="outline-success")
        propagate_btn.pack(side="left", padx=5)

        prune_btn = ttkb.Button(action_frame, text="Prune Weak Echoes", command=self.prune_weak_echoes, bootstyle="outline-warning")
        prune_btn.pack(side="left", padx=5)

        self.echo_fig_frame = ttkb.Frame(self.echo_frame, padding=(5, 5))
        self.echo_fig_frame.pack(expand=1, fill="both", pady=10)

        metrics_frame = ttkb.Frame(self.echo_frame)
        metrics_frame.pack(fill="x", pady=5)

        self.metrics_labels = {}
        for metric in ['total_nodes', 'avg_echo', 'max_echo', 'resonant_nodes', 'depth']:
            label = ttkb.Label(metrics_frame, text=f"{metric.replace('_', ' ').title()}: 0")
            label.pack(side="left", padx=10)
            self.metrics_labels[metric] = label

        self.echo_history_frame = ttkb.Frame(self.echo_frame, padding=(5, 5))
        self.echo_history_frame.pack(expand=1, fill="both", pady=10)

    def create_memory_tab(self):
        self.memory_frame = ttkb.Frame(self.memory_tab, padding=(10, 10))
        self.memory_frame.pack(expand=1, fill="both")

        self.memory_label = ttkb.Label(self.memory_frame, text="Memory Visualization", font=("Helvetica", 14, "bold"))
        self.memory_label.pack(pady=10)

        self.update_memory_visualization()

    def create_cognitive_tab(self):
        self.cognitive_frame = ttkb.Frame(self.cognitive_tab, padding=(10, 10))
        self.cognitive_frame.pack(expand=1, fill="both")

        self.cognitive_label = ttkb.Label(self.cognitive_frame, text="Cognitive Systems", font=("Helvetica", 14, "bold"))
        self.cognitive_label.pack(pady=10)

    def update_dashboard(self):
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        summary = f"CPU Usage: {cpu_usage}%\nMemory Usage: {memory.percent}%\nDisk Usage: {disk.percent}%"
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)

        self.create_pie_chart(cpu_usage, memory.percent, disk.percent)

        self.root.after(1000, self.update_dashboard)

    def create_pie_chart(self, cpu, memory, disk):
        fig, ax = plt.subplots()
        labels = 'CPU', 'Memory', 'Disk'
        sizes = [cpu, memory, disk]
        colors = ['gold', 'yellowgreen', 'lightcoral']
        explode = (0.1, 0, 0)

        ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
        ax.axis('equal')

        for widget in self.pie_chart_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.pie_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=1, fill="both")

    def update_system_health(self):
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        self.cpu_label.config(text=f"CPU Usage: {cpu_usage}%")
        self.memory_label.config(text=f"Memory Usage: {memory.percent}%")
        self.disk_label.config(text=f"Disk Usage: {disk.percent}%")

        self.root.after(1000, self.update_system_health)

    def update_activity_logs(self):
        logs_dir = Path('activity_logs')
        logs = []
        for component in logs_dir.iterdir():
            if component.is_dir():
                activity_file = component / 'activity.json'
                if activity_file.exists():
                    with open(activity_file) as f:
                        logs.extend(json.load(f))

        self.logs_text.delete(1.0, tk.END)
        for log in logs:
            self.logs_text.insert(tk.END, f"{log['time']}: {log['description']}\n")

        self.root.after(5000, self.update_activity_logs)

    def search_logs(self):
        search_term = self.search_entry.get()
        if search_term:
            logs_dir = Path('activity_logs')
            logs = []
            for component in logs_dir.iterdir():
                if component.is_dir():
                    activity_file = component / 'activity.json'
                    if activity_file.exists():
                        with open(activity_file) as f:
                            logs.extend(json.load(f))

            self.logs_text.delete(1.0, tk.END)
            for log in logs:
                if search_term.lower() in log['description'].lower():
                    self.logs_text.insert(tk.END, f"{log['time']}: {log['description']}\n")

    def add_task(self):
        task_id = self.add_task_entry.get()
        if task_id:
            self.activity_regulator.add_task(task_id, lambda: print(f"Executing {task_id}"))
            self.task_listbox.insert(tk.END, task_id)
            self.add_task_entry.delete(0, tk.END)

    def remove_task(self):
        selected_task = self.task_listbox.curselection()
        if selected_task:
            task_id = self.task_listbox.get(selected_task)
            self.activity_regulator.remove_task(task_id)
            self.task_listbox.delete(selected_task)

    def prioritize_task(self):
        selected_task = self.task_listbox.curselection()
        if selected_task:
            task_id = self.task_listbox.get(selected_task)
            self.activity_regulator.prioritize_task(task_id)
            messagebox.showinfo("Task Prioritized", f"Task {task_id} has been prioritized.")

    def update_echo_threshold(self):
        self.echo.echo_threshold = self.threshold_var.get()
        self.update_echo_visualization()

    def update_max_depth(self):
        self.echo.max_depth = self.depth_var.get()
        self.update_echo_visualization()

    def inject_random_echo(self):
        if self.root_node and self.root_node.children:
            all_nodes = self.get_all_tree_nodes(self.root_node)
            if len(all_nodes) > 1:
                source = all_nodes[np.random.randint(0, len(all_nodes))]
                target = all_nodes[np.random.randint(0, len(all_nodes))]

                while source == target:
                    target = all_nodes[np.random.randint(0, len(all_nodes))]

                strength = np.random.uniform(0.3, 0.9)
                self.echo.inject_echo(source, target, strength)
                self.update_echo_visualization()

    def get_all_tree_nodes(self, node, nodes=None):
        if nodes is None:
            nodes = []
        nodes.append(node)
        for child in node.children:
            self.get_all_tree_nodes(child, nodes)
        return nodes

    def manual_propagate_echoes(self):
        self.echo.propagate_echoes()
        self.update_echo_visualization()

    def prune_weak_echoes(self):
        self.echo.prune_weak_echoes()
        self.update_echo_visualization()

    def update_echo_visualization(self):
        if not self.root_node or not self.root_node.children:
            self.create_demo_tree()

        self.echo.propagate_echoes()

        patterns = self.echo.analyze_echo_patterns()

        for metric, label in self.metrics_labels.items():
            if metric in patterns:
                if isinstance(patterns[metric], float):
                    value = f"{patterns[metric]:.2f}"
                else:
                    value = str(patterns[metric])
                label.config(text=f"{metric.replace('_', ' ').title()}: {value}")

        timestamp = time.strftime("%H:%M:%S")
        self.history['timestamps'].append(timestamp)
        self.history['avg_echo'].append(patterns.get('avg_echo', 0))
        self.history['max_echo'].append(patterns.get('max_echo', 0))
        self.history['resonant_nodes'].append(patterns.get('resonant_nodes', 0))

        if len(self.history['timestamps']) > 30:
            for key in self.history:
                self.history[key] = self.history[key][-30:]

        self.visualize_echo_tree()
        self.visualize_echo_history()

        self.root.after(2000, self.update_echo_visualization)

    def create_demo_tree(self):
        self.echo = DeepTreeEcho()
        self.root_node = self.echo.create_tree("Deep Tree Echo Root")

        child1 = TreeNode(content="Memory Systems Integration", parent=self.root_node)
        self.root_node.children.append(child1)

        child2 = TreeNode(content="Echo State Networks", parent=self.root_node)
        self.root_node.children.append(child2)

        child3 = TreeNode(content="Browser Automation", parent=self.root_node)
        self.root_node.children.append(child3)

        grandchild1 = TreeNode(content="Declarative Memory", parent=child1)
        child1.children.append(grandchild1)

        grandchild2 = TreeNode(content="Procedural Memory", parent=child1)
        child1.children.append(grandchild2)

        grandchild3 = TreeNode(content="Episodic Memory", parent=child1)
        child1.children.append(grandchild3)

        grandchild4 = TreeNode(content="Reservoir Computing", parent=child2)
        child2.children.append(grandchild4)

        grandchild5 = TreeNode(content="ChatGPT Integration", parent=child3)
        child3.children.append(grandchild5)

        ggchild1 = TreeNode(content="Long-term Memory", parent=grandchild1)
        grandchild1.children.append(ggchild1)

        ggchild2 = TreeNode(content="Short-term Memory", parent=grandchild1)
        grandchild1.children.append(ggchild2)

        self.echo.propagate_echoes()

    def visualize_echo_tree(self):
        for widget in self.echo_fig_frame.winfo_children():
            widget.destroy()

        G = nx.DiGraph()

        def add_node_to_graph(node, parent_id=None):
            node_id = id(node)
            G.add_node(node_id, echo_value=node.echo_value, content=node.content, size=300 + 1000 * node.echo_value)

            if parent_id is not None:
                G.add_edge(parent_id, node_id)

            for child in node.children:
                add_node_to_graph(child, node_id)

        if self.root_node:
            add_node_to_graph(self.root_node)

            fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
            fig.patch.set_facecolor('#2a3439')
            ax.set_facecolor('#2a3439')

            pos = nx.kamada_kawai_layout(G)

            node_sizes = [data['size'] for _, data in G.nodes(data=True)]
            echo_values = [data['echo_value'] for _, data in G.nodes(data=True)]

            cmap = plt.cm.viridis
            norm = mcolors.Normalize(vmin=0, vmax=1)

            nodes = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=echo_values, cmap=cmap, alpha=0.9, ax=ax)

            nx.draw_networkx_edges(G, pos, edge_color='gray', alpha=0.5, arrows=True, ax=ax)

            sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, label='Echo Value')
            cbar.ax.yaxis.label.set_color('white')
            cbar.ax.tick_params(colors='white')

            ax.set_title("Deep Tree Echo Visualization", color='white', fontsize=14)
            ax.set_axis_off()

            canvas = FigureCanvasTkAgg(fig, master=self.echo_fig_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(expand=1, fill="both")

    def visualize_echo_history(self):
        for widget in self.echo_history_frame.winfo_children():
            widget.destroy()

        if not self.history['timestamps']:
            return

        fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
        fig.patch.set_facecolor('#2a3439')
        ax.set_facecolor('#2a3439')

        ax.plot(self.history['timestamps'], self.history['avg_echo'], label='Average Echo', color='#00bc8c', marker='o', markersize=4)
        ax.plot(self.history['timestamps'], self.history['max_echo'], label='Max Echo', color='#3498db', marker='s', markersize=4)

        ax2 = ax.twinx()
        ax2.plot(self.history['timestamps'], self.history['resonant_nodes'], label='Resonant Nodes', color='#e74c3c', marker='^', markersize=4)

        ax.set_xlabel('Time', color='white')
        if len(self.history['timestamps']) > 10:
            step = len(self.history['timestamps']) // 5
            ax.set_xticks(self.history['timestamps'][::step])
        ax.tick_params(axis='x', colors='white', rotation=45)

        ax.set_ylabel('Echo Value', color='#00bc8c')
        ax.tick_params(axis='y', colors='#00bc8c')

        ax2.set_ylabel('Resonant Nodes', color='#e74c3c')
        ax2.tick_params(axis='y', colors='#e74c3c')

        ax.set_title('Echo Patterns Over Time', color='white')
        ax.grid(True, linestyle='--', alpha=0.3)

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', facecolor='#2a3439', labelcolor='white')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.echo_history_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=1, fill="both")

    def update_memory_visualization(self):
        """Update memory visualization with current hypergraph data"""
        # Clear previous content
        for widget in self.memory_frame.winfo_children():
            if widget != self.memory_label:
                widget.destroy()
                
        # Create control panel
        control_frame = ttkb.Frame(self.memory_frame)
        control_frame.pack(fill="x", pady=5)
        
        # Memory type filter
        type_label = ttkb.Label(control_frame, text="Memory Type:")
        type_label.pack(side="left", padx=5)
        
        self.memory_type_var = tk.StringVar(value="All")
        memory_types = ["All"] + [m_type.value for m_type in MemoryType]
        type_dropdown = ttkb.Combobox(control_frame, textvariable=self.memory_type_var, 
                                    values=memory_types, width=15)
        type_dropdown.pack(side="left", padx=5)
        type_dropdown.bind("<<ComboboxSelected>>", lambda e: self.filter_memory_graph())
        
        # Min salience filter
        salience_label = ttkb.Label(control_frame, text="Min Salience:")
        salience_label.pack(side="left", padx=5)
        
        self.min_salience_var = tk.DoubleVar(value=0.0)
        salience_slider = ttkb.Scale(control_frame, from_=0.0, to=1.0, 
                                   variable=self.min_salience_var, 
                                   orient="horizontal", bootstyle="success", length=150)
        salience_slider.pack(side="left", padx=5)
        salience_slider.bind("<ButtonRelease-1>", lambda e: self.filter_memory_graph())
        
        # Max nodes to display
        max_nodes_label = ttkb.Label(control_frame, text="Max Nodes:")
        max_nodes_label.pack(side="left", padx=5)
        
        self.max_nodes_var = tk.IntVar(value=100)
        max_nodes_entry = ttkb.Entry(control_frame, textvariable=self.max_nodes_var, width=5)
        max_nodes_entry.pack(side="left", padx=5)
        max_nodes_entry.bind("<Return>", lambda e: self.filter_memory_graph())
        
        # Layout selection
        layout_label = ttkb.Label(control_frame, text="Layout:")
        layout_label.pack(side="left", padx=5)
        
        self.layout_var = tk.StringVar(value="spring")
        layouts = ["spring", "kamada_kawai", "circular", "shell", "spectral"]
        layout_dropdown = ttkb.Combobox(control_frame, textvariable=self.layout_var, 
                                      values=layouts, width=12)
        layout_dropdown.pack(side="left", padx=5)
        layout_dropdown.bind("<<ComboboxSelected>>", lambda e: self.filter_memory_graph())
        
        # Actions frame
        action_frame = ttkb.Frame(self.memory_frame)
        action_frame.pack(fill="x", pady=5)
        
        # Add demo memory data
        demo_btn = ttkb.Button(action_frame, text="Generate Demo Memory", 
                             command=self.generate_demo_memory, 
                             bootstyle="outline")
        demo_btn.pack(side="left", padx=5)
        
        update_btn = ttkb.Button(action_frame, text="Update Graph", 
                               command=self.filter_memory_graph, 
                               bootstyle="outline-success")
        update_btn.pack(side="left", padx=5)
        
        community_btn = ttkb.Button(action_frame, text="Show Communities", 
                                  command=self.show_memory_communities, 
                                  bootstyle="outline-info")
        community_btn.pack(side="left", padx=5)
        
        # Memory metrics display
        metrics_frame = ttkb.Frame(self.memory_frame)
        metrics_frame.pack(fill="x", pady=5)
        
        self.memory_metrics = {}
        for metric in ['node_count', 'edge_count', 'avg_salience', 'avg_connections']:
            label = ttkb.Label(metrics_frame, text=f"{metric.replace('_', ' ').title()}: 0")
            label.pack(side="left", padx=10)
            self.memory_metrics[metric] = label
            
        # Split view with graph visualization and memory details
        paned_window = ttk.PanedWindow(self.memory_frame, orient='horizontal')
        paned_window.pack(fill='both', expand=True, pady=5)
        
        # Graph visualization frame
        self.memory_graph_frame = ttkb.Frame(paned_window)
        paned_window.add(self.memory_graph_frame, weight=2)
        
        # Memory details frame
        details_frame = ttkb.Frame(paned_window)
        paned_window.add(details_frame, weight=1)
        
        # Memory details
        details_label = ttkb.Label(details_frame, text="Memory Details", 
                                 font=("Helvetica", 12, "bold"))
        details_label.pack(anchor="w", pady=5)
        
        self.memory_details_text = tk.Text(details_frame, wrap="word", height=10, 
                                        font=("Helvetica", 10))
        self.memory_details_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Memory search
        search_frame = ttkb.Frame(details_frame)
        search_frame.pack(fill="x", pady=5)
        
        search_label = ttkb.Label(search_frame, text="Search:")
        search_label.pack(side="left", padx=5)
        
        self.memory_search_var = tk.StringVar()
        search_entry = ttkb.Entry(search_frame, textvariable=self.memory_search_var)
        search_entry.pack(side="left", padx=5, fill="x", expand=True)
        search_entry.bind("<Return>", lambda e: self.search_memory())
        
        search_btn = ttkb.Button(search_frame, text="Search", 
                               command=self.search_memory, 
                               bootstyle="outline")
        search_btn.pack(side="left", padx=5)
        
        # Initialize graph
        self.filter_memory_graph()
        
        # Schedule updates
        self.root.after(5000, self.update_memory_stats)

    def filter_memory_graph(self):
        """Filter and visualize memory graph based on current filters"""
        if not hasattr(self, 'memory_system') or self.memory_system is None:
            return
            
        memory_type = self.memory_type_var.get()
        min_salience = self.min_salience_var.get()
        max_nodes = self.max_nodes_var.get()
        
        # Prepare filters
        filters = {}
        if memory_type != "All":
            filters['memory_type'] = memory_type
        if min_salience > 0:
            filters['min_salience'] = min_salience
        
        # Get nodes from memory system
        nodes = self.memory_system.find_nodes(**filters)
        
        # Limit number of nodes
        if len(nodes) > max_nodes:
            nodes = sorted(nodes, key=lambda n: n.salience, reverse=True)[:max_nodes]
        
        # Create NetworkX graph from memory nodes
        G = nx.DiGraph()
        
        # Add nodes to graph
        for node in nodes:
            G.add_node(node.id, 
                     content=node.content,
                     salience=node.salience,
                     memory_type=node.memory_type.value if hasattr(node.memory_type, 'value') else node.memory_type,
                     echo_value=node.echo_value,
                     creation_time=node.creation_time)
        
        # Add edges between these nodes
        for edge in self.memory_system.edges:
            if edge.from_id in G and edge.to_id in G:
                G.add_edge(edge.from_id, edge.to_id, 
                         relation=edge.relation_type,
                         weight=edge.weight)
        
        # Draw the graph
        self.draw_memory_graph(G)
        
        # Update metrics
        self.update_memory_stats()

    def draw_memory_graph(self, G):
        """Draw the memory graph visualization"""
        # Clear previous figure
        for widget in self.memory_graph_frame.winfo_children():
            widget.destroy()
        
        if not G.nodes():
            # No nodes to display
            empty_label = ttkb.Label(self.memory_graph_frame, 
                                   text="No memory nodes match the current filters",
                                   font=("Helvetica", 12))
            empty_label.pack(expand=True)
            return
        
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        fig.patch.set_facecolor('#2a3439')
        ax.set_facecolor('#2a3439')
        
        # Choose layout
        layout_name = self.layout_var.get()
        if layout_name == "spring":
            pos = nx.spring_layout(G, k=0.3, iterations=50)
        elif layout_name == "kamada_kawai":
            try:
                pos = nx.kamada_kawai_layout(G)
            except:
                pos = nx.spring_layout(G)  # Fallback
        elif layout_name == "circular":
            pos = nx.circular_layout(G)
        elif layout_name == "shell":
            pos = nx.shell_layout(G)
        elif layout_name == "spectral":
            try:
                pos = nx.spectral_layout(G)
            except:
                pos = nx.spring_layout(G)  # Fallback
        else:
            pos = nx.spring_layout(G)
        
        # Get node attributes for visualization
        node_salience = [data.get('salience', 0.5) for _, data in G.nodes(data=True)]
        node_sizes = [300 + 700 * sal for sal in node_salience]
        
        # Color nodes by memory type
        memory_types = [data.get('memory_type', 'unknown') for _, data in G.nodes(data=True)]
        unique_types = list(set(memory_types))
        color_map = plt.cm.get_cmap('tab10', len(unique_types))
        type_to_color = {t: color_map(i) for i, t in enumerate(unique_types)}
        node_colors = [type_to_color[t] for t in memory_types]
        
        # Draw nodes
        nodes = nx.draw_networkx_nodes(G, pos, 
                                      node_size=node_sizes, 
                                      node_color=node_colors, 
                                      alpha=0.8, ax=ax)
        
        # Draw edges with color based on weight
        edge_weights = [G[u][v].get('weight', 0.5) for u, v in G.edges()]
        nx.draw_networkx_edges(G, pos, 
                              edge_color=edge_weights,
                              edge_cmap=plt.cm.Blues,
                              width=1.5,
                              alpha=0.6,
                              arrows=True,
                              ax=ax,
                              arrowsize=10)
        
        # Draw labels for high-salience nodes only
        high_salience_nodes = {node: data for node, data in G.nodes(data=True) 
                             if data.get('salience', 0) > 0.7}
        if high_salience_nodes:
            nx.draw_networkx_labels(G, pos, 
                                  labels={n: data.get('content', '')[:20] + '...' 
                                        for n, data in high_salience_nodes.items()},
                                  font_size=8,
                                  font_color='white',
                                  ax=ax)
        
        # Create legend for memory types
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                     label=t, markerfacecolor=type_to_color[t], markersize=8) 
                         for t in unique_types]
        ax.legend(handles=legend_elements, title="Memory Types", 
                 loc="upper right", framealpha=0.8,
                 facecolor='#2a3439', labelcolor='white')
        
        # Add title and remove axis
        ax.set_title("Memory Hypergraph Visualization", color='white', fontsize=14)
        ax.set_axis_off()
        
        # Connect node click event
        def on_node_click(event):
            if event.inaxes != ax:
                return
                
            # Find closest node
            node_list = list(G.nodes())
            closest_node = None
            min_dist = float('inf')
            
            for i, (node_id, node_pos) in enumerate(pos.items()):
                dist = np.sqrt((event.xdata - node_pos[0]) ** 2 + 
                              (event.ydata - node_pos[1]) ** 2)
                transformed_dist = dist / (node_sizes[i] / 5000)  # Adjust distance by node size
                if transformed_dist < min_dist and transformed_dist < 0.1:
                    min_dist = transformed_dist
                    closest_node = node_id
            
            if closest_node:
                # Show node details
                self.display_memory_node_details(closest_node)
        
        # Connect the event
        fig.canvas.mpl_connect('button_press_event', on_node_click)
        
        # Create canvas and display
        canvas = FigureCanvasTkAgg(fig, master=self.memory_graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=1, fill="both")
        
        # Add toolbar
        from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
        toolbar_frame = ttkb.Frame(self.memory_graph_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.config(background='#2a3439')
        toolbar.update()

    def display_memory_node_details(self, node_id):
        """Display details of a memory node"""
        node = self.memory_system.get_node(node_id)
        if not node:
            return
            
        # Format details
        details = f"Node ID: {node.id}\n"
        details += f"Content: {node.content}\n"
        details += f"Memory Type: {node.memory_type.value if hasattr(node.memory_type, 'value') else node.memory_type}\n"
        details += f"Salience: {node.salience:.2f}\n"
        details += f"Echo Value: {node.echo_value:.2f}\n"
        details += f"Created: {time.strftime('%Y-%m-%d %H:%M', time.localtime(node.creation_time))}\n"
        details += f"Last Access: {time.strftime('%Y-%m-%d %H:%M', time.localtime(node.last_access_time))}\n"
        details += f"Access Count: {node.access_count}\n\n"
        
        # Show related nodes
        related = self.memory_system.get_related_nodes(node_id)
        if related:
            details += "Connected Memories:\n"
            for i, rel_node in enumerate(related[:10]):  # Show up to 10 related nodes
                details += f"- {rel_node.content[:50]}...\n"
            if len(related) > 10:
                details += f"...and {len(related) - 10} more\n"
        
        # Update details text
        self.memory_details_text.delete(1.0, tk.END)
        self.memory_details_text.insert(tk.END, details)

    def search_memory(self):
        """Search memory nodes for content"""
        query = self.memory_search_var.get()
        if not query:
            return
            
        # Search logic
        results = []
        for node_id, node in self.memory_system.nodes.items():
            if query.lower() in node.content.lower():
                results.append(node)
        
        # Sort by relevance (simple contains) and salience
        results = sorted(results, key=lambda n: (query.lower() in n.content.lower(), n.salience), reverse=True)
        
        # Display results
        self.memory_details_text.delete(1.0, tk.END)
        if results:
            self.memory_details_text.insert(tk.END, f"Found {len(results)} memory nodes:\n\n")
            for i, node in enumerate(results[:15]):  # Show top 15
                self.memory_details_text.insert(tk.END, f"{i+1}. {node.content[:100]}...\n")
                self.memory_details_text.insert(tk.END, f"   [ID: {node.id}, Salience: {node.salience:.2f}]\n\n")
            if len(results) > 15:
                self.memory_details_text.insert(tk.END, f"...and {len(results) - 15} more\n")
        else:
            self.memory_details_text.insert(tk.END, "No results found")

    def update_memory_stats(self):
        """Update memory statistics display"""
        if not hasattr(self, 'memory_system') or self.memory_system is None:
            return
        
        stats = self.memory_system.generate_statistics()
        
        # Update metrics display
        for metric, label in self.memory_metrics.items():
            if metric in stats:
                value = stats[metric]
                if isinstance(value, float):
                    value = f"{value:.2f}"
                label.config(text=f"{metric.replace('_', ' ').title()}: {value}")
        
        self.root.after(5000, self.update_memory_stats)

    def generate_demo_memory(self):
        """Generate demo memory data for visualization"""
        if not hasattr(self, 'memory_system') or self.memory_system is None:
            return
            
        # Create some sample memory nodes
        memory_types = list(MemoryType)
        topics = [
            "Deep Learning Architecture", "Echo State Networks", "Browser Automation",
            "Cognitive Architecture", "Hypergraph Memory", "Neural Networks",
            "Memory Systems", "Attention Mechanisms", "Transformer Models",
            "Neuromorphic Computing", "Quantum Computing", "Cognitive Science",
            "Artificial Intelligence", "Machine Learning", "Consciousness Studies",
            "Natural Language Processing", "Computer Vision", "Reinforcement Learning",
            "Evolutionary Algorithms", "Bayesian Networks"
        ]
        
        # Create nodes
        for i in range(20):
            topic = topics[i % len(topics)]
            memory_type = memory_types[i % len(memory_types)]
            content = f"{topic}: Exploration of concepts and implementation details for {topic.lower()}"
            node_id = f"demo_{int(time.time())}_{i}"
            
            node = self.memory_system.MemoryNode(
                id=node_id,
                content=content,
                memory_type=memory_type,
                salience=np.random.uniform(0.3, 0.9),
                echo_value=np.random.uniform(0.2, 0.8),
                source="demo_generation"
            )
            
            self.memory_system.add_node(node)
        
        # Create some connections
        nodes = list(self.memory_system.nodes.keys())
        for _ in range(30):
            if len(nodes) < 2:
                break
                
            from_id = np.random.choice(nodes)
            to_id = np.random.choice(nodes)
            
            if from_id != to_id:
                relation_types = ["related_to", "part_of", "causes", "similar_to", "contrasts_with"]
                relation = np.random.choice(relation_types)
                
                edge = self.memory_system.MemoryEdge(
                    from_id=from_id,
                    to_id=to_id,
                    relation_type=relation,
                    weight=np.random.uniform(0.3, 0.9)
                )
                
                self.memory_system.add_edge(edge)
        
        # Update visualization
        self.filter_memory_graph()
        messagebox.showinfo("Demo Memory", "Generated demo memory nodes and connections")

    def show_memory_communities(self):
        """Visualize memory communities"""
        if not hasattr(self, 'memory_system') or self.memory_system is None:
            return
        
        # Get communities
        communities = self.memory_system.find_communities()
        
        if not communities:
            messagebox.showinfo("Communities", "No communities found in the memory graph")
            return
        
        # Create NetworkX graph from memory nodes
        G = nx.Graph()  # Use undirected graph for community detection
        
        # Get all nodes in communities
        all_nodes = set()
        for community_id, nodes in communities.items():
            all_nodes.update(nodes)
        
        # Add nodes and their attributes
        for node_id in all_nodes:
            if node_id in self.memory_system.nodes:
                node = self.memory_system.nodes[node_id]
                G.add_node(node_id, 
                         content=node.content,
                         salience=node.salience,
                         memory_type=node.memory_type.value if hasattr(node.memory_type, 'value') else node.memory_type,
                         community=next((comm_id for comm_id, nodes in communities.items() 
                                      if node_id in nodes), -1))
        
        # Add edges between these nodes
        for edge in self.memory_system.edges:
            if edge.from_id in G and edge.to_id in G:
                G.add_edge(edge.from_id, edge.to_id, 
                         relation=edge.relation_type,
                         weight=edge.weight)
        
        # Clear previous figure
        for widget in self.memory_graph_frame.winfo_children():
            widget.destroy()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        fig.patch.set_facecolor('#2a3439')
        ax.set_facecolor('#2a3439')
        
        # Get layout
        pos = nx.spring_layout(G, k=0.3, seed=42)
        
        # Color nodes by community
        community_ids = [data.get('community', -1) for _, data in G.nodes(data=True)]
        unique_communities = sorted(set(community_ids))
        color_map = plt.cm.get_cmap('tab10', max(10, len(unique_communities)))
        
        # Draw nodes for each community
        for i, comm_id in enumerate(unique_communities):
            nodes_in_comm = [node for node, data in G.nodes(data=True) 
                           if data.get('community') == comm_id]
            
            if not nodes_in_comm:
                continue
                
            # Get node sizes based on salience
            node_sizes = [300 + 700 * G.nodes[n].get('salience', 0.5) for n in nodes_in_comm]
            
            # Draw nodes for this community
            nx.draw_networkx_nodes(G, pos,
                                 nodelist=nodes_in_comm,
                                 node_size=node_sizes,
                                 node_color=[color_map(i % 10)],
                                 alpha=0.8,
                                 ax=ax,
                                 label=f"Community {comm_id}")
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, 
                             width=1.0,
                             alpha=0.5,
                             ax=ax)
        
        # Draw labels for high-salience nodes only
        high_salience_nodes = {node: data for node, data in G.nodes(data=True) 
                             if data.get('salience', 0) > 0.7}
        if high_salience_nodes:
            nx.draw_networkx_labels(G, pos, 
                                  labels={n: data.get('content', '')[:20] + '...' 
                                        for n, data in high_salience_nodes.items()},
                                  font_size=8,
                                  font_color='white',
                                  ax=ax)
        
        # Add title and remove axis
        ax.set_title(f"Memory Communities ({len(unique_communities)} found)", 
                   color='white', fontsize=14)
        ax.set_axis_off()
        
        # Add legend
        ax.legend(title="Communities", 
                loc="upper right", 
                framealpha=0.8,
                facecolor='#2a3439', 
                labelcolor='white')
        
        # Create canvas and display
        canvas = FigureCanvasTkAgg(fig, master=self.memory_graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=1, fill="both")
        
        # Add info in details
        self.memory_details_text.delete(1.0, tk.END)
        self.memory_details_text.insert(tk.END, f"Found {len(unique_communities)} memory communities:\n\n")
        for comm_id, nodes in communities.items():
            if nodes:
                self.memory_details_text.insert(tk.END, f"Community {comm_id}: {len(nodes)} nodes\n")
                # Show some example nodes in this community
                for i, node_id in enumerate(list(nodes)[:3]):
                    if node_id in self.memory_system.nodes:
                        node = self.memory_system.nodes[node_id]
                        self.memory_details_text.insert(tk.END, f"- {node.content[:50]}...\n")
                if len(nodes) > 3:
                    self.memory_details_text.insert(tk.END, f"...and {len(nodes) - 3} more\n")
                self.memory_details_text.insert(tk.END, "\n")

    def update_heartbeat_monitor(self):
        """Update the heartbeat monitoring display with current data"""
        try:
            from adaptive_heartbeat import AdaptiveHeartbeat
            
            if not hasattr(self, 'heartbeat_system'):
                self.heartbeat_system = AdaptiveHeartbeat()
                self.heartbeat_logs = []
                if self.heartbeat_system is None:
                    self.log_message("Failed to initialize heartbeat system", level="ERROR")
                    return
                self.log_message("Heartbeat monitoring system initialized", level="INFO")
            
            # Update rate and mode displays
            current_rate = self.heartbeat_system.get_current_rate()
            self.heartbeat_rate_label.config(text=f"Rate: {current_rate:.2f} Hz")
            
            if self.heartbeat_system.is_hyper_drive_active():
                mode_text = "Mode: HYPER"
                mode_style = "danger"
            else:
                mode_text = "Mode: Normal" 
                mode_style = "info"
            self.heartbeat_mode_label.config(text=mode_text, bootstyle=mode_style)
            
            # Update active events counter
            active_events = len(self.heartbeat_system.get_active_events())
            self.active_events_label.config(text=f"Active Events: {active_events}")
            
            # Update system metrics
            cpu_usage = self.heartbeat_system.get_system_metrics().get('cpu_percent', 0)
            mem_usage = self.heartbeat_system.get_system_metrics().get('memory_percent', 0)
            
            self.cpu_progress.config(value=cpu_usage)
            self.cpu_label.config(text=f"{cpu_usage:.1f}%")
            
            self.mem_progress.config(value=mem_usage)
            self.mem_label.config(text=f"{mem_usage:.1f}%")
            
            # Update graph data
            if self.start_time is None:
                self.start_time = time.time()
                
            current_time = time.time() - self.start_time
            self.heartbeat_times.append(current_time)
            self.heartbeat_rates.append(current_rate)
            
            # Keep only the last 60 seconds of data
            while self.heartbeat_times and self.heartbeat_times[0] < current_time - 60:
                self.heartbeat_times.pop(0)
                self.heartbeat_rates.pop(0)
                
            # Update the plot
            if len(self.heartbeat_times) > 0:
                self.heartbeat_line.set_data(self.heartbeat_times, self.heartbeat_rates)
                self.heartbeat_ax.relim()
                self.heartbeat_ax.autoscale_view()
                self.heartbeat_fig.canvas.draw_idle()
            
            # Update event log with new entries
            new_logs = self.heartbeat_system.get_event_logs()
            for log_entry in new_logs:
                if log_entry.id not in self.displayed_log_entries:
                    self.add_heartbeat_log_entry(log_entry)
                    self.displayed_log_entries.add(log_entry.id)
            
        except Exception as e:
            self.log_message(f"Error updating heartbeat monitor: {str(e)}", level="ERROR")
        
        # Schedule the next update
        self.root.after(1000, self.update_heartbeat_monitor)
        
    def toggle_hyper_drive(self, enable=True):
        """Toggle the heartbeat system's hyper drive mode"""
        if hasattr(self, 'heartbeat_system'):
            if enable:
                self.heartbeat_system.enable_hyper_drive()
                self.log_message("Hyper drive mode ACTIVATED", level="WARNING")
            else:
                self.heartbeat_system.disable_hyper_drive()
                self.log_message("Hyper drive mode deactivated", level="INFO")
    
    def reset_heartbeat(self):
        """Reset the heartbeat system to default settings"""
        if hasattr(self, 'heartbeat_system'):
            self.heartbeat_system.reset()
            self.log_message("Heartbeat system reset to defaults", level="INFO")
    
    def clear_heartbeat_log(self):
        """Clear the heartbeat event log display"""
        if hasattr(self, 'heartbeat_log'):
            self.heartbeat_log.config(state="normal")
            self.heartbeat_log.delete(1.0, tk.END)
            self.heartbeat_log.config(state="disabled")
            self.displayed_log_entries.clear()
    
    def add_heartbeat_log_entry(self, log_entry):
        """Add a new entry to the heartbeat log display"""
        if hasattr(self, 'heartbeat_log'):
            timestamp = datetime.datetime.fromtimestamp(log_entry.timestamp).strftime('%H:%M:%S')
            level_colors = {
                "INFO": "blue",
                "WARNING": "orange",
                "ERROR": "red",
                "DEBUG": "gray"
            }
            color = level_colors.get(log_entry.level, "black")
            
            self.heartbeat_log.config(state="normal")
            self.heartbeat_log.insert(tk.END, f"[{timestamp}] ", "timestamp")
            self.heartbeat_log.insert(tk.END, f"{log_entry.level}: ", f"level_{log_entry.level.lower()}")
            self.heartbeat_log.insert(tk.END, f"{log_entry.message}\n", "message")
            
            self.heartbeat_log.tag_configure("timestamp", foreground="darkgray")
            self.heartbeat_log.tag_configure(f"level_{log_entry.level.lower()}", foreground=color, font=("TkDefaultFont", 9, "bold"))
            self.heartbeat_log.tag_configure("message", foreground="black")
            
            self.heartbeat_log.see(tk.END)
            self.heartbeat_log.config(state="disabled")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = GUIDashboard(root)
    root.mainloop()
