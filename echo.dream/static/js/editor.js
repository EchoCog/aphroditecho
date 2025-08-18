// Initialize CodeMirror editor
const editor = CodeMirror.fromTextArea(document.getElementById("code-editor"), {
    mode: "python",
    theme: "monokai",
    lineNumbers: true,
    indentUnit: 4,
    autofocus: true
});

// Handle code execution
document.getElementById("run-code").addEventListener("click", async () => {
    const code = editor.getValue();
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code })
        });
        const data = await response.json();
        if (data.error) {
            alert(`Error: ${data.error}`);
        } else {
            alert(`Result: ${data.result}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});
