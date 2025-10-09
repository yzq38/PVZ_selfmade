"""
事件处理模块 - 负责处理用户输入、鼠标点击等事件（已修复开始战斗按钮和滑块拖拽，添加小推车点击检测，新增图鉴功能）
"""
import pygame
from ui import *
from .game_logic import *
from rsc_mng.audio_manager import play_sound_with_music_pause, set_sounds_volume
from database import *

from ui import ConveyorBeltManager


class EventHandler:
    """事件处理器 - 处理各种用户输入事件"""

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.conveyor_belt_manager = None
        self.dragging_slider = False
        self.slider_bg_rect = None

    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 在退出前保存游戏进度
                if self.game_manager.should_save_game_on_exit():
                    self.game_manager.game_db.save_game_progress(
                        self.game_manager.game,
                        self.game_manager.music_manager,
                        self.game_manager
                    )
                return False

            elif event.type == pygame.KEYDOWN:
                if self.game_manager.state_manager.is_in_transition():
                    continue

                if event.key == pygame.K_ESCAPE:
                    self.game_manager.toggle_fullscreen()
                elif event.key == pygame.K_SPACE:
                    self._handle_space_key()
                elif event.key == pygame.K_F5:
                    self._handle_f5_key()  # 手动重载配置
                elif event.key == pygame.K_F6:
                    self._handle_f6_key()  # 切换热重载开关
                elif event.key == pygame.K_F7:
                    self._handle_f7_key()  # 显示配置信息

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 在过渡动画期间禁用鼠标点击
                if self.game_manager.state_manager.is_in_transition():
                    continue

                should_continue = self.handle_mouse_click(
                    self.game_manager.transform_mouse_pos(event.pos)
                )
                if should_continue is False:
                    return False  # 传播退出信号

            # 新增：处理右键点击取消选中
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # 在过渡动画期间禁用鼠标点击
                if self.game_manager.state_manager.is_in_transition():
                    continue

                # 右键点击取消当前选中的植物或铲子
                self._handle_right_click_cancel()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # 处理鼠标松开事件，停止拖拽
                self._handle_mouse_release()

            elif event.type == pygame.MOUSEMOTION:
                if not self.game_manager.state_manager.is_in_transition():
                    mouse_pos = self.game_manager.transform_mouse_pos(event.pos)
                    self.handle_mouse_motion(mouse_pos)
                    # 处理滑块拖拽
                    self._handle_slider_drag(mouse_pos)

        return True

    def _handle_mouse_release(self):
        """处理鼠标松开事件"""
        # 停止滑块拖拽
        self.dragging_slider = False
        self.slider_bg_rect = None

    def _handle_slider_drag(self, pos):
        """处理滑块拖拽"""
        if self.dragging_slider and self.slider_bg_rect:
            x, y = pos

            # 计算相对位置（移除范围限制，让滑块完全跟随鼠标）
            relative_x = x - self.slider_bg_rect.left
            # 将相对位置转换为0-1范围的音量值
            self.game_manager.volume = relative_x / self.slider_bg_rect.width
            # 限制音量在有效范围内
            self.game_manager.volume = max(0.0, min(1.0, self.game_manager.volume))

            # 应用新的音量
            self.game_manager.music_manager.set_volume(self.game_manager.volume)
            set_sounds_volume(self.game_manager.sounds, self.game_manager.volume)

    def handle_mouse_motion(self, pos):
        """处理鼠标移动事件"""
        x, y = pos

        # 清除之前的悬停状态
        self.game_manager.state_manager.clear_hover_level()

        if self.game_manager.state_manager.game_state == "main_menu":
            self._handle_main_menu_hover(pos)
        elif self.game_manager.state_manager.game_state == "level_select":
            self._handle_level_select_hover(pos)
        elif self.game_manager.state_manager.game_state == "playing":
            self._handle_playing_hover(pos)
        elif self.game_manager.state_manager.game_state == "shop":
            self._handle_shop_hover(pos)
        elif self.game_manager.state_manager.game_state == "codex":
            self._handle_codex_hover(pos)  # 图鉴主页悬浮处理
        elif self.game_manager.state_manager.game_state == "codex_detail":
            self._handle_codex_detail_hover(pos)  # 新增：详细图鉴悬浮处理

        # 处理设置菜单悬浮（在任何状态下都可能显示）
        if self.game_manager.state_manager.show_settings:
            self._handle_settings_hover(pos)

    def _handle_codex_click(self, x, y):
        """处理图鉴界面点击 - 更新支持详细图鉴页面"""
        if self.game_manager.animation_manager.level_select_exit_animation:
            return

        if not self.game_manager.animation_manager.level_select_animation_complete:
            return

        # 图鉴主页 - 处理主页按钮点击
        from ui import draw_codex_page
        back_btn, plant_btn, zombie_btn = draw_codex_page(
            self.game_manager.game_surface,
            self.game_manager.animation_manager.level_select_animation_timer,
            self.game_manager.animation_manager.level_select_animation_complete,
            self.game_manager.animation_manager.level_select_exit_animation,
            self.game_manager.animation_manager.menu_animation_timer,
            self.game_manager.font_large,
            self.game_manager.font_medium,
            self.game_manager.state_manager
        )

        # 处理返回按钮点击
        if back_btn.collidepoint(x, y):
            self.game_manager.animation_manager.start_level_select_exit_animation("main_menu")
            return

        # 处理植物图鉴按钮点击
        if plant_btn.collidepoint(x, y):
            self.game_manager.state_manager.switch_to_codex_detail("plants")
            return

        # 处理僵尸图鉴按钮点击
        if zombie_btn.collidepoint(x, y):
            self.game_manager.state_manager.switch_to_codex_detail("zombies")
            return

    def _handle_codex_hover(self, pos):
        """处理图鉴页面悬浮 - 图鉴主页"""
        if self.game_manager.animation_manager.level_select_exit_animation:
            return

        x, y = pos

        # 图鉴主页悬浮处理
        # 检查返回按钮悬浮
        back_btn = pygame.Rect(20, 20, 100, 40)  # 与draw_codex_page保持一致
        if back_btn.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("back", "codex")
            return

        # 检查植物图鉴按钮悬浮
        button_width = 320
        button_height = 400
        button_spacing = 60

        total_width = 2 * button_width + button_spacing
        start_x = (BASE_WIDTH - total_width) // 2
        start_y = 120

        plant_btn = pygame.Rect(start_x, start_y, button_width, button_height)
        zombie_btn = pygame.Rect(start_x + button_width + button_spacing, start_y, button_width, button_height)

        if plant_btn.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("plants", "codex")
        elif zombie_btn.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("zombies", "codex")

    def _handle_codex_detail_click(self, x, y):
        """处理详细图鉴页面点击"""
        # 获取详细图鉴页面的按钮位置
        from ui import draw_codex_detail_page

        # 临时绘制以获取按钮位置（这不是最优解，但能工作）
        temp_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        back_btn, grid_rects = draw_codex_detail_page(
            temp_surface,
            self.game_manager.state_manager.get_codex_detail_type(),
            self.game_manager.state_manager.get_selected_codex_item(),
            self.game_manager.font_large,
            self.game_manager.font_medium,
            self.game_manager.font_small,
            self.game_manager.font_tiny,
            self.game_manager.scaled_images,
            self.game_manager.state_manager,

        )

        # 处理返回按钮点击
        if back_btn.collidepoint(x, y):
            self.game_manager.state_manager.switch_back_to_codex()
            return

        # 处理网格点击
        for i, (grid_rect, item_data) in enumerate(grid_rects):
            if grid_rect.collidepoint(x, y):
                self.game_manager.state_manager.set_selected_codex_item(i)
                return

    def _handle_codex_detail_hover(self, pos):
        """处理详细图鉴页面悬浮"""
        x, y = pos

        # 检查返回按钮悬浮
        back_btn = pygame.Rect(20, 20, 100, 40)
        if back_btn.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("back", "codex_detail")
            return

        # 检查网格项目悬浮
        grid_cols = 6
        grid_rows = 5
        cell_size = 80
        cell_spacing = 8

        grid_start_x = 50
        grid_start_y = 120

        # 获取当前图鉴数据以确定有效范围
        if self.game_manager.state_manager.get_codex_detail_type() == "plants":
            from ui import get_plants_codex_data
            codex_data = get_plants_codex_data()
        else:
            from ui import get_zombies_codex_data
            codex_data = get_zombies_codex_data()

        for row in range(grid_rows):
            for col in range(grid_cols):
                index = row * grid_cols + col
                if index >= len(codex_data):
                    break  # 超出数据范围就停止

                cell_x = grid_start_x + col * (cell_size + cell_spacing)
                cell_y = grid_start_y + row * (cell_size + cell_spacing)
                cell_rect = pygame.Rect(cell_x, cell_y, cell_size, cell_size)

                if cell_rect.collidepoint(x, y):
                    self.game_manager.state_manager.set_hover_button(f"grid_{index}", "codex_detail")
                    return

    def _handle_settings_click(self, x, y):
        """处理设置菜单点击 - 修复重置逻辑"""
        in_game = self.game_manager.state_manager.game_state == "playing"
        continue_btn, quit_btn, slider_bg, slider, fullscreen_btn, reset_btn, restart_game_btn, return_to_level_select_btn = show_settings_menu_with_hotreload(
            self.game_manager.game_surface, self.game_manager.volume, in_game,
            self.game_manager.hot_reload_enabled,
            self.game_manager.font_large, self.game_manager.font_medium, self.game_manager.font_small
        )

        if continue_btn.collidepoint(x, y):
            self.game_manager.state_manager.show_settings = False
            self.game_manager.state_manager.game_paused = False

        elif quit_btn.collidepoint(x, y):
            if in_game:
                if self.game_manager.should_save_game_on_exit():
                    self.game_manager.game_db.save_game_progress(
                        self.game_manager.game, self.game_manager.music_manager, self.game_manager
                    )
                self.game_manager.state_manager.switch_to_main_menu()
                # 修复：使用新的重置方法
                self.game_manager.game = self.game_manager.state_manager.reset_game()
                self.game_manager.plant_selection_manager.clear_plant_selection_state()
            else:
                if self.game_manager.state_manager.game_state == "playing" and self.game_manager.should_save_game_on_exit():
                    self.game_manager.game_db.save_game_progress(
                        self.game_manager.game, self.game_manager.music_manager, self.game_manager
                    )
                return False  # 退出游戏

            self.game_manager.state_manager.show_settings = False
            self.game_manager.state_manager.game_paused = False

        elif fullscreen_btn.collidepoint(x, y):
            self.game_manager.toggle_fullscreen()

        elif slider_bg.collidepoint(x, y) or slider.collidepoint(x, y):
            # 开始拖拽滑块
            self.dragging_slider = True
            self.slider_bg_rect = slider_bg
            # 立即更新音量到点击位置
            self.game_manager.volume = (x - slider_bg.left) / slider_bg.width
            self.game_manager.volume = max(0, min(1, self.game_manager.volume))
            self.game_manager.music_manager.set_volume(self.game_manager.volume)
            set_sounds_volume(self.game_manager.sounds, self.game_manager.volume)

        elif reset_btn and reset_btn.collidepoint(x, y):
            self.game_manager.state_manager.show_reset_confirmation()

        elif restart_game_btn and restart_game_btn.collidepoint(x, y):
            self._handle_restart_game_click()

        elif return_to_level_select_btn and return_to_level_select_btn.collidepoint(x, y):
            # 新增：处理返回选关页面按钮点击
            self._handle_return_to_level_select_click()

        return True

    def _handle_main_menu_hover(self, pos):
        """处理主菜单悬浮"""
        if (self.game_manager.animation_manager.menu_animation_complete and
                not self.game_manager.animation_manager.menu_exit_animation):

            x, y = pos
            # 主菜单按钮参数（与draw_main_menu保持一致）
            menu_width = 250
            menu_x = BASE_WIDTH - menu_width - 50
            menu_y = 150

            button_labels = ["主线模式", "挑战模式", "无尽模式", "设置"]

            for i, label in enumerate(button_labels):
                btn_y = menu_y + i * 70
                btn_rect = pygame.Rect(menu_x, btn_y, menu_width, 50)

                if btn_rect.collidepoint(x, y):
                    self.game_manager.state_manager.set_hover_button(i, "main_menu")
                    break
            # 检查商店按钮悬浮（在现有按钮检测后面添加）
            if (self.game_manager.animation_manager.menu_animation_complete and
                    not self.game_manager.animation_manager.menu_exit_animation):

                # 商店按钮参数（与draw_main_menu保持一致）
                shop_button_size = 80
                shop_x = 100
                shop_y = BASE_HEIGHT // 2 + 50
                shop_rect = pygame.Rect(shop_x, shop_y, shop_button_size, shop_button_size)

                if shop_rect.collidepoint(x, y):
                    self.game_manager.state_manager.set_hover_button("shop", "main_menu")
                    return  # 找到悬浮按钮后返回

                # 检查图鉴按钮悬浮（新增）
                codex_button_size = CODEX_BUTTON_SIZE
                codex_x = CODEX_BUTTON_X
                codex_y = CODEX_BUTTON_Y
                codex_rect = pygame.Rect(codex_x, codex_y, codex_button_size, codex_button_size)

                if codex_rect.collidepoint(x, y):
                    self.game_manager.state_manager.set_hover_button("codex", "main_menu")
                    return  # 找到悬浮按钮后返回

    def _handle_playing_hover(self, pos):
        """处理游戏界面悬停"""
        if self.game_manager.state_manager.should_pause_game_logic():
            return

        x, y = pos

        # 检查设置按钮悬停
        settings_rect = pygame.Rect(SETTINGS_BUTTON_X, SETTINGS_BUTTON_Y,
                                    SETTINGS_BUTTON_WIDTH, SETTINGS_BUTTON_HEIGHT)
        if settings_rect.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("settings", "game_ui")
            self.game_manager.state_manager.clear_plant_preview()
            return

        # 关键修复：锤子跟随鼠标在任何模式下都要处理（提前到模式检查之前）
        selected = self.game_manager.game["selected"]
        if selected == "hammer":
            self.game_manager.state_manager.set_hammer_cursor_pos(x, y)
            # 锤子模式下清除植物预览，但不直接返回，让后续逻辑继续处理其他悬停
        # 处理种子雨模式的植物预览
        if (hasattr(self.game_manager, 'seed_rain_manager') and
                    self.game_manager.seed_rain_manager and
                    self.game_manager.seed_rain_manager.enabled):
            self._handle_seed_rain_plant_preview(x, y)
            return
        # 优先处理传送带悬停（如果是传送带模式）
        if (hasattr(self.game_manager, 'conveyor_belt_manager') and
                self.game_manager.conveyor_belt_manager is not None and
                self.game_manager.game["level_manager"].current_level != 18):
            # 传送带模式：处理传送带相关的悬停
            self.game_manager.conveyor_belt_manager.handle_hover(pos)

            # 修改：添加传送带模式下的植物预览处理
            self._handle_conveyor_belt_plant_preview(x, y)
            return

        # 非传送带模式：处理传统UI悬停
        # 检查铲子悬停
        shovel_rect = pygame.Rect(self.game_manager.shovel["x"], self.game_manager.shovel["y"],
                                  self.game_manager.shovel["width"], self.game_manager.shovel["height"])
        if shovel_rect.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("shovel", "game_ui")
            self.game_manager.state_manager.clear_plant_preview()
            return

        # 检查锤子悬停
        if (hasattr(self.game_manager, 'shop_manager') and
                self.game_manager.shop_manager.has_hammer()):
            hammer_rect = pygame.Rect(HAMMER_X, HAMMER_Y, HAMMER_WIDTH, HAMMER_HEIGHT)
            if hammer_rect.collidepoint(x, y):
                self.game_manager.state_manager.set_hover_button("hammer", "game_ui")
                self.game_manager.state_manager.clear_plant_preview()
                return

        # 检查卡片悬停
        cards = self.game_manager.get_available_cards_for_current_state()
        for i, card in enumerate(cards):
            card_x = CARD_START_X + i * CARD_WIDTH
            card_rect = pygame.Rect(card_x, CARD_Y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(x, y):
                if self._is_card_hoverable(card):
                    self.game_manager.state_manager.set_hover_button(f"card_{i}", "game_ui")
                self.game_manager.state_manager.clear_plant_preview()
                return

        # 处理植物种植预览（非传送带模式）
        if not self.game_manager.plant_selection_manager.show_plant_select:
            from utils import update_plant_preview_on_mouse_move
            update_plant_preview_on_mouse_move(
                self.game_manager.state_manager,
                self.game_manager.game,
                cards,
                x, y,
                self.game_manager.game["selected"]
            )

        # 检查植物选择界面悬停
        if self.game_manager.plant_selection_manager.show_plant_select:
            self._handle_plant_select_hover(pos)

    def _handle_conveyor_belt_plant_preview(self, x, y):
        """处理传送带模式下的植物预览 - 修复状态同步和格子占用检查"""
        from utils import pixel_to_grid, can_place_plant_at_position, should_show_plant_preview

        # 关键修复：在清除预览之前，先检查传送带状态
        conveyor_selected = None
        if (hasattr(self.game_manager, 'conveyor_belt_manager') and
                self.game_manager.conveyor_belt_manager is not None):
            selected_card = self.game_manager.conveyor_belt_manager.get_selected_card()
            if selected_card:
                conveyor_selected = selected_card.card_type

        # 如果传送带有选中但游戏状态没有，立即同步
        if conveyor_selected and self.game_manager.game["selected"] != conveyor_selected:
            self.game_manager.game["selected"] = conveyor_selected
        # 如果传送带没有选中但游戏状态有非工具选中，清除游戏状态
        elif not conveyor_selected and self.game_manager.game["selected"] not in [None, "shovel", "hammer"]:
            self.game_manager.game["selected"] = None

        # 现在检查最终的选中状态
        selected_plant = conveyor_selected or self.game_manager.game["selected"]

        # 如果没有选中植物或选中的是工具，清除预览并返回
        if not selected_plant or selected_plant in ["shovel", "hammer"]:
            self.game_manager.state_manager.clear_plant_preview()
            return

        # 获取鼠标位置对应的网格坐标
        row, col = pixel_to_grid(x, y)
        if row is None or col is None:
            self.game_manager.state_manager.clear_plant_preview()
            return

        # 关键修复：使用should_show_plant_preview检查是否应该显示预览
        should_show, can_place = should_show_plant_preview(
            self.game_manager.game, selected_plant, row, col
        )

        if not should_show:
            # 如果不应该显示预览（比如格子已有植物），清除预览
            self.game_manager.state_manager.clear_plant_preview()
            return

        # 进一步检查是否可以在该位置种植（考虑传送门等因素）
        can_place = can_place_plant_at_position(
            self.game_manager.game,
            selected_plant,
            row, col,
            self.game_manager.game["level_manager"]
        )

        # 传送带模式下，不检查阳光和卡片冷却，只要选中了就显示预览
        # 设置预览状态
        self.game_manager.state_manager.set_plant_preview(
            selected_plant, row, col, can_place
        )

    def _handle_seed_rain_plant_preview(self, x, y):
        """处理种子雨模式下的植物预览"""
        from utils import pixel_to_grid, should_show_plant_preview

        selected_plant = self.game_manager.game["selected"]

        # 如果没有选中植物或选中的是工具，清除预览
        if not selected_plant or selected_plant in ["shovel", "hammer"]:
            self.game_manager.state_manager.clear_plant_preview()
            return

        # 获取鼠标位置对应的网格坐标
        row, col = pixel_to_grid(x, y)
        if row is None or col is None:
            self.game_manager.state_manager.clear_plant_preview()
            return

        # 检查是否应该显示预览
        should_show, can_place = should_show_plant_preview(
            self.game_manager.game, selected_plant, row, col
        )

        if should_show:
            # 设置预览状态
            self.game_manager.state_manager.set_plant_preview(
                selected_plant, row, col, can_place
            )
        else:
            self.game_manager.state_manager.clear_plant_preview()

    def _is_battlefield_click(self, x, y):
        """检查是否点击了战场区域"""
        adj_x = x - BATTLEFIELD_LEFT
        adj_y = y - BATTLEFIELD_TOP
        return (0 <= adj_x < total_battlefield_width and
                0 <= adj_y < total_battlefield_height)

    def _handle_plant_preview(self, x, y, cards):
        """处理植物种植预览"""
        from utils import pixel_to_grid, can_place_plant_at_position

        # 清除之前的预览状态
        self.game_manager.state_manager.clear_plant_preview()

        # 检查是否选中了植物卡片
        selected_plant = self.game_manager.game["selected"]
        if not selected_plant or selected_plant == "shovel":
            return

        # 检查选中的是否是有效的植物类型
        valid_plant_types = [card["type"] for card in cards]
        if selected_plant not in valid_plant_types:
            return

        # 获取选中植物的卡片信息
        selected_card = None
        for card in cards:
            if card["type"] == selected_plant:
                selected_card = card
                break

        if not selected_card:
            return

        # **新增：检查是否有足够的阳光 - 阳光不足时不显示预览**
        if self.game_manager.game["sun"] < selected_card["cost"]:
            return

        # **新增：检查卡片是否在冷却中 - 冷却中不显示预览**
        if not self._can_select_card(selected_card):
            return

        # 获取鼠标位置对应的网格坐标
        row, col = pixel_to_grid(x, y)
        if row is None or col is None:
            return

        # 检查是否可以在该位置种植
        can_place = can_place_plant_at_position(
            self.game_manager.game,
            selected_plant,
            row, col,
            self.game_manager.game["level_manager"]
        )

        # 设置预览状态
        self.game_manager.state_manager.set_plant_preview(
            selected_plant, row, col, can_place
        )

    def _handle_plant_select_hover(self, pos):
        """处理植物选择界面悬浮"""
        x, y = pos

        # 检查开始战斗按钮
        finish_btn = self.game_manager.renderer_manager.get_finish_button()
        if finish_btn and finish_btn.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("start_battle", "plant_select")
            return

        # 检查植物网格悬浮
        plant_rects = self.game_manager.renderer_manager.get_plant_selection_rects()
        for i, (plant_rect, plant_data) in enumerate(plant_rects):
            if plant_rect.collidepoint(x, y):
                self.game_manager.state_manager.set_hover_button(f"plant_{i}", "plant_select")
                break

    def _handle_settings_hover(self, pos):
        """处理设置菜单悬浮"""
        x, y = pos

        # 设置菜单按钮检测（需要与show_settings_menu_with_hotreload保持一致）
        popup_width = 400
        popup_height = 400 if self.game_manager.state_manager.game_state == "playing" else 300  # 更新高度
        popup = pygame.Rect((BASE_WIDTH - popup_width) // 2,
                            (BASE_HEIGHT - popup_height) // 2,
                            popup_width, popup_height)

        in_game = self.game_manager.state_manager.game_state == "playing"

        # 全屏按钮
        fullscreen_btn = pygame.Rect(popup.left + 75, popup.top + 120, 250, 40)
        if fullscreen_btn.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("fullscreen", "settings")
            return

        # 重置按钮（主菜单）
        if not in_game:
            reset_btn = pygame.Rect(popup.left + 75, popup.top + 175, 250, 40)
            if reset_btn.collidepoint(x, y):
                self.game_manager.state_manager.set_hover_button("reset", "settings")
                return

        # 重新开始按钮（游戏内）
        if in_game:
            restart_game_btn = pygame.Rect(popup.left + 75, popup.top + 175, 250, 40)
            if restart_game_btn.collidepoint(x, y):
                self.game_manager.state_manager.set_hover_button("restart_game", "settings")
                return

            # 新增：返回选关页面按钮悬浮检测（游戏内）
            return_to_level_select_btn = pygame.Rect(popup.left + 75, popup.top + 230, 250, 40)
            if return_to_level_select_btn.collidepoint(x, y):
                self.game_manager.state_manager.set_hover_button("return_level_select", "settings")
                return

        # 继续/返回主页按钮
        if not in_game:
            continue_btn = pygame.Rect(popup.left + 50, popup.top + 235, 140, 35)  # 主菜单位置
            quit_btn = pygame.Rect(popup.left + 210, popup.top + 235, 140, 35)
        else:
            continue_btn = pygame.Rect(popup.left + 50, popup.top + 285, 140, 35)  # 游戏内位置（更低）
            quit_btn = pygame.Rect(popup.left + 210, popup.top + 285, 140, 35)

        if continue_btn.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("continue", "settings")
        elif quit_btn.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("quit", "settings")

    def _is_card_hoverable(self, card):
        """检查卡片是否可以悬浮高亮"""
        level_manager = self.game_manager.game["level_manager"]

        # 检查向日葵是否可用
        if card["type"] == "sunflower" and not level_manager.can_plant_sunflower():
            return False

        # 检查冷却状态
        card_cooldowns = self.game_manager.game.get("card_cooldowns", {})
        needs_cooldown = (level_manager.has_card_cooldown() or
                          self.game_manager.level_settings.get("all_card_cooldown", False) or
                          level_manager.current_level == 8)

        if needs_cooldown and card["type"] in card_cooldowns:
            if card_cooldowns[card["type"]] > 0:
                return False

        return True

    def _handle_level_select_hover(self, pos):
        """处理关卡选择页面的鼠标悬浮"""
        if self.game_manager.animation_manager.level_select_exit_animation:
            return

        x, y = pos

        # 先检查返回按钮悬浮
        back_btn = pygame.Rect(20, 20, 100, 40)  # 与draw_level_select保持一致
        if back_btn.collidepoint(x, y):
            self.game_manager.state_manager.set_hover_button("back", "level_select")
            # 清除关卡悬浮状态
            self.game_manager.state_manager.clear_hover_level()
            return

        # 重新计算关卡按钮位置（与draw_level_select中的逻辑保持一致）
        grid_width = 7
        grid_height = 4
        level_size = 80
        level_spacing = 20
        grid_start_x = (BASE_WIDTH - (grid_width * (level_size + level_spacing) - level_spacing)) // 2
        grid_start_y = 100

        hover_level = None
        hovered_level_button = None

        for row in range(grid_height):
            for col in range(grid_width):
                level_num = row * grid_width + col + 1
                if level_num > 28:  # 最多28关
                    break

                level_x = grid_start_x + col * (level_size + level_spacing)
                level_y = grid_start_y + row * (level_size + level_spacing)
                level_rect = pygame.Rect(level_x, level_y, level_size, level_size)

                if level_rect.collidepoint(x, y):
                    hover_level = level_num
                    hovered_level_button = f"level_{level_num}"
                    break

        # 更新悬浮状态
        if hover_level != self.game_manager.state_manager.hover_level:
            if hover_level:
                # 设置关卡悬浮（用于显示工具提示）
                self.game_manager.state_manager.set_hover_level(hover_level, pos)
                # 设置按钮悬浮（用于高亮效果）
                self.game_manager.state_manager.set_hover_button(hovered_level_button, "level_select")
            else:
                # 清除所有悬浮状态
                self.game_manager.state_manager.clear_hover_level()
                self.game_manager.state_manager.clear_hover_button()
        elif hover_level:
            # 如果是同一个关卡，但鼠标位置改变了，更新位置（用于工具提示跟随鼠标）
            self.game_manager.state_manager.set_hover_level(hover_level, pos)
            self.game_manager.state_manager.set_hover_button(hovered_level_button, "level_select")

    def _handle_space_key(self):
        """处理空格键事件"""
        # 只在游戏进行中且游戏未结束时响应空格键
        if (self.game_manager.state_manager.game_state == "playing" and
                not self.game_manager.game["game_over"] and
                not self.game_manager.state_manager.show_reset_confirm and
                not self.game_manager.state_manager.show_continue_dialog):

            if self.game_manager.state_manager.show_settings:
                # 如果设置窗口已打开，关闭它并继续游戏
                self.game_manager.state_manager.show_settings = False
                self.game_manager.state_manager.game_paused = False
            else:
                # 如果设置窗口未打开，打开它并暂停游戏
                self.game_manager.state_manager.show_settings = True
                self.game_manager.state_manager.game_paused = True

    def _handle_f5_key(self):
        """处理F5键 - 手动重载配置"""
        if self.game_manager.state_manager.game_state == "playing":
            self.game_manager.manual_reload_config()

    def _handle_f6_key(self):
        """处理F6键 - 切换热重载开关"""
        self.game_manager.toggle_hot_reload()

    def _handle_f7_key(self):
        """处理F7键 - 显示配置信息"""
        self.game_manager.show_config_info()

    def _handle_insufficient_coins_dialog_click(self, x, y):
        """处理金币不足对话框点击 - 新增方法"""
        from ui import draw_insufficient_coins_dialog

        # 获取商品信息
        item = self.game_manager.state_manager.get_insufficient_coins_item()
        if not item:
            self.game_manager.state_manager.hide_insufficient_coins_dialog()
            return True

        # 临时绘制对话框以获取按钮位置（这不是最优解，但能工作）
        temp_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        confirm_btn = draw_insufficient_coins_dialog(
            temp_surface,
            item,
            self.game_manager.coins,
            self.game_manager.font_large,
            self.game_manager.font_medium,
            self.game_manager.font_small
        )

        if confirm_btn and confirm_btn.collidepoint(x, y):
            # 点击确认按钮，关闭对话框
            self.game_manager.state_manager.hide_insufficient_coins_dialog()

        return True  # 消费掉点击事件，不传递给下层

    def handle_mouse_click(self, pos):
        """处理鼠标点击事件"""
        x, y = pos
        # 处理金币不足对话框
        if self.game_manager.state_manager.show_insufficient_coins_dialog:
            return self._handle_insufficient_coins_dialog_click(x, y)

        # 处理继续游戏对话框
        if (self.game_manager.state_manager.show_continue_dialog and
                self.game_manager.state_manager.selected_level_for_continue):
            return self._handle_continue_dialog_click(x, y)

        # 处理重置确认对话框
        if self.game_manager.state_manager.show_reset_confirm:
            return self._handle_reset_confirm_click(x, y)

        # 检查是否点击了奖杯
        if self._handle_trophy_click(x, y):
            return True

        # 处理设置菜单
        if self.game_manager.state_manager.show_settings:
            return self._handle_settings_click(x, y)

        # 处理不同游戏状态的点击
        state = self.game_manager.state_manager.game_state
        if state == "main_menu":
            self._handle_main_menu_click(x, y)
        elif state == "level_select":
            self._handle_level_select_click(x, y)
        elif state == "playing":
            self._handle_playing_click(x, y)
        elif state == "shop":
            self._handle_shop_click(x, y)
        elif state == "codex":
            self._handle_codex_click(x, y)  # 图鉴主页点击处理
        elif state == "codex_detail":
            self._handle_codex_detail_click(x, y)  # 新增：详细图鉴点击处理

        return True

    def _handle_shop_click(self, x, y):
        """处理商店界面点击"""
        if self.game_manager.animation_manager.level_select_exit_animation:
            return

        if not self.game_manager.animation_manager.level_select_animation_complete:
            return

        # 如果正在显示购买确认对话框，优先处理
        if self.game_manager.state_manager.show_purchase_confirm:
            self._handle_purchase_confirm_click(x, y)
            return

        # 获取商店界面的所有可点击元素
        back_btn, item_rects, prev_btn, next_btn = draw_shop_page(
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
            self.game_manager.font_tiny,
            self.game_manager.font_small
        )

        # 处理返回按钮点击
        if back_btn.collidepoint(x, y):
            self.game_manager.animation_manager.start_level_select_exit_animation("main_menu")
            return

        # 处理分页按钮点击
        if prev_btn and prev_btn.collidepoint(x, y):
            self.game_manager.shop_manager.prev_page()
            return

        if next_btn and next_btn.collidepoint(x, y):
            self.game_manager.shop_manager.next_page()
            return

        # 处理购买按钮点击（修改：只检测购买按钮区域）
        for item_rect, item, item_index in item_rects:
            # 计算购买按钮的具体位置
            buy_btn_rect = pygame.Rect(
                item_rect.x + 20,
                item_rect.y + 115,
                item_rect.width - 40,
                20
            )

            if buy_btn_rect.collidepoint(x, y):
                # 只有未购买的商品才能点击购买按钮
                if not self.game_manager.shop_manager.is_purchased(item['id']):
                    # 显示购买确认对话框
                    self.game_manager.state_manager.show_purchase_confirmation(item)
                break

    def _handle_purchase_confirm_click(self, x, y):
        """处理购买确认对话框点击"""
        from ui import draw_purchase_confirm_dialog

        # 获取待购买的物品
        item = self.game_manager.state_manager.get_pending_purchase_item()
        if not item:
            self.game_manager.state_manager.hide_purchase_confirmation()
            return

        # 临时绘制对话框以获取按钮位置
        temp_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
        confirm_btn, cancel_btn = draw_purchase_confirm_dialog(
            temp_surface,
            item,
            self.game_manager.coins,
            self.game_manager.font_large,
            self.game_manager.font_medium,
            self.game_manager.font_small
        )

        if confirm_btn and confirm_btn.collidepoint(x, y):
            # 点击确认购买
            self._handle_shop_item_purchase(item, 0)
            self.game_manager.state_manager.hide_purchase_confirmation()
        elif cancel_btn and cancel_btn.collidepoint(x, y):
            # 点击取消
            self.game_manager.state_manager.hide_purchase_confirmation()

        return True

    def _handle_shop_item_purchase(self, item, item_index):
        """处理商品购买 - 添加金币检查"""
        # 检查是否已购买
        if self.game_manager.shop_manager.is_purchased(item['id']):
            return

        # 检查金币是否足够
        if self.game_manager.coins < item['price']:
            # 显示金币不足对话框
            self.game_manager.state_manager.show_insufficient_coins_dialog_for_item(item)
            return

        # 执行购买
        success = self.game_manager.shop_manager.purchase_item(item['id'])
        if success:
            # 扣除金币
            self.game_manager.add_coins(-item['price'])  # 使用负数来扣除金币

            # 特殊处理不同类型的商品
            if item['id'] == 'cart':
                pass
            elif item['id'] == 'extra_sun':
                print("额外阳光已购买！下一关开始时将获得额外阳光")
            # 可以继续添加其他商品的特殊效果

        else:
            print(f"购买 {item['name']} 失败")

    def _handle_shop_hover(self, pos):
        """处理商店界面悬浮"""
        x, y = pos

        # 获取当前页面的商品数量
        current_items = self.game_manager.shop_manager.get_current_page_items()

        # 计算商品网格布局（与draw_shop_page保持一致）
        grid_cols = 4
        item_width = 120
        item_height = 140
        item_spacing_x = 30
        item_spacing_y = 20

        total_grid_width = grid_cols * item_width + (grid_cols - 1) * item_spacing_x
        grid_start_x = (BASE_WIDTH - total_grid_width) // 2
        grid_start_y = 120

        # 检查商品悬浮
        for i, item in enumerate(current_items):
            row = i // grid_cols
            col = i % grid_cols

            item_x = grid_start_x + col * (item_width + item_spacing_x)
            item_y = grid_start_y + row * (item_height + item_spacing_y)
            item_rect = pygame.Rect(item_x, item_y, item_width, item_height)

            if item_rect.collidepoint(x, y):
                self.game_manager.state_manager.set_hover_button(f"item_{i}", "shop")
                return

        # 检查分页按钮悬浮
        page_y = grid_start_y + (2 * item_height + item_spacing_y) + 40

        prev_btn = pygame.Rect(BASE_WIDTH // 2 - 120, page_y, 80, 35)
        next_btn = pygame.Rect(BASE_WIDTH // 2 + 40, page_y, 80, 35)

        if prev_btn.collidepoint(x, y) and self.game_manager.shop_manager.can_prev_page():
            self.game_manager.state_manager.set_hover_button("prev_page", "shop")
        elif next_btn.collidepoint(x, y) and self.game_manager.shop_manager.can_next_page():
            self.game_manager.state_manager.set_hover_button("next_page", "shop")

    def _handle_continue_dialog_click(self, x, y):
        """处理继续游戏对话框点击"""
        saved_game_info = self.game_manager.game_db.get_saved_game_info(
            self.game_manager.state_manager.selected_level_for_continue
        )
        continue_btn, restart_btn, back_btn = draw_continue_dialog(
            self.game_manager.game_surface, saved_game_info,
            self.game_manager.state_manager.selected_level_for_continue,
            self.game_manager.font_large, self.game_manager.font_medium, self.game_manager.font_small
        )

        if continue_btn.collidepoint(x, y):
            # 继续游戏
            saved_data = self.game_manager.game_db.get_saved_game(
                self.game_manager.state_manager.selected_level_for_continue
            )
            if saved_data and saved_data[
                "current_level"] == self.game_manager.state_manager.selected_level_for_continue:
                self.game_manager.state_manager.set_pending_game_data(
                    saved_data, self.game_manager.state_manager.selected_level_for_continue
                )
            else:
                self.game_manager.state_manager.set_pending_game_data(
                    None, self.game_manager.state_manager.selected_level_for_continue
                )
            self.game_manager.state_manager.start_level_transition_animation()

        elif restart_btn.collidepoint(x, y):
            # 重新开始
            self.game_manager.game_db.clear_saved_game(
                self.game_manager.state_manager.selected_level_for_continue
            )
            self.game_manager.state_manager.set_pending_game_data(
                None, self.game_manager.state_manager.selected_level_for_continue
            )
            self.game_manager.state_manager.start_level_transition_animation()

        elif back_btn.collidepoint(x, y):
            # 返回选关页面
            self.game_manager.state_manager.hide_continue_dialog()

        return True

    def _handle_reset_confirm_click(self, x, y):
        """处理重置确认对话框点击"""
        confirm_popup = pygame.Rect(BASE_WIDTH // 2 - 150, BASE_HEIGHT // 2 - 75, 300, 150)
        yes_btn = pygame.Rect(confirm_popup.left + 50, confirm_popup.bottom - 50, 80, 30)
        no_btn = pygame.Rect(confirm_popup.right - 130, confirm_popup.bottom - 50, 80, 30)

        if yes_btn.collidepoint(x, y):
            # 确认重置
            self.game_manager.game_db.reset_progress()
            self.game_manager.state_manager.hide_reset_confirmation()
            self.game_manager.state_manager.game_paused = False
        elif no_btn.collidepoint(x, y):
            # 取消重置
            self.game_manager.state_manager.show_reset_confirm = False
            self.game_manager.state_manager.show_settings = True  # 返回设置菜单

        return True

    def _handle_trophy_click(self, x, y):
        """处理奖杯点击"""
        if (self.game_manager.state_manager.game_state == "playing" and
                not self.game_manager.game["game_over"] and
                self.game_manager.game["level_manager"].trophy and
                self.game_manager.game["level_manager"].trophy.check_click((x, y))):

            # 播放胜利音效并暂停背景音乐
            if self.game_manager.sounds.get("victory"):
                play_sound_with_music_pause(
                    self.game_manager.sounds["victory"],
                    music_manager=self.game_manager.music_manager
                )

            self.game_manager.game["fade_state"] = "fading_out"
            self.game_manager.game["fade_timer"] = 0
            return True
        return False

    def _handle_restart_game_click(self):
        """处理重新开始游戏点击"""
        if self.game_manager.state_manager.game_state == "playing":
            current_level = self.game_manager.game["level_manager"].current_level

            # 使用新的重置方法，确保传送门系统被正确重新初始化
            self.game_manager.reset_game_with_initialization(current_level)

            # 关闭设置菜单
            self.game_manager.state_manager.show_settings = False
            self.game_manager.state_manager.game_paused = self.game_manager.plant_selection_manager.show_plant_select

    def _handle_main_menu_click(self, x, y):
        """处理主菜单点击"""
        if (self.game_manager.animation_manager.menu_animation_complete and
                not self.game_manager.animation_manager.menu_exit_animation):

            menu_buttons = draw_main_menu(
                self.game_manager.game_surface,
                self.game_manager.animation_manager.menu_animation_timer,
                self.game_manager.animation_manager.menu_exit_animation,
                self.game_manager.game_db.has_saved_game(),
                self.game_manager.images.get('menu_bg_img'),
                self.game_manager.font_medium
            )

            for btn_rect, label in menu_buttons:
                if btn_rect.collidepoint(x, y):
                    if label == "主线模式":
                        self.game_manager.animation_manager.start_menu_exit_animation("level_select")
                    elif label == "商店":
                        self.game_manager.animation_manager.start_menu_exit_animation("shop")
                    elif label == "图鉴":  # 新增：图鉴按钮点击处理
                        self.game_manager.animation_manager.start_menu_exit_animation("codex")
                    elif label == "设置":
                        self.game_manager.state_manager.toggle_settings()

    def _handle_level_select_click(self, x, y):
        """处理选关界面点击"""
        if self.game_manager.animation_manager.level_select_exit_animation:
            return

        if not self.game_manager.animation_manager.level_select_animation_complete:
            return

        back_btn, level_buttons = draw_level_select(
            self.game_manager.game_surface, self.game_manager.game_db,
            self.game_manager.level_settings,
            self.game_manager.images.get('menu_bg_img'),
            self.game_manager.font_medium, self.game_manager.font_small,
            self.game_manager.images.get('settings_img'),
            self.game_manager.animation_manager.level_select_animation_timer,
            self.game_manager.animation_manager.level_select_animation_complete
        )

        if back_btn.collidepoint(x, y):
            self.game_manager.animation_manager.start_level_select_exit_animation("main_menu")

        else:
            for level_rect, level_num in level_buttons:
                if level_rect.collidepoint(x, y):
                    self._handle_level_button_click(level_num)
                    break

    def _handle_level_button_click(self, level_num):
        """处理关卡按钮点击"""
        # 如果是第9关及以上且有植物选择，标记为返回状态
        if level_num >= 9 and self.game_manager.plant_selection_manager.has_selected_plants():
            self.game_manager.plant_selection_manager.mark_returning_to_plant_select()

        # 检查该关卡是否有保存的进度
        if check_level_has_save(self.game_manager.game_db, level_num):
            # 有保存进度，显示继续游戏对话框
            self.game_manager.state_manager.show_continue_dialog_for_level(level_num)
        else:
            # 没有保存进度，直接开始新游戏
            self.game_manager.state_manager.set_pending_game_data(None, level_num)
            self.game_manager.state_manager.start_level_transition_animation()

    def _handle_playing_click(self, x, y):
        """处理游戏中的点击"""
        # 如果正在显示植物选择网格，优先处理植物选择
        if self.game_manager.plant_selection_manager.show_plant_select:
            self._handle_plant_select_click(x, y)
        else:
            self._handle_gameplay_click(x, y)


    def _handle_plant_select_click(self, x, y):
        """处理植物选择界面点击（已修复开始战斗按钮）"""
        # 在动画播放期间禁用所有点击
        if self.game_manager.animation_manager.is_plant_select_exit_animating():
            return
        # 首先检查是否点击了设置按钮（即使在植物选择模式下也要可用）
        settings_rect = pygame.Rect(SETTINGS_BUTTON_X, SETTINGS_BUTTON_Y,
                                    SETTINGS_BUTTON_WIDTH, SETTINGS_BUTTON_HEIGHT)
        if settings_rect.collidepoint(x, y):
            self.game_manager.state_manager.toggle_settings()
            return

        # 修复：检查是否点击了开始战斗按钮
        finish_btn = self.game_manager.renderer_manager.get_finish_button()
        if finish_btn and finish_btn.collidepoint(x, y):
            # 检查是否有选中的植物
            if self.game_manager.plant_selection_manager.has_selected_plants():
                # 开始退出动画而不是直接隐藏
                self.game_manager.animation_manager.start_plant_select_exit_animation()

            else:
                # 没有选中植物，可以播放提示音效或显示提示
                print("请先选择植物再开始战斗！")
            return

        # 然后检查是否点击了卡片槽（取下功能）
        if self.game_manager.plant_selection_manager.handle_card_slot_click(x, y):
            return

        # 最后处理植物选择网格点击（修复：获取正确的植物矩形数据）
        plant_rects = self.game_manager.renderer_manager.get_plant_selection_rects()
        self.game_manager.plant_selection_manager.handle_plant_grid_click(x, y, plant_rects)

    def _handle_gameplay_click(self, x, y):
        """处理普通游戏玩法点击"""
        # 游戏结束时处理弹窗按钮
        if self.game_manager.game["game_over"]:
            self._handle_game_over_click(x, y)
            return

        # 游戏进行中：处理铲子/卡槽点击
        if not self.game_manager.state_manager.game_paused:
            self._handle_in_game_click(x, y)

    def _handle_game_over_click(self, x, y):
        """处理游戏结束界面点击"""
        retry_btn, quit_btn, game_over_sound_played = show_game_over(
            self.game_manager.game_surface, self.game_manager.game["game_over_sound_played"],
            self.game_manager.font_large, self.game_manager.font_medium
        )
        self.game_manager.game["game_over_sound_played"] = game_over_sound_played

        if retry_btn.collidepoint(x, y):
            current_game_level = self.game_manager.game["level_manager"].current_level

            # 使用新的重置方法，确保传送门系统被正确重新初始化
            self.game_manager.reset_game_with_initialization(current_game_level)

            # 重置游戏结束状态playing_hover
            self.game_manager.game["game_over"] = False
            self.game_manager.game["game_over_sound_played"] = False

        elif quit_btn.collidepoint(x, y):
            # 清除该关卡的保存数据，因为游戏失败
            self.game_manager.game_db.clear_saved_game()
            self.game_manager.state_manager.switch_to_main_menu()
            self.game_manager.game = self.game_manager.state_manager.reset_game()

    def _handle_in_game_click(self, x, y):
        """处理游戏内点击(种植物、铲子等) - 修复版本：确保工具优先"""

        # **优先级1：检查小推车点击**
        if self.game_manager.cart_manager.handle_cart_click(x, y):
            return

        # **优先级2：检查设置按钮**
        settings_rect = pygame.Rect(SETTINGS_BUTTON_X, SETTINGS_BUTTON_Y,
                                    SETTINGS_BUTTON_WIDTH, SETTINGS_BUTTON_HEIGHT)
        if settings_rect.collidepoint(x, y):
            self.game_manager.state_manager.toggle_settings()
            return

        # **优先级3：工具点击（铲子和锤子）- 必须在种子雨之前处理**
        # 检测是否点击铲子
        shovel_rect = pygame.Rect(self.game_manager.shovel["x"], self.game_manager.shovel["y"],
                                  self.game_manager.shovel["width"], self.game_manager.shovel["height"])
        if shovel_rect.collidepoint(x, y):
            if self.game_manager.game["selected"] == "hammer":
                self.game_manager.state_manager.clear_hammer_cursor()
            self.game_manager.game["selected"] = "shovel"
            return

        # 检测是否点击锤子
        if (hasattr(self.game_manager, 'shop_manager') and
                self.game_manager.shop_manager.has_hammer()):
            hammer_rect = pygame.Rect(HAMMER_X, HAMMER_Y, HAMMER_WIDTH, HAMMER_HEIGHT)
            if hammer_rect.collidepoint(x, y):
                hammer_cooldown = self.game_manager.game.get("hammer_cooldown", 0)
                if hammer_cooldown <= 0:
                    self.game_manager.state_manager.clear_hammer_cursor()
                    self.game_manager.game["selected"] = "hammer"
                    return
                else:
                    print(f"锤子冷却中,还需要 {int(hammer_cooldown / 60) + 1} 秒")
                    return

        # **优先级4：处理已选中工具的使用（战场点击）**
        if self._is_battlefield_click(x, y):
            selected = self.game_manager.game["selected"]

            # 如果选中了铲子或锤子，直接处理
            if selected in ["shovel", "hammer"]:
                from .game_logic import handle_plant_placement
                cards = self.game_manager.get_available_cards_for_current_state()
                handle_plant_placement(
                    self.game_manager.game, cards, x, y,
                    self.game_manager.game["level_manager"],
                    self.game_manager.level_settings,
                    self.game_manager.sounds,
                    self.game_manager.state_manager
                )
                return

        # **优先级5：种子雨卡牌点击**
        if (hasattr(self.game_manager, 'seed_rain_manager') and
                self.game_manager.seed_rain_manager and
                self.game_manager.seed_rain_manager.enabled):

            #  修复：检查是否点击了卡牌区域
            clicked_card = False
            for card in self.game_manager.seed_rain_manager.cards:
                if card.state in ["falling", "stopped"] and card.check_click((x, y)):
                    clicked_card = True
                    # 如果点击的是未选中的卡牌，选中它
                    if not card.selected:
                        selected_plant = self.game_manager.seed_rain_manager.handle_left_click(
                            (x, y),
                            self.game_manager.game
                        )
                        if selected_plant:
                            return  # 选中新卡牌后返回
                    # 如果点击的是已选中的卡牌，不做任何处理（让玩家点击战场种植）
                    break
            # 如果没有点击卡牌区域，继续处理种植逻辑
            if not clicked_card:
                # 继续执行下面的种植逻辑（优先级6）
                pass
            else:
                # 点击了已选中的卡牌，不拦截，继续执行（允许玩家再次点击同一卡牌后点击战场种植）
                pass

        # **优先级6：种子雨植物种植**
        if (hasattr(self.game_manager, 'seed_rain_manager') and
                self.game_manager.seed_rain_manager and
                self.game_manager.seed_rain_manager.enabled):

            selected = self.game_manager.game["selected"]

            # 如果选中了植物（非工具）且点击了战场
            if selected and selected not in ["shovel", "hammer"] and self._is_battlefield_click(x, y):
                plants_before = len(self.game_manager.game["plants"])

                # 🔧 关键修复：临时移除冷却时间，因为种子雨不应该有冷却
                original_cooldown = None
                if selected in self.game_manager.game.get("card_cooldowns", {}):
                    original_cooldown = self.game_manager.game["card_cooldowns"][selected]
                    self.game_manager.game["card_cooldowns"][selected] = 0

                from .game_logic import handle_plant_placement
                temp_card = {"type": selected, "cost": 0}

                plant_placed = handle_plant_placement(
                    self.game_manager.game, [temp_card], x, y,
                    self.game_manager.game["level_manager"],
                    self.game_manager.level_settings,
                    self.game_manager.sounds,
                    self.game_manager.state_manager
                )

                # 🔧 恢复原始冷却时间（如果有的话）
                if original_cooldown is not None:
                    self.game_manager.game["card_cooldowns"][selected] = original_cooldown

                if plant_placed and len(self.game_manager.game["plants"]) > plants_before:
                    # 先移除种子雨卡牌，再清除选中状态
                    self._remove_seed_rain_card_by_type(selected)

                    # 移除卡牌后再清除选中状态
                    self.game_manager.game["selected"] = None
                    self.game_manager.state_manager.clear_plant_preview()
                else:
                    pass

                return
            return

        # **优先级7：传送带模式（如果启用）**
        if (hasattr(self.game_manager, 'conveyor_belt_manager') and
                self.game_manager.conveyor_belt_manager is not None and
                self.game_manager.game["level_manager"].current_level != 18):

            selected_plant_type = self.game_manager.conveyor_belt_manager.handle_click((x, y), 0)
            if selected_plant_type:
                if self.game_manager.game["selected"] == "hammer":
                    self.game_manager.state_manager.clear_hammer_cursor()
                self.game_manager.game["selected"] = selected_plant_type
                return

            if self._is_battlefield_click(x, y):
                self._handle_conveyor_belt_planting(x, y)
                return

            return

        # **优先级8：传统卡槽模式**
        cards = self.game_manager.get_available_cards_for_current_state()

        # 检测是否点击卡槽
        clicked_card = None
        for i, card in enumerate(cards):
            card_x = CARD_START_X + i * CARD_WIDTH
            card_rect = pygame.Rect(card_x, CARD_Y, CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(x, y):
                if self._can_select_card(card):
                    clicked_card = card["type"]
                    break

        if clicked_card:
            if self.game_manager.game["selected"] == "hammer":
                self.game_manager.state_manager.clear_hammer_cursor()
            self.game_manager.game["selected"] = clicked_card
            return

        # 处理植物种植
        plants_before = len(self.game_manager.game["plants"])
        selected_before = self.game_manager.game["selected"]
        is_tool_before = selected_before in ["shovel", "hammer"]

        from .game_logic import handle_plant_placement
        plant_placed = handle_plant_placement(
            self.game_manager.game, cards, x, y,
            self.game_manager.game["level_manager"],
            self.game_manager.level_settings,
            self.game_manager.sounds,
            self.game_manager.state_manager
        )

        plants_after = len(self.game_manager.game["plants"])

        # 铲子使用后保持选中
        if selected_before == "shovel" and plant_placed:
            self.game_manager.game["selected"] = "shovel"
            self.game_manager.state_manager.clear_plant_preview()
        elif plants_after != plants_before or (selected_before == "hammer" and not self.game_manager.game["selected"]):
            self.game_manager.state_manager.clear_plant_preview()

    def _remove_seed_rain_card_by_type(self, plant_type):
        """根据植物类型移除种子雨卡牌 - 增强调试版本"""
        if (hasattr(self.game_manager, 'seed_rain_manager') and
                self.game_manager.seed_rain_manager and
                self.game_manager.seed_rain_manager.enabled):


            # 找到并移除已选中的对应类型卡牌
            card_removed = False
            for card in self.game_manager.seed_rain_manager.cards[:]:
                if card.plant_type == plant_type and card.selected:
                    self.game_manager.seed_rain_manager.cards.remove(card)
                    card_removed = True

                    break

    def _handle_conveyor_belt_planting(self, x, y):
        """处理传送带模式下的植物种植 - 修复：支持铲子和锤子的正常使用"""
        selected = self.game_manager.game["selected"]

        # 修复：移除错误的过滤条件，允许所有工具的使用
        if not selected:
            return

        # 传送带模式：不消耗阳光，直接调用特殊的种植函数
        from .game_logic import handle_conveyor_belt_plant_placement

        # **关键修复：记录使用前的选中状态**
        was_shovel_selected = (selected == "shovel")

        # 关键修复：铲子和锤子也需要正常传递给处理函数
        plant_placed = handle_conveyor_belt_plant_placement(
            self.game_manager.game,
            x, y,
            selected,  # 直接传递选中的工具/植物类型，包括 "shovel" 和 "hammer"
            self.game_manager.game["level_manager"],
            self.game_manager.sounds,
            self.game_manager.state_manager
        )

        if plant_placed:
            # **关键修复：铲子使用成功后保持选中状态**
            if was_shovel_selected:
                # 强制保持铲子选中状态
                self.game_manager.game["selected"] = "shovel"
                # 不清除植物预览，因为铲子模式不需要预览
            elif selected not in ["shovel", "hammer"] and self.game_manager.conveyor_belt_manager:
                # 只有在种植成功后才处理传送带卡牌移除（铲子和锤子不需要移除卡牌）
                # 种植成功，移除传送带上的已选卡牌
                self.game_manager.conveyor_belt_manager.remove_selected_card()

                # 清除选择状态
                self.game_manager.game["selected"] = None
                self.game_manager.state_manager.clear_plant_preview()

            # 特殊处理：如果使用的是锤子，清除锤子跟随状态
            if selected == "hammer":
                self.game_manager.state_manager.clear_hammer_cursor()
                # 锤子使用后清除选中状态（保持原有行为）
                self.game_manager.game["selected"] = None

    def _can_select_card(self, card):
        """检查卡片是否可以选择"""
        level_manager = self.game_manager.game["level_manager"]

        # 使用统一的卡片管理器检查冷却
        cooldown_active = False
        needs_cooldown = (level_manager.has_card_cooldown() or
                          self.game_manager.level_settings.get("all_card_cooldown", False) or
                          level_manager.current_level == 8)

        if needs_cooldown:
            if card["type"] in self.game_manager.game["card_cooldowns"]:
                if self.game_manager.game["card_cooldowns"][card["type"]] > 0:
                    cooldown_active = True

        if cooldown_active:
            return False

        # 检查向日葵是否可用
        if card["type"] == "sunflower" and not level_manager.can_plant_sunflower():
            return False

        # 检查阳光是否足够
        if self.game_manager.game["sun"] < card["cost"]:
            return False

        return True

    def _handle_right_click_cancel(self):
        """处理右键点击取消选中 - 修复传送带模式状态同步问题"""
        # 只在游戏进行中响应右键取消
        if self.game_manager.state_manager.game_state == "playing":
            # 优先处理种子雨取消
            if (hasattr(self.game_manager, 'seed_rain_manager') and
                    self.game_manager.seed_rain_manager and
                    self.game_manager.seed_rain_manager.enabled):
                self.game_manager.seed_rain_manager.handle_right_click(self.game_manager.game)
            # 检查是否有当前选中的植物或铲子
            if self.game_manager.game["selected"]:
                # 如果取消的是锤子，清除锤子跟随状态
                if self.game_manager.game["selected"] == "hammer":
                    self.game_manager.state_manager.clear_hammer_cursor()

                # 关键修复：如果是传送带模式，需要同步清除传送带管理器的选中状态
                if (hasattr(self.game_manager, 'conveyor_belt_manager') and
                        self.game_manager.conveyor_belt_manager is not None):
                    # 清除传送带管理器的选中状态
                    self.game_manager.conveyor_belt_manager.clear_selection()

                # 取消选中
                self.game_manager.game["selected"] = None

                # 清除植物预览状态
                self.game_manager.state_manager.clear_plant_preview()

            # 额外修复：即使游戏状态中没有选中，也要检查传送带是否有选中状态
            elif (hasattr(self.game_manager, 'conveyor_belt_manager') and
                  self.game_manager.conveyor_belt_manager is not None and
                  self.game_manager.conveyor_belt_manager.get_selected_card() is not None):
                # 清除传送带管理器的选中状态
                self.game_manager.conveyor_belt_manager.clear_selection()
                # 清除植物预览状态
                self.game_manager.state_manager.clear_plant_preview()

    def _handle_return_to_level_select_click(self):
        """处理返回选关页面按钮点击"""
        if self.game_manager.state_manager.game_state == "playing":
            # 保存当前游戏进度
            if self.game_manager.should_save_game_on_exit():
                self.game_manager.game_db.save_game_progress(
                    self.game_manager.game,
                    self.game_manager.music_manager,
                    self.game_manager
                )

            # 切换到选关页面
            self.game_manager.state_manager.switch_to_level_select()

            # 重置游戏状态（不保留关卡）
            self.game_manager.game = self.game_manager.state_manager.reset_game()

            # 清理植物选择状态
            self.game_manager.plant_selection_manager.clear_plant_selection_state()

            # 重置小推车状态
            self.game_manager.reset_carts()

            # 关闭设置菜单
            self.game_manager.state_manager.show_settings = False
            self.game_manager.state_manager.game_paused = False