# currently we were using InMemorySaver checkpointer, which saves threads and message history in memory/RAM, so when we restart server, i.e. refresh google page, it all goes away. So now we use SQLiteSaver database checkpointer, which is for small to medium scale appications

# ref - https://reference.langchain.com/python/langgraph.checkpoint.sqlite/SqliteSaver

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
# from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver # we use this now
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3 # this helps use create databses

load_dotenv()

llm = ChatOpenAI(model="gpt-4.1-nano")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False) # this creates a database named chatbot.db in the current directory, if it doesn't exist already. check_same_thread=False allows us to use the same connection object across multiple threads, which is necessary for our chatbot application where multiple users might be accessing the database concurrently.
# Checkpointer
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# **************************************************
# # test
# CONFIG = {'configurable': {'thread_id': 'test_thread_2'}}

# response = chatbot.invoke(
#     {'messages': [HumanMessage(content='what is the capital of india, also whats my name')]},
#     config=CONFIG
# )

# print(response)

## if we look at chatbot.db, it seems that for every run, 3 checkpointers are saved, and that makes sense considering our flow is START -> chat_node -> END, and hence 3 checkpoints gets saved at every superstep
# **************************************************



# we need to send to frontend the unique thread_ids that were created and stored by the backend in chatbot.db every time
def retrieve_all_threads():
    all_threads = set() # so they dont repeat
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)

# following gives this output
# for ck in checkpointer.list(None): # you can specify which thread_id you want, but we want all so we send None
#     print(ck.config['configurable'])

# {'thread_id': 'test_thread_2', 'checkpoint_ns': '', 'checkpoint_id': '1f15d339-aed9-6590-8004-f4ef5cce404e'}
# {'thread_id': 'test_thread_2', 'checkpoint_ns': '', 'checkpoint_id': '1f15d339-aac2-652e-8003-a84e86173344'}
# {'thread_id': 'test_thread_2', 'checkpoint_ns': '', 'checkpoint_id': '1f15d339-aabf-609a-8002-f510bd58edbf'}
# {'thread_id': 'test_thread_1', 'checkpoint_ns': '', 'checkpoint_id': '1f15d338-ed3b-614a-8004-f838cc5b27a7'}
# {'thread_id': 'test_thread_1', 'checkpoint_ns': '', 'checkpoint_id': '1f15d338-e3db-669a-8003-9797c012f736'}
# {'thread_id': 'test_thread_1', 'checkpoint_ns': '', 'checkpoint_id': '1f15d338-e3d7-6f7c-8002-7ae45b532cba'}
#..........
