import autogen

class LLM:
    def __init__(self, model, base_url, api_key, temperature=0.3, max_tokens=4096, **kwargs):
        self.model = model
        # AutoGen / LiteLLM integration mapping adjustment
        # If the model name doesn't start with ollama/, we ensure it maps cleanly
        self.model = model if model.startswith("ollama/") else f"ollama/{model}"
        self.base_url = base_url
        self.api_key = api_key
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)

class Agent:
    def __init__(self, role, goal, backstory, llm, tools=None, **kwargs):
        self.name = role.replace(" ", "_").replace("-", "_")

        # Build AutoGen-compliant configuration format matrix
        config_list = [{
            "model": llm.model,
            "api_key": llm.api_key,
            "base_url": llm.base_url,
            "temperature": llm.temperature,
            "max_tokens": llm.max_tokens
        }]

        self.native_instance = autogen.AssistantAgent(
            name=self.name,
            system_message=f"{backstory}\nYour structural goal is: {goal}",
            llm_config={"config_list": config_list}
        )
        self.tools = tools or []

class Task:
    def __init__(self, description, expected_output, agent, **kwargs):
        self.description = f"{description}\nExpected Return Output Format: {expected_output}"
        self.agent = agent

class Crew:
    def __init__(self, agents, tasks, verbose=True, **kwargs):
        self.agents = agents
        self.tasks = tasks
        self.verbose = verbose

    def kickoff(self):
        """Executes sequential task phases while mapping custom tools to AutoGen."""
        user_proxy = autogen.UserProxyAgent(
            name="Architect_Proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10, # Increased headroom for multi-turn tool calling loops
            code_execution_config=False    # We rely on our dedicated safe_terminal tools instead
        )

        # CRITICAL REFACTOR: Dynamically discover and register tools on the fly
        # before each individual task conversation begins.
        for task in self.tasks:
            agent = task.agent

            for tool_item in agent.tools:
                # Handle both native CrewAI tools and custom functions decorated with @tool
                func = getattr(tool_item, "_func", tool_item)
                name = getattr(tool_item, "name", getattr(func, "__name__", "custom_tool"))
                description = getattr(tool_item, "description", getattr(func, "__doc__", "Execute dynamic task"))

                if callable(func):
                    # AutoGen standard function registration signature
                    autogen.agentchat.register_function(
                        func,
                        caller=agent.native_instance, # Assistant suggests the tool call
                        executor=user_proxy,          # UserProxy executes the local code block
                        name=name,
                        description=description
                    )

            # Initiate sequential conversational handoff
            user_proxy.initiate_chat(agent.native_instance, message=task.description)

        return "AutoGen sequential sequence execution complete."

def tool(*args, **kwargs):
    """
    Unified decorator mapping custom framework tools to local functional schemas.
    Preserves raw functions so AutoGen can parse signatures natively.
    """
    def decorator(func):
        # Attach descriptor objects to mimic crewai tool metadata interface patterns
        func.name = kwargs.get("name", func.__name__)
        func.description = kwargs.get("description", func.__doc__ or "Execute structural task logic")
        func._func = func
        return func
    return decorator

# --- AGNOSTIC INTERFACE STUBS ---
# Prevents import errors across common knowledge loading layers when AutoGen is toggled on.
class Knowledge:
    CSV = object; Docling = object; JSON = object
    Excel = object; TextFile = object; XML = object

class DuckDuckGoSearchTool:
    def __init__(self, *args, **kwargs):
        # Placeholders mapping native searches to callable structures
        self.name = "duckduckgo_search"
        self.description = "Search the web for technical information"
    def _func(self, query: str) -> str:
        return "Web search is disabled when executing raw AutoGen loops."
