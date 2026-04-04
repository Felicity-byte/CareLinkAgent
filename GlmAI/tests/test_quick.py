# -*- coding: utf-8 -*-
"""快速测试 - 验证服务器是否正常"""
import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r"D:\Trea\medical systems\CareLinkAgent\GlmAI")

import grpc
import connect.medical_ai_pb2 as pb2
import connect.medical_ai_pb2_grpc as pb2_grpc

print("="*50)
print("  快速测试 - 验证服务器")
print("="*50)

try:
    # 连接服务器
    print("\n[1] 连接服务器...")
    channel = grpc.insecure_channel('localhost:50053')
    stub = pb2_grpc.PostSurgeryFollowUpServiceStub(channel)
    print("  [OK] 连接成功")
    
    # 创建会话
    print("\n[2] 创建会话...")
    request = pb2.CreateSessionRequest(
        patient_id="TEST001",
        patient_name="测试用户",
        surgery_date="2024-01-15"
    )
    response = stub.CreateSession(request)
    print(f"  [OK] 会话ID: {response.session_id[:20]}...")
    print(f"  [OK] 欢迎语: {response.welcome_message[:50]}...")
    
    # 发送消息
    print("\n[3] 发送测试消息...")
    def message_generator():
        yield pb2.ChatRequest(
            session_id=response.session_id,
            message="我刚做完阑尾手术3天",
            is_end=True
        )
    
    reply_count = 0
    for reply in stub.Chat(message_generator()):
        reply_count += 1
        if reply_count == 1:
            print(f"  [OK] 收到响应: {reply.content[:50]}...")
    
    print(f"  [OK] 共收到 {reply_count} 条响应")
    
    print("\n" + "="*50)
    print("  ✅ 服务器工作正常!")
    print("="*50)
    
except Exception as e:
    print(f"\n[ERROR] 测试失败: {e}")
    import traceback
    traceback.print_exc()
