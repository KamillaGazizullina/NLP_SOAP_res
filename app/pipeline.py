def clean_text(text: str) -> str:
    return " ".join(text.split()).strip()


def split_dialog(dialog: str):
    patient_lines = []
    doctor_lines = []
    other_lines = []

    lines = dialog.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        low = line.lower()

        if low.startswith("пациент:"):
            patient_lines.append(clean_text(line.split(":", 1)[1]))
        elif low.startswith("врач:") or low.startswith("доктор:"):
            doctor_lines.append(clean_text(line.split(":", 1)[1]))
        else:
            other_lines.append(clean_text(line))

    return patient_lines, doctor_lines, other_lines


def is_question_line(line: str) -> bool:
    return "?" in line


def is_plan_line(line: str) -> bool:
    low = line.lower()
    plan_markers = [
        "рекоменд", "назнач", "принимать", "сдать", "контроль", "наблюдение",
        "обильное питье", "покой", "повторный прием", "повторная консультация",
        "полоск", "жаропонижа", "анализ", "лечение", "обратиться", "ограничение нагрузки",
        "антигистамин"
    ]
    return any(marker in low for marker in plan_markers)


def is_assessment_line(line: str) -> bool:
    low = line.lower()

    assessment_markers = [
        "диагноз", "предварительно", "заключение", "вероятно", "похоже на",
        "клиническая картина", "соответствует", "подозрение на"
    ]

    if any(marker in low for marker in assessment_markers):
        return True

    # Важно: ловим только именно формулировки типа
    # "требуется исключить ..." / "необходимо исключить ..."
    # а не любые строки со словом "исключить"
    if "требуется исключить" in low or "необходимо исключить" in low:
        return True

    return False


def is_objective_line(line: str) -> bool:
    low = line.lower()
    objective_keywords = [
        "осмотр", "температур", "давлен", "ад ", "пульс", "сатурац", "чсс", "чдд",
        "хрипы", "зев", "гиперем", "живот", "легк", "аускультац", "пальпац",
        "миндали", "кожа", "слизист", "отек", "болезненность", "дыхание",
        "сып", "крапивниц", "пояснич", "паравертебраль"
    ]
    return any(keyword in low for keyword in objective_keywords)


def generate_soap(dialog: str) -> dict:
    dialog = dialog.replace("\r\n", "\n").replace("\r", "\n").strip()

    if len(dialog) < 30:
        return {
            "S": "Недостаточно данных для формирования отчёта.",
            "O": "—",
            "A": "—",
            "P": "—",
        }

    patient_lines, doctor_lines, other_lines = split_dialog(dialog)

    # S — жалобы и ощущения пациента
    s_text = clean_text(" ".join(patient_lines)) if patient_lines else "—"

    # Убираем вопросы врача
    doctor_statement_lines = [line for line in doctor_lines if not is_question_line(line)]

    # A
    a_lines = [line for line in doctor_statement_lines if is_assessment_line(line)]

    # P
    p_lines = [line for line in doctor_statement_lines if is_plan_line(line)]

    used_lines = set(a_lines + p_lines)

    # O
    o_lines = []
    for line in doctor_statement_lines:
        if line in used_lines:
            continue
        if is_objective_line(line):
            o_lines.append(line)

    a_text = clean_text(" ".join(a_lines)) if a_lines else "—"
    p_text = clean_text(" ".join(p_lines)) if p_lines else "—"
    o_text = clean_text(" ".join(o_lines)) if o_lines else "—"

    if s_text == "—" and not doctor_lines and other_lines:
        s_text = clean_text(" ".join(other_lines))

    return {
        "S": s_text,
        "O": o_text,
        "A": a_text,
        "P": p_text,
    }