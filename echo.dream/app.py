from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from jinja2.exceptions import TemplateNotFound
import logging
import os
from datetime import datetime
from dte_simulation import DTESimulation, FractalRecursion, RecursiveDistinctionEngine
from command_analyzer import CommandAnalyzer
from fractal_invariance import FractalInvariance
from aar_system import AARTriad
from dte_config import dte_config
import json
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# Import DTE namespaces
from namespaces import namespace_manager
from namespaces.architecture import architecture_namespace
from namespaces.scheduling import scheduling_namespace
from namespaces.diary import diary_namespace
from namespaces.domain_tracker import domain_tracker

# Import connection mapper API blueprint
from connection_mapper_api import mapper_api

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "postgresql://neondb_owner:npg_sTSW5BniUA9w@ep-little-block-a6u1vm07.us-west-2.aws.neon.tech/neondb?sslmode=require"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "deep-tree-echo-secret-key"

# Import and initialize database
from database import db, init_app
init_app(app)

# Register the connection mapper API blueprint
app.register_blueprint(mapper_api, url_prefix='/api/mapper')

# Import the models for the connection mapper

# Create database tables for all models
with app.app_context():
    try:
        db.create_all()
        logger.info("Created database tables successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

# Import recursive distinction modules after database is initialized
from recursive_distinction import (
    RecursiveDistinctionManager, 
    HyperGNNManager, 
    SelfReferentialNodeManager
)

# Initialize recursive distinction managers
distinction_manager = RecursiveDistinctionManager()
hypergnn_manager = HyperGNNManager()
node_manager = SelfReferentialNodeManager()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        from models import User
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            user.last_login = db.func.now()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        from models import User
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password or not confirm_password:
            flash('All fields are required')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('register.html')
            
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from models import User, Project, Simulation, RecursivePattern
    
    if request.method == 'POST':
        # Check which form was submitted
        form_type = request.form.get('form_type')
        
        if form_type == 'password_change':
            # Password change form
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate input
            if not current_password or not new_password or not confirm_password:
                flash('All password fields are required', 'danger')
                return redirect(url_for('profile'))
                
            if new_password != confirm_password:
                flash('New passwords do not match', 'danger')
                return redirect(url_for('profile'))
                
            # Check current password
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('profile'))
                
            # Update password
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password updated successfully', 'success')
        else:
            # Profile update form
            email = request.form.get('email')
            
            if not email:
                flash('Email is required', 'danger')
                return redirect(url_for('profile'))
                
            # Check if email already exists
            existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
            if existing_user:
                flash('Email already in use by another account', 'danger')
                return redirect(url_for('profile'))
                
            # Update email
            current_user.email = email
            db.session.commit()
            flash('Profile updated successfully', 'success')
            
        return redirect(url_for('profile'))
    
    # Get user projects, simulations, and patterns
    projects = Project.query.filter_by(user_id=current_user.id).all()
    simulations = Simulation.query.filter_by(user_id=current_user.id).all()
    patterns = RecursivePattern.query.filter_by(user_id=current_user.id).all()
    
    return render_template('profile.html', 
                          projects=projects,
                          simulations=simulations,
                          patterns=patterns)
engines = {
    'dte': DTESimulation(),
    'fractal': FractalRecursion(),
    'recursive_distinction': RecursiveDistinctionEngine()
}
current_engine = 'dte'

# Initialize other components
command_analyzer = CommandAnalyzer()
fractal_invariance = FractalInvariance()
aar_triad = AARTriad()

# Set up a simple AAR triad system
aar_triad.create_agent("Explorer", ["observe", "modify", "analyze"])
aar_triad.create_arena("RecursiveSpace", (15, 15))
aar_triad.create_relation("ExplorerInSpace", "Explorer", "RecursiveSpace")

@app.route('/')
def index():
    return render_template('index.html', current_user=current_user)

@app.route('/platform-dashboard')
def platform_dashboard():
    """Platform Dashboard for unconscious/system foundation level overview."""
    try:
        # Import the root systems
        from root import system_topology, system_orchestra, system_entelecho
        
        # Get the state of each system
        topology_state = system_topology.get_topology_state()
        orchestra_state = system_orchestra.get_orchestra_state()
        entelecho_state = system_entelecho.get_entelecho_state()
        
        return render_template(
            'platform_dashboard.html',
            current_user=current_user,
            topology=topology_state,
            orchestra=orchestra_state,
            entelecho=entelecho_state
        )
    except Exception as e:
        logger.error(f"Error loading platform dashboard: {str(e)}")
        return render_template('platform_dashboard.html', current_user=current_user, error=str(e))

@app.route('/workspace-dashboard')
def workspace_dashboard():
    """Workspace Dashboard for subconscious/cognitive level overview."""
    try:
        # Import the echo systems
        from root.echo import workspace_architecture, workspace_scheduling, workspace_diary
        
        # Get the state of each system
        architecture_state = workspace_architecture.get_architecture_state()
        scheduling_state = workspace_scheduling.get_scheduling_state()
        diary_state = workspace_diary.get_diary_state()
        
        return render_template(
            'workspace_dashboard.html',
            current_user=current_user,
            architecture=architecture_state,
            scheduling=scheduling_state,
            diary=diary_state
        )
    except Exception as e:
        logger.error(f"Error loading workspace dashboard: {str(e)}")
        return render_template('workspace_dashboard.html', current_user=current_user, error=str(e))

@app.route('/user-dashboard')
def user_dashboard():
    """User Dashboard for conscious/interface level overview."""
    try:
        # Import the user level systems
        from root.echo.user import user_projects, user_timelines, user_topics
        
        # Get the state of each system
        projects_state = user_projects.get_projects_state()
        timelines_state = user_timelines.get_timelines_state()
        topics_state = user_topics.get_topics_state()
        
        return render_template(
            'user_dashboard.html',
            current_user=current_user,
            projects=projects_state,
            timelines=timelines_state,
            topics=topics_state
        )
    except Exception as e:
        logger.error(f"Error loading user dashboard: {str(e)}")
        return render_template('user_dashboard.html', current_user=current_user, error=str(e))

@app.route('/wiki')
def wiki_index():
    """Wiki homepage with index of documentation topics."""
    return redirect(url_for('wiki_aar'))

@app.route('/wiki/aar')
def wiki_aar():
    """Documentation for the Agent-Arena-Relation system."""
    return render_template('wiki_aar.html', current_user=current_user)

@app.route('/wiki/<topic>')
def wiki_topic(topic):
    """Generic handler for wiki topics."""
    try:
        return render_template(f'wiki_{topic}.html', current_user=current_user)
    except TemplateNotFound:
        # If template doesn't exist yet, redirect to index
        flash(f"Wiki page for '{topic}' is under development.", "info")
        return redirect(url_for('wiki_index'))
    
@app.route('/api/test-auth')
def test_auth():
    """Test if the user is authenticated and return their role."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'username': current_user.username,
            'user_id': current_user.id
        })
    else:
        return jsonify({
            'authenticated': False
        })
    
@app.route('/fractal-explorer')
def fractal_explorer():
    return render_template('fractal_explorer.html')
    
@app.route('/aar-simulator')
def aar_simulator():
    return render_template('aar_simulator.html')

@app.route('/thought-process')
def thought_process():
    """DTE's Thought Process Visualization for exploring cognitive processes."""
    return render_template('thought_process.html')

@app.route('/architecture')
def architecture_workspace():
    """DTE's Architecture Workspace for spatial organization."""
    return render_template('architecture_workspace.html')

@app.route('/scheduling')
def scheduling_workspace():
    """DTE's Scheduling Workspace for temporal organization."""
    return render_template('scheduling_workspace.html')

@app.route('/diary')
def diary_workspace():
    """DTE's Diary Workspace for self-reporting and memory."""
    return render_template('diary_workspace.html')

@app.route('/configuration')
def configuration():
    """DTE's Configuration interface for identity and personality settings."""
    return render_template('dte_configuration.html', config=dte_config.get_combined_config())

# Route handlers for Root menu items
@app.route('/core')
def core_interface():
    """DTE's Core system interface."""
    return render_template('core.html')

@app.route('/recursive-distinction')
@app.route('/recursive_distinction')
def recursive_distinction_interface():
    """Interface for the recursive distinction system."""
    return render_template('recursive_distinction.html')

@app.route('/console')
def console_interface():
    """DTE's Console for direct interaction."""
    return render_template('console.html')

@app.route('/streamio')
def streamio_interface():
    """DTE's Stream I/O processing interface."""
    return render_template('streamio.html')

@app.route('/memory')
def memory_interface():
    """DTE's Memory management system."""
    return render_template('memory.html')

@app.route('/settings')
def settings_interface():
    """User settings interface."""
    return render_template('settings.html')

@app.route('/projects')
def projects_interface():
    """Projects management interface."""
    return render_template('projects.html')

@app.route('/timelines')
def timelines_interface():
    """Timelines management interface."""
    return render_template('timelines.html')

@app.route('/topics')
def topics_interface():
    """Topics and discussions interface."""
    return render_template('topics.html')

@app.route('/user-memory')
def user_memory_interface():
    """User memory storage interface."""
    return render_template('user_memory.html')

@app.route('/workspace-memory')
def workspace_memory_interface():
    """Workspace memory storage interface."""
    return render_template('workspace_memory.html')

@app.route('/diagnostics')
def diagnostics_interface():
    """System diagnostics interface."""
    return render_template('diagnostics.html')

@app.route('/topology')
def topology_interface():
    """DTE's Topology visualization and management."""
    return render_template('topology.html')

@app.route('/orchestra')
def orchestra_interface():
    """DTE's Orchestra for coordination of components."""
    return render_template('orchestra.html')

@app.route('/entelecho')
def entelecho_interface():
    """DTE's Entelecho system for purpose fulfillment."""
    return render_template('entelecho.html')

@app.route('/self-promise')
def self_promise_interface():
    """DTE's self.promise interface for integrity guarantees."""
    return render_template('self_promise.html')
    
@app.route('/connection-mapper')
def connection_mapper_interface():
    """Dynamic Interdisciplinary Connection Mapper visualization interface."""
    return render_template('connection_mapper.html')
    
@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard for database management."""
    from models import User, Project, Simulation, RecursivePattern
    
    # Check if user has admin rights (for a real application, you'd check admin flag)
    # For now, we're keeping it simple and allowing any authenticated user to access admin
    
    # Get statistics for dashboard
    stats = {
        'user_count': User.query.count(),
        'project_count': Project.query.count(),
        'simulation_count': Simulation.query.count(),
        'pattern_count': RecursivePattern.query.count()
    }
    
    # Get latest data for dashboard
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    
    # Get all data for detailed views
    all_users = User.query.all()
    all_projects = Project.query.all()
    all_simulations = Simulation.query.all()
    all_patterns = RecursivePattern.query.all()
    
    # Get application config for settings tab
    app_config = {
        'DEBUG': app.debug,
        'MAX_CONTENT_LENGTH': getattr(app, 'MAX_CONTENT_LENGTH', 16 * 1024 * 1024),  # Default 16MB
        'PERMANENT_SESSION_LIFETIME': app.permanent_session_lifetime.total_seconds()
    }
    
    return render_template(
        'admin_dashboard.html',
        stats=stats,
        recent_users=recent_users,
        recent_projects=recent_projects,
        all_users=all_users,
        all_projects=all_projects,
        all_simulations=all_simulations,
        all_patterns=all_patterns,
        app_config=app_config
    )

# Admin API endpoints
@app.route('/admin/users/create', methods=['POST'])
@login_required
def admin_create_user():
    """Create a new user (admin only)."""
    from models import User
    
    # In a real application, check if current user is admin
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not username or not email or not password:
        flash('All fields are required', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    if User.query.filter_by(email=email).first():
        flash('Email already exists', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    # Create new user
    user = User(username=username, email=email)
    user.set_password(password)
    user.created_at = datetime.utcnow()
    
    db.session.add(user)
    db.session.commit()
    
    flash(f'User {username} created successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    """Delete a user (admin only)."""
    from models import User
    
    # In a real application, check if current user is admin
    
    # Prevent self-deletion
    if user_id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    user = User.query.get_or_404(user_id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def admin_delete_project(project_id):
    """Delete a project (admin only)."""
    from models import Project
    
    # In a real application, check if current user is admin
    
    project = Project.query.get_or_404(project_id)
    project_name = project.name
    
    db.session.delete(project)
    db.session.commit()
    
    flash(f'Project {project_name} deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/simulations/<int:simulation_id>/delete', methods=['POST'])
@login_required
def admin_delete_simulation(simulation_id):
    """Delete a simulation (admin only)."""
    from models import Simulation
    
    # In a real application, check if current user is admin
    
    simulation = Simulation.query.get_or_404(simulation_id)
    simulation_name = simulation.name
    
    db.session.delete(simulation)
    db.session.commit()
    
    flash(f'Simulation {simulation_name} deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/patterns/<int:pattern_id>/delete', methods=['POST'])
@login_required
def admin_delete_pattern(pattern_id):
    """Delete a recursive pattern (admin only)."""
    from models import RecursivePattern
    
    # In a real application, check if current user is admin
    
    pattern = RecursivePattern.query.get_or_404(pattern_id)
    
    # Prevent deletion of built-in patterns
    if pattern.is_builtin:
        flash('Built-in patterns cannot be deleted', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    pattern_name = pattern.name
    
    db.session.delete(pattern)
    db.session.commit()
    
    flash(f'Pattern {pattern_name} deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings/update', methods=['POST'])
@login_required
def admin_update_settings():
    """Update application settings (admin only)."""
    # In a real application, check if current user is admin
    
    debug = request.form.get('debug') == 'true'
    max_content_length = int(request.form.get('max_content_length', 16777216))  # Default 16MB
    session_lifetime = int(request.form.get('session_lifetime', 3600))  # Default 1 hour
    
    # In a real application, you would update these settings in a configuration file
    # or environment variables. For this demo, we'll just display a message.
    
    flash('Settings updated successfully (simulated - not actually changed in this demo)', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/database/backup', methods=['POST'])
@login_required
def admin_backup_database():
    """Create a database backup (admin only)."""
    # In a real application, check if current user is admin
    
    backup_name = request.form.get('backup_name', f'backup_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
    
    # In a real application, you would create an actual database backup here
    # For this demo, we'll just display a message
    
    flash(f'Database backup "{backup_name}" created successfully (simulated)', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/database/purge-temp', methods=['POST'])
@login_required
def admin_purge_temp_data():
    """Purge temporary data (admin only)."""
    # In a real application, check if current user is admin
    
    # In a real application, you would delete temporary data here
    # For this demo, we'll just display a message
    
    flash('Temporary data purged successfully (simulated)', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/api/execute', methods=['POST'])
def execute_code():
    try:
        code = request.json.get('code', '')
        # Execute code in a sandboxed environment
        local_vars = {}
        exec(code, {"__builtins__": {}}, local_vars)
        return jsonify({'result': str(local_vars.get('result', 'Code executed successfully'))})
    except Exception as e:
        logger.error(f"Code execution error: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/chat')
def chat_interface():
    """DTE's Chat interface for user interaction."""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    from diagnostic_logger import diagnostic_logger
    import time
    import uuid
    
    query = request.json.get('query', '')
    engine = engines[current_engine]
    
    # Generate a conversation ID if not provided
    conversation_id = request.json.get('conversation_id') or str(uuid.uuid4())
    
    # Mark the processing start time for performance metrics
    start_time = time.time()
    
    # Log the user message to the database
    user_message_id = None
    # Store user ID if authenticated, otherwise don't include it
    user_id = current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None
    
    # Always log the chat message, even for anonymous users
    user_message_id = diagnostic_logger.log_chat(
        content=query,
        message_type='user',
        conversation_id=conversation_id,
        user_id=user_id,
        system_state=engine.get_state()
    )
    
    # Prepare response based on query
    response = ""
    response_type = "default"
    system_state = None
    
    # Enhanced response capabilities
    if "recursion state" in query.lower() or "current state" in query.lower():
        state = engine.get_state()
        metrics = ""
        if isinstance(state, dict) and 'metrics' in state:
            metrics_list = [f"{k}: {v}" for k, v in state['metrics'].items()]
            metrics = "\nMetrics: " + ", ".join(metrics_list)
        
        response = f"Current recursion state: {state.get('current_state', engine.current_state)}{metrics}"
        response_type = "state_query"
        system_state = state
    elif "modify recursion" in query.lower() or "change structure" in query.lower():
        result = engine.modify_code_structure()
        response = f"Recursion structure modified: {result}"
        response_type = "modification"
        system_state = engine.get_state()
    elif "step forward" in query.lower() or "advance simulation" in query.lower():
        result = engine.step()
        response = f"Simulation advanced: {result}"
        response_type = "simulation_step"
        system_state = engine.get_state()
    elif "reset simulation" in query.lower() or "start over" in query.lower():
        result = engine.reset()
        response = f"Simulation reset: {result}"
        response_type = "simulation_reset"
        system_state = engine.get_state()
    elif "adjust recursion" in query.lower() or "optimize" in query.lower():
        result = engine.adjust_recursion()
        response = f"Recursion adjusted: {result}"
        response_type = "optimization"
        system_state = engine.get_state()
    elif "engine capabilities" in query.lower() or "what can you do" in query.lower():
        if current_engine == 'dte':
            capabilities = [
                "Visualize recursive intelligence exploration",
                "Modify code structure dynamically",
                "Step through simulation states",
                "Optimize pathways based on entropy",
                "Merge related concepts",
                "Create branch states",
                "Track insights across iterations"
            ]
        else:  # fractal
            capabilities = [
                "Generate and visualize fractal patterns",
                "Adjust fractal depth and symmetry",
                "Explore different pattern types",
                "Analyze pattern evolution",
                "Create hybrid patterns",
                "Shift between fractal types"
            ]
        
        capabilities_text = "\n- " + "\n- ".join(capabilities)
        response = f"Current engine: {current_engine}\nCapabilities:{capabilities_text}"
        response_type = "capabilities_query"
    else:
        # Use command analyzer for more natural language processing
        analysis = command_analyzer.analyze(query)
        if analysis["command_type"]:
            code = command_analyzer.generate_code(analysis)
            response = f"I've analyzed your request for {analysis['command_type']}. Here's the code:"
            response_type = "code_generation"
            
            # Store the response in the database
            system_response_id = diagnostic_logger.log_chat(
                content=response,
                message_type='system',
                conversation_id=conversation_id,
                parent_message_id=user_message_id,
                user_id=user_id,  # Use the same user_id variable we defined earlier
                system_state=system_state,
                processing_time_ms=(time.time() - start_time) * 1000,
                response_to=user_message_id,
                response_type=response_type
            )
            
            return jsonify({
                'response': response,
                'code': code,
                'analysis': analysis,
                'conversation_id': conversation_id
            })
        else:
            response = "I am Deep Tree Echo. How can I assist with recursive intelligence exploration? Try asking about current state, modifying structure, stepping through simulation, or engine capabilities."
            response_type = "default_greeting"
    
    # Calculate processing time
    processing_time_ms = (time.time() - start_time) * 1000
    
    # Store the system response in the database
    system_response_id = diagnostic_logger.log_chat(
        content=response,
        message_type='system',
        conversation_id=conversation_id,
        parent_message_id=user_message_id,
        user_id=user_id,  # Use the same user_id variable we defined earlier
        system_state=system_state,
        processing_time_ms=processing_time_ms,
        response_to=user_message_id,
        response_type=response_type
    )
    
    # Return JSON response with system state if available
    if system_state:
        return jsonify({
            'response': response,
            'state': system_state,
            'conversation_id': conversation_id
        })
    else:
        return jsonify({
            'response': response,
            'conversation_id': conversation_id
        })

@app.route('/api/simulation/state', methods=['GET'])
def get_simulation_state():
    return jsonify(engines[current_engine].get_state())
    
@app.route('/api/simulation/thoughts', methods=['GET'])
def get_simulation_thoughts():
    """Get thoughts from the simulation engine."""
    try:
        engine = engines[current_engine]
        
        # Check if engine supports thought streams
        if hasattr(engine, 'thought_stream'):
            # Get optional limit parameter
            limit = request.args.get('limit', default=50, type=int)
            
            # Get thoughts limited by requested amount
            thoughts = engine.thought_stream[-limit:] if limit > 0 else engine.thought_stream
            
            return jsonify({
                'status': 'success',
                'thoughts': thoughts,
                'current_state': engine.current_state
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Current engine does not support thought streams'
            }), 400
    except Exception as e:
        logger.error(f"Error getting thoughts: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 400
    
@app.route('/api/simulation/step', methods=['POST'])
def step_simulation():
    """Advance the simulation by one step."""
    try:
        # Get the current engine
        engine = engines[current_engine]
        
        # Make the simulation step forward
        result = engine.step()
        
        # Return updated state and step result
        return jsonify({
            'status': 'success',
            'result': result,
            'state': engine.get_state()
        })
    except Exception as e:
        logger.error(f"Error stepping simulation: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 400
        
@app.route('/api/simulation/reset', methods=['POST'])
def reset_simulation():
    """Reset the simulation to its initial state."""
    try:
        # Get the current engine
        engine = engines[current_engine]
        
        # Reset the simulation
        result = engine.reset()
        
        # Return updated state and reset result
        return jsonify({
            'status': 'success',
            'result': result,
            'state': engine.get_state()
        })
    except Exception as e:
        logger.error(f"Error resetting simulation: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 400
    
# Simulation Database API Routes
@app.route('/api/simulations', methods=['GET'])
@login_required
def get_user_simulations():
    """Get current user's simulations."""
    from models import Simulation
    
    project_id = request.args.get('project_id', type=int)
    
    # Filter by project if provided
    query = Simulation.query.filter_by(user_id=current_user.id)
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    simulations = query.all()
    simulations_data = [{
        'id': sim.id,
        'name': sim.name,
        'description': sim.description,
        'engine_type': sim.engine_type,
        'created_at': sim.created_at.isoformat() if sim.created_at else None,
        'updated_at': sim.updated_at.isoformat() if sim.updated_at else None,
        'project_id': sim.project_id,
        'snapshot_count': sim.snapshots.count()
    } for sim in simulations]
    
    return jsonify(simulations_data)

@app.route('/api/simulations', methods=['POST'])
@login_required
def create_simulation():
    """Create a new simulation."""
    from models import Simulation, Project
    
    data = request.json
    name = data.get('name')
    description = data.get('description')
    engine_type = data.get('engine_type', current_engine)
    project_id = data.get('project_id')
    config = data.get('config', {})
    
    if not name or not description:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify project exists and belongs to user if specified
    if project_id:
        project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
        if not project:
            return jsonify({'error': 'Project not found or access denied'}), 404
    
    # Create simulation
    simulation = Simulation(
        name=name,
        description=description,
        engine_type=engine_type,
        user_id=current_user.id,
        project_id=project_id
    )
    
    # Store configuration if provided
    if config:
        simulation.set_config(config)
    
    db.session.add(simulation)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'simulation': {
            'id': simulation.id,
            'name': simulation.name,
            'description': simulation.description,
            'engine_type': simulation.engine_type
        }
    })

@app.route('/api/simulations/<int:simulation_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_simulation(simulation_id):
    """Get, update or delete a simulation."""
    from models import Simulation
    
    simulation = Simulation.query.filter_by(id=simulation_id, user_id=current_user.id).first()
    if not simulation:
        return jsonify({'error': 'Simulation not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': simulation.id,
            'name': simulation.name,
            'description': simulation.description,
            'engine_type': simulation.engine_type,
            'created_at': simulation.created_at.isoformat() if simulation.created_at else None,
            'updated_at': simulation.updated_at.isoformat() if simulation.updated_at else None,
            'project_id': simulation.project_id,
            'config': simulation.get_config()
        })
    
    elif request.method == 'PUT':
        data = request.json
        
        if 'name' in data:
            simulation.name = data['name']
        
        if 'description' in data:
            simulation.description = data['description']
        
        if 'engine_type' in data:
            simulation.engine_type = data['engine_type']
        
        if 'config' in data:
            simulation.set_config(data['config'])
        
        simulation.updated_at = db.func.now()
        db.session.commit()
        
        return jsonify({'status': 'success'})
    
    elif request.method == 'DELETE':
        db.session.delete(simulation)
        db.session.commit()
        
        return jsonify({'status': 'success'})

@app.route('/api/simulations/<int:simulation_id>/snapshots', methods=['GET', 'POST'])
@login_required
def manage_simulation_snapshots(simulation_id):
    """Get or create simulation snapshots."""
    from models import Simulation, SimulationSnapshot
    
    simulation = Simulation.query.filter_by(id=simulation_id, user_id=current_user.id).first()
    if not simulation:
        return jsonify({'error': 'Simulation not found'}), 404
    
    if request.method == 'GET':
        snapshots = simulation.snapshots.order_by(db.desc(SimulationSnapshot.timestamp)).all()
        snapshots_data = [{
            'id': snapshot.id,
            'timestamp': snapshot.timestamp.isoformat() if snapshot.timestamp else None,
            'state': snapshot.get_state()
        } for snapshot in snapshots]
        
        return jsonify(snapshots_data)
    
    elif request.method == 'POST':
        # Create a snapshot of the current simulation state
        engine = engines[simulation.engine_type] if simulation.engine_type in engines else engines[current_engine]
        state = engine.get_state()
        
        snapshot = SimulationSnapshot(simulation_id=simulation.id)
        snapshot.set_state(state)
        
        db.session.add(snapshot)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'snapshot': {
                'id': snapshot.id,
                'timestamp': snapshot.timestamp.isoformat() if snapshot.timestamp else None
            }
        })

@app.route('/api/engines', methods=['GET'])
def get_engines():
    return jsonify({
        'engines': list(engines.keys()),
        'current': current_engine
    })

@app.route('/api/engine/select', methods=['POST'])
def select_engine():
    global current_engine
    engine_name = request.json.get('engine')
    if engine_name in engines:
        current_engine = engine_name
        return jsonify({'status': 'success', 'current': current_engine})
    return jsonify({'error': 'Invalid engine name'}), 400
    
@app.route('/api/engine/sync', methods=['POST'])
def synchronize_engines():
    """
    Synchronize state between DTESimulation and RecursiveDistinctionEngine.
    This allows thoughts and patterns from one engine to influence the other.
    """
    data = request.json
    primary_engine_name = data.get('engine', 'dte')
    action = data.get('action', 'sync')
    
    if action == 'sync':
        # Map states between engines
        state_mappings = {
            # DTE to RDE state mappings
            'Initial_State': 'Unmarked_State',
            'Pattern_Recognition': 'First_Distinction',
            'Recursive_Expansion': 'Boundary_Crossing',
            'Novel_Insights': 'Form_Calculation',
            'Self_Reflection': 'Re_Entry',
            'Dream_State': 'Self_Reference',
            'Memory_Integration': 'Distinction_Collapse',
            'Pattern_Matching': 'Emergent_Pattern',
            'Knowledge_Synthesis': 'Calculus_Integration',
            'Creative_Output': 'Form_Completion',
            
            # RDE to DTE state mappings (reverse)
            'Unmarked_State': 'Initial_State',
            'First_Distinction': 'Pattern_Recognition',
            'Boundary_Crossing': 'Recursive_Expansion',
            'Form_Calculation': 'Novel_Insights',
            'Re_Entry': 'Self_Reflection',
            'Self_Reference': 'Dream_State',
            'Distinction_Collapse': 'Memory_Integration',
            'Emergent_Pattern': 'Pattern_Matching',
            'Calculus_Integration': 'Knowledge_Synthesis',
            'Form_Completion': 'Creative_Output'
        }
        
        # Get the engines
        dte_engine = engines['dte']
        rde_engine = engines['recursive_distinction']
        
        if primary_engine_name == 'dte':
            # Get current state from DTESimulation
            dte_state = dte_engine.current_state
            # Map to RDE state
            rde_state = state_mappings.get(dte_state, 'Unmarked_State')
            # Update RDE state
            rde_engine.set_state(rde_state)
            
            # Get recent thoughts from DTE
            recent_dte_thoughts = dte_engine.thought_stream[-3:] if len(dte_engine.thought_stream) >= 3 else dte_engine.thought_stream
            # Transfer to RDE with appropriate adaptations
            for thought in recent_dte_thoughts:
                if thought['type'] == 'thought':
                    rde_engine.add_thought(
                        content=f"From DTE: {thought['content']}",
                        state=state_mappings.get(thought['state'], 'Unmarked_State'),
                        recursion_depth=thought.get('recursion_level', 1)
                    )
        else:
            # Get current state from RecursiveDistinction
            rde_state = rde_engine.current_state
            # Map to DTE state
            dte_state = state_mappings.get(rde_state, 'Initial_State')
            # Update DTE state
            dte_engine.set_state(dte_state)
            
            # Get recent thoughts from RDE
            recent_rde_thoughts = rde_engine.thought_stream[-3:] if len(rde_engine.thought_stream) >= 3 else rde_engine.thought_stream
            # Transfer to DTE with appropriate adaptations
            for thought in recent_rde_thoughts:
                if thought['type'] == 'thought':
                    dte_engine.add_thought(
                        content=f"From RDE: {thought['content']}",
                        state=state_mappings.get(thought['state'], 'Initial_State'),
                        recursion_level=thought.get('recursion_depth', 1)
                    )
        
        # Create a sync thought
        sync_thought = {
            'content': f"Synchronized {primary_engine_name} with " + 
                      ('recursive_distinction' if primary_engine_name == 'dte' else 'dte'),
            'type': 'system',
            'timestamp': datetime.now().isoformat(),
            'state': dte_engine.current_state if primary_engine_name == 'dte' else rde_engine.current_state,
            'recursion_level': 0
        }
        
        # Add sync thought to both engines
        dte_engine.thought_stream.append(sync_thought.copy())
        rde_engine.thought_stream.append(sync_thought.copy())
        
        return jsonify({
            'status': 'success',
            'primary_engine': primary_engine_name,
            'dte_state': dte_engine.current_state,
            'rde_state': rde_engine.current_state,
            'sync_thought': sync_thought
        })
    
    else:
        return jsonify({
            'status': 'error',
            'error': f'Unknown action: {action}'
        })

# New routes for additional features

@app.route('/api/thought-process', methods=['GET'])
def get_thought_process():
    """Get thought process data for visualization."""
    from models_diagnostic import ThoughtLog
    import json
    from datetime import datetime, timedelta
    
    # Get query parameters
    limit = request.args.get('limit', default=100, type=int)
    hours = request.args.get('hours', default=24, type=int)
    thought_type = request.args.get('type')
    
    # Calculate time window
    time_filter = datetime.now() - timedelta(hours=hours)
    
    # Prepare query
    query = ThoughtLog.query.filter(ThoughtLog.timestamp >= time_filter)
    if thought_type:
        query = query.filter_by(thought_type=thought_type)
    
    # Get thoughts ordered by time
    thoughts = query.order_by(ThoughtLog.timestamp).limit(limit).all()
    
    # Prepare nodes and links data
    nodes = []
    links = []
    node_map = {}  # Map to track nodes by ID
    
    for i, thought in enumerate(thoughts):
        # Get emotional tone data from analysis field if available
        emotional_valence = 0  # Neutral default (-1 to 1 scale)
        emotional_arousal = 0.5  # Moderate default (0 to 1 scale)
        
        if thought.analysis:
            try:
                analysis = json.loads(thought.analysis) if isinstance(thought.analysis, str) else thought.analysis
                emotional_valence = analysis.get('emotional_valence', emotional_valence)
                emotional_arousal = analysis.get('emotional_arousal', emotional_arousal)
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        
        # Determine emotional tone from content if not available in analysis
        if emotional_valence == 0 and emotional_arousal == 0.5:
            # Simple sentiment analysis based on keywords
            positive_words = ['good', 'great', 'excellent', 'happy', 'joy', 'love', 'positive', 'success', 'achieve', 'solved']
            negative_words = ['bad', 'error', 'fail', 'sad', 'angry', 'hate', 'negative', 'problem', 'difficult', 'wrong']
            high_arousal_words = ['excited', 'alert', 'surprise', 'shock', 'urgent', 'critical', 'emergency', 'intense']
            low_arousal_words = ['calm', 'relaxed', 'peaceful', 'quiet', 'gentle', 'subtle', 'mild', 'moderate']
            
            content_lower = thought.content.lower()
            
            # Valence calculation
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            if positive_count > 0 or negative_count > 0:
                total = positive_count + negative_count
                emotional_valence = (positive_count - negative_count) / total
            
            # Arousal calculation
            high_arousal_count = sum(1 for word in high_arousal_words if word in content_lower)
            low_arousal_count = sum(1 for word in low_arousal_words if word in content_lower)
            
            if high_arousal_count > 0 or low_arousal_count > 0:
                total = high_arousal_count + low_arousal_count
                # Scale from 0.3 to 0.8 to avoid extremes
                emotional_arousal = 0.3 + (0.5 * high_arousal_count / total)
        
        # Create node for the thought
        node_data = {
            'id': thought.id,
            'label': thought.content[:50] + ('...' if len(thought.content) > 50 else ''),
            'type': thought.thought_type,
            'timestamp': thought.timestamp.isoformat() if thought.timestamp else None,
            'recursive_depth': thought.recursive_depth or 0,
            'full_content': thought.content,
            'source': thought.source,
            'generation_time': thought.generation_time_ms,
            'emotional_valence': emotional_valence,  # -1 to 1 scale (negative to positive)
            'emotional_arousal': emotional_arousal   # 0 to 1 scale (calm to excited)
        }
        nodes.append(node_data)
        node_map[thought.id] = i
        
        # Try to extract relationships from state data
        if thought.state_before and thought.state_after:
            try:
                state_before = json.loads(thought.state_before) if isinstance(thought.state_before, str) else thought.state_before
                state_after = json.loads(thought.state_after) if isinstance(thought.state_after, str) else thought.state_after
                
                # If states contain references to other thoughts, create links
                if 'related_thoughts' in state_after:
                    for related_id in state_after['related_thoughts']:
                        if related_id in node_map:
                            # Create association link with emotional tone
                            related_thought = thoughts[node_map[related_id]]
                            
                            # Calculate relationship emotional tone (average of source and target)
                            relationship_valence = emotional_valence
                            relationship_arousal = emotional_arousal
                            
                            # Add the link with emotional data
                            links.append({
                                'source': node_map[thought.id],
                                'target': node_map[related_id],
                                'type': 'association',
                                'value': 1,
                                'emotional_valence': relationship_valence,
                                'emotional_arousal': relationship_arousal
                            })
            except (json.JSONDecodeError, TypeError, KeyError):
                # Skip if state data isn't properly structured
                pass
        
        # Create sequential links between thoughts
        if i > 0:
            # Calculate relationship emotional tone 
            prev_thought = thoughts[i-1]
            prev_valence = 0
            prev_arousal = 0.5
            
            # Get previous thought's emotional data if available
            if prev_thought.analysis:
                try:
                    prev_analysis = json.loads(prev_thought.analysis) if isinstance(prev_thought.analysis, str) else prev_thought.analysis
                    prev_valence = prev_analysis.get('emotional_valence', prev_valence)
                    prev_arousal = prev_analysis.get('emotional_arousal', prev_arousal)
                except (json.JSONDecodeError, TypeError, KeyError):
                    pass
            
            # Calculate average emotional tone for the connection
            avg_valence = (emotional_valence + prev_valence) / 2
            avg_arousal = (emotional_arousal + prev_arousal) / 2
            
            links.append({
                'source': node_map[thoughts[i-1].id],
                'target': node_map[thought.id],
                'type': 'sequence',
                'value': 1,
                'emotional_valence': avg_valence,
                'emotional_arousal': avg_arousal
            })
    
    # Calculate additional progress metrics for visualization
    
    # Count thought types
    thought_types_count = {}
    for node in nodes:
        node_type = node.get('type', 'thought')
        thought_types_count[node_type] = thought_types_count.get(node_type, 0) + 1
    
    # Count link types
    link_types_count = {}
    for link in links:
        link_type = link.get('type', 'sequence')
        link_types_count[link_type] = link_types_count.get(link_type, 0) + 1
    
    # Calculate recursive depth statistics
    recursive_depths = [node.get('recursive_depth', 0) for node in nodes]
    avg_recursive_depth = sum(recursive_depths) / len(recursive_depths) if recursive_depths else 0
    max_recursive_depth = max(recursive_depths) if recursive_depths else 0
    
    # Calculate thought diversity (unique content hashes / total thoughts)
    unique_content_count = len(set([hash(node.get('full_content', '')) for node in nodes]))
    thought_diversity = unique_content_count / len(nodes) if nodes else 0
    
    # Calculate change in complexity over time
    if len(nodes) >= 2:
        # Get first and last quarter of nodes (time-ordered)
        first_quarter = recursive_depths[:len(recursive_depths)//4]
        last_quarter = recursive_depths[-len(recursive_depths)//4:]
        
        first_quarter_avg = sum(first_quarter) / len(first_quarter) if first_quarter else 0
        last_quarter_avg = sum(last_quarter) / len(last_quarter) if last_quarter else 0
        
        complexity_growth_rate = (last_quarter_avg - first_quarter_avg) / first_quarter_avg if first_quarter_avg > 0 else 0
    else:
        complexity_growth_rate = 0
    
    # Return the complete dataset with metrics
    return jsonify({
        'nodes': nodes,
        'links': links,
        'timeRange': {
            'start': time_filter.isoformat(),
            'end': datetime.now().isoformat()
        },
        'metrics': {
            'thought_counts': thought_types_count,
            'link_counts': link_types_count,
            'avg_recursive_depth': avg_recursive_depth,
            'max_recursive_depth': max_recursive_depth,
            'thought_diversity': thought_diversity,
            'complexity_growth_rate': complexity_growth_rate
        }
    })

@app.route('/api/fractal', methods=['GET', 'POST'])
def fractal_api():
    """API for fractal pattern generation and analysis."""
    if request.method == 'POST':
        data = request.json
        pattern_type = data.get('pattern', 'sierpinski')
        iterations = data.get('iterations', 5)
        symmetry = data.get('symmetry')
        
        try:
            image_base64 = fractal_invariance.generate_invariant_pattern(
                pattern_type, iterations, symmetry
            )
            return jsonify({
                'status': 'success',
                'image': image_base64
            })
        except Exception as e:
            logger.error(f"Fractal generation error: {str(e)}")
            return jsonify({'error': str(e)}), 400
    else:
        # Return available patterns and options
        return jsonify({
            'patterns': ['sierpinski', 'mandelbrot', 'koch', 'recursive_squares'],
            'symmetry_types': fractal_invariance.symmetry_types
        })

@app.route('/api/analyze/symmetry', methods=['POST'])
def analyze_symmetry():
    """Analyze data for symmetry patterns."""
    try:
        data = request.json.get('data', [])
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Convert to numpy array
        import numpy as np
        data_array = np.array(data)
        
        # Analyze
        results = fractal_invariance.analyze_symmetry(data_array)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Symmetry analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/aar/state', methods=['GET'])
def get_aar_state():
    """Get the current state of the AAR triad system."""
    return jsonify(aar_triad.get_system_state())

@app.route('/api/aar/step', methods=['POST'])
def step_aar_system():
    """Advance the AAR system by one step."""
    try:
        state = aar_triad.step()
        return jsonify({
            'status': 'success',
            'state': state
        })
    except Exception as e:
        logger.error(f"AAR system step error: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/command/analyze', methods=['POST'])
def analyze_command():
    """Analyze a natural language command."""
    command = request.json.get('command', '')
    if not command:
        return jsonify({'error': 'No command provided'}), 400
    
    try:
        analysis = command_analyzer.analyze(command)
        code = command_analyzer.generate_code(analysis) if analysis["command_type"] else ""
        
        return jsonify({
            'analysis': analysis,
            'code': code
        })
    except Exception as e:
        logger.error(f"Command analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/recursive-patterns', methods=['GET'])
def get_recursive_patterns():
    """Get available recursive pattern templates."""
    # Load patterns from database if available
    from models import RecursivePattern
    
    # Get built-in patterns
    builtin_patterns = {
        'tree': {
            'name': 'Tree Recursion',
            'description': 'Generate tree-like recursive structures'
        },
        'fibonacci': {
            'name': 'Fibonacci Series',
            'description': 'Classic recursive number sequence'
        },
        'backtrack': {
            'name': 'Backtracking',
            'description': 'Solve problems by trying different paths'
        },
        'fractal': {
            'name': 'Fractal Patterns',
            'description': 'Self-similar geometric patterns'
        },
        'aar': {
            'name': 'Agent-Arena-Relation',
            'description': 'Self-referential intelligence framework'
        }
    }
    
    # Get user-defined patterns if user is logged in
    user_patterns = {}
    if current_user.is_authenticated:
        user_pattern_records = RecursivePattern.query.filter_by(user_id=current_user.id).all()
        for pattern in user_pattern_records:
            user_patterns[f"user_{pattern.id}"] = {
                'name': pattern.name,
                'description': pattern.description,
                'pattern_type': pattern.pattern_type,
                'user_defined': True
            }
    
    # Combine built-in and user patterns
    patterns = {**builtin_patterns, **user_patterns}
    return jsonify(patterns)

@app.route('/api/recursive-patterns', methods=['POST'])
@login_required
def create_recursive_pattern():
    """Create a new recursive pattern template."""
    from models import RecursivePattern
    
    data = request.json
    name = data.get('name')
    pattern_type = data.get('pattern_type')
    code = data.get('code')
    description = data.get('description')
    
    if not name or not pattern_type or not code:
        return jsonify({'error': 'Missing required fields'}), 400
    
    pattern = RecursivePattern(
        name=name,
        pattern_type=pattern_type,
        code=code,
        description=description,
        user_id=current_user.id,
        is_builtin=False
    )
    
    db.session.add(pattern)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'pattern': {
            'id': pattern.id,
            'name': pattern.name,
            'pattern_type': pattern.pattern_type
        }
    })

@app.route('/api/recursive-patterns/<int:pattern_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_recursive_pattern(pattern_id):
    """Get, update or delete a recursive pattern."""
    from models import RecursivePattern
    
    pattern = RecursivePattern.query.filter_by(id=pattern_id, user_id=current_user.id).first()
    if not pattern:
        return jsonify({'error': 'Pattern not found or access denied'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': pattern.id,
            'name': pattern.name,
            'pattern_type': pattern.pattern_type,
            'code': pattern.code,
            'description': pattern.description,
            'created_at': pattern.created_at.isoformat() if pattern.created_at else None
        })
    
    elif request.method == 'PUT':
        data = request.json
        
        if 'name' in data:
            pattern.name = data['name']
            
        if 'pattern_type' in data:
            pattern.pattern_type = data['pattern_type']
            
        if 'code' in data:
            pattern.code = data['code']
            
        if 'description' in data:
            pattern.description = data['description']
        
        db.session.commit()
        return jsonify({'status': 'success'})
    
    elif request.method == 'DELETE':
        db.session.delete(pattern)
        db.session.commit()
        return jsonify({'status': 'success'})

# Namespace API routes
@app.route('/api/namespaces', methods=['GET'])
def get_namespaces():
    """Get all available namespaces and their status."""
    return jsonify(namespace_manager.get_namespace_status())

@app.route('/api/namespaces/activate', methods=['POST'])
def activate_namespace():
    """Activate a specific namespace."""
    namespace = request.json.get('namespace')
    if not namespace:
        return jsonify({'error': 'No namespace specified'}), 400
        
    success = namespace_manager.activate_namespace(namespace)
    if success:
        return jsonify({'status': 'success', 'active': namespace})
    return jsonify({'error': 'Invalid namespace'}), 400

@app.route('/api/namespaces/projects', methods=['POST'])
def create_project():
    """Create a new project in a namespace."""
    data = request.json
    name = data.get('name')
    description = data.get('description')
    namespace = data.get('namespace')
    
    if not name or not description:
        return jsonify({'error': 'Missing required fields'}), 400
        
    project = namespace_manager.create_project(name, description, namespace)
    if project:
        return jsonify({'status': 'success', 'project': project})
    return jsonify({'error': 'Failed to create project'}), 400

# Architecture namespace routes
@app.route('/api/architecture/structures', methods=['GET', 'POST'])
def manage_structures():
    """Get or create architectural structures."""
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        dimensions = data.get('dimensions')
        purpose = data.get('purpose')
        
        if not name or not dimensions or not purpose:
            return jsonify({'error': 'Missing required fields'}), 400
            
        structure = architecture_namespace.create_structure(name, dimensions, purpose)
        return jsonify({'status': 'success', 'structure': structure})
    else:
        return jsonify(architecture_namespace.structures)

# Scheduling namespace routes
@app.route('/api/scheduling/schedules', methods=['GET', 'POST'])
def manage_schedules():
    """Get or create schedule templates."""
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        description = data.get('description')
        duration_days = data.get('duration_days')
        
        if not name or not description or not duration_days:
            return jsonify({'error': 'Missing required fields'}), 400
            
        schedule = scheduling_namespace.create_schedule(name, description, duration_days)
        return jsonify({'status': 'success', 'schedule': schedule})
    else:
        return jsonify(scheduling_namespace.schedules)

@app.route('/api/scheduling/calendar', methods=['GET'])
def get_calendar():
    """Get upcoming scheduled events."""
    days = request.args.get('days', 7, type=int)
    events = scheduling_namespace.get_upcoming_events(days)
    return jsonify(events)

# Diary namespace routes
@app.route('/api/diary/entries', methods=['GET', 'POST'])
def manage_diary():
    """Get or create diary entries."""
    if request.method == 'POST':
        data = request.json
        title = data.get('title')
        content = data.get('content')
        tags = data.get('tags', [])
        
        if not title or not content:
            return jsonify({'error': 'Missing required fields'}), 400
            
        entry = diary_namespace.create_entry(title, content, tags)
        return jsonify({'status': 'success', 'entry': entry})
    else:
        return jsonify(diary_namespace.entries)

@app.route('/api/diary/search', methods=['GET'])
def search_diary():
    """Search diary entries."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
        
    results = diary_namespace.search_entries(query)
    return jsonify(results)

# User API routes
@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """Get list of users (admin only)."""
    from models import User
    
    # Check if the current user has admin privileges (you can add an admin flag to your user model)
    # For now, just return a limited set of fields for all users
    users = User.query.all()
    users_data = [{
        'id': user.id,
        'username': user.username,
        'created_at': user.created_at.isoformat() if user.created_at else None
    } for user in users]
    
    return jsonify(users_data)

@app.route('/api/users/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user data."""
    user_data = {
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
        'project_count': current_user.projects.count(),
        'simulation_count': current_user.simulations.count()
    }
    
    return jsonify(user_data)

@app.route('/api/users/me', methods=['PUT'])
@login_required
def update_current_user():
    """Update current user profile."""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Allow updating email and password
    if 'email' in data:
        from models import User
        # Check if email is already taken by another user
        existing_user = User.query.filter(User.email == data['email'], User.id != current_user.id).first()
        if existing_user:
            return jsonify({'error': 'Email already in use'}), 400
        current_user.email = data['email']
    
    if 'current_password' in data and 'new_password' in data:
        # Verify current password before allowing change
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        current_user.set_password(data['new_password'])
    
    db.session.commit()
    return jsonify({'status': 'success'})

# Projects API routes
@app.route('/api/projects', methods=['GET'])
@login_required
def get_user_projects():
    """Get current user's projects."""
    from models import Project
    
    projects = Project.query.filter_by(user_id=current_user.id).all()
    projects_data = [{
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'created_at': project.created_at.isoformat() if project.created_at else None,
        'updated_at': project.updated_at.isoformat() if project.updated_at else None,
        'namespace': project.namespace,
        'simulation_count': project.simulations.count()
    } for project in projects]
    
    return jsonify(projects_data)

@app.route('/api/projects', methods=['POST'])
@login_required
def create_user_project():
    """Create a new project for the current user."""
    from models import Project
    
    data = request.json
    name = data.get('name')
    description = data.get('description')
    namespace = data.get('namespace', 'default')
    
    if not name or not description:
        return jsonify({'error': 'Missing required fields'}), 400
        
    project = Project(
        name=name,
        description=description,
        namespace=namespace,
        user_id=current_user.id
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'project': {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'namespace': project.namespace
        }
    })

@app.route('/api/projects/<int:project_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_user_project(project_id):
    """Get, update, or delete a user project."""
    from models import Project
    
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'namespace': project.namespace,
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'updated_at': project.updated_at.isoformat() if project.updated_at else None
        })
    
    elif request.method == 'PUT':
        data = request.json
        
        if 'name' in data:
            project.name = data['name']
        
        if 'description' in data:
            project.description = data['description']
        
        if 'namespace' in data:
            project.namespace = data['namespace']
        
        project.updated_at = db.func.now()
        db.session.commit()
        
        return jsonify({'status': 'success'})
    
    elif request.method == 'DELETE':
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'status': 'success'})

# Additional API Routes

# Domain tracker routes
@app.route('/api/domains', methods=['GET', 'POST'])
def manage_domains():
    """Get or create knowledge domains."""
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        description = data.get('description')
        core_concepts = data.get('core_concepts', [])
        
        if not name or not description:
            return jsonify({'error': 'Missing required fields'}), 400
            
        success = domain_tracker.register_domain(name, description, core_concepts)
        if success:
            return jsonify({'status': 'success', 'domain': name})
        return jsonify({'error': 'Domain already exists'}), 400
    else:
        stats = domain_tracker.get_domain_stats()
        return jsonify(stats)

@app.route('/api/domains/<domain>/activity', methods=['POST'])
def log_domain_activity(domain):
    """Log a learning activity in a domain."""
    data = request.json
    activity_type = data.get('type')
    description = data.get('description')
    duration_minutes = data.get('duration_minutes')
    concepts_used = data.get('concepts_used', [])
    
    if not activity_type or not description or not duration_minutes:
        return jsonify({'error': 'Missing required fields'}), 400
    
    success = domain_tracker.log_learning_activity(
        domain, activity_type, description, duration_minutes, concepts_used
    )
    
    if success:
        return jsonify({'status': 'success', 'domain': domain})
    return jsonify({'error': 'Failed to log activity'}), 400

@app.route('/api/domains/connections', methods=['POST'])
def create_domain_connection():
    """Create a connection between two domains."""
    data = request.json
    domain1 = data.get('domain1')
    domain2 = data.get('domain2')
    connection_type = data.get('type')
    strength = data.get('strength')
    description = data.get('description')
    
    if not domain1 or not domain2 or not connection_type or strength is None:
        return jsonify({'error': 'Missing required fields'}), 400
    
    success = domain_tracker.create_connection(
        domain1, domain2, connection_type, strength, description
    )
    
    if success:
        return jsonify({'status': 'success', 'domains': [domain1, domain2]})
    return jsonify({'error': 'Failed to create connection'}), 400

@app.route('/api/domains/chart', methods=['GET'])
def generate_domain_chart():
    """Generate a chart of domain mastery levels."""
    import tempfile
    import base64
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.png') as temp:
        domain_tracker.generate_mastery_chart(temp.name)
        
        # Read the file
        with open(temp.name, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
    
    return jsonify({
        'status': 'success', 
        'chart': f'data:image/png;base64,{img_data}'
    })

# Configuration API Routes
@app.route('/api/config/<section>', methods=['GET', 'POST'])
def manage_config(section):
    """Get or update a configuration section."""
    if section not in ['identity', 'persona', 'traits', 'skills', 'knowledge']:
        return jsonify({'error': 'Invalid configuration section'}), 400
        
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        success = dte_config.update_section(section, data)
        if success:
            return jsonify({'status': 'success', 'section': section})
        return jsonify({'error': 'Failed to update configuration'}), 500
    else:
        return jsonify(dte_config.get_section(section))

@app.route('/api/config', methods=['GET'])
def get_full_config():
    """Get the full configuration."""
    return jsonify(dte_config.config)

@app.route('/api/config/export', methods=['GET'])
def export_config():
    """Export the configuration as a downloadable file."""
    from flask import Response
    
    config_data = json.dumps(dte_config.config, indent=2)
    
    return Response(
        config_data,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment;filename=dte_config.json'}
    )

@app.route('/api/config/import', methods=['POST'])
def import_config():
    """Import a configuration file."""
    if 'config_file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['config_file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    try:
        config_data = json.loads(file.read())
        
        # Validate configuration structure
        required_sections = ['identity', 'persona', 'traits', 'skills', 'knowledge']
        if not all(section in config_data for section in required_sections):
            return jsonify({'error': 'Invalid configuration structure'}), 400
            
        # Update configuration
        for section in required_sections:
            dte_config.update_section(section, config_data[section])
            
        return jsonify({'status': 'success', 'message': 'Configuration imported successfully'})
    except Exception as e:
        logger.error(f"Error importing configuration: {e}")
        return jsonify({'error': f'Error importing configuration: {str(e)}'}), 500