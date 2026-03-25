import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


SYSTEM_PROMPT = """
Ты медицинский ассистент, который формирует SOAP-протокол
только на основе переданного диалога врача и пациента.

Правила:
1. Не придумывай симптомы, диагнозы, лекарства и факты.
2. Используй только информацию из входного текста.
3. Если данных для раздела нет, ставь "—".
4. Пиши лаконично, в медицинском стиле.
5. Верни строго JSON-объект формата:

{
  "S": "...",
  "O": "...",
  "A": "...",
  "P": "..."
}
""".strip()


FEW_SHOT_EXAMPLE = """
Диалог:
Пациент: Уже 3 дня температура 38, кашель, слабость, болит горло.
Врач: Когда начались симптомы?
Пациент: Три дня назад, сначала появилась слабость, потом температура.
Врач: При осмотре зев гиперемирован, хрипов нет, температура 37.8.
Врач: Предварительно похоже на ОРВИ.
Врач: Рекомендую обильное питье, покой, жаропонижающее при температуре выше 38.5 и повторную консультацию при ухудшении.

Ответ:
{
  "S": "Температура до 38°C в течение 3 дней, кашель, слабость, боль в горле.",
  "O": "При осмотре зев гиперемирован, хрипов нет, температура 37.8.",
  "A": "Предварительно похоже на ОРВИ.",
  "P": "Обильное питье, покой, жаропонижающее при температуре выше 38.5, повторная консультация при ухудшении."
}
""".strip()


def safe_json_extract(text: str) -> dict:
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass

    return {"S": "—", "O": "—", "A": "—", "P": "—"}


def normalize_soap(obj: dict) -> dict:
    result = {}
    for key in ["S", "O", "A", "P"]:
        value = obj.get(key, "—")
        value = str(value).strip()
        result[key] = value if value else "—"
    return result


def generate_soap_llm(dialog: str) -> dict:
    model_name = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/chat")

    user_prompt = f"""
{FEW_SHOT_EXAMPLE}

Теперь обработай новый диалог.

Диалог:
{dialog}

Верни только JSON.
""".strip()

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    response = requests.post(base_url, json=payload, timeout=180)
    response.raise_for_status()
    data = response.json()

    content = data.get("message", {}).get("content", "").strip()
    parsed = safe_json_extract(content)
    return normalize_soap(parsed)