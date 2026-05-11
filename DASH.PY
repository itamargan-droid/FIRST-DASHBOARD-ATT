import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. הגדרות דף ---
st.set_page_config(page_title="דשבורד מעקב מטופלים - AD", layout="wide")

# --- 2. מנגנון סיסמה ---
def check_password():
    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔒 כניסה למערכת מאובטחת")
            pwd = st.text_input("הזן קוד גישה לצפייה בנתונים:", type="password")
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
        df_summary = pd.read_excel(file_path, sheet_name='סיכום מטופלים', header=1)
        df_visits_raw = pd.read_excel(file_path, sheet_name='ביקורים')
        
        df_summary.columns = df_summary.columns.str.strip()
        df_visits_raw.columns = df_visits_raw.columns.str.strip()

        if 'תאריך ביקור' in df_visits_raw.columns:
            df_visits_raw['תאריך ביקור'] = pd.to_datetime(df_visits_raw['תאריך ביקור'], errors='coerce')
            df_visits_raw = df_visits_raw.dropna(subset=['תאריך ביקור'])
        
        # ניקוי עמודות טקסטואליות
        for df in [df_summary, df_visits_raw]:
            for col in ['תרופה', 'מין', 'קופת חולים', 'שם', 'משפחה', 'APOE']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            if 'תרופה' in df.columns:
                df['תרופה'] = df['תרופה'].str.upper()

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

# פונקציות עזר לגרפים
def get_continuous_timeline():
    dates = pd.date_range(start='2025-01-01', end='2026-12-01', freq='MS')
    drugs = ["LECANEMAB", "DONANEMAB"]
    items = []
    for d in dates:
        for drug in drugs:
            items.append({'תאריך_ציר': d.strftime('%m/%Y'), 'תרופה': drug, 'sort_key': d})
    return pd.DataFrame(items)

def plot_timeline_bar(df, title, y_label):
    if df.empty: return px.bar(title="אין נתונים להצגה")
    df = df.copy()
    df['תאריך_ציר'] = df['תאריך ביקור'].dt.strftime('%m/%Y')
    agg = df.groupby(['תאריך_ציר', 'תרופה']).size().reset_index(name='כמות')
    timeline = get_continuous_timeline()
    merged = pd.merge(timeline, agg, on=['תאריך_ציר', 'תרופה'], how='left').fillna(0)
    
    selected_drugs = df['תרופה'].unique()
    merged = merged[merged['תרופה'].isin(selected_drugs)].sort_values('sort_key')

    fig = px.bar(merged, x='תאריך_ציר', y='כמות', color='תרופה',
                 title=title,
                 color_discrete_map={"LECANEMAB": "#9B59B6", "DONANEMAB": "#F1C40F"},
                 text_auto=True, barmode='stack')

    fig.update_layout(xaxis_title="חודש/שנה", yaxis_title=y_label, xaxis={'type': 'category'})
    return fig

# --- 4. לוגיקת דשבורד ---
if df_summary is not None:
    st.title("📊 דשבורד ניתוח טיפולים - מעקב 2025-2026")
    
    with st.sidebar:
        st.header("🛠️ הגדרות תצוגה")
        show_gender_pie = st.toggle("פירוט מגדר בנתח שוק", value=False)
        
        st.divider()
        st.header("🔍 מסננים")
        sel_drug = st.multiselect("💊 תרופה:", options=df_summary['תרופה'].unique(), default=list(df_summary['תרופה'].unique()))
        sel_hmo = st.multiselect("🏥 קופת חולים:", options=df_summary['קופת חולים'].unique(), default=list(df_summary['קופת חולים'].unique()))
        sel_gen = st.multiselect("👤 מגדר:", options=df_summary['מין'].unique(), default=list(df_summary['מין'].unique()))

    # פילטור הנתונים
    f_visits = df_visits[df_visits['תרופה'].isin(sel_drug) & df_visits['מין'].isin(sel_gen) & df_visits['קופת חולים'].isin(sel_hmo)]
    f_summary = df_summary[df_summary['תרופה'].isin(sel_drug) & df_summary['קופת חולים'].isin(sel_hmo) & df_summary['מין'].isin(sel_gen)]

    # KPIs
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("מטופלים (מסונן)", len(f_summary))
    m2.metric("סה\"כ ביקורים", len(f_visits))
    m3.metric("מטופלים חדשים", f_visits['האם_חדש'].sum())
    m4.metric("מטופלי LECANEMAB", len(f_summary[f_summary['תרופה'] == 'LECANEMAB']))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📈 מגמות זמן", "👥 פלח שוק וקופות", "🧬 גנטיקה APOE"])

    with tab1:
        st.plotly_chart(plot_timeline_bar(f_visits, "כמות ביקורים חודשית מצטברת", "מספר ביקורים"), use_container_width=True)
        st.plotly_chart(plot_timeline_bar(f_visits[f_visits['האם_חדש']], "קליטת מטופלים חדשים (ביקור ראשון)", "מספר חדשים"), use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        
        with c1:
            if show_gender_pie:
                df_pie = f_summary.copy()
                df_pie['מגדר_סימון'] = df_pie['מין'].map({'זכר': '♂', 'נקבה': '♀'}).fillna('')
                df_pie['קטגוריה_מגדר'] = df_pie['תרופה'] + " " + df_pie['מגדר_סימון']
                
                fig_market = px.pie(df_pie, names="קטגוריה_מגדר", hole=0.5,
                                   title="נתח שוק - תרופה ומגדר",
                                   color="קטגוריה_מגדר",
                                   color_discrete_map={
                                       "LECANEMAB ♂": "#6C3483", "LECANEMAB ♀": "#BB8FCE",
                                       "DONANEMAB ♂": "#B7950B", "DONANEMAB ♀": "#F4D03F"
                                   })
            else:
                fig_market = px.pie(f_summary, names="תרופה", hole=0.5,
                                   title="נתח שוק כולל",
                                   color="תרופה",
                                   color_discrete_map={"LECANEMAB": "#9B59B6", "DONANEMAB": "#F1C40F"})
            
            fig_market.update_traces(textinfo='value+percent', texttemplate='%{value} (%{percent})')
            st.plotly_chart(fig_market, use_container_width=True)

        with c2:
            hmo_agg = f_summary.groupby(['קופת חולים', 'תרופה']).size().reset_index(name='כמות')
            if not hmo_agg.empty:
                hmo_agg['percent'] = hmo_agg.groupby('קופת חולים')['כמות'].transform(lambda x: (x / x.sum() * 100).round(1))
                hmo_agg['label'] = hmo_agg.apply(lambda x: f"{int(x['כמות'])} ({x['percent']}%)", axis=1)

                fig_hmo = px.bar(hmo_agg, x='קופת חולים', y='כמות', color='תרופה', 
                                 text='label', barmode='group',
                                 color_discrete_map={"LECANEMAB": "#9B59B6", "DONANEMAB": "#F1C40F"},
                                 title="התפלגות לפי קופה (מספר ואחוז)")
                st.plotly_chart(fig_hmo, use_container_width=True)

    with tab3:
        if 'APOE' in f_summary.columns:
            apoe_agg = f_summary.groupby(['APOE', 'תרופה']).size().reset_index(name='כמות')
            if not apoe_agg.empty:
                total_a = apoe_agg['כמות'].sum()
                apoe_agg['label'] = apoe_agg.apply(lambda x: f"{int(x['כמות'])} ({(x['כמות']/total_a*100):.1f}%)", axis=1)
                
                fig_apoe = px.bar(apoe_agg, x='APOE', y='כמות', color='תרופה',
                                 text='label', barmode='stack',
                                 color_discrete_map={"LECANEMAB": "#9B59B6", "DONANEMAB": "#F1C40F"},
                                 title="התפלגות גנוטיפ APOE")
                st.plotly_chart(fig_apoe, use_container_width=True)
            else:
                st.info("אין נתוני APOE להצגה תחת הסינון הנוכחי")
        else:
            st.warning("עמודת 'APOE' לא נמצאה בקובץ")

    with st.expander("👁️ צפייה בנתונים הגולמיים"):
        st.dataframe(f_summary, use_container_width=True)