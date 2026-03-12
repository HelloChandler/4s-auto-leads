# 用户评分模块
# 负责对评论用户的购车意向进行评分和等级判定

import re
import json
from typing import Dict, List, Tuple, Optional
from loguru import logger
import yaml

class UserScorer:
    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        初始化评分器
        :param config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.scoring_rules = self.config.get('scoring_rules', {})
        self.keyword_weights = self.scoring_rules.get('keyword_matches', {})
        self.levels = self.scoring_rules.get('levels', {
            'high': 20,
            'medium': 10,
            'low': 0
        })
        logger.info("用户评分器初始化完成")

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def _extract_keywords(self, comment: str) -> Tuple[List[str], int]:
        """
        提取评论中的购车相关关键词并计算关键词得分
        :param comment: 用户评论内容
        :return: (匹配到的关键词列表, 关键词总得分)
        """
        comment_lower = comment.lower()
        matched_keywords = []
        keyword_score = 0

        for keyword, weight in self.keyword_weights.items():
            if keyword.lower() in comment_lower:
                matched_keywords.append(keyword)
                keyword_score += weight
                logger.debug(f"匹配到关键词: {keyword}, 权重: {weight}")

        return matched_keywords, keyword_score

    def _calculate_behavior_score(self, comment: str, comment_data: Dict = None) -> int:
        """
        计算行为相关得分
        :param comment: 评论内容
        :param comment_data: 评论的其他数据（回复数、点赞数等）
        :return: 行为得分
        """
        behavior_score = 0
        comment_data = comment_data or {}

        # 评论长度得分
        length_config = self.scoring_rules.get('comment_length', {})
        min_length = length_config.get('min_length', 10)
        length_weight = length_config.get('weight', 2)
        if len(comment) >= min_length:
            behavior_score += length_weight
            logger.debug(f"评论长度达标，加{length_weight}分")

        # 回复数得分
        reply_config = self.scoring_rules.get('reply_count', {})
        reply_threshold = reply_config.get('threshold', 2)
        reply_weight = reply_config.get('weight', 3)
        reply_count = comment_data.get('reply_count', 0)
        if reply_count >= reply_threshold:
            behavior_score += reply_weight
            logger.debug(f"回复数达标，加{reply_weight}分")

        # 提到价格得分
        price_weight = self.scoring_rules.get('mention_price', {}).get('weight', 8)
        # 匹配价格相关的数字模式
        price_patterns = [
            r'\d+万', r'\d+\.?\d*万', r'\d+元', r'\d+\.?\d*元',
            r'多少钱', r'价格', r'优惠', r'落地价', r'首付', r'月供'
        ]
        for pattern in price_patterns:
            if re.search(pattern, comment.lower()):
                behavior_score += price_weight
                logger.debug(f"提到价格相关内容，加{price_weight}分")
                break

        # 提到位置得分
        location_weight = self.scoring_rules.get('mention_location', {}).get('weight', 3)
        # 匹配常见城市和位置相关词汇
        location_patterns = [
            r'北京', r'上海', r'广州', r'深圳', r'杭州', r'南京', r'成都', r'重庆', r'武汉', r'西安',
            r'本地', r'当地', r'本市', r'我在', r'请问', r'你们店', r'4s店', r'地址', r'位置'
        ]
        for pattern in location_patterns:
            if re.search(pattern, comment.lower()):
                behavior_score += location_weight
                logger.debug(f"提到位置相关内容，加{location_weight}分")
                break

        return behavior_score

    def _determine_level(self, total_score: int) -> str:
        """
        根据总得分判定意向等级
        :param total_score: 总得分
        :return: 等级：high/medium/low
        """
        high_threshold = self.levels.get('high', 20)
        medium_threshold = self.levels.get('medium', 10)

        if total_score >= high_threshold:
            return 'high'
        elif total_score >= medium_threshold:
            return 'medium'
        else:
            return 'low'

    def score_user(self, comment: str, comment_data: Dict = None, video_info: Dict = None) -> Dict:
        """
        对用户评论进行综合评分
        :param comment: 用户评论内容
        :param comment_data: 评论的其他数据（回复数、点赞数、用户信息等）
        :param video_info: 视频相关信息（品牌、型号等）
        :return: 评分结果字典
        """
        comment_data = comment_data or {}
        video_info = video_info or {}

        logger.info(f"开始对用户评论进行评分: {comment[:50]}...")

        # 1. 关键词匹配得分
        matched_keywords, keyword_score = self._extract_keywords(comment)

        # 2. 行为得分
        behavior_score = self._calculate_behavior_score(comment, comment_data)

        # 3. 总得分
        total_score = keyword_score + behavior_score

        # 4. 判定等级
        level = self._determine_level(total_score)

        result = {
            'total_score': total_score,
            'level': level,
            'keyword_score': keyword_score,
            'behavior_score': behavior_score,
            'matched_keywords': matched_keywords,
            'keywords_json': json.dumps(matched_keywords, ensure_ascii=False),
            'has_intent': level in ['high', 'medium']
        }

        logger.info(f"用户评分完成，总得分: {total_score}, 等级: {level}, 关键词: {matched_keywords}")
        return result

    def batch_score(self, comments: List[Dict]) -> List[Dict]:
        """
        批量对评论进行评分
        :param comments: 评论列表，每个元素包含comment和comment_data字段
        :return: 评分结果列表
        """
        results = []
        for comment_item in comments:
            comment = comment_item.get('content', '')
            comment_data = comment_item.get('data', {})
            video_info = comment_item.get('video_info', {})
            score_result = self.score_user(comment, comment_data, video_info)
            result = {**comment_item, **score_result}
            results.append(result)
        logger.info(f"批量评分完成，共处理{len(results)}条评论")
        return results

    def get_scoring_statistics(self, scored_results: List[Dict]) -> Dict:
        """
        统计评分结果分布
        :param scored_results: 评分结果列表
        :return: 统计信息
        """
        total = len(scored_results)
        high_count = sum(1 for r in scored_results if r['level'] == 'high')
        medium_count = sum(1 for r in scored_results if r['level'] == 'medium')
        low_count = sum(1 for r in scored_results if r['level'] == 'low')

        stats = {
            'total': total,
            'high_count': high_count,
            'medium_count': medium_count,
            'low_count': low_count,
            'high_rate': high_count / total if total > 0 else 0,
            'medium_rate': medium_count / total if total > 0 else 0,
            'low_rate': low_count / total if total > 0 else 0,
            'avg_score': sum(r['total_score'] for r in scored_results) / total if total > 0 else 0
        }

        logger.info(f"评分统计: 总数{total}, 高意向{high_count}, 中意向{medium_count}, 低意向{low_count}")
        return stats