import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. הגדרות דף ---
st.set_page_config(page_title="דשבורד מוגן - מעקב מטופלים", layout="wide")

# --- 2. מנגנון סיסמה (חייב להופיע ראשון!) ---
def check_password():
    """מחזירה True אם המשתמש הקיש סיסמה נכונה."""
    if "password_correct" not in st.session_state:
        # עיצוב דף הכניסה
        st.title("🔒 כניסה למערכת מאובטחת")
        pwd = st.text_input("הזן קוד גישה לצפייה בנתונים:", type="password")
        if st.button("כניסה"):
            # הסיסמה היא: 12345
            if pwd == "12345": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ קוד שגוי")
        return False
    return True

# עצירה כאן אם הסיסמה לא הוזנה - שום דבר מתחת לשורה הזו לא ירוץ!
if not check_password():
    st.stop()

# --- 3. אם הגענו לכאן, הסיסמה נכונה. עכשיו מריצים את העיצוב והנתונים ---

# הזרקת CSS לעיצוב מודרני בסגנון Glassmorphism (עם הרקע והעיטור הסגלגל)
st.markdown("""
    <style>
    /* רקע האתר */
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); }
    
    /* עיצוב כרטיסיות המדדים (Metrics) */
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-bottom: 4px solid #9B59B6; /* פס עיטור סגלגל */
    }
    
    /* עיצוב ה-Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
    }
    
    /* עיצוב כותרות */
    h1, h2, h3 { color: #2c3e50; font-family: 'Segoe UI', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# הגדרת צבעים מותאמת (LECA=סגלגל, DONA=צהוב)
custom_colors = {"LECA": "#9B59B6", "DONA": "#F1C40F"}

# פונקציית טעינת הנתונים מהאקסל (כולל ניקוי רווחים)
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("נסיון.xlsx")
        
        # ניקוי רווחים משדות טקסט קריטיים
        cols_to_clean = ['תרופה', 'מין', 'האם ARIA', 'האם תגובה לעירוי']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return df
    except Exception as e:
        # במקרה שאין קובץ, נחזיר DataFrame ריק ונודיע על השגיאה ב-Logs
        return pd.DataFrame()

# טעינת הנתונים בפועל
df = load_data()

# --- 4. בניית הממשק (רק אם יש נתונים) ---
if not df.empty:
    st.title("📊 דשבורד מעקב מטופלים - ניתוח נתונים")
    st.markdown("---")
    st.sidebar.success("✅ גישה מאובטחת אושרה")
    
    # --- סרגל צדי למסננים ---
    with st.sidebar:
        st.header("🛠️ מרכז סינון")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # מסנן תרופה (בחירה מרובה)
        selected_drug = st.multiselect(
            "💊 בחר תרופה:", 
            options=df['תרופה'].unique(), 
            default=list(df['תרופה'].unique())
        )
        
        # מסנן מין (בחירה מרובה - חדש)
        # וודא שיש עמודה באקסל בשם exact "מין"
        if 'מין' in df.columns:
            selected_gender = st.multiselect(
                "👤 בחר מין:", 
                options=df['מין'].unique(), 
                default=list(df['מין'].unique())
            )
        else:
            st.sidebar.error("❌ לא נמצאה עמודת 'מין' בקובץ האקסל")
            selected_gender = [] # ברירת מחדל כדי למנוע קריסה

    # פילטור הנתונים לפי הבחירות ב-Sidebar
    mask = (df['תרופה'].isin(selected_drug))
    if 'מין' in df.columns and selected_gender:
        mask &= (df['מין'].isin(selected_gender))
        
    filtered_df = df[mask]

    # --- תצוגת מדדים מרכזיים (KPIs) ---
    st.markdown("### מדדי מפתח")
    m1, m2, m3, m4 = st.columns(4)
    
    m1.metric("סה\"כ מטופלים", len(filtered_df))
    
    avg_age = round(filtered_df['גיל'].mean(), 1) if not filtered_df.empty else 0
    m2.metric("גיל ממוצע", f"{avg_age}")
    
    aria_count = len(filtered_df[filtered_df['האם ARIA'] == 'כן'])
    m3.metric("מקרים של ARIA", aria_count)
    
    reaction_count = len(filtered_df[filtered_df['האם תגובה לעירוי'] == 'כן'])
    m4.metric("תגובה לעירוי", reaction_count)

    st.markdown("<br>", unsafe_allow_html=True) # רווח עדין

    # --- תצוגת גרפים ---
    # הוספת טאבים למראה נקי יותר
    tab_graphs, tab_data = st.tabs(["📈 ניתוח ויזואלי", "📋 נתונים גולמיים"])
    
    with tab_graphs:
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("התפלגות גילאים לפי תרופה")
            # גרף היסטוגרמה עם הצגת מספרים מוחלטים (text_auto=True)
            fig_age = px.histogram(
                filtered_df, 
                x="גיל", 
                color="תרופה", 
                color_discrete_map=custom_colors, 
                title="פיזור גילאים (מספרים אבסולוטיים)", 
                barmode="group", 
                template="plotly_white",
                text_auto=True # מציג את המספר מעל העמודה
            )
            # שיפור תצוגת הטקסט מעל העמודות
            fig_age.update_traces(textposition='outside')
            st.plotly_chart(fig_age, use_container_width=True)

        with c2:
            st.subheader("נתח שוק - תרופות")
            # גרף עוגה (דונאט) המציג גם מספרים מוחלטים וגם אחוזים
            fig_pie = px.pie(
                filtered_df, 
                names="תרופה", 
                hole=0.5, 
                color="תרופה", 
                color_discrete_map=custom_colors, 
                title="התפלגות תרופות במדגם (% ומספר אבסולוטי)"
            )
            # עדכון התצוגה: מציג לייבל (שם התרופה), אחוז, ומספר מוחלט (value)
            fig_pie.update_traces(textinfo='label+percent+value', textposition='inside')
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab_data:
        st.subheader("📋 נתוני מטופלים מפורטים (מסוננים)")
        # הצגת הטבלה המלאה
        st.dataframe(filtered_df, use_container_width=True)

    # פוטר עדין
    st.markdown("<hr style='opacity: 0.1'>", unsafe_allow_html=True)
    st.caption("מערכת ניהול נתונים קליניים | עובד על בסיס קובץ 'נסיון.xlsx'")

else:
    # הודעה במידה וטעינת הקובץ נכשלה (קובץ חסר ב-GitHub)
    st.warning("⚠️ הקוד מוכן, אך לא נמצא קובץ הנתונים 'נסיון.xlsx' בתיקיית הפרויקט.")
    st.info("וודא שהעלית את קובץ האקסל המעודכן ל-GitHub באותה תיקייה של קוד הפייתון.")