"""
UI模块 - 包含植物选择、渲染和UI管理相关功能
"""

from .plant_selection_manager import PlantSelectionManager
from .portal_manager import PortalManager
from .conveyor_belt_manager import ConveyorBeltManager,ConveyorCard
from .seed_rain_manager import SeedRainManager, SeedRainCard
from .renderer_manager import RendererManager
from .ui_manager import (
    draw_grid, draw_ui, show_game_over, show_settings_menu_with_hotreload,
    draw_main_menu, draw_level_select, draw_continue_dialog,
    draw_plant_select_grid, draw_codex_page, draw_codex_detail_page,
    draw_shop_page, draw_insufficient_coins_dialog, get_button_color,
    get_plants_codex_data, get_zombies_codex_data, wrap_text_chinese,draw_purchase_confirm_dialog
)

__all__ = [
    'PlantSelectionManager',
    'RendererManager',
    'PortalManager',
    "ConveyorBeltManager",
    "ConveyorCard",
    'SeedRainManager',
    'SeedRainCard',
    'draw_grid',
    'draw_ui',
    'show_game_over',
    'show_settings_menu_with_hotreload',
    'draw_main_menu',
    'draw_level_select',
    'draw_continue_dialog',
    'draw_plant_select_grid',
    'draw_codex_page',
    'draw_codex_detail_page',
    'draw_shop_page',
    'draw_insufficient_coins_dialog',
    'get_button_color',
    'get_plants_codex_data',
    'get_zombies_codex_data',
    'wrap_text_chinese',
    'draw_purchase_confirm_dialog'
]