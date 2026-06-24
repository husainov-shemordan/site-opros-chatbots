import os
import io
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.express as px
import streamlit as st

# --- Инициализация Firebase (Умная версия для Cloud и Локалки) ---
import json  # <--- Добавь эту строку в самые верхние импорты, если её там нет!

if not firebase_admin._apps:
    # 1. Пытаемся взять ключ из Secrets (для Streamlit Cloud)
    key_content = os.getenv("FIREBASE_KEY")

    if key_content:
        # Если ключ есть в настройках облака, превращаем текст в объект
        cred_dict = json.loads(key_content)
        cred = credentials.Certificate(cred_dict)

    # 2. Если ключа в облаке нет, пытаемся найти файл (для локального запуска)
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")

    # 3. Если ничего не нашли — выдаем ошибку
    else:
        st.error("❌ Ошибка: Ключ Firebase не найден ни в Secrets, ни в файле!")
        st.stop()

    firebase_admin.initialize_app(cred)

db = firestore.client()

st.set_page_config(page_title="AI Monitoring Premium", layout="wide")

# --- БЛОК ПРОДВИНУТЫХ КИБЕР-АНИМАЦИЙ ---
st.markdown("""
<style>
    /* 1. Плавный переход при смене вкладок (Fade-in + Slide-up) */
    .main .block-container {
        animation: fadeInSlide 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }

    @keyframes fadeInSlide {
        0% { opacity: 0; transform: translateY(20px); filter: blur(5px); }
        100% { opacity: 1; transform: translateY(0); filter: blur(0); }
    }

    /* 2. Анимация кнопок (улучшенная версия) */
    div.stButton > button, div.stDownloadButton > button {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 2px solid #6366f1 !important;
        background-color: transparent !important;
        color: #f8fafc !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #6366f1 !important;
        box-shadow: 0 0 25px rgba(99, 102, 241, 0.6) !important;
        transform: scale(1.02);
    }

    div.stButton > button:active, div.stDownloadButton > button:active {
        transform: scale(0.95);
        filter: brightness(1.2);
    }

    /* 3. Кастомный стиль для полей ввода (чтобы светились при фокусе) */
    input, textarea, select {
        transition: border 0.3s ease, box-shadow 0.3s ease !important;
    }
    input:focus, textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.3) !important;
    }

    /* 4. Анимация боковой панели */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #6366f1;
        transition: all 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

THICK_LINE = "<hr style='border: 2px solid #6366f1; margin: 25px 0; opacity: 1;'>"

# Сайдбар с иконками
st.sidebar.title("💎 AI NAVIGATOR")
mode = st.sidebar.radio(
    "Выберите раздел:",
    ["📝 Заполнить опрос", "📊 Панель аналитики"],
    captions=["Режим респондента", "Режим администратора"]
)

COLUMN_NAMES = {
    "age": "Возраст", "occupation": "Род занятий", "frequency": "Частота",
    "platforms": "Платформы", "purpose": "Задачи", "accuracy": "Точность",
    "convenience": "Удобство", "trust": "Доверие", "issues": "Проблемы",
    "productivity": "Продуктивность", "pay_ready": "Оплата",
    "future_sphere": "Будущее", "comment": "Отзыв", "timestamp": "Дата"
}

if mode == "📝 Заполнить опрос":
    st.title("Глобальный опрос: Роль ИИ 🚀")

    with st.form("survey_form", clear_on_submit=True):
        st.subheader("Раздел 1: Профиль")
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("1. Возраст:", 14, 80, 20)
            occupation = st.selectbox("2. Род занятий:", ["Студент", "IT", "Другое", "Не работаю"])
            frequency = st.radio("3. Частота использования:", ["Каждый день", "Несколько раз в неделю", "Редко"])
        with c2:
            platforms = st.multiselect("4. Платформы:", ["ChatGPT", "Claude", "Gemini", "YandexGPT", "GigaChat"])
            purpose = st.multiselect("5. Задачи:", ["Учёба", "Поиск", "Код", "Тексты", "Развлечение"])

        st.markdown(THICK_LINE, unsafe_allow_html=True)
        st.subheader("Раздел 2: Оценка опыта")
        c3, c4 = st.columns(2)
        with c3:
            accuracy = st.slider("6. Точность ИИ (1-10):", 1, 10, 5)
            convenience = st.slider("7. Удобство (1-10):", 1, 10, 5)
        with c4:
            trust = st.selectbox("8. Уровень доверия:", ["Верю всему", "Перепроверяю важное", "Не верю"])
            productivity = st.radio("9. Влияние на продуктивность:", ["Растет", "Немного растет", "Не влияет"])

        st.markdown(THICK_LINE, unsafe_allow_html=True)
        comment = st.text_area("10. Ваш развернутый отзыв:")

        submitted = st.form_submit_button("ОТПРАВИТЬ АНКЕТУ В ОБЛАКО")

        if submitted:
            # Анимация обработки
            with st.spinner('Синхронизация с нейросетью...'):
                doc_data = {
                    "age": int(age), "occupation": occupation, "frequency": frequency,
                    "platforms": platforms, "purpose": purpose, "accuracy": int(accuracy),
                    "convenience": int(convenience), "trust": trust, "productivity": productivity,
                    "comment": comment, "timestamp": datetime.utcnow()
                }
                db.collection("responses").add(doc_data)
                time.sleep(1)  # Короткая пауза для визуального эффекта

            # ЭФФЕКТНАЯ АНИМАЦИЯ УСПЕХА
            st.balloons()
            st.toast('Данные успешно доставлены в Firebase!', icon='✅')

elif mode == "📊 Панель аналитики":
    st.title("Центр стратегической аналитики ⚡")

    docs = db.collection("responses").stream()
    data = [doc.to_dict() for doc in docs]

    if not data:
        st.info("База данных пока пуста.")
    else:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
        df_russian = df.rename(columns=COLUMN_NAMES)

        # KPI Метрики с анимацией цифр (автоматически встроено в Streamlit)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Респонденты", len(df), "+1")
        m2.metric("Средний возраст", round(df['age'].mean(), 1))
        m3.metric("Точность ответов", f"{round(df['accuracy'].mean(), 1)}/10")
        m4.metric("Юзабилити", f"{round(df['convenience'].mean(), 1)}/10")

        st.markdown(THICK_LINE, unsafe_allow_html=True)

        # БЛОК ЭКСПОРТА
        st.subheader("📥 Выгрузка отчетов")
        exp_col1, exp_col2 = st.columns(2)

        with exp_col1:
            csv = df_russian.to_csv(index=False).encode('utf-8-sig')
            if st.download_button("📂 Экспорт в CSV", csv, "report.csv", "text/csv", use_container_width=True):
                st.snow()  # Анимация при нажатии

        with exp_col2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                df_russian.to_excel(w, index=False)
            if st.download_button("📉 Экспорт в EXCEL", buf.getvalue(), "report.xlsx", use_container_width=True):
                st.snow()  # Анимация при нажатии

        st.markdown(THICK_LINE, unsafe_allow_html=True)
        st.subheader("Сводная таблица")
        st.dataframe(df_russian.head(10), use_container_width=True)

        # Графики
        st.subheader("Визуализация")
        c_left, c_right = st.columns(2)
        with c_left:
            fig1 = px.histogram(df, x="accuracy", title="Распределение точности", color_discrete_sequence=['#38bdf8'])
            fig1.update_layout(plot_bgcolor='#1e293b', paper_bgcolor='#1e293b', font_color='#f8fafc')
            st.plotly_chart(fig1, use_container_width=True)
        with c_right:
            fig2 = px.pie(df, names="trust", title="Уровень доверия", hole=0.4,
                          color_discrete_sequence=['#6366f1', '#f472b6', '#34d399'])
            fig2.update_layout(paper_bgcolor='#1e293b', font_color='#f8fafc')
            st.plotly_chart(fig2, use_container_width=True)
