"""
网页存储适配器 - 用于在浏览器环境中替代文件系统操作
"""
import json
import sys

# 检测是否在网页环境
IS_WEB = hasattr(sys, '_emscripten_info') or 'emscripten' in sys.platform or 'pygbag' in sys.modules

# 内存存储（作为localStorage的备份）
_memory_storage = {}

def load_from_storage(key, default=None):
    """从存储加载数据"""
    if IS_WEB:
        # 网页环境：使用内存存储
        return _memory_storage.get(key, default)
    else:
        # 桌面环境：尝试从文件加载
        try:
            import os
            filename = f"database/{key}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return default

def save_to_storage(key, data):
    """保存数据到存储"""
    if IS_WEB:
        # 网页环境：保存到内存
        _memory_storage[key] = data
    else:
        # 桌面环境：保存到文件
        try:
            filename = f"database/{key}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

def file_exists(path):
    """检查文件是否存在"""
    if IS_WEB:
        return False  # 网页环境总是返回False
    else:
        import os
        return os.path.exists(path)

def get_file_time(path):
    """获取文件修改时间"""
    if IS_WEB:
        return 0  # 网页环境返回0
    else:
        import os
        return os.path.getmtime(path) if os.path.exists(path) else 0