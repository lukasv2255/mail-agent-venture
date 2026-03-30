"""
Klasifikátor emailů — určí typ dotazu pomocí GPT-4o mini.
"""
import logging
import os

from openai import OpenAI

logger = logging.getLogger(__name__)

UNKNOWN_TYPE = "unknown"
client = None


def get_client():
    global client
    if client is None:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client


def load_classifier_prompt():
    prompt_file = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "classifier_prompt.txt"
    )
    with open(prompt_file, encoding="utf-8") as f:
        return f.read()


def classify_email(email):
    """
    Vrátí typ emailu jako string (např. 'type_a', 'type_b', 'unknown').
    """
    system_prompt = load_classifier_prompt()

    user_message = (
        f"Od: {email['from']}\n"
        f"Předmět: {email['subject']}\n\n"
        f"{email['body'][:2000]}"
    )

    response = get_client().chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=50,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    result = response.choices[0].message.content.strip().lower()
    logger.info(f"Klasifikace emailu '{email['subject']}': {result}")
    return result
