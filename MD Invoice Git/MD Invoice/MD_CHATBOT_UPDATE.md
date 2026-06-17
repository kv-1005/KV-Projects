# MD Chatbot - Updated Configuration

## Changes Made

### 1. Chatbot Renamed to "MD"
- The chatbot is now named **"MD"** instead of "AI Assistant"
- Updated in chat header and welcome messages
- Branded for your MD Invoice system

### 2. Enhanced to Answer All Questions
- MD can now answer **any type of question**, not just invoice-related
- Updated AI prompt to handle:
  - Invoice system questions
  - General business questions
  - Technology and programming
  - General knowledge
  - Any topic the user asks about

### 3. Database Table Names Fixed
- Added explicit `__tablename__` to all chatbot models
- Tables created: `chat_conversations`, `chat_messages`, `chatbot_knowledge`
- Migration script updated and tested successfully

## Current Status

✅ **Database Tables**: Created successfully
✅ **Chatbot Name**: Changed to "MD"
✅ **General Q&A**: Enabled for all types of questions
✅ **UI Updated**: Welcome message reflects new capabilities

## How MD Works

1. **Rule-Based Responses** (Instant, no API needed)
   - Common invoice system questions
   - Pattern matching for quick answers

2. **AI Fallback** (If Hugging Face API key is set)
   - Handles any type of question
   - General knowledge, business, tech, etc.
   - Friendly and helpful responses

3. **Default Response** (If no match and no API)
   - Helpful message indicating MD can answer anything
   - Suggests topics to ask about

## To Enable Full AI Capabilities

1. Get a free Hugging Face API key:
   - Visit: https://huggingface.co/settings/tokens
   - Create account (free)
   - Generate new token

2. Add to `.env` file:
   ```
   HUGGINGFACE_API_KEY=your-api-key-here
   HUGGINGFACE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
   ```

3. Restart your application

**Note**: MD works without an API key using rule-based responses, but with an API key, it can answer any question!

## Testing

Try asking MD:
- "How do I create an invoice?" (rule-based)
- "What is Python?" (requires AI)
- "Tell me about business strategies" (requires AI)
- "What is the weather?" (requires AI)

## Files Modified

- `app.py` - Added explicit table names to models
- `chatbot_service.py` - Updated system prompt for general Q&A
- `templates/base.html` - Changed name to "MD"
- `static/js/chatbot.js` - Updated welcome messages
- `create_chatbot_tables.py` - Fixed table name checks

## Ready to Use!

MD is now ready to answer all types of questions. The chatbot widget appears in the bottom-right corner of all pages.

