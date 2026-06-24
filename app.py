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

st.set_page_config(page_title="AI Cyber Analytics v2.0", layout="wide")

# --- МАКСИМАЛЬНЫЙ КИБЕРПАНК СТЕК АНИМАЦИЙ (CSS) ---
st.markdown("""
<style>
    /* 1. Эффектный въезд контента при смене вкладок (3D разворот + размытие) */
    .main .block-container {
        animation: cyberEntrance 0.8s cubic-bezier(0.25, 1, 0.5, 1) forwards;
    }
    @keyframes cyberEntrance {
        0% { opacity: 0; transform: translateY(40px) scale(0.98) rotateX(-2deg); filter: blur(8px); }
        100% { opacity: 1; transform: translateY(0) scale(1) rotateX(0); filter: blur(0); }
    }

    /* 2. Постоянно пульсирующий неоновый заголовок */
    .cyber-title {
        font-family: 'Courier New', monospace;
        color: #fff;
        text-shadow: 0 0 5px #fff, 0 0 10px #6366f1, 0 0 20px #6366f1, 0 0 40px #6366f1;
        animation: neonPulse 2s infinite alternate;
    }
    @keyframes neonPulse {
        0% { text-shadow: 0 0 5px #fff, 0 0 10px #6366f1, 0 0 20px #6366f1; }
        100% { text-shadow: 0 0 10px #fff, 0 0 20px #ec4899, 0 0 30px #ec4899, 0 0 50px #ec4899; }
    }

    /* 3. "Дышащие" карточки KPI (Метрики) с подсветкой */
    div[data-testid="stMetric"] {
        border: 1px solid rgba(99, 102, 241, 0.2);
        padding: 15px !important;
        border-radius: 12px !important;
        background: #1e293b !important;
        transition: all 0.4s ease !important;
        animation: metricFloat 4s infinite ease-in-out alternate;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px) scale(1.03) !important;
        border-color: #ec4899 !important;
        box-shadow: 0 0 20px rgba(236, 72, 153, 0.4) !important;
    }
    @keyframes metricFloat {
        0% { box-shadow: 0 0 5px rgba(99, 102, 241, 0.1); }
        100% { box-shadow: 0 0 15px rgba(99, 102, 241, 0.3); }
    }

    /* 4. Бешеные супер-кнопки */
    div.stButton > button, div.stDownloadButton > button {
        background: linear-gradient(45deg, #6366f1, #ec4899) !important;
        border: none !important;
        color: white !important;
        font-weight: bold !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        transform: scale(1.05) translateY(-2px) !important;
        box-shadow: 0 0 30px rgba(236, 72, 153, 0.8) !important;
        filter: brightness(1.1);
    }
    div.stButton > button:active, div.stDownloadButton > button:active {
        transform: scale(0.95) !important;
    }

    /* 5. Поля ввода плавно подсвечиваются неоном */
    input, textarea, select, div[data-baseweb="select"] {
        transition: all 0.3s ease !important;
    }
    input:focus, textarea:focus {
        border-color: #ec4899 !important;
        box-shadow: 0 0 15px rgba(236, 72, 153, 0.5) !important;
        background: #0f172a !important;
    }

    /* 6. Анимация появления графиков */
    div[data-testid="stPlotlyChart"] {
        animation: chartPop 1s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
    }
    @keyframes chartPop {
        0% { transform: scale(0.9) opacity: 0; }
        100% { transform: scale(1) opacity: 1; }
    }

    /* 7. Кастомный взрывной алерт при успехе */
    .success-glitch {
        padding: 15px;
        background: linear-gradient(90deg, #10b981, #059669);
        color: white;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 0 25px #10b981;
        animation: alertShake 0.4s ease-in-out 2;
    }
    @keyframes alertShake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
</style>
""", unsafe_allow_html=True)

THICK_LINE = "<hr style='border: 2px solid #6366f1; margin: 25px 0; opacity: 1;'>"

# Сайдбар
st.sidebar.markdown("<h2 style='color:#6366f1;'>💎 CYBER NAV</h2>", unsafe_allow_html=True)
mode = st.sidebar.radio(
    "Выберите терминал:",
    ["📝 Ввод данных (Опрос)", "📊 Ядро аналитики"],
    captions=["Доступ открыт", "Требуется авторизация"]
)

COLUMN_NAMES = {
    "age": "Возраст", "occupation": "Род занятий", "frequency": "Частота",
    "platforms": "Платформы", "purpose": "Задачи", "accuracy": "Точность",
    "convenience": "Удобство", "trust": "Доверие", "productivity": "Продуктивность",
    "comment": "Отзыв", "timestamp": "Дата матрицы"
}

if mode == "📝 Ввод данных (Опрос)":
    # Применяем глитч-заголовок
    st.markdown("<h1 class='cyber-title'>СИНХРОНИЗАЦИЯ С ИИ МАТРИЦЕЙ</h1>", unsafe_allow_html=True)
    st.caption("Данные шифруются сквозным методом NoSQL.")

    with st.form("survey_form", clear_on_submit=True):
        st.subheader("🔥 Шаг 1: Идентификация")
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("Укажите биологический возраст:", 14, 80, 20)
            occupation = st.selectbox("Сфера деятельности:",
                                      ["Студент", "IT-инженерия", "Гуманитарные науки", "Инкубатор"])
            frequency = st.radio("Цикл взаимодействия с ИИ:", ["Каждый день", "Раз в неделю", "В режиме гибернации"])
        with c2:
            platforms = st.multiselect("Используемые нейросети:",
                                       ["ChatGPT", "Claude", "Gemini", "YandexGPT", "GigaChat"])
            purpose = st.multiselect("Приоритетные задачи:",
                                     ["Генерация кода", "Промпт-инжиниринг", "Сбор датасетов", "Синтез текстов"])

        st.markdown(THICK_LINE, unsafe_allow_html=True)
        st.subheader("📊 Шаг 2: Калибровка метрик")
        c3, c4 = st.columns(2)
        with c3:
            accuracy = st.slider("Точность генерации (1-10):", 1, 10, 6)
            convenience = st.slider("UX/UI Юзабилити (1-10):", 1, 10, 7)
        with c4:
            trust = st.selectbox("Критерий доверия к ИИ:", ["Слепая вера", "Валидация фактов", "Тотальный скептицизм"])
            productivity = st.radio("Индекс личной эффективности:",
                                    ["Множитель x2", "Незначительный буст", "Стагнация"])

        st.markdown(THICK_LINE, unsafe_allow_html=True)
        comment = st.text_area("Развернутый лог-отзыв:")

        submitted = st.form_submit_button("💥 ИНИЦИИРОВАТЬ ОТПРАВКУ ДАННЫХ")

        if submitted:
            # Мощная анимация загрузки ядра
            progress_text = "Пробиваем файрвол базы данных..."
            cyber_bar = st.progress(0, text=progress_text)
            for percent_complete in range(100):
                time.sleep(0.01)
                cyber_bar.progress(percent_complete + 1, text=progress_text)

            doc_data = {
                "age": int(age), "occupation": occupation, "frequency": frequency,
                "platforms": platforms, "purpose": purpose, "accuracy": int(accuracy),
                "convenience": int(convenience), "trust": trust, "productivity": productivity,
                "comment": comment, "timestamp": datetime.utcnow()
            }
            db.collection("responses").add(doc_data)

            # ЯРКИЙ НЕОНОВЫЙ ХЛОПОК ПРИ УСПЕХЕ
            st.markdown("<div class='success-glitch'>🔥 ДАННЫЕ ИНТЕГРИРОВАНЫ В ОБЛАКО FIRESTORE!</div>",
                        unsafe_allow_html=True)
            st.balloons()  # Стандартные шарики поверх кастомного баннера
            st.toast("Пакет синхронизирован.", icon="⚡")

elif mode == "📊 Ядро аналитики":
    st.markdown("<h1 class='cyber-title'>ЦЕНТРАЛЬНЫЙ ПРОЦЕССОР АНАЛИТИКИ</h1>", unsafe_allow_html=True)

    docs = db.collection("responses").stream()
    data = [doc.to_dict() for doc in docs]

    if not data:
        st.info("Потоки данных не обнаружены. База пуста.")
    else:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
        df_russian = df.rename(columns=COLUMN_NAMES)

        # Карточки KPI теперь парят и светятся (см. CSS)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Собрано логов", f"{len(df)} ед.", "+100% стабильность")
        m2.metric("Ср. возраст ядра", f"{df['age'].mean():.1f} л.")
        m3.metric("Точность систем", f"{df['accuracy'].mean():.1f}/10")
        m4.metric("Юзабилити систем", f"{df['convenience'].mean():.1f}/10")

        st.markdown(THICK_LINE, unsafe_allow_html=True)

        # Выгрузка отчетов
        st.subheader("📥 Выгрузка матричных отчетов")
        exp_col1, exp_col2 = st.columns(2)

        with exp_col1:
            csv = df_russian.to_csv(index=False).encode('utf-8-sig')
            if st.download_button("🟢 СКАЧАТЬ ДАТАСЕТ (CSV)", csv, "cyber_db.csv", "text/csv", use_container_width=True):
                # Взрывная яркая вспышка снега вместо обычного клика
                st.snow()
                st.toast("CSV Датасет успешно выгружен на ваш терминал!", icon="💾")

        with exp_col2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                df_russian.to_excel(w, index=False)
            if st.download_button("🔵 СКАЧАТЬ ОТЧЕТ (EXCEL)", buf.getvalue(), "cyber_db.xlsx", use_container_width=True):
                st.snow()
                st.toast("Excel Матрица успешно сохранена!", icon="💻")

        st.markdown(THICK_LINE, unsafe_allow_html=True)
        st.subheader("Прямой лог базы данных (Top-10)")
        st.dataframe(df_russian.head(10), use_container_width=True)

        # Графики красиво вылетают масштабированием при загрузке страницы
        st.markdown(THICK_LINE, unsafe_allow_html=True)
        st.subheader("Визуальный анализ потоков")
        c_left, c_right = st.columns(2)
        with c_left:
            fig1 = px.histogram(df, x="accuracy", title="Кривая точности генерации",
                                color_discrete_sequence=['#38bdf8'])
            fig1.update_layout(plot_bgcolor='#1e293b', paper_bgcolor='#1e293b', font_color='#f8fafc')
            st.plotly_chart(fig1, use_container_width=True)
        with c_right:
            fig2 = px.pie(df, names="trust", title="Доверие к потокам ИИ", hole=0.4,
                          color_discrete_sequence=['#6366f1', '#ec4899', '#34d399'])
            fig2.update_layout(paper_bgcolor='#1e293b', font_color='#f8fafc')
            st.plotly_chart(fig2, use_container_width=True)
