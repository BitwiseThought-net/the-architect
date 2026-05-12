import os
from typing import TypedDict, Annotated, Sequence, List
import requests

# LangGraph and LangChain imports are isolated purely to this factory connector file
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# --- STATE SCHEMA ---
class AgentState(TypedDict):
    """Internal structural state schema tracking the sequential mission loop data."""
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    current_task_index: int
    outputs: List[str]

# --- UNIFIED INTERFACE CLASSES ---
class LLM:
    def __init__(self, model, base_url, api_key, temperature=0.3, max_tokens=4096, **kwargs):
        # LangChain's ChatOpenAI requires custom models to bypass strict validation via model strings
        self.model_name = model if model.startswith("ollama/") else f"ollama/{model}"
        self.native_instance = ChatOpenAI(
            model=self.model_name,
            openai_api_base=base_url,
            openai_api_key=api_key,
            temperature=float(temperature),
            max_tokens=int(max_tokens)
        )

class Agent:
    def __init__(self, role, goal, backstory, llm, tools=None, **kwargs):
        self.role = role
        self.name = role.replace(" ", "_").replace("-", "_")
        self.goal = goal
        self.backstory = backstory
        self.llm = llm
        self.tools = tools or []

        # Build standard chat prompt structure compiling role identity metadata layers
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are a {role}.\nBackstory: {backstory}\nYour ultimate goal is: {goal}\n"
                       "If you have tools, call them when needed. Once you have finalized your work, "
                       "provide your clear and complete answer directly."),
            MessagesPlaceholder(variable_name="messages")
        ])

class Task:
    def __init__(self, description, expected_output, agent, **kwargs):
        self.description = description
        self.expected_output = expected_output
        self.agent = agent

class Crew:
    def __init__(self, agents, tasks, verbose=True, **kwargs):
        self.agents = agents
        self.tasks = tasks
        self.verbose = verbose

    def _create_node(self, task, task_idx: int):
        """Generates an internal execution node wrapper for a specific task step."""
        agent = task.agent
        # Bind the specific tools array schema natively to the LangChain model wrapper
        model_with_tools = agent.llm.native_instance.bind_tools(agent.tools) if agent.tools else agent.llm.native_instance

        def node_callable(state: AgentState):
            # Instruct the agent on its current explicit task instructions
            task_instruction = (
                f"CURRENT TASK ASSIGNMENT:\n{task.description}\n"
                f"EXPECTED OUTPUT FORMAT:\n{task.expected_output}\n"
                "Execute this task thoroughly based on your role context."
            )

            # Combine historical messages with the new task instruction
            current_messages = list(state["messages"]) + [HumanMessage(content=task_instruction)]

            # Invoke the model instance
            chain = agent.prompt | model_with_tools
            response = chain.invoke({"messages": current_messages})

            # LangGraph models require explicit name identification parameters on return message objects
            if isinstance(response, AIMessage):
                response.name = agent.name

            return {
                "messages": [response],
                "current_task_index": task_idx
            }
        return node_callable

    def kickoff(self):
        """Compiles and executes a dynamic LangGraph State Graph on the fly."""
        workflow = StateGraph(AgentState)
        all_tools = []

        # 1. Dynamically aggregate tools across the crew for unified execution routing
        for agent in self.agents:
            all_tools.extend(agent.tools)

        # Deduplicate tools based on names to prevent crash intersections
        unique_tools = {getattr(t, "name", getattr(t, "__name__", str(t))): t for t in all_tools}.values()
        tool_node = ToolNode(list(unique_tools)) if unique_tools else None

        if tool_node:
            workflow.add_node("tools", tool_node)

        # 2. Build and map task nodes inside the Graph layout matrix
        node_names = []
        for idx, task in enumerate(self.tasks):
            node_name = f"task_{idx}_{task.agent.name}"
            node_names.append(node_name)
            workflow.add_node(node_name, self._create_node(task, idx))

        # 3. Establish routing edges
        workflow.add_edge(START, node_names[0])

        for idx, current_node in enumerate(node_names):
            is_last = (idx == len(node_names) - 1)

            # Define conditional router execution path
            def router(state: AgentState):
                messages = state.get("messages", [])
                if not messages:
                    return "next"
                last_message = messages[-1]

                # Check if the LLM invoked a tool execution request hook
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    return "tools"
                return "next"

            # Create path mappings
            next_target = END if is_last else node_names[idx + 1]
            path_map = {"tools": "tools", "next": next_target}

            workflow.add_conditional_edges(current_node, router, path_map)

            # Map tools return connection straight back to the originating execution node
            if tool_node:
                workflow.add_edge("tools", current_node)

        # 4. Compile and Run the Graph layout architecture
        app = workflow.compile()
        initial_state = {
            "messages": [HumanMessage(content="Initialize Mission Workflow Engine.")],
            "current_task_index": 0,
            "outputs": []
        }

        final_output = app.invoke(initial_state)

        # Extract the final output message response slice
        messages = final_output.get("messages", [])
        if messages:
            return messages[-1].content
        return "LangGraph sequential workflow execution completed with an empty response layout."

def tool(*args, **kwargs):
    """
    Unified decorator wrapping custom local functions to LangChain tool primitives.
    Enables native parameter type validation inside LangGraph loops.
    """
    def decorator(func):
        from langchain_core.tools import tool as langchain_tool
        name = kwargs.get("name", func.__name__)
        description = kwargs.get("description", func.__doc__ or "Execute structural project logic")

        # Instantiate a native LangChain structured tool mapping signature schemas cleanly
        lc_tool = langchain_tool(func)
        lc_tool.name = name
        lc_tool.description = description
        return lc_tool
    return decorator

# --- AGNOSTIC CONNECTOR STUBS ---
class Knowledge:
    CSV = object; Docling = object; JSON = object
    Excel = object; TextFile = object; XML = object

class DuckDuckGoSearchTool:
    def __init__(self, *args, **kwargs):
        from langchain_community.tools import DuckDuckGoSearchRun
        # Re-map standard comunitary tools into matching names
        self.native_tool = DuckDuckGoSearchRun()
        self.name = "duckduckgo_search"
        self.description = "Search the web for technical documentation"
    def invoke(self, *args, **kwargs):
        return self.native_tool.invoke(*args, **kwargs)
