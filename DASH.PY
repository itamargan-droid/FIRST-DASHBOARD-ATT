import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. הגדרות דף ועיצוב CSS מותאם ---
st.set_page_config(page_title="AD Clinical Insights", layout="wide")

# הזרקת CSS לעיצוב מודרני
st.markdown("""
    <style>
    /* רקע כללי של האפליקציה */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* עיצוב כרטיסי ה-Metric (KPIs) */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #00D1B2 !important;
    }
    
    /* עיצוב ה-Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    /* כותרות */
    h1, h2, h3 {
        color: #FFFFFF;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* עיצוב ה-Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #161B22;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1F6FEB !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. מנגנון סיסמה ---
def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<h2 style='text-align: center;'>🔐 כניסה למערכת ניהול</h2>", unsafe_allow_html=True)
            pwd = st.text_input("קוד גישה:", type="password")
            if st.button("התחברות"):
                if pwd == "12345": 
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ קוד שגוי")
        return False
    return True

if not check_password():
    st.stop()

# --- 3. טעינת נתונים (זהה לקוד הקודם) ---
@st.cache_data
def load_data():
    file_path = "איתמרATT_אשפוז_יום_סופי.xlsx"
    try:
        df_summary = pd.read_excel(file_path, sheet_name='סיכום מטופלים', header=1)
        df_visits_raw = pd.read_excel(file_path, sheet_name='ביקורים')
        
        df_summary.columns = df_summary.columns.str.strip()
        df_visits_raw.columns = df_visits_raw.columns.str.strip()

        if 'תאריך ביקור' in df_visits_raw.columns:
            df_visits_raw['תאריך ביקור'] = pd.to_datetime(df_visits_raw['תאריך ביקור'], errors='coerce')
            df_visits_raw = df_visits_raw.dropna(subset=['תאריך ביקור'])
        
        for df in [df_summary, df_visits_raw]:
            for col in ['תרופה', 'מין', 'קופת חולים', 'שם', 'משפחה', 'APOE']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            if 'תרופה' in df.columns:
                df['תרופה'] = df['תרופה'].str.upper()

        df_visits = df_visits_raw.drop_duplicates(subset=['שם', 'משפחה', 'תאריך ביקור'])
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

# פונקציה לגרפי Plotly בעיצוב "Dark"
def apply_dark_theme(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#E0E0E0",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(showgrid=False, linecolor='#30363D')
    fig.update_yaxes(showgrid=True, gridcolor='#30363D', linecolor='#30363D')
    return fig

# --- 4. לוגיקת דשבורד ---
if df_summary is not None:
    st.markdown("<h1 style='text-align: right;'>📊 תובנות קליניות: מעקב טיפולים באלצהיימר</h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### ⚙️ הגדרות")
        show_gender_pie = st.toggle("פירוט מגדר בנתח שוק", value=False)
        st.divider()
        sel_drug = st.multiselect("💊 תרופה:", options=df_summary['תרופה'].unique(), default=list(df_summary['תרופה'].unique()))
        sel_hmo = st.multiselect("🏥 קופת חולים:", options=df_summary['קופת חולים'].unique(), default=list(df_summary['קופת חולים'].unique()))
        sel_gen = st.multiselect("👤 מגדר:", options=df_summary['מין'].unique(), default=list(df_summary['מין'].unique()))

    # פילטור
    f_visits = df_visits[df_visits['תרופה'].isin(sel_drug) & df_visits['מין'].isin(sel_gen) & df_visits['קופת חולים'].isin(sel_hmo)]
    f_summary = df_summary[df_summary['תרופה'].isin(sel_drug) & df_summary['קופת חולים'].isin(sel_hmo) & df_summary['מין'].isin(sel_gen)]

    # KPIs בעיצוב נקי
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("סה\"כ מטופלים", len(f_summary))
    with kpi2:
        st.metric("ביקורים שבוצעו", len(f_visits))
    with kpi3:
        st.metric("מטופלים חדשים", f_visits['האם_חדש'].sum())
    with kpi4:
        st.metric("Lecanemab", len(f_summary[f_summary['תרופה'] == 'LECANEMAB']))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🕒 מגמות זמן", "🌓 ניתוח דמוגרפי", "🧬 פרופיל גנטי"])

    with tab1:
        # גרף ביקורים מודרני
        df_v_count = f_visits.copy()
        df_v_count['חודש'] = df_v_count['תאריך ביקור'].dt.strftime('%m/%Y')
        agg_v = df_v_count.groupby(['חודש', 'תרופה']).size().reset_index(name='כמות')
        
        fig_v = px.line(agg_v, x='חודש', y='כמות', color='תרופה', markers=True,
                        title="נפח ביקורים חודשי",
                        color_discrete_map={"LECANEMAB": "#A29BFE", "DONANEMAB": "#FDCB6E"})
        st.plotly_chart(apply_dark_theme(fig_v), use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            if show_gender_pie:
                df_pie = f_summary.copy()
                df_pie['קטגוריה'] = df_pie['תרופה'] + " (" + df_pie['מין'].map({'זכר': '♂', 'נקבה': '♀'}) + ")"
                fig_p = px.pie(df_pie, names="קטגוריה", hole=0.6, title="פילוח שוק ומגדר",
                               color_discrete_sequence=["#6C5CE7", "#A29BFE", "#E17055", "#FAB1A0"])
            else:
                fig_p = px.pie(f_summary, names="תרופה", hole=0.6, title="נתח שוק תרופות",
                               color_discrete_map={"LECANEMAB": "#6C5CE7", "DONANEMAB": "#E17055"})
            
            fig_p.update_traces(textinfo='value+percent', texttemplate='%{value}<br>(%{percent})')
            st.plotly_chart(apply_dark_theme(fig_p), use_container_width=True)

        with c2:
            hmo_agg = f_summary.groupby(['קופת חולים', 'תרופה']).size().reset_index(name='כמות')
            fig_h = px.bar(hmo_agg, x='קופת חולים', y='כמות', color='תרופה', barmode='group',
                           title="פריסה לפי קופות חולים",
                           color_discrete_map={"LECANEMAB": "#6C5CE7", "DONANEMAB": "#E17055"})
            st.plotly_chart(apply_dark_theme(fig_h), use_container_width=True)

    with tab3:
        if 'APOE' in f_summary.columns:
            apoe_agg = f_summary.groupby(['APOE', 'תרופה']).size().reset_index(name='כמות')
            fig_a = px.bar(apoe_agg, x='APOE', y='כמות', color='תרופה',
                           title="התפלגות גנוטיפ APOE",
                           color_discrete_map={"LECANEMAB": "#6C5CE7", "DONANEMAB": "#E17055"},
                           text_auto=True)
            st.plotly_chart(apply_dark_theme(fig_a), use_container_width=True)

    st.divider()
    with st.expander("📂 גישה למסד הנתונים הגולמי"):
        st.dataframe(f_summary.style.background_gradient(cmap='Blues'), use_container_width=True)