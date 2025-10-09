from .base_bullet import BaseBullet
from .moon_bullet import MoonBullet
from .pea_bullet import PeaBullet
from .melon_bullet import MelonBullet
from .spike_bullet import SpikeBullet
from .ice_bullet import IceBullet
from .dandelion_seed import DandelionSeed
from .psychedelic_bullet import PsychedelicBullet


# 工厂函数，用于创建不同类型的子弹，支持传送门穿越
def create_bullet(bullet_type, row, col, **kwargs):
    """
    根据类型创建相应的子弹对象，支持传送门穿越

    Args:
        bullet_type: 子弹类型 ("pea", "melon", "spike", "ice")
        row: 行位置
        col: 列位置
        **kwargs: 其他参数，包括传送门相关参数

    Returns:
        对应类型的子弹对象
    """
    bullet_classes = {
        "pea": PeaBullet,
        "melon": MelonBullet,
        "spike": SpikeBullet,
        "ice": IceBullet,
        "moon":MoonBullet,
        "psychedelic":PsychedelicBullet
    }

    bullet_class = bullet_classes.get(bullet_type, PeaBullet)
    bullet = bullet_class(row, col, **kwargs)

    # 传送门支持设置（在子弹创建后设置，避免修改每个子弹类的构造函数）
    _setup_portal_support(bullet, bullet_type, **kwargs)

    return bullet


def _setup_portal_support(bullet, bullet_type, **kwargs):
    """
    为子弹设置传送门支持

    Args:
        bullet: 子弹对象
        bullet_type: 子弹类型
        **kwargs: 传送门相关参数
    """
    # 只有特定类型的子弹支持传送门穿越
    portal_supported_types = ["pea", "ice","moon"]

    if bullet_type in portal_supported_types:
        # 从kwargs中提取传送门相关参数
        portal_manager = kwargs.get('portal_manager', None)
        source_plant_row = kwargs.get('source_plant_row', bullet.row)
        source_plant_col = kwargs.get('source_plant_col', bullet.col)

        # 设置传送门相关属性
        bullet.supports_portal_travel = portal_manager is not None
        bullet.portal_manager = portal_manager
        bullet.source_plant_row = source_plant_row
        bullet.source_plant_col = source_plant_col
        bullet.has_traveled_through_portal = False
        bullet.original_row = bullet.row

        # 添加传送门检测方法（如果基类中没有的话）
        if not hasattr(bullet, '_check_portal_travel'):
            bullet._check_portal_travel = lambda: _check_bullet_portal_travel(bullet)
            bullet._get_portals_in_row = lambda row: _get_portals_in_row(bullet.portal_manager, row)
            bullet._find_exit_portal = lambda entrance: _find_exit_portal(bullet.portal_manager, entrance)
    else:
        # 非支持类型设置默认值
        bullet.supports_portal_travel = False
        bullet.portal_manager = None
        bullet.has_traveled_through_portal = False
        bullet.original_row = bullet.row


def _check_bullet_portal_travel(bullet):
    """为子弹检查传送门穿越"""
    if not bullet.portal_manager:
        return False

    # 获取当前行的传送门
    current_row_portals = _get_portals_in_row(bullet.portal_manager, bullet.row)

    for portal in current_row_portals:
        # 检查子弹是否接近传送门位置
        if (portal.is_active and
                abs(bullet.col - portal.col) < 0.3 and  # 传送门检测范围
                portal.col > bullet.source_plant_col):  # 确保是植物右侧的传送门

            # 执行传送门穿越
            exit_portal = _find_exit_portal(bullet.portal_manager, portal)
            if exit_portal:
                # 传送到出口传送门
                bullet.row = exit_portal.row
                bullet.col = exit_portal.col + 0.5  # 在传送门右侧稍微偏移
                bullet.has_traveled_through_portal = True


                return True

    return False


def _get_portals_in_row(portal_manager, row):
    """获取指定行的活跃传送门"""
    if not portal_manager or not hasattr(portal_manager, 'portals'):
        return []

    return [portal for portal in portal_manager.portals
            if portal.row == row and portal.is_active]


def _find_exit_portal(portal_manager, entrance_portal):
    """寻找传送门出口"""
    if not portal_manager or not hasattr(portal_manager, 'portals'):
        return None

    # 获取其他活跃的传送门作为可能的出口
    exit_candidates = [portal for portal in portal_manager.portals
                       if (portal.is_active and portal != entrance_portal)]

    if not exit_candidates:
        return None

    # 选择最优出口（这里可以实现不同的选择策略）
    # 目前选择第一个可用的出口
    return exit_candidates[0]


__all__ = [
    'BaseBullet',
    'PeaBullet',
    'MelonBullet',
    'SpikeBullet',
    'IceBullet',
    'DandelionSeed',
    'create_bullet',
    'MoonBullet',
    'PsychedelicBullet',
]