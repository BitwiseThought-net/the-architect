import os
import subprocess
from crewai import (
    Agent as NativeAgent,
    Task as NativeTask,
    Crew as NativeCrew,
    Process as NativeProcess,
    LLM as NativeLLM
)
from crewai.tools import tool as native_tool

# Import stable native tools to satisfy core framework dependencies
from crewai_tools import (
    FileReadTool as NativeFileReadTool,
    FileWriterTool as NativeFileWriterTool,
    DuckDuckGoSearchTool as NativeDuckDuckGoSearchTool
)

# Import explicit knowledge source classes utilized by your loaders/ directory
from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource
from crewai.knowledge.source.crew_docling_source import CrewDoclingSource
from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource
from crewai.knowledge.source.excel_knowledge_source import ExcelKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.xml_knowledge_source import XMLKnowledgeSource

# --- CORE BINDINGS ---
Agent = NativeAgent
Task = NativeTask
Crew = NativeCrew
Process = NativeProcess
LLM = NativeLLM
tool = native_tool

# --- TOOL BINDINGS ---
FileReadTool = NativeFileReadTool
FileWriterTool = NativeFileWriterTool
DuckDuckGoSearchTool = NativeDuckDuckGoSearchTool

# --- INLINE SECURE SHELL EXECUTION FALLBACK ---
# Re-maps raw subprocess utilities to a stable tool class to avoid library drift crashes
class NativeShellInterpreter:
    def __init__(self):
        self.name = "terminal_execution_tool"
        self.description = "Executes arbitrary shell commands inside the application workspace container environment."

    def _run(self, command: str) -> str:
        """Executes terminal parameters safely and returns output packages."""
        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            out = res.stdout if res.stdout else ""
            err = res.stderr if res.stderr else ""
            return f"Stdout: {out}\nStderr: {err}"
        except Exception as e:
            return f"Execution Failed: {str(e)}"

# Bind the stable inline executor class to the standard abstract token interface
EXECTool = NativeShellInterpreter

# --- KNOWLEDGE LOADER MAPPINGS ---
class Knowledge:
    CSV = CSVKnowledgeSource
    Docling = CrewDoclingSource
    JSON = JSONKnowledgeSource
    Excel = ExcelKnowledgeSource
    TextFile = TextFileKnowledgeSource
    XML = XMLKnowledgeSource
