
// Deep Tree Echo Configuration Interface

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Forms
    const identityForm = document.getElementById('identity-form');
    const personaForm = document.getElementById('persona-form');
    const traitsForm = document.getElementById('traits-form');
    const addDomainForm = document.getElementById('add-domain-form');
    const saveDomainBtn = document.getElementById('save-domain-btn');
    
    // Knowledge Graph
    initKnowledgeGraph();
    
    // Skill Tree
    initSkillTree();
    
    // Event Listeners
    if (identityForm) {
        identityForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveIdentityConfig();
        });
    }
    
    if (personaForm) {
        personaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            savePersonaConfig();
        });
    }
    
    if (traitsForm) {
        traitsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveTraitsConfig();
        });
    }
    
    if (saveDomainBtn) {
        saveDomainBtn.addEventListener('click', function() {
            saveDomain();
        });
    }
    
    // Domain list event listeners
    const domainList = document.getElementById('domain-list');
    if (domainList) {
        domainList.querySelectorAll('a').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                // Remove active class from all items
                domainList.querySelectorAll('a').forEach(i => i.classList.remove('active'));
                // Add active class to clicked item
                this.classList.add('active');
                // Update knowledge graph for selected domain
                updateKnowledgeGraph(this.dataset.domain);
            });
        });
    }
    
    // Skill categories event listeners
    const skillCategories = document.getElementById('skill-categories');
    if (skillCategories) {
        skillCategories.querySelectorAll('a').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                // Remove active class from all items
                skillCategories.querySelectorAll('a').forEach(i => i.classList.remove('active'));
                // Add active class to clicked item
                this.classList.add('active');
                // Update skill tree for selected category
                updateSkillTree(this.dataset.category);
            });
        });
    }
});

// Configuration Saving Functions
function saveIdentityConfig() {
    const corePurpose = document.getElementById('core-purpose').value;
    const corePrinciples = document.getElementById('core-principles').value;
    const coreValues = document.getElementById('core-values').value;
    
    const config = {
        core_purpose: corePurpose,
        core_principles: corePrinciples,
        core_values: coreValues
    };
    
    saveConfig('identity', config);
}

function savePersonaConfig() {
    const communicationStyle = document.getElementById('communication-style').value;
    const interactionPatterns = document.getElementById('interaction-patterns').value;
    const responseFormat = document.getElementById('response-format').value;
    
    const config = {
        communication_style: communicationStyle,
        interaction_patterns: interactionPatterns,
        response_format: responseFormat
    };
    
    saveConfig('persona', config);
}

function saveTraitsConfig() {
    const openness = document.getElementById('openness').value;
    const conscientiousness = document.getElementById('conscientiousness').value;
    const logic = document.getElementById('logic').value;
    const learningStyle = document.getElementById('learning-style').value;
    const problemSolving = document.getElementById('problem-solving').value;
    
    const config = {
        openness: parseInt(openness),
        conscientiousness: parseInt(conscientiousness),
        logic: parseInt(logic),
        learning_style: learningStyle,
        problem_solving: problemSolving
    };
    
    saveConfig('traits', config);
}

function saveDomain() {
    const domainName = document.getElementById('domain-name').value;
    const domainDescription = document.getElementById('domain-description').value;
    const domainConcepts = document.getElementById('domain-core-concepts').value;
    
    if (!domainName || !domainDescription) {
        alert('Domain name and description are required');
        return;
    }
    
    const domainData = {
        name: domainName,
        description: domainDescription,
        core_concepts: domainConcepts.split(',').map(c => c.trim())
    };
    
    fetch('/api/domains', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(domainData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addDomainModal'));
            modal.hide();
            
            // Add domain to list
            const domainList = document.getElementById('domain-list');
            const newDomain = document.createElement('a');
            newDomain.href = '#';
            newDomain.className = 'list-group-item list-group-item-action';
            newDomain.dataset.domain = domainName.toLowerCase().replace(/\s+/g, '-');
            newDomain.textContent = domainName;
            domainList.appendChild(newDomain);
            
            // Clear form
            document.getElementById('domain-name').value = '';
            document.getElementById('domain-description').value = '';
            document.getElementById('domain-core-concepts').value = '';
            
            // Update knowledge graph
            updateKnowledgeGraph(domainName.toLowerCase().replace(/\s+/g, '-'));
        } else {
            alert('Error creating domain: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while saving the domain');
    });
}

function saveConfig(section, data) {
    fetch(`/api/config/${section}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(`${section.charAt(0).toUpperCase() + section.slice(1)} configuration saved successfully`);
        } else {
            alert(`Error saving ${section} configuration: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`An error occurred while saving ${section} configuration`);
    });
}

function showToast(message) {
    // Create toast element
    const toastContainer = document.createElement('div');
    toastContainer.style.position = 'fixed';
    toastContainer.style.bottom = '20px';
    toastContainer.style.right = '20px';
    toastContainer.style.zIndex = '1050';
    
    const toast = document.createElement('div');
    toast.className = 'toast show';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">Deep Tree Echo</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    document.body.appendChild(toastContainer);
    
    // Auto hide after 3 seconds
    setTimeout(() => {
        document.body.removeChild(toastContainer);
    }, 3000);
}

// Knowledge Graph Visualization
function initKnowledgeGraph() {
    const container = document.getElementById('knowledge-graph');
    if (!container) return;
    
    // Sample data - this would be replaced with actual domain data
    const nodes = [
        { id: 'architecture', label: 'Architecture', x: 0, y: 0, size: 15, color: '#5B9BD5' },
        { id: 'scheduling', label: 'Scheduling', x: 1, y: 1, size: 10, color: '#ED7D31' },
        { id: 'self-reflection', label: 'Self-Reflection', x: -1, y: 1, size: 12, color: '#A5A5A5' },
        { id: 'spatial', label: 'Spatial Organization', x: 0.5, y: -0.5, size: 8, color: '#70AD47' },
        { id: 'temporal', label: 'Temporal Organization', x: 1.5, y: 0.5, size: 8, color: '#4472C4' }
    ];
    
    const edges = [
        { id: 'e0', source: 'architecture', target: 'spatial' },
        { id: 'e1', source: 'scheduling', target: 'temporal' },
        { id: 'e2', source: 'architecture', target: 'self-reflection' },
        { id: 'e3', source: 'scheduling', target: 'self-reflection' },
        { id: 'e4', source: 'spatial', target: 'temporal', type: 'dotted' }
    ];
    
    // Initialize sigma.js
    try {
        const s = new sigma({
            graph: { nodes, edges },
            container: 'knowledge-graph',
            settings: {
                defaultNodeColor: '#5B9BD5',
                defaultEdgeColor: '#aaa',
                edgeColor: 'default',
                labelThreshold: 5,
                minEdgeSize: 0.5,
                maxEdgeSize: 2,
                minNodeSize: 1,
                maxNodeSize: 15
            }
        });
        
        // Store sigma instance for later use
        window.knowledgeGraph = s;
    } catch (e) {
        console.error('Error initializing knowledge graph:', e);
        container.innerHTML = '<div class="alert alert-danger">Error initializing knowledge graph visualization.</div>';
    }
}

function updateKnowledgeGraph(domain) {
    if (!window.knowledgeGraph) return;
    
    // In a real implementation, this would fetch domain data from the server
    // For now, we'll just highlight the selected domain
    const graph = window.knowledgeGraph.graph;
    
    graph.nodes().forEach(node => {
        if (node.id === domain) {
            graph.nodes(node.id).color = '#FF5733'; // Highlight color
            graph.nodes(node.id).size = 18;
        } else {
            graph.nodes(node.id).color = '#5B9BD5'; // Default color
            graph.nodes(node.id).size = node.originalSize || 10;
        }
    });
    
    window.knowledgeGraph.refresh();
}

// Skill Tree Visualization
function initSkillTree() {
    const container = document.getElementById('skill-tree');
    if (!container) return;
    
    // Initialize a tree visualization with D3.js
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    const svg = d3.select('#skill-tree')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    // Sample skill tree data
    const treeData = {
        name: "Skills",
        children: [
            {
                name: "Recursive Thinking",
                children: [
                    { name: "Self-reference", mastery: 0.7 },
                    { name: "Meta-cognition", mastery: 0.5 },
                    { name: "Nested structures", mastery: 0.8 }
                ]
            },
            {
                name: "Fractal Analysis",
                children: [
                    { name: "Pattern recognition", mastery: 0.6 },
                    { name: "Scale invariance", mastery: 0.4 },
                    { name: "Symmetry identification", mastery: 0.7 }
                ]
            },
            {
                name: "Systems Thinking",
                children: [
                    { name: "Emergent properties", mastery: 0.5 },
                    { name: "Feedback loops", mastery: 0.6 },
                    { name: "Network analysis", mastery: 0.3 }
                ]
            }
        ]
    };
    
    // Create a tree layout
    const treeLayout = d3.tree().size([width - 100, height - 100]);
    
    // Create a hierarchy from the data
    const root = d3.hierarchy(treeData);
    
    // Assign the data to the tree layout
    const tree = treeLayout(root);
    
    // Create links
    svg.selectAll('.link')
        .data(tree.links())
        .enter()
        .append('path')
        .attr('class', 'link')
        .attr('fill', 'none')
        .attr('stroke', '#555')
        .attr('d', d3.linkHorizontal()
            .x(d => d.y + 50)
            .y(d => d.x + 50));
    
    // Create nodes
    const nodes = svg.selectAll('.node')
        .data(tree.descendants())
        .enter()
        .append('g')
        .attr('class', 'node')
        .attr('transform', d => `translate(${d.y + 50},${d.x + 50})`);
    
    // Add circles to nodes
    nodes.append('circle')
        .attr('r', d => d.data.mastery ? d.data.mastery * 10 + 3 : 8)
        .attr('fill', d => {
            if (d.depth === 0) return '#333';
            if (d.depth === 1) return '#5B9BD5';
            
            // Color based on mastery for leaf nodes
            if (d.data.mastery) {
                const value = d.data.mastery;
                return d3.interpolateViridis(value);
            }
            
            return '#70AD47';
        });
    
    // Add labels to nodes
    nodes.append('text')
        .attr('dy', d => d.children ? -12 : 4)
        .attr('x', d => d.children ? -8 : 10)
        .attr('text-anchor', d => d.children ? 'end' : 'start')
        .text(d => d.data.name)
        .attr('fill', '#fff');
    
    // Store D3 selection for later use
    window.skillTree = svg;
}

function updateSkillTree(category) {
    // In a real implementation, this would update the skill tree based on the selected category
    console.log(`Updating skill tree for category: ${category}`);
    
    // This would be replaced with actual data fetching and visualization update
    if (!window.skillTree) return;
    
    // Highlight the category in the visualization
    window.skillTree.selectAll('.node circle')
        .attr('stroke', function(d) {
            if (d.data.name.toLowerCase() === category) {
                return '#FF5733';
            }
            return 'none';
        })
        .attr('stroke-width', function(d) {
            if (d.data.name.toLowerCase() === category) {
                return 3;
            }
            return 0;
        });
}
