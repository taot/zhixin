from pydantic import BaseModel
from typing import List

from crewai import Agent, Task
from crewai_tools import SerperDevTool

class ResearchFindings(BaseModel):
    main_points: List[str]
    key_technologies: List[str]
    future_predictions: str

# Create an agent
researcher = Agent(
    role="AI Technology Researcher",
    goal="Research the latest AI developments",
    backstory="""You're a meticulous analyst with a keen eye for detail. You're known for
your ability to turn complex data into clear and concise reports, making
it easy for others to understand and act on the information you provide.""",
    # tools=[SerperDevTool()],
    verbose=True
)

# Use kickoff() to interact directly with the agent
result = researcher.kickoff(
    "What are the latest developments in language models?",
    response_format=ResearchFindings
)

# Access the raw response
print(result.pydantic)
