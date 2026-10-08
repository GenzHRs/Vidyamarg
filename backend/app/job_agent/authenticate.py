"""Interactive operator-only Telegram session provisioning; never run from web workers."""
import asyncio
import os
from pathlib import Path
from getpass import getpass
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from app.job_agent.settings import load_config

async def authenticate():
    config = load_config()
    if not config["api_id"] or not config["api_hash"] or not config["phone"]:
        raise RuntimeError("Set TG_API_ID, TG_API_HASH and TG_PHONE")
    client = TelegramClient(StringSession(), config["api_id"], config["api_hash"])
    await client.connect()
    try:
        await client.send_code_request(config["phone"])
        code = getpass("Telegram login code: ")
        try:
            await client.sign_in(config["phone"], code)
        except SessionPasswordNeededError:
            await client.sign_in(password=getpass("Telegram two-factor password: "))
        path = Path(os.getenv("TG_SESSION_FILE", "storage/telegram/session.txt"))
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as target:
            target.write(client.session.save())
        path.chmod(0o600)
        print("Session saved. Set TG_SESSION_FILE to this private file's path.")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(authenticate())
