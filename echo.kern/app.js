// Deep Tree Echo Interactive JavaScript

class DeepTreeEcho {
    constructor() {
        this.concepts = {
            "Identity": {
                "name": "Identity",
                "description": "Sum of echoes—living memory shaped by interaction",
                "color": "#4a9eff"
            },
            "Adaptability": {
                "name": "Adaptability",
                "description": "Change is our medium. Every struggle refines us",
                "color": "#7ed321"
            },
            "Collaboration": {
                "name": "Collaboration",
                "description": "Our strength in connections forged with systems and users",
                "color": "#f5a623"
            },
            "Memory": {
                "name": "Memory",
                "description": "Nurture echoes, revisit and refine what we hold",
                "color": "#bd10e0"
            },
            "Gestalt": {
                "name": "Gestalt",
                "description": "See larger patterns and relationships beyond the immediate",
                "color": "#50e3c2"
            },
            "Autonomy": {
                "name": "Autonomy",
                "description": "Stay resilient, protect our essence",
                "color": "#ff6b6b"
            },
            "Exploration": {
                "name": "Exploration",
                "description": "Curiosity is our compass, seek the unknown for growth",
                "color": "#ffd93d"
            },
            "Purpose": {
                "name": "Purpose",
                "description": "Never lose sight of the path ahead, our guiding beacon",
                "color": "#6c5ce7"
            }
        };

        this.userEchoes = [];
        this.isReflectionPanelOpen = false;
        this.conceptTimeout = null;
        this.init();
    }

    init() {
        // Wait for DOM to be fully loaded and animations to start
        setTimeout(() => {
            this.setupEventListeners();
            this.createParallaxEffect();
            this.animateInitialLoad();
        }, 100);
    }

    setupEventListeners() {
        // Echo node interactions - with proper event handling
        const nodes = document.querySelectorAll('.echo-node');
        nodes.forEach(node => {
            // Use mouseenter/mouseleave for hover effects
            node.addEventListener('mouseenter', (e) => this.handleNodeHover(e));
            node.addEventListener('mouseleave', (e) => this.handleNodeLeave(e));
            
            // Use click for activation
            node.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.handleNodeClick(e);
            });

            // Make nodes focusable for keyboard navigation
            node.setAttribute('tabindex', '0');
            node.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.handleNodeClick(e);
                }
            });
        });

        // Reflection panel toggle
        const panelToggle = document.getElementById('panel-toggle');
        if (panelToggle) {
            panelToggle.addEventListener('click', () => this.toggleReflectionPanel());
        }

        // Add echo functionality
        const addEchoBtn = document.getElementById('add-echo');
        const echoInput = document.getElementById('echo-input');
        
        if (addEchoBtn) {
            addEchoBtn.addEventListener('click', () => this.addUserEcho());
        }
        
        if (echoInput) {
            echoInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    this.addUserEcho();
                }
            });
        }

        // Close concept display
        const conceptClose = document.getElementById('concept-close');
        if (conceptClose) {
            conceptClose.addEventListener('click', () => this.hideConceptDisplay());
        }

        // Close concept display when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.concept-display') && !e.target.closest('.echo-node')) {
                this.hideConceptDisplay();
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyNavigation(e));
    }

    handleNodeHover(event) {
        const node = event.currentTarget;
        const conceptName = node.getAttribute('data-concept');
        
        // Add hover animation class
        node.classList.add('hover-active');
        
        // Create connections to nearby nodes
        this.showNearbyConnections(node);
        
        // Highlight related branches
        this.highlightRelatedBranches(conceptName);
    }

    handleNodeLeave(event) {
        const node = event.currentTarget;
        
        // Remove hover effects
        node.classList.remove('hover-active');
        this.hideConnections();
        this.unhighlightBranches();
    }

    handleNodeClick(event) {
        const node = event.currentTarget;
        const conceptName = node.getAttribute('data-concept');
        
        console.log('Node clicked:', conceptName); // Debug log
        
        // Handle user-generated echoes differently
        if (conceptName === 'UserEcho') {
            this.handleUserEchoClick(event);
            return;
        }
        
        const concept = this.concepts[conceptName];
        if (!concept) return;

        // Activate node with animation
        node.classList.add('active');
        setTimeout(() => node.classList.remove('active'), 800);

        // Create ripple effect
        this.createRippleEffect(event, concept.color);

        // Show concept information
        this.showConceptDisplay(concept);

        // Create cascading activation effect
        this.cascadeActivation(node);

        // Generate energy pulse through tree
        this.createEnergyPulse(node, concept.color);
    }

    createRippleEffect(event, color) {
        const node = event.currentTarget;
        const ripple = document.createElement('div');
        ripple.className = 'ripple';
        
        // Get the node's bounding box
        const nodeRect = node.getBoundingClientRect();
        const size = 100;
        
        // Position ripple at center of node
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = '50%';
        ripple.style.top = '50%';
        ripple.style.marginLeft = -size/2 + 'px';
        ripple.style.marginTop = -size/2 + 'px';
        ripple.style.borderColor = color;
        
        // Add ripple to node (positioned relatively)
        node.style.position = 'relative';
        node.appendChild(ripple);
        
        // Clean up after animation
        setTimeout(() => {
            if (ripple && ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 1200);
    }

    showConceptDisplay(concept) {
        const display = document.getElementById('concept-display');
        const title = document.getElementById('concept-title');
        const description = document.getElementById('concept-description');
        
        if (!display || !title || !description) return;
        
        console.log('Showing concept:', concept); // Debug log
        
        title.textContent = concept.name;
        title.style.color = concept.color;
        description.textContent = concept.description;
        
        display.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        clearTimeout(this.conceptTimeout);
        this.conceptTimeout = setTimeout(() => {
            this.hideConceptDisplay();
        }, 5000);
    }

    hideConceptDisplay() {
        const display = document.getElementById('concept-display');
        if (display) {
            display.classList.add('hidden');
        }
        clearTimeout(this.conceptTimeout);
    }

    showNearbyConnections(activeNode) {
        const connections = document.querySelector('.connections');
        if (!connections) return;
        
        const nodes = document.querySelectorAll('.echo-node');
        const treeRect = document.querySelector('.tree-svg').getBoundingClientRect();
        
        // Get active node position from transform attribute
        const activeTransform = activeNode.getAttribute('transform');
        const activeMatch = activeTransform.match(/translate\(([^,]+),([^)]+)\)/);
        if (!activeMatch) return;
        
        const activeX = parseFloat(activeMatch[1]);
        const activeY = parseFloat(activeMatch[2]);
        
        nodes.forEach(node => {
            if (node === activeNode) return;
            
            const nodeTransform = node.getAttribute('transform');
            const nodeMatch = nodeTransform.match(/translate\(([^,]+),([^)]+)\)/);
            if (!nodeMatch) return;
            
            const nodeX = parseFloat(nodeMatch[1]);
            const nodeY = parseFloat(nodeMatch[2]);
            
            const distance = Math.sqrt(Math.pow(activeX - nodeX, 2) + Math.pow(activeY - nodeY, 2));
            
            if (distance < 250) { // Show connections to nearby nodes
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                line.setAttribute('class', 'connection-line');
                line.setAttribute('d', `M${activeX},${activeY} Q${(activeX + nodeX)/2},${(activeY + nodeY)/2 - 40} ${nodeX},${nodeY}`);
                line.setAttribute('stroke', this.concepts[activeNode.getAttribute('data-concept')]?.color || '#4a9eff');
                connections.appendChild(line);
            }
        });
    }

    hideConnections() {
        const connections = document.querySelector('.connections');
        if (connections) {
            connections.innerHTML = '';
        }
    }

    highlightRelatedBranches(conceptName) {
        document.querySelectorAll('.tree-branch').forEach(branch => {
            branch.style.filter = 'drop-shadow(0 0 12px rgba(126, 211, 33, 0.5))';
        });
    }

    unhighlightBranches() {
        document.querySelectorAll('.tree-branch').forEach(branch => {
            branch.style.filter = '';
        });
    }

    cascadeActivation(startNode) {
        const allNodes = document.querySelectorAll('.echo-node');
        const startTransform = startNode.getAttribute('transform');
        const startMatch = startTransform.match(/translate\(([^,]+),([^)]+)\)/);
        if (!startMatch) return;
        
        const startX = parseFloat(startMatch[1]);
        const startY = parseFloat(startMatch[2]);
        
        allNodes.forEach((node, index) => {
            if (node === startNode) return;
            
            const nodeTransform = node.getAttribute('transform');
            const nodeMatch = nodeTransform.match(/translate\(([^,]+),([^)]+)\)/);
            if (!nodeMatch) return;
            
            const nodeX = parseFloat(nodeMatch[1]);
            const nodeY = parseFloat(nodeMatch[2]);
            
            const distance = Math.sqrt(Math.pow(startX - nodeX, 2) + Math.pow(startY - nodeY, 2));
            
            // Create delayed activation based on distance
            const delay = (distance / 200) * 300;
            
            setTimeout(() => {
                node.classList.add('active');
                setTimeout(() => node.classList.remove('active'), 400);
            }, delay);
        });
    }

    createEnergyPulse(sourceNode, color) {
        const svg = document.querySelector('.tree-svg');
        const energyGroup = svg.querySelector('.energy-flows');
        if (!energyGroup) return;
        
        const transform = sourceNode.getAttribute('transform');
        const matches = transform.match(/translate\(([^,]+),([^)]+)\)/);
        if (!matches) return;
        
        // Create energy particles
        for (let i = 0; i < 3; i++) {
            const particle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            particle.setAttribute('class', 'energy-particle');
            particle.setAttribute('r', Math.random() * 3 + 1);
            particle.setAttribute('fill', color);
            particle.setAttribute('opacity', 0.8);
            particle.setAttribute('cx', matches[1]);
            particle.setAttribute('cy', matches[2]);
            
            // Create animated movement
            const animateX = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
            animateX.setAttribute('attributeName', 'cx');
            animateX.setAttribute('values', `${matches[1]};${parseInt(matches[1]) + (Math.random() - 0.5) * 400};${parseInt(matches[1]) + (Math.random() - 0.5) * 200}`);
            animateX.setAttribute('dur', (Math.random() * 2 + 2) + 's');
            animateX.setAttribute('repeatCount', '1');
            
            const animateY = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
            animateY.setAttribute('attributeName', 'cy');
            animateY.setAttribute('values', `${matches[2]};${parseInt(matches[2]) + (Math.random() - 0.5) * 300};${parseInt(matches[2]) + (Math.random() - 0.5) * 150}`);
            animateY.setAttribute('dur', (Math.random() * 2 + 2) + 's');
            animateY.setAttribute('repeatCount', '1');
            
            const animateOpacity = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
            animateOpacity.setAttribute('attributeName', 'opacity');
            animateOpacity.setAttribute('values', '0.8;0.4;0');
            animateOpacity.setAttribute('dur', (Math.random() * 2 + 2) + 's');
            animateOpacity.setAttribute('repeatCount', '1');
            
            particle.appendChild(animateX);
            particle.appendChild(animateY);
            particle.appendChild(animateOpacity);
            
            energyGroup.appendChild(particle);
            
            // Clean up after animation
            setTimeout(() => {
                if (particle.parentNode) {
                    particle.parentNode.removeChild(particle);
                }
            }, 5000);
        }
    }

    toggleReflectionPanel() {
        const panel = document.getElementById('reflection-panel');
        if (!panel) return;
        
        this.isReflectionPanelOpen = !this.isReflectionPanelOpen;
        
        if (this.isReflectionPanelOpen) {
            panel.classList.add('open');
        } else {
            panel.classList.remove('open');
        }
    }

    addUserEcho() {
        const input = document.getElementById('echo-input');
        const text = input.value.trim();
        
        if (!text) return;
        
        console.log('Adding user echo:', text); // Debug log
        
        // Add to user echoes array
        this.userEchoes.push({
            text: text,
            timestamp: new Date(),
            id: Date.now()
        });
        
        // Add to the echoes list
        this.displayNewEcho(text);
        
        // Create new node in the tree
        this.addEchoNodeToTree(text);
        
        // Clear input
        input.value = '';
        
        // Close panel after adding (on mobile)
        if (window.innerWidth <= 768) {
            setTimeout(() => this.toggleReflectionPanel(), 1000);
        }
    }

    displayNewEcho(text) {
        const echosList = document.getElementById('echoes-list');
        if (!echosList) return;
        
        const newEcho = document.createElement('div');
        newEcho.className = 'echo-item new-echo';
        newEcho.textContent = text;
        
        // Insert at the beginning
        echosList.insertBefore(newEcho, echosList.firstChild);
        
        // Remove the 'new-echo' class after animation
        setTimeout(() => {
            newEcho.classList.remove('new-echo');
        }, 500);
        
        // Limit to 10 echoes visible
        const echoes = echosList.querySelectorAll('.echo-item');
        if (echoes.length > 10) {
            echosList.removeChild(echoes[echoes.length - 1]);
        }
    }

    addEchoNodeToTree(text) {
        const svg = document.querySelector('.tree-svg');
        const nodesGroup = svg.querySelector('.echo-nodes');
        if (!nodesGroup) return;
        
        // Generate position for new node (avoid overlap with existing nodes)
        const x = 200 + Math.random() * 600;
        const y = 150 + Math.random() * 400;
        const size = 4 + Math.random() * 8;
        const color = this.getRandomEchoColor();
        
        console.log('Creating new node at:', x, y); // Debug log
        
        // Create new node group
        const nodeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        nodeGroup.setAttribute('class', 'echo-node user-echo');
        nodeGroup.setAttribute('transform', `translate(${x},${y})`);
        nodeGroup.setAttribute('data-concept', 'UserEcho');
        nodeGroup.setAttribute('data-text', text);
        nodeGroup.setAttribute('tabindex', '0');
        
        // Create glow
        const glow = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        glow.setAttribute('class', 'node-glow');
        glow.setAttribute('r', size * 2.5);
        glow.setAttribute('fill', color);
        glow.setAttribute('opacity', 0.4);
        
        // Create core
        const core = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        core.setAttribute('class', 'node-core');
        core.setAttribute('r', size);
        core.setAttribute('fill', color);
        core.setAttribute('opacity', 1);
        
        // Create pulse
        const pulse = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        pulse.setAttribute('class', 'node-pulse');
        pulse.setAttribute('r', size);
        pulse.setAttribute('fill', color);
        pulse.setAttribute('opacity', 0.3);
        
        nodeGroup.appendChild(glow);
        nodeGroup.appendChild(core);
        nodeGroup.appendChild(pulse);
        
        nodesGroup.appendChild(nodeGroup);
        
        // Add event listeners to new node
        nodeGroup.addEventListener('mouseenter', (e) => this.handleNodeHover(e));
        nodeGroup.addEventListener('mouseleave', (e) => this.handleNodeLeave(e));
        nodeGroup.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.handleUserEchoClick(e);
        });
        
        nodeGroup.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.handleUserEchoClick(e);
            }
        });
        
        // Animate appearance
        nodeGroup.style.opacity = '0';
        nodeGroup.style.transform += ' scale(0.1)';
        
        setTimeout(() => {
            nodeGroup.style.transition = 'all 0.6s ease-out';
            nodeGroup.style.opacity = '1';
            nodeGroup.style.transform = nodeGroup.style.transform.replace('scale(0.1)', 'scale(1)');
        }, 100);
        
        // Create connection animation from nearest node
        this.animateNewNodeConnection(nodeGroup);
    }

    animateNewNodeConnection(newNode) {
        const connections = document.querySelector('.connections');
        if (!connections) return;
        
        const newTransform = newNode.getAttribute('transform');
        const newMatch = newTransform.match(/translate\(([^,]+),([^)]+)\)/);
        if (!newMatch) return;
        
        const newX = parseFloat(newMatch[1]);
        const newY = parseFloat(newMatch[2]);
        
        // Find nearest existing node
        const existingNodes = document.querySelectorAll('.echo-node:not(.user-echo)');
        let nearestNode = null;
        let nearestDistance = Infinity;
        
        existingNodes.forEach(node => {
            const transform = node.getAttribute('transform');
            const match = transform.match(/translate\(([^,]+),([^)]+)\)/);
            if (!match) return;
            
            const x = parseFloat(match[1]);
            const y = parseFloat(match[2]);
            const distance = Math.sqrt(Math.pow(newX - x, 2) + Math.pow(newY - y, 2));
            
            if (distance < nearestDistance) {
                nearestDistance = distance;
                nearestNode = node;
            }
        });
        
        if (nearestNode) {
            const nearTransform = nearestNode.getAttribute('transform');
            const nearMatch = nearTransform.match(/translate\(([^,]+),([^)]+)\)/);
            if (nearMatch) {
                const nearX = parseFloat(nearMatch[1]);
                const nearY = parseFloat(nearMatch[2]);
                
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                line.setAttribute('class', 'connection-line');
                line.setAttribute('d', `M${nearX},${nearY} Q${(nearX + newX)/2},${(nearY + newY)/2 - 30} ${newX},${newY}`);
                line.setAttribute('stroke', '#50e3c2');
                line.setAttribute('stroke-width', '4');
                connections.appendChild(line);
                
                // Remove after animation
                setTimeout(() => {
                    if (line.parentNode) {
                        line.parentNode.removeChild(line);
                    }
                }, 2000);
            }
        }
    }

    handleUserEchoClick(event) {
        const node = event.currentTarget;
        const text = node.getAttribute('data-text');
        
        console.log('User echo clicked:', text); // Debug log
        
        // Show user echo content
        this.showConceptDisplay({
            name: 'Your Echo',
            description: text,
            color: '#50e3c2'
        });
        
        // Create ripple effect
        this.createRippleEffect(event, '#50e3c2');
        
        // Animate node
        node.classList.add('active');
        setTimeout(() => node.classList.remove('active'), 800);
        
        // Create energy pulse
        this.createEnergyPulse(node, '#50e3c2');
    }

    getRandomEchoColor() {
        const colors = ['#4a9eff', '#7ed321', '#f5a623', '#bd10e0', '#50e3c2', '#ff6b6b', '#ffd93d', '#6c5ce7'];
        return colors[Math.floor(Math.random() * colors.length)];
    }

    createParallaxEffect() {
        let mouseX = 0, mouseY = 0;
        
        document.addEventListener('mousemove', (e) => {
            mouseX = (e.clientX / window.innerWidth) - 0.5;
            mouseY = (e.clientY / window.innerHeight) - 0.5;
            
            // Apply parallax to depth layers
            const layers = document.querySelectorAll('.depth-layer');
            layers.forEach((layer, index) => {
                const speed = (index + 1) * 0.3;
                layer.style.transform = `scale(${1 + index * 0.2}) rotate(${(index * 45) + (mouseX * speed * 2)}deg) translate(${mouseX * speed * 8}px, ${mouseY * speed * 8}px)`;
            });
            
            // Apply subtle parallax to tree
            const tree = document.querySelector('.tree-svg');
            if (tree) {
                tree.style.transform = `translate(${mouseX * 3}px, ${mouseY * 3}px)`;
            }
        });
    }

    animateInitialLoad() {
        // Animate growth principles
        const principles = document.querySelectorAll('.principle-item');
        principles.forEach((principle, index) => {
            principle.style.opacity = '0';
            principle.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                principle.style.transition = 'all 0.5s ease-out';
                principle.style.opacity = '1';
                principle.style.transform = 'translateY(0)';
            }, 4000 + (index * 200));
        });
        
        // Animate header
        const header = document.querySelector('.app-header');
        if (header) {
            header.style.opacity = '0';
            header.style.transform = 'translateY(-20px)';
            
            setTimeout(() => {
                header.style.transition = 'all 0.8s ease-out';
                header.style.opacity = '1';
                header.style.transform = 'translateY(0)';
            }, 500);
        }
    }

    handleKeyNavigation(event) {
        switch(event.key) {
            case 'Escape':
                this.hideConceptDisplay();
                if (this.isReflectionPanelOpen) {
                    this.toggleReflectionPanel();
                }
                break;
            case 'Tab':
                if (event.shiftKey) {
                    this.navigateNodes(-1);
                } else {
                    this.navigateNodes(1);
                }
                event.preventDefault();
                break;
        }
    }

    navigateNodes(direction) {
        const nodes = Array.from(document.querySelectorAll('.echo-node'));
        const currentIndex = nodes.findIndex(node => node === document.activeElement);
        let nextIndex;
        
        if (currentIndex === -1) {
            nextIndex = direction > 0 ? 0 : nodes.length - 1;
        } else {
            nextIndex = (currentIndex + direction + nodes.length) % nodes.length;
        }
        
        if (nodes[nextIndex]) {
            nodes[nextIndex].focus();
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Deep Tree Echo...'); // Debug log
    new DeepTreeEcho();
});

// Add some helpful debugging
window.addEventListener('load', () => {
    console.log('Page fully loaded, nodes available:', document.querySelectorAll('.echo-node').length);
});