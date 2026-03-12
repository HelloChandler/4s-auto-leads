# 通用工具函数模块
# 提供日志配置、时间处理、文件操作等通用功能

import os
import sys
import time
import random
import yaml
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from loguru import logger
import hashlib
import re

def setup_logging(log_level: str = "INFO", log_file: str = "data/logs/app.log") -> None:
    """
    配置日志系统
    :param log_level: 日志级别：DEBUG/INFO/WARNING/ERROR
    :param log_file: 日志文件路径
    """
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        enqueue=True
    )
    
    # 文件输出
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",  # 10MB轮转
        retention=30,  # 保留30天
        compression="zip",  # 压缩历史日志
        enqueue=True
    )
    
    logger.info(f"日志系统初始化完成，级别: {log_level}")

def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    加载YAML配置文件
    :param config_path: 配置文件路径
    :return: 配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.debug(f"配置文件加载成功: {config_path}")
        return config or {}
    except Exception as e:
        logger.error(f"加载配置文件失败 {config_path}: {e}")
        raise

def save_yaml_config(config: Dict[str, Any], config_path: str) -> None:
    """
    保存配置到YAML文件
    :param config: 配置字典
    :param config_path: 配置文件路径
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        logger.debug(f"配置文件保存成功: {config_path}")
    except Exception as e:
        logger.error(f"保存配置文件失败 {config_path}: {e}")
        raise

def load_json_file(file_path: str) -> Any:
    """
    加载JSON文件
    :param file_path: JSON文件路径
    :return: JSON数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"JSON文件加载成功: {file_path}")
        return data
    except Exception as e:
        logger.error(f"加载JSON文件失败 {file_path}: {e}")
        raise

def save_json_file(data: Any, file_path: str, indent: int = 2) -> None:
    """
    保存数据到JSON文件
    :param data: 要保存的数据
    :param file_path: 文件路径
    :param indent: 缩进空格数
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        logger.debug(f"JSON文件保存成功: {file_path}")
    except Exception as e:
        logger.error(f"保存JSON文件失败 {file_path}: {e}")
        raise

def get_current_time_str(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前时间字符串
    :param format_str: 时间格式
    :return: 格式化的时间字符串
    """
    return datetime.now().strftime(format_str)

def get_today_str() -> str:
    """获取今日日期字符串，格式：YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")

def timestamp_to_datetime(timestamp: float) -> datetime:
    """
    时间戳转datetime对象
    :param timestamp: 时间戳（秒）
    :return: datetime对象
    """
    return datetime.fromtimestamp(timestamp)

def datetime_to_str(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    datetime对象转字符串
    :param dt: datetime对象
    :param format_str: 时间格式
    :return: 时间字符串
    """
    return dt.strftime(format_str)

def str_to_datetime(time_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    字符串转datetime对象
    :param time_str: 时间字符串
    :param format_str: 时间格式
    :return: datetime对象
    """
    try:
        return datetime.strptime(time_str, format_str)
    except ValueError as e:
        logger.error(f"时间字符串解析失败: {time_str}, 格式: {format_str}, 错误: {e}")
        raise

def get_time_diff_in_seconds(time1: datetime, time2: datetime) -> float:
    """
    计算两个时间的差值（秒）
    :param time1: 时间1
    :param time2: 时间2
    :return: 时间差（秒），正数表示time1比time2晚
    """
    return (time1 - time2).total_seconds()

def random_delay(min_seconds: float, max_seconds: float = None) -> None:
    """
    随机延迟
    :param min_seconds: 最小延迟秒数
    :param max_seconds: 最大延迟秒数，不填则固定延迟min_seconds
    """
    if max_seconds is None:
        delay = min_seconds
    else:
        delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    logger.debug(f"随机延迟: {delay:.2f}秒")

def md5_hash(text: str) -> str:
    """
    计算字符串的MD5哈希值
    :param text: 输入字符串
    :return: MD5哈希值
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def extract_phone_number(text: str) -> Optional[str]:
    """
    从文本中提取电话号码
    :param text: 输入文本
    :return: 匹配到的电话号码，没有则返回None
    """
    # 匹配中国大陆手机号
    phone_pattern = r'1[3-9]\d{9}'
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else None

def extract_keywords(text: str, keywords: List[str]) -> List[str]:
    """
    从文本中提取匹配的关键词
    :param text: 输入文本
    :param keywords: 关键词列表
    :return: 匹配到的关键词列表
    """
    text_lower = text.lower()
    matched = []
    for keyword in keywords:
        if keyword.lower() in text_lower:
            matched.append(keyword)
    return matched

def clean_text(text: str) -> str:
    """
    清理文本，去除多余空白字符、特殊符号等
    :param text: 原始文本
    :return: 清理后的文本
    """
    if not text:
        return ""
    # 去除多余空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    # 去除特殊符号，保留中文、英文、数字、常见标点
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？,.!? ]', '', text)
    return text

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    :param text: 原始文本
    :param max_length: 最大长度
    :param suffix: 截断后缀
    :return: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def ensure_dir_exists(dir_path: str) -> None:
    """
    确保目录存在，不存在则创建
    :param dir_path: 目录路径
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"目录已创建: {dir_path}")

def get_file_size(file_path: str) -> int:
    """
    获取文件大小（字节）
    :param file_path: 文件路径
    :return: 文件大小，不存在则返回0
    """
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

def get_disk_usage(path: str = ".") -> Dict[str, int]:
    """
    获取磁盘使用情况
    :param path: 要检查的路径
    :return: 磁盘使用信息：total(总字节), used(已用字节), free(可用字节)
    """
    if sys.platform == 'win32':
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        total_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(path),
            None,
            ctypes.pointer(total_bytes),
            ctypes.pointer(free_bytes)
        )
        total = total_bytes.value
        free = free_bytes.value
        used = total - free
    else:
        stat = os.statvfs(path)
        total = stat.f_frsize * stat.f_blocks
        free = stat.f_frsize * stat.f_bfree
        used = total - free
    
    return {
        'total': total,
        'used': used,
        'free': free
    }

def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为可读格式
    :param size_bytes: 文件大小（字节）
    :return: 格式化后的大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def retry_on_failure(max_retries: int = 3, delay: int = 1, backoff: int = 2):
    """
    重试装饰器，函数失败时自动重试
    :param max_retries: 最大重试次数
    :param delay: 初始延迟秒数
    :param backoff: 延迟倍数，每次重试延迟乘以这个数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"函数 {func.__name__} 执行失败，已达到最大重试次数 {max_retries}，错误: {e}")
                        raise
                    logger.warning(f"函数 {func.__name__} 执行失败，第 {retries} 次重试，延迟 {current_delay} 秒，错误: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator

def singleton(cls):
    """单例模式装饰器"""
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

class TimeUtils:
    """时间工具类"""
    
    @staticmethod
    def now() -> datetime:
        """获取当前时间"""
        return datetime.now()
    
    @staticmethod
    def today() -> datetime:
        """获取今日0点时间"""
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def tomorrow() -> datetime:
        """获取明日0点时间"""
        return TimeUtils.today() + timedelta(days=1)
    
    @staticmethod
    def is_business_hour(start_hour: int = 9, end_hour: int = 18) -> bool:
        """检查当前是否为工作时间"""
        current_hour = datetime.now().hour
        return start_hour <= current_hour < end_hour
    
    @staticmethod
    def is_weekend() -> bool:
        """检查当前是否为周末"""
        return datetime.now().weekday() >= 5

class StringUtils:
    """字符串工具类"""
    
    @staticmethod
    def is_empty(s: str) -> bool:
        """判断字符串是否为空"""
        return s is None or len(s.strip()) == 0
    
    @staticmethod
    def is_not_empty(s: str) -> bool:
        """判断字符串是否不为空"""
        return not StringUtils.is_empty(s)
    
    @staticmethod
    def camel_to_snake(s: str) -> str:
        """驼峰命名转下划线命名"""
        pattern = re.compile(r'(?<!^)(?=[A-Z])')
        return pattern.sub('_', s).lower()
    
    @staticmethod
    def snake_to_camel(s: str) -> str:
        """下划线命名转驼峰命名"""
        parts = s.split('_')
        return parts[0] + ''.join(part.capitalize() for part in parts[1:])

class ValidationUtils:
    """验证工具类"""
    
    @staticmethod
    def is_phone_number(phone: str) -> bool:
        """验证是否为中国大陆手机号"""
        if StringUtils.is_empty(phone):
            return False
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def is_email(email: str) -> bool:
        """验证是否为邮箱地址"""
        if StringUtils.is_empty(email):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_url(url: str) -> bool:
        """验证是否为URL地址"""
        if StringUtils.is_empty(url):
            return False
        pattern = r'^https?://[^\s]+$'
        return re.match(pattern, url) is not None