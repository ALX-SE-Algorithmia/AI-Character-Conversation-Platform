from types import SimpleNamespace

from backend.core.config import Settings
from backend.service.llm_service import LLMService
from backend.service.platform_service import PlatformService
from backend.model.schemas import MessageRole


def test_llm_service_stub_mode_without_key():
    settings = Settings(GROQ_API_KEY=None)
    llm = LLMService(settings)
    assert llm.stub_mode is True


def test_llm_service_non_stub_chat_path(monkeypatch):
    settings = Settings(GROQ_API_KEY="dummy")
    llm = LLMService(settings)
    # Force into non-stub and attach fake client
    llm.stub_mode = False

    class FakeMessage:
        def __init__(self, content):
            self.content = content

    class FakeChoice:
        def __init__(self, content):
            self.message = FakeMessage(content)

    class FakeCompletion:
        def __init__(self, content):
            self.choices = [FakeChoice(content)]

    class FakeCompletions:
        def create(self, **kwargs):
            return FakeCompletion("ok from fake")

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeGroqClient:
        def __init__(self):
            self.chat = FakeChat()

    llm._groq_client = FakeGroqClient()
    out = llm.chat([{"role": "user", "content": "hi"}], model="m", temperature=0.1, max_tokens=16)
    assert out == "ok from fake"


def test_llm_service_non_stub_chat_exception_returns_fallback():
    settings = Settings(GROQ_API_KEY="dummy")
    llm = LLMService(settings)
    llm.stub_mode = False

    class Boom(Exception):
        pass

    class FakeCompletions:
        def create(self, **kwargs):
            raise Boom("fail")

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeGroqClient:
        def __init__(self):
            self.chat = FakeChat()

    llm._groq_client = FakeGroqClient()
    out = llm.chat([{"role": "user", "content": "hi"}])
    assert "trouble responding" in out


def test_platform_service_misc_paths(tmp_path):
    ps = PlatformService(Settings(GROQ_API_KEY=None))
    # Clean response strips prefixes
    assert ps._clean_response("Assistant: Hello").startswith("Hello")
    # Generate a response to create a conversation
    result = ps.generate_response("hello", None, character_id="coach", user_id="u1")
    cid = result["conversation_id"]
    # characters_map property
    assert "coach" in ps.characters_map
    # get_user_conversations shows our conversation
    items = ps.get_user_conversations("u1")
    assert any(it["id"] == cid for it in items)
    # clean_inactive_conversations executes without error
    ps.clean_inactive_conversations()
    # _system_prompt_for toggles intro text
    char = ps.characters.characters["coach"]
    p_first = ps._system_prompt_for(char, True)
    p_next = ps._system_prompt_for(char, False)
    assert p_first != p_next and "first message" in p_first
