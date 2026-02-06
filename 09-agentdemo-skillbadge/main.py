import key_param
from pymongo import MongoClient
from langchain_openai import ChatOpenAI
from state import execute_graph, init_graph
from tools import get_information_for_question_answering
from tools import get_page_content_for_summarization
import certifi
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def init_mongodb():
    """
    Initialize MongoDB client and collections.

    Returns:
        tuple: MongoDB client, vector search collection, full documents collection.
    """
    mongodb_client = MongoClient(key_param.mongodb_uri, tlsCAFile=certifi.where())
    
    DB_NAME = "ai_agents"
    
    vs_collection = mongodb_client[DB_NAME]["chunked_docs"]
    
    full_collection = mongodb_client[DB_NAME]["full_docs"]
    
    return mongodb_client, vs_collection, full_collection



def main():
    """
    Main function to initialize and execute the graph.
    """
    # Initialize MongoDB connections
    mongodb_client, vs_collection, full_collection = init_mongodb()
    
    # Initialize the ChatOpenAI model with API key
    llm = ChatOpenAI(openai_api_key=key_param.openai_api_key, temperature=0, model="gpt-4o")
    
    tools = [
        get_information_for_question_answering,
        get_page_content_for_summarization
    ]

    # Test the tools
    #answer = get_information_for_question_answering.invoke(
    #"What are some best practices for data backups in MongoDB?"
    #)
    #print("answer:" + answer)

    #summary = get_page_content_for_summarization.invoke("Create a MongoDB Deployment")
    #print("Summary:" + summary)
    
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "You are a helpful AI assistant."
                " You are provided with tools to answer questions and summarize technical documentation related to MongoDB."
                " Think step-by-step and use these tools to get the information required to answer the user query."
                " Do not re-run tools unless absolutely necessary."
                " If you are not able to get enough information using the tools, reply with I DON'T KNOW."
                " You have access to the following tools: {tool_names}."
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    
    bind_tools = llm.bind_tools(tools)
    
    llm_with_tools = prompt | bind_tools
    
    # Check tool calls via prompt
    #tool_call_check = llm_with_tools.invoke(["What are some best practices for data backups in MongoDB?"]).tool_calls
    #print("Tool call check:")
    #print(tool_call_check)

    tools_by_name = {tool.name: tool for tool in tools}
    
    app = init_graph(llm_with_tools, tools_by_name, mongodb_client)
    
    execute_graph(app, "1", "What are some best practices for data backups in MongoDB?")
    execute_graph(app, "1", "Give me a summary of the page titled Create a MongoDB Deployment")
    execute_graph(app, "1", "What did I just ask you?")
    

main()