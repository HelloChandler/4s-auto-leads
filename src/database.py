# 数据库操作模块
# 负责SQLite数据库的初始化、增删改查操作

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from loguru import logger

class Database:
    def __init__(self, db_path: str = "data/leads.db"):
        """
        初始化数据库连接
        :param db_path: 数据库文件路径
        """
        self.db_path = db_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = None
        self._connect()
        self._init_tables()

    def _connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 让查询返回字典格式
            logger.info(f"数据库连接成功: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def _init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()

        # 用户线索表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,  # 平台用户ID
            username TEXT,  # 用户名
            platform TEXT NOT NULL,  # 来源平台：douyin/kuaishou/xiaohongshu
            comment_content TEXT,  # 评论内容
            comment_time DATETIME,  # 评论时间
            video_url TEXT,  # 评论所在视频/笔记URL
            brand TEXT,  # 相关汽车品牌
            model TEXT,  # 相关汽车型号
            score INTEGER,  # 意向评分
            level TEXT,  # 意向等级：high/medium/low
            keywords TEXT,  # 匹配到的关键词，JSON格式
            contact_status TEXT DEFAULT 'pending',  # 触达状态：pending/success/failed
            contact_time DATETIME,  # 触达时间
            contact_channel TEXT,  # 触达渠道：private_message/call
            contact_result TEXT,  # 触达结果描述
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 已触达用户表（用于快速去重）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacted_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            contact_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            contact_count INTEGER DEFAULT 1,
            last_contact_result TEXT,
            UNIQUE(user_id, platform)
        )
        ''')

        # 任务运行日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            platform TEXT,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME,
            status TEXT NOT NULL,  # running/success/failed
            new_comments_count INTEGER DEFAULT 0,
            new_leads_count INTEGER DEFAULT 0,
            contact_count INTEGER DEFAULT 0,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 配置表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        self.conn.commit()
        logger.info("数据库表初始化完成")

    def add_lead(self, lead_data: Dict) -> int:
        """
        添加新线索
        :param lead_data: 线索数据字典
        :return: 插入的线索ID
        """
        try:
            cursor = self.conn.cursor()
            columns = ', '.join(lead_data.keys())
            placeholders = ', '.join(['?' for _ in lead_data])
            values = list(lead_data.values())
            
            query = f'INSERT INTO leads ({columns}) VALUES ({placeholders})'
            cursor.execute(query, values)
            self.conn.commit()
            logger.info(f"新线索添加成功，用户ID: {lead_data.get('user_id')}")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"线索已存在，用户ID: {lead_data.get('user_id')}")
            return -1
        except Exception as e:
            logger.error(f"添加线索失败: {e}")
            self.conn.rollback()
            raise

    def update_lead_contact_status(self, lead_id: int, status: str, channel: str = None, result: str = None):
        """
        更新线索触达状态
        :param lead_id: 线索ID
        :param status: 触达状态：success/failed
        :param channel: 触达渠道
        :param result: 触达结果
        """
        try:
            cursor = self.conn.cursor()
            update_data = {
                'contact_status': status,
                'contact_time': datetime.now(),
                'updated_at': datetime.now()
            }
            if channel:
                update_data['contact_channel'] = channel
            if result:
                update_data['contact_result'] = result

            set_clause = ', '.join([f'{k} = ?' for k in update_data.keys()])
            values = list(update_data.values()) + [lead_id]

            query = f'UPDATE leads SET {set_clause} WHERE id = ?'
            cursor.execute(query, values)
            self.conn.commit()
            logger.info(f"线索ID {lead_id} 触达状态更新为: {status}")
        except Exception as e:
            logger.error(f"更新线索状态失败: {e}")
            self.conn.rollback()
            raise

    def add_contacted_user(self, user_id: str, platform: str, result: str = "success"):
        """
        添加已触达用户
        :param user_id: 平台用户ID
        :param platform: 来源平台
        :param result: 触达结果
        """
        try:
            cursor = self.conn.cursor()
            # 先检查是否存在，存在则更新计数
            cursor.execute('''
                INSERT INTO contacted_users (user_id, platform, last_contact_result)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, platform) DO UPDATE SET
                    contact_count = contact_count + 1,
                    contact_time = CURRENT_TIMESTAMP,
                    last_contact_result = ?
            ''', (user_id, platform, result, result))
            self.conn.commit()
            logger.info(f"已触达用户更新成功: {platform}/{user_id}")
        except Exception as e:
            logger.error(f"添加已触达用户失败: {e}")
            self.conn.rollback()
            raise

    def is_user_contacted(self, user_id: str, platform: str, days: int = 30) -> bool:
        """
        检查用户是否已经被触达过
        :param user_id: 平台用户ID
        :param platform: 来源平台
        :param days: 检查最近多少天内的触达记录，默认30天
        :return: 是否已触达
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 1 FROM contacted_users 
                WHERE user_id = ? AND platform = ? 
                AND contact_time >= datetime('now', '-? days')
            ''', (user_id, platform, days))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"检查用户触达状态失败: {e}")
            return False

    def get_leads_by_level(self, level: str, limit: int = 100) -> List[Dict]:
        """
        根据意向等级获取线索
        :param level: 意向等级：high/medium/low
        :param limit: 返回数量限制
        :return: 线索列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM leads 
                WHERE level = ? AND contact_status = 'pending'
                ORDER BY score DESC
                LIMIT ?
            ''', (level, limit))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取线索失败: {e}")
            return []

    def add_task_log(self, task_data: Dict) -> int:
        """
        添加任务运行日志
        :param task_data: 任务日志数据
        :return: 日志ID
        """
        try:
            cursor = self.conn.cursor()
            columns = ', '.join(task_data.keys())
            placeholders = ', '.join(['?' for _ in task_data])
            values = list(task_data.values())
            
            query = f'INSERT INTO task_logs ({columns}) VALUES ({placeholders})'
            cursor.execute(query, values)
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"添加任务日志失败: {e}")
            self.conn.rollback()
            raise

    def update_task_log(self, log_id: int, status: str, **kwargs):
        """
        更新任务日志
        :param log_id: 日志ID
        :param status: 任务状态
        :param kwargs: 其他需要更新的字段
        """
        try:
            cursor = self.conn.cursor()
            update_data = {
                'status': status,
                'end_time': datetime.now()
            }
            update_data.update(kwargs)

            set_clause = ', '.join([f'{k} = ?' for k in update_data.keys()])
            values = list(update_data.values()) + [log_id]

            query = f'UPDATE task_logs SET {set_clause} WHERE id = ?'
            cursor.execute(query, values)
            self.conn.commit()
        except Exception as e:
            logger.error(f"更新任务日志失败: {e}")
            self.conn.rollback()
            raise

    def get_last_task_run_time(self, task_name: str) -> Optional[datetime]:
        """
        获取任务上次运行时间
        :param task_name: 任务名称
        :return: 上次运行时间
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT end_time FROM task_logs 
                WHERE task_name = ? AND status = 'success'
                ORDER BY end_time DESC
                LIMIT 1
            ''', (task_name,))
            result = cursor.fetchone()
            return datetime.fromisoformat(result[0]) if result else None
        except Exception as e:
            logger.error(f"获取任务上次运行时间失败: {e}")
            return None

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()