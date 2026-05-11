import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. הגדרות דף ---
st.set_page_config(page_title="דשבורד מעקב מטופלים - AD", layout="wide")

# --- 2. מנגנון סיסמה ---
def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔒 כניסה למערכת")
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

# --- 3. טעינת נתונים ---
@st.cache_data
def load_data():
    file_path = "איתמרATT_אשפוז_יום_סופי.xlsx"
    try:
        # קריאת הגיליונות
        df_summary = pd.read_excel(file_path, sheet_name='סיכום מטופלים', header=1)
        df_visits_raw = pd.read_excel(file_path, sheet_name='ביקורים')
        
        # ניקוי שמות עמודות
        df_summary.columns = df_summary.columns.str.strip()
        df_visits_raw.columns = df_visits_raw.columns.str.strip()

        # המרת תאריכים
        if 'תאריך ביקור' in df_visits_raw.columns:
            df_visits_raw['תאריך ביקור'] = pd.to_datetime(df_visits_raw['תאריך ביקור'], errors='coerce')
            df_visits_raw = df_visits_raw.dropna(subset=['תאריך ביקור'])
        
        # ניקוי טקסטים
        cols_to_clean = ['תרופה', 'מין', 'קופת חולים', 'שם', 'משפחה', 'APOE']
        for df in [df_summary, df_visits_raw]:
            for col in cols_to_clean:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            if 'תרופה' in df.columns:
                df['תרופה'] = df['תרופה'].str.upper()

        # הסרת כפילויות בביקורים
        df_visits = df_visits_raw.drop_duplicates(subset=['שם', 'משפחה', 'תאריך ביקור'])
        
        # זיהוי מטופלים חדשים
        df_visits['מזהה_מטופל'] = df_visits['שם'] + "_" + df_visits['משפחה']
        first_v = df_visits.groupby('מזהה_מטופל')['תאריך ביקור'].min().reset_index()
        first_v.columns = ['מזהה_מטופל', 'תאריך_הצטרפות']
        df_visits = df_visits.merge(first_v, on='מזהה_מטופל')
        df_visits['האם_חדש'] = df_visits['תאריך ביקור'] == df_visits['תאריך_הצטרפות']
        
        return df_summary, df_visits
    except Exception as e:
        st.error(f"שגיאה בטעינת הקובץ: {e}")
        return None, None

df_summary, df_visits = load_data()

# --- פונקציות עזר לגרפים ---
def get_continuous_timeline():
    dates = pd.date_range(start='2025-01-01', end='2026-12-01', freq='MS')
    drugs = ["LECANEMAB", "DONANEMAB"]
    items = []
    for d in dates:
        for drug in drugs:
            items.append({'תאריך_ציר': d.strftime('%m/%Y'), 'תרופה': drug, 'sort_key': d})
    return pd.DataFrame(items)

def plot_timeline_bar(df, title, y_label):
    if df.empty: return px.bar(title="אין נתונים")
    df = df.copy()
    df['תאריך_ציר'] = df['תאריך ביקור'].dt.strftime('%m/%Y')
    agg = df.groupby(['תאריך_ציר', 'תרופה']).size().reset_index(name='כמות')
    timeline = get_continuous_timeline()
    merged = pd.merge(timeline, agg, on=['תאריך_ציר', 'תרופה'], how='left').fillna(0)
    
    fig = px.bar(merged[merged['תרופה'].isin(df['תרופה'].unique())].sort_values('sort_key'), 
                 x='תאריך_ציר', y='כמות', color='תרופה', title=title,
                 color_discrete_map={"LECANEMAB": "#9B59B6", "DONANEMAB": "#F1C40F"},
                 text_auto=True, barmode='stack')
    
    fig.update_layout(xaxis_title="חודש/שנה", yaxis_title=y_label, xaxis={'type': 'category'})
    return fig

# --- 4. לוגיקת דשבורד ---
if df_summary is not None:
    st.title("📊 דשבורד ניתוח טיפולים - AD")
    
    with st.sidebar:
        st.header("🛠️ הגדרות תצוגה")
        show_gender_breakdown = st.toggle("הצג חיתוך מגדר בנתח שוק", value=False)
        
        st.divider()
        st.header("🔍 מסננים")
        sel_drug = st.multiselect("💊 תרופה:", options=df_summary['תרופה'].unique(), default=list(df_summary['תרופה'].unique()))
        sel_hmo = st.multiselect("🏥 קופת חולים:", options=df_summary['קופת חולים'].unique(), default=list(df_summary['קופת חולים'].unique()))
        sel_gen = st.multiselect("👤 מגדר:", options=df_summary['מין'].unique(), default=list(df_summary['מין'].unique()))

    # פילטור
    f_visits = df_visits[df_visits['תרופה'].isin(sel_drug) & df_visits['מין'].isin(sel_gen) & df_visits['קופת חולים'].isin(sel_hmo)]
    f_summary = df_summary[df_summary['תרופה'].isin(sel_drug) & df_summary['קופת חולים'].isin(sel_hmo) & df_summary['מין'].isin(sel_gen)]

    # KPIs
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("מטופלים", len(f_summary))
    m2.metric("סה\"כ ביקורים", len(f_visits))
    m3.metric("מטופלים חדשים", f_visits['האם_חדש'].sum())
    m4.metric("מטופלי LECANEMAB", len(f_summary[f_summary['תרופה'] == 'LECANEMAB']))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📈 מגמות זמן", "👥 פלח שוק ומגדר", "🧬 גנטיקה (APOE)"])
    
    with tab1:
        st.plotly_chart(plot_timeline_bar(f_visits, "כמות ביקורים חודשית מצטברת", "מספר ביקורים"), use_container_width=True)
        st.plotly_chart(plot_timeline_bar(f_visits[f_visits['האם_חדש']], "קליטת מטופלים חדשים", "מספר חדשים"), use_container_width=True)

    with tab2:
        c1, c2 = st.columns([1, 1])
        
        with c1:
            # גרף בייגלה עם חיתוך מגדר מותנה
            if show_gender_breakdown:
                # יצירת עמודה משולבת עם סמלים
                df_pie = f_summary.copy()
                df_pie['מגדר_סימון'] = df_pie['מין'].map({'זכר': '♂', 'נקבה': '♀'}).fillna('')
                df_pie['קטגוריה_משולבת'] = df_pie['תרופה'] + " " + df_pie['מגדר_סימון']
                
                fig_market = px.pie(df_pie, names="קטגוריה_משול