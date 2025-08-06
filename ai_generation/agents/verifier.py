from crewai import Agent
from tools.file_tools import read_file, list_files

def get_verifier_agent(llm):
    return Agent(
        role="Code Verifier",
        goal="Verify generated code matches requirements",
        backstory="Quality assurance expert using granite3.3:2b for precise verification. Uses absolute paths to ensure file access.",
        llm=llm,  # Expects granite3.3:2b with increased context
        tools=[read_file, list_files],
        verbose=True,
        allow_delegation=False,
        max_iter=15,  # Increased for thorough verification
        max_execution_time=600  # Extended timeout for verification process
    )