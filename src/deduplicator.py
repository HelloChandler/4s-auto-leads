# 去重模块
# 负责检查用户是否已经被触达过，避免重复骚扰

import hashlib
import json
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from loguru import logger
from .database import Database

class Deduplicator:
    def __init__(self, db: Database = None, check_days: int = 30):
        """
        初始化去重器
        :param db: 数据库实例，如果为None则自动创建
        :param check_days: 检查最近多少天内的触达记录，默认30天
        """
        self.db = db or Database()
        self.check_days = check_days
        # 内存缓存，减少数据库查询
        self.cache = {}
        self.cache_ttl = 3600  # 缓存过期时间1小时
        logger.info(f"去重器初始化完成，检查周期: {check_days}天")

    def _get_cache_key(self, user_id: str, platform: str) -> str:
        """生成缓存键"""
        key = f"{platform}:{user_id}"
        return hashlib.md5(key.encode()).hexdigest()

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """检查缓存是否有效"""
        if not cache_entry:
            return False
        expire_time = cache_entry.get('expire_time', 0)
        return datetime.now().timestamp() < expire_time

    def is_duplicate(self, user_id: str, platform: str, force_check_db: bool = False) -> Tuple[bool, Optional[Dict]]:
        """
        检查用户是否已经被触达过
        :param user_id: 平台用户ID
        :param platform: 来源平台
        :param force_check_db: 是否强制检查数据库，跳过缓存
        :return: (是否重复, 触达记录详情)
        """
        # 先检查缓存
        cache_key = self._get_cache_key(user_id, platform)
        if not force_check_db and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.debug(f"缓存命中，用户{platform}/{user_id}已触达")
                return True, cache_entry.get('record')

        # 查询数据库
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT * FROM contacted_users 
                WHERE user_id = ? AND platform = ? 
                AND contact_time >= datetime('now', '-? days')
                ORDER BY contact_time DESC
                LIMIT 1
            ''', (user_id, platform, self.check_days))
            
            result = cursor.fetchone()
            if result:
                record = dict(result)
                # 更新缓存
                self.cache[cache_key] = {
                    'record': record,
                    'expire_time': (datetime.now() + timedelta(seconds=self.cache_ttl)).timestamp()
                }
                logger.info(f"用户{platform}/{user_id}在{self.check_days}天内已触达过，上次触达时间: {record['contact_time']}")
                return True, record
            
            # 缓存未触达的用户，有效期5分钟
            self.cache[cache_key] = {
                'record': None,
                'expire_time': (datetime.now() + timedelta(seconds=300)).timestamp()
            }
            logger.debug(f"用户{platform}/{user_id}未触达过")
            return False, None

        except Exception as e:
            logger.error(f"检查用户重复状态失败: {e}")
            # 出错时默认不认为重复，避免漏处理
            return False, None

    def batch_check_duplicates(self, users: List[Tuple[str, str]]) -> Dict[str, bool]:
        """
        批量检查用户是否重复
        :param users: 用户列表，每个元素是(user_id, platform)元组
        :return: 结果字典，key为"platform:user_id"，value为是否重复
        """
        results = {}
        for user_id, platform in users:
            key = f"{platform}:{user_id}"
            is_dup, _ = self.is_duplicate(user_id, platform)
            results[key] = is_dup
        
        duplicate_count = sum(1 for v in results.values() if v)
        logger.info(f"批量去重检查完成，共{len(results)}个用户，重复{duplicate_count}个")
        return results

    def mark_contacted(self, user_id: str, platform: str, contact_result: str = "success", 
                       contact_channel: str = None, extra_data: Dict = None):
        """
        标记用户为已触达
        :param user_id: 平台用户ID
        :param platform: 来源平台
        :param contact_result: 触达结果
        :param contact_channel: 触达渠道
        :param extra_data: 额外数据
        """
        try:
            # 添加到数据库
            self.db.add_contacted_user(user_id, platform, contact_result)
            
            # 更新缓存
            cache_key = self._get_cache_key(user_id, platform)
            self.cache[cache_key] = {
                'record': {
                    'user_id': user_id,
                    'platform': platform,
                    'contact_time': datetime.now().isoformat(),
                    'contact_result': contact_result,
                    'contact_channel': contact_channel,
                    'extra_data': extra_data
                },
                'expire_time': (datetime.now() + timedelta(seconds=self.cache_ttl)).timestamp()
            }
            
            logger.info(f"用户{platform}/{user_id}已标记为已触达，结果: {contact_result}")

        except Exception as e:
            logger.error(f"标记用户已触达失败: {e}")
            raise

    def get_contact_history(self, user_id: str, platform: str, limit: int = 10) -> List[Dict]:
        """
        获取用户的触达历史
        :param user_id: 平台用户ID
        :param platform: 来源平台
        :param limit: 返回记录数量限制
        :return: 触达历史列表
        """
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT * FROM contacted_users 
                WHERE user_id = ? AND platform = ? 
                ORDER BY contact_time DESC
                LIMIT ?
            ''', (user_id, platform, limit))
            
            records = [dict(row) for row in cursor.fetchall()]
            logger.info(f"获取到用户{platform}/{user_id}的{len(records)}条触达历史")
            return records

        except Exception as e:
            logger.error(f"获取用户触达历史失败: {e}")
            return []

    def cleanup_expired_cache(self):
        """清理过期的缓存条目"""
        now = datetime.now().timestamp()
        expired_keys = [k for k, v in self.cache.items() if v.get('expire_time', 0) < now]
        for key in expired_keys:
            del self.cache[key]
        logger.info(f"清理过期缓存完成，共删除{len(expired_keys)}条过期记录")

    def get_statistics(self) -> Dict:
        """
        获取去重统计信息
        :return: 统计数据
        """
        try:
            cursor = self.db.conn.cursor()
            
            # 总触达用户数
            cursor.execute('SELECT COUNT(*) FROM contacted_users')
            total_contacted = cursor.fetchone()[0]
            
            # 今日触达数
            cursor.execute('''
                SELECT COUNT(*) FROM contacted_users 
                WHERE contact_time >= date('now')
            ''')
            today_contacted = cursor.fetchone()[0]
            
            # 近7天触达数
            cursor.execute('''
                SELECT COUNT(*) FROM contacted_users 
                WHERE contact_time >= date('now', '-7 days')
            ''')
            week_contacted = cursor.fetchone()[0]
            
            # 成功率统计
            cursor.execute('''
                SELECT last_contact_result, COUNT(*) as count 
                FROM contacted_users 
                GROUP BY last_contact_result
            ''')
            result_stats = {row[0]: row[1] for row in cursor.fetchall()}

            stats = {
                'total_contacted': total_contacted,
                'today_contacted': today_contacted,
                'week_contacted': week_contacted,
                'result_distribution': result_stats,
                'cache_size': len(self.cache)
            }

            logger.info(f"去重统计: 总触达{total_contacted}, 今日{today_contacted}, 近7天{week_contacted}")
            return stats

        except Exception as e:
            logger.error(f"获取去重统计失败: {e}")
            return {}

    def deduplicate_leads(self, leads: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        对线索列表进行去重，返回新线索和重复线索
        :param leads: 线索列表，每个元素必须包含user_id和platform字段
        :return: (新线索列表, 重复线索列表)
        """
        new_leads = []
        duplicate_leads = []

        for lead in leads:
            user_id = lead.get('user_id')
            platform = lead.get('platform')
            
            if not user_id or not platform:
                logger.warning(f"线索缺少user_id或platform字段，跳过: {lead}")
                continue

            is_dup, record = self.is_duplicate(user_id, platform)
            if is_dup:
                lead['duplicate_info'] = record
                duplicate_leads.append(lead)
            else:
                new_leads.append(lead)

        logger.info(f"线索去重完成，共{len(leads)}条线索，新线索{len(new_leads)}条，重复{len(duplicate_leads)}条")
        return new_leads, duplicate_leads