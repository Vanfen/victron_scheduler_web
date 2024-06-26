from time import sleep
from typing import List, Optional
from fastapi import Request


class UserLoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")
        print("load_data")
    
    async def is_valid(self):
        if not self.password or not len(self.password) >= 4:
            self.errors.append("A valid password is required")
        if not self.errors:
            return True
        return False