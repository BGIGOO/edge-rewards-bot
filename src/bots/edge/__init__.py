# -*- coding: utf-8 -*-
"""
src/bots/edge
=============
Edge Rewards Search Bot package.
"""

from src.bots.edge.anti_detect import (
    dismiss_popups,
    human_type,
    simulate_natural_mouse_movement,
    simulate_human_browsing,
    simulate_random_result_click
)
from src.bots.edge.browser import (
    get_profile_abs_path,
    sync_profile_from_system,
    kill_zombie_edge_processes,
    open_browser_for_login,
    create_edge_driver,
    managed_browser
)
from src.bots.edge.points_parser import (
    parse_rewards_breakdown_text,
    check_profile_points
)
from src.bots.edge.searcher import (
    load_keywords,
    execute_search_session
)
from src.bots.edge.runner import (
    load_config,
    check_and_prompt_first_time_login,
    run_profile_session,
    main
)

__all__ = [
    "dismiss_popups",
    "human_type",
    "simulate_natural_mouse_movement",
    "simulate_human_browsing",
    "simulate_random_result_click",
    "get_profile_abs_path",
    "sync_profile_from_system",
    "kill_zombie_edge_processes",
    "open_browser_for_login",
    "create_edge_driver",
    "managed_browser",
    "parse_rewards_breakdown_text",
    "check_profile_points",
    "load_keywords",
    "execute_search_session",
    "load_config",
    "check_and_prompt_first_time_login",
    "run_profile_session",
    "main"
]
