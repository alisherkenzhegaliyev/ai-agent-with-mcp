def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Product Management Agent</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            h1 {
                color: #333;
                text-align: center;
            }
            #chat-container {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                height: 500px;
                overflow-y: auto;
                margin-bottom: 20px;
            }
            .message {
                margin: 10px 0;
                padding: 10px;
                border-radius: 5px;
            }
            .user-message {
                background-color: #007bff;
                color: white;
                text-align: right;
            }
            .agent-message {
                background-color: #e9ecef;
                color: #333;
            }
            .tool-calls {
                font-size: 0.8em;
                color: #666;
                font-style: italic;
                margin-top: 5px;
            }
            #input-container {
                display: flex;
                gap: 10px;
            }
            #query-input {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
            }
            #send-button {
                padding: 10px 30px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            #send-button:hover {
                background-color: #0056b3;
            }
            #send-button:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            .loading {
                text-align: center;
                color: #666;
                font-style: italic;
            }
        </style>
    </head>
    <body>
        <h1>Product Management Agent</h1>
        <div id="chat-container"></div>
        <div id="input-container">
            <input type="text" id="query-input" placeholder="Ask about products..." />
            <button id="send-button">Send</button>
        </div>

        <script>
            const chatContainer = document.getElementById('chat-container');
            const queryInput = document.getElementById('query-input');
            const sendButton = document.getElementById('send-button');

            function addMessage(text, isUser, toolCalls = []) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'agent-message'}`;
                messageDiv.innerHTML = text.replace(/\\n/g, '<br>');
                
                if (toolCalls.length > 0) {
                    const toolDiv = document.createElement('div');
                    toolDiv.className = 'tool-calls';
                    toolDiv.textContent = `🔧 Used tools: ${toolCalls.join(', ')}`;
                    messageDiv.appendChild(toolDiv);
                }
                
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            async function sendQuery() {
                const query = queryInput.value.trim();
                if (!query) return;

                // Disable input while processing
                queryInput.disabled = true;
                sendButton.disabled = true;

                // Add user message
                addMessage(query, true);
                queryInput.value = '';

                // Show loading
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'loading';
                loadingDiv.textContent = 'Agent is thinking...';
                chatContainer.appendChild(loadingDiv);

                try {
                    const response = await fetch('/api/v1/agent/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query: query })
                    });

                    const data = await response.json();
                    
                    // Remove loading
                    chatContainer.removeChild(loadingDiv);
                    
                    // Add agent response
                    addMessage(data.response, false, data.tool_calls);
                } catch (error) {
                    chatContainer.removeChild(loadingDiv);
                    addMessage('Error: Could not connect to agent', false);
                }

                // Re-enable input
                queryInput.disabled = false;
                sendButton.disabled = false;
                queryInput.focus();
            }

            sendButton.addEventListener('click', sendQuery);
            queryInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendQuery();
            });

            // Welcome message
            addMessage('Hello! I can help you manage products. Try asking:\\n• "show all products"\\n• "make a 15% discount on Mouse"\\n• "what\\'s the average price?"\\n• "add product: Mouse, price 1500, category Electronics"', false);
        </script>
    </body>
    </html>
    """
