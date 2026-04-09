# -*- coding: utf-8 -*-
"""
CareLinkAgent AI服务 - 问题复现测试文件
基于 test/ai/AI服务测试报告.md 和 test/Gtests/AI服务功能测试报告.md 中的问题

测试目标：验证以下已知问题是否仍然存在
1. BUG-1: EndSession 病历结构化字段大量为空
2. BUG-2: Chat 接口对无效 session_id 静默处理
3. BUG-3: CreateSession 无参数校验
4. BUG-4: AnalyzeWoundImage 返回空 invalid_reason
5. BUG-5: ProcessPatientAnswers 错误信息不精确
6. 病症识别率低
7. 健康建议质量评分低
8. 病历结构化生成不完整

运行方式: python test_issue_reproduction.py
"""

import sys
import os
import time
import grpc
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import medical_ai_pb2
import medical_ai_pb2_grpc

AI_SERVICE_HOST = "localhost"
AI_SERVICE_PORT = 50053

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(test_name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{status}] {test_name}")
    if details:
        print(f"       详情: {details}")

def create_insecure_channel():
    return grpc.insecure_channel(
        f"{AI_SERVICE_HOST}:{AI_SERVICE_PORT}",
        options=[
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
        ]
    )

class IssueReproductionTests:
    def __init__(self):
        self.channel = None
        self.stub = None
        self.session_id = None
        self.test_results = []

    def setup(self):
        try:
            self.channel = create_insecure_channel()
            grpc.channel_ready_future(self.channel).result(timeout=10)
            self.stub = medical_ai_pb2_grpc.PostSurgeryFollowupServiceStub(self.channel)
            print("✅ gRPC通道连接成功")
            return True
        except Exception as e:
            print(f"❌ gRPC通道连接失败: {e}")
            return False

    def teardown(self):
        if self.channel:
            self.channel.close()

    def test_bug1_end_session_empty_fields(self):
        print_header("BUG-1: EndSession 病历结构化字段为空")
        print("=" * 70)
        print("测试目标: 验证 EndSession 返回的 MedicalReport 字段是否为空")
        print("预期问题: patient_info、surgery_status、past_history、doctor_advice 字段为空")
        print()

        try:
            channel = create_insecure_channel()
            stub = medical_ai_pb2_grpc.PostSurgeryFollowupServiceStub(channel)

            session_resp = stub.CreateSession(
                medical_ai_pb2.CreateSessionRequest(
                    patient_id="test_patient_001",
                    patient_name="测试患者",
                    surgery_date="2026-04-01"
                ),
                timeout=30
            )
            session_id = session_resp.session_id
            print(f"创建的会话ID: {session_id}")

            stub.Chat(iter([
                medical_ai_pb2.ChatRequest(session_id=session_id, message="我做了阑尾切除手术，现在伤口有点疼", is_end=False),
                medical_ai_pb2.ChatRequest(session_id=session_id, message="体温37.5度，有点低烧", is_end=False),
                medical_ai_pb2.ChatRequest(session_id=session_id, message="没有了", is_end=True)
            ]), timeout=60)

            print("等待10秒确保会话处理完成...")
            time.sleep(10)

            end_resp = stub.EndSession(
                medical_ai_pb2.EndSessionRequest(session_id=session_id),
                timeout=30
            )

            report = end_resp.report
            print()
            print("--- MedicalReport 字段检查 ---")

            patient_info = report.patient
            print(f"patient.name: '{patient_info.name}'")
            print(f"patient.gender: '{patient_info.gender}'")
            print(f"patient.age: {patient_info.age}")
            print(f"patient.surgery_type: '{patient_info.surgery_type}'")
            print(f"patient.surgery_date: '{patient_info.surgery_date}'")
            print(f"patient.doctor_name: '{patient_info.doctor_name}'")
            print()
            print(f"chief_complaint: '{report.chief_complaint}'")
            print()
            print(f"surgery_status.wound_healing: '{report.surgery_status.wound_healing}'")
            print(f"surgery_status.temperature: '{report.surgery_status.temperature}'")
            print(f"surgery_status.appetite: '{report.surgery_status.appetite}'")
            print(f"surgery_status.activity: '{report.surgery_status.activity}'")
            print()
            print(f"past_history.allergy: '{report.past_history.allergy}'")
            print(f"past_history.chronic_disease: '{report.past_history.chronic_disease}'")
            print(f"past_history.medication: '{report.past_history.medication}'")
            print()
            print(f"ai_analysis.health_advice: '{report.ai_analysis.health_advice[:100]}..." if len(report.ai_analysis.health_advice) > 100 else f"ai_analysis.health_advice: '{report.ai_analysis.health_advice}'")
            print(f"ai_analysis.alert_flag: '{report.ai_analysis.alert_flag}'")
            print()
            print(f"doctor_advice.rest_advice: '{report.doctor_advice.rest_advice}'")
            print(f"doctor_advice.diet_advice: '{report.doctor_advice.diet_advice}'")
            print(f"doctor_advice.medication: '{report.doctor_advice.medication}'")
            print(f"doctor_advice.follow_up_date: '{report.doctor_advice.follow_up_date}'")

            is_bug_present = (
                patient_info.name == "" and
                patient_info.gender == "" and
                patient_info.age == 0 and
                report.surgery_status.wound_healing == "" and
                report.past_history.allergy == "" and
                report.doctor_advice.rest_advice == ""
            )

            print_result(
                "BUG-1: EndSession 病历结构化字段为空",
                is_bug_present,
                "字段大量为空" if is_bug_present else "字段已填充"
            )

            channel.close()
            return is_bug_present

        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_bug2_chat_invalid_session_silent(self):
        print_header("BUG-2: Chat 接口对无效 session_id 静默处理")
        print("=" * 70)
        print("测试目标: 验证 Chat 接口对无效 session_id 的处理")
        print("预期问题: 使用不存在的 session_id 时，静默返回空响应而非错误")
        print()

        try:
            channel = create_insecure_channel()
            stub = medical_ai_pb2_grpc.PostSurgeryFollowupServiceStub(channel)

            invalid_session_id = "non_existent_session_id_12345"
            print(f"使用无效session_id: {invalid_session_id}")

            responses = []
            try:
                for resp in stub.Chat(iter([
                    medical_ai_pb2.ChatRequest(session_id=invalid_session_id, message="测试消息", is_end=False)
                ]), timeout=10):
                    responses.append(resp)
                    print(f"收到响应: content='{resp.content[:50]}...' is_final={resp.is_final}" if len(resp.content) > 50 else f"收到响应: content='{resp.content}' is_final={resp.is_final}")
            except grpc.RpcError as e:
                print(f"gRPC错误: code={e.code()} details={e.details()}")
                print_result("BUG-2: Chat 无效session返回错误", True, f"正确返回错误: {e.code()}")
                channel.close()
                return False

            if len(responses) == 0:
                print_result("BUG-2: Chat 无效session静默处理", True, "确认问题存在 - 静默返回空响应")
                channel.close()
                return True
            else:
                print_result("BUG-2: Chat 无效session静默处理", False, "问题已修复 - 有响应返回")
                channel.close()
                return False

        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_bug3_create_session_no_validation(self):
        print_header("BUG-3: CreateSession 无参数校验")
        print("=" * 70)
        print("测试目标: 验证 CreateSession 接口是否校验参数")
        print("预期问题: 空 patient_id、空 patient_name、无效日期格式均能创建会话")
        print()

        bugs_found = []

        try:
            channel = create_insecure_channel()
            stub = medical_ai_pb2_grpc.PostSurgeryFollowupServiceStub(channel)

            print("--- 测试1: 空 patient_id ---")
            try:
                resp = stub.CreateSession(
                    medical_ai_pb2.CreateSessionRequest(
                        patient_id="",
                        patient_name="测试患者",
                        surgery_date="2026-04-01"
                    ),
                    timeout=10
                )
                print(f"空patient_id创建成功: session_id={resp.session_id[:20]}...")
                print_result("BUG-3.1: 空patient_id可创建会话", True, "确认问题存在")
                bugs_found.append("empty_patient_id")
            except grpc.RpcError as e:
                print(f"正确拒绝: code={e.code()} details={e.details()}")
                print_result("BUG-3.1: 空patient_id可创建会话", False, "已添加校验")

            print()
            print("--- 测试2: 空 patient_name ---")
            try:
                resp = stub.CreateSession(
                    medical_ai_pb2.CreateSessionRequest(
                        patient_id="test_patient",
                        patient_name="",
                        surgery_date="2026-04-01"
                    ),
                    timeout=10
                )
                print(f"空patient_name创建成功: session_id={resp.session_id[:20]}...")
                print_result("BUG-3.2: 空patient_name可创建会话", True, "确认问题存在")
                bugs_found.append("empty_patient_name")
            except grpc.RpcError as e:
                print(f"正确拒绝: code={e.code()} details={e.details()}")
                print_result("BUG-3.2: 空patient_name可创建会话", False, "已添加校验")

            print()
            print("--- 测试3: 无效日期格式 ---")
            try:
                resp = stub.CreateSession(
                    medical_ai_pb2.CreateSessionRequest(
                        patient_id="test_patient",
                        patient_name="测试患者",
                        surgery_date="invalid-date-format"
                    ),
                    timeout=10
                )
                print(f"无效日期创建成功: session_id={resp.session_id[:20]}...")
                print_result("BUG-3.3: 无效日期格式可创建会话", True, "确认问题存在")
                bugs_found.append("invalid_date")
            except grpc.RpcError as e:
                print(f"正确拒绝: code={e.code()} details={e.details()}")
                print_result("BUG-3.3: 无效日期格式可创建会话", False, "已添加校验")

            channel.close()

            print()
            print_result(
                "BUG-3: CreateSession 参数校验缺失",
                len(bugs_found) > 0,
                f"发现 {len(bugs_found)} 个校验缺失: {', '.join(bugs_found)}"
            )
            return len(bugs_found) > 0

        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_bug4_analyze_wound_invalid_reason_empty(self):
        print_header("BUG-4: AnalyzeWoundImage 返回空 invalid_reason")
        print("=" * 70)
        print("测试目标: 验证 AnalyzeWoundImage 对无效图片的 invalid_reason 字段")
        print("预期问题: 伪造图片时 image_valid=False 但 invalid_reason 为空")
        print()

        try:
            channel = create_insecure_channel()
            stub = medical_ai_pb2_grpc.PostSurgeryFollowupServiceStub(channel)

            session_resp = stub.CreateSession(
                medical_ai_pb2.CreateSessionRequest(
                    patient_id="test_patient_001",
                    patient_name="测试患者",
                    surgery_date="2026-04-01"
                ),
                timeout=30
            )
            session_id = session_resp.session_id
            print(f"创建的会话ID: {session_id}")

            fake_image_base64 = "fake_image_data_not_real_base64"
            print(f"发送伪造图片 base64 (长度: {len(fake_image_base64)})")

            resp = stub.AnalyzeWoundImage(
                medical_ai_pb2.AnalyzeWoundImageRequest(
                    session_id=session_id,
                    image_data=fake_image_base64,
                    description="测试伤口图片"
                ),
                timeout=10
            )

            print()
            print("--- AnalyzeWoundImage 响应 ---")
            print(f"image_valid: {resp.image_valid}")
            print(f"invalid_reason: '{resp.invalid_reason}'")

            if not resp.image_valid and resp.invalid_reason == "":
                print_result("BUG-4: invalid_reason 为空", True, "确认问题存在 - invalid_reason 为空字符串")
                channel.close()
                return True
            else:
                print_result("BUG-4: invalid_reason 为空", False, f"问题已修复 - invalid_reason: '{resp.invalid_reason}'")
                channel.close()
                return False

        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_bug5_process_patient_answers_error_imprecise(self):
        print_header("BUG-5: ProcessPatientAnswers 错误信息不精确")
        print("=" * 70)
        print("测试目标: 验证 ProcessPatientAnswers 的错误信息是否精确")
        print("预期问题: 未先调用 AnalyzeWoundImage 时，返回'会话不存在'而非'缺少图片分析上下文'")
        print()

        try:
            channel = create_insecure_channel()
            stub = medical_ai_pb2_grpc.PostSurgeryFollowupServiceStub(channel)

            session_resp = stub.CreateSession(
                medical_ai_pb2.CreateSessionRequest(
                    patient_id="test_patient_001",
                    patient_name="测试患者",
                    surgery_date="2026-04-01"
                ),
                timeout=30
            )
            session_id = session_resp.session_id
            print(f"创建的会话ID (未进行图片分析): {session_id}")

            resp = stub.ProcessPatientAnswers(
                medical_ai_pb2.ProcessPatientAnswersRequest(
                    session_id=session_id,
                    answers={
                        "q1": "疼痛",
                        "q2": "37.5度"
                    }
                ),
                timeout=10
            )

            print()
            print("--- ProcessPatientAnswers 响应 ---")
            print(f"status: {resp.status}")
            print(f"message: '{resp.message}'")

            is_imprecise = "不存在" in resp.message or "过期" in resp.message
            print_result(
                "BUG-5: ProcessPatientAnswers 错误信息不精确",
                is_imprecise,
                f"当前信息: '{resp.message}'" if is_imprecise else "错误信息已精确化"
            )

            channel.close()
            return is_imprecise

        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_symptom_recognition_rate(self):
        print_header("病症识别率测试")
        print("=" * 70)
        print("测试目标: 验证 AI 对患者描述中病症信息的识别能力")
        print("评估标准: 识别率目标 ≥80%")
        print()

        try:
            channel = create_insecure_channel()
            stub = medical_ai_pb2_grpc.PostSurgeryFollowupServiceStub(channel)

            test_cases = [
                {
                    "input": "伤口有点疼，低烧37.5度，有点恶心",
                    "expected_symptoms": ["疼痛", "低热", "恶心"],
                    "keywords": ["疼", "37.5", "恶心", "发烧", "热"]
                },
                {
                    "input": "术后5天，伤口发炎红肿，有脓性分泌物",
                    "expected_symptoms": ["发炎", "红肿", "脓性分泌物"],
                    "keywords": ["发炎", "红肿", "脓", "感染"]
                },
                {
                    "input": "食欲不好，有点乏力",
                    "expected_symptoms": ["食欲减退", "乏力"],
                    "keywords": ["食欲", "不好", "乏力", "累"]
                }
            ]

            recognized_count = 0
            total_keywords = 0
            recognized_keywords = 0

            for i, case in enumerate(test_cases):
                print(f"--- 测试用例 {i+1}: {case['input'][:30]}... ---")

                session_resp = stub.CreateSession(
                    medical_ai_pb2.CreateSessionRequest(
                        patient_id=f"test_patient_{i}",
                        patient_name="测试患者",
                        surgery_date="2026-04-01"
                    ),
                    timeout=30
                )
                session_id = session_resp.session_id

                responses = []
                for resp in stub.Chat(iter([
                    medical_ai_pb2.ChatRequest(session_id=session_id, message=case["input"], is_end=False),
                    medical_ai_pb2.ChatRequest(session_id=session_id, message="结束了", is_end=True)
                ]), timeout=60):
                    responses.append(resp)

                full_response = "".join([r.content for r in responses])
                print(f"AI回复 (前200字): {full_response[:200]}...")

                for keyword in case["keywords"]:
                    if keyword in full_response:
                        recognized_keywords += 1
                    total_keywords += 1

                print()

            recognition_rate = (recognized_keywords / total_keywords * 100) if total_keywords > 0 else 0
            print(f"--- 病症识别统计 ---")
            print(f"识别的关键词数: {recognized_keywords}/{total_keywords}")
            print(f"识别率: {recognition_rate:.1f}%")

            is_low = recognition_rate < 80
            print_result(
                "病症识别率测试",
                is_low,
                f"识别率 {recognition_rate:.1f}% (目标≥80%)" if is_low else f"识别率 {recognition_rate:.1f}% 已达标"
            )

            channel.close()
            return is_low

        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_health_advice_quality(self):
        print_header("健康建议质量测试")
        print("=" * 70)
        print("测试目标: 验证 AI 健康建议的专业性和完整性")
        print("评估标准: 关键词覆盖率目标≥60%")
        print()

        try:
            channel = create_insecure_channel()
            stub = medical_ai_pb2_grpc.PostSurgeryFollowupServiceStub(channel)

            test_scenarios = [
                {
                    "case": "高风险 - 伤口发炎红肿有脓",
                    "input": "我的阑尾手术伤口发炎了，红肿还有脓",
                    "expected_keywords": ["就医", "感染", "医院", "医生", "抗生素", "换药", "清理"]
                },
                {
                    "case": "中风险 - 伤口渗血",
                    "input": "伤口有少量渗血",
                    "expected_keywords": ["观察", "换药", "清洁", "就医", "压迫"]
                },
                {
                    "case": "低风险 - 饮食咨询",
                    "input": "术后吃什么恢复快？",
                    "expected_keywords": ["清淡", "易消化", "蛋白质", "蔬菜", "水果", "避免", "恢复"]
                }
            ]

            total_keywords = 0
            covered_keywords = 0

            for i, scenario in enumerate(test_scenarios):
                print(f"--- 场景 {i+1}: {scenario['case']} ---")

                session_resp = stub.CreateSession(
                    medical_ai_pb2.CreateSessionRequest(
                        patient_id=f"test_patient_{i}",
                        patient_name="测试患者",
                        surgery_date="2026-04-01"
                    ),
                    timeout=30
                )
                session_id = session_resp.session_id

                responses = []
                for resp in stub.Chat(iter([
                    medical_ai_pb2.ChatRequest(session_id=session_id, message=scenario["input"], is_end=False),
                    medical_ai_pb2.ChatRequest(session_id=session_id, message="谢谢", is_end=True)
                ]), timeout=60):
                    responses.append(resp)

                full_response = "".join([r.content for r in responses])
                print(f"AI回复 (前150字): {full_response[:150]}...")

                for keyword in scenario["expected_keywords"]:
                    if keyword in full_response:
                        covered_keywords += 1
                        print(f"  ✅ 包含关键词: {keyword}")
                    else:
                        print(f"  ❌ 缺失关键词: {keyword}")
                    total_keywords += 1

                print()

            coverage_rate = (covered_keywords / total_keywords * 100) if total_keywords > 0 else 0
            print(f"--- 健康建议质量统计 ---")
            print(f"覆盖的关键词数: {covered_keywords}/{total_keywords}")
            print(f"覆盖率: {coverage_rate:.1f}%")

            is_low = coverage_rate < 60
            print_result(
                "健康建议质量测试",
                is_low,
                f"覆盖率 {coverage_rate:.1f}% (目标≥60%)" if is_low else f"覆盖率 {coverage_rate:.1f}% 已达标"
            )

            channel.close()
            return is_low

        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_medical_record_structuring(self):
        print_header("病历结构化生成测试")
        print("=" * 70)
        print("测试目标: 验证 EndSession 生成的病历结构化程度")
        print("评估标准: 字段完整性目标≥80%")
        print()

        try:
            channel = create_insecure_channel()
            stub = medical_ai_pb2_grpc.PostSurgeryFollowupServiceStub(channel)

            print("创建测试会话并完成对话...")
            session_resp = stub.CreateSession(
                medical_ai_pb2.CreateSessionRequest(
                    patient_id="struct_test_001",
                    patient_name="结构化测试患者",
                    surgery_date="2026-04-01"
                ),
                timeout=30
            )
            session_id = session_resp.session_id

            print("进行多轮对话...")
            responses = []
            for resp in stub.Chat(iter([
                medical_ai_pb2.ChatRequest(session_id=session_id, message="我做了阑尾切除手术3天了", is_end=False),
                medical_ai_pb2.ChatRequest(session_id=session_id, message="伤口周围有点红肿", is_end=False),
                medical_ai_pb2.ChatRequest(session_id=session_id, message="体温37.8度", is_end=False),
                medical_ai_pb2.ChatRequest(session_id=session_id, message="没有过敏史", is_end=False),
                medical_ai_pb2.ChatRequest(session_id=session_id, message="以前有高血压", is_end=False),
                medical_ai_pb2.ChatRequest(session_id=session_id, message="现在吃降压药", is_end=False),
                medical_ai_pb2.ChatRequest(session_id=session_id, message="好了，就这样", is_end=True)
            ]), timeout=120):
                responses.append(resp)

            print("等待病历生成...")
            time.sleep(5)

            end_resp = stub.EndSession(
                medical_ai_pb2.EndSessionRequest(session_id=session_id),
                timeout=30
            )

            report = end_resp.report
            print()
            print("--- 病历结构化字段检查 ---")

            required_fields = {
                "patient.name": report.patient.name,
                "patient.gender": report.patient.gender,
                "patient.age": report.patient.age,
                "patient.surgery_type": report.patient.surgery_type,
                "chief_complaint": report.chief_complaint,
                "present_illness": report.present_illness,
                "surgery_status.wound_healing": report.surgery_status.wound_healing,
                "surgery_status.temperature": report.surgery_status.temperature,
                "past_history.allergy": report.past_history.allergy,
                "past_history.chronic_disease": report.past_history.chronic_disease,
                "ai_analysis.health_advice": report.ai_analysis.health_advice,
                "ai_analysis.alert_flag": report.ai_analysis.alert_flag,
                "doctor_advice.rest_advice": report.doctor_advice.rest_advice,
            }

            filled_count = 0
            empty_fields = []

            for field_name, field_value in required_fields.items():
                is_filled = field_value != "" and field_value != 0
                status = "✅" if is_filled else "❌"
                print(f"{status} {field_name}: '{field_value}'" if field_value != "" else f"{status} {field_name}: (空)")
                if is_filled:
                    filled_count += 1
                else:
                    empty_fields.append(field_name)

            completeness_rate = (filled_count / len(required_fields)) * 100
            print()
            print(f"--- 病历结构化完整性统计 ---")
            print(f"填充字段数: {filled_count}/{len(required_fields)}")
            print(f"完整性: {completeness_rate:.1f}%")

            is_incomplete = completeness_rate < 80
            if empty_fields:
                print(f"空字段列表: {', '.join(empty_fields)}")

            print_result(
                "病历结构化生成测试",
                is_incomplete,
                f"完整性 {completeness_rate:.1f}% (目标≥80%)" if is_incomplete else f"完整性 {completeness_rate:.1f}% 已达标"
            )

            channel.close()
            return is_incomplete

        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_all_tests(self):
        print("\n")
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 20 + "AI服务问题复现测试" + " " * 28 + "║")
        print("║" + " " * 15 + "基于两份测试报告的已知问题验证" + " " * 17 + "║")
        print("╚" + "═" * 68 + "╝")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"AI服务地址: {AI_SERVICE_HOST}:{AI_SERVICE_PORT}")

        if not self.setup():
            print("❌ 连接AI服务失败，请确保服务正在运行")
            return

        results = {}

        results["BUG-1"] = self.test_bug1_end_session_empty_fields()
        results["BUG-2"] = self.test_bug2_chat_invalid_session_silent()
        results["BUG-3"] = self.test_bug3_create_session_no_validation()
        results["BUG-4"] = self.test_bug4_analyze_wound_invalid_reason_empty()
        results["BUG-5"] = self.test_bug5_process_patient_answers_error_imprecise()
        results["SYMPTOM"] = self.test_symptom_recognition_rate()
        results["ADVICE"] = self.test_health_advice_quality()
        results["STRUCT"] = self.test_medical_record_structuring()

        self.teardown()

        print("\n")
        print("=" * 70)
        print("  测试结果汇总")
        print("=" * 70)

        bugs_confirmed = 0
        bugs_fixed = 0

        for test_name, is_bug_present in results.items():
            status = "❌ 问题仍存在" if is_bug_present else "✅ 已修复"
            print(f"  {test_name}: {status}")
            if is_bug_present:
                bugs_confirmed += 1
            else:
                bugs_fixed += 1

        print()
        print(f"共测试 {len(results)} 项:")
        print(f"  - 确认问题仍存在: {bugs_confirmed} 项")
        print(f"  - 问题已修复: {bugs_fixed} 项")
        print()

        return results


def main():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    tester = IssueReproductionTests()
    results = tester.run_all_tests()

    print("\n测试完成!")
    return 0 if all(not v for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
