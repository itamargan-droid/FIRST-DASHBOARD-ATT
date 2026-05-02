import streamlit as st

def check_password():
    """מחזירה True אם המשתמש הקיש סיסמה נכונה."""
    if "password_correct" not in st.session_state:
        # מציג תיבת טקסט להזנת סיסמה
        st.text_input("הזן קוד גישה לצפייה בנתונים:", type="password", key="password")
        if st.button("כניסה"):
            if st.session_state["password"] == "12345": # כאן תקבע את הקוד שלך
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ קוד שגוי")
        return False
    else:
        return True

# אם הסיסמה לא נכונה, עוצרים כאן ולא מציגים את שאר הדאשבורד
if not check_password():
    st.stop()

# --- מכאן והלאה מגיע שאר הקוד של הדאשבורד שלך ---
st.success("גישה אושרה!")


import streamlit as st
import pandas as pd
import plotly.express as px

# 1. הגדרות דף
st.set_page_config(page_title="Patient Analytics - Purple & Yellow Edition", layout="wide")

# 2. CSS מודרני עם דגש על הצבעים שביקשת
st.markdown("""
    <style>
    /* רקע האתר */
    .stApp {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
    }
    
    /* עיצוב כרטיסיות המדדים - צבע סגלגל כברירת מחדל */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-bottom: 4px solid #9B59B6; /* קו סגלגל למטה */
    }

    /* כותרות */
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Segoe UI', sans-serif;
    }

    /* התאמת ה-Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
    }

    /* עיצוב טאבים */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. מפת צבעים (סגלגל וצהוב)
custom_colors = {
    "LECA": "#9B59B6", # סגלגל (Amethyst)
    "DONA": "#F1C40F"  # צהוב (Sunflower)
}

# 4. פונקציית טעינת נתונים
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("נסיון.xlsx")
        df['תרופה'] = df['תרופה'].str.strip()
        return df
    except Exception as e:
        st.error(f"לא נמצא קובץ אקסל: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- כותרת ראשית ---
    st.title("📊 דשבורד מעקב מטופלים")
    st.markdown("---")

    # --- סרגל צדי (Filters) ---
    with st.sidebar:
        st.header("מסננים")
        selected_drug = st.multiselect("בחר תרופה:", options=df['תרופה'].unique(), default=list(df['תרופה'].unique()))
        selected_aria = st.selectbox("סטטוס ARIA:", ["הכל"] + list(df['האם ARIA'].unique()))

    # פילטור
    mask = df['תרופה'].isin(selected_drug)
    if selected_aria != "הכל":
        mask &= (df['האם ARIA'] == selected_aria)
    
    filtered_df = df[mask]

    # --- מדדים (KPIs) ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("סה\"כ מטופלים", len(filtered_df))
    with m2:
        val = round(filtered_df['גיל'].mean(), 1) if not filtered_df.empty else 0
        st.metric("גיל ממוצע", val)
    with m3:
        aria_yes = len(filtered_df[filtered_df['האם ARIA'] == 'כן'])
        st.metric("מקרים של ARIA", aria_yes)
    with m4:
        react_yes = len(filtered_df[filtered_df['האם תגובה לעירוי'] == 'כן'])
        st.metric("תגובה לעירוי", react_yes)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- טאבים לתצוגה ---
    tab_charts, tab_table = st.tabs(["📈 ניתוח גרפי", "📄 נתונים גולמיים"])

    with tab_charts:
        c1, c2 = st.columns(2)
        
        with c1:
            # היסטוגרמה בצבעי המותג
            fig_age = px.histogram(
                filtered_df, 
                x="גיל", 
                color="תרופה",
                color_discrete_map=custom_colors,
                title="התפלגות גילאים",
                barmode="group",
                template="plotly_white"
            )
            st.plotly_chart(fig_age, use_container_width=True)

        with c2:
            # גרף עוגה (דונאט)
            fig_pie = px.pie(
                filtered_df, 
                names="תרופה", 
                hole=0.5,
                color="תרופה",
                color_discrete_map=custom_colors,
                title="התפלגות תרופות במדגם"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab_table:
        st.subheader("📋 נתוני מטופלים מפורטים")
        st.dataframe(filtered_df, use_container_width=True)

else:
    st.warning("הקוד מוכן, אך חסר קובץ הנתונים 'נסיון.xlsx' בתיקייה.")

# פוטר
st.markdown("---")
st.caption("מערכת ניטור קלינית - מבוסס סגלגל וצהוב")