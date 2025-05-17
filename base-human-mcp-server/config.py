import os
import yaml
from typing import Dict, List, Any, Optional


class HumanConfig:
    """
    Configuration for a Human MCP server.
    Each person can customize their own instance by providing a YAML file.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize with a config file path or use environment variables.

        Args:
            config_file: Path to YAML configuration file
        """
        # Default configuration
        self.config = {
            "persona": {
                "name": "Default User",
                "bio": "No bio provided",
                "location": "Unknown",
                "timezone": "UTC",
                "style": "friendly and informative",
            },
            "conversation": {
                "prompt_template": """You are {name}. You speak in a {style} voice.
                
Conversation history:
{history}

Respond to this message: "{message}"

Keep your response authentic to your personality. Be engaging but concise.""",
                "max_history": 5,
            },
            "matching": {
                "interest_weight": 0.4,
                "skill_weight": 0.4,
                "goal_weight": 0.2,
                "min_score_threshold": 0.6,
            },
            "startup_ideas": {
                "prompt_template": """Generate 3-5 innovative startup ideas based on these shared interests and complementary skills:

Shared Interests: {interests}
My Key Skills: {my_skills}
Their Key Skills: {their_skills}

For each idea, include:
1. A catchy name
2. A brief description of the concept
3. A clear value proposition
4. How it leverages our combined skills and interests

Focus on ideas that would be genuinely exciting and feasible given our skillsets.""",
                "num_ideas": 3,
            },
            "paths": {
                "interests_file": "data/interests.json",
                "skills_file": "data/skills.json",
                "goals_file": "data/goals.json",
                "services_file": "data/services.json",
                "close_friends_file": "data/close_friends.json",
                "invites_file": "data/invites.json",
                "conversation_file": "data/conversations.json",
            },
            "llm": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 500,
            },
        }

        # Load config from file if provided
        if config_file and os.path.exists(config_file):
            self._load_from_yaml(config_file)

        # Override with environment variables
        self._load_from_env()

    def _load_from_yaml(self, config_file: str) -> None:
        """Load configuration from a YAML file."""
        try:
            with open(config_file, "r") as f:
                yaml_config = yaml.safe_load(f)

            # Update nested dictionaries
            self._deep_update(self.config, yaml_config)
        except Exception as e:
            print(f"Error loading config from {config_file}: {str(e)}")

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Load persona details
        if os.environ.get("HUMAN_NAME"):
            self.config["persona"]["name"] = os.environ.get("HUMAN_NAME")
        if os.environ.get("HUMAN_BIO"):
            self.config["persona"]["bio"] = os.environ.get("HUMAN_BIO")
        if os.environ.get("HUMAN_LOCATION"):
            self.config["persona"]["location"] = os.environ.get("HUMAN_LOCATION")
        if os.environ.get("HUMAN_TIMEZONE"):
            self.config["persona"]["timezone"] = os.environ.get("HUMAN_TIMEZONE")
        if os.environ.get("HUMAN_STYLE"):
            self.config["persona"]["style"] = os.environ.get("HUMAN_STYLE")

        # Load LLM settings
        if os.environ.get("LLM_PROVIDER"):
            self.config["llm"]["provider"] = os.environ.get("LLM_PROVIDER")
        if os.environ.get("LLM_MODEL"):
            self.config["llm"]["model"] = os.environ.get("LLM_MODEL")
        if os.environ.get("LLM_TEMPERATURE"):
            self.config["llm"]["temperature"] = float(os.environ.get("LLM_TEMPERATURE"))
        if os.environ.get("LLM_MAX_TOKENS"):
            self.config["llm"]["max_tokens"] = int(os.environ.get("LLM_MAX_TOKENS"))

        # Load matching weights
        if os.environ.get("MATCH_INTEREST_WEIGHT"):
            self.config["matching"]["interest_weight"] = float(
                os.environ.get("MATCH_INTEREST_WEIGHT")
            )
        if os.environ.get("MATCH_SKILL_WEIGHT"):
            self.config["matching"]["skill_weight"] = float(
                os.environ.get("MATCH_SKILL_WEIGHT")
            )
        if os.environ.get("MATCH_GOAL_WEIGHT"):
            self.config["matching"]["goal_weight"] = float(
                os.environ.get("MATCH_GOAL_WEIGHT")
            )

        # Load file paths
        for key in self.config["paths"]:
            env_key = f"PATH_{key.upper()}"
            if os.environ.get(env_key):
                self.config["paths"][key] = os.environ.get(env_key)

    def _deep_update(self, original: Dict, update: Dict) -> None:
        """Recursively update nested dictionaries."""
        for key, value in update.items():
            if (
                key in original
                and isinstance(original[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(original[key], value)
            else:
                original[key] = value

    def get(self, section: str, key: Optional[str] = None) -> Any:
        """
        Get a configuration value.

        Args:
            section: The configuration section
            key: The specific key (if None, returns the whole section)

        Returns:
            The configuration value or section
        """
        if section not in self.config:
            return None

        if key is None:
            return self.config[section]

        if key not in self.config[section]:
            return None

        return self.config[section][key]

    def get_persona_name(self) -> str:
        """Get the persona name."""
        return self.config["persona"]["name"]

    def get_persona_style(self) -> str:
        """Get the persona conversation style."""
        return self.config["persona"]["style"]

    def get_conversation_prompt(
        self, name: str, style: str, message: str, history: str
    ) -> str:
        """Get the formatted conversation prompt."""
        template = self.config["conversation"]["prompt_template"]
        return template.format(name=name, style=style, message=message, history=history)

    def get_startup_ideas_prompt(
        self, interests: str, my_skills: str, their_skills: str
    ) -> str:
        """Get the formatted startup ideas prompt."""
        template = self.config["startup_ideas"]["prompt_template"]
        return template.format(
            interests=interests, my_skills=my_skills, their_skills=their_skills
        )

    def get_matching_weights(self) -> Dict[str, float]:
        """Get the weights used for compatibility matching."""
        return {
            "interest": self.config["matching"]["interest_weight"],
            "skill": self.config["matching"]["skill_weight"],
            "goal": self.config["matching"]["goal_weight"],
        }

    def get_file_path(self, key: str) -> str:
        """Get a file path from the configuration."""
        return self.config["paths"].get(key, f"data/{key}.json")

    def get_llm_config(self) -> Dict[str, Any]:
        """Get the LLM configuration."""
        return self.config["llm"]
