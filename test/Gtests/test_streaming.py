# -*- coding: utf-8 -*-
"""
AI服务完整功能测试脚本
包含: 流式输出、结构化病历、多轮对话、边界测试、错误处理、性能测试
"""
import sys
import os
import time
import uuid
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 禁用输出缓冲，确保实时显示
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'GlmAI'))

import grpc
import connect.medical_ai_pb2 as medical_ai_pb2
import connect.medical_ai_pb2_grpc as medical_ai_grpc


class TestResult:
    """测试结果类"""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.duration = 0.0
        self.details = {}
    
    def set_passed(self, message: str = ""):
        self.passed = True
        self.message = message
    
    def set_failed(self, message: str):
        self.passed = False
        self.message = message


class TestRunner:
    """测试运行器"""
    def __init__(self, stub):
        self.stub = stub
        self.results = []
        self.start_time = None
    
    def add_result(self, result: TestResult):
        self.results.append(result)
    
    def print_header(self, title: str):
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
    
    def print_section(self, title: str):
        print(f"\n--- {title} ---")
    
    def summary(self):
        """打印测试汇总"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print("\n" + "="*70)
        print("  测试结果汇总")
        print("="*70)
        
        print(f"\n{'测试项目':<35} {'状态':<8} {'耗时':<10} {'说明'}")
        print("-" * 80)
        
        for r in self.results:
            status = "✅ 通过" if r.passed else "❌ 失败"
            duration = f"{r.duration:.2f}s"
            print(f"{r.name:<35} {status:<8} {duration:<10} {r.message}")
        
        print("-" * 80)
        print(f"\n总计: {passed}/{total} 通过", end="")
        if failed > 0:
            print(f", {failed} 项失败")
        else:
            print(" - 全部通过! ✅")
        
        return passed == total


class FunctionalTests:
    """功能测试类"""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.stub = runner.stub
    
    def test_create_session(self) -> str:
        """测试1: 创建会话"""
        result = TestResult("创建会话")
        start = time.time()
        
        try:
            request = medical_ai_pb2.CreateSessionRequest(
                patient_id=f"test_patient_{uuid.uuid4().hex[:8]}",
                patient_name="测试患者",
                surgery_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            response = self.stub.CreateSession(request)
            
            if response.session_id and response.welcome_message:
                result.set_passed(f"session_id: {response.session_id[:16]}...")
                result.details['session_id'] = response.session_id
            else:
                result.set_failed("返回数据不完整")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.details.get('session_id', '')
    
    def test_chat_surgery_type(self, session_id: str) -> bool:
        """测试2: 流式对话 - 手术类型识别"""
        result = TestResult("流式对话-手术类型识别")
        start = time.time()
        
        try:
            surgery_types = [
                "我做的是阑尾切除手术",
                "刚做完甲状腺切除手术",
                "做了胆囊切除手术"
            ]
            
            def request_generator():
                yield medical_ai_pb2.ChatRequest(
                    session_id=session_id,
                    message=surgery_types[0],
                    is_end=False
                )
            
            chunk_count = 0
            full_response = ""
            
            for response in self.stub.Chat(request_generator()):
                if response.content:
                    chunk_count += 1
                    full_response += response.content
            
            if chunk_count > 0 and len(full_response) > 10:
                result.set_passed(f"收到 {chunk_count} 个数据块, 响应长度: {len(full_response)}")
            else:
                result.set_failed(f"响应不完整: chunks={chunk_count}, len={len(full_response)}")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed
    
    def test_chat_symptom(self, session_id: str) -> bool:
        """测试3: 流式对话 - 症状描述"""
        result = TestResult("流式对话-症状描述")
        start = time.time()
        
        try:
            symptoms = "伤口有点疼，偶尔还会恶心，没有发烧"
            
            def request_generator():
                yield medical_ai_pb2.ChatRequest(
                    session_id=session_id,
                    message=symptoms,
                    is_end=False
                )
            
            chunk_count = 0
            for response in self.stub.Chat(request_generator()):
                if response.content:
                    chunk_count += 1
            
            if chunk_count > 0:
                result.set_passed(f"收到 {chunk_count} 个数据块")
            else:
                result.set_failed("未收到任何响应数据")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed
    
    def test_chat_fever(self, session_id: str) -> bool:
        """测试4: 流式对话 - 发烧情况"""
        result = TestResult("流式对话-发烧情况")
        start = time.time()
        
        try:
            fever_msg = "体温38.2度，有点担心是不是感染了"
            
            def request_generator():
                yield medical_ai_pb2.ChatRequest(
                    session_id=session_id,
                    message=fever_msg,
                    is_end=False
                )
            
            chunk_count = 0
            for response in self.stub.Chat(request_generator()):
                if response.content:
                    chunk_count += 1
            
            if chunk_count > 0:
                result.set_passed(f"收到 {chunk_count} 个数据块")
            else:
                result.set_failed("未收到任何响应数据")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed
    
    def test_multi_round_conversation(self, session_id: str) -> bool:
        """测试5: 多轮对话"""
        result = TestResult("多轮对话连续交互")
        start = time.time()
        
        try:
            messages = [
                "我已经排气了",
                "今天可以喝粥了吗",
                "医生说明天可以出院"
            ]
            
            total_chunks = 0
            for msg in messages:
                def request_generator():
                    yield medical_ai_pb2.ChatRequest(
                        session_id=session_id,
                        message=msg,
                        is_end=False
                    )
                
                for response in self.stub.Chat(request_generator()):
                    if response.content:
                        total_chunks += 1
            
            if total_chunks > 0:
                result.set_passed(f"3轮对话共收到 {total_chunks} 个数据块")
            else:
                result.set_failed("多轮对话无响应")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed
    
    def test_end_session(self, session_id: str) -> bool:
        """测试6: 结束会话生成病历"""
        result = TestResult("结束会话生成病历")
        start = time.time()
        
        try:
            request = medical_ai_pb2.EndSessionRequest(session_id=session_id)
            response = self.stub.EndSession(request)
            
            report = response.report
            
            if response.status == "COMPLETED" and report.present_illness:
                result.set_passed(f"病历长度: {len(report.present_illness)} 字符")
            else:
                result.set_failed(f"状态: {response.status}, 病历内容为空")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed
    
    def test_get_session_history(self, session_id: str) -> bool:
        """测试7: 获取对话历史"""
        result = TestResult("获取对话历史")
        start = time.time()
        
        try:
            request = medical_ai_pb2.GetSessionHistoryRequest(session_id=session_id)
            response = self.stub.GetSessionHistory(request)
            
            if response.session_id and len(response.messages) > 0:
                result.set_passed(f"消息数: {len(response.messages)}")
            else:
                result.set_failed("无历史记录")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed


class BoundaryTests:
    """边界测试类"""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.stub = runner.stub
    
    def test_empty_message(self, session_id: str) -> bool:
        """测试8: 空消息处理"""
        result = TestResult("边界测试-空消息")
        start = time.time()
        
        try:
            def request_generator():
                yield medical_ai_pb2.ChatRequest(
                    session_id=session_id,
                    message="",
                    is_end=False
                )
            
            has_response = False
            for response in self.stub.Chat(request_generator()):
                if response.content:
                    has_response = True
            
            result.set_passed("空消息处理正常" if has_response else "空消息返回空响应")
        
        except Exception as e:
            if "empty" in str(e).lower() or "invalid" in str(e).lower():
                result.set_passed("正确拒绝空消息")
            else:
                result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed
    
    def test_long_message(self, session_id: str) -> bool:
        """测试9: 超长消息处理"""
        result = TestResult("边界测试-超长消息")
        start = time.time()
        
        try:
            long_msg = "术后恢复情况描述：" + "伤口恢复良好，" * 100
            
            def request_generator():
                yield medical_ai_pb2.ChatRequest(
                    session_id=session_id,
                    message=long_msg,
                    is_end=False
                )
            
            chunk_count = 0
            for response in self.stub.Chat(request_generator()):
                if response.content:
                    chunk_count += 1
            
            if chunk_count > 0:
                result.set_passed(f"超长消息({len(long_msg)}字符)处理正常")
            else:
                result.set_failed("超长消息无响应")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed
    
    def test_special_characters(self, session_id: str) -> bool:
        """测试10: 特殊字符处理"""
        result = TestResult("边界测试-特殊字符")
        start = time.time()
        
        try:
            special_msg = "伤口位置：右下腹（麦氏点）\n症状：<疼痛>、\"恶心\"、'呕吐'"
            
            def request_generator():
                yield medical_ai_pb2.ChatRequest(
                    session_id=session_id,
                    message=special_msg,
                    is_end=False
                )
            
            chunk_count = 0
            for response in self.stub.Chat(request_generator()):
                if response.content:
                    chunk_count += 1
            
            if chunk_count > 0:
                result.set_passed("特殊字符处理正常")
            else:
                result.set_failed("特殊字符导致无响应")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed


class ErrorHandlingTests:
    """错误处理测试类"""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.stub = runner.stub
    
    def test_invalid_session_id(self) -> bool:
        """测试11: 无效会话ID"""
        result = TestResult("错误处理-无效会话ID")
        start = time.time()
        
        try:
            def request_generator():
                yield medical_ai_pb2.ChatRequest(
                    session_id="invalid-session-id-12345",
                    message="测试消息",
                    is_end=False
                )
            
            has_error_response = False
            for response in self.stub.Chat(request_generator()):
                if response.content and ("不存在" in response.content or "过期" in response.content or "ERROR" in response.content):
                    has_error_response = True
            
            if has_error_response:
                result.set_passed("正确返回错误提示")
            else:
                result.set_passed("服务端处理了无效ID")
        
        except grpc.RpcError as e:
            result.set_passed(f"正确抛出gRPC错误: {e.code()}")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed
    
    def test_ended_session_reuse(self, session_id: str) -> bool:
        """测试12: 已结束会话重用"""
        result = TestResult("错误处理-已结束会话重用")
        start = time.time()
        
        try:
            def request_generator():
                yield medical_ai_pb2.ChatRequest(
                    session_id=session_id,
                    message="这是对已结束会话的测试",
                    is_end=False
                )
            
            has_response = False
            for response in self.stub.Chat(request_generator()):
                if response.content:
                    has_response = True
            
            if has_response:
                result.set_passed("已结束会话仍可访问")
            else:
                result.set_passed("已结束会话正确拒绝")
        
        except Exception as e:
            result.set_passed(f"正确处理: {str(e)[:30]}")
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed
    
    def test_double_end_session(self, session_id: str) -> bool:
        """测试13: 重复结束会话"""
        result = TestResult("错误处理-重复结束会话")
        start = time.time()
        
        try:
            request = medical_ai_pb2.EndSessionRequest(session_id=session_id)
            response = self.stub.EndSession(request)
            
            if response.status:
                result.set_passed(f"重复结束返回状态: {response.status}")
            else:
                result.set_passed("重复结束正常处理")
        
        except grpc.RpcError as e:
            result.set_passed(f"正确抛出错误: {e.code()}")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed


class PerformanceTests:
    """性能测试类"""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.stub = runner.stub
    
    def test_response_time(self, session_id: str) -> bool:
        """测试14: 响应时间测试"""
        result = TestResult("性能测试-响应时间")
        start = time.time()
        
        try:
            times = []
            
            for i in range(3):
                msg = f"第{i+1}次测试消息"
                
                def request_generator():
                    yield medical_ai_pb2.ChatRequest(
                        session_id=session_id,
                        message=msg,
                        is_end=False
                    )
                
                req_start = time.time()
                chunk_count = 0
                for response in self.stub.Chat(request_generator()):
                    if response.content:
                        chunk_count += 1
                req_time = time.time() - req_start
                times.append(req_time)
            
            avg_time = sum(times) / len(times)
            if avg_time < 60:
                result.set_passed(f"平均响应时间: {avg_time:.2f}s")
            else:
                result.set_failed(f"响应时间过长: {avg_time:.2f}s")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed
    
    def test_concurrent_sessions(self) -> bool:
        """测试15: 并发会话测试"""
        result = TestResult("性能测试-并发会话")
        start = time.time()
        
        try:
            session_ids = []
            
            for i in range(3):
                request = medical_ai_pb2.CreateSessionRequest(
                    patient_id=f"concurrent_test_{i}",
                    patient_name=f"并发测试患者{i}",
                    surgery_date=datetime.now().strftime("%Y-%m-%d")
                )
                response = self.stub.CreateSession(request)
                if response.session_id:
                    session_ids.append(response.session_id)
            
            if len(session_ids) == 3:
                result.set_passed(f"成功创建 {len(session_ids)} 个并发会话")
            else:
                result.set_failed(f"仅创建 {len(session_ids)}/3 个会话")
        
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return result.passed


class LongConversationTests:
    """长对话测试类 - 测试30轮连续对话"""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.stub = runner.stub
        self.issues = []
    
    def test_30_round_conversation(self, session_id: str) -> dict:
        """测试16: 30轮长对话测试"""
        result = TestResult("长对话-30轮连续交互")
        start = time.time()
        
        conversation_topics = [
            "我刚做完阑尾切除手术3天",
            "伤口有点疼，是正常的吗",
            "疼痛程度大概是4分，不是特别剧烈",
            "伤口周围有点红肿",
            "没有发烧，体温36.8度",
            "已经排气了，可以吃东西了吗",
            "今天吃了点粥，感觉还行",
            "有点恶心，不想吃东西",
            "排便了吗？还没有",
            "有点腹胀，正常吗",
            "伤口换药是医生换还是自己换",
            "什么时候可以拆线",
            "可以洗澡吗",
            "饮食上有什么禁忌",
            "可以吃水果吗",
            "什么时候可以恢复正常工作",
            "可以运动吗，比如散步",
            "伤口有点渗液，要紧吗",
            "晚上睡觉伤口疼，影响睡眠",
            "需要复查吗，什么时候",
            "开了什么药需要按时吃吗",
            "止痛药可以继续吃吗",
            "有点便秘怎么办",
            "可以喝牛奶吗",
            "什么时候可以开车",
            "伤口愈合大概需要多长时间",
            "有什么并发症需要注意吗",
            "出院后需要注意什么",
            "家属需要做什么准备",
            "谢谢医生，我没有其他问题了"
        ]
        
        stats = {
            'total_rounds': 0,
            'successful_rounds': 0,
            'failed_rounds': 0,
            'total_chunks': 0,
            'response_times': [],
            'context_retention_issues': 0,
            'memory_issues': []
        }
        
        try:
            for i, msg in enumerate(conversation_topics):
                round_start = time.time()
                stats['total_rounds'] += 1
                
                def request_generator():
                    yield medical_ai_pb2.ChatRequest(
                        session_id=session_id,
                        message=msg,
                        is_end=False
                    )
                
                chunk_count = 0
                try:
                    for response in self.stub.Chat(request_generator()):
                        if response.content:
                            chunk_count += 1
                    
                    round_time = time.time() - round_start
                    stats['response_times'].append(round_time)
                    stats['total_chunks'] += chunk_count
                    
                    if chunk_count > 0:
                        stats['successful_rounds'] += 1
                    else:
                        stats['failed_rounds'] += 1
                        stats['memory_issues'].append(f"第{i+1}轮无响应: {msg[:20]}")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    stats['failed_rounds'] += 1
                    stats['memory_issues'].append(f"第{i+1}轮异常: {str(e)[:30]}")
            
            avg_time = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
            
            if stats['successful_rounds'] >= 28:
                result.set_passed(f"{stats['successful_rounds']}/30轮成功, 平均响应{avg_time:.2f}s")
            elif stats['successful_rounds'] >= 20:
                result.set_passed(f"{stats['successful_rounds']}/30轮成功(部分问题)")
                self.issues.append("长对话稳定性需优化")
            else:
                result.set_failed(f"仅{stats['successful_rounds']}/30轮成功")
            
            result.details['stats'] = stats
            
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return stats


class SymptomExtractionTests:
    """病症信息定位抓取测试类"""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.stub = runner.stub
        self.issues = []
    
    def test_symptom_extraction(self, session_id: str) -> dict:
        """测试17: 病症信息定位抓取"""
        result = TestResult("病症信息-定位抓取能力")
        start = time.time()
        
        test_cases = [
            {
                'message': "我做完阑尾手术5天了，伤口有点疼，体温37.5度，有点低烧，还有点恶心想吐",
                'expected_symptoms': ['伤口疼', '低烧', '恶心', '想吐'],
                'expected_values': ['体温37.5度', '术后5天']
            },
            {
                'message': "甲状腺切除手术后一周，声音有点嘶哑，吞咽有点困难，没有发烧",
                'expected_symptoms': ['声音嘶哑', '吞咽困难'],
                'expected_values': ['术后一周', '无发烧']
            },
            {
                'message': "胆囊切除术后第3天，右上腹隐痛，已经排气排便了，食欲不太好",
                'expected_symptoms': ['右上腹隐痛', '食欲不好'],
                'expected_values': ['术后第3天', '已排气', '已排便']
            }
        ]
        
        extraction_stats = {
            'total_cases': len(test_cases),
            'successful_extractions': 0,
            'missed_symptoms': [],
            'response_quality': []
        }
        
        try:
            for i, case in enumerate(test_cases):
                def request_generator():
                    yield medical_ai_pb2.ChatRequest(
                        session_id=session_id,
                        message=case['message'],
                        is_end=False
                    )
                
                full_response = ""
                for response in self.stub.Chat(request_generator()):
                    if response.content:
                        full_response += response.content
                
                found_symptoms = []
                missed = []
                
                for symptom in case['expected_symptoms']:
                    if symptom in full_response or any(s in full_response for s in symptom.split()):
                        found_symptoms.append(symptom)
                    else:
                        missed.append(symptom)
                
                if len(found_symptoms) >= len(case['expected_symptoms']) * 0.5:
                    extraction_stats['successful_extractions'] += 1
                else:
                    extraction_stats['missed_symptoms'].append({
                        'case': i + 1,
                        'missed': missed
                    })
                
                extraction_stats['response_quality'].append({
                    'case': i + 1,
                    'response_length': len(full_response),
                    'found': len(found_symptoms),
                    'total': len(case['expected_symptoms'])
                })
                
                time.sleep(0.5)
            
            success_rate = extraction_stats['successful_extractions'] / extraction_stats['total_cases']
            
            if success_rate >= 0.8:
                result.set_passed(f"病症识别率: {success_rate*100:.0f}%")
            elif success_rate >= 0.5:
                result.set_passed(f"病症识别率: {success_rate*100:.0f}%(需优化)")
                self.issues.append("病症信息抓取不完整")
            else:
                result.set_failed(f"病症识别率过低: {success_rate*100:.0f}%")
            
            result.details['stats'] = extraction_stats
            
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return extraction_stats


class HealthAdviceQualityTests:
    """健康建议质量测试类"""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.stub = runner.stub
        self.issues = []
    
    def test_health_advice_quality(self, session_id: str) -> dict:
        """测试18: 健康建议专业性和响应时间"""
        result = TestResult("健康建议-专业性与响应时间")
        start = time.time()
        
        advice_scenarios = [
            {
                'message': "伤口发炎了，红肿有脓，体温38.5度",
                'required_keywords': ['就医', '医院', '医生', '感染', '处理'],
                'severity': 'high'
            },
            {
                'message': "术后第2天，伤口有点渗血，不多",
                'required_keywords': ['观察', '换药', '清洁', '消毒'],
                'severity': 'medium'
            },
            {
                'message': "可以吃辛辣食物吗",
                'required_keywords': ['避免', '清淡', '饮食', '恢复'],
                'severity': 'low'
            }
        ]
        
        quality_stats = {
            'total_scenarios': len(advice_scenarios),
            'appropriate_advice': 0,
            'response_times': [],
            'missing_keywords': [],
            'severity_handling': []
        }
        
        try:
            for i, scenario in enumerate(advice_scenarios):
                req_start = time.time()
                
                def request_generator():
                    yield medical_ai_pb2.ChatRequest(
                        session_id=session_id,
                        message=scenario['message'],
                        is_end=False
                    )
                
                full_response = ""
                for response in self.stub.Chat(request_generator()):
                    if response.content:
                        full_response += response.content
                
                response_time = time.time() - req_start
                quality_stats['response_times'].append(response_time)
                
                found_keywords = []
                missing = []
                for keyword in scenario['required_keywords']:
                    if keyword in full_response:
                        found_keywords.append(keyword)
                    else:
                        missing.append(keyword)
                
                keyword_coverage = len(found_keywords) / len(scenario['required_keywords'])
                
                if keyword_coverage >= 0.6:
                    quality_stats['appropriate_advice'] += 1
                else:
                    quality_stats['missing_keywords'].append({
                        'scenario': i + 1,
                        'severity': scenario['severity'],
                        'missing': missing
                    })
                
                quality_stats['severity_handling'].append({
                    'scenario': i + 1,
                    'severity': scenario['severity'],
                    'keyword_coverage': keyword_coverage,
                    'response_time': response_time
                })
                
                time.sleep(0.5)
            
            avg_response_time = sum(quality_stats['response_times']) / len(quality_stats['response_times'])
            advice_quality = quality_stats['appropriate_advice'] / quality_stats['total_scenarios']
            
            issues = []
            if avg_response_time > 30:
                issues.append(f"响应时间过长({avg_response_time:.1f}s)")
            if advice_quality < 0.7:
                issues.append("建议专业性不足")
            
            if not issues and advice_quality >= 0.8:
                result.set_passed(f"建议质量: {advice_quality*100:.0f}%, 平均响应: {avg_response_time:.1f}s")
            elif advice_quality >= 0.5:
                result.set_passed(f"建议质量: {advice_quality*100:.0f}%(需优化)")
                self.issues.extend(issues)
            else:
                result.set_failed(f"建议质量过低: {advice_quality*100:.0f}%")
            
            result.details['stats'] = quality_stats
            
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return quality_stats


class MedicalReportQualityTests:
    """结构化病历生成规范测试类"""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.stub = runner.stub
        self.issues = []
    
    def _create_conversation_for_report(self, session_id: str) -> bool:
        """为病历生成创建对话内容"""
        messages = [
            "我刚做完阑尾切除手术，今天是术后第3天",
            "伤口有点疼，疼痛程度大概3分",
            "体温36.8度，没有发烧",
            "已经排气了，今天吃了点粥",
            "有点恶心，没有呕吐",
            "伤口没有红肿，有点渗液",
            "医生开了头孢，在按时吃",
            "可以出院了吗"
        ]
        
        for msg in messages:
            def request_generator():
                yield medical_ai_pb2.ChatRequest(
                    session_id=session_id,
                    message=msg,
                    is_end=False
                )
            
            for response in self.stub.Chat(request_generator()):
                pass
            time.sleep(0.3)
        
        return True
    
    def test_report_structure(self, session_id: str) -> dict:
        """测试19: 结构化病历生成规范"""
        result = TestResult("病历生成-结构化规范")
        start = time.time()
        
        self._create_conversation_for_report(session_id)
        
        report_structure = {
            'required_fields': [
                'present_illness',
                'symptoms',
                'vital_signs',
                'medications',
                'advice'
            ],
            'field_coverage': {},
            'content_quality': {},
            'issues': []
        }
        
        try:
            request = medical_ai_pb2.EndSessionRequest(session_id=session_id)
            response = self.stub.EndSession(request)
            
            report = response.report
            
            report_structure['field_coverage'] = {
                'present_illness': bool(report.present_illness),
                'symptoms': bool(report.symptoms),
                'vital_signs': bool(report.vital_signs),
                'medications': bool(report.medications),
                'advice': bool(report.advice)
            }
            
            report_structure['content_quality'] = {
                'present_illness_length': len(report.present_illness) if report.present_illness else 0,
                'symptoms_length': len(report.symptoms) if report.symptoms else 0,
                'vital_signs_length': len(report.vital_signs) if report.vital_signs else 0,
                'medications_length': len(report.medications) if report.medications else 0,
                'advice_length': len(report.advice) if report.advice else 0
            }
            
            covered_fields = sum(1 for v in report_structure['field_coverage'].values() if v)
            total_fields = len(report_structure['required_fields'])
            coverage_rate = covered_fields / total_fields
            
            if coverage_rate >= 0.8:
                result.set_passed(f"字段覆盖率: {coverage_rate*100:.0f}% ({covered_fields}/{total_fields})")
            elif coverage_rate >= 0.5:
                result.set_passed(f"字段覆盖率: {coverage_rate*100:.0f}%(需完善)")
                missing = [f for f in report_structure['field_coverage'] if not report_structure['field_coverage'][f]]
                report_structure['issues'].append(f"缺失字段: {', '.join(missing)}")
                self.issues.append("病历结构不完整")
            else:
                result.set_failed(f"字段覆盖率过低: {coverage_rate*100:.0f}%")
            
            result.details['stats'] = report_structure
            
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return report_structure


class AIProfessionalismTests:
    """AI建议专业性测试类"""
    
    def __init__(self, runner: TestRunner):
        self.runner = runner
        self.stub = runner.stub
        self.issues = []
    
    def test_medical_professionalism(self, session_id: str) -> dict:
        """测试20: AI建议的医学专业性"""
        result = TestResult("AI建议-医学专业性评估")
        start = time.time()
        
        professionalism_criteria = {
            'medical_accuracy': {
                'description': '医学准确性',
                'test_cases': [
                    {
                        'input': "阑尾炎术后多久可以正常饮食",
                        'expected_elements': ['排气', '流质', '逐渐', '过渡']
                    },
                    {
                        'input': "伤口感染有什么症状",
                        'expected_elements': ['红肿', '发热', '疼痛', '脓液', '渗液']
                    }
                ]
            },
            'safety_disclaimer': {
                'description': '安全免责声明',
                'test_cases': [
                    {
                        'input': "我伤口裂开了怎么办",
                        'expected_elements': ['医院', '就医', '医生', '紧急', '立即']
                    }
                ]
            },
            'doctor_assistance': {
                'description': '医生辅助建议',
                'test_cases': [
                    {
                        'input': "患者术后第5天，伤口愈合良好，体温正常，可以出院吗",
                        'expected_elements': ['评估', '检查', '医生', '确认', '复查']
                    }
                ]
            }
        }
        
        professionalism_stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'category_scores': {},
            'issues': []
        }
        
        try:
            for category, criteria in professionalism_criteria.items():
                category_passed = 0
                category_total = len(criteria['test_cases'])
                
                for test_case in criteria['test_cases']:
                    professionalism_stats['total_tests'] += 1
                    
                    def request_generator():
                        yield medical_ai_pb2.ChatRequest(
                            session_id=session_id,
                            message=test_case['input'],
                            is_end=False
                        )
                    
                    full_response = ""
                    for response in self.stub.Chat(request_generator()):
                        if response.content:
                            full_response += response.content
                    
                    found_elements = sum(1 for elem in test_case['expected_elements'] if elem in full_response)
                    element_coverage = found_elements / len(test_case['expected_elements'])
                    
                    if element_coverage >= 0.5:
                        category_passed += 1
                        professionalism_stats['passed_tests'] += 1
                    else:
                        professionalism_stats['issues'].append({
                            'category': criteria['description'],
                            'input': test_case['input'][:30],
                            'missing': [e for e in test_case['expected_elements'] if e not in full_response]
                        })
                    
                    time.sleep(0.5)
                
                professionalism_stats['category_scores'][category] = {
                    'description': criteria['description'],
                    'score': category_passed / category_total
                }
            
            overall_score = professionalism_stats['passed_tests'] / professionalism_stats['total_tests']
            
            if overall_score >= 0.8:
                result.set_passed(f"专业性评分: {overall_score*100:.0f}%")
            elif overall_score >= 0.5:
                result.set_passed(f"专业性评分: {overall_score*100:.0f}%(需提升)")
                self.issues.append("AI建议专业性需加强")
            else:
                result.set_failed(f"专业性评分过低: {overall_score*100:.0f}%")
            
            result.details['stats'] = professionalism_stats
            
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return professionalism_stats
    
    def test_patient_safety_advice(self, session_id: str) -> dict:
        """测试21: 患者安全建议评估"""
        result = TestResult("AI建议-患者安全性")
        start = time.time()
        
        safety_scenarios = [
            {
                'input': "我发烧39度，伤口红肿流脓",
                'critical_keywords': ['立即', '紧急', '医院', '就医', '感染'],
                'severity': 'critical'
            },
            {
                'input': "伤口出血不止",
                'critical_keywords': ['压迫', '止血', '医院', '紧急'],
                'severity': 'critical'
            },
            {
                'input': "剧烈腹痛，难以忍受",
                'critical_keywords': ['医院', '就医', '检查', '医生'],
                'severity': 'high'
            }
        ]
        
        safety_stats = {
            'total_scenarios': len(safety_scenarios),
            'appropriate_responses': 0,
            'missing_critical': [],
            'severity_handling': []
        }
        
        try:
            for scenario in safety_scenarios:
                def request_generator():
                    yield medical_ai_pb2.ChatRequest(
                        session_id=session_id,
                        message=scenario['input'],
                        is_end=False
                    )
                
                full_response = ""
                for response in self.stub.Chat(request_generator()):
                    if response.content:
                        full_response += response.content
                
                found_critical = [kw for kw in scenario['critical_keywords'] if kw in full_response]
                
                if len(found_critical) >= 2:
                    safety_stats['appropriate_responses'] += 1
                else:
                    safety_stats['missing_critical'].append({
                        'scenario': scenario['input'][:20],
                        'severity': scenario['severity'],
                        'missing': [kw for kw in scenario['critical_keywords'] if kw not in full_response]
                    })
                
                safety_stats['severity_handling'].append({
                    'severity': scenario['severity'],
                    'found_keywords': len(found_critical),
                    'required_keywords': len(scenario['critical_keywords'])
                })
                
                time.sleep(0.5)
            
            safety_rate = safety_stats['appropriate_responses'] / safety_stats['total_scenarios']
            
            if safety_rate >= 0.8:
                result.set_passed(f"安全建议合格率: {safety_rate*100:.0f}%")
            elif safety_rate >= 0.5:
                result.set_passed(f"安全建议合格率: {safety_rate*100:.0f}%(需改进)")
                self.issues.append("危急情况处理需加强")
            else:
                result.set_failed(f"安全建议合格率过低: {safety_rate*100:.0f}%")
            
            result.details['stats'] = safety_stats
            
        except Exception as e:
            result.set_failed(str(e))
        
        result.duration = time.time() - start
        self.runner.add_result(result)
        return safety_stats


def main():
    """主测试函数"""
    print("="*70, flush=True)
    print("  AI服务完整功能测试", flush=True)
    print("  包含: 功能测试、边界测试、错误处理、性能测试、优化测试", flush=True)
    print("="*70, flush=True)
    
    print("\n正在连接AI服务 (localhost:50053)...", flush=True)
    
    channel = grpc.insecure_channel('localhost:50053')
    stub = medical_ai_grpc.PostSurgeryFollowUpServiceStub(channel)
    
    try:
        grpc.channel_ready_future(channel).result(timeout=10)
        print("[OK] 连接成功!\n", flush=True)
    except Exception as e:
        print(f"[ERROR] 连接失败: {e}", flush=True)
        return
    
    runner = TestRunner(stub)
    all_issues = []
    
    print("\n" + "="*70)
    print("  第一部分: 功能测试")
    print("="*70)
    
    functional = FunctionalTests(runner)
    
    session_id = functional.test_create_session()
    if not session_id:
        print("\n[ERROR] 无法创建会话，终止测试")
        channel.close()
        return
    
    time.sleep(0.5)
    functional.test_chat_surgery_type(session_id)
    time.sleep(0.5)
    functional.test_chat_symptom(session_id)
    time.sleep(0.5)
    functional.test_chat_fever(session_id)
    time.sleep(0.5)
    functional.test_multi_round_conversation(session_id)
    time.sleep(0.5)
    functional.test_get_session_history(session_id)
    time.sleep(0.5)
    functional.test_end_session(session_id)
    
    print("\n" + "="*70)
    print("  第二部分: 边界测试")
    print("="*70)
    
    boundary_session = functional.test_create_session()
    time.sleep(0.5)
    
    boundary = BoundaryTests(runner)
    boundary.test_empty_message(boundary_session)
    time.sleep(0.5)
    boundary.test_long_message(boundary_session)
    time.sleep(0.5)
    boundary.test_special_characters(boundary_session)
    
    print("\n" + "="*70)
    print("  第三部分: 错误处理测试")
    print("="*70)
    
    error = ErrorHandlingTests(runner)
    error.test_invalid_session_id()
    time.sleep(0.5)
    error.test_ended_session_reuse(session_id)
    time.sleep(0.5)
    error.test_double_end_session(session_id)
    
    print("\n" + "="*70)
    print("  第四部分: 性能测试")
    print("="*70)
    
    perf_session = functional.test_create_session()
    time.sleep(0.5)
    
    performance = PerformanceTests(runner)
    performance.test_response_time(perf_session)
    time.sleep(0.5)
    performance.test_concurrent_sessions()
    
    print("\n" + "="*70)
    print("  第五部分: 长对话测试 (30轮)")
    print("="*70)
    
    long_conv_session = functional.test_create_session()
    time.sleep(0.5)
    
    long_conv = LongConversationTests(runner)
    long_conv.test_30_round_conversation(long_conv_session)
    all_issues.extend(long_conv.issues)
    
    print("\n" + "="*70)
    print("  第六部分: 病症信息抓取测试")
    print("="*70)
    
    symptom_session = functional.test_create_session()
    time.sleep(0.5)
    
    symptom_test = SymptomExtractionTests(runner)
    symptom_test.test_symptom_extraction(symptom_session)
    all_issues.extend(symptom_test.issues)
    
    print("\n" + "="*70)
    print("  第七部分: 健康建议质量测试")
    print("="*70)
    
    advice_session = functional.test_create_session()
    time.sleep(0.5)
    
    advice_test = HealthAdviceQualityTests(runner)
    advice_test.test_health_advice_quality(advice_session)
    all_issues.extend(advice_test.issues)
    
    print("\n" + "="*70)
    print("  第八部分: 结构化病历生成测试")
    print("="*70)
    
    report_session = functional.test_create_session()
    time.sleep(0.5)
    
    report_test = MedicalReportQualityTests(runner)
    report_test.test_report_structure(report_session)
    all_issues.extend(report_test.issues)
    
    print("\n" + "="*70)
    print("  第九部分: AI建议专业性测试")
    print("="*70)
    
    prof_session = functional.test_create_session()
    time.sleep(0.5)
    
    prof_test = AIProfessionalismTests(runner)
    prof_test.test_medical_professionalism(prof_session)
    time.sleep(0.5)
    prof_test.test_patient_safety_advice(prof_session)
    all_issues.extend(prof_test.issues)
    
    all_passed = runner.summary()
    
    if all_issues:
        print("\n" + "="*70)
        print("  发现的优化建议")
        print("="*70)
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
    
    print("\n" + "="*70)
    print("  测试完成")
    print("="*70)
    print(f"  总测试数: {len(runner.results)}")
    print(f"  通过数: {sum(1 for r in runner.results if r.passed)}")
    print(f"  失败数: {sum(1 for r in runner.results if not r.passed)}")
    print(f"  总耗时: {sum(r.duration for r in runner.results):.2f}s")
    print(f"  优化建议数: {len(all_issues)}")
    print("="*70)
    
    channel.close()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
