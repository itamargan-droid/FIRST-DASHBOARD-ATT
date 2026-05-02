import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. הגדרות דף ---
st.set_page_config(page_title="דשבורד מוגן - מעקב מטופלים", layout="wide")

# --- 2. מנגנון סיסמה ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 כניסה למערכת מאובטחת")
        pwd = st.text_input("הזן קוד גישה:", type="password")
        if st.button("כניסה"):
            if pwd == "12345": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ קוד שגוי")
        return False
    return True

if not check_password():
    st.stop()

# --- 3. עיצוב (CSS) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); }
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-bottom: 4px solid #9B59B6;
    }
    </style>
    """, unsafe_allow_html=True)

custom_colors = {"LECA": "#9B59B6", "DONA": "#F1C40F"}

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("נסיון.xlsx")
        # ניקוי רווחים
        for col in ['תרופה', 'מין', 'האם ARIA', 'האם תגובה לעירוי']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

df = load_data()

if not df.empty:
    st.title("📊 דשבורד מעקב מטופלים")
    st.sidebar.success("✅ גישה מאובטחת אושרה")
    
    # --- סרגל צדי עם מסננים ---
    with st.sidebar:
        st.header("מסננים")
        
        # מסנן תרופה
        selected_drug = st.multiselect(
            "בחר תרופה:", 
            options=df['תרופה'].unique(), 
            default=list(df['תרופה'].unique())
        )
        
        # מסנן מין (חדש)
        selected_gender = st.multiselect(
            "בחר מין:", 
            options=df['מין'].unique(), 
            default=list(df['מין'].unique())
        )

    # פילטור הנתונים
    mask = (df['תרופה'].isin(selected_drug)) & (df['מין'].isin(selected_gender))
    filtered_df = df[mask]

    # --- מדדים (KPIs) ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("סה\"כ מטופלים", len(filtered_df))
    m2.metric("גיל ממוצע", round(filtered_df['גיל'].mean(), 1) if not filtered_df.empty else 0)
    
    aria_count = len(filtered_df[filtered_df['האם ARIA'] == 'כן'])
    m3.metric("מקרים של ARIA", aria_count)
    
    reaction_count = len(filtered_df[filtered_df['האם תגובה לעירוי'] == 'כן'])
    m4.metric("תגובה לעירוי", reaction_count)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- גרפים ---
    c1, c2 = st.columns(2)
    
    with c1:
        # גרף התפלגות גילאים עם הצגת מספרים (text_auto=True מציג את המספר מעל העמודה)
        fig_age = px.histogram(
            filtered_df, 
            x="גיל", 
            color="תרופה", 
            color_discrete_map=custom_colors, 
            title="התפלגות גילאים (מספרים אבסולוטיים)", 
            barmode="group", 
            template="plotly_white",
            text_auto=True
        )
        st.plotly_chart(fig_age, use_container_width=True)

    with c2:
        # גרף עוגה המציג גם מספר וגם אחוז
        fig_pie = px.pie(
            filtered_df, 
            names="תרופה", 
            hole=0.5, 
            color="תרופה", 
            color_discrete_map=custom_colors, 
            title="התפלגות תרופות (% ומספר אבסולוטי)"
        )
        # עדכון התצוגה של הגרף להצגת Label, Percent ו-Value
        fig_pie.update_traces(textinfo='percent+value+label', textposition='inside')
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- טבלת נתונים ---
    st.subheader("📋 נתוני מטופלים מפורטים (לפי הסינון)")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.warning("הקוד רץ, אך לא נמצא קובץ נתונים או שהקובץ ריק.")