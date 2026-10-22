
import streamlit as st
import requests
from datetime import date

st.set_page_config(page_title="Football Predictor", page_icon="⚽", layout="wide")

BASE_URL = "https://v3.football.api-sports.io"

st.title("⚽ Football Predictor")
st.caption("بيانات المباريات والتوقعات من API-Football")

# API key stays in Streamlit Secrets
try:
    API_KEY = st.secrets["API_FOOTBALL_KEY"]
except Exception:
    st.error("خاصك تزيد API_FOOTBALL_KEY فـ Streamlit → Settings → Secrets.")
    st.stop()


@st.cache_data(ttl=600)
def api_get(endpoint, params, api_key):
    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        headers={"x-apisports-key": api_key},
        params=params,
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("errors"):
        raise ValueError(str(data["errors"]))

    return data.get("response", []), data.get("results", 0)


def show_api_error(error):
    st.warning(
        "ما قدرناش نجيبو هاد البيانات. ممكن تكون غير متوفرة "
        "فالبطولة أو الخطة المجانية، أو كاين مشكل فـ API Key."
    )
    with st.expander("تفاصيل الخطأ"):
        st.code(str(error))


def team_name(team):
    return team.get("name", "غير معروف")


def show_fixtures(items):
    for item in items:
        fixture = item.get("fixture", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        home = team_name(teams.get("home", {}))
        away = team_name(teams.get("away", {}))
        status = fixture.get("status", {}).get("short", "")
        gh, ga = goals.get("home"), goals.get("away")
        score = f"{gh} - {ga}" if gh is not None and ga is not None else "لم تلعب بعد"
        st.write(
            f"**{home} {score} {away}** — "
            f"{fixture.get('date', '')[:16].replace('T', ' ')} "
            f"({status})"
        )


match_date = st.date_input("اختار تاريخ المباريات", value=date.today())

st.subheader("📅 المباريات")

try:
    fixtures, total = api_get(
        "fixtures", {"date": match_date.isoformat()}, API_KEY
    )

    if not fixtures:
        st.info("ما لقيناش مباريات فهاد التاريخ حسب البيانات المتاحة.")
    else:
        options = {}
        for item in fixtures:
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            home = team_name(teams.get("home", {}))
            away = team_name(teams.get("away", {}))
            league = item.get("league", {}).get("name", "")
            kickoff = fixture.get("date", "")[:16].replace("T", " ")
            label = f"{home} - {away} | {league} | {kickoff}"
            options[label] = fixture.get("id")

        selected_label = st.selectbox("اختار الماتش", list(options.keys()))
        fixture_id = options[selected_label]

        selected = next(
            item for item in fixtures
            if item.get("fixture", {}).get("id") == fixture_id
        )

        st.divider()
        teams = selected.get("teams", {})
        home_team = teams.get("home", {})
        away_team = teams.get("away", {})
        home_id = home_team.get("id")
        away_id = away_team.get("id")

        left, right = st.columns(2)
        left.metric("الفريق الأول", team_name(home_team))
        right.metric("الفريق الثاني", team_name(away_team))

        tabs = st.tabs([
            "الإحصائيات",
            "التشكيلة",
            "النتائج السابقة",
            "التوقعات",
        ])

        with tabs[0]:
            st.subheader("إحصائيات الماتش")
            if selected.get("fixture", {}).get("status", {}).get("short") in [
                "NS", "TBD"
            ]:
                st.info("الإحصائيات كتكون غالباً متاحة من بعد بداية الماتش.")
            if st.button("جيب الإحصائيات", key="stats"):
                try:
                    rows, _ = api_get(
                        "fixtures/statistics",
                        {"fixture": fixture_id},
                        API_KEY,
                    )
                    if not rows:
                        st.info("الإحصائيات مازال ما متوفراش لهاد الماتش.")
                    else:
                        for row in rows:
                            st.markdown(
                                f"**{team_name(row.get('team', {}))}**"
                            )
                            st.dataframe(
                                [
                                    {
                                        "الإحصائية": x.get("type"),
                                        "القيمة": x.get("value"),
                                    }
                                    for x in row.get("statistics", [])
                                ],
                                use_container_width=True,
                                hide_index=True,
                            )
                except Exception as e:
                    show_api_error(e)

        with tabs[1]:
            st.subheader("التشكيلة الرسمية")
            if st.button("جيب التشكيلة", key="lineups"):
                try:
                    rows, _ = api_get(
                        "fixtures/lineups",
                        {"fixture": fixture_id},
                        API_KEY,
                    )
                    if not rows:
                        st.info("التشكيلة مازال ما تعلناتش أو غير متوفرة.")
                    for row in rows:
                        st.markdown(
                            f"### {team_name(row.get('team', {}))}"
                        )
                        st.write("الخطة:", row.get("formation") or "غير متاحة")
                        st.write("المدرب:", (row.get("coach") or {}).get("name", "غير متاح"))
                        players = row.get("startXI", [])
                        if players:
                            st.dataframe(
                                [
                                    {
                                        "اللاعب": (p.get("player") or {}).get("name"),
                                        "الرقم": (p.get("player") or {}).get("number"),
                                        "المركز": (p.get("player") or {}).get("pos"),
                                    }
                                    for p in players
                                ],
                                use_container_width=True,
                                hide_index=True,
                            )
                        st.write(
                            "الاحتياط:",
                            ", ".join(
                                (p.get("player") or {}).get("name", "")
                                for p in row.get("substitutes", [])
                            ) or "غير متاح",
                        )
                except Exception as e:
                    show_api_error(e)

        with tabs[2]:
            st.subheader("آخر 5 مباريات لكل فريق")
            if st.button("جيب النتائج السابقة", key="history"):
                for tid, name in [
                    (home_id, team_name(home_team)),
                    (away_id, team_name(away_team)),
                ]:
                    st.markdown(f"### {name}")
                    try:
                        history, _ = api_get(
                            "fixtures",
                            {"team": tid, "last": 5},
                            API_KEY,
                        )
                        if history:
                            show_fixtures(history)
                        else:
                            st.info("ما كايناش نتائج متاحة.")
                    except Exception as e:
                        show_api_error(e)

        with tabs[3]:
            st.subheader("توقعات الماتش")
            st.caption(
                "التوقعات من المزود إذا كانت متاحة. ماشي ضمان للنتيجة."
            )
            if st.button("جيب التوقعات", key="predictions"):
                try:
                    rows, _ = api_get(
                        "predictions",
                        {"fixture": fixture_id},
                        API_KEY,
                    )
                    if not rows:
                        st.info("التوقعات غير متاحة لهاد الماتش أو الخطة.")
                    else:
                        for row in rows:
                            pred = row.get("predictions", {})
                            teams_pred = pred.get("teams", {})
                            st.write("الفائز المتوقع:", (pred.get("winner") or {}).get("name", "غير محدد"))
                            st.write("نسبة الفوز:", pred.get("percent", {}))
                            st.write("الأهداف المتوقعة:", pred.get("goals", {}))
                            st.write("نصيحة المزود:", pred.get("advice", "غير متاحة"))
                            st.write("معلومات إضافية:", teams_pred)
                            st.write(
                                "xG: ما نعرضوهش إلا إذا رجع من مصدر موثوق "
                                "وبحقل واضح؛ ماشي كل API كيوفره."
                            )
                except Exception as e:
                    show_api_error(e)

except requests.HTTPError as e:
    show_api_error(e)
except Exception as e:
    show_api_error(e)

st.divider()
st.caption(
    "المعلومات كتختلف حسب البطولة والخطة. البيانات الناقصة ما كنعتابروهاش صفر، "
    "والتوقعات احتمالات وليست نتائج مضمونة."
)
