"""Environment and Streamlit-secrets configuration with redacted status helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

from jira_qa_crew.exceptions import ConfigurationError


def _secret_value(secrets: Any, key: str) -> str | None:
    try:
        value = secrets.get(key)
    except (AttributeError, RuntimeError, StreamlitSecretNotFoundError):
        return None
    return str(value) if value not in (None, "") else None


@dataclass(frozen=True)
class AppConfig:
    app_name: str = "Jira QA Crew"
    app_env: str = "development"
    output_dir: Path = Path("outputs")
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_temperature: float = 0.1
    jira_integration_mode: str = "auto"
    jira_url: str = ""
    jira_auth_mode: str = "basic"
    jira_email: str = ""
    jira_api_token: str = ""
    jira_bearer_token: str = ""
    jira_api_version: int = 3
    jira_acceptance_criteria_field: str = ""
    jira_include_comments: bool = False
    jira_max_comments: int = 20
    jira_mcp_transport: str = "streamable_http"
    jira_mcp_url: str = ""
    jira_mcp_command: str = ""
    jira_mcp_args_json: str = "[]"
    jira_mcp_headers_json: str = "{}"
    jira_mcp_get_issue_tool: str = ""
    jira_mcp_issue_argument: str = "issue_key"
    jira_mcp_timeout_seconds: int = 20
    pipeline_max_tickets: int = 20
    pipeline_max_retries: int = 2
    pipeline_ticket_timeout_seconds: int = 600
    log_level: str = "INFO"
    demo_mode: bool = False
    max_input_chars: int = 5000
    jira_key_pattern: str = r"^[A-Z][A-Z0-9_]*-\d+$"

    @classmethod
    def load(cls, secrets: Any = None, env_file: Path | None = None) -> AppConfig:
        if env_file:
            load_dotenv(env_file, override=False)

        def value(key: str, default: str = "") -> str:
            return os.getenv(key) or _secret_value(secrets, key) or default

        try:
            return cls(
                app_name=value("APP_NAME", "Jira QA Crew"),
                app_env=value("APP_ENV", "development"),
                output_dir=Path(value("OUTPUT_DIR", "outputs")),
                llm_model=value("LLM_MODEL", value("GROQ_MODEL")),
                llm_api_key=value("LLM_API_KEY", value("GROQ_API_KEY")),
                llm_base_url=value("LLM_BASE_URL", value("BASE_URL")),
                llm_temperature=float(value("LLM_TEMPERATURE", "0.1")),
                jira_integration_mode=value("JIRA_INTEGRATION_MODE", "auto").lower(),
                jira_url=value("JIRA_URL"),
                jira_auth_mode=value("JIRA_AUTH_MODE", "basic").lower(),
                jira_email=value("JIRA_EMAIL"),
                jira_api_token=value("JIRA_API_TOKEN", value("JIRA_TOKEN")),
                jira_bearer_token=value("JIRA_BEARER_TOKEN"),
                jira_api_version=int(value("JIRA_API_VERSION", "3")),
                jira_acceptance_criteria_field=value("JIRA_ACCEPTANCE_CRITERIA_FIELD"),
                jira_include_comments=value("JIRA_INCLUDE_COMMENTS", "false").lower()
                == "true",
                jira_max_comments=int(value("JIRA_MAX_COMMENTS", "20")),
                jira_mcp_transport=value(
                    "JIRA_MCP_TRANSPORT", "streamable_http"
                ).lower(),
                jira_mcp_url=value("JIRA_MCP_URL"),
                jira_mcp_command=value("JIRA_MCP_COMMAND"),
                jira_mcp_args_json=value("JIRA_MCP_ARGS_JSON", "[]"),
                jira_mcp_headers_json=value("JIRA_MCP_HEADERS_JSON", "{}"),
                jira_mcp_get_issue_tool=value("JIRA_MCP_GET_ISSUE_TOOL"),
                jira_mcp_issue_argument=value("JIRA_MCP_ISSUE_ARGUMENT", "issue_key"),
                jira_mcp_timeout_seconds=int(value("JIRA_MCP_TIMEOUT_SECONDS", "20")),
                pipeline_max_tickets=int(value("PIPELINE_MAX_TICKETS", "20")),
                pipeline_max_retries=int(value("PIPELINE_MAX_RETRIES", "2")),
                pipeline_ticket_timeout_seconds=int(
                    value("PIPELINE_TICKET_TIMEOUT_SECONDS", "600")
                ),
                log_level=value("LOG_LEVEL", "INFO").upper(),
                demo_mode=value("DEMO_MODE", "false").lower() == "true",
                max_input_chars=int(value("PIPELINE_MAX_INPUT_CHARS", "5000")),
                jira_key_pattern=value("JIRA_KEY_PATTERN", r"^[A-Z][A-Z0-9_]*-\d+$"),
            )
        except (ValueError, TypeError) as error:
            raise ConfigurationError(
                f"Invalid numeric configuration: {error}"
            ) from error

    def validate_for_run(self, integration_mode: str | None = None) -> None:
        mode = (integration_mode or self.jira_integration_mode).lower()
        if mode not in {"auto", "mcp", "rest"}:
            raise ConfigurationError("Integration mode must be auto, mcp, or rest.")
        if not self.llm_model:
            raise ConfigurationError("Set LLM_MODEL to a CrewAI-supported model name.")
        if not self.llm_api_key:
            raise ConfigurationError(
                "Set LLM_API_KEY in the environment or Streamlit secrets."
            )
        rest_ready = bool(
            self.jira_url.startswith("https://")
            and (
                (
                    self.jira_auth_mode == "basic"
                    and self.jira_email
                    and self.jira_api_token
                )
                or (self.jira_auth_mode == "bearer" and self.jira_bearer_token)
            )
        )
        mcp_ready = bool(
            self.jira_mcp_get_issue_tool
            and (
                (self.jira_mcp_transport == "streamable_http" and self.jira_mcp_url)
                or (self.jira_mcp_transport == "stdio" and self.jira_mcp_command)
            )
        )
        if mode == "rest":
            if not self.jira_url.startswith("https://"):
                raise ConfigurationError(
                    "Set JIRA_URL to your HTTPS Jira Cloud site URL."
                )
            if self.jira_auth_mode == "basic" and not (
                self.jira_email and self.jira_api_token
            ):
                raise ConfigurationError(
                    "Basic Jira auth requires JIRA_EMAIL and JIRA_API_TOKEN."
                )
            if self.jira_auth_mode == "bearer" and not self.jira_bearer_token:
                raise ConfigurationError("Bearer Jira auth requires JIRA_BEARER_TOKEN.")
        if mode == "mcp":
            if not self.jira_mcp_get_issue_tool:
                raise ConfigurationError(
                    "Set JIRA_MCP_GET_ISSUE_TOOL to the MCP read-only issue tool name."
                )
            if self.jira_mcp_transport == "streamable_http" and not self.jira_mcp_url:
                raise ConfigurationError(
                    "Set JIRA_MCP_URL for streamable HTTP Jira MCP."
                )
            if self.jira_mcp_transport == "stdio" and not self.jira_mcp_command:
                raise ConfigurationError("Set JIRA_MCP_COMMAND for stdio Jira MCP.")
        if mode == "auto" and not (rest_ready or mcp_ready):
            raise ConfigurationError(
                "Auto mode needs at least one configured provider: Jira REST credentials "
                "or a Jira MCP tool."
            )

    def redacted_status(self) -> dict[str, bool | str]:
        return {
            "LLM configured": bool(self.llm_model and self.llm_api_key),
            "Jira URL": self.jira_url or "Not set",
            "Jira credentials configured": bool(
                (self.jira_email and self.jira_api_token) or self.jira_bearer_token
            ),
            "MCP configured": bool(self.jira_mcp_get_issue_tool),
            "Demo mode": self.demo_mode,
        }

    def mcp_args(self) -> list[str]:
        parsed = json.loads(self.jira_mcp_args_json)
        if not isinstance(parsed, list) or not all(
            isinstance(part, str) for part in parsed
        ):
            raise ConfigurationError(
                "JIRA_MCP_ARGS_JSON must be a JSON array of strings."
            )
        return parsed

    def mcp_headers(self) -> dict[str, str]:
        parsed = json.loads(self.jira_mcp_headers_json)
        if not isinstance(parsed, dict):
            raise ConfigurationError("JIRA_MCP_HEADERS_JSON must be a JSON object.")
        return {str(key): str(value) for key, value in parsed.items()}
