from crewai.knowledge.source.crew_docling_source import CrewDoclingSource

def get_source(file_paths):
    return CrewDoclingSource(file_paths=file_paths)
