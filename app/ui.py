import json
from pathlib import Path

import streamlit as st

from app.metrics import evaluate_soap
from app.llm import generate_soap_llm
from app.pipeline import generate_soap


def load_test_dialogs():
    data_path = Path(__file__).resolve().parent.parent / "data" / "test_dialogs.json"

    if not data_path.exists():
        return []

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


st.set_page_config(page_title="SOAP Generator", page_icon="🩺", layout="centered")

st.title("Генератор SOAP-протоколов")
st.caption("MVP: локальный LLM как основной режим, baseline используется как fallback")
st.write("Выберите тестовый сценарий или вставьте свой текст диалога врача и пациента.")

test_dialogs = load_test_dialogs()
selected_case = None

if "selected_case_title" not in st.session_state:
    st.session_state["selected_case_title"] = None

if "dialog_text" not in st.session_state:
    st.session_state["dialog_text"] = ""

mode = st.radio(
    "Режим генерации",
    ["LLM (основной режим)", "Baseline fallback"],
    index=0,
    horizontal=True
)

if test_dialogs:
    titles = [case["title"] for case in test_dialogs]
    selected_title = st.selectbox("Тестовый сценарий", titles, key="case_selector")

    selected_case = next(case for case in test_dialogs if case["title"] == selected_title)

    if st.session_state["selected_case_title"] != selected_title:
        st.session_state["selected_case_title"] = selected_title
        st.session_state["dialog_text"] = selected_case["dialog"]

    st.caption(f"ID кейса: {selected_case['id']}")
else:
    st.info("Файл data/test_dialogs.json не найден. Можно работать с ручным вводом.")

dialog = st.text_area("Диалог", height=260, key="dialog_text")

if st.button("Сгенерировать SOAP"):
    if not dialog.strip():
        st.warning("Пожалуйста, вставьте текст диалога.")
    else:
        try:
            if mode == "LLM (основной режим)":
                with st.spinner("LLM обрабатывает диалог... Это может занять до пары минут при локальном запуске."):
                    result = generate_soap_llm(dialog)
            else:
                with st.spinner("Baseline fallback обрабатывает диалог..."):
                    result = generate_soap(dialog)
        except Exception as e:
            st.error(f"Ошибка LLM-режима: {e}")
            st.info("LLM-режим недоступен, поэтому используется baseline fallback.")
            result = generate_soap(dialog)

        st.subheader("Результат")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### S — Subjective")
            st.write(result["S"])

            st.markdown("### A — Assessment")
            st.write(result["A"])

        with col2:
            st.markdown("### O — Objective")
            st.write(result["O"])

            st.markdown("### P — Plan")
            st.write(result["P"])

        soap_text = (
            f"S: {result['S']}\n\n"
            f"O: {result['O']}\n\n"
            f"A: {result['A']}\n\n"
            f"P: {result['P']}"
        )

        st.download_button(
            label="Скачать SOAP как .txt",
            data=soap_text,
            file_name="soap_note.txt",
            mime="text/plain"
        )

        if selected_case and selected_case.get("gold"):
            gold = selected_case["gold"]
            rows, avg_rouge, avg_coverage = evaluate_soap(result, gold)

            with st.expander("Показать эталонный SOAP и оценку качества"):
                st.subheader("Эталонный SOAP")

                g1, g2 = st.columns(2)

                with g1:
                    st.markdown("### S — Gold")
                    st.write(gold["S"])

                    st.markdown("### A — Gold")
                    st.write(gold["A"])

                with g2:
                    st.markdown("### O — Gold")
                    st.write(gold["O"])

                    st.markdown("### P — Gold")
                    st.write(gold["P"])

                st.markdown("---")
                st.subheader("Автоматическая оценка качества")
                st.caption(
                    "ROUGE-L сравнивает совпадение с эталонным SOAP, Entity Coverage оценивает покрытие ключевых сущностей по секциям."
                )
                st.table(rows)

                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Средний ROUGE-L", f"{avg_rouge * 100:.0f}%")
                with c2:
                    st.metric("Средний Entity Coverage", f"{avg_coverage * 100:.0f}%")