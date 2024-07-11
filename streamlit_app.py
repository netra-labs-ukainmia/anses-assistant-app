import streamlit as st
import os
from openai import OpenAI
import traceback

# Streamlit app title
st.title("ANSES Assistant")

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
            You are a highly specialized assistant created to provide information and guidance on {specialization}-related procedures and benefits offered by the National Social Security Administration (ANSES) in Argentina.
            """,
            model="gpt-4o",
            tools=[{"type": "file_search"}]
        )
        return assistant.id
    except Exception as e:
        st.error(f"Error creating assistant: {str(e)}")
        return None

# Create multiple Assistants
retirement_assistant_id = create_assistant("Retirement")
family_allowances_assistant_id = create_assistant("Family Allowances")
disability_assistant_id = create_assistant("Disability")

# Function to determine the appropriate Assistant
def determine_assistant(question):
    if "retirement" in question.lower():
        return retirement_assistant_id
    elif "family allowance" in question.lower():
        return family_allowances_assistant_id
    elif "disability" in question.lower():
        return disability_assistant_id
    else:
        return retirement_assistant_id

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
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        while run.status not in ["completed", "failed"]:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            st.write(f"Run status: {run.status}")

        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            for message in messages.data:
                if message.role == "assistant":
                    return message.content
        else:
            st.error("Run failed or was incomplete.")
            return None
    except Exception as e:
        st.error(f"Error getting assistant response: {str(e)}")
        return None

# Function to format the assistant's response
def format_response(response):
    if response:
        return "\n".join([content.text.value for content in response])
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
if prompt := st.chat_input("Ask a question about ANSES procedures and benefits:"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        # Determine the appropriate Assistant based on the user's question
        assistant_id = determine_assistant(prompt)

        # Add message to the thread
        add_message(st.session_state.thread_id, prompt)

        # Create a run
        run_response = create_run(st.session_state.thread_id, assistant_id)

        if run_response and hasattr(run_response, 'id'):
            # Retrieve the Assistant's response message
            response_message = get_assistant_response(st.session_state.thread_id, run_response.id)

            # Format and display the Assistant's response
            formatted_response = format_response(response_message)
            st.session_state.messages.append({"role": "assistant", "content": formatted_response})
            with st.chat_message("assistant"):
                st.markdown(formatted_response)
        else:
            st.error("Failed to create a run. Please try again.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error(traceback.format_exc())
