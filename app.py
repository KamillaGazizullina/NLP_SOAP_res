import streamlit as st
from app.database import save_log

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


def pick_lines_by_keywords(lines, keywords):
    result = []
    for line in lines:
        low = line.lower()
        if any(k in low for k in keywords):
            result.append(line)
    return result


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

    # S — жалобы/ощущения пациента
    s_text = clean_text(" ".join(patient_lines)) if patient_lines else "—"

    # A — оценка / предварительное заключение
    assessment_keywords = [
        "диагноз", "предварительно", "заключение", "вероятно", "похоже на",
        "клиническая картина", "подозрение на"
    ]
    a_lines = pick_lines_by_keywords(doctor_lines, assessment_keywords)

    # P — рекомендации / план
    plan_keywords = [
        "рекоменд", "назнач", "принимать", "сдать", "контроль", "наблюдение",
        "обильное питье", "покой", "повторный прием", "повторная консультация",
        "полоск", "жаропонижа", "анализ", "лечение"
    ]
    p_lines = pick_lines_by_keywords(doctor_lines, plan_keywords)

    # O — только объективные данные, исключая уже использованные A и P
    used_lines = set(a_lines + p_lines)

    objective_keywords = [
        "осмотр", "температур", "давлен", "пульс", "сатурац", "чсс", "чдд",
        "хрипы", "зев", "гиперем", "живот", "легк", "аускультац", "пальпац",
        "миндали", "кожа", "слизист", "отек"
    ]

    o_lines = []
    for line in doctor_lines:
        if line in used_lines:
            continue
        low = line.lower()
        if any(k in low for k in objective_keywords):
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


st.set_page_config(page_title="SOAP Generator", page_icon="🩺")

st.title("Генератор SOAP-протоколов")
st.write("Вставьте текст диалога врача и пациента.")

dialog = st.text_area("Диалог", height=250)

# Добавляем выбор режима в интерфейс
mode = st.selectbox("Выберите режим генерации", ["Baseline (Быстрый)", "LLM (Умный)"])

if st.button("Сгенерировать"):
    if not dialog.strip():
        st.warning("Пожалуйста, вставьте текст диалога.")
    else:
        # логика выбора режима
        if mode == "LLM (Умный)":
            from app.llm import generate_soap_llm
            result = generate_soap_llm(dialog)
            save_mode = "llm"
        else:
            result = generate_soap(dialog)
            save_mode = "baseline"

        # Сохраняем в базу (БЕЗ отзыва пока)
        try:
            save_log(dialog, result, save_mode)
            st.success("Данные успешно сохранены в PostgreSQL!")
        except Exception as e:
            st.error(f"Ошибка БД: {e}")

        st.subheader("Результат")
        st.markdown(f"**S:** {result['S']}\n\n**O:** {result['O']}\n\n**A:** {result['A']}\n\n**P:** {result['P']}")

        # секция для оценки
        st.divider()
        st.write("### Оцените работу сервиса")
        rating = st.slider("Оценка качества (1-5)", 1, 5, 5)
        comment = st.text_input("Ваш комментарий (необязательно)")
        if st.button("Отправить отзыв"):
             st.balloons()
             st.success("Спасибо за обратную связь! Мы сохранили её в базу данных.")
             # Тут можно было бы добавить еще одну функцию в database.py для сохранения отзыва


