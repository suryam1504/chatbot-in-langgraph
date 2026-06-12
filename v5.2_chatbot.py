# First, here's a normal langgraph chatbot we have always worked with.

# In this case, it has access to one calculator tool.

from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

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

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tool_node", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", 
                            tools_condition,  
                            {"tools": "tool_node", END: END})

graph.add_edge("tool_node", "chat_node") 

chatbot = graph.compile()

result = chatbot.invoke({'messages': [HumanMessage(content="Find the sum of 5 and 3 using the calculator tool and answer as a pirate.")]})

print(result['messages'][-1].content)

# Arrr! The sum of 5 and 3 be 8, matey! Now let’s sail to the next treasure! 🏴‍☠️🍂



# So now the plan is: the tool that we have here, we will be replacing it with an MCP client which we will write, and this tool's code will be in the MCP server that we will write (essentially the mcp-math-demo-local server we made in the Learning-MCP repo), and then we will just connect the two.

# Now before writing MCP client, we will do something: the current code and functions are synchronous (everything runs step by step in sequential manner), but with these MCP clients and servers (also with FastMCP which is used to build these), these need to be asynchronous (i.e. they can run in parallel and not wait for each other to finish), so we will first convert this code to be asynchronous.

