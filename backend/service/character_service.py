from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Dict, List

from backend.core.logging import get_logger
from backend.model.schemas import Character
from backend.service.llm_service import LLMService


logger = get_logger(__name__)


class CharacterService:
    def __init__(self, data_dir: Path, llm: LLMService):
        self.data_dir = data_dir
        self.characters_file = self.data_dir / "characters.json"
        self.llm = llm
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.characters: Dict[str, Character] = self._load_characters()

    def _load_characters(self) -> Dict[str, Character]:
        try:
            if not self.characters_file.exists():
                logger.info("No characters.json found, writing defaults")
                self._write_default_characters()
            with self.characters_file.open("r") as f:
                character_data = json.load(f)
            chars = {c["id"]: Character(**c) for c in character_data}
            logger.info("Loaded %d characters", len(chars))
            return chars
        except Exception as e:
            logger.error("Error loading characters: %s", e)
            return {}

    def _write_default_characters(self) -> None:
        defaults = [
            {
                "id": "coach",
                "name": "Interview Coach",
                "description": "An expert interview coach helping you prepare for job interviews.",
                "personality": "Professional, supportive, and insightful.",
                "system_prompt": (
                    "You are an expert interview coach helping prepare candidates for interviews. "
                    "Provide helpful advice, use the STAR framework, and be supportive but honest."
                ),
                "avatar_url": "coach.png",
                "category": "professional",
                "tags": ["interview", "career", "advice"],
            },
        ]
        with self.characters_file.open("w") as f:
            json.dump(defaults, f, indent=2)

    def save_characters(self) -> None:
        try:
            data = [c.model_dump() for c in self.characters.values()]
            with self.characters_file.open("w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Error saving characters: %s", e)

    def generate_character(self, topic: str, traits: List[str]) -> Character:
        prompt = f"""
        Create a detailed AI character based on the following specifications:

        Topic or theme: {topic}
        Personality traits: {', '.join(traits)}

        Please provide a JSON object with fields: name, description, personality, system_prompt, category, tags
        """
        text = self.llm.chat([
            {"role": "user", "content": prompt}
        ])
        # Try to extract JSON object
        import re
        try:
            json_match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
            candidate = json_match.group(1) if json_match else text
            obj = json.loads(candidate)
        except Exception:
            logger.warning("Falling back to minimal character from LLM text")
            obj = {
                "name": f"Generated {topic.title()}",
                "description": text[:200],
                "personality": ", ".join(traits) or "helpful",
                "system_prompt": f"You are a helpful assistant about {topic}.",
                "category": "generated",
                "tags": [topic] + traits,
            }
        char_id = f"gen_{uuid.uuid4().hex[:8]}"
        character = Character(
            id=char_id,
            name=obj.get("name", f"Generated {topic}"),
            description=obj.get("description", ""),
            personality=obj.get("personality", "helpful"),
            system_prompt=obj.get("system_prompt", f"You are a helpful assistant about {topic}"),
            avatar_url="generated.png",
            category=obj.get("category", "generated"),
            tags=obj.get("tags", [topic] + traits),
        )
        self.characters[character.id] = character
        self.save_characters()
        return character
