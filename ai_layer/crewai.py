import os
import subprocess
import requests
from crewai import (
    Agent as NativeAgent,
    Task as NativeTask,
    Crew as NativeCrew,
    Process as NativeProcess,
    LLM as NativeLLM
)
from crewai.tools import tool as native_tool

# Import only the stable core file interaction tools
from crewai_tools import (
    FileReadTool as NativeFileReadTool,
    FileWriterTool as NativeFileWriterTool
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

# --- INLINE SECURE SHELL EXECUTION FALLBACK ---
class NativeShellInterpreter:
    def __init__(self):
        self.name = "terminal_execution_tool"
        self.description = "Executes arbitrary shell commands inside the application workspace container environment."

    def _run(self, command: str) -> str:
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

EXECTool = NativeShellInterpreter

# --- INLINE SECURE SEARCH FALLBACK ---
# Bypasses version mismatches by executing requests against DuckDuckGo's HTML fallback endpoint
class NativeDuckDuckGoSearch:
    def __init__(self):
        self.name = "duckduckgo_search"
        self.description = "Search the web for real-time technical documentation, requirements, and standards."

    def _run(self, query: str) -> str:
        """Executes an unauthenticated search query pass against the public index."""
        url = "duckduckgo.com"
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0"}
        try:
            response = requests.post(url, data={"q": query}, headers=headers, timeout=10)
            if response.status_code == 200:
                # Returns raw scraped context string elements for LLM semantic processing
                return response.text[:8000]
            return f"⚠️ Search index rejected query with status: {response.status_code}"
        except Exception as e:
            return f"❌ Search execution failed: {str(e)}"

DuckDuckGoSearchTool = NativeDuckDuckGoSearch

# --- KNOWLEDGE LOADER MAPPINGS ---
class Knowledge:
    CSV = CSVKnowledgeSource
    Docling = CrewDoclingSource
    JSON = JSONKnowledgeSource
    Excel = ExcelKnowledgeSource
    TextFile = TextFileKnowledgeSource
    XML = XMLKnowledgeSource
