import requests
from typing import Any, Dict, List, Optional

class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def login(self, username: str, password: str) -> Dict[str, Any]:
        # backend expects form-like query params in our simple MVP
        r = requests.post(f"{self.base_url}/login", params={"username": username, "password": password}, timeout=10)
        r.raise_for_status()
        return r.json()
    
    def list_users(self, username: str, role: str):
        r = requests.get(f"{self.base_url}/users", params={"username": username, "role": role}, timeout=10)
        r.raise_for_status()
        return r.json()

    def create_user(self, username: str, role: str, new_username: str, password: str, new_role: str):
        r = requests.post(
            f"{self.base_url}/users",
            params={"username": username, "role": role},
            json={"username": new_username, "password": password, "role": new_role},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    
    def update_user_role(self, username: str, role: str, user_id: int, new_role: str):
        r = requests.put(
            f"{self.base_url}/users/{user_id}/role",
            params={"username": username, "role": role},
            json={"role": new_role},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    
    def delete_user(self, username: str, role: str, user_id: int):
        r = requests.delete(f"{self.base_url}/users/{user_id}", params={"username": username, "role": role}, timeout=10)
        r.raise_for_status()
        return r.json()

    def search_items(self, q: str = "", base: str = "") -> List[Dict[str, Any]]:
        r = requests.get(f"{self.base_url}/items", params={"q": q, "base": base}, timeout=10)
        r.raise_for_status()
        return r.json()

    def adjust_qty(
        self,
        username: str,
        role: str,
        stock_number: str,
        base_location: str,
        action: str,
        qty: int,
        reason: str
    ):
        r = requests.post(
            f"{self.base_url}/items/adjust",
            params={
                "username": username,
                "role": role,
                "stock_number": stock_number,
                "base_location": base_location,
                "action": action,
                "qty": qty,
                "reason": reason,
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    
    def get_transactions(self, base: str = "", stock_number: str = "", limit: int = 500):
        r = requests.get(
        f"{self.base_url}/transactions",
        params={"base": base, "stock_number": stock_number, "limit": limit},
        timeout=10,
        )
        r.raise_for_status()
        return r.json()
    
    def import_items(self, username: str, role: str, excel_path: str):
        with open(excel_path, "rb") as f:
            r = requests.post(
                f"{self.base_url}/import/items",
                params={"username": username, "role": role},
                files={"file": f},
                timeout=60,
            )

        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(f"{e}\nBackend says: {r.text}")

        return r.json()





