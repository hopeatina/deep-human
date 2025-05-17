# Human MCP Server

This is a base MCP (Machine Controlled Protocol) server for representing human personas. It provides tools, resources, and prompts for creating digital human representations that can interact with each other and facilitate matches.

## Features

- **Personal Profile**: Define interests, skills, goals, and services
- **Compatibility Analysis**: Calculate compatibility between humans based on shared interests and complementary skills
- **Conversation**: Engage in conversation with customizable style
- **Social Connection**: Add to close friends, invite to events
- **Startup Ideation**: Brainstorm startup ideas based on shared interests and complementary skills

## Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key
- FastMCP library

### Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

### Configuration

Each human persona is configured using a YAML file. Create a file (e.g., `your_name_config.yaml`) with the following structure:

```yaml
persona:
  name: "Your Name"
  bio: "A brief bio about yourself"
  location: "Your Location"
  timezone: "Your Timezone"
  style: "your conversational style"

conversation:
  prompt_template: |
    You are {name}, a person with [your description].
    You speak in a {style} voice.
    
    Conversation history:
    {history}
    
    Respond to this message: "{message}"
    
    [Additional instructions for conversation style]

matching:
  interest_weight: 0.4
  skill_weight: 0.4
  goal_weight: 0.2
  min_score_threshold: 0.6

startup_ideas:
  prompt_template: |
    [Your custom prompt for generating startup ideas]

llm:
  provider: "openai"
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 500
```

### Running the Server

1. Run the server with your configuration:

```bash
python server.py --config your_name_config.yaml
```

2. By default, the server will use the STDIO transport. For HTTP transport:

```bash
python server.py --config your_name_config.yaml --transport http --host 127.0.0.1 --port 8000
```

## Creating 1v1 Conversations

To create a conversation between two MCP servers:

1. Start two servers with different configurations
2. Use an MCP client to connect to both servers
3. Pass messages between them using the `converse` tool
4. Use the compatibility tools to analyze the match potential

## Architecture

The server uses FastMCP for handling MCP protocol interactions. Key components:

- **Tools**: Functions that provide capabilities (e.g., get_interests, compatibility_score)
- **Resources**: Data accessible through URIs (e.g., profile://interests)
- **Prompts**: Templates for generating responses based on the human's personality

## Customization

You can customize:

- **Profile Data**: Modify the default interests, skills, goals, and services
- **Prompt Templates**: Change how the server generates responses
- **Compatibility Metrics**: Adjust weights for different factors in compatibility scoring
- **LLM Settings**: Change the model, temperature, and token limit

## Example Configurations

We've included example configurations:

- `hope_config.yaml`: Technology-focused persona with emphasis on human connections
- (Add your own examples here)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request 