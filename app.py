import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.express as px
import streamlit as st
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

st.set_page_config(page_title="Мониторинг: Чат-боты и ИИ", layout="wide")

# Жирные дизайнерские разделительные линии неонового цвета
THICK_LINE = "<hr style='border: 2px solid #6366f1; margin: 25px 0; opacity: 1;'>"

mode = st.sidebar.radio("Выберите режим:", ["Заполнить опрос", "Панель аналитики (Преподаватель)"])

# Маппинг всех 13 полей для таблицы
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
    "productivity": "Влияние на продуктивность",
    "pay_ready": "Готовность платить",
    "future_sphere": "Сфера ИИ в будущем",
    "comment": "Развернутый отзыв",
    "timestamp": "Время отправки"
}

if mode == "Заполнить опрос":
    st.title("Глобальный опрос: Роль ИИ в современном обществе")
    st.caption("Исследование проводится анонимно. Время заполнения: ~3 минуты.")

    with st.form("survey_form"):
        st.subheader("Раздел 1: Профиль респондента")
        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("1. Укажите ваш возраст:", min_value=14, max_value=80, value=20, step=1)
            occupation = st.selectbox(
                "2. Ваш основной род занятий:",
                ["Школьник / Студент", "Работаю в сфере IT", "Работаю в другой сфере", "Временно не работаю"]
            )
            frequency = st.radio(
                "3. Как часто вы общаетесь с ИИ-помощниками?",
                ["Каждый день", "Несколько раз в неделю", "Редко (раз в месяц и реже)", "Никогда не пользовался"]
            )

        with col2:
            platforms = st.multiselect(
                "4. Какими платформами вы пользуетесь? (множественный выбор):",
                ["ChatGPT / OpenAI", "Claude (Anthropic)", "Gemini (Google)", "YandexGPT / Шедеврум", "GigaChat (Сбер)",
                 "Telegram-боты"]
            )
            purpose = st.multiselect(
                "5. Для каких ключевых задач вы их применяете?:",
                ["Помощь в учёбе / эссе", "Поиск информации", "Написание / проверка кода", "Генерация текстов и идей",
                 "Развлечение и общение"]
            )

        st.markdown(THICK_LINE, unsafe_allow_html=True)
        st.subheader("Раздел 2: Опыт и метрики взаимодействия")

        col3, col4 = st.columns(2)
        with col3:
            accuracy = st.slider("6. Оцените точность ответы ИИ (1-10):", 1, 10, 5)
            convenience = st.slider("7. Оцените удобство интерфейсов (1-10):", 1, 10, 5)
            trust = st.selectbox(
                "8. Ваш уровень доверия к фактам от ИИ:",
                ["Слепо верю всему", "Перепроверяю только важные факты", "Никогда не верю на слово"]
            )

        with col4:
            issues = st.multiselect(
                "9. С какими главными минусами вы сталкивались?:",
                ["Галлюцинации (выдумка фактов)", "Шаблонные/скучные ответы", "Медленная работа / сбои",
                 "Сложный интерфейс", "Нет проблем"]
            )
            productivity = st.radio(
                "10. Как использование ИИ влияет на вашу личную продуктивность?",
                ["Значительно повышает", "Немного повышает", "Не влияет", "Замедляет мою работу"]
            )

        st.markdown(THICK_LINE, unsafe_allow_html=True)
        st.subheader("Раздел 3: Экономика и будущее технологий")
        col5, col6 = st.columns(2)

        with col5:
            pay_ready = st.radio(
                "11. Готовы ли вы оплачивать платную подписку на ИИ (для работы или учебы)?:",
                ["Да, готов при необходимости", "Нет, принципиально ищу бесплатные", "Уже оплачиваю подписку"]
            )
        with col6:
            future_sphere = st.selectbox(
                "12. В какой сфере, по вашему мнению, ИИ принесет наибольшую пользу в ближайшие 5 лет?:",
                ["Медицина и диагностика", "Образование и репетиторство", "Наука и новые открытия",
                 "Автоматизация рутины", "Искусство и дизайн"]
            )

        st.markdown(THICK_LINE, unsafe_allow_html=True)
        comment = st.text_area("13. Ваш развернутый отзыв (главный плюс или минус нейросетей из личного опыта):")

        submitted = st.form_submit_button("Отправить анкету в базу")

        if submitted:
            if not platforms or not purpose:
                st.warning("Пожалуйста, заполните обязательные множественные списки (пункты 4 и 5).")
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
                    "productivity": productivity,
                    "pay_ready": pay_ready,
                    "future_sphere": future_sphere,
                    "comment": comment,
                    "timestamp": datetime.utcnow()
                }

                try:
                    db.collection("responses").add(doc_data)
                    st.success("Анкета успешно отправлена. Спасибо за участие!")
                except Exception as e:
                    st.error(f"Ошибка сохранения: {e}")

elif mode == "Панель аналитики (Преподаватель)":
    st.title("Центр стратегической аналитики")

    docs = db.collection("responses").stream()
    data = [doc.to_dict() for doc in docs]

    if not data:
        st.info("В базе данных Firestore пока нет ответов.")
    else:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df_russian = df.rename(columns=COLUMN_NAMES)

        st.subheader("Ключевые показатели эффективности")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(label="Всего респондентов", value=f"{len(df)} чел.")
        with m2:
            st.metric(label="Средний возраст", value=f"{df['age'].mean():.1f} лет")
        with m3:
            st.metric(label="Ср. оценка точности", value=f"{df['accuracy'].mean():.1f} / 10")
        with m4:
            st.metric(label="Ср. оценка удобства", value=f"{df['convenience'].mean():.1f} / 10")

        st.markdown(THICK_LINE, unsafe_allow_html=True)

        st.subheader("Сводная база данных")
        st.dataframe(df_russian.head(10), use_container_width=True)

        st.markdown(THICK_LINE, unsafe_allow_html=True)
        st.subheader("Визуальный анализ метрик")

        # Ряд графиков 1: Неоновый Голубой и Неоновый Розовый на темном фоне
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.histogram(
                df, x="accuracy", nbins=10,
                title="Распределение оценок точности ответов ИИ",
                labels={"accuracy": "Оценка точности"},
                color_discrete_sequence=['#38bdf8']  # Кибер-голубой
            )
            fig1.update_traces(marker_line_color='#0f172a', marker_line_width=2)
            fig1.update_layout(
                yaxis_title_text="Ответы",
                plot_bgcolor='#1e293b', paper_bgcolor='#1e293b', font_color='#f8fafc'
            )
            fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#334155', linecolor='#f8fafc', linewidth=2)
            fig1.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#334155', linecolor='#f8fafc', linewidth=2)
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            fig2 = px.histogram(
                df, x="convenience", nbins=10,
                title="Распределение оценок юзабилити интерфейсов",
                labels={"convenience": "Оценка удобства"},
                color_discrete_sequence=['#f472b6']  # Неоново-розовый
            )
            fig2.update_traces(marker_line_color='#0f172a', marker_line_width=2)
            fig2.update_layout(
                yaxis_title_text="Ответы",
                plot_bgcolor='#1e293b', paper_bgcolor='#1e293b', font_color='#f8fafc'
            )
            fig2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#334155', linecolor='#f8fafc', linewidth=2)
            fig2.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#334155', linecolor='#f8fafc', linewidth=2)
            st.plotly_chart(fig2, use_container_width=True)

        # Ряд графиков 2: Ярко-изумрудный бар-чарт и фиолетовый донат-чарт
        st.markdown(THICK_LINE, unsafe_allow_html=True)
        c3, c4 = st.columns(2)

        with c3:
            fig3 = px.bar(
                df['productivity'].value_counts().reset_index(),
                x='productivity', y='count',
                title="Как технологии влияют на продуктивность пользователей",
                labels={'productivity': 'Категория влияния', 'count': 'Количество'},
                color_discrete_sequence=['#34d399']  # Мятно-изумрудный
            )
            fig3.update_traces(marker_line_color='#0f172a', marker_line_width=2)
            fig3.update_layout(plot_bgcolor='#1e293b', paper_bgcolor='#1e293b', font_color='#f8fafc')
            fig3.update_xaxes(linecolor='#f8fafc', linewidth=2)
            fig3.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#334155', linecolor='#f8fafc', linewidth=2)
            st.plotly_chart(fig3, use_container_width=True)

        with c4:
            fig4 = px.pie(
                df, names="pay_ready",
                title="Экономический аспект: Готовность платить за ИИ",
                hole=0.4,
                color_discrete_sequence=['#c084fc', '#a78bfa', '#818cf8']  # Градиент фиолетового
            )
            fig4.update_traces(marker=dict(line=dict(color='#0f172a', width=2)))
            fig4.update_layout(paper_bgcolor='#1e293b', font_color='#f8fafc')
            st.plotly_chart(fig4, use_container_width=True)

        # Ряд графиков 3: Будущее ИИ (Яркий многоцветный пирог с темной подложкой)
        st.markdown(THICK_LINE, unsafe_allow_html=True)
        fig5 = px.pie(
            df, names="future_sphere",
            title="Какая сфера получит максимальный толчок развития от ИИ?",
            color_discrete_sequence=['#fbbf24', '#38bdf8', '#f87171', '#34d399', '#a78bfa']
        )
        fig5.update_traces(textposition='inside', textinfo='percent+label',
                           marker=dict(line=dict(color='#0f172a', width=2)))
        fig5.update_layout(paper_bgcolor='#1e293b', font_color='#f8fafc')
        st.plotly_chart(fig5, use_container_width=True)