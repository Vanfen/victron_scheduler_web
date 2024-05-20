from typing import Dict
from typing import Optional

from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
# from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from typing import Tuple

import os
from dotenv import load_dotenv
load_dotenv('.env')


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.cookies.get(
            "access_token"
        )  # changed to accept access token from httpOnly Cookie
        if not authorization:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return authorization

# conf = ConnectionConfig(
#     MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
#     MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
#     MAIL_FROM=os.getenv('MAIL_FROM'),
#     MAIL_PORT=int(os.getenv('MAIL_PORT')),
#     MAIL_SERVER=os.getenv('MAIL_SERVER'),
#     MAIL_FROM_NAME=os.getenv('MAIN_FROM_NAME'),
#     MAIL_STARTTLS = True,
#     MAIL_SSL_TLS = False,
#     USE_CREDENTIALS = True,
#     VALIDATE_CERTS = False,
#     TEMPLATE_FOLDER='./templates/',
# )

# async def send_reset_token_email(subject: str, email_to: str, body: dict):
#     message = MessageSchema(
#         subject=subject,
#         recipients=[email_to],
#         template_body=body,
#         subtype="html",
#     )
#     fm = FastMail(conf)
#     await fm.send_message(message, template_name='reset_token_email.html')