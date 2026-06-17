/**
 * Enhanced AI Chatbot JavaScript Handler
 * Advanced features: caching, debouncing, quick replies, timestamps, copy functionality
 */

let chatHistoryLoaded = false;
let isProcessing = false;
let debounceTimer = null;
let messageQueue = [];
const QUICK_REPLIES = [
    "How do I create an invoice?",
    "What is GST?",
    "How to add a customer?",
    "Explain the dashboard"
];

// Initialize chatbot on page load
document.addEventListener('DOMContentLoaded', function() {
    loadChatHistory();
    setupKeyboardShortcuts();
    setupQuickReplies();
    setupAutoResize();
});

function toggleChatbot() {
    const container = document.getElementById('chatbot-container');
    const isVisible = container.style.display !== 'none';
    
    if (!isVisible) {
        container.style.display = 'flex';
        if (!chatHistoryLoaded) {
            loadChatHistory();
        }
        // Focus input
        setTimeout(() => {
            const input = document.getElementById('chatbot-input');
            input.focus();
        }, 100);
    } else {
        container.style.display = 'none';
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    } else if (event.key === 'Escape') {
        toggleChatbot();
    }
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to open/close chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            toggleChatbot();
        }
    });
}

function setupQuickReplies() {
    // Add quick reply buttons to welcome message (avoid duplicates)
    const welcome = document.querySelector('.chatbot-welcome');
    if (welcome && !document.querySelector('.quick-replies')) {
        const quickRepliesDiv = document.createElement('div');
        quickRepliesDiv.className = 'quick-replies';
        
        QUICK_REPLIES.forEach(reply => {
            const btn = document.createElement('button');
            btn.className = 'quick-reply-btn';
            btn.textContent = reply;
            btn.onclick = () => {
                const input = document.getElementById('chatbot-input');
                input.value = reply;
                input.style.height = 'auto';
                input.style.height = Math.min(input.scrollHeight, 120) + 'px';
                sendChatMessage();
            };
            quickRepliesDiv.appendChild(btn);
        });
        
        welcome.appendChild(quickRepliesDiv);
    }
}

// Enhanced auto-resize with better handling
function setupAutoResize() {
    const input = document.getElementById('chatbot-input');
    if (input) {
        input.addEventListener('input', function() {
            this.style.height = 'auto';
            const newHeight = Math.min(this.scrollHeight, 120); // Max 120px
            this.style.height = newHeight + 'px';
        });
        
        // Handle paste
        input.addEventListener('paste', function() {
            setTimeout(() => {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            }, 10);
        });
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    
    if (!message || isProcessing) {
        return;
    }
    
    // Debounce to prevent rapid-fire requests
    if (debounceTimer) {
        clearTimeout(debounceTimer);
    }
    
    debounceTimer = setTimeout(async () => {
        isProcessing = true;
        
        // Clear input but save value
        input.value = '';
        input.style.height = 'auto';
        input.disabled = true;
        
        // Remove welcome message if present
        const welcome = document.querySelector('.chatbot-welcome');
        if (welcome) {
            welcome.remove();
        }
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Show loading indicator
        const loadingId = showLoading();
        
        try {
            // Get CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
            
            // Send message to backend
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            // Remove loading indicator
            removeLoading(loadingId);
            
        if (data.success) {
            // Add assistant response
            addMessageToChat('assistant', data.response);
        } else {
            // Show error or fallback response
            const errorMessage = data.response || 
                ('Sorry, I encountered an error. Please try again. ' + (data.error || ''));
            addMessageToChat('assistant', errorMessage);
        }
            
        } catch (error) {
            console.error('Chat error:', error);
            removeLoading(loadingId);
            addMessageToChat('assistant', 
                'Sorry, I couldn\'t process your request. Please check your connection and try again.');
        } finally {
            isProcessing = false;
            input.disabled = false;
            input.focus();
            debounceTimer = null;
        }
    }, 300); // 300ms debounce
}

function addMessageToChat(role, message, timestamp = null) {
    const messagesContainer = document.getElementById('chatbot-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chatbot-message ${role}`;
    messageDiv.setAttribute('data-role', role);
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'chatbot-message-content';
    
    // Format message with enhanced markdown
    const formattedMessage = formatMessage(message);
    contentDiv.innerHTML = formattedMessage;
    
    // Add timestamp
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-timestamp';
    timeDiv.textContent = timestamp || formatTime(new Date());
    timeDiv.style.cssText = 'font-size: 10px; color: #999; margin-top: 4px; opacity: 0.7;';
    
    // Add copy button for assistant messages
    if (role === 'assistant') {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-copy-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.title = 'Copy message';
        copyBtn.style.cssText = 'position: absolute; top: 5px; right: 5px; background: transparent; border: none; color: #667eea; cursor: pointer; opacity: 0.5; padding: 4px; font-size: 10px; transition: opacity 0.2s;';
        copyBtn.onmouseover = () => copyBtn.style.opacity = '1';
        copyBtn.onmouseout = () => copyBtn.style.opacity = '0.5';
        copyBtn.onclick = () => copyMessage(message, copyBtn);
        
        contentDiv.style.position = 'relative';
        contentDiv.appendChild(copyBtn);
    }
    
    const messageWrapper = document.createElement('div');
    messageWrapper.appendChild(contentDiv);
    messageWrapper.appendChild(timeDiv);
    messageDiv.appendChild(messageWrapper);
    
    messagesContainer.appendChild(messageDiv);
    
    // Smooth scroll to bottom
    setTimeout(() => {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

function formatTime(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

function copyMessage(message, button) {
    navigator.clipboard.writeText(message).then(() => {
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.style.color = '#28a745';
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.style.color = '#667eea';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

function formatMessage(message) {
    // Enhanced markdown formatting
    let formatted = message
        // Code blocks (```code```)
        .replace(/```([\s\S]*?)```/g, '<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; margin: 8px 0;"><code>$1</code></pre>')
        // Inline code (`code`)
        .replace(/`([^`]+)`/g, '<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 0.9em;">$1</code>')
        // Bold text (**text**)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic text (*text*)
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Links [text](url)
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color: #667eea; text-decoration: underline;">$1</a>')
        // Line breaks
        .replace(/\n/g, '<br>')
        // Bullet points
        .replace(/^[-•]\s+(.+)$/gm, '<br>• $1')
        // Numbered lists
        .replace(/^(\d+)\.\s+(.+)$/gm, '<br>$1. $2')
        // Headers
        .replace(/^###\s+(.+)$/gm, '<h3 style="margin: 10px 0 5px 0; font-size: 1.1em; font-weight: 600;">$1</h3>')
        .replace(/^##\s+(.+)$/gm, '<h2 style="margin: 12px 0 6px 0; font-size: 1.2em; font-weight: 600;">$1</h2>')
        .replace(/^#\s+(.+)$/gm, '<h1 style="margin: 14px 0 8px 0; font-size: 1.3em; font-weight: 600;">$1</h1>');
    
    return formatted;
}

function showLoading() {
    const messagesContainer = document.getElementById('chatbot-messages');
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chatbot-message assistant';
    loadingDiv.id = 'chatbot-loading';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'chatbot-loading';
    contentDiv.innerHTML = '<span></span><span></span><span></span>';
    
    loadingDiv.appendChild(contentDiv);
    messagesContainer.appendChild(loadingDiv);
    
    // Smooth scroll
    setTimeout(() => {
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
    
    return 'chatbot-loading';
}

function removeLoading(loadingId) {
    const loading = document.getElementById(loadingId);
    if (loading) {
        loading.style.opacity = '0';
        loading.style.transition = 'opacity 0.3s';
        setTimeout(() => loading.remove(), 300);
    }
}

async function loadChatHistory() {
    if (chatHistoryLoaded) {
        return;
    }
    
    try {
        const response = await fetch('/api/chat/history');
        const data = await response.json();
        
        if (data.messages && data.messages.length > 0) {
            const messagesContainer = document.getElementById('chatbot-messages');
            const welcome = document.querySelector('.chatbot-welcome');
            if (welcome) {
                welcome.remove();
            }
            
            data.messages.forEach(msg => {
                const timestamp = msg.created_at ? new Date(msg.created_at) : new Date();
                addMessageToChat(msg.role, msg.message, formatTime(timestamp));
            });
        }
        
        chatHistoryLoaded = true;
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

async function clearChat() {
    if (!confirm('Are you sure you want to clear the chat history?')) {
        return;
    }
    
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
        
        const response = await fetch('/api/chat/clear', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        
        if (response.ok) {
            // Clear messages container
            const messagesContainer = document.getElementById('chatbot-messages');
            messagesContainer.innerHTML = `
                <div class="chatbot-welcome">
                    <div class="welcome-icon">
                        <i class="fas fa-sparkles"></i>
                    </div>
                    <h5>Welcome to Marvel!</h5>
                    <p>I'm your AI-powered assistant. I can help with invoices, business questions, technical topics, or anything else you need!</p>
                    <div class="welcome-features">
                        <div class="feature-item">
                            <i class="fas fa-bolt"></i>
                            <span>Fast & Smart</span>
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-shield-alt"></i>
                            <span>Secure</span>
                        </div>
                        <div class="feature-item">
                            <i class="fas fa-brain"></i>
                            <span>Knowledgeable</span>
                        </div>
                    </div>
                </div>
            `;
            
            chatHistoryLoaded = false;
            setupQuickReplies(); // Re-add quick replies
        }
    } catch (error) {
        console.error('Error clearing chat:', error);
        alert('Failed to clear chat. Please try again.');
    }
}

// New advanced features
function searchChatMessages() {
    const searchTerm = prompt('Search in chat messages:');
    if (!searchTerm) return;
    
    const messages = document.querySelectorAll('.chatbot-message');
    let found = false;
    
    messages.forEach(msg => {
        const content = msg.textContent.toLowerCase();
        if (content.includes(searchTerm.toLowerCase())) {
            msg.style.backgroundColor = 'rgba(102, 126, 234, 0.1)';
            msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
            found = true;
            
            // Remove highlight after 3 seconds
            setTimeout(() => {
                msg.style.backgroundColor = '';
            }, 3000);
        }
    });
    
    if (!found) {
        alert('No messages found matching: ' + searchTerm);
    }
}

function exportChat() {
    try {
        const messages = document.querySelectorAll('.chatbot-message');
        let chatText = 'Marvel Chat Export\n';
        chatText += '='.repeat(50) + '\n\n';
        
        messages.forEach(msg => {
            const role = msg.classList.contains('user') ? 'User' : 'Marvel';
            const content = msg.querySelector('.chatbot-message-content')?.textContent || '';
            const timestamp = msg.querySelector('.message-timestamp')?.textContent || '';
            
            chatText += `[${timestamp}] ${role}:\n${content}\n\n`;
        });
        
        // Create download
        const blob = new Blob([chatText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `marvel-chat-export-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // Show success feedback
        const sendBtn = document.getElementById('chatbot-send-btn');
        const originalHTML = sendBtn.innerHTML;
        sendBtn.innerHTML = '<i class="fas fa-check"></i>';
        sendBtn.style.background = 'var(--chatbot-success)';
        setTimeout(() => {
            sendBtn.innerHTML = originalHTML;
            sendBtn.style.background = '';
        }, 2000);
    } catch (error) {
        console.error('Export error:', error);
        alert('Failed to export chat.');
    }
}

function showAttachMenu() {
    // Placeholder for future attachment feature
    alert('Attachment feature coming soon!');
}

// Enhanced scroll behavior
function setupSmoothScroll() {
    const messagesContainer = document.getElementById('chatbot-messages');
    if (messagesContainer) {
        // Show scroll indicator when not at bottom
        let scrollTimeout;
        messagesContainer.addEventListener('scroll', function() {
            clearTimeout(scrollTimeout);
            const isNearBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < 100;
            
            // Remove existing indicator
            const existing = document.querySelector('.scroll-indicator');
            if (existing) existing.remove();
            
            if (!isNearBottom) {
                const indicator = document.createElement('div');
                indicator.className = 'scroll-indicator';
                indicator.innerHTML = '<i class="fas fa-chevron-down"></i> New messages';
                indicator.onclick = () => {
                    messagesContainer.scrollTo({
                        top: messagesContainer.scrollHeight,
                        behavior: 'smooth'
                    });
                };
                messagesContainer.appendChild(indicator);
            }
        });
    }
}

// Initialize enhanced features on load
document.addEventListener('DOMContentLoaded', function() {
    setupSmoothScroll();
});
