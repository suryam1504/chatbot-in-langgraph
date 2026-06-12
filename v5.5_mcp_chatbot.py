# removing tools code and writing mcp client and connecting with mcp server

from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import asyncio 
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

llm = ChatOpenAI(model='gpt-4o-mini')

# MCP client for local FastMCP server running math tools
client = MultiServerMCPClient(
    {
        "arith": {
            "transport": "stdio",
            "command": "python3",
            "args": ["/Users/suryamgupta/Documents/chatbot-in-langgraph/v5.4_mcp_math_server/main.py"],
        }
    }
)

# @tool
# def calculator(first_num: float, second_num: float, operation: str) -> dict:
#     """
#     Perform a basic arithmetic operation on two numbers.
#     Supported operations: add, sub, mul, div
#     """
#     try:
#         if operation == "add":
#             result = first_num + second_num
#         elif operation == "sub":
#             result = first_num - second_num
#         elif operation == "mul":
#             result = first_num * second_num
#         elif operation == "div":
#             if second_num == 0:
#                 return {"error": "Division by zero is not allowed"}
#             result = first_num / second_num
#         else:
#             return {"error": f"Unsupported operation '{operation}'"}
        
#         return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
#     except Exception as e:
#         return {"error": str(e)}
    
# tools = [calculator]

# llm_with_tools = llm.bind_tools(tools)

#state
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# now we assign the task of building a graph to another function, and to make a langgraph code async, we need to make its node's executions async

async def build_graph():

    # get tools from the server
    tools = await client.get_tools()
    llm_with_tools = llm.bind_tools(tools)

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
    chatbot = await build_graph()
    # running graph
    result = await chatbot.ainvoke({'messages': [HumanMessage(content="Find the sum of 5 and 3 using the calculator tool and answer as a pirate.")]})
    print(result['messages'][-1].content)

if __name__ == '__main__':
    asyncio.run(main())

# Arrr, matey! The treasure ye seek be the sum of 5 and 3, which be 8! 🏴‍☠️✨

# Ok so connecting to server is working properly, great!