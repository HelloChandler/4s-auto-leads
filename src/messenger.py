# 消息触达模块
# 负责通过私信、电话等方式触达潜在客户

import os
import time
import random
from datetime import datetime
from typing import Dict, Optional
from loguru import logger
import yaml
from dotenv import load_dotenv
import requests

# 加载环境变量
load_dotenv()

class Messenger:
    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        初始化消息发送器
        :param config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.templates = self.config.get('message_templates', {})
        self.strategy = self.config.get('contact_strategy', {})
        self.contact_hours = self.strategy.get('contact_hours', [9, 21])
        self.max_daily_contacts = self.strategy.get('max_daily_contacts', 50)
        self.retry_times = self.strategy.get('retry_times', 2)
        self.retry_interval = self.strategy.get('retry_interval', 86400)
        
        # OpenClaw配置
        self.openclaw_api_key = os.getenv('OPENCLAW_API_KEY')
        self.openclaw_base_url = os.getenv('OPENCLAW_BASE_URL', 'http://localhost:8080')
        
        # 今日发送计数
        self.today_send_count = 0
        self.last_count_reset = datetime.now().date()
        
        logger.info("消息触达模块初始化完成")

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def _reset_daily_count_if_needed(self):
        """如果是新的一天，重置今日发送计数"""
        today = datetime.now().date()
        if today != self.last_count_reset:
            self.today_send_count = 0
            self.last_count_reset = today
            logger.info("新的一天，已重置每日触达计数")

    def _is_contact_time_allowed(self) -> bool:
        """检查当前时间是否在允许的触达时间段内"""
        current_hour = datetime.now().hour
        start_hour, end_hour = self.contact_hours
        return start_hour <= current_hour < end_hour

    def _can_send_more_today(self) -> bool:
        """检查今日是否还可以发送更多消息"""
        self._reset_daily_count_if_needed()
        return self.today_send_count < self.max_daily_contacts

    def _generate_message(self, template_type: str, level: str, context: Dict) -> str:
        """
        根据模板和上下文生成消息内容
        :param template_type: 模板类型：private_message/call_script
        :param level: 用户等级：high/medium
        :param context: 模板上下文变量
        :return: 生成的消息内容
        """
        template = self.templates.get(template_type, {}).get(level, '')
        if not template:
            logger.warning(f"未找到模板: {template_type}/{level}，使用默认模板")
            template = "您好！看到您关注{brand}{model}车型，我们有最新优惠信息，感兴趣可以了解一下~"
        
        try:
            return template.format(**context)
        except KeyError as e:
            logger.error(f"模板变量缺失: {e}")
            return template

    def _random_delay(self, min_seconds: int = 3, max_seconds: int = 10):
        """随机延迟，避免触发平台反作弊"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        logger.debug(f"随机延迟: {delay:.2f}秒")

    def send_private_message(self, platform: str, user_id: str, level: str, context: Dict) -> Dict:
        """
        发送私信
        :param platform: 平台：douyin/kuaishou/xiaohongshu
        :param user_id: 目标用户ID
        :param level: 用户意向等级
        :param context: 模板上下文，包含brand、model等变量
        :return: 发送结果
        """
        # 检查发送限制
        if not self._is_contact_time_allowed():
            error_msg = f"当前时间不在允许的触达时间段内({self.contact_hours[0]}点-{self.contact_hours[1]}点)"
            logger.warning(error_msg)
            return {'success': False, 'message': error_msg}

        if not self._can_send_more_today():
            error_msg = f"今日触达数量已达上限({self.max_daily_contacts}条)"
            logger.warning(error_msg)
            return {'success': False, 'message': error_msg}

        # 生成消息内容
        message_content = self._generate_message('private_message', level, context)
        logger.info(f"准备发送私信给{platform}用户{user_id}，内容: {message_content[:50]}...")

        try:
            # 随机延迟
            self._random_delay()

            # 调用OpenClaw技能发送私信
            # 这里根据不同平台调用对应的发送接口
            if self.openclaw_api_key:
                headers = {
                    'Authorization': f'Bearer {self.openclaw_api_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'platform': platform,
                    'user_id': user_id,
                    'message': message_content,
                    'type': 'private_message'
                }
                
                response = requests.post(
                    f"{self.openclaw_base_url}/api/messages/send",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get('success'):
                    self.today_send_count += 1
                    logger.info(f"私信发送成功，用户ID: {user_id}")
                    return {
                        'success': True,
                        'message_id': result.get('message_id'),
                        'content': message_content,
                        'send_time': datetime.now().isoformat()
                    }
                else:
                    error_msg = result.get('error', '未知错误')
                    logger.error(f"私信发送失败: {error_msg}")
                    return {'success': False, 'message': error_msg}
            else:
                # 调试模式，模拟发送成功
                logger.warning("OpenClaw API Key未配置，模拟发送成功")
                self.today_send_count += 1
                return {
                    'success': True,
                    'message_id': f'mock_{int(time.time())}',
                    'content': message_content,
                    'send_time': datetime.now().isoformat(),
                    'mock': True
                }

        except Exception as e:
            logger.error(f"发送私信失败: {e}")
            return {'success': False, 'message': str(e)}

    def make_call(self, user_phone: str, level: str, context: Dict) -> Dict:
        """
        发起电话触达
        :param user_phone: 用户电话号码
        :param level: 用户意向等级
        :param context: 模板上下文
        :return: 呼叫结果
        """
        # 检查发送限制
        if not self._is_contact_time_allowed():
            error_msg = f"当前时间不在允许的触达时间段内({self.contact_hours[0]}点-{self.contact_hours[1]}点)"
            logger.warning(error_msg)
            return {'success': False, 'message': error_msg}

        if not self._can_send_more_today():
            error_msg = f"今日触达数量已达上限({self.max_daily_contacts}条)"
            logger.warning(error_msg)
            return {'success': False, 'message': error_msg}

        # 生成话术
        call_script = self._generate_message('call_script', level, context)
        logger.info(f"准备拨打用户电话{user_phone[:3]}****{user_phone[-4:]}，话术: {call_script[:50]}...")

        try:
            # 随机延迟
            self._random_delay(5, 15)

            # 这里调用电话服务API
            # 实际使用时替换为真实的电话服务调用
            logger.warning("电话功能需要配置对应的电话服务API，当前为模拟呼叫")
            self.today_send_count += 1
            
            return {
                'success': True,
                'call_id': f'call_{int(time.time())}',
                'script': call_script,
                'call_time': datetime.now().isoformat(),
                'mock': True
            }

        except Exception as e:
            logger.error(f"发起呼叫失败: {e}")
            return {'success': False, 'message': str(e)}

    def contact_user(self, lead: Dict, channel: str = 'auto') -> Dict:
        """
        统一触达用户入口
        :param lead: 线索数据
        :param channel: 触达渠道：auto/private_message/call
        :return: 触达结果
        """
        user_id = lead.get('user_id')
        platform = lead.get('platform')
        level = lead.get('level', 'medium')
        brand = lead.get('brand', '')
        model = lead.get('model', '')

        context = {
            'brand': brand,
            'model': model,
            'username': lead.get('username', ''),
            'comment_content': lead.get('comment_content', '')
        }

        logger.info(f"开始触达用户: {platform}/{user_id}, 等级: {level}, 渠道: {channel}")

        # 自动选择渠道：高意向用户优先电话，中意向用户优先私信
        if channel == 'auto':
            if level == 'high' and lead.get('phone'):
                channel = 'call'
            else:
                channel = 'private_message'

        result = {'success': False, 'channel': channel}

        if channel == 'private_message':
            send_result = self.send_private_message(platform, user_id, level, context)
            result.update(send_result)
        elif channel == 'call' and lead.get('phone'):
            call_result = self.make_call(lead['phone'], level, context)
            result.update(call_result)
        else:
            error_msg = f"不支持的触达渠道或缺少必要信息: {channel}"
            logger.error(error_msg)
            result['message'] = error_msg

        return result

    def batch_contact(self, leads: List[Dict], channel: str = 'auto') -> List[Dict]:
        """
        批量触达用户
        :param leads: 线索列表
        :param channel: 触达渠道
        :return: 触达结果列表
        """
        results = []
        success_count = 0
        failed_count = 0

        for lead in leads:
            result = self.contact_user(lead, channel)
            results.append({**lead, 'contact_result': result})
            
            if result['success']:
                success_count += 1
            else:
                failed_count += 1

            # 每发送10条日志一次进度
            if len(results) % 10 == 0:
                logger.info(f"批量触达进度: {len(results)}/{len(leads)}, 成功{success_count}, 失败{failed_count}")

        logger.info(f"批量触达完成，共{len(leads)}条，成功{success_count}，失败{failed_count}")
        return results

    def get_contact_statistics(self) -> Dict:
        """
        获取触达统计信息
        :return: 统计数据
        """
        self._reset_daily_count_if_needed()
        
        stats = {
            'today_send_count': self.today_send_count,
            'max_daily_contacts': self.max_daily_contacts,
            'remaining_quota': self.max_daily_contacts - self.today_send_count,
            'contact_hours': self.contact_hours,
            'is_contact_time_allowed': self._is_contact_time_allowed()
        }
        
        logger.info(f"触达统计: 今日已发送{self.today_send_count}条，剩余配额{stats['remaining_quota']}条")
        return stats

    def test_message(self, platform: str, user_id: str, message: str = None) -> Dict:
        """
        发送测试消息
        :param platform: 平台
        :param user_id: 测试用户ID
        :param message: 测试消息内容，不填则使用默认测试消息
        :return: 发送结果
        """
        if not message:
            message = "您好！这是一条测试消息，系统调试使用，打扰请见谅~"
        
        logger.info(f"发送测试消息到{platform}用户{user_id}")
        return self.send_private_message(platform, user_id, 'high', {
            'brand': '测试',
            'model': '车型'
        })