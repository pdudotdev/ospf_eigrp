import json
from pydantic import BaseModel, Field, model_validator


class BaseParamsModel(BaseModel):
    """Base class for all MCP tool input models.

    Adds a pre-validator that handles the case where the model passes `params`
    as a JSON string instead of a dict (e.g. '{"device": "R1A"}}' with trailing
    garbage). Uses raw_decode() so any trailing characters after valid JSON are
    silently ignored.
    """
    @model_validator(mode='before')
    @classmethod
    def parse_string_input(cls, v):
        if isinstance(v, str):
            try:
                obj, _ = json.JSONDecoder().raw_decode(v.strip())
                return obj
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(f"Could not parse params as JSON: {v!r}") from e
        return v


# OSPF query - input model
class OspfQuery(BaseParamsModel):
    device: str = Field(..., description="Device name from inventory")
    query: str = Field(..., description="neighbors | database | borders | config | interfaces | details")

# EIGRP query - input model
class EigrpQuery(BaseParamsModel):
    device: str = Field(..., description="Device name from inventory")
    query: str = Field(..., description="neighbors | topology | config | interfaces")

# BGP query - input model
class BgpQuery(BaseParamsModel):
    device: str
    query: str = Field(..., description="summary | detail | config")

class RoutingQuery(BaseParamsModel):
    device: str
    prefix: str | None = Field(None, description="Optional prefix to look up")

# Routing policies query - input model
class RoutingPolicyQuery(BaseParamsModel):
    device: str
    query: str = Field(..., description="route_maps | prefix_lists | policy_based_routing | access_lists | nat_pat")

# Interfaces query - input model
class InterfacesQuery(BaseParamsModel):
    device: str = Field(..., description="Device name from inventory")

# Ping - input model
class PingInput(BaseParamsModel):
    device: str = Field(..., description="Device name from inventory")
    destination: str = Field(..., description="IP address to ping")
    source: str | None = Field(None, description="Optional source IP or interface")

# Traceroute - input model
class TracerouteInput(BaseParamsModel):
    device: str = Field(..., description="Device name from inventory")
    destination: str = Field(..., description="IP address to trace")
    source: str | None = Field(None, description="Optional source IP or interface")

# Show command - input model
class ShowCommand(BaseParamsModel):
    """Run a show command against a network device."""
    device: str = Field(..., description="Device name from inventory (e.g. R1, R2, R3)")
    command: str = Field(..., description="Show command to execute on the device")

# Config commands - input model
class ConfigCommand(BaseParamsModel):
    """Send configuration commands to one or more devices."""
    devices: list[str] = Field(..., description="Device names from inventory (e.g. ['R1','R2','R3'])")
    commands: list[str] = Field(..., description="Configuration commands to apply")

# Empty placeholder - input model
class EmptyInput(BaseParamsModel):
    pass

# Snapshot - input model
class SnapshotInput(BaseParamsModel):
    devices: list[str] = Field(..., description="Devices to snapshot (e.g. R1, R2, R3)")
    profile: str = Field(..., description="Snapshot profile (e.g. ospf, stp)")

# Risk score - input model
class RiskInput(BaseParamsModel):
    devices: list[str] = Field(..., description="Devices affected by the config change")
    commands: list[str] = Field(..., description="The configuration commands to apply")

# Jira case management - input models
class JiraCommentInput(BaseParamsModel):
    issue_key: str = Field(..., description="Jira issue key (e.g. 'SUP-12')")
    comment: str = Field(..., description="Comment text to add to the ticket")

class JiraResolveInput(BaseParamsModel):
    issue_key: str = Field(..., description="Jira issue key (e.g. 'SUP-12')")
    resolution_comment: str = Field(..., description="Resolution summary to add as final comment")
    resolution: str = Field("Done", description="Transition name: 'Done', 'Resolved', or \"Won't Fix\"")
