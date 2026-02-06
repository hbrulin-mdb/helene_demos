# Desxcription
## Tools
Two tools for our AI agents : 
- vector search
- col find

To create tools, we use langchain's tool decorator : @tool -> makes the tol available to the agent along wiht tool metadata. 

to give the tools to the prompt (to inform the model of its available tools), we use langchain's partial. 

## State
To add state to the agent, use a graph data structure -> to represent complex relationship, incorporate conditional logic, model cyclical processes, offer flexibility, provide clear visual representation. 
-> langgraph is a framework for AI agents, it allos us to create a cyclical graph, where info can flow in loops. perfect to build agent that take complex deicisons or engage in multi-term reasoning. 

Within an app using langgraph state is implemented through a shared graph that represents the current snapshot of your app as it progresses through the steps of execution. It tracks the information flowing through your graph workflow, while memory rfers to the storage that can persist state for your current sessions or extend across multiple sessions/conversations. 

state allows the agent to handle more complex queries, by properly sequencing tool usage and reasoning steps. 
then we persist that agent's state using mongodb and memory store. 

the state graph contains : 
- the schema of the graph
- reducer functions inform how the state will be updated

## Memory
Agents have different type fo memory : 
- short term : storage of info relevant for immediate use, within a single interaction or session ("what about the first option?)
- long term : storing info across multiple interactions or sessions -> user preferences, previous, conv, records of actions

in this app we use langgraph's checkpointer API utilizing mongodb to store the memory. Within langgraph, a checkpointer captures the state of the graph at each ietration of the nodes. the checkpointer automatically creates a mdb db with the checkpoints. the documents in this coll store conv history and agent state.

the checkpointer utilizes a threadID, or session ID. it is hardcoded here, for demo purposes, but in prod it would be a generated session ID when the person logs in. 

In this app we implement short term memory, with same session id 

# create a key_param.py file and write
```py
mongodb_uri = ""
openai_api_key = ""
```

# Activate venv & install dependencies
uv venv
source .venv/bin/activate
uv pip install -r pyproject.toml

# Run
python3 main.py


