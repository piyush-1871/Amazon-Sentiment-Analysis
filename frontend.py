import streamlit as st
import plotly.express as px
from transformers import pipeline
import pandas as pd
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

@st.cache_resource
def load_bert_model():
    return pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')

bert_model = load_bert_model()

def analyze_sentiment_bert_batch(texts):
    texts = texts.fillna("").astype(str).apply(lambda x: x[:1000])  # Truncate and clean
    results = bert_model(texts.tolist())  # Batch inference
    return ["Positive" if r['label'] == "POSITIVE" else "Negative" for r in results]

st.set_page_config(page_title="Amazon Sentiment Analysis System")
st.title("Amazon Review Sentiment Analysis System")

choice = st.sidebar.selectbox("My Menu", ("Home", "Analysis Via Google Sheets", "Analysis Via File Upload", "Results"))

if choice == "Home":
    st.image("https://miro.medium.com/v2/1*_JW1JaMpK_fVGld8pd1_JQ.gif")
    st.write("1. It is a Natural Language Processing application that analyzes sentiment in text data.")
    st.write("2. Predicts sentiment as Positive or Negative using BERT.")
    st.write("3. Visualizes the results based on age, gender, and other features.")

elif choice == "Analysis Via Google Sheets":
    sid = st.text_input("Enter your Google Sheet ID")
    r = st.text_input("Enter the Range (e.g., A1:D1000)")
    c = st.text_input("Enter the column name to analyze")
    btn = st.button("Analyze")

    if btn:
        if 'cred' not in st.session_state:
            flow = InstalledAppFlow.from_client_secrets_file("key.json", ["https://www.googleapis.com/auth/spreadsheets"])
            st.session_state.cred = flow.run_local_server(port=0)

        service = build('sheets', 'v4', credentials=st.session_state.cred).spreadsheets().values()
        response = service.get(spreadsheetId=sid, range=r).execute()
        data = response.get('values', [])

        if data:
            df = pd.DataFrame(data[1:], columns=data[0])

            if c not in df.columns:
                st.error("Invalid column name.")
            else:
                with st.spinner("Analyzing sentiments..."):
                    df["Sentiment"] = analyze_sentiment_bert_batch(df[c])
                    df.to_csv("results.csv", index=False)

                st.success("Sentiment analysis completed!")
                st.dataframe(df)
                st.download_button("Download Results", data=df.to_csv(index=False), file_name="results.csv", mime="text/csv")
        else:
            st.error("No data retrieved. Check the sheet ID and range.")

elif choice == "Analysis Via File Upload":
    uploaded_file = st.file_uploader("Choose a file (CSV or Excel)", type=['csv', 'xlsx'])
    c = st.text_input("Enter the column name to analyze")
    btn = st.button("Start Analysis")

    if btn and uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, low_memory=False)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)

        if c not in df.columns:
            st.error("Invalid column name.")
        else:
            with st.spinner("Analyzing sentiments..."):
                df["Sentiment"] = analyze_sentiment_bert_batch(df[c])
                df.to_csv("results.csv", index=False)

            st.success("Sentiment analysis completed!")
            st.dataframe(df.head(100))
            st.download_button("Download Results", data=df.to_csv(index=False), file_name="results.csv", mime="text/csv")

    elif btn and not uploaded_file:
        st.error("Please upload a file before starting the analysis.")

elif choice == "Results":
    try:
        df = pd.read_csv("results.csv")
        st.title("Results")
        choice2 = st.selectbox("Choose Visualization", ("None", "Pie Chart", "Histogram", "Scatter Plot"))
        st.dataframe(df)

        if choice2 == "Pie Chart":
            counts = df["Sentiment"].value_counts(normalize=True) * 100
            pc = px.pie(values=counts.values, names=counts.index)
            st.plotly_chart(pc)

        elif choice2 == "Histogram":
            col = st.selectbox("Choose column", df.columns)
            if col:
                ht = px.histogram(x=df[col], color=df["Sentiment"])
                st.plotly_chart(ht)

        elif choice2 == "Scatter Plot":
            col = st.selectbox("Choose column for X-axis", df.columns)
            if col:
                sc = px.scatter(x=df[col], y=df["Sentiment"])
                st.plotly_chart(sc)
    except FileNotFoundError:
        st.error("No results.csv file found. Please run an analysis first.")