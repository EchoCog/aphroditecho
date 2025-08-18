
// Pattern Wizard for Deep Tree Echo
// Facilitates creation of recursive patterns for exploration

const patternWizard = {
    currentStep: 1,
    selectedPattern: null,
    configuration: {},
    
    // Pattern templates with generators
    patterns: {
        'fractal_tree': {
            name: 'Fractal Tree',
            description: 'Tree-like recursive structures with branching patterns',
            config: {
                'iterations': { type: 'number', default: 5, min: 1, max: 12, label: 'Iterations' },
                'angle': { type: 'number', default: 25, min: 10, max: 45, label: 'Branch Angle (degrees)' },
                'reduction': { type: 'number', default: 0.75, min: 0.5, max: 0.9, step: 0.05, label: 'Size Reduction Factor' }
            },
            generate: (config) => {
                return `
import matplotlib.pyplot as plt
import numpy as np

def draw_tree(x, y, length, angle, iterations):
    if iterations == 0:
        return
    
    # Calculate endpoint
    x2 = x + length * np.cos(np.radians(angle))
    y2 = y + length * np.sin(np.radians(angle))
    
    # Draw the branch
    plt.plot([x, x2], [y, y2], 'k-', linewidth=iterations/2)
    
    # Recursive calls for branches
    new_length = length * ${config.reduction}
    draw_tree(x2, y2, new_length, angle + ${config.angle}, iterations - 1)
    draw_tree(x2, y2, new_length, angle - ${config.angle}, iterations - 1)

# Set up plot
plt.figure(figsize=(10, 8))
plt.axis('equal')
plt.axis('off')

# Start drawing from bottom center, pointing up
draw_tree(0, -1, 0.5, 90, ${config.iterations})

plt.tight_layout()
plt.savefig('fractal_tree.png')
plt.close()

print("Fractal tree generated with ${config.iterations} iterations")
                `;
            }
        },
        'aar_simulation': {
            name: 'Agent-Arena-Relation Simulation',
            description: 'Self-referential intelligence framework simulation',
            config: {
                'agents': { type: 'number', default: 3, min: 1, max: 10, label: 'Number of Agents' },
                'arena_size': { type: 'number', default: 10, min: 5, max: 30, label: 'Arena Size' },
                'iterations': { type: 'number', default: 20, min: 5, max: 100, label: 'Simulation Iterations' }
            },
            generate: (config) => {
                return `
from aar_system import AARTriad
import matplotlib.pyplot as plt
import networkx as nx
import random

# Initialize the AAR system
aar = AARTriad()

# Create agents
agent_names = ["Agent" + str(i+1) for i in range(${config.agents})]
for name in agent_names:
    capabilities = random.sample(["observe", "modify", "analyze", "create", "destroy"], 
                                k=random.randint(2, 4))
    aar.create_agent(name, capabilities)

# Create arena
arena_name = "RecursiveSpace"
aar.create_arena(arena_name, (${config.arena_size}, ${config.arena_size}))

# Create relations
for agent in agent_names:
    relation_name = f"{agent}InSpace"
    aar.create_relation(relation_name, agent, arena_name)

# Run simulation
results = []
for i in range(${config.iterations}):
    state = aar.step()
    results.append(state)
    print(f"Iteration {i+1}: {len(state['agents'])} agents, {len(state['relations'])} relations")

# Visualize final state as a graph
G = nx.DiGraph()

# Add agent nodes
for agent in aar.agents.values():
    G.add_node(agent.name, type='agent')

# Add arena nodes
for arena in aar.arenas.values():
    G.add_node(arena.name, type='arena')

# Add relation edges
for relation in aar.relations.values():
    G.add_edge(relation.agent_name, relation.arena_name, label=relation.name)

# Plot the graph
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G)
agent_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'agent']
arena_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'arena']

nx.draw_networkx_nodes(G, pos, nodelist=agent_nodes, node_color='skyblue', node_size=500)
nx.draw_networkx_nodes(G, pos, nodelist=arena_nodes, node_color='lightgreen', node_size=800)
nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True)
nx.draw_networkx_labels(G, pos)

plt.axis('off')
plt.title('AAR Triad System Simulation')
plt.tight_layout()
plt.savefig('aar_simulation.png')
plt.close()

print("AAR simulation completed with ${config.iterations} iterations")
                `;
            }
        },
        'recursive_fibonacci': {
            name: 'Fibonacci Visualization',
            description: 'Visual representation of the Fibonacci sequence',
            config: {
                'terms': { type: 'number', default: 10, min: 5, max: 20, label: 'Number of Terms' },
                'visual_style': { type: 'select', options: ['spiral', 'tree', 'blocks'], default: 'spiral', label: 'Visualization Style' }
            },
            generate: (config) => {
                const style = config.visual_style;
                if (style === 'spiral') {
                    return `
import matplotlib.pyplot as plt
import numpy as np

def fibonacci(n):
    """Generate first n Fibonacci numbers"""
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence

# Generate sequence
fib_sequence = fibonacci(${config.terms})
print(f"Fibonacci sequence: {fib_sequence}")

# Create spiral visualization
golden_angle = np.pi * (3 - np.sqrt(5))  # Golden angle in radians

plt.figure(figsize=(10, 10))
theta = np.zeros(len(fib_sequence))
radius = np.zeros(len(fib_sequence))

for i in range(len(fib_sequence)):
    theta[i] = i * golden_angle
    radius[i] = np.sqrt(fib_sequence[i])
    
    # Plot point
    x = radius[i] * np.cos(theta[i])
    y = radius[i] * np.sin(theta[i])
    
    circle = plt.Circle((x, y), radius[i]/10, 
                        alpha=0.6, 
                        fc=plt.cm.viridis(i/len(fib_sequence)))
    plt.gca().add_patch(circle)
    plt.text(x, y, str(fib_sequence[i]), 
             ha='center', va='center', fontsize=8)

plt.axis('equal')
plt.title('Fibonacci Spiral')
plt.axis('off')
plt.tight_layout()
plt.savefig('fibonacci_spiral.png')
plt.close()

print(f"Fibonacci visualization created with {len(fib_sequence)} terms")
                    `;
                } else if (style === 'tree') {
                    return `
import matplotlib.pyplot as plt
import networkx as nx

def fibonacci(n):
    """Generate first n Fibonacci numbers with their call tree"""
    memo = {}
    calls = []
    
    def fib(k):
        calls.append(k)
        if k in memo:
            return memo[k]
        if k <= 1:
            memo[k] = k
            return k
        memo[k] = fib(k-1) + fib(k-2)
        return memo[k]
    
    # Generate sequence
    sequence = [fib(i) for i in range(${config.terms})]
    return sequence, calls

# Generate sequence and call tree
fib_sequence, call_history = fibonacci(${config.terms}-1)
print(f"Fibonacci sequence: {fib_sequence}")

# Create call graph
G = nx.DiGraph()

# Add edges for each parent-child call
for i in range(1, len(call_history)):
    parent = call_history[i-1]
    child = call_history[i]
    G.add_edge(f"fib({parent})", f"fib({child})")

# Draw the graph
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, seed=42)
nx.draw(G, pos, with_labels=True, node_color='lightblue', 
        node_size=700, font_size=8, arrows=True)
plt.title('Fibonacci Call Tree')
plt.tight_layout()
plt.savefig('fibonacci_tree.png')
plt.close()

print(f"Fibonacci call tree visualization created")
                    `;
                } else {
                    return `
import matplotlib.pyplot as plt
import numpy as np

def fibonacci(n):
    """Generate first n Fibonacci numbers"""
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence

# Generate sequence
fib_sequence = fibonacci(${config.terms})
print(f"Fibonacci sequence: {fib_sequence}")

# Create block visualization
plt.figure(figsize=(12, 6))
for i, val in enumerate(fib_sequence):
    # Draw rectangles with area proportional to fibonacci value
    if val == 0:
        continue  # Skip first element (0)
    width = np.sqrt(val)
    height = np.sqrt(val)
    
    # Position blocks in a grid
    row = i // 5
    col = i % 5
    
    x = col * 2.5
    y = row * 2.5
    
    rect = plt.Rectangle((x, y), width, height, 
                        facecolor=plt.cm.viridis(i/len(fib_sequence)),
                        alpha=0.8, edgecolor='black')
    plt.gca().add_patch(rect)
    plt.text(x + width/2, y + height/2, str(val), 
             ha='center', va='center')

plt.axis('equal')
plt.title('Fibonacci Blocks')
plt.xlim(-0.5, 12.5)
plt.ylim(-0.5, 7.5)
plt.axis('off')
plt.tight_layout()
plt.savefig('fibonacci_blocks.png')
plt.close()

print(f"Fibonacci block visualization created with {len(fib_sequence)} terms")
                    `;
                }
            }
        }
    },
    
    initialize: function() {
        document.getElementById('wizard-prev').addEventListener('click', () => {
            if (this.currentStep > 1) {
                this.showStep(this.currentStep - 1);
            }
        });
        
        document.getElementById('wizard-next').addEventListener('click', () => {
            if (this.currentStep === 1 && !this.selectedPattern) {
                alert('Please select a recursion pattern');
                return;
            }
            
            if (this.currentStep === 1) {
                this.createConfigForm(this.selectedPattern);
            } else if (this.currentStep === 2) {
                // Gather configuration
                this.configuration = {};
                const pattern = this.patterns[this.selectedPattern];
                
                Object.keys(pattern.config).forEach(key => {
                    const inputEl = document.getElementById('config-' + key);
                    if (inputEl) {
                        if (inputEl.type === 'checkbox') {
                            this.configuration[key] = inputEl.checked;
                        } else {
                            this.configuration[key] = inputEl.value;
                        }
                    }
                });
                
                // Generate and show preview
                const generatedCode = pattern.generate(this.configuration);
                document.getElementById('preview-code').value = generatedCode;
            } else if (this.currentStep === 3) {
                // Create and execute pattern
                this.executePattern();
                return;
            }
            
            this.showStep(this.currentStep + 1);
        });
        
        // Set up pattern selection
        this.setupPatternSelection();
    },
    
    setupPatternSelection: function() {
        const container = document.getElementById('pattern-selection');
        if (!container) return;
        
        container.innerHTML = '';
        
        // Create pattern tiles
        Object.keys(this.patterns).forEach(patternKey => {
            const pattern = this.patterns[patternKey];
            
            const tile = document.createElement('div');
            tile.className = 'pattern-tile';
            tile.setAttribute('data-pattern', patternKey);
            
            tile.innerHTML = `
                <h5>${pattern.name}</h5>
                <p>${pattern.description}</p>
            `;
            
            tile.addEventListener('click', () => {
                document.querySelectorAll('.pattern-tile').forEach(t => {
                    t.classList.remove('active');
                });
                tile.classList.add('active');
                this.selectedPattern = patternKey;
            });
            
            container.appendChild(tile);
        });
    },
    
    createConfigForm: function(patternKey) {
        const configForm = document.getElementById('recursion-config');
        if (!configForm) return;
        
        configForm.innerHTML = '';
        const pattern = this.patterns[patternKey];
        
        Object.keys(pattern.config).forEach(key => {
            const config = pattern.config[key];
            const formGroup = document.createElement('div');
            formGroup.className = 'mb-3';
            
            const label = document.createElement('label');
            label.className = 'form-label';
            label.setAttribute('for', 'config-' + key);
            label.textContent = config.label || key;
            
            let input;
            
            if (config.type === 'select') {
                input = document.createElement('select');
                config.options.forEach(option => {
                    const optEl = document.createElement('option');
                    optEl.value = option;
                    optEl.textContent = option.charAt(0).toUpperCase() + option.slice(1);
                    if (option === config.default) {
                        optEl.selected = true;
                    }
                    input.appendChild(optEl);
                });
            } else {
                input = document.createElement('input');
                input.type = config.type || 'text';
                
                if (config.type === 'number') {
                    input.min = config.min;
                    input.max = config.max;
                    if (config.step) input.step = config.step;
                }
                
                input.value = config.default;
            }
            
            input.className = 'form-control';
            input.id = 'config-' + key;
            
            formGroup.appendChild(label);
            formGroup.appendChild(input);
            configForm.appendChild(formGroup);
        });
    },
    
    showStep: function(stepNumber) {
        document.querySelectorAll('.wizard-step').forEach(step => {
            step.style.display = 'none';
        });
        
        document.getElementById('wizard-step-' + stepNumber).style.display = 'block';
        this.currentStep = stepNumber;
        
        // Update buttons
        document.getElementById('wizard-prev').style.display = stepNumber === 1 ? 'none' : 'block';
        
        const nextButton = document.getElementById('wizard-next');
        if (stepNumber === 3) {
            nextButton.textContent = 'Create Pattern';
        } else {
            nextButton.textContent = 'Next';
        }
    },
    
    executePattern: function() {
        const code = document.getElementById('preview-code').value;
        
        // Submit code for execution
        fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                alert('Pattern executed successfully: ' + data.result);
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('wizardModal'));
                if (modal) modal.hide();
                
                // Reset wizard
                this.showStep(1);
                this.selectedPattern = null;
                this.configuration = {};
                document.querySelectorAll('.pattern-tile').forEach(tile => {
                    tile.classList.remove('active');
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while executing the pattern. Please try again.');
        });
    }
};

// Initialize pattern wizard when document is ready
document.addEventListener('DOMContentLoaded', function() {
    patternWizard.initialize();
});
