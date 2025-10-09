"""
僵尸模块初始化文件 - 添加冰车僵尸支持
"""

from .base_zombie import BaseZombie
from .normal_zombie import NormalZombie
from .giant_zombie import GiantZombie
from .exploding_zombie import ExplodingZombie, ExplodingZombieDeathHandler
from .ice_car_zombie import IceCarZombie
from .zombie_factory import ZombieFactory, create_zombie
from .effects import CucumberSprayParticle,CharmEffect
from .ice_trail_manager import (
    IceTrailManager, IceTrail, get_ice_trail_manager,
    add_ice_trail, update_ice_trails, draw_ice_trails, clear_all_ice_trails
)

# 为了保持向后兼容，导出Zombie类
Zombie = ZombieFactory

__all__ = [
    'BaseZombie',
    'NormalZombie',
    'GiantZombie',
    'ExplodingZombie',
    'ExplodingZombieDeathHandler',
    'IceCarZombie',
    'ZombieFactory',
    'create_zombie',
    'Zombie',
    'CucumberSprayParticle',
    'CharmEffect',
    'IceTrailManager',
    'IceTrail',
    'get_ice_trail_manager',
    'add_ice_trail',
    'update_ice_trails',
    'draw_ice_trails',
    'clear_all_ice_trails'
]