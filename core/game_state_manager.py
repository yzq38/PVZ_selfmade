"""
游戏状态管理模块 - 负责游戏状态的切换和管理（添加详细图鉴状态支持）
"""
import pygame
from .constants import *
from .level_manager import LevelManager


class GameStateManager:
    """游戏状态管理器"""

    def __init__(self):
        # 游戏状态
        self.game_state = "main_menu"
        self.previous_game_state = None

        # UI状态
        self.game_paused = False
        self.show_settings = False
        self.show_reset_confirm = False
        self.show_continue_dialog = False
        self.selected_level_for_continue = None
        self.show_purchase_confirm = False
        self.pending_purchase_item = None
        # 过渡状态
        self.transition_state = "none"  # "none", "level_to_game_fade_out", "level_to_game_fade_in"
        self.transition_timer = 0
        self.transition_duration = 60  # 1秒 (60帧)
        self.transition_alpha = 0
        self.pending_game_data = None  # 存储待加载的游戏数据
        self.pending_level_num = None  # 存储待开始的关卡号
        self.hover_level = None  # 当前悬停的关卡号
        self.hover_pos = None  # 鼠标位置，用于显示工具提示
        self.hover_button = None  # 当前悬停的按钮标识
        self.hover_button_type = None  # 按钮类型 ('main_menu', 'settings', 'card', 'shovel', etc.)
        self.show_insufficient_coins_dialog = False
        self.insufficient_coins_item = None  # 存储试图购买但金币不足的商品信息

        # 新增：详细图鉴状态
        self.codex_detail_type = None  # "plants" 或 "zombies"
        self.selected_codex_item = 0  # 当前选中的图鉴项目索引

        # 植物预览状态
        self.plant_preview = {
            'enabled': False,
            'plant_type': None,
            'target_row': None,
            'target_col': None,
            'can_place': False
        }
        self.hammer_cursor = {
            'enabled': False,
            'x': 0,
            'y': 0
        }

    def set_hover_level(self, level_num, mouse_pos=None):
        """设置当前悬停的关卡"""
        self.hover_level = level_num
        self.hover_pos = mouse_pos

    def clear_hover_level(self):
        """清除悬停状态"""
        self.hover_level = None
        self.hover_pos = None

    def set_hover_button(self, button_id, button_type):
        """设置当前悬停的按钮"""
        self.hover_button = button_id
        self.hover_button_type = button_type

    def is_button_hovered(self, button_id, button_type):
        """检查指定按钮是否被悬停"""
        return (self.hover_button == button_id and
                self.hover_button_type == button_type)

    def clear_hover_button(self):
        """清除按钮悬停状态"""
        self.hover_button = None
        self.hover_button_type = None

    def set_plant_preview(self, plant_type, target_row, target_col, can_place):
        """设置植物预览状态"""
        self.plant_preview['enabled'] = True
        self.plant_preview['plant_type'] = plant_type
        self.plant_preview['target_row'] = target_row
        self.plant_preview['target_col'] = target_col
        self.plant_preview['can_place'] = can_place

    def clear_plant_preview(self):
        """清除植物预览状态"""
        self.plant_preview['enabled'] = False
        self.plant_preview['plant_type'] = None
        self.plant_preview['target_row'] = None
        self.plant_preview['target_col'] = None
        self.plant_preview['can_place'] = False

    def get_plant_preview(self):
        """获取植物预览状态"""
        return self.plant_preview.copy() if self.plant_preview['enabled'] else None

    def reset_game(self, keep_level=None):
        """
        重置游戏状态，修改为使用新的配置系统和特性管理器
        更新：完全集成特性管理系统，修复传送门系统重置问题
        """
        # 创建关卡管理器（现在从配置文件加载）
        level_manager = LevelManager("database/levels.json")  # 指定配置文件路径
        level_manager.enable_hot_reload(True)  # 默认启用热重载

        # 如果指定了保持关卡，则设置对应关卡
        if keep_level is not None:
            level_manager.start_level(keep_level)

        # 根据关卡配置设置初始阳光 - 使用特性管理器
        initial_sun = level_manager.get_initial_sun()

        new_game = {
            "plants": [], "zombies": [], "bullets": [],
            "zombie_timer": 0, "sun": initial_sun, "game_over": False, "selected": None,
            "wave_mode": False,
            "wave_timer": 0,
            "zombies_spawned": 0,
            "zombies_killed": 0,
            "first_wave_spawned": False,
            "game_over_sound_played": False,
            "level_manager": level_manager,
            "fade_state": "none",
            "fade_alpha": 0,
            "fade_timer": 0,
            "fade_duration": 190,
            "card_cooldowns": {},
            "last_update_time": pygame.time.get_ticks(),
            "last_save_time": 0,
            # 修复：添加缺少的字段
            "portal_manager": None,
            "hammer_cooldown": 0,
            "zombie_stun_timers": {},
            "cucumber_spray_timers": {},
            "cucumber_plant_healing": {},
            "dandelion_seeds": [],
            "_pending_coins": 0
        }

        return new_game

    def start_level_transition_animation(self):
        """开始关卡过渡动画"""
        self.transition_state = "level_to_game_fade_out"
        self.transition_timer = 0
        self.transition_alpha = 0
        self.show_continue_dialog = False  # 关闭对话框

    def update_transition_animation(self):
        """更新过渡动画状态"""
        if self.transition_state == "none":
            return False  # 没有动画在进行

        self.transition_timer += 1

        if self.transition_state == "level_to_game_fade_out":
            # 渐暗阶段
            progress = min(1.0, self.transition_timer / self.transition_duration)
            self.transition_alpha = int(255 * progress)

            if self.transition_timer >= self.transition_duration:
                # 渐暗完成，加载游戏数据并开始渐亮
                self.transition_state = "level_to_game_fade_in"
                self.transition_timer = 0
                return True  # 返回True表示需要加载游戏数据

        elif self.transition_state == "level_to_game_fade_in":
            # 渐亮阶段
            progress = min(1.0, self.transition_timer / self.transition_duration)
            self.transition_alpha = int(255 * (1.0 - progress))

            if self.transition_timer >= self.transition_duration:
                # 渐亮完成，恢复正常状态
                self.transition_state = "none"
                self.transition_alpha = 0
                self.game_paused = False  # 允许用户操作

        return False

    def switch_to_game_state(self):
        """切换到游戏状态"""
        self.game_state = "playing"

    def switch_to_main_menu(self):
        """切换到主菜单"""
        self.game_state = "main_menu"

    def switch_to_level_select(self):
        """切换到选关界面"""
        self.game_state = "level_select"

    def switch_to_shop(self):
        """切换到商店界面"""
        self.game_state = "shop"

    def switch_to_codex(self):
        """切换到图鉴界面"""
        self.game_state = "codex"

    def switch_to_codex_detail(self, detail_type):
        """切换到详细图鉴界面"""
        self.game_state = "codex_detail"
        self.codex_detail_type = detail_type
        self.selected_codex_item = 0  # 重置选中项

    def switch_back_to_codex(self):
        """从详细图鉴返回图鉴主页"""
        self.game_state = "codex"
        self.codex_detail_type = None
        self.selected_codex_item = 0

    def set_selected_codex_item(self, index):
        """设置选中的图鉴项目"""
        self.selected_codex_item = index

    def get_codex_detail_type(self):
        """获取当前详细图鉴类型"""
        return self.codex_detail_type

    def get_selected_codex_item(self):
        """获取当前选中的图鉴项目索引"""
        return self.selected_codex_item

    def show_continue_dialog_for_level(self, level_num):
        """显示指定关卡的继续游戏对话框"""
        self.selected_level_for_continue = level_num
        self.show_continue_dialog = True

    def hide_continue_dialog(self):
        """隐藏继续游戏对话框"""
        self.show_continue_dialog = False
        self.selected_level_for_continue = None

    def set_pending_game_data(self, game_data, level_num):
        """设置待加载的游戏数据"""
        self.pending_game_data = game_data
        self.pending_level_num = level_num

    def clear_pending_game_data(self):
        """清除待加载的游戏数据"""
        self.pending_game_data = None
        self.pending_level_num = None

    def get_pending_game_data(self):
        """获取待加载的游戏数据"""
        return self.pending_game_data, self.pending_level_num

    def toggle_settings(self):
        """切换设置菜单显示状态"""
        self.show_settings = not self.show_settings
        self.game_paused = self.show_settings

    def show_reset_confirmation(self):
        """显示重置确认对话框"""
        self.show_reset_confirm = True
        self.show_settings = False

    def hide_reset_confirmation(self):
        """隐藏重置确认对话框"""
        self.show_reset_confirm = False

    def is_in_transition(self):
        """检查是否正在过渡动画中"""
        return self.transition_state != "none"

    def should_pause_game_logic(self):
        """检查是否应该暂停游戏逻辑"""
        return (self.game_paused or
                self.show_settings or
                self.show_reset_confirm or
                self.is_in_transition())

    def get_transition_alpha(self):
        """获取过渡动画的透明度"""
        return self.transition_alpha

    def update_game_state_music(self, music_manager):
        """更新游戏状态对应的音乐"""
        if self.game_state != self.previous_game_state:
            music_manager.change_music_for_state(self.game_state)
            self.previous_game_state = self.game_state

    def show_insufficient_coins_dialog_for_item(self, item):
        """显示金币不足对话框"""
        self.show_insufficient_coins_dialog = True
        self.insufficient_coins_item = item

    def hide_insufficient_coins_dialog(self):
        """隐藏金币不足对话框"""
        self.show_insufficient_coins_dialog = False
        self.insufficient_coins_item = None

    def get_insufficient_coins_item(self):
        """获取金币不足的商品信息"""
        return self.insufficient_coins_item

    def show_purchase_confirmation(self, item):
        """显示购买确认对话框"""
        self.show_purchase_confirm = True
        self.pending_purchase_item = item

    def hide_purchase_confirmation(self):
        """隐藏购买确认对话框"""
        self.show_purchase_confirm = False
        self.pending_purchase_item = None

    def get_pending_purchase_item(self):
        """获取待购买的物品"""
        return self.pending_purchase_item

    def set_hammer_cursor_pos(self, x, y):
        """设置锤子跟随鼠标的位置"""
        self.hammer_cursor['enabled'] = True
        self.hammer_cursor['x'] = x
        self.hammer_cursor['y'] = y

    def clear_hammer_cursor(self):
        """清除锤子鼠标跟随状态"""
        self.hammer_cursor['enabled'] = False
        self.hammer_cursor['x'] = 0
        self.hammer_cursor['y'] = 0

    def get_hammer_cursor_pos(self):
        """获取锤子鼠标跟随位置"""
        if self.hammer_cursor['enabled']:
            return self.hammer_cursor['x'], self.hammer_cursor['y']
        return None

    def is_hammer_cursor_enabled(self):
        """检查锤子鼠标跟随是否启用"""
        return self.hammer_cursor['enabled']