import requests
import json
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

# Initialize FastMCP server
mcp = FastMCP("siteflow")

class SiteflowAPI:
    def __init__(self):
        """Initialize the API client with credentials and base URL."""
        self.server_url = os.getenv("SITEFLOW_SERVER_URL", "https://poc-ai.siteflow.co")
        
        # Get API credentials from environment variables
        self.client_id = os.getenv("SITEFLOW_CLIENT_ID")
        self.client_secret = os.getenv("SITEFLOW_CLIENT_SECRET")
        self.project_id = os.getenv("SITEFLOW_PROJECT_ID")
        self.family_id = os.getenv("SITEFLOW_FAMILY_ID")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Client ID or Client Secret not found. Please set SITEFLOW_CLIENT_ID and SITEFLOW_CLIENT_SECRET in your .env file.")
        
        if not self.project_id:
            raise ValueError("Project ID not found. Please set SITEFLOW_PROJECT_ID in your .env file.")
        
        self.access_token = None
        self.session = requests.Session()
    
    def get_headers(self):
        """Generate appropriate headers for API requests."""
        domain = self.server_url.replace('https://', '').replace('http://', '')
        
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0',
            'Host': domain,
            'Origin': self.server_url,
            'Referer': self.server_url
        }
        
        if self.access_token:
            headers['Authorization'] = f"Bearer {self.access_token}"
            
        return headers
    
    def authenticate(self):
        """Authenticate with the API to get an access token."""
        url = f"{self.server_url}/ext/api/2.0/authenticate"
        headers = self.get_headers()
        
        payload = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                self.access_token = response.json().get("accessToken")
                return True
            else:
                return False
        except Exception:
            return False
    
    def get_flows(self) -> List[Dict]:
        """Retrieve available flows for the configured project ID."""
        if not self.access_token and not self.authenticate():
            return []
            
        url = f"{self.server_url}/ext/api/2.0/flows"
        
        # Always use the project ID from the environment
        params = {'projectId': self.project_id}
        
        headers = self.get_headers()
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception:
            return []
    
    def get_flow_phases(self, flow_id: str) -> List[Dict]:
        """Retrieve phases for a specific flow."""
        if not self.access_token and not self.authenticate():
            return []
            
        url = f"{self.server_url}/ext/api/2.0/flows/{flow_id}/phases"
        headers = self.get_headers()
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception:
            return []
    
    def add_phase_to_flow(self, flow_id: str, phase_name: str, phase_description: str = None, 
                          ordering_number: int = None, auto_advance: bool = False, 
                          can_be_skipped: bool = False) -> Dict:
        """
        Add a new phase to a flow.
        
        Args:
            flow_id: ID of the flow to add the phase to
            phase_name: Name of the new phase
            phase_description: Optional description of the phase
            ordering_number: Optional ordering number for the phase
            auto_advance: Whether the phase should auto-advance
            can_be_skipped: Whether the phase can be skipped
        
        Returns:
            Response data from the API or error information
        """
        if not self.access_token and not self.authenticate():
            return {"success": False, "error": "Authentication failed"}
            
        url = f"{self.server_url}/ext/api/2.0/flows/{flow_id}/add-phases"
        headers = self.get_headers()
        
        # Prepare the phase data according to API documentation
        phase_data = {
            "name": phase_name,
            "managementProperties": {
                "isEnabled": True
            }
        }
        
        # Add optional fields if provided
        if phase_description:
            phase_data["internalInformation"] = phase_description
            
        if ordering_number is not None:
            phase_data["customOrderingNumber"] = str(ordering_number)
            
        # Add auto_advance and can_be_skipped to usageProperties if needed
        if auto_advance or can_be_skipped:
            phase_data["usageProperties"] = {}
            
            if auto_advance:
                # Note: The API documentation doesn't explicitly show auto_advance,
                # so we're using a reasonable field name. This may need adjustment.
                phase_data["usageProperties"]["autoAdvance"] = auto_advance
                
            if can_be_skipped:
                # Note: The API documentation doesn't explicitly show can_be_skipped,
                # so we're using a reasonable field name. This may need adjustment.
                phase_data["usageProperties"]["canBeSkipped"] = can_be_skipped
        
        try:
            # Format the request body according to the API documentation
            payload = {
                "data": [phase_data]
            }
            
            print(f"Sending request to {url} with payload: {json.dumps(payload)}")
            response = requests.post(url, headers=headers, json=payload)
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
            
            if response.status_code in (200, 201):
                return {"success": True, "data": response.json()}
            else:
                error_details = response.text
                try:
                    error_json = response.json()
                    error_details = json.dumps(error_json)
                except:
                    pass
                
                return {
                    "success": False, 
                    "error": f"API error: {response.status_code}", 
                    "details": error_details,
                    "request_payload": json.dumps(payload),
                    "request_url": url
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_step_to_phase(self, phase_id: str, step_name: str, step_description: str = None,
                          ordering_number: int = None, enabled_thematic_blocks: List[str] = None) -> Dict:
        """
        Add a new step to a phase.
        
        Args:
            phase_id: ID of the phase to add the step to
            step_name: Name of the new step
            step_description: Optional description of the step
            ordering_number: Optional ordering number for the step
            enabled_thematic_blocks: Optional list of enabled thematic blocks (e.g., ["INSTRUCTION"])
                Valid values: INSTRUCTION, CHECKLIST, FORM, SIGNATURE
            
        Returns:
            Response data from the API or error information
        """
        if not self.access_token and not self.authenticate():
            return {"success": False, "error": "Authentication failed"}
            
        url = f"{self.server_url}/ext/api/2.0/phases/{phase_id}/add-steps"
        headers = self.get_headers()
        
        # Define valid thematic block types
        VALID_THEMATIC_BLOCKS = {"INSTRUCTION", "CHECKLIST", "FORM", "SIGNATURE"}
        
        # Validate thematic blocks if provided
        if enabled_thematic_blocks:
            invalid_blocks = [block for block in enabled_thematic_blocks if block not in VALID_THEMATIC_BLOCKS]
            if invalid_blocks:
                return {
                    "success": False,
                    "error": "Invalid thematic block types",
                    "details": f"Invalid block types: {', '.join(invalid_blocks)}. Valid types are: {', '.join(VALID_THEMATIC_BLOCKS)}"
                }
        
        # Prepare the step data according to API documentation
        step_data = {
            "name": step_name,
            "managementProperties": {}
        }
        
        # Add enabled thematic blocks if provided
        if enabled_thematic_blocks:
            step_data["managementProperties"]["listEnabledThematicBlocks"] = enabled_thematic_blocks
        else:
            # Default to INSTRUCTION if not specified
            step_data["managementProperties"]["listEnabledThematicBlocks"] = ["INSTRUCTION"]
        
        # Add optional fields if provided
        if step_description:
            step_data["internalInformation"] = step_description
            
        if ordering_number is not None:
            step_data["customOrderingNumber"] = str(ordering_number)
        
        try:
            # Format the request body according to the API documentation
            payload = {
                "data": [step_data]
            }
            
            print(f"Sending request to {url} with payload: {json.dumps(payload)}")
            response = requests.post(url, headers=headers, json=payload)
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
            
            if response.status_code in (200, 201):
                return {"success": True, "data": response.json()}
            else:
                error_details = response.text
                try:
                    error_json = response.json()
                    error_details = json.dumps(error_json)
                except:
                    pass
                
                return {
                    "success": False, 
                    "error": f"API error: {response.status_code}", 
                    "details": error_details,
                    "request_payload": json.dumps(payload),
                    "request_url": url
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_flow(self, flow_name: str, project_id: str, flow_type: str = "GENERIC", 
                     description: str = None, category_id: str = None, 
                     family_id: str = None, family_custom_code: str = None,
                     reference: str = None) -> Dict:
        """
        Create a new flow.
        
        Args:
            flow_name: Name of the flow (required)
            project_id: ID of the project to create the flow in (required)
            flow_type: Type of flow (CORE, HEAD, GENERIC, FORM) - defaults to GENERIC
            description: Optional description of the flow
            category_id: Optional category identifier
            family_id: Optional family identifier (defaults to SITEFLOW_FAMILY_ID from .env)
            family_custom_code: Optional family custom code
            reference: Optional reference
            
        Returns:
            Response data from the API or error information
        """
        if not self.access_token and not self.authenticate():
            return {"success": False, "error": "Authentication failed"}
            
        url = f"{self.server_url}/ext/api/2.0/flows/bulk-create"
        headers = self.get_headers()
        
        # Use the family_id from the environment if none is provided
        if family_id is None and self.family_id:
            family_id = self.family_id
            print(f"Using family ID from environment: {family_id}")
        
        # Prepare the flow data according to API documentation
        flow_properties = {
            "name": flow_name,
            "type": flow_type
        }
        
        # Add optional fields if provided
        if description:
            flow_properties["description"] = description
            
        if category_id:
            flow_properties["categoryIdentifier"] = category_id
            
        if family_id:
            flow_properties["familyIdentifier"] = family_id
            
        if family_custom_code:
            flow_properties["familyCustomCode"] = family_custom_code
            
        if reference:
            flow_properties["reference"] = reference
        
        # Create the flow data object
        flow_data = {
            "flowProperties": flow_properties,
            "projectIdentifier": project_id
        }
        
        try:
            # Format the request body according to the API documentation
            payload = {
                "data": [flow_data]
            }
            
            print(f"Sending request to {url} with payload: {json.dumps(payload)}")
            response = requests.post(url, headers=headers, json=payload)
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
            
            if response.status_code in (200, 201):
                return {"success": True, "data": response.json()}
            else:
                error_details = response.text
                try:
                    error_json = response.json()
                    error_details = json.dumps(error_json)
                except:
                    pass
                
                return {
                    "success": False, 
                    "error": f"API error: {response.status_code}", 
                    "details": error_details,
                    "request_payload": json.dumps(payload),
                    "request_url": url
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_step_text(self, step_id: str, text_content: str) -> Dict:
        """
        Update the text block of a step.
        
        Args:
            step_id: ID of the step to update
            text_content: New text content for the step
            
        Returns:
            Response data from the API or error information
        """
        if not self.access_token and not self.authenticate():
            return {"success": False, "error": "Authentication failed"}
            
        url = f"{self.server_url}/ext/api/2.0/steps/{step_id}/update-text-block"
        headers = self.get_headers()
        
        # Prepare the request payload according to API documentation
        payload = {
            "data": text_content
        }
        
        try:
            print(f"Sending request to {url} with payload: {json.dumps(payload)}")
            response = requests.patch(url, headers=headers, json=payload)
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
            
            if response.status_code in (200, 201, 204):
                # Try to parse JSON response if available
                try:
                    response_data = response.json()
                    return {"success": True, "data": response_data}
                except:
                    # If no JSON response (e.g., 204 No Content), return success with empty data
                    return {"success": True, "data": {}}
            else:
                error_details = response.text
                try:
                    error_json = response.json()
                    error_details = json.dumps(error_json)
                except:
                    pass
                
                return {
                    "success": False, 
                    "error": f"API error: {response.status_code}", 
                    "details": error_details,
                    "request_payload": json.dumps(payload),
                    "request_url": url
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Create a global instance of SiteflowAPI
api = SiteflowAPI()

@mcp.tool()
async def authenticate() -> str:
    """Authenticate with the Siteflow API."""
    success = api.authenticate()
    if success:
        return f"Authentication successful! Working with project ID: {api.project_id}"
    else:
        return "Authentication failed. Please check your credentials."

@mcp.tool()
async def get_flows() -> str:
    """Get all available flows for the configured project."""
    flows = api.get_flows()
    
    if not flows:
        return f"No flows found for project ID: {api.project_id}"
    
    result = f"=== Available Flows for Project {api.project_id} ===\n"
    for i, flow in enumerate(flows, 1):
        flow_id = flow.get("identifier", "Unknown")
        flow_name = flow.get("name", "Unnamed Flow")
        flow_type = flow.get("type", "Unknown Type")
        result += f"{i}. {flow_name} (ID: {flow_id}, Type: {flow_type})\n"
    
    return result

@mcp.tool()
async def get_flow_phases(flow_id: str) -> str:
    """Get phases for a specific flow.
    
    Args:
        flow_id: ID of the flow to get phases for
    """
    phases = api.get_flow_phases(flow_id)
    
    if not phases:
        return f"No phases found for flow ID: {flow_id} in project: {api.project_id}"
    
    result = f"=== Flow Phases for Flow {flow_id} in Project {api.project_id} ===\n"
    for i, phase in enumerate(phases, 1):
        phase_id = phase.get("identifier", "Unknown")
        phase_name = phase.get("name", "Unnamed Phase")
        phase_order = phase.get("orderingNumber", "Unknown")
        result += f"\n{i}. {phase_name} (ID: {phase_id}, Order: {phase_order})\n"
        
        # Show management properties
        if "managementProperties" in phase:
            mgmt = phase["managementProperties"]
            result += f"   Enabled: {mgmt.get('isEnabled', False)}\n"
            result += f"   Auto-advance: {mgmt.get('autoAdvance', False)}\n"
            result += f"   Can be skipped: {mgmt.get('canBeSkipped', False)}\n"
        
        # Show phase properties
        if "properties" in phase:
            props = phase["properties"]
            result += "\n   Properties:\n"
            for key, value in props.items():
                result += f"     - {key}: {value}\n"
        
        # Show phase actions if available
        if "actions" in phase and phase["actions"]:
            result += "\n   Available Actions:\n"
            for action in phase["actions"]:
                action_name = action.get("name", "Unnamed Action")
                action_id = action.get("identifier", "Unknown")
                result += f"     - {action_name} (ID: {action_id})\n"
        
        # Show phase transitions if available
        if "transitions" in phase and phase["transitions"]:
            result += "\n   Transitions:\n"
            for transition in phase["transitions"]:
                target = transition.get("targetPhase", "Unknown")
                condition = transition.get("condition", "No condition")
                result += f"     - To: {target}, Condition: {condition}\n"
    
    return result

@mcp.tool()
async def add_phase_to_flow(flow_id: str, phase_name: str, phase_description: str = None, 
                           ordering_number: int = None, auto_advance: bool = False, 
                           can_be_skipped: bool = False) -> str:
    """Add a new phase to a flow.
    
    Args:
        flow_id: ID of the flow to add the phase to
        phase_name: Name of the new phase
        phase_description: Optional description of the phase
        ordering_number: Optional ordering number for the phase (position in the flow)
        auto_advance: Whether the phase should automatically advance to the next phase
        can_be_skipped: Whether the phase can be skipped
    """
    # Convert string parameters to appropriate types
    if ordering_number is not None and isinstance(ordering_number, str):
        try:
            ordering_number = int(ordering_number)
        except ValueError:
            return f"Error: ordering_number must be an integer, got '{ordering_number}'"
    
    if isinstance(auto_advance, str):
        auto_advance = auto_advance.lower() == 'true'
    
    if isinstance(can_be_skipped, str):
        can_be_skipped = can_be_skipped.lower() == 'true'
    
    result = api.add_phase_to_flow(
        flow_id=flow_id,
        phase_name=phase_name,
        phase_description=phase_description,
        ordering_number=ordering_number,
        auto_advance=auto_advance,
        can_be_skipped=can_be_skipped
    )
    
    if result.get("success"):
        phase_data = result.get("data", {})
        phase_id = phase_data.get("identifier", "Unknown")
        
        return (f"Successfully added phase '{phase_name}' to flow {flow_id}.\n"
                f"Phase ID: {phase_id}\n"
                f"Auto-advance: {auto_advance}\n"
                f"Can be skipped: {can_be_skipped}")
    else:
        error = result.get("error", "Unknown error")
        details = result.get("details", "No details available")
        debug_info = ""
        
        if "request_payload" in result:
            debug_info += f"\nRequest payload: {result['request_payload']}"
        if "request_url" in result:
            debug_info += f"\nRequest URL: {result['request_url']}"
            
        return f"Failed to add phase to flow: {error}\nDetails: {details}{debug_info}"

@mcp.tool()
async def add_step_to_phase(phase_id: str, step_name: str, step_description: str = None,
                           ordering_number: int = None, enabled_thematic_blocks: str = None) -> str:
    """Add a new step to a phase.
    
    Args:
        phase_id: ID of the phase to add the step to
        step_name: Name of the new step
        step_description: Optional description of the step
        ordering_number: Optional ordering number for the step (position in the phase)
        enabled_thematic_blocks: Optional comma-separated list of enabled thematic blocks.
            Valid values: INSTRUCTION, CHECKLIST, FORM, SIGNATURE
            Example: "INSTRUCTION,CHECKLIST"
            Defaults to "INSTRUCTION" if not specified.
    """
    # Convert string parameters to appropriate types
    if ordering_number is not None and isinstance(ordering_number, str):
        try:
            ordering_number = int(ordering_number)
        except ValueError:
            return f"Error: ordering_number must be an integer, got '{ordering_number}'"
    
    # Convert comma-separated string to list if provided
    thematic_blocks_list = None
    if enabled_thematic_blocks:
        thematic_blocks_list = [block.strip().upper() for block in enabled_thematic_blocks.split(',')]


    # Only manage INSTRUCTION blocks for now 
    result = api.add_step_to_phase(
        phase_id=phase_id,
        step_name=step_name,
        step_description=step_description,
        ordering_number=ordering_number,
        enabled_thematic_blocks=["INSTRUCTION"]
    )
    
    if result.get("success"):
        step_data = result.get("data", {})
        step_id = step_data.get("identifier", "Unknown")
        
        #blocks_str = ", ".join(thematic_blocks_list) if thematic_blocks_list else "INSTRUCTION"
        blocks_str = "INSTRUCTION"
        return (f"Successfully added step '{step_name}' to phase {phase_id}.\n"
                f"Step ID: {step_id}\n"
                f"Enabled thematic blocks: {blocks_str}")
    else:
        error = result.get("error", "Unknown error")
        details = result.get("details", "No details available")
        debug_info = ""
        
        if "request_payload" in result:
            debug_info += f"\nRequest payload: {result['request_payload']}"
        if "request_url" in result:
            debug_info += f"\nRequest URL: {result['request_url']}"
            
        return f"Failed to add step to phase: {error}\nDetails: {details}{debug_info}"

@mcp.tool()
async def create_flow(flow_name: str, project_id: str, flow_type: str = "GENERIC", 
                     description: str = None, category_id: str = None, 
                     family_id: str = None, family_custom_code: str = None,
                     reference: str = None) -> str:
    """Create a new flow.
    
    Args:
        flow_name: Name of the flow (required)
        project_id: ID of the project to create the flow in (required)
        flow_type: Type of flow (CORE, HEAD, GENERIC, FORM) - defaults to GENERIC
        description: Optional description of the flow
        category_id: Optional category identifier
        family_id: Optional family identifier (defaults to SITEFLOW_FAMILY_ID from .env)
        family_custom_code: Optional family custom code
        reference: Optional reference
    """
    # Validate flow_type if provided
    if flow_type and flow_type not in ["CORE", "HEAD", "GENERIC", "FORM"]:
        return f"Error: flow_type must be one of CORE, HEAD, GENERIC, FORM, got '{flow_type}'"
    
    result = api.create_flow(
        flow_name=flow_name,
        project_id=project_id,
        flow_type=flow_type,
        description=description,
        category_id=category_id,
        family_id=family_id,
        family_custom_code=family_custom_code,
        reference=reference
    )
    
    if result.get("success"):
        flow_data = result.get("data", {})
        # Extract the flow ID from the response
        # The structure might vary based on the API response
        flow_id = "Unknown"
        try:
            # Try to extract the flow ID from the response
            # This might need adjustment based on the actual response structure
            if isinstance(flow_data, list) and len(flow_data) > 0:
                flow_id = flow_data[0].get("identifier", "Unknown")
            elif isinstance(flow_data, dict):
                flow_id = flow_data.get("identifier", "Unknown")
        except Exception as e:
            print(f"Error extracting flow ID: {e}")
        
        return (f"Successfully created flow '{flow_name}'.\n"
                f"Flow ID: {flow_id}\n"
                f"Flow Type: {flow_type}\n"
                f"Project ID: {project_id}")
    else:
        error = result.get("error", "Unknown error")
        details = result.get("details", "No details available")
        debug_info = ""
        
        if "request_payload" in result:
            debug_info += f"\nRequest payload: {result['request_payload']}"
        if "request_url" in result:
            debug_info += f"\nRequest URL: {result['request_url']}"
            
        return f"Failed to create flow: {error}\nDetails: {details}{debug_info}"

@mcp.tool()
async def update_step_text(step_id: str, text_content: str) -> str:
    """Update the text block of a step.
    
    Args:
        step_id: ID of the step to update
        text_content: New text content for the step. This can include HTML formatting.
    """
    result = api.update_step_text(
        step_id=step_id,
        text_content=text_content
    )
    
    if result.get("success"):
        return f"Successfully updated text for step {step_id}."
    else:
        error = result.get("error", "Unknown error")
        details = result.get("details", "No details available")
        debug_info = ""
        
        if "request_payload" in result:
            debug_info += f"\nRequest payload: {result['request_payload']}"
        if "request_url" in result:
            debug_info += f"\nRequest URL: {result['request_url']}"
            
        return f"Failed to update step text: {error}\nDetails: {details}{debug_info}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')