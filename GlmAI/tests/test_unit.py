"""
AI服务单元测试
测试核心功能模块
使用unittest框架
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zhipuGLM.session_manager import (
    SessionManager, Session, SessionStatus, ChatMessage,
    safe_isoformat, safe_parse_isoformat
)
from zhipuGLM.prompts.prompts import (
    EMERGENCY_KEYWORDS, SYMPTOM_KEYWORDS
)
from zhipuGLM.service import (
    detect_emergency, extract_symptoms
)


class TestTimestampFunctions(unittest.TestCase):
    """测试时间戳函数"""
    
    def test_safe_isoformat_returns_string(self):
        """测试safe_isoformat返回字符串"""
        result = safe_isoformat()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        
    def test_safe_isoformat_format(self):
        """测试safe_isoformat格式正确"""
        result = safe_isoformat()
        self.assertIn('T', result)
        self.assertTrue(result.endswith('Z'))
        
    def test_safe_parse_isoformat_valid(self):
        """测试safe_parse_isoformat解析有效时间"""
        from datetime import datetime
        iso_str = "2024-01-15T10:30:00.000Z"
        result = safe_parse_isoformat(iso_str)
        self.assertIsInstance(result, datetime)
        
    def test_safe_parse_isoformat_empty(self):
        """测试safe_parse_isoformat处理空字符串"""
        from datetime import datetime
        result = safe_parse_isoformat("")
        self.assertIsInstance(result, datetime)
        
    def test_safe_parse_isoformat_invalid(self):
        """测试safe_parse_isoformat处理无效字符串"""
        from datetime import datetime
        result = safe_parse_isoformat("invalid")
        self.assertIsInstance(result, datetime)


class TestChatMessage(unittest.TestCase):
    """测试ChatMessage类"""
    
    def test_create_message(self):
        """测试创建消息"""
        msg = ChatMessage("patient", "我感觉有点疼")
        self.assertEqual(msg.role, "patient")
        self.assertEqual(msg.content, "我感觉有点疼")
        self.assertIsNotNone(msg.timestamp)
        
    def test_message_timestamp_format(self):
        """测试消息时间戳格式"""
        msg = ChatMessage("ai", "请描述疼痛位置")
        self.assertIn('T', msg.timestamp)


class TestSession(unittest.TestCase):
    """测试Session类"""
    
    def test_create_session(self):
        """测试创建会话"""
        session = Session("P001", "测试患者", "2024-01-15")
        self.assertEqual(session.patient_id, "P001")
        self.assertEqual(session.patient_name, "测试患者")
        self.assertEqual(session.surgery_date, "2024-01-15")
        self.assertEqual(session.status, SessionStatus.WAITING_SURGERY)
        self.assertEqual(len(session.conversation), 0)
        
    def test_add_message(self):
        """测试添加消息"""
        session = Session("P001", "测试患者", "2024-01-15")
        session.add_message("patient", "我感觉伤口有点疼")
        self.assertEqual(len(session.conversation), 1)
        self.assertEqual(session.conversation[0].role, "patient")
        
    def test_set_surgery_type(self):
        """测试设置手术类型"""
        session = Session("P001", "测试患者", "2024-01-15")
        session.set_surgery_type("阑尾切除术")
        self.assertEqual(session.surgery_type, "阑尾切除术")
        self.assertEqual(session.status, SessionStatus.WAITING_SURGERY_CONFIRM)
        
    def test_confirm_surgery(self):
        """测试确认手术"""
        session = Session("P001", "测试患者", "2024-01-15")
        session.set_surgery_type("阑尾切除术")
        session.confirm_surgery()
        self.assertEqual(session.status, SessionStatus.ACTIVE)
        
    def test_complete_session(self):
        """测试完成会话"""
        session = Session("P001", "测试患者", "2024-01-15")
        session.complete()
        self.assertEqual(session.status, SessionStatus.COMPLETED)
        self.assertIsNotNone(session.ended_at)
        
    def test_get_history(self):
        """测试获取历史记录"""
        session = Session("P001", "测试患者", "2024-01-15")
        session.add_message("patient", "我感觉疼")
        session.add_message("ai", "请描述疼痛位置")
        history = session.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "patient")
        self.assertEqual(history[1]["role"], "ai")


class TestSessionManager(unittest.TestCase):
    """测试SessionManager类"""
    
    def test_create_session(self):
        """测试创建会话"""
        manager = SessionManager()
        session = manager.create_session("P001", "测试患者", "2024-01-15")
        self.assertIn(session.session_id, manager.sessions)
        
    def test_get_session(self):
        """测试获取会话"""
        manager = SessionManager()
        session = manager.create_session("P001", "测试患者", "2024-01-15")
        retrieved = manager.get_session(session.session_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.session_id, session.session_id)
        
    def test_get_nonexistent_session(self):
        """测试获取不存在的会话"""
        manager = SessionManager()
        retrieved = manager.get_session("nonexistent-id")
        self.assertIsNone(retrieved)
        
    def test_end_session(self):
        """测试结束会话"""
        manager = SessionManager()
        session = manager.create_session("P001", "测试患者", "2024-01-15")
        ended = manager.end_session(session.session_id)
        self.assertEqual(ended.status, SessionStatus.COMPLETED)
        
    def test_get_session_history(self):
        """测试获取会话历史"""
        manager = SessionManager()
        session = manager.create_session("P001", "测试患者", "2024-01-15")
        session.add_message("patient", "我感觉疼")
        history = manager.get_session_history(session.session_id)
        self.assertIsNotNone(history)
        self.assertEqual(len(history["messages"]), 1)


class TestEmergencyDetection(unittest.TestCase):
    """测试危急情况检测"""
    
    def test_detect_high_fever(self):
        """测试检测高烧"""
        is_emergency, keywords = detect_emergency("我发烧39度了")
        self.assertTrue(is_emergency)
        self.assertTrue("高烧" in keywords or "发烧39" in keywords)
        
    def test_detect_severe_pain(self):
        """测试检测剧烈疼痛"""
        is_emergency, keywords = detect_emergency("伤口剧烈疼痛")
        self.assertTrue(is_emergency)
        self.assertIn("剧烈疼痛", keywords)
        
    def test_detect_no_emergency(self):
        """测试无危急情况"""
        is_emergency, keywords = detect_emergency("伤口有点痒")
        self.assertFalse(is_emergency)
        self.assertEqual(len(keywords), 0)
        
    def test_detect_multiple_emergencies(self):
        """测试多个危急情况"""
        is_emergency, keywords = detect_emergency("我高烧不退，呼吸困难")
        self.assertTrue(is_emergency)
        self.assertGreaterEqual(len(keywords), 2)


class TestSymptomExtraction(unittest.TestCase):
    """测试症状提取"""
    
    def test_extract_fever(self):
        """测试提取发热症状"""
        symptoms = extract_symptoms("我有点发烧")
        self.assertIn("发热", symptoms)
        
    def test_extract_pain(self):
        """测试提取疼痛症状"""
        symptoms = extract_symptoms("伤口很疼")
        self.assertIn("疼痛", symptoms)
        
    def test_extract_wound_issue(self):
        """测试提取伤口问题"""
        symptoms = extract_symptoms("伤口红肿")
        self.assertIn("伤口问题", symptoms)
        
    def test_extract_multiple_symptoms(self):
        """测试提取多个症状"""
        symptoms = extract_symptoms("我发烧，伤口也疼")
        self.assertGreaterEqual(len(symptoms), 2)


class TestPromptTemplates(unittest.TestCase):
    """测试提示词模板"""
    
    def test_emergency_keywords_not_empty(self):
        """测试危急关键词不为空"""
        self.assertGreater(len(EMERGENCY_KEYWORDS), 0)
        
    def test_symptom_keywords_not_empty(self):
        """测试症状关键词不为空"""
        self.assertGreater(len(SYMPTOM_KEYWORDS), 0)
        
    def test_symptom_keywords_structure(self):
        """测试症状关键词结构"""
        for category, keywords in SYMPTOM_KEYWORDS.items():
            self.assertIsInstance(keywords, list)
            self.assertGreater(len(keywords), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
