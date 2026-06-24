import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.express as px
import streamlit as st

# Инициализация подключения к базе данных Firebase
# --- Инициализация Firebase (Умная версия для Cloud и Локалки) ---
import json # <--- Добавь эту строку в самые верхние импорты, если её там нет!

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

st.set_page_config(page_title="Мониторинг: Чат-боты и ИИ", layout="wide")

mode = st.sidebar.radio("Выберите режим:", ["Заполнить опрос", "Панель аналитики (Преподаватель)"])

# Перевод названий колонок для таблицы аналитики
COLUMN_NAMES = {
    "age": "Возраст",
    "occupation": "Род занятий",
    "frequency": "Частота использования",
    "platforms": "Популярные платформы",
    "purpose": "Цели использования",
    "accuracy": "Оценка точности",
    "convenience": "Оценка удобства",
    "trust": "Уровень доверия",
    "issues": "Проблемы и недостатки",
    "comment": "Отзыв / Комментарий",
    "timestamp": "Время отправки"
}

# Режим заполнения анкеты респондентом (10 пунктов)
if mode == "Заполнить опрос":
    st.title("Опрос: Использование чат-ботов и ИИ-помощников")
    st.caption("Данные собираются анонимно исключительно в учебных целях.")

    with st.form("survey_form"):
        st.subheader("Профиль респондента")
        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("1. Укажите ваш возраст:", min_value=14, max_value=80, value=20, step=1)

            occupation = st.selectbox(
                "2. Ваш основной rod занятий:",
                ["Школьник / Студент", "Работаю в сфере IT", "Работаю в другой сфере", "Временно не работаю"]
            )

            frequency = st.radio(
                "3. Как часто вы общаетесь с чат-ботами?",
                ["Каждый день", "Несколько раз в неделю", "Редко (раз в месяц и реже)", "Никогда не пользовался"]
            )

        with col2:
            platforms = st.multiselect(
                "4. Какими ИИ-помощниками вы пользуетесь? (допускается множественный выбор):",
                ["ChatGPT / ИИ от OpenAI", "Claude (Anthropic)", "Gemini (Google)", "YandexGPT / Шедеврум",
                 "GigaChat (Сбер)", "Другие боты в Telegram"]
            )

            purpose = st.multiselect(
                "5. Для каких задач вы их применяете?:",
                ["Помощь в учёбе / написание эссе", "Поиск информации вместо поисковых систем",
                 "Написание и проверка программного кода", "Генерация идей и текстов", "Развлечение и ведение диалога"]
            )

        st.markdown("---")
        st.subheader("Оценка опыта взаимодействия (Метрики темы)")

        col3, col4 = st.columns(2)
        with col3:
            accuracy = st.slider("6. Оцените точность и правильность ответов ИИ (1-10):", 1, 10, 5)
            convenience = st.slider("7. Оцените удобство работы и интерфейса (1-10):", 1, 10, 5)

        with col4:
            trust = st.selectbox(
                "8. Каков ваш уровень доверия к выданным ИИ фактам?",
                ["Слепо верю всему, что пишет бот", "Перепроверяю только важные факты",
                 "Почти не верю, всегда проверяю в надежных источниках"]
            )

            issues = st.multiselect(
                "9. С какими главными недостатками вы сталкивались?:",
                ["Бот выдумывает факты (галлюцинации)", "Слишком шаблонизированные или скучные ответы",
                 "Частые сбои связи или медленная работа", "Сложный интерфейс", "Не сталкивался с проблемами"]
            )

        st.markdown("---")
        comment = st.text_area("10. Ваш главный плюс или минус нейросетей (развернутый отзыв):")

        submitted = st.form_submit_button("Отправить результаты")

        if submitted:
            if not platforms or not purpose:
                st.warning("Пожалуйста, заполните обязательные пункты 4 и 5.")
            else:
                doc_data = {
                    "age": int(age),
                    "occupation": occupation,
                    "frequency": frequency,
                    "platforms": platforms,
                    "purpose": purpose,
                    "accuracy": int(accuracy),
                    "convenience": int(convenience),
                    "trust": trust,
                    "issues": issues,
                    "comment": comment,
                    "timestamp": datetime.utcnow()
                }

                try:
                    db.collection("responses").add(doc_data)
                    st.success("Данные успешно сохранены в базе Firebase.")
                except Exception as e:
                    st.error(f"Ошибка отправки данных: {e}")

# Режим просмотра результатов аналитики
elif mode == "Панель аналитики (Преподаватель)":
    st.title("Панель аналитики результатов")

    docs = db.collection("responses").stream()
    data = [doc.to_dict() for doc in docs]

    if not data:
        st.info("В базе данных пока нет ответов. Заполните форму хотя бы один раз.")
    else:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        df_russian = df.rename(columns=COLUMN_NAMES)

        st.subheader("Таблица собранных ответов (Последние 10 записей)")
        st.dataframe(df_russian.head(10))

        st.subheader("Визуализация ключевых метрик")
        c1, c2 = st.columns(2)

        with c1:
            fig1 = px.histogram(
                df, x="accuracy",
                nbins=10,
                title="Распределение оценок точности чат-ботов",
                labels={"accuracy": "Оценка точности (1-10)"},
                color_discrete_sequence=['#1e293b']
            )
            fig1.update_layout(
                yaxis_title_text="Количество ответов",
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            fig2 = px.histogram(
                df, x="convenience",
                nbins=10,
                title="Распределение оценок удобства интерфейса",
                labels={"convenience": "Оценка удобства (1-10)"},
                color_discrete_sequence=['#475569']
            )
            fig2.update_layout(
                yaxis_title_text="Количество ответов",
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.pie(
            df, names="trust",
            title="Уровень доверия пользователей к информации от ИИ",
            hole=0.4,
            color_discrete_sequence=['#1e293b', '#475569', '#94a3b8']
        )
        fig3.update_layout(paper_bgcolor='white')
        st.plotly_chart(fig3, use_container_width=True)