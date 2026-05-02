import streamlit as st
import pandas as pd
import plotly.express as px

# הגדרת כותרת לדף
st.set_page_config(page_title="דשבורד מעקב מטופלים", layout="wide")

st.title("📊 דשבורד מעקב מטופלים - ניתוח נתונים")

# טעינת הנתונים
@st.cache_data
def load_data():
    df = pd.read_excel("נסיון.xlsx")
    return df

try:
    df = load_data()

    # --- סרגל צדי למסננים ---
    st.sidebar.header("מסננים")

    # מסנן מין
    gender_list = ["הכל"] + list(df['מין'].unique())
    selected_gender = st.sidebar.selectbox("בחר מין:", gender_list)

    # מסנן תרופה
    drug_list = ["הכל"] + list(df['תרופה'].unique())
    selected_drug = st.sidebar.selectbox("בחר תרופה:", drug_list)

    # מסנן ARIA
    aria_list = ["הכל"] + list(df['האם ARIA'].unique())
    selected_aria = st.sidebar.selectbox("האם ARIA:", aria_list)

    # מסנן תגובה לעירוי
    reaction_list = ["הכל"] + list(df['האם תגובה לעירוי'].unique())
    selected_reaction = st.sidebar.selectbox("תגובה לעירוי:", reaction_list)

    # --- פילטור הנתונים בפועל ---
    filtered_df = df.copy()

    if selected_gender != "הכל":
        filtered_df = filtered_df[filtered_df['מין'] == selected_gender]
    
    if selected_drug != "הכל":
        filtered_df = filtered_df[filtered_df['תרופה'] == selected_drug]

    if selected_aria != "הכל":
        filtered_df = filtered_df[filtered_df['האם ARIA'] == selected_aria]

    if selected_reaction != "הכל":
        filtered_df = filtered_df[filtered_df['האם תגובה לעירוי'] == selected_reaction]

    # --- תצוגת מדדים מרכזיים (Metrics) ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("סה\"כ מטופלים (מסונן)", len(filtered_df))
    col2.metric("גיל ממוצע", round(filtered_df['גיל'].mean(), 1) if not filtered_df.empty else 0)
    col3.metric("מטופלי ARIA", len(filtered_df[filtered_df['האם ARIA'] == 'כן']))
    col4.metric("תגובות לעירוי", len(filtered_df[filtered_df['האם תגובה לעירוי'] == 'כן']))

    st.divider()

    # --- תצוגת גרפים ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("התפלגות גילאים")
        fig_age = px.histogram(filtered_df, x="גיל", nbins=10, title="התפלגות גיל המטופלים", color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig_age, use_container_width=True)

    with c2:
        st.subheader("סוגי תרופות")
        fig_drug = px.pie(filtered_df, names="תרופה", title="חלוקה לפי תרופה", hole=0.4)
        st.plotly_chart(fig_drug, use_container_width=True)

    # --- טבלת נתונים ---
    st.subheader("📋 נתוני מטופלים מפורטים")
    st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"שגיאה בטעינת הקובץ: {e}")
    st.info("וודא שהקובץ 'נסיון.xlsx' נמצא באותה תיקייה של הקוד.")