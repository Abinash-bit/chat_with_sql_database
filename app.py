import os
import re
import streamlit as st
from langchain.chains import create_sql_query_chain
from langchain_google_genai import GoogleGenerativeAI
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
db_user = "root"
db_password = "abinash"
db_host = "localhost"
db_name = "retail_sales_db"

# Create SQLAlchemy engine
engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")

# Initialize SQLDatabase
db = SQLDatabase(engine, sample_rows_in_table_info=3)

# Initialize LLM
llm = GoogleGenerativeAI(model="gemini-pro", google_api_key=os.environ["GOOGLE_API_KEY"])

# Create SQL query chain
chain = create_sql_query_chain(llm, db)

def clean_sql_query(raw_response):
    # Extract SQL from markdown code block if present
    code_block_match = re.search(r'```sql(.*?)```', raw_response, re.DOTALL)
    if code_block_match:
        cleaned = code_block_match.group(1).strip()
    else:
        cleaned = raw_response.strip()
    
    # Remove any remaining 'sql' prefix
    cleaned = re.sub(r'^sql\s*', '', cleaned, flags=re.IGNORECASE)
    return cleaned

def execute_query(question):
    try:
        # Generate SQL query from question
        raw_response = chain.invoke({"question": question})
        cleaned_sql = clean_sql_query(raw_response)

        # Execute the cleaned query
        result = db.run(cleaned_sql)
                
        return cleaned_sql, result
    except ProgrammingError as e:
        st.error(f"Database error: {e}")
        return None, None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None, None

# Streamlit interface
st.title("Question Answering App")

# Input from user
question = st.text_input("Enter your question:")

if st.button("Execute"):
    if question:
        response, query_result = execute_query(question)
        
        if response and query_result is not None:
            st.write("Generated SQL Query:")
            st.code(response, language="sql")
            st.write("Query Result:")
            st.write(query_result)
        else:
            st.write("No result returned due to an error.")
    else:
        st.write("Please enter a question.")
