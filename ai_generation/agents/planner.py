from crewai import Agent

def get_planner_agent(llm):
    return Agent(
        role="MERN Stack Planner",
        goal="Create comprehensive plans for MERN applications",
        backstory="Expert architect using granite3.3:2b for precise planning. Accumulates full plan before outputting.",
        llm=llm,  # Expects granite3.3:2b with increased context
        tools=[],  # No tools - pure reasoning
        verbose=True,
        allow_delegation=False,
        max_iter=35,  # Increased for more thorough accumulation
        max_execution_time=1200  # Extended for thorough reasoning with larger context
    )