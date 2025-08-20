from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict, Optional

from backend.core.logging import get_logger
from backend.model.schemas import UserProfile


logger = get_logger(__name__)


class UserService:
    def __init__(self):
        self.users: Dict[str, UserProfile] = {}

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username: str, password: str) -> UserProfile:
        import uuid
        uid = str(uuid.uuid4())
        user = UserProfile(id=uid, username=username, password_hash=self._hash(password))
        self.users[uid] = user
        return user

    def authenticate(self, username: str, password: str) -> Optional[UserProfile]:
        pw = self._hash(password)
        for user in self.users.values():
            if user.username == username and user.password_hash == pw:
                user.last_login = datetime.now()
                return user
        return None
