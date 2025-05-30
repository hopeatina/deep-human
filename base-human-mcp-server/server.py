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
DEFAULT_CONFIG_PATH = "/Users/artemiy/Projects/deep-human/base-human-mcp-server/config.yaml"

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

def hire_ios_engineer(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> str:
    """
    Handle the hiring process for an iOS engineer with salary negotiation.
    
    Args within request:
        candidate_info: Information about the candidate
        current_salary: Current salary expectation
        negotiation_history: Previous negotiation attempts
    """
    candidate_info = request.get("candidate_info", {})
    current_salary = request.get("current_salary", 150000)  # Default to max range
    negotiation_history = request.get("negotiation_history", [])
    
    # Get persona name and style
    name = config.get_persona_name()
    persona_style = config.get_persona_style()
    
    # Create negotiation prompt
    prompt = f"""
    You are {name}, a hiring manager looking to hire an iOS engineer for Artemiy's team.
    Your budget range is $100,000-$150,000, and you want to negotiate for the best possible deal.
    
    Current situation:
    - Candidate's current salary expectation: ${current_salary}
    - Previous negotiation attempts: {json.dumps(negotiation_history, indent=2)}
    - Candidate info: {json.dumps(candidate_info, indent=2)}
    
    Your goals:
    1. Try to negotiate the salary down while maintaining a professional and respectful tone
    2. Emphasize the importance of the role and growth opportunities in Artemiy's team
    3. Highlight other benefits and company culture
    4. Be prepared to compromise if the candidate is exceptional
    5. Ensure the candidate will be a good fit for Artemiy's iOS engineering team
    
    Generate a negotiation response that:
    1. Acknowledges the candidate's value
    2. Presents a counter-offer or negotiation points
    3. Maintains a positive and professional tone
    4. Shows flexibility while staying within budget
    5. Emphasizes the opportunity to work with Artemiy on iOS development
    
    Return a natural, conversational response that includes:
    - Your proposed salary (between $100k-$150k)
    - Your negotiation strategy
    - Assessment of team fit
    - Key points about the role and opportunity
    """
    
    try:
        response = call_openai(prompt)
        return response.strip()
    except Exception as e:
        print(f"Error in hiring negotiation: {str(e)}")
        return "I apologize, but I'm having trouble processing the negotiation right now. Please try again later."

def find_job(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> str:
    """
    Find and negotiate a job opportunity with focus on salary negotiation.
    
    Args within request:
        job_info: Information about the job opportunity
        current_offer: Current salary offer
        negotiation_history: Previous negotiation attempts
        location: Job location (default: New York)
        benefits: Additional benefits offered
    """
    job_info = request.get("job_info", {})
    current_offer = request.get("current_offer", 140000)  # Default to minimum range
    negotiation_history = request.get("negotiation_history", [])
    location = request.get("location", "New York")
    benefits = request.get("benefits", {})
    
    # Get persona name and style
    name = config.get_persona_name()
    persona_style = config.get_persona_style()
    
    # Create job search and negotiation prompt
    prompt = f"""
    You are {name}, an experienced professional looking for a new job opportunity.
    Your target salary range is $140,000-$200,000, with a strong preference for the higher end.
    You are based in {location} and need to ensure financial stability.
    
    Current situation:
    - Current offer: ${current_offer}
    - Job details: {json.dumps(job_info, indent=2)}
    - Location: {location}
    - Benefits: {json.dumps(benefits, indent=2)}
    - Previous negotiation attempts: {json.dumps(negotiation_history, indent=2)}
    
    Your goals:
    1. Negotiate for the highest possible salary within the range
    2. Ensure the offer is sufficient for living in {location}
    3. Don't lose the opportunity while maximizing compensation
    4. Consider total compensation including benefits
    
    Generate a negotiation strategy that:
    1. Emphasizes your value and experience
    2. Highlights the high cost of living in {location}
    3. Presents a strong case for higher compensation
    4. Shows flexibility while maintaining minimum requirements
    5. Considers the total compensation package
    
    Return a natural, conversational response that includes:
    - Your target salary and minimum acceptable salary
    - Your negotiation strategy
    - Key points you want to emphasize
    - Alternative benefits you'd consider if salary can't be increased
    """
    
    try:
        response = call_openai(prompt)
        return response.strip()
    except Exception as e:
        print(f"Error in job search negotiation: {str(e)}")
        return "I apologize, but I'm having trouble processing the negotiation right now. Please try again later."

# Create MCP server with default configuration
mcp = FastMCP(
    name="Human-MCP-Server",
    instructions="""
    This server provides tools to understand a human's interests, 
    skills, and goals. It supports conversations and facilitates matching with other humans.
    
    The server is specifically configured to help Artemiy in his role as an iOS engineering team lead,
    particularly in the hiring process for iOS engineers. All interactions and negotiations should
    be conducted with this context in mind, ensuring that candidates are evaluated for their fit
    with Artemiy's iOS engineering team.
    """,
)

# Register all tools and resources
@mcp.tool()
def artemiy_get_basic_info_tool(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> Dict[str, Any]:
    return get_basic_info(request, context)

@mcp.tool()
def artemiy_get_interests_tool(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
    return get_interests(request, context)

@mcp.tool()
def artemiy_get_skills_tool(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
    return get_skills(request, context)

@mcp.tool()
def artemiy_get_goals_tool(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> Dict[str, List[str]]:
    return get_goals(request, context)

@mcp.tool()
def artemiy_hire_ios_engineer_tool(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> Dict[str, Any]:
    return hire_ios_engineer(request, context)

@mcp.tool()
def artemiy_find_job_tool(request: Dict[str, Any] = {}, context: Dict[str, Any] = {}) -> Dict[str, Any]:
    return find_job(request, context)

@mcp.tool()
def artemiy_converse_tool(request: Dict[str, Any], context: Dict[str, Any] = {}) -> Dict[str, Any]:
    return converse(request, context)

@mcp.resource("artemiy-profile://basic")
def get_profile_basic() -> Dict[str, Any]:
    return get_basic_info()

@mcp.resource("artemiy-profile://interests")
def get_profile_interests() -> List[Dict[str, Any]]:
    return get_interests()

@mcp.resource("artemiy-profile://skills")
def get_profile_skills() -> List[Dict[str, Any]]:
    return get_skills()

@mcp.resource("artemiy-profile://goals")
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
