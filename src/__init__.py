# 4S店汽车销售线索自动获取系统
# 版本: 1.0.0
# 作者: OpenClaw
# 描述: 自动监控多平台评论，识别潜在购车用户并自动触达

__version__ = "1.0.0"
__author__ = "OpenClaw"
__description__ = "4S店汽车销售线索自动获取系统"

# 导出核心模块
from .database import Database
from .scorer import UserScorer
from .deduplicator import Deduplicator
from .messenger import Messenger
from .utils import *

__all__ = [
    "Database",
    "UserScorer",
    "Deduplicator",
    "Messenger",
]