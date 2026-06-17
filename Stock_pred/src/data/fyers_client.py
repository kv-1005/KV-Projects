"""
Fyers API v3 — Authentication & Client Singleton
-------------------------------------------------
Handles daily login flow (OAuth2 token generation),
session management, and provides a ready-to-use fyersModel.

Usage:
    from src.data.fyers_client import get_fyers_client
    fyers = get_fyers_client()
    quotes = fyers.quotes({"symbols": "NSE:RELIANCE-EQ"})
"""

from __future__ import annotations

import os
import webbrowser
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

load_dotenv()

_CLIENT_ID    = os.getenv("FYERS_CLIENT_ID", "")
_SECRET_KEY   = os.getenv("FYERS_SECRET_KEY", "")
_REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI", "http://127.0.0.1:5000/")

_fyers_instance: fyersModel.FyersModel | None = None


def _generate_access_token() -> str:
    """
    Opens Fyers OAuth2 URL in browser, asks user to paste the redirect URL,
    and exchanges the auth_code for a long-lived access token.
    Saves the token to `.fyers_token` so we don't re-login intraday.
    """
    from fyers_apiv3.fyersModel import SessionModel  # type: ignore

    session = SessionModel(
        client_id=_CLIENT_ID,
        secret_key=_SECRET_KEY,
        redirect_uri=_REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code",
    )
    auth_url = session.generate_authcode()
    print(f"\n[Fyers Login] Opening browser for OAuth login...\n{auth_url}\n")
    webbrowser.open(auth_url)

    redirect_url = input("[Fyers Login] Paste the full redirect URL here: ").strip()
    parsed = urlparse(redirect_url)
    auth_code = parse_qs(parsed.query).get("auth_code", [""])[0]
    if not auth_code:
        raise ValueError("auth_code not found in redirect URL. Check the pasted URL.")

    session.set_token(auth_code)
    response = session.generate_token()
    access_token: str = response.get("access_token", "")
    if not access_token:
        raise RuntimeError(f"Token generation failed: {response}")

    # Cache the token so we don't re-login during the same session
    with open(".fyers_token", "w") as f:
        f.write(access_token)

    print("[Fyers Login] ✅ Access token generated and cached.")
    return access_token


def _load_cached_token() -> str | None:
    """Return cached token if it exists (valid for the current trading day)."""
    if os.path.exists(".fyers_token"):
        with open(".fyers_token") as f:
            token = f.read().strip()
        if token:
            return token
    return None


def get_fyers_client(force_login: bool = False) -> fyersModel.FyersModel:
    """
    Returns an authenticated FyersModel singleton.
    On first call (or if force_login=True), triggers browser login flow.
    Subsequent calls in the same process return the cached instance.
    """
    global _fyers_instance
    if _fyers_instance is not None and not force_login:
        return _fyers_instance

    access_token = None if force_login else _load_cached_token()
    if access_token is None:
        access_token = _generate_access_token()

    # Ensure log directory exists before Fyers tries to create the log file
    os.makedirs("artifacts/fyers_logs", exist_ok=True)

    _fyers_instance = fyersModel.FyersModel(
        client_id=_CLIENT_ID,
        token=access_token,
        log_path="artifacts/fyers_logs",
        is_async=False,
    )
    # Quick profile check to validate token
    profile = _fyers_instance.get_profile()
    if profile.get("code") != 200:
        print("[Fyers] Token invalid, re-logging in...")
        access_token = _generate_access_token()
        _fyers_instance = fyersModel.FyersModel(
            client_id=_CLIENT_ID,
            token=access_token,
            log_path="artifacts/fyers_logs",
            is_async=False,
        )

    print(f"[Fyers] ✅ Connected as: {profile.get('data', {}).get('name', 'Unknown')}")
    return _fyers_instance
