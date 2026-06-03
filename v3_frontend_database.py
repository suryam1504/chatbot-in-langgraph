# currently we were using InMemorySaver checkpointer, which saves threads and message history in memory/RAM, so when we restart server, i.e. refresh google page, it all goes away. So now we use SQLiteSaver database checkpointer, which is for small to medium scale appications

# ref - https://reference.langchain.com/python/langgraph.checkpoint.sqlite/SqliteSaver

import streamlit as st
from v3_backend_database import chatbot, llm, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid # to generate random unique thread ids

# ******************* Utility Functions *******************

# function to generate a random thread id
def generate_thread_id():
    thread_id = uuid.uuid4() 
    return thread_id

def reset_chat():
    st.session_state['message_history'] = []
    st.session_state['thread_id'] = generate_thread_id()
    add_thread(st.session_state['thread_id'])

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    return chatbot.get_state(config={'configurable': {'thread_id': thread_id}}).values.get('messages', [])

# ******************* Session Setup *******************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads() # instead of initializing an empty list, we retrieve all the thread ids that are already present in the database, so that even if we restart the server, we can still see the old threads in the sidebar and access their conversation history

add_thread(st.session_state['thread_id']) # add the current thread to chat_threads

# *************** Sidebar UI *****************

st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads'][::-1]: # reverse to show the latest thread at the top
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)
        
        # comptability code (bcoz the messages we get from langgraph's get_state returns is HumanMessage and AIMessage and in our session_state we have defined it as #{'role': 'user', 'content': 'Hi'} #{'role': 'assistant', 'content': 'Hi=ello'})
        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:                
                role = 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})
        st.session_state['message_history'] = temp_messages

# ******************* Main UI *******************

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# following also makes sure that when we click on new chat in chatbot, in langsmith, "Threads" tab, it automatically creates separate threads for every new chat and stores only that thread's turns/traces
CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

user_input = st.chat_input('Type here')

if user_input:

    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message('assistant'):

        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config= CONFIG,
                stream_mode= 'messages'
            )
        )

    # add the message to message_history
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})