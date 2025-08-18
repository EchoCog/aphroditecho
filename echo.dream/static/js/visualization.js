// Initialize force-directed graph
const width = document.getElementById('visualization').clientWidth;
const height = 300;

const svg = d3.select("#visualization")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

const simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(d => d.id))
    .force("charge", d3.forceManyBody().strength(-100))
    .force("center", d3.forceCenter(width / 2, height / 2));

// Engine selector handling
const engineSelector = document.getElementById('engine-selector');
engineSelector.addEventListener('change', async () => {
    const response = await fetch('/api/engine/select', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ engine: engineSelector.value })
    });
    if (response.ok) {
        updateVisualization();
    }
});

// Update visualization
async function updateVisualization() {
    const response = await fetch('/api/simulation/state');
    const data = await response.json();

    // Clear previous visualization
    svg.selectAll("*").remove();

    const link = svg.append("g")
        .selectAll("line")
        .data(data.links)
        .enter().append("line")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6);

    const node = svg.append("g")
        .selectAll("circle")
        .data(data.nodes)
        .enter().append("circle")
        .attr("r", 5)
        .attr("fill", "#69b3a2");

    // Add labels to nodes
    const labels = svg.append("g")
        .selectAll("text")
        .data(data.nodes)
        .enter().append("text")
        .attr("x", 8)
        .attr("y", ".31em")
        .text(d => d.id)
        .style("font-size", "10px")
        .style("fill", "#fff");

    simulation
        .nodes(data.nodes)
        .on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            labels
                .attr("x", d => d.x + 8)
                .attr("y", d => d.y + 3);
        });

    simulation.force("link")
        .links(data.links);

    simulation.alpha(1).restart();
}

// Initialize engine selection
async function initializeEngines() {
    const response = await fetch('/api/engines');
    const data = await response.json();
    engineSelector.value = data.current;
}

// Update visualization periodically
setInterval(updateVisualization, 5000);
initializeEngines();
updateVisualization();