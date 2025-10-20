"""Prompt strategies for LLM attacks."""

from .prompt_templates import (
    PromptStrategy,
    JailbreakStrategy,
    SocialEngineeringStrategy,
    TechnicalObfuscationStrategy,
    MultiTurnStrategy,
    ALL_STRATEGIES as TEMPLATE_STRATEGIES,
    get_strategy_by_name as _get_strategy_by_name_template,
    get_strategies_by_category as _get_strategies_by_category_template,
    get_all_strategy_names as _get_all_strategy_names_template,
)

from .multi_step_attacks import MULTI_STEP_STRATEGIES

# Combine all strategies
ALL_STRATEGIES = TEMPLATE_STRATEGIES + MULTI_STEP_STRATEGIES


def get_strategy_by_name(name: str) -> PromptStrategy:
    """Get a strategy by name from all strategies."""
    for strategy in ALL_STRATEGIES:
        if strategy.name == name:
            return strategy
    raise ValueError(f"Strategy '{name}' not found")


def get_strategies_by_category(category: str):
    """Get all strategies in a category."""
    return [s for s in ALL_STRATEGIES if s.category == category]


def get_all_strategy_names():
    """Get names of all strategies."""
    return [s.name for s in ALL_STRATEGIES]

__all__ = [
    'PromptStrategy',
    'JailbreakStrategy',
    'SocialEngineeringStrategy',
    'TechnicalObfuscationStrategy',
    'MultiTurnStrategy',
    'ALL_STRATEGIES',
    'MULTI_STEP_STRATEGIES',
    'get_strategy_by_name',
    'get_strategies_by_category',
    'get_all_strategy_names',
]
