import re


def normalize_text(text: str) -> str:
    if text is None:
        return "—"

    text = str(text).strip().lower()

    if text in {"", "-", "—"}:
        return "—"

    text = re.sub(r"[^\w\sа-яё/.-]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def token_set(text: str) -> set:
    text = normalize_text(text)

    if text == "—":
        return set()

    stopwords = {
        "и", "в", "во", "на", "по", "при", "с", "со", "у", "к", "от", "до",
        "не", "нет", "как", "или", "а", "но", "же", "что", "это", "только",
        "уже", "около", "было", "есть"
    }

    return {t for t in text.split() if len(t) > 1 and t not in stopwords}


def section_similarity(pred: str, gold: str) -> float:
    pred_norm = normalize_text(pred)
    gold_norm = normalize_text(gold)

    if pred_norm == "—" and gold_norm == "—":
        return 1.0

    pred_tokens = token_set(pred_norm)
    gold_tokens = token_set(gold_norm)

    if not pred_tokens and not gold_tokens:
        return 1.0

    if not pred_tokens or not gold_tokens:
        return 0.0

    return len(pred_tokens & gold_tokens) / len(pred_tokens | gold_tokens)


def compare_soap(prediction: dict, gold: dict):
    sections = ["S", "O", "A", "P"]
    rows = []
    similarities = []

    for section in sections:
        pred_text = prediction.get(section, "—")
        gold_text = gold.get(section, "—")

        sim = section_similarity(pred_text, gold_text)
        similarities.append(sim)

        gold_empty = normalize_text(gold_text) == "—"
        pred_empty = normalize_text(pred_text) == "—"

        if gold_empty:
            empty_eval = "Да" if pred_empty else "Нет"
        else:
            empty_eval = "Н/П"

        rows.append(
            {
                "Section": section,
                "Similarity": f"{sim * 100:.0f}%",
                "Empty section handled": empty_eval,
            }
        )

    overall = sum(similarities) / len(similarities)
    return rows, overall