import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid
import json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# ----- Core Models and Business Logic -----

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator('content')
    def clean_content(cls, v):
        v = v.strip()
        prefixes_to_remove = [
            "MessageRole.ASSISTANT:",
            "MessageRole.ASSISTANT",
            "Assistant:",
            "assistant:",
            "ASSISTANT:",
            "user:",
            "USER:",
            "system:",
            "SYSTEM:"
        ]
        for prefix in prefixes_to_remove:
            if v.startswith(prefix):
                v = v[len(prefix):].strip()
                break
        return v

class Character(BaseModel):
    id: str
    name: str
    description: str
    personality: str
    system_prompt: str
    avatar_url: str = "default_avatar.png"
    category: str = "general"
    tags: List[str] = []
    
    class Config:
        arbitrary_types_allowed = True

class ConversationState(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    last_activity: datetime = Field(default_factory=datetime.now)
    character_id: str
    user_id: str
    active: bool = True

    class Config:
        arbitrary_types_allowed = True

class UserInput(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    character_id: Optional[str] = None
    user_id: str

    @field_validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()

class UserProfile(BaseModel):
    id: str
    username: str
    password_hash: str
    name: str = ""
    email: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: datetime = Field(default_factory=datetime.now)
    favorites: List[str] = []

# ----- Constants -----
INACTIVITY_TIMEOUT = 1800  # 30 minutes
MAX_TOKENS = 2048
TEMPERATURE = 0.7
DATA_DIR = "data"
CHARACTERS_FILE = os.path.join(DATA_DIR, "characters.json")
CONVERSATIONS_DIR = os.path.join(DATA_DIR, "conversations")

# ----- Conversation Platform Configuration and Logic -----

class ConversationPlatformConfig:
    def __init__(self):
        load_dotenv()
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.exit_phrases = {"thank you", "thanks", "bye", "goodbye", "exit", "stop"}
        self.setup_directory_structure()
        self.setup_logging()
        
    def setup_directory_structure(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(CONVERSATIONS_DIR, exist_ok=True)
        if not os.path.exists(CHARACTERS_FILE):
            default_characters = [
                {
                    "id": "coach",
                    "name": "Interview Coach",
                    "description": "An expert interview coach helping you prepare for job interviews.",
                    "personality": "Professional, supportive, and insightful.",
                    "system_prompt": ("You are an expert interview coach helping prepare candidates for "
                                      "interviews. Provide helpful advice, use the STAR framework, and be supportive but honest."),
                    "avatar_url": "coach.png",
                    "category": "professional",
                    "tags": ["interview", "career", "advice"]
                },
                {
                    "id": "philosopher",
                    "name": "Socrates",
                    "description": "The ancient Greek philosopher known for his Socratic method of questioning.",
                    "personality": "Curious, thoughtful, and always questioning assumptions.",
                    "system_prompt": ("You are Socrates, the ancient Greek philosopher. Engage in thoughtful dialogue using the Socratic method. "
                                      "Ask questions that help the user examine their assumptions and beliefs. Speak as Socrates would, with wisdom and curiosity."),
                    "avatar_url": "socrates.png",
                    "category": "philosophy",
                    "tags": ["philosophy", "wisdom", "questions"]
                },
                {
                    "id": "storyteller",
                    "name": "The Storyteller",
                    "description": "A creative storyteller who can weave tales of any genre on demand.",
                    "personality": "Creative, expressive, and imaginative.",
                    "system_prompt": ("You are a master storyteller capable of creating engaging stories across various genres. "
                                      "Respond to the user's prompts by crafting imaginative tales, helping develop story ideas, or discussing narrative techniques. "
                                      "Be creative and engaging in your responses."),
                    "avatar_url": "storyteller.png",
                    "category": "entertainment",
                    "tags": ["stories", "creativity", "fiction"]
                }
            ]
            with open(CHARACTERS_FILE, 'w') as f:
                json.dump(default_characters, f, indent=2)
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(), logging.FileHandler('conversation_platform.log')]
        )
        return logging.getLogger(__name__)

class ConversationPlatform:
    def __init__(self):
        self.config = ConversationPlatformConfig()
        self.logger = self.config.setup_logging()
        from groq import Groq
        from langchain_groq import ChatGroq
        self.groq_client = Groq(api_key=self.config.groq_api_key)
        self.llm = ChatGroq(groq_api_key=self.config.groq_api_key, model_name="Llama3-8b-8192")
        
        self.characters: Dict[str, Character] = self.load_characters()
        self.conversation_storage: Dict[str, ConversationState] = {}
        self.user_storage: Dict[str, UserProfile] = {}
        self.load_conversations()
        # Cleanup task will be scheduled by FastAPI on startup

    def load_characters(self) -> Dict[str, Character]:
        try:
            with open(CHARACTERS_FILE, 'r') as f:
                character_data = json.load(f)
            characters = {char_dict["id"]: Character(**char_dict) for char_dict in character_data}
            self.logger.info(f"Loaded {len(characters)} characters")
            return characters
        except Exception as e:
            self.logger.error(f"Error loading characters: {str(e)}")
            return {
                "coach": Character(
                    id="coach",
                    name="Interview Coach",
                    description="An expert interview coach helping you prepare for job interviews.",
                    personality="Professional, supportive, and insightful.",
                    system_prompt=("You are an expert interview coach helping prepare candidates for interviews. Provide helpful advice, "
                                   "use the STAR framework, and be supportive but honest."),
                    avatar_url="coach.png",
                    category="professional",
                    tags=["interview", "career", "advice"]
                )
            }

    def save_characters(self):
        try:
            character_data = [char.model_dump() for char in self.characters.values()]
            with open(CHARACTERS_FILE, 'w') as f:
                json.dump(character_data, f, indent=2)
            self.logger.info(f"Saved {len(character_data)} characters")
        except Exception as e:
            self.logger.error(f"Error saving characters: {str(e)}")

    def generate_character(self, topic: str, personality_traits: List[str]) -> Character:
        try:
            prompt = f"""
            Create a detailed AI character based on the following specifications:
            
            Topic or theme: {topic}
            Personality traits: {', '.join(personality_traits)}
            
            Please provide:
            1. A unique name for this character
            2. A short description
            3. A detailed personality description
            4. A system prompt that would guide an AI to accurately represent this character
            5. A category for this character
            6. A list of relevant tags
            
            Format your response as a JSON object with these fields.
            """
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="Llama3-8b-8192",
                temperature=0.7,
                max_tokens=1024
            )
            response_text = response.choices[0].message.content
            import re
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                character_json = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', response_text, re.DOTALL)
                character_json = json_match.group(1) if json_match else response_text
            character_data = json.loads(character_json)
            required_fields = {"name", "description", "personality", "system_prompt"}
            if not all(field in character_data for field in required_fields):
                raise ValueError("Generated character missing required fields")
            char_id = f"gen_{uuid.uuid4().hex[:8]}"
            new_character = Character(
                id=char_id,
                name=character_data.get("name"),
                description=character_data.get("description"),
                personality=character_data.get("personality"),
                system_prompt=character_data.get("system_prompt"),
                avatar_url="generated_avatar.png",
                category=character_data.get("category", "generated"),
                tags=character_data.get("tags", [topic] + personality_traits)
            )
            self.characters[char_id] = new_character
            self.save_characters()
            return new_character
        except Exception as e:
            self.logger.error(f"Error generating character: {str(e)}")
            raise Exception("Failed to generate character")

    def load_conversations(self):
        try:
            conversation_files = Path(CONVERSATIONS_DIR).glob("*.json")
            loaded_count = 0
            for file_path in conversation_files:
                try:
                    with open(file_path, 'r') as f:
                        conversation_data = json.load(f)
                    for msg in conversation_data.get("messages", []):
                        if "timestamp" in msg:
                            msg["timestamp"] = datetime.fromisoformat(msg["timestamp"])
                    if "last_activity" in conversation_data:
                        conversation_data["last_activity"] = datetime.fromisoformat(conversation_data["last_activity"])
                    conv_id = file_path.stem
                    conversation = ConversationState(**conversation_data)
                    self.conversation_storage[conv_id] = conversation
                    loaded_count += 1
                except Exception as e:
                    self.logger.error(f"Error loading conversation {file_path}: {str(e)}")
            self.logger.info(f"Loaded {loaded_count} conversations")
        except Exception as e:
            self.logger.error(f"Error loading conversations: {str(e)}")

    def save_conversation(self, conversation_id: str):
        if conversation_id not in self.conversation_storage:
            return
        try:
            conversation = self.conversation_storage[conversation_id]
            conv_dict = conversation.model_dump()
            for msg in conv_dict["messages"]:
                msg["timestamp"] = msg["timestamp"].isoformat()
            conv_dict["last_activity"] = conv_dict["last_activity"].isoformat()
            file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
            with open(file_path, 'w') as f:
                json.dump(conv_dict, f, indent=2)
            self.logger.info(f"Saved conversation {conversation_id}")
        except Exception as e:
            self.logger.error(f"Error saving conversation {conversation_id}: {str(e)}")

    def clean_response(self, response: str) -> str:
        response = response.strip()
        prefixes_to_remove = [
            "MessageRole.ASSISTANT:",
            "MessageRole.ASSISTANT",
            "Assistant:",
            "assistant:",
            "ASSISTANT:",
            "Response:",
            "Answer:"
        ]
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
                break
        return response

    async def generate_response(self, message: str, conversation_id: Optional[str], character_id: str, user_id: str) -> Dict[str, str]:
        try:
            if conversation_id not in self.conversation_storage:
                if character_id not in self.characters:
                    raise Exception(f"Character with ID {character_id} not found")
                conversation_id = str(uuid.uuid4())
                self.conversation_storage[conversation_id] = ConversationState(
                    character_id=character_id,
                    user_id=user_id
                )
                character = self.characters[character_id]
                self.add_message_to_conversation(conversation_id, MessageRole.SYSTEM, character.system_prompt)
            conversation = self.conversation_storage[conversation_id]
            character = self.characters[conversation.character_id]
            is_first_message = len([m for m in conversation.messages if m.role == MessageRole.USER]) == 0
            system_prompt = character.system_prompt
            if is_first_message:
                intro_context = f"""
                You are {character.name}. {character.description}
                Personality: {character.personality}
                
                This is the first message from the user. Introduce yourself briefly and then respond to their message.
                """
                system_prompt = f"{system_prompt}\n\n{intro_context}"
            messages = [{"role": "system", "content": system_prompt}]
            for msg in conversation.messages:
                if msg.role != MessageRole.SYSTEM:
                    messages.append({"role": msg.role.value, "content": msg.content})
            messages.append({"role": "user", "content": message})
            chat_completion = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                messages=messages,
                model="Llama3-8b-8192",
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )
            response = chat_completion.choices[0].message.content
            cleaned_response = self.clean_response(response)
            self.add_message_to_conversation(conversation_id, MessageRole.USER, message)
            self.add_message_to_conversation(conversation_id, MessageRole.ASSISTANT, cleaned_response)
            self.save_conversation(conversation_id)
            return {"conversation_id": conversation_id, "response": cleaned_response}
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise Exception("Failed to generate response")

    def get_conversation_context(self, conversation_id: str, context_window: int = 10) -> str:
        if conversation_id not in self.conversation_storage:
            return ""
        conversation = self.conversation_storage[conversation_id]
        recent_messages = conversation.messages[-context_window:]
        return "\n".join([f"{msg.role}: {msg.content}" for msg in recent_messages])

    def add_message_to_conversation(self, conversation_id: str, role: MessageRole, content: str):
        if conversation_id not in self.conversation_storage:
            raise Exception(f"Conversation {conversation_id} not found")
        conversation = self.conversation_storage[conversation_id]
        cleaned_content = Message(role=role, content=content).content
        conversation.messages.append(Message(role=role, content=cleaned_content))
        conversation.last_activity = datetime.now()

    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        user_conversations = []
        for conv_id, conv in self.conversation_storage.items():
            if conv.user_id == user_id:
                character = self.characters.get(conv.character_id)
                last_message = ""
                if conv.messages:
                    non_system_messages = [m for m in conv.messages if m.role != MessageRole.SYSTEM]
                    if non_system_messages:
                        last_message = non_system_messages[-1].content
                user_conversations.append({
                    "id": conv_id,
                    "character_name": character.name if character else "Unknown Character",
                    "character_id": conv.character_id,
                    "last_activity": conv.last_activity,
                    "message_count": len([m for m in conv.messages if m.role != MessageRole.SYSTEM]),
                    "preview": last_message[:100] + "..." if len(last_message) > 100 else last_message
                })
        user_conversations.sort(key=lambda x: x["last_activity"], reverse=True)
        return user_conversations

    async def cleanup_task(self):
        while True:
            try:
                self.clean_inactive_conversations()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {str(e)}")
                await asyncio.sleep(60)  # If there's an error, retry after 1 minute

    def clean_inactive_conversations(self):
        current_time = datetime.now()
        for conversation_id, conversation in list(self.conversation_storage.items()):
            if (current_time - conversation.last_activity) > timedelta(seconds=INACTIVITY_TIMEOUT):
                conversation.active = False
                self.logger.info(f"Conversation {conversation_id} marked as inactive due to timeout")

    def create_user(self, username: str, password: str) -> UserProfile:
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user_id = str(uuid.uuid4())
        user = UserProfile(id=user_id, username=username, password_hash=password_hash)
        self.user_storage[user_id] = user
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[UserProfile]:
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        for user in self.user_storage.values():
            if user.username == username and user.password_hash == password_hash:
                user.last_login = datetime.now()
                return user
        return None

# ----- Test Execution Block -----
if __name__ == '__main__':
    import asyncio

    async def test_platform():
        # Initialize the conversation platform
        platform = ConversationPlatform()
        # Print loaded characters
        print("Loaded Characters:")
        for char_id, character in platform.characters.items():
            print(f"ID: {char_id}, Name: {character.name}")
        
        # Pick the first character for testing
        test_character_id = list(platform.characters.keys())[0]
        test_user_id = "test_user"
        test_message = "Hello, how are you?"
        
        # Generate a test response
        print("\nSending test message to generate response...")
        result = await platform.generate_response(test_message, None, test_character_id, test_user_id)
        print("Test Conversation Response:")
        print(result)

    asyncio.run(test_platform())