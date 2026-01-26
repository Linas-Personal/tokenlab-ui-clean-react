"""
Parallel Agent Execution Utilities.

Execute agent decisions in parallel batches for performance.
"""
import asyncio
from typing import List
import logging

from app.abm.agents.token_holder import TokenHolderAgent, AgentAction

logger = logging.getLogger(__name__)


async def execute_agents_parallel(
    agents: List[TokenHolderAgent],
    batch_size: int = 100
) -> List[AgentAction]:
    """
    Execute agent decisions in parallel batches.

    Batching prevents overwhelming the event loop with too many
    concurrent tasks.

    Args:
        agents: List of agents to execute
        batch_size: Number of agents per batch

    Returns:
        List of AgentAction results
    """
    all_actions = []

    total_agents = len(agents)
    num_batches = (total_agents + batch_size - 1) // batch_size

    logger.debug(
        f"Executing {total_agents} agents in {num_batches} batches "
        f"(batch_size={batch_size})"
    )

    for batch_idx in range(0, total_agents, batch_size):
        batch = agents[batch_idx:batch_idx + batch_size]

        # Execute batch in parallel
        batch_actions = await asyncio.gather(
            *[agent.execute() for agent in batch],
            return_exceptions=True  # Don't fail entire batch if one agent fails
        )

        # Handle exceptions
        for i, action_or_exception in enumerate(batch_actions):
            if isinstance(action_or_exception, Exception):
                agent = batch[i]
                logger.error(
                    f"Agent {agent.attrs.agent_id} failed: {action_or_exception}",
                    exc_info=action_or_exception
                )
                # Create zero-action as fallback
                action_or_exception = AgentAction(
                    agent_id=agent.attrs.agent_id,
                    sell_tokens=0.0,
                    stake_tokens=0.0,
                    hold_tokens=0.0,
                    scaling_weight=agent.attrs.scaling_weight
                )

            all_actions.append(action_or_exception)

    logger.debug(f"Completed execution of {len(all_actions)} agents")
    return all_actions


def aggregate_agent_actions(actions: List[AgentAction]) -> dict:
    """
    Aggregate agent actions to global metrics.

    Applies scaling weights for meta-agents.

    Args:
        actions: List of AgentAction results

    Returns:
        Dictionary with aggregated metrics
    """
    total_sell = 0.0
    total_stake = 0.0
    total_hold = 0.0

    for action in actions:
        # Apply scaling weight (for meta-agents)
        total_sell += action.sell_tokens * action.scaling_weight
        total_stake += action.stake_tokens * action.scaling_weight
        total_hold += action.hold_tokens * action.scaling_weight

    return {
        "total_sell": total_sell,
        "total_stake": total_stake,
        "total_hold": total_hold,
        "num_agents": len(actions)
    }


def aggregate_by_cohort(actions: List[AgentAction], agents: List[TokenHolderAgent]) -> dict:
    """
    Aggregate agent actions by cohort.

    Args:
        actions: List of AgentAction results
        agents: List of agents (for cohort lookup)

    Returns:
        Dictionary mapping cohort name to aggregated metrics
    """
    cohort_metrics = {}

    for action, agent in zip(actions, agents):
        cohort = agent.attrs.cohort

        if cohort not in cohort_metrics:
            cohort_metrics[cohort] = {
                "total_sell": 0.0,
                "total_stake": 0.0,
                "total_hold": 0.0,
                "num_agents": 0
            }

        # Apply scaling weight
        cohort_metrics[cohort]["total_sell"] += action.sell_tokens * action.scaling_weight
        cohort_metrics[cohort]["total_stake"] += action.stake_tokens * action.scaling_weight
        cohort_metrics[cohort]["total_hold"] += action.hold_tokens * action.scaling_weight
        cohort_metrics[cohort]["num_agents"] += 1

    return cohort_metrics
