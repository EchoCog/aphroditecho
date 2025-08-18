
module Server

using HTTP
using JSON3
using Sockets
using ..ChatStore
using ..TerminalStore
using ..FileStore
using ..EditorStore
using ..StreamText
using ..MessageParser

export start_server

function start_server(port::Int = 5000)
    println("Starting Bolt.jl server on port $port...")
    
    # Create static file handler
    function serve_static(req::HTTP.Request)
        path = HTTP.URI(req.target).path
        
        if path == "/"
            return HTTP.Response(200, ["Content-Type" => "text/html"], html_template())
        elseif path == "/api/chat"
            return handle_chat_api(req)
        elseif path == "/api/enhancer"
            return handle_enhancer_api(req)
        elseif path == "/api/files"
            return handle_files_api(req)
        elseif path == "/api/terminal"
            return handle_terminal_api(req)
        elseif path == "/api/editor"
            return handle_editor_api(req)
        else
            return HTTP.Response(404, "Not Found")
        end
    end
    
    # Start the server
    HTTP.serve(serve_static, "0.0.0.0", port)
end

function html_template()::String
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bolt.jl - AI-Powered Development Environment</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #1a1a1a;
                color: #ffffff;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            
            .header {
                background: #2d2d2d;
                padding: 1rem;
                border-bottom: 1px solid #444;
            }
            
            .main-container {
                display: flex;
                flex: 1;
                overflow: hidden;
            }
            
            .sidebar {
                width: 250px;
                background: #252526;
                border-right: 1px solid #444;
                overflow-y: auto;
            }
            
            .content {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .chat-container {
                flex: 1;
                padding: 1rem;
                overflow-y: auto;
            }
            
            .input-container {
                padding: 1rem;
                border-top: 1px solid #444;
            }
            
            .input-box {
                width: 100%;
                padding: 0.75rem;
                background: #2d2d2d;
                border: 1px solid #444;
                border-radius: 8px;
                color: #fff;
                font-size: 14px;
            }
            
            .input-box:focus {
                outline: none;
                border-color: #007acc;
            }
            
            .message {
                margin-bottom: 1rem;
                padding: 0.75rem;
                border-radius: 8px;
            }
            
            .message.user {
                background: #007acc;
                margin-left: 2rem;
            }
            
            .message.assistant {
                background: #2d2d2d;
                margin-right: 2rem;
            }
            
            .file-tree {
                padding: 1rem;
            }
            
            .file-item {
                padding: 0.25rem 0;
                cursor: pointer;
                border-radius: 4px;
            }
            
            .file-item:hover {
                background: #37373d;
            }
            
            .terminal {
                background: #1e1e1e;
                padding: 1rem;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                height: 200px;
                overflow-y: auto;
                border-top: 1px solid #444;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Bolt.jl - AI Development Environment</h1>
        </div>
        
        <div class="main-container">
            <div class="sidebar">
                <div class="file-tree">
                    <h3>Explorer</h3>
                    <div id="file-list">
                        <div class="file-item">📁 src/</div>
                        <div class="file-item">📁 lib/</div>
                        <div class="file-item">📄 main.jl</div>
                        <div class="file-item">📄 Project.toml</div>
                    </div>
                </div>
            </div>
            
            <div class="content">
                <div class="chat-container" id="chat-container">
                    <div class="message assistant">
                        <strong>Bolt.jl Assistant:</strong><br>
                        Welcome to Bolt.jl! I'm your AI-powered development assistant. I can help you:
                        <ul style="margin-top: 0.5rem; margin-left: 1rem;">
                            <li>Write and debug Julia code</li>
                            <li>Create and manage files</li>
                            <li>Run terminal commands</li>
                            <li>Build complete applications</li>
                        </ul>
                        <br>
                        How can I help you today?
                    </div>
                </div>
                
                <div class="input-container">
                    <input type="text" id="message-input" class="input-box" 
                           placeholder="Ask me anything about development..." 
                           onkeypress="handleKeyPress(event)">
                </div>
                
                <div class="terminal" id="terminal">
                    <div>Bolt.jl Terminal</div>
                    <div>Type 'help' for available commands</div>
                    <div>julia> </div>
                </div>
            </div>
        </div>
        
        <script>
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            async function sendMessage() {
                const input = document.getElementById('message-input');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Add user message
                addMessage(message, 'user');
                input.value = '';
                
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            messages: [{ role: 'user', content: message }]
                        })
                    });
                    
                    const data = await response.json();
                    addMessage(data.content, 'assistant');
                } catch (error) {
                    addMessage('Error: ' + error.message, 'assistant');
                }
            }
            
            function addMessage(content, role) {
                const container = document.getElementById('chat-container');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role}`;
                messageDiv.innerHTML = `<strong>${role === 'user' ? 'You' : 'Bolt.jl Assistant'}:</strong><br>${content}`;
                container.appendChild(messageDiv);
                container.scrollTop = container.scrollHeight;
            }
        </script>
    </body>
</html>
"""

function start_server(port::Int = 5000)
    router = HTTP.Router()
    
    # Serve main page
    HTTP.register!(router, "GET", "/", (req) -> HTTP.Response(200, html_content))
    
    # Chat API endpoint
    HTTP.register!(router, "POST", "/api/chat", handle_chat)
    
    # Start server
    println("Starting server on port $port...")
    HTTP.serve(router, "0.0.0.0", port)
end

function handle_chat(req::HTTP.Request)
    try
        body = String(req.body)
        data = JSON3.read(body)
        messages = data.messages
        
        # Simple echo response for now
        response = Dict(
            "content" => "Hello! I received your message: $(messages[end].content)",
            "role" => "assistant"
        )
        
        return HTTP.Response(200, ["Content-Type" => "application/json"], JSON3.write(response))
    catch e
        error_response = Dict("error" => string(e))
        return HTTP.Response(500, ["Content-Type" => "application/json"], JSON3.write(error_response))
    end
endSON.stringify({
                            message: message,
                            chat_id: null
                        })
                    });
                    
                    const data = await response.json();
                    addMessage(data.response, 'assistant');
                    
                } catch (error) {
                    addMessage('Sorry, there was an error processing your request.', 'assistant');
                }
            }
            
            function addMessage(content, role) {
                const chatContainer = document.getElementById('chat-container');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role}`;
                
                const roleLabel = role === 'user' ? 'You' : 'Bolt.jl Assistant';
                messageDiv.innerHTML = `<strong>${roleLabel}:</strong><br>${content.replace(/\\n/g, '<br>')}`;
                
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            // Auto-focus input
            document.getElementById('message-input').focus();
        </script>
    </body>
    </html>
    """
end

function handle_chat_api(req::HTTP.Request)::HTTP.Response
    if req.method == "POST"
        try
            body = JSON3.read(String(req.body))
            message = body.message
            chat_id = get(body, :chat_id, nothing)
            
            # Create new chat if needed
            if chat_id === nothing
                chat_id = create_new_chat("Chat with Bolt.jl")
            end
            
            # Add user message
            send_message(message, "user")
            
            # Generate AI response
            messages = [Dict("role" => "user", "content" => message)]
            response = stream_text(messages)
            
            # Add assistant response
            send_message(response.text, "assistant")
            
            return HTTP.Response(200, 
                ["Content-Type" => "application/json"],
                JSON3.write(Dict("response" => response.text, "chat_id" => chat_id))
            )
        catch e
            return HTTP.Response(500, 
                ["Content-Type" => "application/json"],
                JSON3.write(Dict("error" => string(e)))
            )
        end
    else
        return HTTP.Response(405, "Method Not Allowed")
    end
end

function handle_enhancer_api(req::HTTP.Request)::HTTP.Response
    return HTTP.Response(200, 
        ["Content-Type" => "application/json"],
        JSON3.write(Dict("enhanced" => "Feature not implemented yet"))
    )
end

function handle_files_api(req::HTTP.Request)::HTTP.Response
    if req.method == "GET"
        load_file_tree()
        return HTTP.Response(200, 
            ["Content-Type" => "application/json"],
            JSON3.write(Dict("files" => "File tree loaded"))
        )
    else
        return HTTP.Response(405, "Method Not Allowed")
    end
end

function handle_terminal_api(req::HTTP.Request)::HTTP.Response
    if req.method == "POST"
        try
            body = JSON3.read(String(req.body))
            command = body.command
            
            terminal_id = create_terminal()
            execute_command(command, terminal_id)
            
            return HTTP.Response(200, 
                ["Content-Type" => "application/json"],
                JSON3.write(Dict("output" => "Command executed"))
            )
        catch e
            return HTTP.Response(500, 
                ["Content-Type" => "application/json"],
                JSON3.write(Dict("error" => string(e)))
            )
        end
    else
        return HTTP.Response(405, "Method Not Allowed")
    end
end

function handle_editor_api(req::HTTP.Request)::HTTP.Response
    return HTTP.Response(200, 
        ["Content-Type" => "application/json"],
        JSON3.write(Dict("editor" => "Editor API not implemented yet"))
    )
end

end # module Server
