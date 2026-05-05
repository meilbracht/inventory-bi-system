from dataclasses import dataclass

@dataclass
class SessionState:
    base_url: str = "http://127.0.0.1:8000"
    username: str = ""
    role: str = ""  # "admin", "clerk", "viewer"
