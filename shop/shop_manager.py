"""
商店管理器 - 处理商品展示、分页和购买逻辑
"""
import json
import os


class ShopManager:
    """商店管理器 - 处理商品展示、分页和购买逻辑"""

    def __init__(self):
        self.items_per_page = 8  # 每页显示8个商品（4x2网格）
        self.current_page = 0
        self.purchased_items = self.load_purchased_items()

        # 商店商品列表
        self.shop_items = [
            {
                'id': 'cart',
                'name': '小推车',
                'price': 250,
                'type': 'tool',
                'icon': 'cart_img',
                'description': '战场每行增加一个小推车防御'
            },
            {
                'id': 'hammer',
                'name': '锤子',
                'price': 1000,
                'type': 'tool',
                'icon': 'hammer_img',
                'description': '每20秒可用一次秒杀一格内僵尸'
            },
            {
                'id': '7th_cardbg',
                'name': '第七卡槽',
                'price': 1000,
                'type': 'tool',
                'icon': 'card_bg_img',
                'description': '可多选择一个植物'
            },
            {
                'id': 'zombie_slower',
                'name': '僵尸减速剂',
                'price': 60,
                'type': 'consumable',
                'icon': 'slower_img',
                'description': '所有僵尸移动速度降低20%'
            },
            {
                'id': 'sun_generator',
                'name': '阳光发生器',
                'price': 150,
                'type': 'tool',
                'icon': 'generator_img',
                'description': '自动每10秒产生25阳光'
            },
            {
                'id': 'plant_armor',
                'name': '植物护甲',
                'price': 80,
                'type': 'consumable',
                'icon': 'armor_img',
                'description': '所有植物血量增加50%'
            },
            {
                'id': 'seed_packet',
                'name': '种子包',
                'price': 40,
                'type': 'consumable',
                'icon': 'seed_img',
                'description': '随机获得一种新植物种子'
            },
            {
                'id': 'fertilizer',
                'name': '肥料',
                'price': 30,
                'type': 'consumable',
                'icon': 'fertilizer_img',
                'description': '植物生长速度提升30%'
            }
        ]

    def load_purchased_items(self):
        """从文件加载已购买物品"""
        try:
            if os.path.exists("save/purchased_items.json"):  # 修改路径
                with open("save/purchased_items.json", "r", encoding="utf-8") as f:
                    return set(json.load(f))
            return set()
        except:
            return set()

    def save_purchased_items(self):
        """保存已购买物品到文件"""
        try:
            with open("save/purchased_items.json", "w", encoding="utf-8") as f:  # 修改路径
                json.dump(list(self.purchased_items), f, ensure_ascii=False, indent=2)
        except:
            pass

    def purchase_item(self, item_id):
        """购买物品"""
        if item_id not in self.purchased_items:
            self.purchased_items.add(item_id)
            self.save_purchased_items()
            return True
        return False

    def is_purchased(self, item_id):
        """检查物品是否已购买"""
        return item_id in self.purchased_items

    def has_cart(self):
        """检查是否购买了小推车"""
        return self.is_purchased('cart')

    def has_hammer(self):
        """检查是否购买了锤子"""
        return self.is_purchased('hammer')

    def has_7th_card_slot(self):
        """检查是否购买了第七卡槽"""
        return self.is_purchased('7th_cardbg')

    @property
    def total_pages(self):
        """总页数"""
        return (len(self.shop_items) + self.items_per_page - 1) // self.items_per_page

    def get_current_page_items(self):
        """获取当前页面的商品"""
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return self.shop_items[start_idx:end_idx]

    def can_prev_page(self):
        """是否可以翻到上一页"""
        return self.current_page > 0

    def can_next_page(self):
        """是否可以翻到下一页"""
        return self.current_page < self.total_pages - 1

    def prev_page(self):
        """翻到上一页"""
        if self.can_prev_page():
            self.current_page -= 1

    def next_page(self):
        """翻到下一页"""
        if self.can_next_page():
            self.current_page += 1