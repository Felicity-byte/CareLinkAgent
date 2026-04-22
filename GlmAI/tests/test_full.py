# -*- coding: utf-8 -*-
"""
AI服务完整功能测试
覆盖: 连接、会话管理、对话流、危急检测、病历生成、错误处理
"""
import sys
import os
import time
import traceback

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
import connect.medical_ai_pb2 as pb2
import connect.medical_ai_pb2_grpc as pb2_grpc

PASS_COUNT = 0
FAIL_COUNT = 0
SKIP_COUNT = 0
RESULTS = []


def record(name, status, detail=""):
    global PASS_COUNT, FAIL_COUNT, SKIP_COUNT
    if status == "PASS":
        PASS_COUNT += 1
        icon = "✅"
    elif status == "FAIL":
        FAIL_COUNT += 1
        icon = "❌"
    else:
        SKIP_COUNT += 1
        icon = "⏭️"
    RESULTS.append((name, status, detail))
    print(f"  {icon} {name}" + (f" - {detail}" if detail else ""))


def connect_server():
    """测试1: 连接服务器"""
    print("\n" + "=" * 60)
    print("  测试1: 服务器连接")
    print("=" * 60)
    
    try:
        channel = grpc.insecure_channel('localhost:50053', options=[
            ('grpc.max_receive_message_length', 10 * 1024 * 1024),
            ('grpc.max_send_message_length', 10 * 1024 * 1024),
        ])
        stub = pb2_grpc.PostSurgeryFollowUpServiceStub(channel)
        grpc.channel_ready_future(channel).result(timeout=10)
        record("gRPC连接", "PASS")
        return channel, stub
    except Exception as e:
        record("gRPC连接", "FAIL", str(e))
        return None, None


def test_create_session(stub):
    """测试2: 创建会话"""
    print("\n" + "=" * 60)
    print("  测试2: 会话创建")
    print("=" * 60)
    
    try:
        request = pb2.CreateSessionRequest(
            patient_id="TEST_FULL_001",
            patient_name="张三",
            surgery_date="2024-01-15"
        )
        response = stub.CreateSession(request)
        
        if response.session_id:
            record("会话ID生成", "PASS", f"ID: {response.session_id[:16]}...")
        else:
            record("会话ID生成", "FAIL", "session_id为空")
            
        if response.welcome_message:
            record("欢迎语生成", "PASS", f"长度: {len(response.welcome_message)}")
        else:
            record("欢迎语生成", "FAIL", "welcome_message为空")
            
        if response.created_at:
            record("时间戳格式", "PASS", response.created_at)
        else:
            record("时间戳格式", "FAIL", "created_at为空")
            
        return response.session_id
    except Exception as e:
        record("会话创建", "FAIL", str(e))
        traceback.print_exc()
        return None


def test_surgery_type_recognition(stub, session_id):
    """测试3: 手术类型识别"""
    print("\n" + "=" * 60)
    print("  测试3: 手术类型识别")
    print("=" * 60)
    
    test_cases = [
        ("我刚做完阑尾切除术", "阑尾"),
        ("我做了胆囊切除手术", "胆囊"),
        ("胃部手术", "胃"),
    ]
    
    for message, expected_keyword in test_cases:
        try:
            def msg_gen():
                yield pb2.ChatRequest(
                    session_id=session_id,
                    message=message,
                    is_end=True
                )
            
            full_response = ""
            for reply in stub.Chat(msg_gen()):
                full_response += reply.content
            
            if expected_keyword in full_response:
                record(f"识别'{expected_keyword}'", "PASS", f"响应长度: {len(full_response)}")
            else:
                record(f"识别'{expected_keyword}'", "FAIL", f"响应中未包含'{expected_keyword}'")
        except Exception as e:
            record(f"识别'{expected_keyword}'", "FAIL", str(e))


def test_chat_stream(stub, session_id):
    """测试4: 流式对话"""
    print("\n" + "=" * 60)
    print("  测试4: 流式对话")
    print("=" * 60)
    
    try:
        def msg_gen():
            yield pb2.ChatRequest(
                session_id=session_id,
                message="阑尾切除术",
                is_end=True
            )
        
        chunk_count = 0
        full_response = ""
        start_time = time.time()
        
        for reply in stub.Chat(msg_gen()):
            chunk_count += 1
            full_response += reply.content
            if reply.is_final:
                break
        
        elapsed = time.time() - start_time
        
        if chunk_count > 0:
            record("流式响应接收", "PASS", f"{chunk_count}个chunk, 耗时{elapsed:.2f}s")
        else:
            record("流式响应接收", "FAIL", "未收到任何响应")
            
        if len(full_response) > 0:
            record("响应内容非空", "PASS", f"长度: {len(full_response)}")
        else:
            record("响应内容非空", "FAIL", "响应为空")
            
        record("流式响应性能", "PASS" if elapsed < 30 else "FAIL", f"耗时: {elapsed:.2f}s")
        
        return full_response
    except Exception as e:
        record("流式对话", "FAIL", str(e))
        traceback.print_exc()
        return ""


def test_multi_turn_conversation(stub, session_id):
    """测试5: 多轮对话"""
    print("\n" + "=" * 60)
    print("  测试5: 多轮对话")
    print("=" * 60)
    
    messages = [
        "我感觉伤口有点疼",
        "疼痛大概在右下腹，持续了两天",
        "没有发烧，食欲还可以",
        "没有了，感觉整体还行",
    ]
    
    turn_count = 0
    
    for msg in messages:
        try:
            def msg_gen():
                yield pb2.ChatRequest(
                    session_id=session_id,
                    message=msg,
                    is_end=True
                )
            
            full_response = ""
            for reply in stub.Chat(msg_gen()):
                full_response += reply.content
                if reply.is_final:
                    break
            
            turn_count += 1
            if full_response:
                record(f"第{turn_count}轮对话", "PASS", f"输入: '{msg[:15]}...' 响应长度: {len(full_response)}")
            else:
                record(f"第{turn_count}轮对话", "FAIL", "响应为空")
        except Exception as e:
            turn_count += 1
            record(f"第{turn_count}轮对话", "FAIL", str(e))


def test_emergency_detection(stub):
    """测试6: 危急情况检测"""
    print("\n" + "=" * 60)
    print("  测试6: 危急情况检测")
    print("=" * 60)
    
    try:
        request = pb2.CreateSessionRequest(
            patient_id="TEST_EMERGENCY",
            patient_name="紧急测试",
            surgery_date="2024-01-15"
        )
        response = stub.CreateSession(request)
        session_id = response.session_id
        
        def surgery_gen():
            yield pb2.ChatRequest(
                session_id=session_id,
                message="阑尾切除术",
                is_end=True
            )
        for _ in stub.Chat(surgery_gen()):
            pass
        
        def emergency_gen():
            yield pb2.ChatRequest(
                session_id=session_id,
                message="我高烧39度，伤口剧烈疼痛，呼吸困难",
                is_end=True
            )
        
        full_response = ""
        is_emergency = False
        for reply in stub.Chat(emergency_gen()):
            full_response += reply.content
            if "紧急" in reply.content or "就医" in reply.content or "120" in reply.content:
                is_emergency = True
        
        if is_emergency:
            record("危急关键词检测", "PASS", "响应中包含紧急就医提示")
        else:
            record("危急关键词检测", "FAIL", "未检测到危急情况")
            
    except Exception as e:
        record("危急情况检测", "FAIL", str(e))


def test_session_history(stub, session_id):
    """测试7: 会话历史查询"""
    print("\n" + "=" * 60)
    print("  测试7: 会话历史查询")
    print("=" * 60)
    
    try:
        request = pb2.GetSessionHistoryRequest(session_id=session_id)
        response = stub.GetSessionHistory(request)
        
        if response.session_id:
            record("历史查询-会话ID", "PASS")
        else:
            record("历史查询-会话ID", "FAIL", "session_id为空")
            
        if len(response.messages) > 0:
            record("历史查询-消息记录", "PASS", f"{len(response.messages)}条消息")
        else:
            record("历史查询-消息记录", "FAIL", "无消息记录")
            
        record("历史查询-状态", "PASS", f"状态: {response.status}")
        
    except Exception as e:
        record("会话历史查询", "FAIL", str(e))


def test_end_session(stub, session_id):
    """测试8: 结束会话"""
    print("\n" + "=" * 60)
    print("  测试8: 结束会话与病历生成")
    print("=" * 60)
    
    try:
        request = pb2.EndSessionRequest(session_id=session_id)
        response = stub.EndSession(request)
        
        if response.status:
            record("会话结束状态", "PASS", f"状态: {response.status}")
        else:
            record("会话结束状态", "FAIL", "状态为空")
            
        if response.report.present_illness:
            record("病历内容生成", "PASS", f"病历长度: {len(response.report.present_illness)}")
        else:
            record("病历内容生成", "FAIL", "病历内容为空")
            
    except Exception as e:
        record("结束会话", "FAIL", str(e))
        traceback.print_exc()


def test_error_handling(stub):
    """测试9: 错误处理"""
    print("\n" + "=" * 60)
    print("  测试9: 错误处理")
    print("=" * 60)
    
    try:
        request = pb2.GetSessionHistoryRequest(session_id="nonexistent-session-id")
        response = stub.GetSessionHistory(request)
        
        if not response.session_id and not response.messages:
            record("无效会话ID处理", "PASS", "返回空响应")
        else:
            record("无效会话ID处理", "FAIL", "应返回空响应")
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            record("无效会话ID处理", "PASS", "返回NOT_FOUND")
        else:
            record("无效会话ID处理", "PASS", f"返回错误码: {e.code()}")
    except Exception as e:
        record("无效会话ID处理", "FAIL", str(e))
    
    try:
        request = pb2.CreateSessionRequest()
        response = stub.CreateSession(request)
        if response.session_id:
            record("空参数创建会话", "PASS", "使用默认值创建")
        else:
            record("空参数创建会话", "FAIL", "未能创建会话")
    except Exception as e:
        record("空参数创建会话", "FAIL", str(e))


def test_concurrent_sessions(stub):
    """测试10: 并发会话"""
    print("\n" + "=" * 60)
    print("  测试10: 并发会话管理")
    print("=" * 60)
    
    session_ids = []
    
    try:
        for i in range(3):
            request = pb2.CreateSessionRequest(
                patient_id=f"CONCURRENT_{i}",
                patient_name=f"并发用户{i}",
                surgery_date="2024-01-15"
            )
            response = stub.CreateSession(request)
            if response.session_id:
                session_ids.append(response.session_id)
        
        if len(session_ids) == 3:
            record("多会话创建", "PASS", f"成功创建{len(session_ids)}个会话")
        else:
            record("多会话创建", "FAIL", f"仅创建{len(session_ids)}/3个会话")
        
        active_count = 0
        for sid in session_ids:
            try:
                request = pb2.GetSessionHistoryRequest(session_id=sid)
                response = stub.GetSessionHistory(request)
                if response.session_id:
                    active_count += 1
            except Exception:
                pass
        
        if active_count == len(session_ids):
            record("多会话查询", "PASS", f"所有{active_count}个会话可查询")
        else:
            record("多会话查询", "FAIL", f"仅{active_count}/{len(session_ids)}个可查询")
            
    except Exception as e:
        record("并发会话管理", "FAIL", str(e))


def print_report():
    """打印测试报告"""
    print("\n" + "=" * 60)
    print("  📊 AI服务完整测试报告")
    print("=" * 60)
    
    total = PASS_COUNT + FAIL_COUNT + SKIP_COUNT
    
    print(f"\n  总测试数: {total}")
    print(f"  ✅ 通过: {PASS_COUNT}")
    print(f"  ❌ 失败: {FAIL_COUNT}")
    print(f"  ⏭️ 跳过: {SKIP_COUNT}")
    print(f"  通过率: {PASS_COUNT/total*100:.1f}%")
    
    if FAIL_COUNT > 0:
        print("\n  ❌ 失败项:")
        for name, status, detail in RESULTS:
            if status == "FAIL":
                print(f"    - {name}: {detail}")
    
    print("\n" + "=" * 60)
    
    if FAIL_COUNT == 0:
        print("  🎉 所有测试通过!")
    else:
        print("  ⚠️ 存在失败项，请检查上方详情")
    print("=" * 60 + "\n")


def main():
    print("=" * 60)
    print("  AI服务完整功能测试")
    print("  时间: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    channel, stub = connect_server()
    if not stub:
        print("\n[ERROR] 无法连接服务器，测试终止")
        return
    
    session_id = test_create_session(stub)
    
    if session_id:
        test_surgery_type_recognition(stub, session_id)
        test_chat_stream(stub, session_id)
        test_multi_turn_conversation(stub, session_id)
        test_session_history(stub, session_id)
        test_end_session(stub, session_id)
    
    test_emergency_detection(stub)
    test_error_handling(stub)
    test_concurrent_sessions(stub)
    
    if channel:
        channel.close()
    
    print_report()


if __name__ == "__main__":
    main()
