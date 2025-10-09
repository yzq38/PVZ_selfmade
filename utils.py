"""
通用工具函数模块
"""
import pygame
import math
from core.constants import *

# 导入植物注册系统（如果存在）
try:
    from plants.plant_registry import plant_registry
    PLANT_REGISTRY_AVAILABLE = True
except ImportError:
    PLANT_REGISTRY_AVAILABLE = False


def clamp(value, min_value, max_value):
    """将值限制在指定范围内"""
    return max(min_value, min(value, max_value))


def lerp(start, end, t):
    """线性插值函数"""
    return start + (end - start) * t


def distance(pos1, pos2):
    """计算两点间距离"""
    x1, y1 = pos1
    x2, y2 = pos2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def grid_to_pixel(row, col):
    """将网格坐标转换为像素坐标"""
    x = BATTLEFIELD_LEFT + col * (GRID_SIZE + GRID_GAP)
    y = BATTLEFIELD_TOP + row * (GRID_SIZE + GRID_GAP)
    return x, y


def pixel_to_grid(x, y):
    """将像素坐标转换为网格坐标"""
    adj_x = x - BATTLEFIELD_LEFT
    adj_y = y - BATTLEFIELD_TOP

    if 0 <= adj_x < total_battlefield_width and 0 <= adj_y < total_battlefield_height:
        # 计算点击的网格坐标
        col = 0
        while col < GRID_WIDTH and adj_x > (col + 1) * GRID_SIZE + col * GRID_GAP:
            col += 1
        row = 0
        while row < GRID_HEIGHT and adj_y > (row + 1) * GRID_SIZE + row * GRID_GAP:
            row += 1
        return row, col
    return None, None


def is_point_in_battlefield(x, y):
    """检查点是否在战场范围内"""
    adj_x = x - BATTLEFIELD_LEFT
    adj_y = y - BATTLEFIELD_TOP
    return 0 <= adj_x < total_battlefield_width and 0 <= adj_y < total_battlefield_height


def format_time(seconds):
    """格式化时间显示"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}分{remaining_seconds}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分钟"


def create_text_surface(text, font, color, background_color=None):
    """创建文本表面，可选背景色"""
    text_surface = font.render(text, True, color)
    if background_color:
        bg_surface = pygame.Surface(text_surface.get_size())
        bg_surface.fill(background_color)
        bg_surface.blit(text_surface, (0, 0))
        return bg_surface
    return text_surface


def draw_outlined_text(surface, text, font, pos, text_color, outline_color, outline_width=1):
    """绘制带轮廓的文字"""
    x, y = pos

    # 绘制轮廓
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                outline_surface = font.render(text, True, outline_color)
                surface.blit(outline_surface, (x + dx, y + dy))

    # 绘制主文字
    text_surface = font.render(text, True, text_color)
    surface.blit(text_surface, (x, y))


def create_gradient_surface(width, height, start_color, end_color, vertical=True):
    """创建渐变表面"""
    surface = pygame.Surface((width, height))

    if vertical:
        for y in range(height):
            ratio = y / height
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
    else:
        for x in range(width):
            ratio = x / width
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (x, 0), (x, height))

    return surface


def create_rounded_rect_surface(width, height, color, radius=10):
    """创建圆角矩形表面"""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # 绘制主矩形
    pygame.draw.rect(surface, color, (radius, 0, width - 2 * radius, height))
    pygame.draw.rect(surface, color, (0, radius, width, height - 2 * radius))

    # 绘制四个角的圆
    pygame.draw.circle(surface, color, (radius, radius), radius)
    pygame.draw.circle(surface, color, (width - radius, radius), radius)
    pygame.draw.circle(surface, color, (radius, height - radius), radius)
    pygame.draw.circle(surface, color, (width - radius, height - radius), radius)

    return surface


def animate_value(current, target, speed):
    """动画值插值函数"""
    diff = target - current
    if abs(diff) < 0.01:
        return target
    return current + diff * speed


def create_shadow_surface(original_surface, offset=(2, 2), shadow_color=(0, 0, 0, 100)):
    """为表面创建阴影效果"""
    shadow_surface = pygame.Surface(
        (original_surface.get_width() + abs(offset[0]),
         original_surface.get_height() + abs(offset[1])),
        pygame.SRCALPHA
    )

    # 创建阴影
    shadow = original_surface.copy()
    shadow.fill(shadow_color, special_flags=pygame.BLEND_RGBA_MULT)

    # 绘制阴影和原图
    shadow_x = max(0, offset[0])
    shadow_y = max(0, offset[1])
    original_x = max(0, -offset[0])
    original_y = max(0, -offset[1])

    shadow_surface.blit(shadow, (shadow_x, shadow_y))
    shadow_surface.blit(original_surface, (original_x, original_y))

    return shadow_surface


def get_safe_rect(surface, rect):
    """确保矩形在表面边界内"""
    surface_rect = surface.get_rect()
    return rect.clip(surface_rect)


def split_text_to_lines(text, font, max_width):
    """将文本按宽度分割为多行"""
    words = text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def draw_multiline_text(surface, text, font, pos, color, line_spacing=5, max_width=None):
    """绘制多行文本"""
    x, y = pos

    if max_width:
        lines = split_text_to_lines(text, font, max_width)
    else:
        lines = text.split('\n')

    for i, line in enumerate(lines):
        line_surface = font.render(line, True, color)
        surface.blit(line_surface, (x, y + i * (font.get_height() + line_spacing)))


def create_button_surface(width, height, text, font,
                          bg_color, text_color, border_color=None, border_width=2):
    """创建按钮表面"""
    surface = pygame.Surface((width, height))
    surface.fill(bg_color)

    if border_color:
        pygame.draw.rect(surface, border_color, surface.get_rect(), border_width)

    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(width // 2, height // 2))
    surface.blit(text_surface, text_rect)

    return surface


def fade_surface(surface, alpha):
    """为表面添加透明度"""
    faded_surface = surface.copy()
    faded_surface.set_alpha(alpha)
    return faded_surface


def rotate_around_point(surface, angle, center_point):
    """围绕指定点旋转表面"""
    rotated_surface = pygame.transform.rotate(surface, angle)
    rotated_rect = rotated_surface.get_rect()
    rotated_rect.center = center_point
    return rotated_surface, rotated_rect


def create_pulse_effect(time, frequency=1.0, min_alpha=100, max_alpha=255):
    """创建脉冲效果的alpha值"""
    pulse = (math.sin(time * frequency * math.pi * 2) + 1) / 2
    return int(min_alpha + (max_alpha - min_alpha) * pulse)


def ease_in_out_cubic(t):
    """三次方缓入缓出函数"""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def ease_out_bounce(t):
    """弹跳缓出函数"""
    n1 = 7.5625
    d1 = 2.75

    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        return n1 * (t - 1.5 / d1) * t + 0.75
    elif t < 2.5 / d1:
        return n1 * (t - 2.25 / d1) * t + 0.9375
    else:
        return n1 * (t - 2.625 / d1) * t + 0.984375


def debug_draw_grid(surface, color=(100, 100, 100), alpha=128):
    """绘制调试网格"""
    debug_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)

    # 绘制战场网格
    for row in range(GRID_HEIGHT + 1):
        y = BATTLEFIELD_TOP + row * (GRID_SIZE + GRID_GAP)
        pygame.draw.line(debug_surface, (*color, alpha),
                         (BATTLEFIELD_LEFT, y),
                         (BATTLEFIELD_LEFT + total_battlefield_width, y))

    for col in range(GRID_WIDTH + 1):
        x = BATTLEFIELD_LEFT + col * (GRID_SIZE + GRID_GAP)
        pygame.draw.line(debug_surface, (*color, alpha),
                         (x, BATTLEFIELD_TOP),
                         (x, BATTLEFIELD_TOP + total_battlefield_height))

    surface.blit(debug_surface, (0, 0))


def get_fps_color(fps):
    """根据FPS返回对应颜色"""
    if fps >= 55:
        return (0, 255, 0)  # 绿色 - 良好
    elif fps >= 45:
        return (255, 255, 0)  # 黄色 - 一般
    elif fps >= 30:
        return (255, 165, 0)  # 橙色 - 较差
    else:
        return (255, 0, 0)  # 红色 - 很差


def can_place_plant_at_position(game, plant_type, row, col, level_manager):
    """
    检查是否可以在指定位置种植植物

    Args:
        game: 游戏状态
        plant_type: 植物类型
        row, col: 网格坐标
        level_manager: 关卡管理器

    Returns:
        bool: 是否可以种植
    """
    # 新增：检查冰道系统
    if "ice_trail_manager" in game and game["ice_trail_manager"]:
        ice_trail_manager = game["ice_trail_manager"]
        # 检查该位置是否有冰道
        if ice_trail_manager.has_ice_trail_at(row, col):
            return False  # 冰道上不能种植物

    # 检查该位置是否已有植物
    for plant in game["plants"]:
        if plant.row == row and plant.col == col:
            # 如果是坚果墙且血量不满，可以修复
            if plant_type == "wall_nut" and plant.plant_type == "wall_nut":
                return plant.health < plant.max_health
            return False

    # 检查向日葵种植限制
    if plant_type == "sunflower":
        if not level_manager.can_plant_sunflower():
            return False

    return True


def should_show_plant_preview(game, selected_plant_type, target_row, target_col):
    """
    判断是否应该显示植物预览

    Args:
        game: 游戏状态
        selected_plant_type: 选中的植物类型
        target_row: 目标行
        target_col: 目标列

    Returns:
        tuple: (是否显示预览, 是否可以放置)
    """
    # 新增：检查冰道系统
    if "ice_trail_manager" in game and game["ice_trail_manager"]:
        ice_trail_manager = game["ice_trail_manager"]
        # 检查该位置是否有冰道
        if ice_trail_manager.has_ice_trail_at(target_row, target_col):
            return False, False  # 冰道上不显示预览，不可放置

    # 检查目标位置是否有植物
    target_plant = None
    for plant in game["plants"]:
        if plant.row == target_row and plant.col == target_col:
            target_plant = plant
            break

    # 如果目标位置没有植物，正常显示预览
    if target_plant is None:
        return True, True  # 显示预览，可以放置

    # 如果目标位置有植物
    # 特殊情况：坚果墙修复
    if (selected_plant_type == "wall_nut" and
            target_plant.plant_type == "wall_nut" and
            target_plant.health < target_plant.max_health):
        # 坚果墙可以修复，显示预览
        return True, True  # 显示预览，可以放置（修复）

    # 其他情况：有植物的格子不显示预览
    return False, False  # 不显示预览，不能放置


def get_plant_preview_image_key(plant_type):
    """
    获取植物预览图片的键名
    优先使用植物注册表，如果不可用则使用硬编码映射

    Args:
        plant_type: 植物类型

    Returns:
        str: 图片键名
    """
    # 如果植物注册表可用，优先使用
    if PLANT_REGISTRY_AVAILABLE:
        return plant_registry.get_plant_icon_key(plant_type)

    # 后备方案：硬编码映射
    image_map = {
        'sunflower': 'sunflower_60',
        'shooter': 'pea_shooter_60',
        'melon_pult': 'watermelon_60',
        'cattail': 'cattail_60',
        'wall_nut': 'wall_nut_60',
        'cherry_bomb': 'cherry_bomb_60',
        'cucumber': 'cucumber_60',
        'dandelion': 'dandelion_60',
        'lightning_flower': 'lightning_flower_60',
        'ice_cactus': 'ice_cactus_60',
        'psychedelic_pitcher': 'psychedelic_pitcher_60',
    }
    return image_map.get(plant_type, f"{plant_type}_60")


def draw_plant_preview(surface, scaled_images, plant_type, target_row, target_col, can_place, alpha=None):
    """
    绘制植物种植预览 - 使用植物注册表系统

    Args:
        surface: 绘制表面
        scaled_images: 缩放后的图片字典
        plant_type: 植物类型
        target_row: 目标行
        target_col: 目标列
        can_place: 是否可以放置
        alpha: 透明度（可选，不提供则使用植物默认值）
    """
    from core.constants import BATTLEFIELD_LEFT, BATTLEFIELD_TOP, GRID_SIZE, GRID_GAP

    # 获取植物的默认透明度
    if alpha is None:
        if PLANT_REGISTRY_AVAILABLE:
            alpha = plant_registry.get_preview_alpha(plant_type)
        else:
            alpha = 128  # 默认透明度

    # 如果不能放置，降低透明度
    if not can_place:
        alpha = max(50, alpha // 2)

    # 计算目标位置
    preview_x = BATTLEFIELD_LEFT + target_col * (GRID_SIZE + GRID_GAP)
    preview_y = BATTLEFIELD_TOP + target_row * (GRID_SIZE + GRID_GAP)

    if scaled_images:
        # 获取植物图标键名
        plant_img_key = get_plant_preview_image_key(plant_type)

        if plant_img_key and plant_img_key in scaled_images:
            plant_img = scaled_images[plant_img_key]

            # 创建半透明的植物图标
            preview_surface = plant_img.copy()
            preview_surface.set_alpha(alpha)

            # 如果不能放置，添加红色叠加层
            if not can_place:
                overlay = pygame.Surface(plant_img.get_size(), pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 60))  # 半透明红色
                preview_surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            # 计算居中位置
            img_x = preview_x + (GRID_SIZE - plant_img.get_width()) // 2
            img_y = preview_y + (GRID_SIZE - plant_img.get_height()) // 2

            surface.blit(preview_surface, (img_x, img_y))
        else:
            # 如果没有图片，绘制占位符
            _draw_placeholder_preview(surface, preview_x, preview_y, GRID_SIZE, can_place, alpha)
    else:
        # 如果没有图片资源，绘制占位符
        _draw_placeholder_preview(surface, preview_x, preview_y, GRID_SIZE, can_place, alpha)


def _draw_placeholder_preview(surface, x, y, size, can_place, alpha):
    """
    绘制占位符预览（内部函数）

    Args:
        surface: 绘制表面
        x, y: 位置坐标
        size: 格子大小
        can_place: 是否可以放置
        alpha: 透明度
    """
    preview_surface = pygame.Surface((size, size), pygame.SRCALPHA)

    # 选择颜色
    if can_place:
        color = (100, 200, 100, alpha)  # 绿色
    else:
        color = (200, 100, 100, alpha)  # 红色

    # 绘制圆形占位符
    pygame.draw.circle(preview_surface, color,
                       (size // 2, size // 2),
                       size // 3)

    # 绘制边框
    border_color = (*color[:3], min(255, alpha + 50))
    pygame.draw.circle(preview_surface, border_color,
                       (size // 2, size // 2),
                       size // 3, 2)

    surface.blit(preview_surface, (x, y))


def update_plant_preview_on_mouse_move(state_manager, game, cards, mouse_x, mouse_y, selected):
    """
    根据鼠标位置更新植物预览状态
    修复：添加阳光和冷却检查，阳光不足或冷却时不显示预览

    Args:
        state_manager: 状态管理器
        game: 游戏状态
        cards: 可用卡牌列表
        mouse_x: 鼠标X坐标
        mouse_y: 鼠标Y坐标
        selected: 当前选中的植物类型
    """
    from core.constants import BATTLEFIELD_LEFT, BATTLEFIELD_TOP, GRID_SIZE, GRID_GAP, GRID_WIDTH, GRID_HEIGHT

    # 如果没有选中植物卡牌，清除预览
    if not selected or selected == "shovel":
        state_manager.clear_plant_preview()
        return

    # 检查选中的是否是有效的植物卡牌
    valid_plant_types = [card["type"] for card in cards]
    if selected not in valid_plant_types:
        state_manager.clear_plant_preview()
        return

    # **新增：获取选中植物的卡片信息**
    selected_card = None
    for card in cards:
        if card["type"] == selected:
            selected_card = card
            break

    if not selected_card:
        state_manager.clear_plant_preview()
        return

    # **新增：检查阳光是否足够 - 阳光不足时不显示预览**
    if game["sun"] < selected_card["cost"]:
        state_manager.clear_plant_preview()
        return

    # **新增：检查卡片是否在冷却中 - 冷却中不显示预览**
    level_manager = game.get("level_manager")
    if level_manager:
        # 检查向日葵是否可用
        if selected == "sunflower" and not level_manager.can_plant_sunflower():
            state_manager.clear_plant_preview()
            return

        # 检查冷却状态
        card_cooldowns = game.get("card_cooldowns", {})
        needs_cooldown = (level_manager.has_card_cooldown() or
                          level_manager.current_level == 8)

        if needs_cooldown and selected in card_cooldowns:
            if card_cooldowns[selected] > 0:
                state_manager.clear_plant_preview()
                return

    # 计算鼠标相对于战场的位置
    adj_x = mouse_x - BATTLEFIELD_LEFT
    adj_y = mouse_y - BATTLEFIELD_TOP

    # 检查鼠标是否在战场范围内
    total_battlefield_width = GRID_WIDTH * GRID_SIZE + (GRID_WIDTH - 1) * GRID_GAP
    total_battlefield_height = GRID_HEIGHT * GRID_SIZE + (GRID_HEIGHT - 1) * GRID_GAP

    if not (0 <= adj_x < total_battlefield_width and 0 <= adj_y < total_battlefield_height):
        state_manager.clear_plant_preview()
        return

    # 计算目标格子坐标
    col = 0
    while col < GRID_WIDTH and adj_x > (col + 1) * GRID_SIZE + col * GRID_GAP:
        col += 1
    row = 0
    while row < GRID_HEIGHT and adj_y > (row + 1) * GRID_SIZE + row * GRID_GAP:
        row += 1

    # 确保坐标在有效范围内
    if row >= GRID_HEIGHT or col >= GRID_WIDTH:
        state_manager.clear_plant_preview()
        return

    # 判断是否应该显示预览
    should_show, can_place = should_show_plant_preview(game, selected, row, col)

    if should_show:
        # 设置植物预览
        state_manager.set_plant_preview(selected, row, col, can_place)
    else:
        # 清除预览
        state_manager.clear_plant_preview()