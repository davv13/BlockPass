from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    def create_user(self, username: str, hashed_pw: str) -> dict:
        ...

    @abstractmethod
    def get_by_username(self, username: str) -> dict | None:
        ...

    @abstractmethod
    def get_by_id(self, user_id: str) -> dict | None:
        ...
