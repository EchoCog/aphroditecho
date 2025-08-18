/**
 * Deep Tree Echo Thought Stream
 * Visualizes the recursive system's internal thoughts, dreams, and insights
 * Enhanced with interactive animations and dynamic connections
 */

// Selectors
const thoughtStream = document.getElementById('thought-stream');
const autoScrollToggle = document.getElementById('autoScrollToggle');
const stepButton = document.getElementById('step-simulation');
const resetButton = document.getElementById('reset-simulation');
const filterButtons = document.querySelectorAll('[data-filter]');
// Get the engine selector (already defined in visualization.js)
let engineSelectorThought = document.getElementById('engine-selector');

// State
let currentFilter = 'all';
let thoughts = [];
let isPolling = true;
let pollingInterval = null;
let selectedThought = null;
let thoughtConnections = {};
let animationSpeed = 'normal'; // slow, normal, fast
let colorMode = 'default'; // default, depth, state, type

// Format the timestamp
function formatTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// Create a DOM element for a thought with animations and interactive elements
function createThoughtElement(thought) {
    // Store the thought ID for reference
    const thoughtId = thought.timestamp;
    
    // Create the main thought element
    const thoughtElement = document.createElement('div');
    thoughtElement.className = `thought-item ${thought.type}`;
    thoughtElement.dataset.type = thought.type;
    thoughtElement.dataset.id = thoughtId;
    thoughtElement.dataset.state = thought.state;
    
    // Type indicator with first letter capitalized
    const typeIndicator = thought.type.charAt(0).toUpperCase() + thought.type.slice(1);
    
    // Create header with type and state
    const header = document.createElement('div');
    header.className = 'thought-header';
    
    // Handle both recursion_level (used by DTESimulation) and recursion_depth (used by RecursiveDistinctionEngine)
    const recursionLevel = thought.recursion_level !== undefined ? thought.recursion_level : 
                          (thought.recursion_depth !== undefined ? thought.recursion_depth : 0);
    
    // Handle distinction_level for RecursiveDistinctionEngine if available
    const distinctionLevel = thought.distinction_level !== undefined ? thought.distinction_level : 0;
    
    // Create recursion level visualization dots
    const recursionVisual = document.createElement('div');
    recursionVisual.className = 'recursion-visual';
    
    // Add dots representing recursion level
    for (let i = 0; i < 5; i++) {
        const dot = document.createElement('span');
        dot.className = 'recursion-level';
        if (i < recursionLevel) {
            dot.classList.add('active');
        }
        recursionVisual.appendChild(dot);
    }
    
    // Create state label
    const stateLabel = document.createElement('span');
    stateLabel.className = 'state-label';
    stateLabel.textContent = `${thought.state.split('_')[0]}`;
    
    const headerText = document.createElement('span');
    headerText.textContent = `[${typeIndicator}] `;
    header.appendChild(headerText);
    header.appendChild(stateLabel);
    
    if (distinctionLevel > 0) {
        const distinctionInfo = document.createElement('span');
        distinctionInfo.className = 'distinction-info';
        distinctionInfo.textContent = ` D${distinctionLevel}`;
        header.appendChild(distinctionInfo);
    }
    
    header.appendChild(recursionVisual);
    
    // Timestamp
    const time = document.createElement('span');
    time.className = 'thought-time';
    time.textContent = formatTime(thought.timestamp);
    header.appendChild(time);
    
    // Content container with fade effect
    const contentContainer = document.createElement('div');
    contentContainer.className = 'thought-content-container';
    
    // Content
    const content = document.createElement('div');
    content.className = 'thought-content';
    content.textContent = thought.content;
    
    // Add fade overlay for long content
    const fade = document.createElement('div');
    fade.className = 'thought-fade';
    contentContainer.appendChild(content);
    contentContainer.appendChild(fade);
    
    // Expand button for long content
    const expand = document.createElement('div');
    expand.className = 'thought-expand';
    expand.textContent = 'Show more';
    expand.addEventListener('click', (e) => {
        e.stopPropagation();
        thoughtElement.classList.toggle('expanded');
        expand.textContent = thoughtElement.classList.contains('expanded') ? 'Show less' : 'Show more';
    });
    
    // Create footer with actions
    const footer = document.createElement('div');
    footer.className = 'thought-footer';
    
    // Action buttons
    const actions = document.createElement('div');
    actions.className = 'thought-actions';
    
    // Connect action - find related thoughts
    const connectAction = document.createElement('span');
    connectAction.className = 'thought-action';
    connectAction.textContent = '🔗 Connect';
    connectAction.addEventListener('click', (e) => {
        e.stopPropagation();
        highlightRelatedThoughts(thought);
    });
    
    // Focus action - isolate this thought thread
    const focusAction = document.createElement('span');
    focusAction.className = 'thought-action';
    focusAction.textContent = '👁️ Focus';
    focusAction.addEventListener('click', (e) => {
        e.stopPropagation();
        focusOnThoughtThread(thought);
    });
    
    // Pattern action - show pattern structure
    const patternAction = document.createElement('span');
    patternAction.className = 'thought-action';
    patternAction.textContent = '🧩 Pattern';
    patternAction.addEventListener('click', (e) => {
        e.stopPropagation();
        visualizePattern(thought);
    });
    
    // Add action buttons to footer
    actions.appendChild(connectAction);
    actions.appendChild(focusAction);
    actions.appendChild(patternAction);
    footer.appendChild(actions);
    
    // Add metadata info to footer
    const meta = document.createElement('div');
    meta.className = 'thought-meta';
    meta.textContent = `R:${recursionLevel} `;
    
    if (distinctionLevel > 0) {
        const distinctionBadge = document.createElement('span');
        distinctionBadge.className = 'distinction-badge';
        distinctionBadge.textContent = `D:${distinctionLevel}`;
        meta.appendChild(distinctionBadge);
    }
    
    footer.appendChild(meta);
    
    // Add click event to the thought element for selection
    thoughtElement.addEventListener('click', () => {
        selectThought(thought, thoughtElement);
    });
    
    // Append all elements
    thoughtElement.appendChild(header);
    thoughtElement.appendChild(contentContainer);
    thoughtElement.appendChild(expand);
    thoughtElement.appendChild(footer);
    
    // Apply animation delay based on recent
    // Newer thoughts animate in later for a cascade effect
    const animationDelay = Math.min(thoughts.length, 5) * 0.05;
    thoughtElement.style.animationDelay = `${animationDelay}s`;
    
    return thoughtElement;
}

// Add a single thought to the stream
function addThought(thought) {
    const element = createThoughtElement(thought);
    
    // Hide if filtered out
    if (currentFilter !== 'all' && thought.type !== currentFilter) {
        element.classList.add('hidden');
    }
    
    // Add to the stream
    thoughtStream.appendChild(element);
    
    // Auto scroll if enabled
    if (autoScrollToggle.checked) {
        thoughtStream.scrollTop = thoughtStream.scrollHeight;
    }
}

// Fetch thoughts from the API
async function fetchThoughts() {
    try {
        const response = await fetch('/api/simulation/thoughts');
        const data = await response.json();
        
        if (data.status === 'success') {
            // Get only new thoughts
            const newThoughts = data.thoughts.filter(thought => 
                !thoughts.some(t => t.timestamp === thought.timestamp && t.content === thought.content)
            );
            
            // Update our thoughts array
            thoughts = data.thoughts;
            
            // Add any new thoughts to the display
            newThoughts.forEach(thought => addThought(thought));
        } else {
            console.error("Error fetching thoughts:", data.message);
        }
    } catch (error) {
        console.error("Failed to fetch thoughts:", error);
    }
}

// Apply a filter to the thought stream
function applyFilter(filter) {
    currentFilter = filter;
    
    // Update active state on filter buttons
    filterButtons.forEach(button => {
        if (button.dataset.filter === filter) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
    
    // Show/hide thoughts based on filter
    const thoughtElements = thoughtStream.querySelectorAll('.thought-item');
    thoughtElements.forEach(element => {
        if (filter === 'all' || element.dataset.type === filter) {
            element.classList.remove('hidden');
        } else {
            element.classList.add('hidden');
        }
    });
}

// Step the simulation forward
async function stepSimulation() {
    try {
        const response = await fetch('/api/simulation/step', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log("Simulation stepped:", data.result);
            
            // Update visualization if available
            if (typeof updateVisualization === 'function' && data.state) {
                updateVisualization(data.state);
            }
            
            // Fetch new thoughts after a short delay to allow backend to generate them
            setTimeout(fetchThoughts, 300);
        } else {
            console.error("Error stepping simulation:", data.error);
        }
    } catch (error) {
        console.error("Failed to step simulation:", error);
    }
}

// Reset the simulation
async function resetSimulation() {
    if (!confirm("Are you sure you want to reset the simulation? This will clear all thoughts and return to the initial state.")) {
        return;
    }
    
    try {
        const response = await fetch('/api/simulation/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log("Simulation reset:", data.result);
            
            // Clear the thought stream
            thoughtStream.innerHTML = '';
            thoughts = [];
            
            // Update visualization if available
            if (typeof updateVisualization === 'function' && data.state) {
                updateVisualization(data.state);
            }
            
            // Fetch initial thoughts
            setTimeout(fetchThoughts, 300);
        } else {
            console.error("Error resetting simulation:", data.error);
        }
    } catch (error) {
        console.error("Failed to reset simulation:", error);
    }
}

// Start polling for thoughts
function startPolling() {
    if (isPolling) {
        // Initial fetch
        fetchThoughts();
        
        // Set up polling interval
        pollingInterval = setInterval(fetchThoughts, 5000); // Poll every 5 seconds
    }
}

// Stop polling for thoughts
function stopPolling() {
    isPolling = false;
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// Select a different engine
async function selectEngine(engineName) {
    try {
        const response = await fetch('/api/engine/select', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ engine: engineName })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log(`Switched to engine: ${data.current}`);
            
            // Clear the thought stream
            thoughtStream.innerHTML = '';
            thoughts = [];
            
            // Fetch initial thoughts from the new engine
            setTimeout(fetchThoughts, 300);
        } else {
            console.error("Error switching engine:", data.error);
        }
    } catch (error) {
        console.error("Failed to switch engine:", error);
    }
}

// Event listeners
filterButtons.forEach(button => {
    button.addEventListener('click', () => {
        applyFilter(button.dataset.filter);
    });
});

stepButton.addEventListener('click', stepSimulation);
resetButton.addEventListener('click', resetSimulation);

// Select and highlight a thought
function selectThought(thought, element) {
    // Remove selection from previous thought
    const previousSelected = document.querySelector('.thought-item.selected');
    if (previousSelected) {
        previousSelected.classList.remove('selected');
    }
    
    // Set the new selected thought
    selectedThought = thought;
    element.classList.add('selected');
    
    // Update any visualizations that depend on selection
    updateThoughtVisualizations(thought);
}

// Highlight thoughts related to the selected thought
function highlightRelatedThoughts(thought) {
    // Clear previous highlights
    document.querySelectorAll('.thought-item.related').forEach(el => {
        el.classList.remove('related');
    });
    
    // Find related thoughts based on:
    // 1. Same recursion level
    // 2. Sequential states in the same engine
    // 3. Pattern matches
    const thoughtElements = document.querySelectorAll('.thought-item');
    
    thoughtElements.forEach(el => {
        const elThought = thoughts.find(t => t.timestamp === el.dataset.id);
        if (!elThought) return;
        
        // Check for relation criteria
        const sameRecursionLevel = 
            (elThought.recursion_level !== undefined && 
             thought.recursion_level !== undefined &&
             elThought.recursion_level === thought.recursion_level) ||
            (elThought.recursion_depth !== undefined && 
             thought.recursion_depth !== undefined &&
             elThought.recursion_depth === thought.recursion_depth);
             
        const sameState = elThought.state === thought.state;
        const sequentialState = isSequentialState(thought, elThought);
        const patternMatch = hasPatternMatch(thought, elThought);
        
        // Highlight if related by any criteria
        if ((sameRecursionLevel && !sameState) || 
            sequentialState || 
            patternMatch) {
            el.classList.add('related');
        }
    });
    
    // Draw connection lines between related thoughts
    drawConnectionLines();
}

// Check if two thoughts have sequential states
function isSequentialState(thought1, thought2) {
    // For DTESimulation
    const dteStates = [
        'Initial_State', 'Pattern_Recognition', 'Recursive_Expansion',
        'Novel_Insights', 'Self_Reflection', 'Dream_State',
        'Memory_Integration', 'Pattern_Matching', 'Knowledge_Synthesis',
        'Creative_Output'
    ];
    
    // For RecursiveDistinctionEngine
    const rdeStates = [
        'Unmarked_State', 'First_Distinction', 'Boundary_Crossing',
        'Form_Calculation', 'Re_Entry', 'Self_Reference',
        'Distinction_Collapse', 'Emergent_Pattern', 'Calculus_Integration'
    ];
    
    // Determine which state sequence to use
    const states = thought1.recursion_depth !== undefined ? rdeStates : dteStates;
    
    // Get indices of states
    const index1 = states.indexOf(thought1.state);
    const index2 = states.indexOf(thought2.state);
    
    // Check if they're sequential (adjacent in the state array)
    return Math.abs(index1 - index2) === 1;
}

// Check if two thoughts have matching patterns
function hasPatternMatch(thought1, thought2) {
    // Simple content-based matching
    if (thought1.content && thought2.content) {
        // Look for shared key phrases (3+ words)
        const words1 = thought1.content.split(' ');
        const words2 = thought2.content.split(' ');
        
        for (let i = 0; i < words1.length - 2; i++) {
            const phrase = words1.slice(i, i + 3).join(' ').toLowerCase();
            if (thought2.content.toLowerCase().includes(phrase)) {
                return true;
            }
        }
    }
    
    // Return false if no pattern match found
    return false;
}

// Draw connection lines between related thoughts
function drawConnectionLines() {
    // Remove existing connection lines
    document.querySelectorAll('.thought-connection').forEach(el => el.remove());
    
    // Get all related thoughts
    const related = document.querySelectorAll('.thought-item.related');
    const selected = document.querySelector('.thought-item.selected');
    
    if (!selected || related.length === 0) return;
    
    // Get position of selected thought
    const selectedRect = selected.getBoundingClientRect();
    const streamRect = thoughtStream.getBoundingClientRect();
    
    // Draw lines from selected to each related thought
    related.forEach(el => {
        const relatedRect = el.getBoundingClientRect();
        
        // Create the connection line
        const line = document.createElement('div');
        line.className = 'thought-connection';
        
        // Calculate position and length of line (relative to thought stream)
        const top = Math.min(selectedRect.top, relatedRect.top) - streamRect.top + 10;
        const height = Math.abs(selectedRect.top - relatedRect.top);
        
        line.style.top = `${top}px`;
        line.style.height = `${height}px`;
        
        // Add line to thought stream
        thoughtStream.appendChild(line);
    });
}

// Focus on a specific thought thread
function focusOnThoughtThread(thought) {
    // Determine which thoughts belong to the same thread
    const threadThoughts = getThreadThoughts(thought);
    
    // Hide all thoughts not in the thread
    document.querySelectorAll('.thought-item').forEach(el => {
        const elId = el.dataset.id;
        if (!threadThoughts.some(t => t.timestamp === elId)) {
            el.classList.add('hidden');
        } else {
            el.classList.remove('hidden');
        }
    });
    
    // Add a "show all" button
    addShowAllButton();
}

// Get all thoughts in the same thread as the given thought
function getThreadThoughts(thought) {
    // For simplicity, get thoughts of same type and related states
    return thoughts.filter(t => 
        t.type === thought.type || 
        isSequentialState(thought, t) ||
        hasPatternMatch(thought, t)
    );
}

// Add a button to show all thoughts after filtering
function addShowAllButton() {
    // Remove existing button if any
    const existingButton = document.getElementById('show-all-button');
    if (existingButton) existingButton.remove();
    
    // Create new button
    const button = document.createElement('button');
    button.id = 'show-all-button';
    button.className = 'btn';
    button.textContent = 'Show All Thoughts';
    button.addEventListener('click', () => {
        // Show all thoughts (respecting current type filter)
        document.querySelectorAll('.thought-item').forEach(el => {
            if (currentFilter === 'all' || el.dataset.type === currentFilter) {
                el.classList.remove('hidden');
            }
        });
        button.remove();
    });
    
    // Add button to the top of the thought stream
    thoughtStream.insertAdjacentElement('afterbegin', button);
}

// Visualize pattern structure in a thought
function visualizePattern(thought) {
    // Create a popup for pattern visualization
    const popup = document.createElement('div');
    popup.className = 'pattern-popup';
    popup.innerHTML = `
        <div class="pattern-popup-header">
            <h3>Pattern Visualization</h3>
            <button class="pattern-popup-close">×</button>
        </div>
        <div class="pattern-popup-content">
            <div class="pattern-info">
                <div>Type: ${thought.type}</div>
                <div>State: ${thought.state}</div>
                <div>Recursion: ${thought.recursion_level || thought.recursion_depth || 0}</div>
                ${thought.distinction_level ? `<div>Distinction: ${thought.distinction_level}</div>` : ''}
            </div>
            <div class="pattern-structure" id="pattern-structure">
                <!-- Pattern structure visualization -->
            </div>
        </div>
    `;
    
    // Add the popup to the body
    document.body.appendChild(popup);
    
    // Close button functionality
    popup.querySelector('.pattern-popup-close').addEventListener('click', () => {
        popup.remove();
    });
    
    // Render pattern structure
    renderPatternStructure(thought, document.getElementById('pattern-structure'));
}

// Render the pattern structure of a thought
function renderPatternStructure(thought, container) {
    // Simple text-based representation for now
    container.innerHTML = `<div class="pattern-text">${processPatternText(thought.content)}</div>`;
}

// Process thought text to highlight patterns
function processPatternText(text) {
    if (!text) return '';
    
    // Highlight potential recursive patterns
    text = text.replace(/\(([^()]*)\)/g, '<span class="pattern-highlight">($1)</span>');
    
    // Highlight potential self-references
    text = text.replace(/\b(self|recursive|loop|pattern|cycle)\b/gi, 
                        '<span class="pattern-keyword">$1</span>');
    
    return text;
}

// Update visualizations based on selected thought
function updateThoughtVisualizations(thought) {
    // Update any additional visualizations here
    console.log('Selected thought:', thought);
    
    // If visualization.js has a function to update based on thought
    if (typeof updateVisualizationForThought === 'function') {
        updateVisualizationForThought(thought);
    }
}

// Sync DTESimulation with RecursiveDistinction
function syncEngines() {
    // Get current engine name
    const currentEngine = engineSelectorThought ? engineSelectorThought.value : 'DTESimulation';
    
    // Send sync request to the backend
    fetch('/api/engine/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            engine: currentEngine,
            action: 'sync'
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Engine sync result:', data);
        // Refresh thoughts after sync
        setTimeout(fetchThoughts, 300);
    })
    .catch(error => {
        console.error('Engine sync failed:', error);
    });
}

// Create sync button
function createSyncButton() {
    const controlPanel = document.querySelector('.controls') || document.getElementById('control-panel');
    
    if (controlPanel) {
        const syncButton = document.createElement('button');
        syncButton.id = 'sync-engines';
        syncButton.className = 'btn';
        syncButton.textContent = 'Sync Engines';
        syncButton.addEventListener('click', syncEngines);
        
        controlPanel.appendChild(syncButton);
    }
}

// Engine selector event listener
if (engineSelectorThought) {
    engineSelectorThought.addEventListener('change', () => {
        selectEngine(engineSelectorThought.value);
    });
}

// Start the thought stream when the page loads
document.addEventListener('DOMContentLoaded', () => {
    startPolling();
    // Add the sync button after the page loads
    createSyncButton();
    
    // Set up window resize handler for connection lines
    window.addEventListener('resize', () => {
        if (document.querySelector('.thought-item.related')) {
            drawConnectionLines();
        }
    });
});

// Clean up when navigating away
window.addEventListener('beforeunload', () => {
    stopPolling();
});