"""Typed errors used at provider and pipeline boundaries."""


class JiraProviderError(RuntimeError):
    """A Jira provider could not return a usable issue."""


class JiraAuthenticationError(JiraProviderError):
    """Jira rejected configured credentials."""


class JiraNotFoundError(JiraProviderError):
    """The issue is missing or not visible to the configured Jira account."""


class JiraRateLimitError(JiraProviderError):
    """Jira rate-limited the request after bounded retries."""


class ConfigurationError(RuntimeError):
    """Required application configuration is missing or invalid."""


class OutputValidationError(ValueError):
    """Crew output failed deterministic schema or traceability checks."""
