import json
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.core.config import Settings
from backend.model.schemas import MessageRole
from backend.service.llm_service import LLMService
from backend.service.character_service import CharacterService
from backend.service.conversation_service import ConversationService


def test_llm_service_stub_chat_echoes_last_user():
    settings = Settings(GROQ_API_KEY=None)
    llm = LLMService(settings)
    out = llm.chat([
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "Ack"},
        {"role": "user", "content": "Second"},
    ])
    assert "[stub] You said: Second" in out


def test_character_service_load_defaults_and_generate_character_fallback():
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        # characters.json doesn't exist; defaults should be written and loaded
        cs = CharacterService(data_dir, llm=LLMService(Settings(GROQ_API_KEY=None)))
        assert "coach" in cs.characters
        # Force generate character; in stub mode returns plain text, triggers fallback JSON parsing
        char = cs.generate_character("space", ["curious", "brave"])
        assert char.id.startswith("gen_")
        assert char.category in ("generated", "generated")
        assert char.id in cs.characters
        # Verify characters persisted
        content = json.loads((data_dir / "characters.json").read_text())
        assert isinstance(content, list) and len(content) >= 2


def test_conversation_service_flow_load_save_clean_and_list():
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        conv = ConversationService(data_dir, inactivity_timeout_seconds=0)  # immediate timeout
        # Start new conversation via ensure
        cid = conv.ensure_conversation(None, user_id="u1", character_id="coach")
        assert cid in conv.conversations
        # Add messages and save
        conv.add_message(cid, MessageRole.USER, "hello")
        conv.add_message(cid, MessageRole.ASSISTANT, "hi")
        conv.save_conversation(cid)
        # Reload via new instance to cover _load_conversations
        conv2 = ConversationService(data_dir, inactivity_timeout_seconds=0)
        assert cid in conv2.conversations
        # Clean inactive marks inactive
        conv2.clean_inactive()
        assert conv2.conversations[cid].active is False
        # List user conversations includes preview and message_count
        items = conv2.get_user_conversations("u1")
        assert items and items[0]["id"] == cid and items[0]["message_count"] >= 2
