"""
种子雨管理器 - 负责管理从天而降的植物卡牌
"""
import pygame
import random
from core.constants import *
# 种子雨卡牌的背景颜色
CARD_BG_COLOR = (139, 69, 19)  # 棕色背景


class SeedRainCard:
    """单个降落的种子卡牌"""

    def __init__(self, plant_type, target_row, target_col, images):
        self.plant_type = plant_type
        self.target_row = target_row
        self.target_col = target_col
        self.images = images

        # 计算起始和目标位置
        self.target_x = BATTLEFIELD_LEFT + target_col * (GRID_SIZE + GRID_GAP) + GRID_SIZE // 2
        self.target_y = BATTLEFIELD_TOP + target_row * (GRID_SIZE + GRID_GAP) + GRID_SIZE // 2

        # 起始位置在战场上方
        self.x = self.target_x
        self.y = BATTLEFIELD_TOP - 20

        # 状态
        self.state = "falling"  # falling, stopped, fading
        self.fall_speed = 0.96
        self.wait_timer = 0
        self.wait_duration = 480  # 8秒
        self.fade_duration = 60
        self.fade_timer = 0
        self.alpha = 250

        # 卡牌尺寸
        self.card_width = CARD_WIDTH
        self.card_height = CARD_HEIGHT

        # 是否被选中
        self.selected = False

        # 新增：等待计时是否已开始（用于防止重复点击重置计时器）
        self.wait_started = False

    def update(self):
        """更新卡牌状态"""
        if self.state == "falling":
            # 缓慢下降
            self.y += self.fall_speed

            # 检查是否到达目标位置
            if self.y >= self.target_y:
                self.y = self.target_y
                self.state = "stopped"
                self.wait_timer = 0
                self.wait_started = True  # 标记等待已开始

        elif self.state == "stopped":
            # 等待计时（不受再次点击影响）
            self.wait_timer += 1

            if self.wait_timer >= self.wait_duration:
                # 开始渐隐
                self.state = "fading"
                self.fade_timer = 0

        elif self.state == "fading":
            # 渐隐效果
            self.fade_timer += 1
            progress = self.fade_timer / self.fade_duration
            self.alpha = int(200 * (1 - progress))

            if self.fade_timer >= self.fade_duration:
                return False  # 标记为可移除

        return True  # 继续存在

    def stop_falling(self):
        """停止下降，进入等待状态"""
        # 🔧 修复：无论什么状态，都设置为选中
        self.selected = True

        if self.state == "falling":
            self.state = "stopped"
            self.wait_timer = 0
            self.wait_started = True

    def cancel_selection(self):
        """取消选中（不影响等待计时器）"""
        self.selected = False
        # 关键修复：不重置 wait_timer，让8秒倒计时继续

    def check_click(self, mouse_pos):
        """检查是否点击了卡牌"""
        mx, my = mouse_pos
        card_rect = pygame.Rect(
            self.x - self.card_width // 2,
            self.y - self.card_height // 2,
            self.card_width,
            self.card_height
        )
        return card_rect.collidepoint(mx, my)

    def draw(self, surface, scaled_images):
        """绘制卡牌 - 智能查找图片键名"""
        card_surface = pygame.Surface((self.card_width, self.card_height), pygame.SRCALPHA)

        # 🔧 智能查找图片键名的多种可能性
        possible_keys = []

        # 1. 尝试从植物注册表获取
        try:
            from plants.plant_registry import plant_registry
            possible_keys.append(plant_registry.get_plant_icon_key(self.plant_type))
        except (ImportError, AttributeError):
            pass

        # 2. 添加常见的命名模式
        possible_keys.extend([
            f"{self.plant_type}_60",  # shooter_60
            f"{self.plant_type}_img",  # shooter_img
        ])

        # 3. 特殊映射（针对已知的不一致命名）
        special_mappings = {
            'shooter': ['pea_shooter_60', 'pea_shooter_img'],
            'melon_pult': ['watermelon_60', 'watermelon_img'],
        }
        if self.plant_type in special_mappings:
            possible_keys.extend(special_mappings[self.plant_type])

        # 查找第一个存在的键名
        plant_img = None
        used_key = None
        for key in possible_keys:
            if key in scaled_images:
                plant_img = scaled_images[key].copy()
                used_key = key
                break

        if plant_img:
            if self.selected:
                dark_overlay = pygame.Surface(plant_img.get_size(), pygame.SRCALPHA)
                dark_overlay.fill((0, 0, 0, 128))
                plant_img.blit(dark_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            plant_img.set_alpha(self.alpha - 100)
            img_rect = plant_img.get_rect(center=(self.card_width // 2, self.card_height // 2))

            bg_color = (*CARD_BG_COLOR, self.alpha)
            pygame.draw.rect(card_surface, bg_color, (0, 0, self.card_width, img_rect.top))
            pygame.draw.rect(card_surface, bg_color,
                             (0, img_rect.bottom, self.card_width, self.card_height - img_rect.bottom))
            pygame.draw.rect(card_surface, bg_color, (0, img_rect.top, img_rect.left, img_rect.height))
            pygame.draw.rect(card_surface, bg_color,
                             (img_rect.right, img_rect.top, self.card_width - img_rect.right, img_rect.height))
            card_surface.blit(plant_img, img_rect)
        else:
            bg_color = (*CARD_BG_COLOR, self.alpha)
            card_surface.fill(bg_color)
            print(f"警告：种子雨找不到图片 - {self.plant_type}, 尝试了: {possible_keys}")

        card_x = self.x - self.card_width // 2
        card_y = self.y - self.card_height // 2
        surface.blit(card_surface, (card_x, card_y))


class SeedRainManager:
    """种子雨管理器"""

    def __init__(self, level_manager, available_plants, images):
        self.level_manager = level_manager
        self.available_plants = available_plants  # 可掉落的植物类型列表
        self.images = images

        # 卡牌列表
        self.cards = []

        # 生成计时器
        self.spawn_timer = 0
        self.spawn_interval = 240  # 4秒 = 240帧

        # 配置参数
        self.enabled = False
        self._check_feature_enabled()

    def _check_feature_enabled(self):
        """检查种子雨特性是否启用"""
        if hasattr(self.level_manager, 'has_special_feature'):
            self.enabled = self.level_manager.has_special_feature("seed_rain")

    def update(self):
        """更新种子雨系统"""
        if not self.enabled:
            return

        # 更新生成计时器
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self._spawn_new_card()
            self.spawn_timer = 0

        # 更新所有卡牌
        cards_to_remove = []
        for card in self.cards:
            if not card.update():
                cards_to_remove.append(card)

        # 移除已消失的卡牌
        for card in cards_to_remove:
            self.cards.remove(card)

    def _spawn_new_card(self):
        """生成新的种子卡牌"""
        if not self.available_plants:
            return

        # 随机选择植物类型
        plant_type = random.choice([p['type'] for p in self.available_plants])

        # 随机选择目标行列
        target_row = random.randint(0, GRID_HEIGHT - 1)
        target_col = random.randint(0, GRID_WIDTH - 1)

        # 创建新卡牌
        new_card = SeedRainCard(plant_type, target_row, target_col, self.images)
        self.cards.append(new_card)

    def handle_left_click(self, mouse_pos, game_state):
        """处理左键点击 - 修复版本：确保selected属性正确设置"""
        if not self.enabled:
            return None

        # 检查是否点击了卡牌
        for card in self.cards:
            # 只有 falling 或 stopped 状态的卡牌可以点击
            if card.state in ["falling", "stopped"] and card.check_click(mouse_pos):
                if not card.selected:
                    # 🔧 关键修复：先取消其他已选中的同类型卡牌
                    self._cancel_other_selected_cards(card.plant_type)

                    # 🔧 修复：强制设置选中状态，确保一定被设置
                    card.selected = True
                    card.stop_falling()
                    game_state["selected"] = card.plant_type

                    return card.plant_type
                else:
                    # 如果卡牌已经选中，重新确认选中状态
                    game_state["selected"] = card.plant_type

                    return None

        return None

    def _cancel_other_selected_cards(self, plant_type):
        """取消其他已选中的相同类型卡牌的选中状态"""
        for card in self.cards:
            if card.plant_type == plant_type and card.selected:
                card.cancel_selection()
                # 🔧 关键修复：确保卡牌真正恢复到未选中状态
                card.selected = False

    def handle_right_click(self, game_state):
        """处理右键取消选中 - 修复版本"""
        if not self.enabled:
            return

        # 取消所有选中的卡牌（不影响等待计时器）
        for card in self.cards:
            if card.selected:
                card.cancel_selection()

        # 清除游戏选中状态
        current_selected = game_state.get("selected")
        if current_selected:
            # 🔧 修复：直接清除选中状态，不再检查是否是种子雨卡牌
            # 因为可能卡牌已经被移除但选中状态还在
            game_state["selected"] = None

    def draw(self, surface, scaled_images):
        """绘制所有种子雨卡牌"""
        if not self.enabled:
            return

        for card in self.cards:
            card.draw(surface, scaled_images)

    def reset(self):
        """重置种子雨系统"""
        self.cards.clear()
        self.spawn_timer = 0

    def get_save_data(self):
        """获取种子雨系统的保存数据"""
        if not self.enabled:
            return {}

        save_data = {
            "enabled": self.enabled,
            "spawn_timer": self.spawn_timer,
            "spawn_interval": self.spawn_interval,
            "cards": []
        }

        # 保存每个卡牌的状态
        for card in self.cards:
            card_data = {
                "plant_type": card.plant_type,
                "target_row": card.target_row,
                "target_col": card.target_col,
                "x": card.x,
                "y": card.y,
                "target_x": card.target_x,
                "target_y": card.target_y,
                "state": card.state,
                "fall_speed": card.fall_speed,
                "wait_timer": card.wait_timer,
                "wait_duration": card.wait_duration,
                "fade_duration": card.fade_duration,
                "fade_timer": card.fade_timer,
                "alpha": card.alpha,
                "selected": card.selected,
                "wait_started": card.wait_started
            }
            save_data["cards"].append(card_data)

        return save_data

    def load_save_data(self, save_data):
        """从保存数据恢复种子雨系统"""
        if not save_data:
            return

        self.enabled = save_data.get("enabled", True)
        self.spawn_timer = save_data.get("spawn_timer", 0)
        self.spawn_interval = save_data.get("spawn_interval", 240)

        # 清空现有卡牌
        self.cards.clear()

        # 恢复每个卡牌
        for card_data in save_data.get("cards", []):
            card = SeedRainCard(
                card_data["plant_type"],
                card_data["target_row"],
                card_data["target_col"],
                self.images
            )

            # 恢复卡牌状态
            card.x = card_data.get("x", card.x)
            card.y = card_data.get("y", card.y)
            card.target_x = card_data.get("target_x", card.target_x)
            card.target_y = card_data.get("target_y", card.target_y)
            card.state = card_data.get("state", "falling")
            card.fall_speed = card_data.get("fall_speed", 0.96)
            card.wait_timer = card_data.get("wait_timer", 0)
            card.wait_duration = card_data.get("wait_duration", 480)
            card.fade_duration = card_data.get("fade_duration", 60)
            card.fade_timer = card_data.get("fade_timer", 0)
            card.alpha = card_data.get("alpha", 250)
            card.selected = card_data.get("selected", False)
            card.wait_started = card_data.get("wait_started", False)

            self.cards.append(card)