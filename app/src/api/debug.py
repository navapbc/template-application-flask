from pydantic import Field

from src.util.env_config import PydanticBaseEnvConfig


class DebugAdapterProtocolConfig(PydanticBaseEnvConfig):
    enable: bool = Field(
        default=False,
        description="Enable debug mode. Overwritten to True when running a debug make target",
    )
    host: str = Field(default="0.0.0.0", description="The host for the debugger to listen on")
    port: int = Field(default=5678, description="The port for the debugger to listen on")

    wait_for_client: bool = Field(
        default=True, description="Whether to wait for the debugger client to attach"
    )
    wait_for_client_message: str = Field(
        default="Waiting for remote attach debugger...",
        description="Message to log when waiting for debugger",
    )

    class Config:
        env_prefix = "DEBUG_ADAPTER_PROTOCOL_"
