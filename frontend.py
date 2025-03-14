import streamlit as st
import plotly.express as px
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
#needed for taking permission
from google_auth_oauthlib.flow import InstalledAppFlow
#for bulding the services
from googleapiclient.discovery import build

st.set_page_config(page_title="Amazon Sentiment Analysis System")

st.title("Amazon Review Sentiment Analysis System")
choice = st.sidebar.selectbox("My Menu", ("Home", "Analysis Via Google Sheets", "Analysis Via File Upload", "Results"))

if(choice == "Home"):
    st.image("https://miro.medium.com/v2/1*_JW1JaMpK_fVGld8pd1_JQ.gif")
    st.write("1.It is a natural language Processing Application which can analyze the sentiment on the text data.")
    st.write("2.This application predicts the sentiment into 3 categories Positive, Negative and Neutral.")
    st.write("3.This application then visualizes the results based on different factors such as age, gender.")
elif(choice == "Analysis Via Google Sheets"):
    sid = st.text_input("Enter your Google Sheet ID")
    r = st.text_input("Enter the Range between first column and last column.")
    c = st.text_input("Enter column name that is to be analyzed.")
    btn = st.button("Analyze")
    
    if(btn):
        if 'cred' not in st.session_state:
            f = InstalledAppFlow.from_client_secrets_file("key.json", ["https://www.googleapis.com/auth/spreadsheets"])
            st.session_state.cred = f.run_local_server(port = 0)
        
        mymodel = SentimentIntensityAnalyzer()
        
        # Building the service
        service = build('sheets', 'v4', credentials=st.session_state.cred).spreadsheets().values()
        k = service.get(spreadsheetId= sid, range=r).execute()
        d = k['values']
        
        # Convert the retrieved data into a pandas DataFrame
        df = pd.DataFrame(data=d[1:], columns=d[0])
        
        sentiments = []
        for i in range(0, len(df)):
            t = df._get_value(i, c)
            pred = mymodel.polarity_scores(t)
            if pred['compound'] > 0.5:
                sentiments.append("Positive")
            elif pred['compound'] < -0.5:
                sentiments.append("Negative")
            else:
                sentiments.append("Neutral")
        
        # Add the Sentiment column to the DataFrame
        df['Sentiment'] = sentiments  
        
        # Save results to CSV
        results = "results.csv"
        df.to_csv(results, index=False)  
        
        # Display the results dataframe
        st.subheader("Sentiment Analysis Results")
        st.dataframe(df)
        
        # Add a download button for the results
        btn2 = st.download_button(
            label="Download Results",
            data=df.to_csv(index=False),
            file_name=results,
            mime="text/csv"
        )
        
        if btn2:
            st.success(f"Results saved as {results}.")
elif(choice == "Analysis Via File Upload"):
    st.subheader("Upload a CSV or Excel File for Sentiment Analysis")
    uploaded_file = st.file_uploader("Choose a file (CSV or Excel)", type=['csv','xlsx'])
    c = st.text_input("Enter the column name to be analyzed for sentiment.")
    btn = st.button("Start Analysis")
    
    if btn and uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        
        if c not in df.columns:
            st.error("Invalid column name. Please enter a valid column name.")
        else:
            mymodel = SentimentIntensityAnalyzer()
            sentiments = []
            
            for i in range(len(df)):
                t = str(df[c].iloc[i])
                
                pred = mymodel.polarity_scores(t)
                if pred['compound'] > 0.5:
                    sentiments.append("Positive")
                elif pred['compound'] < -0.5:
                    sentiments.append("Negative")
                else:
                    sentiments.append("Neutral")
                    
            # Add the Sentiment column to the DataFrame
            df['Sentiment'] = sentiments
            
            
            #save results to downloadable csv
            results = "results.csv"
            btn2 = st.download_button(
                label="Download Results",
                data=df.to_csv(index=False),
                file_name=results,
                mime="text/csv"
            )
            if btn2:
                df.to_csv(results, index=False)
            
            # Display success message and preview results
            st.success(f"Sentiment analysis completed! Click on the Download Results button to save the {results}")
            st.dataframe(df.head(100))
            # Provide download link
            
    elif btn and not uploaded_file:
        st.error("Please upload a file before starting the analysis.")        
            
elif(choice == "Results"):
    st.title("Results")
    df = pd.read_csv("results.csv")
    choice2 = st.selectbox("Choose Visualization", ("None", "Pie Chart", "Histogram", "Scatter Plot"))
    st.dataframe(df)
    if(choice2 == "Pie Chart"):
        #Pie Chart
        prosper = (len(df[df["Sentiment"] == "Positive"])/len(df))*100
        negper = (len(df[df["Sentiment"] == "Negative"])/len(df))*100
        neuper = (len(df[df["Sentiment"] == "Neutral"])/len(df))*100

        pc = px.pie(values = [prosper, negper, neuper], names = ["Positive", "Negative", "Neutral"])
        st.plotly_chart(pc)
    if(choice2 == "Histogram"):
        #histogram for categorical value
        k = st.selectbox("Choose column", df.columns)
        if(k):
            ht = px.histogram(x=df[k], color=df['Sentiment'])
            ht.update_layout(yaxis_title = k)
            st.plotly_chart(ht)

    if(choice2 == "Scatter Plot"):
        k = st.selectbox("Choose column x", df.columns)
        sc = px.scatter(x=df[k], y=df["Sentiment"]) 
        sc.update_layout(xaxis_title = k) 
        st.plotly_chart(sc)

    

        


