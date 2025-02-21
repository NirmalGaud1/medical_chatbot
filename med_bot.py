#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Load knowledge base with error handling
def load_knowledge_base(file_path):
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            st.error(f"File not found: {file_path}")
            return None
        
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        # Check if the file is empty
        if df.empty:
            st.error(f"The file {file_path} is empty.")
            return None
        
        return df
    
    except Exception as e:
        st.error(f"Error loading the knowledge base: {e}")
        return None

# Preprocess the data
def preprocess_data(df):
    df = df.fillna("")
    df['short_question'] = df['short_question'].str.lower()
    df['short_answer'] = df['short_answer'].str.lower()
    return df

# Create a TF-IDF vectorizer for similarity matching
def create_vectorizer(df):
    vectorizer = TfidfVectorizer()
    question_vectors = vectorizer.fit_transform(df['short_question'])
    return vectorizer, question_vectors

# Find the closest matching question
def find_closest_question(user_query, vectorizer, question_vectors, df):
    query_vector = vectorizer.transform([user_query.lower()])
    similarities = cosine_similarity(query_vector, question_vectors).flatten()
    best_match_index = similarities.argmax()
    best_match_score = similarities[best_match_index]
    
    # Set a similarity threshold (e.g., 0.5)
    if best_match_score > 0.5:
        return df.iloc[best_match_index]['short_answer']
    else:
        return None

# Configure the Generative AI model
def configure_generative_model(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

# Use Gemini to refine and frame a better answer
def refine_answer_with_gemini(generative_model, user_query, closest_answer):
    try:
        # Augment the prompt with context
        context = """
        You are a medical chatbot. Refine the following answer to make it more professional, clear, and actionable.
        Ensure the response is concise and easy to understand.
        """
        prompt = f"{context}\n\nUser Query: {user_query}\nClosest Answer: {closest_answer}\nRefined Answer:"
        
        # Generate refined response
        response = generative_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error refining the answer: {e}"

# Main chatbot function
def medical_chatbot(df, vectorizer, question_vectors, generative_model):
    st.title("Medical Chatbot 🩺")
    st.write("Welcome to the Medical Chatbot! Ask me anything about medical topics.")
    
    user_query = st.text_input("You:", placeholder="Type your question here...")
    
    if user_query:
        # Step 1: Retrieve from knowledge base
        closest_answer = find_closest_question(user_query, vectorizer, question_vectors, df)
        
        if closest_answer:
            # Step 2: Use Gemini to refine the answer
            with st.spinner("Refining the answer..."):
                refined_answer = refine_answer_with_gemini(generative_model, user_query, closest_answer)
                st.write(f"**Bot (refined answer):** {refined_answer}")
        else:
            # Step 3: Generate using AI Agent if no match is found
            try:
                # Augment the prompt with context
                context = """
                You are a medical chatbot. Provide accurate and concise answers to medical questions.
                If the user describes symptoms, suggest possible causes and recommend consulting a doctor for a proper diagnosis.
                Use a professional tone and format the response clearly.
                """
                prompt = f"{context}\n\nUser: {user_query}\nBot:"
                
                # Generate response
                response = generative_model.generate_content(prompt)
                st.write(f"**Bot (AI-generated):** {response.text}")
            except Exception as e:
                st.error(f"Sorry, I couldn't generate a response. Error: {e}")

# Main function
def main():
    # Load your CSV file
    file_path = "med_bot_data.csv"  # Replace with your CSV file path
    
    # Load and preprocess the knowledge base
    df = load_knowledge_base(file_path)
    if df is None:
        return  # Stop execution if the knowledge base couldn't be loaded
    
    df = preprocess_data(df)
    
    # Create TF-IDF vectorizer and question vectors
    vectorizer, question_vectors = create_vectorizer(df)
    
    # Configure the Generative AI model
    API_KEY = "AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c"  # Replace with your API key
    if not API_KEY:
        st.error("API key not found. Please set the GOOGLE_API_KEY environment variable.")
        return
    generative_model = configure_generative_model(API_KEY)
    
    # Run the chatbot
    medical_chatbot(df, vectorizer, question_vectors, generative_model)

if __name__ == "__main__":
    main()
