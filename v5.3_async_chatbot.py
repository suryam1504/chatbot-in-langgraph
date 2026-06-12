# converting previous synchronus chatbot to asynchronous chatbot

# first of all, here's now async and await keywords simply work in python

import asyncio
from unittest import result

async def func():
    print("Hello!")
    await asyncio.sleep(2)  # Pause for 2 second without blocking
    print("Geeks for Geeks") 

asyncio.run(func())

# Hello!
# Geeks for Geeks

# there was a 2 sec wait here

# Running Multiple Tasks Simultaneously
# With the help of async, multiple tasks can run without waiting for one to finish before starting another.

async def task1():
    print("Task 1 started")
    await asyncio.sleep(3)
    print("Task 1 finished")

async def task2():
    print("Task 2 started")
    await asyncio.sleep(1)
    print("Task 2 finished")

async def main():
    await asyncio.gather(task1(), task2())  # Runs both tasks together

asyncio.run(main())

# Hello!
# Geeks for Geeks
# Task 1 started
# Task 2 started
# Task 2 finished
# Task 1 finished

# In this code, task1() and task2() run at the same time because they are defined as async functions.
# task2() completes first because it waits for only 1 second, while task1() waits for 3 seconds.




# Now lets write async chatbot by copy pasting previous code and adding async/await keywords with comments on wherever i make a change from the previous code


# imports as usual
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import asyncio # one more import

load_dotenv()

llm = ChatOpenAI(model='gpt-4o-mini')

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}
        
        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}
    
tools = [calculator]

llm_with_tools = llm.bind_tools(tools)

#state
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# now we assign the task of building a graph to another function, and to make a langgraph code async, we need to make its node's executions async

def build_graph():

    async def chat_node(state: ChatState):
        messages = state['messages']
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools) # ToolNode is already async compatible, so no changes needed here

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tool_node", tool_node)

    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", 
                                tools_condition,  
                                {"tools": "tool_node", END: END})

    graph.add_edge("tool_node", "chat_node") 

    chatbot = graph.compile()

    return chatbot

# async main function, and notice the .ainvoke instead of .invoke
async def main():
    chatbot = build_graph()
    # running graph
    result = await chatbot.ainvoke({'messages': [HumanMessage(content="Find the sum of 5 and 3 using the calculator tool and answer as a pirate.")]})
    print(result['messages'][-1].content)

if __name__ == '__main__':
    asyncio.run(main())


# Arrr matey! The sum of 5 and 3 be 8! Yarrr! 🏴‍☠️

# ok so everything's working. Now we will remove this tool code and write an MCP client. Before, let's just rewrite the math MCP server from Learning-MCP repo in this project too.