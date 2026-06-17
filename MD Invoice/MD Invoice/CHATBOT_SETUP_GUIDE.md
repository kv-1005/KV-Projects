# 🤖 AI Chatbot Setup Guide

## Overview

Your invoice management system now includes a **personal AI chatbot assistant** that helps users with:
- Creating and managing invoices
- Understanding GST calculations
- Customer management
- Dashboard analytics
- Purchase orders
- General invoice system questions

## ✨ Features

1. **Hybrid Approach**: Rule-based responses for common queries + AI for complex questions
2. **Free Tier Available**: Works with Hugging Face free API (1,000 requests/month)
3. **Context-Aware**: Understands your invoice data
4. **Chat History**: Saves conversations for future reference
5. **Beautiful UI**: Modern, responsive chat widget

## 🚀 Quick Setup

### Step 1: Create Database Tables

Run the migration script to create chatbot tables:

```bash
python create_chatbot_tables.py
```

This will:
- Create `chat_conversation`, `chat_message`, and `chatbot_knowledge` tables
- Initialize the knowledge base with default entries

### Step 2: Enable AI Features (Optional)

The chatbot works **without AI** using rule-based responses. To enable AI features:

1. **Get a free Hugging Face API key:**
   - Visit: https://huggingface.co/settings/tokens
   - Create a free account (if needed)
   - Generate a new token
   - Free tier: 1,000 requests/month

2. **Add to your `.env` file:**
   ```bash
   HUGGINGFACE_API_KEY=your-api-key-here
   HUGGINGFACE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
   ```

3. **Restart your application**

### Step 3: Test the Chatbot

1. Login to your application
2. Look for the **robot icon** in the bottom-right corner
3. Click it to open the chat widget
4. Try asking:
   - "How do I create an invoice?"
   - "What is GST?"
   - "How to add a customer?"

## 📁 Files Created

- `chatbot_service.py` - Core chatbot logic with rule engine and AI integration
- `static/js/chatbot.js` - Frontend JavaScript for chat interactions
- `templates/base.html` - Updated with chat widget UI (embedded)
- `create_chatbot_tables.py` - Database migration script
- `CHATBOT_SETUP_GUIDE.md` - This guide

## 🔧 How It Works

### Architecture

```
User Query
    ↓
Rule Engine (Pattern Matching)
    ↓ (if no match)
AI Service (Hugging Face API)
    ↓
Response + Context
    ↓
Save to Database
```

### Rule Engine

The system first checks user queries against a knowledge base of patterns:
- **Keyword matching**: "create invoice", "GST calculation", etc.
- **Regex patterns**: More flexible pattern matching
- **Instant responses**: No API calls needed

### AI Fallback

If no rule matches:
- Sends query to Hugging Face API
- Includes system context about invoice management
- Returns intelligent response
- Falls back to default response if API fails

## 💡 Customization

### Adding Knowledge Base Entries

Edit `chatbot_service.py` and add entries to `KNOWLEDGE_BASE`:

```python
{
    'keywords': ['your keyword'],
    'pattern': r'regex pattern here',
    'response': 'Your response text here',
    'category': 'category_name'
}
```

### Changing AI Model

Update `HUGGINGFACE_MODEL` in `.env`:
- `mistralai/Mistral-7B-Instruct-v0.2` (default, recommended)
- `meta-llama/Llama-2-7b-chat-hf`
- `google/flan-t5-large`

### Styling the Chat Widget

Edit the CSS in `templates/base.html` (look for `.chatbot-widget` styles).

## 🔐 Security

- **Authentication Required**: Only logged-in users can chat
- **User Isolation**: Each user has their own conversation history
- **Input Sanitization**: User messages are validated
- **Rate Limiting**: Protected by Flask-Limiter (if configured)

## 📊 Database Schema

### Tables Created

**chat_conversations**
- `id` - Primary key
- `user_id` - Foreign key to user table
- `created_at` - Timestamp
- `updated_at` - Last update timestamp

**chat_messages**
- `id` - Primary key
- `conversation_id` - Foreign key to conversation
- `role` - 'user' or 'assistant'
- `message` - Message text
- `created_at` - Timestamp

**chatbot_knowledge**
- `id` - Primary key
- `keyword` - Keyword for matching
- `pattern` - Regex pattern (optional)
- `response` - Response text
- `category` - Category name
- `created_at` - Timestamp

## 🎯 API Endpoints

### POST `/api/chat/send`
Send a message to the chatbot.

**Request:**
```json
{
  "message": "How do I create an invoice?"
}
```

**Response:**
```json
{
  "success": true,
  "response": "To create an invoice...",
  "message_id": 123
}
```

### GET `/api/chat/history`
Get chat conversation history.

**Response:**
```json
{
  "messages": [
    {
      "id": 1,
      "role": "user",
      "message": "Hello",
      "created_at": "2024-01-01 12:00:00"
    }
  ]
}
```

### POST `/api/chat/clear`
Clear chat history.

**Response:**
```json
{
  "success": true
}
```

## 🐛 Troubleshooting

### Chatbot not appearing

1. Check browser console for JavaScript errors
2. Ensure you're logged in
3. Check that `static/js/chatbot.js` exists
4. Clear browser cache

### AI responses not working

1. Check `HUGGINGFACE_API_KEY` in `.env`
2. Verify API key is valid at https://huggingface.co/settings/tokens
3. Check API rate limits (free tier: 1,000/month)
4. Check application logs for API errors

### Database errors

1. Run `python create_chatbot_tables.py`
2. Check database connection
3. Ensure tables were created: `SELECT * FROM chat_conversation LIMIT 1;`

## 📝 Notes

- **Free Usage**: Rule-based responses work without any API keys
- **No Internet Required**: Rule engine works offline
- **Privacy**: Conversations are stored locally in your database
- **Cost**: Free tier (1K requests/month) is usually enough for personal use

## 🎉 You're All Set!

The chatbot is now ready to use. Users will see the robot icon in the bottom-right corner on all pages.

**Enjoy your AI assistant!** 🚀

