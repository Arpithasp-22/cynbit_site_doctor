"""Helper for accessing secrets from both Streamlit secrets and environment variables."""
import os


def get_secret(key: str, default=None):
    """Get a secret from Streamlit secrets or environment variables.
    
    Tries Streamlit secrets first (when running on Streamlit Cloud),
    falls back to environment variables (for local development).
    
    Args:
        key: The secret key to retrieve
        default: Default value if secret is not found
        
    Returns:
        The secret value or default
    """
    # Try Streamlit secrets first
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except (ImportError, FileNotFoundError, KeyError):
        pass
    
    # Fall back to environment variables
    return os.environ.get(key, default)


def has_api_key() -> bool:
    """Check if ANTHROPIC_API_KEY is available."""
    return get_secret("ANTHROPIC_API_KEY") is not None


def get_model() -> str:
    """Get the Claude model name from secrets or use default."""
    return get_secret("CLAUDE_MODEL", "claude-sonnet-5-5")
