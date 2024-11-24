"""AuthService is defined here."""

import datetime
import time

import requests
from loguru import logger


class AuthService:
    """Auth service is needed to exchange oauth token for YandexCloud to IAM token"""

    def __init__(self, oauth_token: str, endpoint: str = "https://iam.api.cloud.yandex.net/iam/v1/tokens"):
        self.endpoint = endpoint
        self.oauth_token = oauth_token
        self.iam: str = ...
        self.validity_time = 0
        """IAM token validity time in seconds"""
        self.updated_at = time.time()
        """Update time in epoch time"""

    def update(self):
        """Update IAM token using oauth token."""
        response = requests.post(self.endpoint, json={"yandexPassportOauthToken": self.oauth_token}, timeout=10)
        if response.status_code != 200:
            logger.error("Could not exchange oauth token for IAM token (response code {})", response.status_code)
            logger.debug("Response: {}", response.text)
            raise RuntimeError("Could not update IAM code")

        body = response.json()
        self.iam = body["iamToken"]
        # trim datetime for parsing 2023-11-22T02:53:03.540231221Z -> 2023-11-22T02:53:03.54023
        expire = datetime.datetime.fromisoformat(body["expiresAt"][:26])
        self.validity_time = (expire - datetime.datetime.utcnow()).seconds
        self.updated_at = int(time.time())

    def need_update(self) -> bool:
        """Return true if token has lived more than 15% of its validity time (as docs say about 10% at
        https://cloud.yandex.ru/docs/iam/concepts/authorization/iam-token#lifetime)).
        """
        return time.time() - self.updated_at > self.validity_time * 0.15

    def get_iam(self) -> str:
        """Return valid IAM token, updating it if necessary."""
        if self.need_update():
            self.update()
        return self.iam
