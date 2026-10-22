
import streamlit as st
import pandas as pd
import math

st.set_page_config(
    page_title="Football Predictor",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Football Predictor")
st.write("أداة لتحليل مباريات كرة القدم وتقدير النتائج المحتملة.")
st.warning("هاد النسخة أولية: الحسابات مبنية على المعطيات اللي كتدخل، وماشي بيانات مباشرة من Sofascore.")

st.header("🏟️ معلومات المباراة")

col1, col2 = st.columns(2)

with col1:
    home = st.text_input("الفريق المستضيف", "Real Madrid")
    home_goals = st.number_input("معدل أهداف المستضيف فالمباراة", 0.0, 10.0, 1.8, 0.1)
    home_conceded = st.number_input("معدل الأهداف اللي كيتلقى", 0.0, 10.0, 0.9, 0.1)

with col2:
    away = st.text_input("الفريق الضيف", "Barcelona")
    away_goals = st.number_input("معدل أهداف الضيف فالمباراة", 0.0, 10.0, 1.4, 0.1)
    away_conceded = st.number_input("معدل الأهداف اللي كيتلقى الضيف", 0.0, 10.0, 1.1, 0.1)

if st.button("حلل المباراة", type="primary"):
    if not home.strip() or not away.strip():
        st.error("دخل اسم الفريقين.")
    else:
        expected_home = (home_goals + away_conceded) / 2
        expected_away = (away_goals + home_conceded) / 2

        def poisson(k, lam):
            return (math.exp(-lam) * lam**k) / math.factorial(k)

        home_win = draw = away_win = 0.0
        scores = []

        for h in range(8):
            for a in range(8):
                p = poisson(h, expected_home) * poisson(a, expected_away)
                scores.append((p, h, a))
                if h > a:
                    home_win += p
                elif h == a:
                    draw += p
                else:
                    away_win += p

        total = home_win + draw + away_win
        home_win, draw, away_win = [
            p / total * 100 for p in (home_win, draw, away_win)
        ]

        st.subheader(f"{home} ضد {away}")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"فوز {home}", f"{home_win:.1f}%")
        c2.metric("التعادل", f"{draw:.1f}%")
        c3.metric(f"فوز {away}", f"{away_win:.1f}%")

        best = max(scores, key=lambda x: x[0])
        st.metric("النتيجة الدقيقة الأكثر احتمالاً حسب النموذج",
                  f"{best[1]} - {best[2]}")

        st.write(f"الأهداف المتوقعة: {home} **{expected_home:.2f}** — **{expected_away:.2f}** {away}")
        st.caption("التوقعات تقريبية وتعتمد على الأرقام المدخلة، وليست ضماناً لنتيجة المباراة.")
