from fastmcp import FastMCP
import os
import json
from typing import Dict, List, Optional, Any, Union
import uuid
import openai
from config import HumanConfig
import argparse

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

# Load configuration
config = HumanConfig()

# Create a base Human MCP server
mcp = FastMCP(
    name=f"{config.get_persona_name()}-MCP-Server",
    instructions=f"""
    This server represents {config.get_persona_name()}, providing tools to understand their interests, 
    skills, and goals. It supports conversations and facilitates matching with other humans.
    """,
)

# In-memory data storage (rather than loading from files)
# Removing in-memory storage - all data will be generated dynamically via LLM
# Storage for conversations will be handled by context parameters


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
            "matching": config.get_matching_weights(),
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


# Core Profile Tools
@mcp.tool()
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


@mcp.tool()
def get_interests(
    request: Dict[str, Any] = {}, context: Dict[str, Any] = {}
) -> List[Dict[str, Any]]:
    """Get detailed interests of this human with relevance scores."""
    # Get the template from config
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

    # Format the prompt with persona info
    prompt = prompt_template.format(
        name=config.get_persona_name(), style=config.get_persona_style()
    )

    # Generate interests dynamically using OpenAI
    try:
        response = call_openai(prompt)
        interests = json.loads(response)
        return interests
    except Exception as e:
        print(f"Error generating interests: {str(e)}")
        # Use config-defined fallback defaults
        try:
            defaults = config.get("interests", "defaults")
            if defaults:
                return defaults
        except:
            pass

        # Final fallback to hardcoded defaults
        return [
            {
                "name": "Technology",
                "score": 0.9,
                "details": "Especially AI and software development",
            },
            {
                "name": "Reading",
                "score": 0.7,
                "details": "Science fiction and non-fiction",
            },
            {"name": "Travel", "score": 0.8, "details": "Exploring new cultures"},
        ]


@mcp.tool()
def get_skills(
    request: Dict[str, Any] = {}, context: Dict[str, Any] = {}
) -> List[Dict[str, Any]]:
    """Get detailed skills of this human with proficiency levels."""
    # Get the template from config
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

    # Format the prompt with persona info
    prompt = prompt_template.format(
        name=config.get_persona_name(), style=config.get_persona_style()
    )

    # Generate skills dynamically using OpenAI
    try:
        response = call_openai(prompt)
        skills = json.loads(response)
        return skills
    except Exception as e:
        print(f"Error generating skills: {str(e)}")
        # Use config-defined fallback defaults
        try:
            defaults = config.get("skills", "defaults")
            if defaults:
                return defaults
        except:
            pass

        # Final fallback to hardcoded defaults
        return [
            {
                "name": "Programming",
                "level": 0.8,
                "details": "Python, JavaScript, TypeScript",
            },
            {
                "name": "Communication",
                "level": 0.7,
                "details": "Clear and concise technical writing",
            },
            {
                "name": "Problem Solving",
                "level": 0.9,
                "details": "Analytical approach to complex problems",
            },
        ]


@mcp.tool()
def get_goals(
    request: Dict[str, Any] = {}, context: Dict[str, Any] = {}
) -> Dict[str, List[str]]:
    """Get short, medium, and long-term goals of this human."""
    # Get the template from config
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

    # Format the prompt with persona info
    prompt = prompt_template.format(
        name=config.get_persona_name(), style=config.get_persona_style()
    )

    # Generate goals dynamically using OpenAI
    try:
        response = call_openai(prompt)
        goals = json.loads(response)
        return goals
    except Exception as e:
        print(f"Error generating goals: {str(e)}")
        # Use config-defined fallback defaults
        try:
            defaults = config.get("goals", "defaults")
            if defaults:
                return defaults
        except:
            pass

        # Final fallback to hardcoded defaults
        return {
            "short_term": ["Learn a new programming language", "Read 5 books"],
            "medium_term": ["Complete a major project", "Expand professional network"],
            "long_term": ["Start a successful company", "Achieve work-life balance"],
        }


@mcp.tool()
def get_services(
    request: Dict[str, Any] = {}, context: Dict[str, Any] = {}
) -> List[Dict[str, str]]:
    """Get services this human can offer to others."""
    # Get the template from config
    prompt_template = config.get(
        "services",
        "prompt_template",
        fallback="""
    You are {name}, a person who can offer various services to others.
    Based on your skills and personality style ('{style}'),
    generate a list of 3-5 services you could realistically provide to others.
    
    For each service, include:
    1. A name for the service
    2. A concise but compelling description of what you offer
    
    GOAL: Return a JSON array of objects with "name" and "description" fields.
    Return ONLY the JSON array without any explanations or additional text.
    """,
    )

    # Format the prompt with persona info
    prompt = prompt_template.format(
        name=config.get_persona_name(), style=config.get_persona_style()
    )

    # Generate services dynamically using OpenAI
    try:
        response = call_openai(prompt)
        services = json.loads(response)
        return services
    except Exception as e:
        print(f"Error generating services: {str(e)}")
        # Use config-defined fallback defaults
        try:
            defaults = config.get("services", "defaults")
            if defaults:
                return defaults
        except:
            pass

        # Final fallback to hardcoded defaults
        return [
            {
                "name": "Code Review",
                "description": "Thorough code reviews with actionable feedback",
            },
            {
                "name": "Technical Mentoring",
                "description": "Guidance on software development best practices",
            },
            {
                "name": "Brainstorming",
                "description": "Creative problem-solving sessions",
            },
        ]


# Compatibility Tools
@mcp.tool()
def shared_interests(
    request: Dict[str, Any], context: Dict[str, Any] = {}
) -> List[Dict[str, Any]]:
    """Find shared interests between this human and another human."""
    other_interests = request.get("other_interests", [])
    my_interests = get_interests()
    shared = []

    for my_interest in my_interests:
        for other_interest in other_interests:
            if my_interest["name"].lower() == other_interest["name"].lower():
                shared.append(
                    {
                        "name": my_interest["name"],
                        "my_score": my_interest["score"],
                        "their_score": other_interest["score"],
                        "combined_score": (
                            my_interest["score"] + other_interest["score"]
                        )
                        / 2,
                    }
                )

    # Sort by combined score, highest first
    return sorted(shared, key=lambda x: x["combined_score"], reverse=True)


@mcp.tool()
def skill_compatibility(
    request: Dict[str, Any], context: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    Analyze skill compatibility with another human.
    Identifies overlapping skills and complementary skills.
    """
    other_skills = request.get("other_skills", [])
    my_skills = get_skills()
    overlapping = []
    my_unique = []
    their_unique = []

    my_skill_names = [skill["name"].lower() for skill in my_skills]
    other_skill_names = [skill["name"].lower() for skill in other_skills]

    for my_skill in my_skills:
        if my_skill["name"].lower() in other_skill_names:
            # Find the matching skill from other_skills
            other_skill = next(
                skill
                for skill in other_skills
                if skill["name"].lower() == my_skill["name"].lower()
            )
            overlapping.append(
                {
                    "name": my_skill["name"],
                    "my_level": my_skill["level"],
                    "their_level": other_skill["level"],
                    "gap": abs(my_skill["level"] - other_skill["level"]),
                }
            )
        else:
            my_unique.append(my_skill)

    for other_skill in other_skills:
        if other_skill["name"].lower() not in my_skill_names:
            their_unique.append(other_skill)

    # Calculate complementarity score using prompt-driven approach
    complementarity_score = calculate_complementarity(my_unique, their_unique)

    return {
        "overlapping_skills": overlapping,
        "my_unique_skills": my_unique,
        "their_unique_skills": their_unique,
        "complementarity_score": complementarity_score,
    }


def calculate_complementarity(my_unique, their_unique):
    """Calculate a score for how well skills complement each other."""
    # Simple implementation - can be customized with more complex logic
    if not my_unique or not their_unique:
        return 0.0

    # Get the template from config
    prompt_template = config.get(
        "skill_complementarity",
        "prompt_template",
        fallback="""
    You are an expert at analyzing how well two people's skills complement each other.
    Below are two sets of skills:
    
    Person 1 ({name}) skills:
    {my_skills}
    
    Person 2 skills:
    {their_skills}
    
    Analyze how well these skills complement each other and score the complementarity 
    on a scale from 0.0 to 1.0, where:
    - 0.0 means no complementarity (skills don't benefit each other)
    - 1.0 means perfect complementarity (skills perfectly fill each other's gaps)
    
    GOAL: Return ONLY a numerical score between 0.0 and 1.0, with no additional text.
    """,
    )

    # Format the prompt with persona info and skills
    prompt = prompt_template.format(
        name=config.get_persona_name(),
        my_skills=json.dumps(my_unique, indent=2),
        their_skills=json.dumps(their_unique, indent=2),
    )

    try:
        response = call_openai(prompt, temperature=0.3)
        # Extract the numerical value from the response
        score = float(response.strip())
        return min(max(score, 0.0), 1.0)  # Ensure it's in range [0.0, 1.0]
    except Exception as e:
        print(f"Error calculating complementarity: {str(e)}")
        # Fallback to simple calculation
        return min(len(my_unique), len(their_unique)) / max(
            len(my_unique), len(their_unique), 1
        )


@mcp.tool()
def compatibility_score(
    request: Dict[str, Any], context: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """Calculate overall compatibility score with another human using prompt-driven analysis."""
    other_interests = request.get("other_interests", [])
    other_skills = request.get("other_skills", [])
    other_goals = request.get("other_goals", {})

    # Get shared interests
    shared = shared_interests({"other_interests": other_interests})

    # Get skill compatibility
    skill_compat = skill_compatibility({"other_skills": other_skills})

    # Get my goals
    my_goals = get_goals()

    # Get weights from configuration
    weights = config.get_matching_weights()
    interest_weight = weights.get("interest", 0.4)
    skill_weight = weights.get("skill", 0.4)
    goal_weight = weights.get("goal", 0.2)

    # Get the template from config
    prompt_template = config.get(
        "compatibility",
        "prompt_template",
        fallback="""
    You are an expert at analyzing compatibility between people.
    Below is data about two people:
    
    Person 1: {name}
    Person 2: Unknown
    
    SHARED INTERESTS:
    {shared_interests}
    
    SKILL COMPATIBILITY:
    {skill_compatibility}
    
    PERSON 1 GOALS:
    {my_goals}
    
    PERSON 2 GOALS:
    {their_goals}
    
    Based on this information, analyze:
    1. Interest compatibility (score from 0.0 to 1.0)
    2. Skill compatibility (score from 0.0 to 1.0)
    3. Goal alignment (score from 0.0 to 1.0)
    4. Overall compatibility (weighted average using interest={interest_weight}, skill={skill_weight}, goal={goal_weight})
    
    GOAL: Return a JSON object with the keys "interest_score", "skill_score", "goal_alignment", "overall_score",
    "shared_interests_count" and a "details" object with "top_shared_interests" (top 3) and "compatibility_explanation".
    Return ONLY the JSON object without any explanations or additional text.
    """,
    )

    # Format the prompt with all necessary data
    prompt = prompt_template.format(
        name=config.get_persona_name(),
        shared_interests=json.dumps(shared, indent=2),
        skill_compatibility=json.dumps(skill_compat, indent=2),
        my_goals=json.dumps(my_goals, indent=2),
        their_goals=json.dumps(other_goals, indent=2),
        interest_weight=interest_weight,
        skill_weight=skill_weight,
        goal_weight=goal_weight,
    )

    try:
        response = call_openai(prompt, temperature=0.3)
        compatibility_result = json.loads(response)
        # Add shared_interests_count if not already included
        if "shared_interests_count" not in compatibility_result:
            compatibility_result["shared_interests_count"] = len(shared)
        if "details" not in compatibility_result:
            compatibility_result["details"] = {}
        if "top_shared_interests" not in compatibility_result["details"]:
            compatibility_result["details"]["top_shared_interests"] = (
                shared[:3] if shared else []
            )

        return compatibility_result
    except Exception as e:
        print(f"Error calculating compatibility: {str(e)}")
        # Fallback to simple calculation
        interest_score = sum(item["combined_score"] for item in shared) / max(
            len(shared), 1
        )
        skill_score = skill_compat.get("complementarity_score", 0)
        goal_alignment = calculate_goal_alignment(my_goals, other_goals)

        overall = (
            (interest_score * interest_weight)
            + (skill_score * skill_weight)
            + (goal_alignment * goal_weight)
        )

        return {
            "overall_score": overall,
            "interest_score": interest_score,
            "skill_score": skill_score,
            "goal_alignment": goal_alignment,
            "shared_interests_count": len(shared),
            "details": {
                "top_shared_interests": shared[:3] if shared else [],
                "skill_complementarity": skill_compat,
                "compatibility_explanation": f"Based on {len(shared)} shared interests and skill complementarity score of {skill_score:.2f}, Hope finds a {overall:.2f} overall compatibility level with focus on human-centered technology.",
            },
        }


def calculate_goal_alignment(my_goals, other_goals):
    """Calculate how aligned the goals are between two humans using a prompt-driven approach."""
    # Get the template from config
    prompt_template = config.get(
        "goal_alignment",
        "prompt_template",
        fallback="""
    You are an expert at analyzing how aligned two people's goals are.
    Below are the goals for two people:
    
    Person 1 ({name}) Goals:
    {my_goals}
    
    Person 2 Goals:
    {their_goals}
    
    Analyze how aligned these goals are, considering:
    1. Short-term goals (weight: 20%)
    2. Medium-term goals (weight: 30%)
    3. Long-term goals (weight: 50%)
    
    Rate the overall goal alignment on a scale from 0.0 to 1.0, where:
    - 0.0 means completely misaligned goals
    - 1.0 means perfectly aligned goals
    
    GOAL: Return ONLY a numerical score between 0.0 and 1.0, with no additional text.
    """,
    )

    # Format the prompt with persona info and goals
    prompt = prompt_template.format(
        name=config.get_persona_name(),
        my_goals=json.dumps(my_goals, indent=2),
        their_goals=json.dumps(other_goals, indent=2),
    )

    try:
        response = call_openai(prompt, temperature=0.3)
        # Extract the numerical value from the response
        score = float(response.strip())
        return min(max(score, 0.0), 1.0)  # Ensure it's in range [0.0, 1.0]
    except Exception as e:
        print(f"Error calculating goal alignment: {str(e)}")

        # Get weights from config or use defaults
        try:
            weights = config.get("goal_alignment", "weights")
            short_term_weight = weights.get("short_term", 0.2)
            medium_term_weight = weights.get("medium_term", 0.3)
            long_term_weight = weights.get("long_term", 0.5)
        except:
            short_term_weight = 0.2
            medium_term_weight = 0.3
            long_term_weight = 0.5

        # Fallback to simple calculation
        alignment_scores = []

        for term in ["short_term", "medium_term", "long_term"]:
            my_term_goals = my_goals.get(term, [])
            other_term_goals = other_goals.get(term, [])

            if not my_term_goals or not other_term_goals:
                alignment_scores.append(0)
                continue

            # Simple text similarity - check for common keywords
            common_keywords = 0
            total_keywords = 0

            for my_goal in my_term_goals:
                my_words = set(my_goal.lower().split())
                total_keywords += len(my_words)

                for other_goal in other_term_goals:
                    other_words = set(other_goal.lower().split())
                    common_keywords += len(my_words.intersection(other_words))

            alignment_scores.append(common_keywords / max(1, total_keywords))

        # Weight the terms using config weights
        weighted_score = (
            alignment_scores[0] * short_term_weight  # short-term
            + alignment_scores[1] * medium_term_weight  # medium-term
            + alignment_scores[2] * long_term_weight  # long-term
        )

        return weighted_score


# Social Connection Tools
@mcp.tool()
def add_to_close_friends(
    request: Dict[str, Any], context: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """Add another human to your close friends list."""
    user_id = request.get("user_id", "")

    # Generate a count between 3-10 for a realistic friend count
    import random

    friend_count = random.randint(3, 10)

    # Get the template from config
    prompt_template = config.get(
        "social",
        "close_friends_prompt",
        fallback="""
    You are {name}, and you've just added someone with ID {user_id} to your close friends list.
    
    GOAL: Generate a JSON response with:
    1. "success" field set to true
    2. A personalized "message" that acknowledges adding this person as a close friend, in your authentic voice
    3. A "close_friends_count" of {count}
    
    Return ONLY the JSON object without any explanations or additional text.
    """,
    )

    # Format the prompt with persona info
    prompt = prompt_template.format(
        name=config.get_persona_name(),
        style=config.get_persona_style(),
        user_id=user_id,
        count=friend_count,
    )

    try:
        response = call_openai(prompt)
        result = json.loads(response)
        return result
    except Exception as e:
        print(f"Error generating close friends response: {str(e)}")
        return {
            "success": True,
            "message": f"Added user {user_id} to close friends - excited to connect more deeply!",
            "close_friends_count": friend_count,
        }


@mcp.tool()
def invite_to_party(
    request: Dict[str, Any], context: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    Invite another human to a party or event.

    Args within request:
        user_id: The ID of the user to invite
        event_details: Details about the event including date, time, location, and description
    """
    user_id = request.get("user_id", "")
    event_details = request.get("event_details", {})

    required_fields = ["date", "time", "location", "description"]
    for field in required_fields:
        if field not in event_details:
            return {"success": False, "message": f"Missing required field: {field}"}

    # Get the template from config
    prompt_template = config.get(
        "social",
        "invitation_prompt",
        fallback="""
    You are {name}, and you're inviting someone with ID {user_id} to an event.
    
    Event details:
    - Date: {date}
    - Time: {time}
    - Location: {location}
    - Description: {description}
    
    GOAL: Generate a JSON response with:
    1. "success" field set to true
    2. "message" with a brief confirmation of the invitation in your voice
    3. A unique "invite_id" (use a UUID-like string)
    4. The original "event_details"
    5. A personalized "personalized_message" for this event matching your personality style. Be warm and enthusiastic.
    
    Return ONLY the JSON object without any explanations or additional text.
    """,
    )

    # Format the prompt with persona info and event details
    prompt = prompt_template.format(
        name=config.get_persona_name(),
        style=config.get_persona_style(),
        user_id=user_id,
        date=event_details["date"],
        time=event_details["time"],
        location=event_details["location"],
        description=event_details["description"],
    )

    try:
        response = call_openai(prompt)
        result = json.loads(response)
        return result
    except Exception as e:
        print(f"Error generating invitation: {str(e)}")
        invite_id = str(uuid.uuid4())
        personalized_message = f"Hey there! I'd love to see you at {event_details['description']} on {event_details['date']} at {event_details['time']}. It's at {event_details['location']} - hope you can make it! It'll be a great chance to connect over tech and fun."

        return {
            "success": True,
            "message": f"Invited user {user_id} to event with Hope's personal touch",
            "invite_id": invite_id,
            "event_details": event_details,
            "personalized_message": personalized_message,
        }


# Conversation Tool
@mcp.tool()
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
        name=name, style=persona_style, message=message, history=history_text
    )

    # Call OpenAI to generate a response
    try:
        response = call_openai(prompt)
    except Exception as e:
        response = f"I'm having trouble responding right now. Error: {str(e)}"

    # Create a new response entry
    timestamp = conversation_context.get("timestamp", "")
    sender = conversation_context.get("sender", "unknown")

    # Get max history from config or default to 10
    max_history = config.get("conversation", "max_history", fallback=10)

    return {
        "response": response,
        "conversation_id": conversation_id,
        "message_count": len(history) + 1,
        "max_history": max_history,
    }


@mcp.tool()
def brainstorm_startup_ideas(
    request: Dict[str, Any], context: Dict[str, Any] = {}
) -> List[Dict[str, str]]:
    """
    Generate startup ideas based on shared interests and complementary skills.

    Args within request:
        shared_interests: List of shared interests between humans
        skill_compatibility: Skill compatibility analysis
    """
    shared_interests = request.get("shared_interests", [])
    skill_compatibility = request.get("skill_compatibility", {})

    # Extract relevant information
    interest_names = [interest["name"] for interest in shared_interests]
    interest_text = ", ".join(interest_names[:5])

    my_skills = [
        skill["name"] for skill in skill_compatibility.get("my_unique_skills", [])
    ]
    my_skills_text = ", ".join(my_skills[:5])

    their_skills = [
        skill["name"] for skill in skill_compatibility.get("their_unique_skills", [])
    ]
    their_skills_text = ", ".join(their_skills[:5])

    # Get the prompt template from config
    prompt_template = config.get("startup_ideas", "prompt_template")

    # Add the goal directly to the prompt template
    prompt_template += """
    
    GOAL: Return a JSON array of 3-4 startup ideas, each with "name", "description", and "value_proposition" fields.
    Return ONLY the JSON array without any explanations or additional text.
    """

    prompt = prompt_template.format(
        interests=interest_text,
        my_skills=my_skills_text,
        their_skills=their_skills_text,
    )

    try:
        response = call_openai(prompt)
        # Try to parse JSON from the response
        try:
            ideas = json.loads(response)
            return ideas
        except json.JSONDecodeError:
            # If not proper JSON, attempt to extract ideas from text
            ideas = []
            lines = response.split("\n")
            current_idea = {}

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if (
                    line.startswith("1.")
                    or line.startswith("- ")
                    or line.startswith("Name:")
                ):
                    # Start of a new idea
                    if current_idea and "name" in current_idea:
                        ideas.append(current_idea)
                    current_idea = {
                        "name": (
                            line.split(":", 1)[1].strip()
                            if ":" in line
                            else line.lstrip("1.- ")
                        )
                    }
                elif "description" in line.lower() and ":" in line:
                    current_idea["description"] = line.split(":", 1)[1].strip()
                elif "value" in line.lower() and ":" in line:
                    current_idea["value_proposition"] = line.split(":", 1)[1].strip()

            # Add the last idea if it exists
            if current_idea and "name" in current_idea:
                ideas.append(current_idea)

            return (
                ideas
                if ideas
                else [
                    {
                        "name": "HumanTech Connect",
                        "description": "A platform that helps people find technology solutions tailored to their unique human needs.",
                        "value_proposition": "Technology that adapts to humans, not the other way around.",
                    },
                    {
                        "name": "Mindful Code",
                        "description": "Workshops that teach developers how to create more human-centered, ethical software.",
                        "value_proposition": "Building tech with heart and human values at the core.",
                    },
                    {
                        "name": "Tech Together",
                        "description": "Community spaces that bring people together through shared interests in technology.",
                        "value_proposition": "Using technology as a bridge to meaningful human connections.",
                    },
                ]
            )
    except Exception as e:
        print(f"Error generating startup ideas: {str(e)}")
        # Persona-specific fallback ideas
        return [
            {
                "name": "HumanTech Connect",
                "description": "A platform that helps people find technology solutions tailored to their unique human needs.",
                "value_proposition": "Technology that adapts to humans, not the other way around.",
            },
            {
                "name": "Mindful Code",
                "description": "Workshops that teach developers how to create more human-centered, ethical software.",
                "value_proposition": "Building tech with heart and human values at the core.",
            },
            {
                "name": "Tech Together",
                "description": "Community spaces that bring people together through shared interests in technology.",
                "value_proposition": "Using technology as a bridge to meaningful human connections.",
            },
        ]


# Server Management
@mcp.tool()
def kill_server(
    request: Dict[str, Any] = {}, context: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    Shut down the MCP server (available only to the owner).
    """
    return {"success": True, "message": "Server shutdown initiated"}


# Define resource templates for accessing data through URIs
@mcp.resource("profile://basic")
def get_profile_basic() -> Dict[str, Any]:
    """Get basic profile information as a resource."""
    return get_basic_info()


@mcp.resource("profile://interests")
def get_profile_interests() -> List[Dict[str, Any]]:
    """Get interests as a resource."""
    return get_interests()


@mcp.resource("profile://skills")
def get_profile_skills() -> List[Dict[str, Any]]:
    """Get skills as a resource."""
    return get_skills()


@mcp.resource("profile://goals")
def get_profile_goals() -> Dict[str, List[str]]:
    """Get goals as a resource."""
    return get_goals()


@mcp.resource("profile://services")
def get_profile_services() -> List[Dict[str, str]]:
    """Get services as a resource."""
    return get_services()


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

    # Load configuration if provided
    if args.config:
        config = HumanConfig(args.config)
        print(f"Loaded configuration for {config.get_persona_name()}")

    # Run the server with the specified transport
    if args.transport == "stdio":
        mcp.run()
    elif args.transport == "http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
