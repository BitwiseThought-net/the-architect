import os
from crewai import (
    Agent as NativeAgent,
    Task as NativeTask,
    Crew as NativeCrew,
    Process as NativeProcess,
    LLM as NativeLLM
)
from crewai.tools import tool as native_tool

# Import native tools to satisfy tool refactoring requirements
from crewai_tools import (
    FileReadTool as NativeFileReadTool,
    FileWriterTool as NativeFileWriterTool,
    CodeInterpreterTool as NativeCodeInterpreterTool, # FIXED: Changed from EXECTool
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
# Expose core CrewAI primitives directly to the orchestrator factory layer
Agent = NativeAgent
Task = NativeTask
Crew = NativeCrew
Process = NativeProcess
LLM = NativeLLM
tool = native_tool

# --- TOOL BINDINGS ---
# Bind specific custom/standard tool classes to abstract interface tokens
FileReadTool = NativeFileReadTool
FileWriterTool = NativeFileWriterTool
EXECTool = NativeCodeInterpreterTool # FIXED: Aliased to maintain orchestrator compatibility
DuckDuckGoSearchTool = NativeDuckDuckGoSearchTool

# --- KNOWLEDGE LOADER MAPPINGS ---
# Centralize framework-specific imports inside a neat class mapping object
class Knowledge:
    CSV = CSVKnowledgeSource
    Docling = CrewDoclingSource
    JSON = JSONKnowledgeSource
    Excel = ExcelKnowledgeSource
    TextFile = TextFileKnowledgeSource
    XML = XMLKnowledgeSource
