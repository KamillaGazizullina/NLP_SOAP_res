import re
from typing import Dict, List, Set, Tuple


def normalize_text(text: str) -> str:
    if text is None:
        return ""

    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str) -> List[str]:
    text = normalize_text(text)
    text = re.sub(r"[^\w\sа-яё/-]", " ", text, flags=re.IGNORECASE)
    tokens = [t for t in text.split() if t.strip()]
    return tokens


def lcs_length(a: List[str], b: List[str]) -> int:
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[n][m]


def rouge_l_score(pred: str, gold: str) -> float:
    pred_tokens = tokenize(pred)
    gold_tokens = tokenize(gold)

    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0

    lcs = lcs_length(pred_tokens, gold_tokens)
    recall = lcs / len(gold_tokens)
    precision = lcs / len(pred_tokens)

    if recall + precision == 0:
        return 0.0

    beta = 1.2
    num = (1 + beta**2) * precision * recall
    den = recall + beta**2 * precision
    return num / den if den > 0 else 0.0


SYMPTOM_KEYWORDS = {
    "температура", "кашель", "слабость", "горло", "боль", "тошнота",
    "сыпь", "зуд", "насморк", "чихание", "голова", "шум", "живот",
    "поясница", "давление", "хрипы", "одышка", "отек", "покраснение"
}


OBJECTIVE_KEYWORDS = {
    "осмотр", "гиперемирован", "хрипов", "температура", "ад", "пульс",
    "пальпации", "болезненность", "крапивницы", "дыхание", "аускультации",
    "нормальная", "свободное", "подвздошной", "паравертебрально"
}


ASSESSMENT_KEYWORDS = {
    "орви", "ринит", "аппендицит", "аллергическую", "давления",
    "мышечно-тонический", "инфекции", "синдром"
}


PLAN_KEYWORDS = {
    "обильное", "питье", "покой", "жаропонижающее", "консультация",
    "промывание", "наблюдение", "антигистаминный", "аллерген",
    "стационар", "контроль", "соли", "ограничение", "нагрузки"
}


def extract_entities_for_section(text: str, section: str) -> Set[str]:
    tokens = set(tokenize(text))

    if section == "S":
        return {t for t in tokens if t in SYMPTOM_KEYWORDS}
    if section == "O":
        return {t for t in tokens if t in OBJECTIVE_KEYWORDS}
    if section == "A":
        return {t for t in tokens if t in ASSESSMENT_KEYWORDS}
    if section == "P":
        return {t for t in tokens if t in PLAN_KEYWORDS}

    return set()


def entity_coverage(pred: str, gold: str, section: str) -> float:
    pred_entities = extract_entities_for_section(pred, section)
    gold_entities = extract_entities_for_section(gold, section)

    if not gold_entities and not pred_entities:
        return 1.0
    if not gold_entities:
        return 1.0
    if not pred_entities:
        return 0.0

    covered = len(pred_entities & gold_entities)
    return covered / len(gold_entities)


def evaluate_soap(prediction: Dict[str, str], gold: Dict[str, str]) -> Tuple[List[Dict], float, float]:
    rows = []
    rouge_values = []
    coverage_values = []

    for section in ["S", "O", "A", "P"]:
        pred_text = prediction.get(section, "—")
        gold_text = gold.get(section, "—")

        rouge = rouge_l_score(pred_text, gold_text)
        coverage = entity_coverage(pred_text, gold_text, section)

        rouge_values.append(rouge)
        coverage_values.append(coverage)

        rows.append(
            {
                "Section": section,
                "ROUGE-L": f"{rouge * 100:.0f}%",
                "Entity Coverage": f"{coverage * 100:.0f}%"
            }
        )

    avg_rouge = sum(rouge_values) / len(rouge_values)
    avg_coverage = sum(coverage_values) / len(coverage_values)

    return rows, avg_rouge, avg_coverage