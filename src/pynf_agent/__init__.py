"""
pynf_agent - AI agent for automated bioinformatics workflows using Nextflow.

This package provides an interactive agent that can discover, configure, and execute
nf-core modules through natural language conversation using LLMs via OpenRouter.
"""

from .agent import BioinformaticsAgent, SessionContext
from .openrouter_client import OpenRouterClient

__all__ = [
    'BioinformaticsAgent',
    'SessionContext',
    'OpenRouterClient',
]
