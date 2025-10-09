"""
渲染管理模块 - 负责游戏画面的绘制和渲染（集成小推车渲染功能 + 暗夜效果）
"""
import pygame
import sys
import os

# 添加父目录到路径以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.constants import *
# 使用相对导入引用同一文件夹下的ui_manager
from . import ui_manager
from core.cards_manager import get_available_cards_new


class RendererManager:
    """渲染管理器 - 负责绘制游戏的各种界面"""

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.finish_btn = None  # 新增：存储开始战斗按钮

    def render_game(self):
        """渲染游戏画面"""

        self.game_manager.game_surface.fill((0, 120, 0))

        if self.game_manager.state_manager.game_state == "main_menu":
            self._render_main_menu()
        elif self.game_manager.state_manager.game_state == "level_select":
            self._render_level_select()
        elif self.game_manager.state_manager.game_state == "playing":
            self._render_playing()
        elif self.game_manager.state_manager.game_state == "shop":
            self._render_shop()
        elif self.game_manager.state_manager.game_state == "codex":
            self._render_codex()
        elif self.game_manager.state_manager.game_state == "codex_detail":
            self._render_codex_detail()

        # 渲染通用UI元素（适用于所有状态）
        self._render_common_ui()

        # 渲染过渡动画（适用于所有状态）
        if self.game_manager.state_manager.is_in_transition():
            self._render_transition_mask()

        # 最终屏幕绘制（适用于所有状态）
        self._blit_to_screen()

    def _render_codex_detail(self):
        """渲染详细图鉴页面"""
        # 绘制背景（在draw_codex_detail_page中处理）
        # 不需要单独绘制背景，因为详细页面会填充整个画面15

        # 绘制详细图鉴页面
        ui_manager.draw_codex_detail_page(
            self.game_manager.game_surface,
            self.game_manager.state_manager.get_codex_detail_type(),
            self.game_manager.state_manager.get_selected_codex_item(),
            self.game_manager.font_large,
            self.game_manager.font_medium,
            self.game_manager.font_small,
            self.game_manager.font_tiny,
            self.game_manager.scaled_images,
            self.game_manager.state_manager
        )

    def _render_codex(self):
        """渲染图鉴页面"""
        # 绘制背景
        if self.game_manager.images.get('menu_bg_img'):
            self.game_manager.game_surface.blit(self.game_manager.images.get('menu_bg_img'), (0, 0))
        else:
            self.game_manager.game_surface.fill((0, 100, 0))

        # 绘制图鉴页面
        ui_manager.draw_codex_page(
            self.game_manager.game_surface,
            self.game_manager.animation_manager.level_select_animation_timer,
            self.game_manager.animation_manager.level_select_animation_complete,
            self.game_manager.animation_manager.level_select_exit_animation,
            self.game_manager.animation_manager.menu_animation_timer,
            self.game_manager.font_large,
            self.game_manager.font_medium,
            self.game_manager.state_manager
        )

    def _render_main_menu(self):
        """渲染主菜单"""
        ui_manager.draw_main_menu(
            self.game_manager.game_surface,
            self.game_manager.animation_manager.menu_animation_timer,
            self.game_manager.animation_manager.menu_exit_animation,
            self.game_manager.game_db.has_saved_game(),
            self.game_manager.images.get('menu_bg_img'),
            self.game_manager.font_medium,
            self.game_manager.state_manager,
            self.game_manager.font_tiny
        )

    def _render_level_select(self):
        """渲染选关界面"""
        ui_manager.draw_level_select(
            self.game_manager.game_surface,
            self.game_manager.game_db,
            self.game_manager.level_settings,
            self.game_manager.images.get('menu_bg_img'),
            self.game_manager.font_medium,
            self.game_manager.font_small,
            self.game_manager.images.get('settings_img'),
            self.game_manager.animation_manager.level_select_animation_timer,
            self.game_manager.animation_manager.level_select_animation_complete,
            self.game_manager.animation_manager.level_select_exit_animation,
            self.game_manager.animation_manager.menu_animation_timer,
            # 传递悬停状态
            self.game_manager.state_manager.hover_pos,
            self.game_manager.state_manager.hover_level,
            self.game_manager.state_manager
        )

    def _render_playing(self):
        """渲染游戏界面"""
        # 1. 先绘制整个战场区域的背景（深绿色）
        battlefield_rect = pygame.Rect(BATTLEFIELD_LEFT, BATTLEFIELD_TOP,
                                       total_battlefield_width, total_battlefield_height)
        pygame.draw.rect(self.game_manager.game_surface, (0, 120, 0), battlefield_rect)

        # 2. 绘制战场网格（在战场背景之上）
        ui_manager.draw_grid(self.game_manager.game_surface, self.game_manager.images.get('grid_bg_img'))

        # 3. 绘制暗夜效果（第22关）- 在网格之后，游戏对象之前
        self._render_night_effect()
        self._render_ice_trails()
        # 4. 绘制小推车（在网格和暗夜效果之后，游戏对象之前）
        self._render_carts()

        # 获取可用卡片
        cards = self.game_manager.get_available_cards_for_current_state()

        # 绘制UI
        settings_rect = ui_manager.draw_ui(
            self.game_manager.game_surface,
            self.game_manager.game["sun"],
            cards,
            self.game_manager.shovel,
            self.game_manager.game["selected"],
            self.game_manager.game["level_manager"],
            self.game_manager.game["wave_mode"],
            self.game_manager.game["wave_timer"],
            WAVE_INTERVAL,
            self.game_manager.state_manager.show_settings,
            self.game_manager.game,
            self.game_manager.level_settings,
            self.game_manager.scaled_images,
            self.game_manager.font_small,
            self.game_manager.font_medium,
            self.game_manager.images,
            game_manager=self.game_manager,
            conveyor_belt_manager=self.game_manager.conveyor_belt_manager,
            seed_rain_manager=self.game_manager.seed_rain_manager,
        )

        # 如果显示植物选择，在战场区域绘制选择网格
        if self.game_manager.plant_selection_manager.show_plant_select:
            self._render_plant_selection()
        else:
            self._render_game_objects()

        # 绘制植物预览（在游戏对象之后）
        if not self.game_manager.plant_selection_manager.show_plant_select:
            self._render_plant_preview()
        self._render_portals()
        self._render_hammer_cursor()

        # 绘制奖杯
        self._render_trophy()

        # 绘制淡入淡出效果
        self._render_fade_effect()

    def _render_ice_trails(self):
        """渲染冰道效果"""
        # 检查是否有冰道管理器
        if "ice_trail_manager" in self.game_manager.game:
            ice_trail_manager = self.game_manager.game["ice_trail_manager"]
            if ice_trail_manager:
                # 绘制所有冰道
                ice_trail_manager.draw(self.game_manager.game_surface)

    def _render_night_effect(self):
        """渲染暗夜效果 - 仅在第22关生效，只覆盖战场区域"""
        # 检查当前是否是第22关
        level_manager = self.game_manager.game.get("level_manager")
        if not level_manager:
            return

        if not level_manager.has_special_feature("night"):
            return

        # 创建仅覆盖战场区域的暗夜效果
        battlefield_night = pygame.Surface((total_battlefield_width, total_battlefield_height), pygame.SRCALPHA)

        # 轻微的深蓝色半透明效果 - 大幅降低透明度以保持可见性
        # 从顶部到底部创建轻微的渐变，营造自然的夜晚氛围
        for y in range(total_battlefield_height):
            gradient_ratio = y / total_battlefield_height
            # 顶部稍微更暗，底部稍微更亮，但整体都很透明
            alpha_variation = int(60 + (20 - 60) * gradient_ratio)
            alpha_variation = max(150, min(35, alpha_variation))

            # 深蓝色调，营造夜晚氛围
            gradient_color = (0, 25, 70, alpha_variation)  # 深蓝色，非常低的透明度
            line_surface = pygame.Surface((total_battlefield_width, 1), pygame.SRCALPHA)
            line_surface.fill(gradient_color)
            battlefield_night.blit(line_surface, (0, y))

        # 将暗夜覆盖层只绘制到战场区域
        self.game_manager.game_surface.blit(battlefield_night, (BATTLEFIELD_LEFT, BATTLEFIELD_TOP))

    def _render_portals(self):
        """渲染传送门"""
        # 检查关卡管理器是否有传送门系统特性
        if hasattr(self.game_manager.game.get("level_manager"), 'has_special_feature'):
            level_manager = self.game_manager.game.get("level_manager")
            if level_manager and level_manager.has_special_feature("portal_system"):
                # 检查游戏状态中是否有传送门管理器
                if "portal_manager" in self.game_manager.game:
                    portal_manager = self.game_manager.game["portal_manager"]
                    portal_manager.draw_portals(self.game_manager.game_surface)

    def _render_carts(self):
        """渲染小推车"""
        # 调用小推车管理器绘制所有小推车
        self.game_manager.cart_manager.draw_carts(self.game_manager.game_surface)

    def _render_hammer_cursor(self):
        """渲染跟随鼠标的锤子"""
        # 检查锤子是否被选中并跟随鼠标
        if (self.game_manager.game["selected"] == "hammer" and
                self.game_manager.state_manager.is_hammer_cursor_enabled()):

            # 获取锤子跟随的鼠标位置
            cursor_pos = self.game_manager.state_manager.get_hammer_cursor_pos()
            if cursor_pos is not None:
                cursor_x, cursor_y = cursor_pos

                # 检查锤子是否可用（不在冷却中）
                hammer_cooldown = self.game_manager.game.get("hammer_cooldown", 0)
                is_hammer_ready = hammer_cooldown <= 0

                if is_hammer_ready:
                    # 锤子图像尺寸（与UI中的锤子保持一致）
                    hammer_size = 50  # 可以调整大小

                    # 计算锤子绘制位置（以鼠标为中心）
                    hammer_x = cursor_x - hammer_size // 2
                    hammer_y = cursor_y - hammer_size // 2

                    # 绘制锤子图像
                    if (self.game_manager.images and
                            self.game_manager.images.get('hammer_img')):
                        # 使用锤子图像
                        hammer_img = self.game_manager.images['hammer_img']
                        hammer_scaled = pygame.transform.scale(hammer_img, (hammer_size, hammer_size))

                        # 添加轻微的阴影效果
                        shadow_offset = 2
                        shadow_surface = pygame.Surface((hammer_size, hammer_size), pygame.SRCALPHA)
                        shadow_surface.fill((0, 0, 0, 100))  # 半透明黑色阴影
                        self.game_manager.game_surface.blit(shadow_surface,
                                                            (hammer_x + shadow_offset, hammer_y + shadow_offset))

                        # 绘制锤子图像
                        self.game_manager.game_surface.blit(hammer_scaled, (hammer_x, hammer_y))

                        # 添加高亮边框，表示这是可交互的工具
                        hammer_rect = pygame.Rect(hammer_x, hammer_y, hammer_size, hammer_size)
                        pygame.draw.rect(self.game_manager.game_surface, (255, 255, 255), hammer_rect, 2)

                    else:
                        # 没有图像时绘制简单的锤子形状
                        from constants import HAMMER_COLOR

                        # 绘制阴影
                        shadow_rect = pygame.Rect(hammer_x + 2, hammer_y + 2, hammer_size, hammer_size)
                        shadow_surface = pygame.Surface((hammer_size, hammer_size), pygame.SRCALPHA)
                        shadow_surface.fill((0, 0, 0, 100))
                        self.game_manager.game_surface.blit(shadow_surface, shadow_rect.topleft)

                        # 绘制锤子矩形
                        hammer_rect = pygame.Rect(hammer_x, hammer_y, hammer_size, hammer_size)
                        pygame.draw.rect(self.game_manager.game_surface, HAMMER_COLOR, hammer_rect)
                        pygame.draw.rect(self.game_manager.game_surface, (255, 255, 255), hammer_rect, 2)

                        # 绘制简单的锤子图案（十字形）
                        center_x = hammer_x + hammer_size // 2
                        center_y = hammer_y + hammer_size // 2

                        # 垂直线
                        pygame.draw.line(self.game_manager.game_surface, (255, 255, 255),
                                         (center_x, hammer_y + 5), (center_x, hammer_y + hammer_size - 5), 3)
                        # 水平线
                        pygame.draw.line(self.game_manager.game_surface, (255, 255, 255),
                                         (hammer_x + 5, center_y), (hammer_x + hammer_size - 5, center_y), 3)

    def _render_plant_preview(self):
        """渲染植物种植预览"""

        preview = self.game_manager.state_manager.get_plant_preview()
        if not preview:
            return

        # 导入预览绘制函数
        try:
            from utils import draw_plant_preview
            draw_plant_preview(
                self.game_manager.game_surface,
                self.game_manager.scaled_images,
                preview['plant_type'],
                preview['target_row'],
                preview['target_col'],
                preview['can_place'],
                alpha=120  # 半透明效果
            )
        except ImportError:
            # 如果导入失败，跳过植物预览绘制
            pass

    def _render_plant_selection(self):
        """渲染植物选择界面"""
        # 获取退出动画进度
        exit_progress = self.game_manager.animation_manager.get_plant_select_exit_progress()
        # 绘制植物选择网格，并传入选中的植物列表
        plant_rects, finish_btn = ui_manager.draw_plant_select_grid(
            self.game_manager.game_surface,
            self.game_manager.plant_selection_manager.plant_select_grid,
            self.game_manager.animation_manager.plant_select_animation_timer,
            self.game_manager.animation_manager.plant_select_animation_complete,
            self.game_manager.scaled_images,
            self.game_manager.font_small,
            self.game_manager.font_medium,
            self.game_manager.plant_selection_manager.selected_plants_for_game,
            self.game_manager.plant_selection_manager,
            exit_progress
        )

        # 存储开始战斗按钮引用
        self.finish_btn = finish_btn

        # 绘制飞行中的植物（也需要考虑退出动画）
        if exit_progress < 0.8:  # 在动画接近完成前继续显示飞行植物
            self.game_manager.plant_selection_manager.draw_flying_plants(
                self.game_manager.game_surface,
                self.game_manager.scaled_images
            )

    def _render_game_objects(self):
        """渲染游戏对象（植物、僵尸、子弹）"""
        # 正常游戏时绘制游戏对象
        for p in self.game_manager.game["plants"]:
            p.draw(self.game_manager.game_surface)
        for z in self.game_manager.game["zombies"]:
            z.draw(self.game_manager.game_surface)
        for b in self.game_manager.game["bullets"]:
            b.draw(self.game_manager.game_surface)
        if "dandelion_seeds" in self.game_manager.game:
            for seed in self.game_manager.game["dandelion_seeds"]:
                seed.draw(self.game_manager.game_surface)

        # 绘制种子雨卡牌（在所有游戏对象之上）
        if (hasattr(self.game_manager, 'seed_rain_manager') and
                self.game_manager.seed_rain_manager):
            self.game_manager.seed_rain_manager.draw(
                self.game_manager.game_surface,
                self.game_manager.scaled_images
            )

    def _render_trophy(self):
        """渲染奖杯"""
        level_mgr = self.game_manager.game["level_manager"]
        if level_mgr.trophy:
            level_mgr.trophy.draw(self.game_manager.game_surface)
            level_mgr.trophy.draw_particles(self.game_manager.game_surface)

    def _render_fade_effect(self):
        """渲染淡入淡出效果"""
        if self.game_manager.game["fade_state"] != "none":
            fade_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, self.game_manager.game["fade_alpha"]))
            self.game_manager.game_surface.blit(fade_surface, (0, 0))

    def _render_common_ui(self):
        """渲染通用UI元素"""
        # 绘制设置菜单
        if self.game_manager.state_manager.show_settings:
            self._render_settings_menu()

        # 绘制重置确认对话框
        if self.game_manager.state_manager.show_reset_confirm:
            self._render_reset_confirm_dialog()

        # 绘制游戏结束弹窗
        if (self.game_manager.state_manager.game_state == "playing" and
                self.game_manager.game["game_over"]):
            self._render_game_over_dialog()

        # 绘制继续游戏对话框
        if (self.game_manager.state_manager.show_continue_dialog and
                self.game_manager.state_manager.selected_level_for_continue):
            self._render_continue_dialog()

        # 绘制配置重载提示
        if self.game_manager.animation_manager.show_config_reload_message:
            self._render_config_reload_message()

    def _render_settings_menu(self):
        """渲染设置菜单"""
        # 先绘制半透明覆盖层
        overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.game_manager.game_surface.blit(overlay, (0, 0))

        # 再绘制设置菜单内容（保持正常亮度）
        in_game = self.game_manager.state_manager.game_state == "playing"
        ui_manager.show_settings_menu_with_hotreload(
            self.game_manager.game_surface,
            self.game_manager.volume,
            in_game,
            self.game_manager.hot_reload_enabled,
            self.game_manager.font_large,
            self.game_manager.font_medium,
            self.game_manager.font_small,
            self.game_manager.state_manager
        )

    def _render_reset_confirm_dialog(self):
        """渲染重置确认对话框"""
        # 半透明背景
        confirm_overlay = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        confirm_overlay.fill((0, 0, 0, 150))
        self.game_manager.game_surface.blit(confirm_overlay, (0, 0))

        # 对话框
        confirm_popup = pygame.Rect(BASE_WIDTH // 2 - 150, BASE_HEIGHT // 2 - 75, 300, 150)
        pygame.draw.rect(self.game_manager.game_surface, GRAY_DARK, confirm_popup)
        pygame.draw.rect(self.game_manager.game_surface, RED, confirm_popup, 3)

        # 文字
        confirm_text = self.game_manager.font_medium.render("确定重置所有进度？", True, WHITE)
        self.game_manager.game_surface.blit(confirm_text,
                                            confirm_text.get_rect(
                                                center=(confirm_popup.centerx, confirm_popup.centery - 20)))

        # 按钮
        yes_btn = pygame.Rect(confirm_popup.left + 50, confirm_popup.bottom - 50, 80, 30)
        no_btn = pygame.Rect(confirm_popup.right - 130, confirm_popup.bottom - 50, 80, 30)

        pygame.draw.rect(self.game_manager.game_surface, (150, 0, 0), yes_btn)
        pygame.draw.rect(self.game_manager.game_surface, (0, 150, 0), no_btn)

        yes_text = self.game_manager.font_small.render("确定", True, WHITE)
        no_text = self.game_manager.font_small.render("取消", True, WHITE)
        self.game_manager.game_surface.blit(yes_text, yes_text.get_rect(center=yes_btn.center))
        self.game_manager.game_surface.blit(no_text, no_text.get_rect(center=no_btn.center))

    def _render_game_over_dialog(self):
        """渲染游戏结束对话框"""
        _, _, self.game_manager.game["game_over_sound_played"] = ui_manager.show_game_over(
            self.game_manager.game_surface,
            self.game_manager.game["game_over_sound_played"],
            self.game_manager.font_large,
            self.game_manager.font_medium
        )

    def _render_continue_dialog(self):
        """渲染继续游戏对话框"""
        saved_game_info = self.game_manager.game_db.get_saved_game_info(
            self.game_manager.state_manager.selected_level_for_continue
        )
        ui_manager.draw_continue_dialog(
            self.game_manager.game_surface,
            saved_game_info,
            self.game_manager.state_manager.selected_level_for_continue,
            self.game_manager.font_large,
            self.game_manager.font_medium,
            self.game_manager.font_small
        )

    def _render_transition_mask(self):
        """渲染过渡动画遮罩"""
        transition_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        transition_alpha = self.game_manager.state_manager.get_transition_alpha()
        transition_surface.fill((0, 0, 0, transition_alpha))
        self.game_manager.game_surface.blit(transition_surface, (0, 0))

    def _render_config_reload_message(self):
        """渲染配置重载提示消息"""
        alpha = self.game_manager.animation_manager.get_config_reload_message_alpha()

        if alpha > 0:
            # 创建消息表面
            message = "配置已重新加载"
            text_surface = self.game_manager.font_medium.render(message, True, (255, 255, 255))

            # 添加半透明背景
            bg_width = text_surface.get_width() + 20
            bg_height = text_surface.get_height() + 10
            bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, min(alpha, 180)))

            # 计算位置（屏幕右上角）
            x = BASE_WIDTH - bg_width - 20
            y = 20

            # 绘制到游戏表面
            self.game_manager.game_surface.blit(bg_surface, (x, y))

            # 设置文字透明度
            text_surface.set_alpha(alpha)
            text_x = x + 10
            text_y = y + 5
            self.game_manager.game_surface.blit(text_surface, (text_x, text_y))

    def _blit_to_screen(self):
        """将游戏表面绘制到屏幕"""
        if self.game_manager.fullscreen:
            # 先将整个屏幕填充为黑色（确保letterbox区域为黑色）
            self.game_manager.screen.fill((0, 0, 0))  # 明确使用黑色元组

            # 缩放游戏表面
            scaled_surface = pygame.transform.scale(
                self.game_manager.game_surface,
                (int(BASE_WIDTH * self.game_manager.screen_scale),
                 int(BASE_HEIGHT * self.game_manager.screen_scale))
            )

            # 将缩放后的游戏表面居中绘制到屏幕上
            self.game_manager.screen.blit(
                scaled_surface,
                (self.game_manager.screen_offset_x, self.game_manager.screen_offset_y)
            )
        else:
            # 窗口模式直接绘制
            self.game_manager.screen.blit(self.game_manager.game_surface, (0, 0))

        pygame.display.flip()

    def get_plant_selection_rects(self):
        """获取植物选择网格的矩形列表（用于事件处理）"""
        if not self.game_manager.plant_selection_manager.show_plant_select:
            return []

        plant_rects = []
        plant_grid = self.game_manager.plant_selection_manager.plant_select_grid

        # 网格参数（与ui_manager.py中的draw_plant_select_grid保持一致）
        grid_cols = 6
        grid_rows = 5
        cell_width = GRID_SIZE
        cell_height = GRID_SIZE
        cell_spacing = 4

        # 计算起始位置（在战场区域居中）
        total_width = grid_cols * cell_width + (grid_cols - 1) * cell_spacing
        total_height = grid_rows * cell_height + (grid_rows - 1) * cell_spacing
        start_x = BATTLEFIELD_LEFT + (total_battlefield_width - total_width) // 2
        start_y = BATTLEFIELD_TOP + (total_battlefield_height - total_height) // 2

        # 生成可点击的植物矩形
        selected_count_dict = {}
        for plant_type in self.game_manager.plant_selection_manager.selected_plants_for_game:
            selected_count_dict[plant_type] = selected_count_dict.get(plant_type, 0) + 1

        for row in range(grid_rows):
            for col in range(grid_cols):
                plant_data = plant_grid[row][col]
                if plant_data is not None:
                    plant_type = plant_data['type']
                    selected_count = selected_count_dict.get(plant_type, 0)

                    # 只有未选中的植物才可以点击
                    if selected_count == 0:
                        cell_x = start_x + col * (cell_width + cell_spacing)
                        cell_y = start_y + row * (cell_height + cell_spacing)
                        cell_rect = pygame.Rect(cell_x, cell_y, cell_width, cell_height)
                        plant_rects.append((cell_rect, plant_data))

        return plant_rects

    def get_finish_button(self):
        """获取开始战斗按钮矩形（新增）"""
        return self.finish_btn

    def _render_shop(self):
        """渲染商店界面 - 添加金币不足对话框支持"""
        # 绘制背景
        if self.game_manager.images.get('menu_bg_img'):
            self.game_manager.game_surface.blit(self.game_manager.images.get('menu_bg_img'), (0, 0))
        else:
            self.game_manager.game_surface.fill((0, 100, 0))

        # 绘制商店界面
        ui_manager.draw_shop_page(
            self.game_manager.game_surface,
            self.game_manager.animation_manager.level_select_animation_timer,
            self.game_manager.animation_manager.level_select_animation_complete,
            self.game_manager.animation_manager.level_select_exit_animation,
            self.game_manager.animation_manager.menu_animation_timer,
            self.game_manager.font_large,
            self.game_manager.font_medium,
            self.game_manager.state_manager,
            self.game_manager.shop_manager,
            self.game_manager.scaled_images,
            self.game_manager.font_tiny,  # 传递font_tiny
            self.game_manager.font_small,  # 传递font_small
            game_manager=self.game_manager
        )

        # 如果显示金币不足对话框，则在商店页面上方绘制
        if hasattr(self.game_manager.state_manager, 'show_insufficient_coins_dialog') and \
                self.game_manager.state_manager.show_insufficient_coins_dialog:
            item = None
            if hasattr(self.game_manager.state_manager, 'get_insufficient_coins_item'):
                item = self.game_manager.state_manager.get_insufficient_coins_item()

            if item:
                # 绘制金币不足对话框，并获取确认按钮位置
                confirm_btn = ui_manager.draw_insufficient_coins_dialog(
                    self.game_manager.game_surface,
                    item,
                    self.game_manager.coins,
                    self.game_manager.font_large,
                    self.game_manager.font_medium,
                    self.game_manager.font_small
                )

                # 将确认按钮信息存储到state_manager中，供事件处理使用
                if confirm_btn:
                    if not hasattr(self.game_manager.state_manager, 'insufficient_coins_confirm_btn'):
                        # 如果没有这个属性，就动态添加
                        setattr(self.game_manager.state_manager, 'insufficient_coins_confirm_btn', confirm_btn)
                    else:
                        self.game_manager.state_manager.insufficient_coins_confirm_btn = confirm_btn

        # 如果显示购买确认对话框
        if self.game_manager.state_manager.show_purchase_confirm:
            item = self.game_manager.state_manager.get_pending_purchase_item()
            if item:
                ui_manager.draw_purchase_confirm_dialog(
                    self.game_manager.game_surface,
                    item,
                    self.game_manager.coins,
                    self.game_manager.font_large,
                    self.game_manager.font_medium,
                    self.game_manager.font_small
                )