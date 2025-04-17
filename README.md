# MCP Siteflow

A Python-based MCP server that integrates with the Siteflow API, providing an easy-to-use command line interface for managing flows, phases, and steps.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- uv (Python package installer)
- A Siteflow account with API access (client ID and secret)
- Project ID from your Siteflow account

## Installation

1. Clone this repository or download the source code:

```bash
git clone https://github.com/aymbridge/mcp-siteflow-local
cd mcp-siteflow-local
```

2. Install FastMCP using uv:

```bash
uv pip install fastmcp
```

3. Install the other required dependencies:

```bash
pip install -r requirements.txt
```

Note: The `mcp` module is part of the `fastmcp` package, so only installing fastmcp is needed for MCP functionality.

## Environment Setup

This application uses environment variables to securely store your Siteflow API credentials. You need to create a `.env` file in the project root directory.

1. Create a `.env` file in the project root directory:

```bash
touch .env
```

2. Open the `.env` file in your preferred text editor and add the following variables:

```
SITEFLOW_CLIENT_ID=your_client_id_here
SITEFLOW_CLIENT_SECRET=your_client_secret_here
SITEFLOW_PROJECT_ID=your_project_id_here
SITEFLOW_FAMILY_ID=your_family_id_here  # Optional
```

Replace the placeholder values with your actual Siteflow API credentials.

## Running the MCP Server

To start the MCP server, run:

```bash
python mcp_siteflow.py
```

This will start the MCP server in the terminal, waiting for commands.

## Configuring with Claude Desktop

To use this MCP server with Claude Desktop, you need to add configuration details to Claude's MCP configuration file.

1. In Claude Desktop, navigate to Settings > Advanced Settings
2. Locate the MCP configuration section or file
3. Add the following configuration (adjust paths as needed):

```json
{
  "mcpServers": {
    "siteflow": {
      "command": "path/to/python3",
      "args": [
        "path/to/mcp_siteflow.py"
      ]
    }
  }
}
```

Replace `path/to/python3` with the actual path to your Python executable (e.g., `/usr/bin/python3` on Linux/macOS or `C:\\Python38\\python.exe` on Windows).

Replace `path/to/mcp_siteflow.py` with the absolute path to the `mcp_siteflow.py` file in your installation directory.

4. Restart Claude Desktop to apply the changes
5. You should now be able to access the Siteflow MCP commands directly from Claude Desktop

## Available Commands

The MCP server provides several commands for interacting with the Siteflow API:

- `authenticate`: Authenticate with the Siteflow API
- `get_flows`: List all available flows for your project
- `get_flow_phases`: Get all phases for a specific flow
- `add_phase_to_flow`: Add a new phase to a flow
- `add_step_to_phase`: Add a new step to a phase
- `create_flow`: Create a new flow
- `update_step_text`: Update the text content of a step

## Usage Examples

Here are some examples of how to use the MCP commands:

### Authenticate with the API

```
authenticate
```

### List all flows

```
get_flows
```

### Get phases for a flow

```
get_flow_phases flow_id=your_flow_id_here
```

### Create a new flow

```
create_flow flow_name="My New Flow" project_id=your_project_id_here
```

### Add a phase to a flow

```
add_phase_to_flow flow_id=your_flow_id_here phase_name="Setup Phase"
```

### Add a step to a phase

```
add_step_to_phase phase_id=your_phase_id_here step_name="Initial Setup"
```

### Update step text content

```
update_step_text step_id=your_step_id_here text_content="<p>Follow these instructions...</p>"
```

## Troubleshooting

- **Authentication Failures**: Make sure your client ID and secret are correct in the `.env` file
- **Permission Issues**: Verify that your API credentials have the necessary permissions in Siteflow
- **Project ID Errors**: Confirm that the project ID in your `.env` file exists and is accessible with your credentials

## Support

If you encounter any issues or have questions, please file an issue on the repository or contact the maintainers.

## License

[Specify license information here] 