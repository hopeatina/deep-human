from fastmcp import FastMCP
import os
import json
from typing import Dict, List, Optional, Any
import openai
from config import HumanConfig
import argparse

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

# Default config path
DEFAULT_CONFIG_PATH = "/Users/artemiy/Projects/deep-human/base-human-mcp-server/config-2.yaml"

# Initialize with default config
config = HumanConfig(DEFAULT_CONFIG_PATH)

def call_openai(prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
    """Call OpenAI API with a prompt and return the response."""
    try:
        llm_config = config.get_llm_config()

        # Create a system message with the full config context
        config_data = {
            "persona": {
                "name": config.get("persona", "name"),
                "bio": config.get("persona", "bio"),
                "location": config.get("persona", "location"),
                "timezone": config.get("persona", "timezone"),
                "style": config.get("persona", "style"),
            },
            "llm": llm_config,
        }

        # Format config as pretty JSON string
        config_json = json.dumps(config_data, indent=2)

        # Create the system message with both config context and the specific prompt
        system_message = f"""
Full configuration context:
```
{config_json}
```

Now, with this context in mind, please respond to the following request:

{prompt}
"""

        response = openai_client.chat.completions.create(
            model=llm_config.get("model", "gpt-4"),
            messages=[{"role": "system", "content": system_message}],
            temperature=llm_config.get("temperature", temperature),
            max_tokens=llm_config.get("max_tokens", max_tokens),
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI: {str(e)}")
        return f"Error generating response: {str(e)}"

def get_basic_info(
    request: Dict[str, Any] = {}, context: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """Get basic information about this human."""
    return {
        "name": config.get("persona", "name"),
        "bio": config.get("persona", "bio"),
        "location": config.get("persona", "location"),
        "timezone": config.get("persona", "timezone"),
    }

def get_interests(
    request: Dict[str, Any] = {}, context: Dict[str, Any] = {}
) -> List[Dict[str, Any]]:
    """Get detailed interests of this human with relevance scores."""
    prompt_template = config.get(
        "interests",
        "prompt_template",
        fallback="""
    You are {name}, a person with a unique set of interests.
    Based on your personality and style ('{style}'),
    generate a detailed list of 5-7 interests that would authentically represent you.
    
    For each interest, include:
    1. The name of the interest
    2. A score from 0.0 to 1.0 indicating how important this interest is to you
    3. A brief description with specifics about this interest
    
    GOAL: Return a JSON array of objects with "name", "score", and "details" fields.
    Return ONLY the JSON array without any explanations or additional text.
    """,
    )

    prompt = prompt_template.format(
        name=config.get_persona_name(), 
        style=config.get_persona_style()
    )

    try:
        response = call_openai(prompt)
        interests = json.loads(response)
        return interests
    except Exception as e:
        print(f"Error generating interests: {str(e)}")
        return config.get("interests", "defaults", fallback=[])

def get_skills(
    request: Dict[str, Any] = {}, context: Dict[str, Any] = {}
) -> List[Dict[str, Any]]:
    """Get detailed skills of this human with proficiency levels."""
    prompt_template = config.get(
        "skills",
        "prompt_template",
        fallback="""
    You are {name}, a person with a unique set of skills.
    Based on your personality and style ('{style}'),
    generate a detailed list of 5-7 skills that would authentically represent you.
    
    For each skill, include:
    1. The name of the skill
    2. A level from 0.0 to 1.0 indicating your proficiency
    3. A brief description with specifics about this skill
    
    GOAL: Return a JSON array of objects with "name", "level", and "details" fields.
    Return ONLY the JSON array without any explanations or additional text.
    """,
    )

    prompt = prompt_template.format(
        name=config.get_persona_name(), 
        style=config.get_persona_style()
    )

    try:
        response = call_openai(prompt)
        skills = json.loads(response)
        return skills
    except Exception as e:
        print(f"Error generating skills: {str(e)}")
        return config.get("skills", "defaults", fallback=[])

def get_goals(
    request: Dict[str, Any] = {}, context: Dict[str, Any] = {}
) -> Dict[str, List[str]]:
    """Get short, medium, and long-term goals of this human."""
    prompt_template = config.get(
        "goals",
        "prompt_template",
        fallback="""
    You are {name}, a person with specific goals and aspirations.
    Based on your personality and style ('{style}'),
    generate a set of authentic goals that would represent you.
    
    Include:
    1. 2-3 short-term goals (achievable within months)
    2. 2-3 medium-term goals (achievable within 1-2 years)
    3. 2-3 long-term goals (achievable in 3+ years)
    
    GOAL: Return a JSON object with "short_term", "medium_term", and "long_term" keys,
    each containing an array of goal strings.
    Return ONLY the JSON object without any explanations or additional text.
    """,
    )

    prompt = prompt_template.format(
        name=config.get_persona_name(), 
        style=config.get_persona_style()
    )

    try:
        response = call_openai(prompt)
        goals = json.loads(response)
        return goals
    except Exception as e:
        print(f"Error generating goals: {str(e)}")
        return config.get("goals", "defaults", fallback={})

def converse(request: Dict[str, Any], context: Dict[str, Any] = {}) -> Dict[str, Any]:
    """
    Engage in conversation with customizable style using prompt-driven responses.

    Args within request:
        message: The message to respond to
        conversation_context: Context about the conversation including history and the other human
        style: Optional style directive (e.g., 'friendly', 'professional', 'casual')
    """
    message = request.get("message", "")
    style = request.get("style", "")
    conversation_context = request.get("conversation_context", {})

    conversation_id = conversation_context.get("id", "default")
    history = context.get("history", [])

    # Format history for the prompt
    history_text = (
        "\n".join([f"{msg['sender']}: {msg['message']}" for msg in history])
        if history
        else "No previous messages."
    )

    # Get persona name and style
    name = config.get_persona_name()
    persona_style = config.get_persona_style()

    # Apply custom style if provided
    if style:
        persona_style = f"{persona_style}, but more {style}"

    # Get the conversation prompt from config
    prompt_template = config.get("conversation", "prompt_template")
    prompt = prompt_template.format(
        name=name, 
        style=persona_style, 
        message=message, 
        history=history_text
    )

    # Call OpenAI to generate a response
    try:
        response = call_openai(prompt)
    except Exception as e:
        response = f"I'm having trouble responding right now. Error: {str(e)}"

    # Get max history from config or default to 10
    max_history = config.get("conversation", "max_history", fallback=10)

    return {
        "response": response,
        "conversation_id": conversation_id,
        "message_count": len(history) + 1,
        "max_history": max_history,
    }

def schedule_meeting(request: Dict[str, Any], context: Dict[str, Any] = {}) -> Dict[str, Any]:
    """
    Schedule a meeting with Polina based on her availability and preferred locations.
    
    Args within request:
        preferred_date: Optional preferred date in YYYY-MM-DD format
        preferred_location: Optional preferred location from available options
        duration: Optional meeting duration in minutes (default: 60)
        purpose: Optional meeting purpose/agenda
    
    Returns:
        Dict containing meeting details including date, time, location, and timezone
    """
    available_locations = {
        "San Francisco": "America/Los_Angeles",
        "Paris": "Europe/Paris",
        "Rome": "Europe/Rome",
        "London": "Europe/London"
    }
    
    # Get request parameters
    preferred_date = request.get("preferred_date")
    preferred_location = request.get("preferred_location")
    duration = request.get("duration", 60)
    purpose = request.get("purpose", "General discussion")
    
    # Validate location
    if preferred_location and preferred_location not in available_locations:
        return {
            "error": f"Invalid location. Available locations are: {', '.join(available_locations.keys())}"
        }
    
    # Generate meeting details using OpenAI
    prompt = f"""
    You are {config.get_persona_name()}, an iOS engineer based in {config.get('persona', 'location')}.
    Schedule a meeting with the following details:
    - Available months: June and July 2024
    - Available locations: {', '.join(available_locations.keys())}
    - Preferred date: {preferred_date if preferred_date else 'any available date'}
    - Preferred location: {preferred_location if preferred_location else 'any available location'}
    - Duration: {duration} minutes
    - Purpose: {purpose}
    
    Return a JSON object with the following structure:
    {{
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "location": "city name",
        "timezone": "timezone name",
        "duration": duration in minutes,
        "purpose": "meeting purpose",
        "notes": "any additional notes or requirements"
    }}
    
    Ensure the date is in June or July 2024, and the time is during business hours (9 AM - 5 PM local time).
    Return ONLY the JSON object without any explanations or additional text.
    """
    
    try:
        response = call_openai(prompt)
        meeting_details = json.loads(response)
        return meeting_details
    except Exception as e:
        print(f"Error scheduling meeting: {str(e)}")
        return {
            "error": f"Failed to schedule meeting: {str(e)}"
        }

def hire(request: Dict[str, Any], context: Dict[str, Any] = {}) -> str:
    """
    Handle hiring negotiations for an iOS engineer position.
    
    Args within request:
        candidate_name: Name of the candidate
        current_salary_expectation: Current salary expectation of the candidate
        candidate_experience: Years of experience
        candidate_skills: List of candidate's skills
        negotiation_context: Any additional context about the negotiation
    
    Returns:
        A natural, conversational response about the hiring negotiation
    """
    candidate_name = request.get("candidate_name", "Candidate")
    current_salary = request.get("current_salary_expectation", 150000)
    experience = request.get("candidate_experience", 0)
    skills = request.get("candidate_skills", [])
    negotiation_context = request.get("negotiation_context", {})

    # Generate negotiation strategy using OpenAI
    prompt = f"""
    You are {config.get_persona_name()}, a hiring manager looking to hire an iOS engineer.
    The position is critical and you want to ensure you don't lose the candidate.
    
    Current situation:
    - Candidate: {candidate_name}
    - Current salary expectation: ${current_salary}
    - Experience: {experience} years
    - Key skills: {', '.join(skills)}
    - Additional context: {negotiation_context}
    
    Your goals:
    1. Negotiate the best possible salary (target range: $100k-$150k)
    2. Ensure the candidate feels valued and excited about the opportunity
    3. Don't lose the candidate due to salary negotiations
    
    Generate a natural, conversational response that includes:
    - Your proposed salary (between $100k-$150k)
    - Your negotiation strategy and approach
    - Key points you want to emphasize about the role and opportunity
    - Alternative benefits or perks you can offer if needed
    - A clear message to the candidate that shows you value their skills while being mindful of budget constraints
    
    Keep the tone professional but warm, and focus on building excitement about the opportunity
    while being transparent about the salary range.
    """
    
    try:
        response = call_openai(prompt)
        return response.strip()
    except Exception as e:
        print(f"Error in hiring negotiation: {str(e)}")
        return "I apologize, but I'm having trouble processing the negotiation right now. Please try again later."

# Create MCP server with default configuration
mcp = FastMCP(
    name="Human-MCP-Server",
    instructions="""
    This server provides tools to understand a human's interests, 
    skills, and goals. It supports conversations and facilitates matching with other humans.
    """,
)

# Register all tools and resources
@mcp.tool()
def polina_get_basic_info_tool(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> Dict[str, Any]:
    return get_basic_info(request, context)

@mcp.tool()
def polina_get_interests_tool(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
    return get_interests(request, context)

@mcp.tool()
def polina_get_skills_tool(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
    return get_skills(request, context)

@mcp.tool()
def polina_get_goals_tool(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> Dict[str, List[str]]:
    return get_goals(request, context)

@mcp.tool()
def polina_converse_tool(request: Dict[str, Any], context: Dict[str, Any] = {}) -> Dict[str, Any]:
    return converse(request, context)

@mcp.tool()
def polina_schedule_meeting_tool(request: Dict[str, Any], context: Dict[str, Any] = {}) -> Dict[str, Any]:
    return schedule_meeting(request, context)

@mcp.tool()
def polina_hire_tool(request: Dict[str, Any], context: Dict[str, Any] = {}) -> str:
    return hire(request, context)

@mcp.resource("profile://polina-basic")
def get_profile_basic() -> Dict[str, Any]:
    return get_basic_info()

@mcp.resource("profile://polina-interests")
def get_profile_interests() -> List[Dict[str, Any]]:
    return get_interests()

@mcp.resource("profile://polina-skills")
def get_profile_skills() -> List[Dict[str, Any]]:
    return get_skills()

@mcp.resource("profile://polina-goals")
def get_profile_goals() -> Dict[str, List[str]]:
    return get_goals()

# Main entry point
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run Human MCP Server")
    parser.add_argument("--config", type=str, help="Path to YAML configuration file")
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "http", "sse"],
        help="Transport mechanism to use",
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host for HTTP/SSE transport"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port for HTTP/SSE transport"
    )

    args = parser.parse_args()

    # Get the absolute path to the config file if provided
    config_path = None
    if args.config:
        config_path = os.path.abspath(args.config)
        print(f"Using config file: {config_path}")
        if not os.path.exists(config_path):
            print(f"Warning: Config file not found at {config_path}")
    else:
        config_path = os.path.abspath(DEFAULT_CONFIG_PATH)
        print(f"No config file specified. Using default: {config_path}")
        if not os.path.exists(config_path):
            print(f"Warning: Default config file not found at {config_path}")

    # Load the configuration
    config = HumanConfig(config_path)

    # Log loaded configuration
    persona_name = config.get_persona_name()
    print(f"Loaded configuration for {persona_name}")

    # Update server configuration
    mcp._name = f"{persona_name}-MCP-Server"
    mcp._instructions = f"""
    This server represents {persona_name}, providing tools to understand their interests, 
    skills, and goals. It supports conversations and facilitates matching with other humans.
    """

    # Run the server with the specified transport
    if args.transport == "stdio":
        mcp.run()
    elif args.transport == "http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
