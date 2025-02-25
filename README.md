# AI Character Conversation Platform

A modern, interactive web application that allows users to chat with AI-powered characters. Built with FastAPI, WebSockets, and Groq's LLM API.

## 📋 Overview

This platform enables users to:
- Chat with pre-defined AI characters
- Create custom AI characters based on topics and traits
- Save and continue conversations
- Interact via WebSocket for real-time messaging

## 🚀 Features

- **Multiple AI Characters**: Chat with various pre-defined characters including an Interview Coach, Socrates, and a Storyteller
- **Custom Character Creation**: Generate unique AI characters based on user-defined topics and personality traits
- **Conversation Management**: Save, retrieve, and continue conversations
- **Real-time Chat**: WebSocket implementation for responsive messaging
- **User Authentication**: Simple user creation and authentication system
- **Responsive Design**: Web interface adaptable to different devices

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3
- **AI Integration**: Groq API with Llama3-8b-8192 model
- **Frontend**: HTML, Jinja2 Templates
- **Real-time Communication**: WebSockets
- **Data Storage**: JSON-based file storage

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-character-platform.git
   cd ai-character-platform
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn jinja2 python-dotenv langchain-groq groq
   ```

4. **Create environment variables**
   Create a `.env` file in the root directory with your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Create necessary directories**
   ```bash
   mkdir -p static templates data/conversations
   ```

6. **Create template files**
   Copy the HTML templates from the repository into the `templates` folder.

## 🏃‍♀️ Running the Application

1. **Start the server**
   ```bash
   python app.py
   ```
   Or alternatively:
   ```bash
   uvicorn app:app --reload
   ```

2. **Access the application**
   Open your browser and navigate to `http://localhost:8000`

## 📁 Project Structure

```
.
├── app.py                  # FastAPI application
├── main.py                 # Business logic and models
├── .env                    # Environment variables
├── data/
│   ├── characters.json     # Character definitions
│   └── conversations/      # Stored conversations
├── static/                 # Static files (CSS, JS, images)
└── templates/              # HTML templates
    ├── index.html          # Home page
    ├── login.html          # Login page
    ├── characters.html     # Character selection
    ├── chat.html           # Chat interface
    ├── conversations.html  # Conversation history
    └── create_character.html # Character creation
```

## 🔌 API Endpoints

### HTML Endpoints
- `GET /`: Home page
- `GET /login`: Login page
- `GET /characters`: Character selection
- `GET /chat/{character_id}`: Chat with a specific character
- `GET /conversations`: View conversation history
- `GET /create-character`: Create a new character

### API Endpoints
- `POST /login`: Authenticate user
- `POST /api/create-character`: Create a new AI character
- `POST /api/send-message`: Send a message to an AI character

### WebSocket Endpoint
- `WebSocket /ws/chat/{user_id}/{character_id}/{conversation_id}`: Real-time chat connection

## 🌟 Using the Platform

### Login/Registration
- Navigate to `/login`
- Enter a username and password
- The system will create a new user if the username doesn't exist

### Chatting with Characters
1. Select a character from the characters page
2. Send messages in the chat interface
3. Your conversation will be saved automatically

### Creating Custom Characters
1. Navigate to the create character page
2. Enter a topic and personality traits
3. Submit the form to generate a new character
4. You'll be automatically redirected to chat with your new character

### Viewing Past Conversations
- Visit the conversations page to see all your previous chats
- Select any conversation to continue where you left off

## 🧩 Extending the Platform

### Adding New Characters
Modify the `characters.json` file in the data directory to add new pre-defined characters:

```json
{
  "id": "unique_id",
  "name": "Character Name",
  "description": "Brief description",
  "personality": "Personality traits",
  "system_prompt": "System prompt for the AI",
  "avatar_url": "avatar_image.png",
  "category": "category",
  "tags": ["tag1", "tag2"]
}
```

### Customizing the UI
Edit the HTML templates in the `templates` directory to customize the user interface.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Groq](https://groq.com/)
- [Llama 3](https://ai.meta.com/llama/)