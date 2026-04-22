"""
Generátor odpovědí — vytvoří draft odpovědi pro daný typ emailu pomocí GPT-4o mini.
"""
import logging
import os

from openai import OpenAI

from src.config import PROMPTS_DIR
from src.kb_loader import load_kb

logger = logging.getLogger(__name__)

client = None


def get_client():
    global client
    if client is None:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client


def load_response_prompt(email_type):
    prompt_file = PROMPTS_DIR / f"response_{email_type}.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt soubor neexistuje: {prompt_file}")
    with open(prompt_file, encoding="utf-8") as f:
        return f.read()


def generate_reply(email, email_type):
    """
    Vygeneruje text odpovědi pro daný email a typ.
    """
    system_prompt = load_response_prompt(email_type)
    kb = load_kb()
    if kb:
        system_prompt = f"{system_prompt}\n\n## Knowledge Base\n\n{kb}"

    user_message = (
        f"Od: {email['from']}\n"
        f"Předmět: {email['subject']}\n\n"
        f"{email['body'][:2000]}"
    )

    response = get_client().chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    reply = response.choices[0].message.content.strip()
    logger.info(f"Vygenerována odpověď pro typ '{email_type}', délka: {len(reply)} znaků.")
    return reply
