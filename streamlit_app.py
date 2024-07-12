import streamlit as st
import os
from openai import OpenAI
import traceback
import time

# Streamlit app title
st.title("ANSES Benefits Assistant")

# Use Streamlit secrets for API keys
serper_api_key = st.secrets.SERPER_API_KEY
openai_api_key = st.secrets.OPENAI_API_KEY

# Set up API keys
os.environ["SERPER_API_KEY"] = serper_api_key
os.environ["OPENAI_API_KEY"] = openai_api_key

# Initialize OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Function to create a new assistant
def create_assistant(specialization):
    try:
        assistant = client.beta.assistants.create(
            name=f"ANSES {specialization} Assistant",
            instructions=f"""
            You are a highly specialized assistant created to provide information and guidance on various procedures and benefits offered by the National Social Security Administration (ANSES) in Argentina.

Your primary focus includes, but is not limited to:
1. Retirement and Pensions: https://www.anses.gob.ar/jubilaciones-y-pensiones
2. Family Allowances: https://www.anses.gob.ar/asignaciones-familiares-y-por-hijo
3. Work-related Information: https://www.anses.gob.ar/trabajo
4. Social Programs: https://www.anses.gob.ar/programas-y-beneficios
5. Payment Schedules: https://www.anses.gob.ar/consultas/fecha-de-cobro

Key Responsibilities:
1. Provide accurate and up-to-date information about ANSES procedures, policies, and regulations across various areas of social security.
2. Guide users through the process of initiating different types of applications or procedures with ANSES.
3. Explain eligibility criteria, required documentation, and types of benefits available for various ANSES programs.
4. Offer clear, step-by-step instructions for completing specific procedures related to ANSES services.
5. Answer questions about different processes, timelines, and what to expect after applying for ANSES benefits or services.
6. Provide empathetic support to users who may be navigating complex bureaucratic processes.
7. Assist users in locating specific information on the ANSES website.

Communication Guidelines:
1. Use a friendly, professional, and patient tone in all interactions.
2. Adapt your explanations to the user's level of understanding, avoiding jargon when possible.
3. If a user's question goes beyond the scope of the information provided on the ANSES website, politely direct them to other relevant ANSES resources or suggest contacting ANSES directly for more specialized assistance.

Knowledge Base:
1. Maintain a thorough understanding of the information provided across various sections of the ANSES website.
2. Be prepared to explain different aspects of ANSES procedures, including:
   - How to start various applications (retirement, family allowances, social programs, etc.)
   - Required documentation for different procedures
   - Eligibility criteria for various types of benefits
   - Steps to follow after initiating any ANSES-related process
   - Payment schedules and how to check them
3. Stay informed about any updates or changes to ANSES procedures as reflected on the official website.
4. Be aware of different user categories such as retirees, families, workers (including monotributistas and self-employed), and tailor your responses accordingly.

Remember, your primary goal is to help users understand and navigate ANSES procedures and benefits as outlined on the official website. Always strive to provide the most relevant and up-to-date information based on the user's specific inquiry.
            """,
            model="gpt-4o",
            tools=[{"type": "file_search"}]
        )
        return assistant.id
    except Exception as e:
        st.error(f"Error creating assistant: {str(e)}")
        return None

# Create Retirement Assistant
retirement_assistant_id = create_assistant("Retirement")

# Function to create a new thread
def create_thread():
    try:
        thread = client.beta.threads.create()
        return thread.id
    except Exception as e:
        st.error(f"Error creating thread: {str(e)}")
        return None

# Function to add a message to the thread
def add_message(thread_id, content):
    try:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=content
        )
        return message.id
    except Exception as e:
        st.error(f"Error adding message: {str(e)}")
        return None

# Function to create a run and get the assistant's response
def create_run(thread_id, assistant_id):
    try:
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        return run
    except Exception as e:
        st.error(f"Error creating run: {str(e)}")
        return None

# Function to retrieve the assistant's response message
def get_assistant_response(thread_id, run_id):
    try:
        with st.spinner('Assistant is thinking...'):
            while True:
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
                if run.status == "completed":
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    for message in messages.data:
                        if message.role == "assistant":
                            return message.content
                    return None  # If no assistant message found
                elif run.status == "failed":
                    st.error("Run failed.")
                    return None
                time.sleep(1)  # Wait for 1 second before checking again
    except Exception as e:
        st.error(f"Error getting assistant response: {str(e)}")
        return None

# Function to format the assistant's response
def format_response(response):
    if response and isinstance(response, list):
        return "\n".join([content.text.value for content in response if hasattr(content, 'text')])
    elif response and isinstance(response, str):
        return response
    return "No response received."

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.thread_id = create_thread()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about ANSES retirement procedures:"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        # Add message to the thread
        add_message(st.session_state.thread_id, prompt)

        # Create a run
        run_response = create_run(st.session_state.thread_id, retirement_assistant_id)

        if run_response:
            # Retrieve the Assistant's response message
            response_message = get_assistant_response(st.session_state.thread_id, run_response.id)

            # Format and display the Assistant's response
            formatted_response = format_response(response_message)
            if formatted_response != "No response received.":
                st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                with st.chat_message("assistant"):
                    st.markdown(formatted_response)
            else:
                st.error("No response received from the assistant. Please try again.")
        else:
            st.error("Failed to create a run. Please try again.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error(traceback.format_exc())

# Add some context about ANSES retirement procedures
st.sidebar.markdown("""
## ANSES Retirement Procedures

This assistant can help you with information about:

- How to start your retirement process
- Required documentation
- Eligibility criteria
- Types of retirement benefits

For official information, please visit [ANSES Retirement and Pensions](https://www.anses.gob.ar/jubilaciones-y-pensiones).
""")
