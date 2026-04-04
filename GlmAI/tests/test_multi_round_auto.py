# -*- coding: utf-8 -*-
"""
多轮测试脚本 - 10轮完整测试
每轮测试: 启动服务器 -> 运行测试 -> 关闭服务器
"""
import sys
import os
import time
import subprocess
import signal
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 路径配置
GLM_DIR = r"D:\Trea\medical systems\CareLinkAgent\GlmAI"
SERVER_SCRIPT = os.path.join(GLM_DIR, "connect", "server.py")
TEST_SCRIPT = os.path.join(GLM_DIR, "tests", "test_streaming.py")
PORT = 50053

def kill_python_processes():
    """清理所有Python进程"""
    print("\n[清理] 正在清理旧进程...")
    try:
        subprocess.run(
            ['taskkill', '/F', '/IM', 'python.exe'],
            capture_output=True,
            timeout=5
        )
        time.sleep(2)
        print("  [OK] 旧进程已清理")
    except Exception as e:
        print(f"  [INFO] 清理进程: {e}")

def start_server():
    """启动AI服务器"""
    print("\n[启动] 正在启动AI服务器...")
    
    process = subprocess.Popen(
        ['python', SERVER_SCRIPT],
        cwd=GLM_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    # 等待服务器启动完成
    print("  等待服务器启动...")
    max_wait = 30
    start_time = time.time()
    server_ready = False
    
    while time.time() - start_time < max_wait:
        try:
            line = process.stdout.readline()
            if not line:
                time.sleep(0.5)
                continue
            
            # 检测服务器启动成功的标志
            if "AI服务启动成功" in line or "AI鏈嶅姟鍚姩鎴愬姛" in line:
                server_ready = True
                print(f"  [OK] 服务器启动成功! (耗时: {time.time() - start_time:.1f}秒)")
                break
            
            # 检测RAG加载完成
            if "RAG" in line and "加载" in line:
                print(f"  [INFO] {line.strip()}")
                
        except Exception as e:
            print(f"  [ERROR] 读取输出失败: {e}")
            break
    
    if not server_ready:
        print(f"  [ERROR] 服务器启动超时 ({max_wait}秒)")
        process.terminate()
        return None
    
    # 额外等待RAG加载
    print("  等待RAG加载完成...")
    time.sleep(8)
    
    return process

def stop_server(process):
    """停止AI服务器"""
    print("\n[关闭] 正在关闭AI服务器...")
    
    if process:
        try:
            process.terminate()
            process.wait(timeout=5)
            print("  [OK] 服务器已关闭")
        except subprocess.TimeoutExpired:
            process.kill()
            print("  [OK] 服务器已强制关闭")
        except Exception as e:
            print(f"  [ERROR] 关闭服务器失败: {e}")

def run_tests(round_num):
    """运行测试脚本"""
    print(f"\n[测试] 开始执行第 {round_num} 轮测试...")
    print("-" * 70)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ['python', TEST_SCRIPT],
            cwd=GLM_DIR,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=600  # 10分钟超时
        )
        
        duration = time.time() - start_time
        
        # 解析测试结果
        output = result.stdout + result.stderr
        
        # 统计通过/失败数量
        passed = output.count("✅ 通过")
        failed = output.count("❌ 失败")
        total = passed + failed
        
        # 检查是否全部通过
        all_passed = "全部通过" in output or (failed == 0 and total > 0)
        
        print(f"\n[结果] 第 {round_num} 轮测试完成")
        print(f"  通过: {passed}/{total}")
        print(f"  失败: {failed}")
        print(f"  耗时: {duration:.1f}秒")
        print(f"  状态: {'✅ 全部通过' if all_passed else '⚠️ 有失败项'}")
        
        return {
            'round': round_num,
            'passed': passed,
            'failed': failed,
            'total': total,
            'duration': duration,
            'all_passed': all_passed,
            'output': output,
            'time': datetime.now().strftime("%H:%M:%S")
        }
        
    except subprocess.TimeoutExpired:
        print(f"\n[ERROR] 第 {round_num} 轮测试超时")
        return {
            'round': round_num,
            'passed': 0,
            'failed': 0,
            'total': 0,
            'duration': 600,
            'all_passed': False,
            'output': '测试超时',
            'time': datetime.now().strftime("%H:%M:%S")
        }
    except Exception as e:
        print(f"\n[ERROR] 第 {round_num} 轮测试失败: {e}")
        return {
            'round': round_num,
            'passed': 0,
            'failed': 0,
            'total': 0,
            'duration': 0,
            'all_passed': False,
            'output': str(e),
            'time': datetime.now().strftime("%H:%M:%S")
        }

def main():
    """主函数：执行10轮测试"""
    print("="*70)
    print("  AI服务多轮测试 (10轮)")
    print("="*70)
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  测试脚本: {TEST_SCRIPT}")
    print("="*70)
    
    results = []
    start_round = 13  # 从第13轮开始（之前已有12轮）
    
    for i in range(10):
        round_num = start_round + i
        
        print(f"\n{'='*70}")
        print(f"  第 {round_num} 轮测试")
        print("="*70)
        
        # 1. 清理旧进程
        kill_python_processes()
        
        # 2. 启动服务器
        server_process = start_server()
        if not server_process:
            print(f"[ERROR] 第 {round_num} 轮: 服务器启动失败")
            results.append({
                'round': round_num,
                'passed': 0,
                'failed': 0,
                'total': 0,
                'duration': 0,
                'all_passed': False,
                'output': '服务器启动失败',
                'time': datetime.now().strftime("%H:%M:%S")
            })
            continue
        
        # 3. 运行测试
        result = run_tests(round_num)
        results.append(result)
        
        # 4. 关闭服务器
        stop_server(server_process)
        
        # 5. 轮次间隔
        if i < 9:  # 最后一轮不需要等待
            print(f"\n[等待] 5秒后开始下一轮测试...")
            time.sleep(5)
    
    # 打印汇总
    print("\n" + "="*70)
    print("  多轮测试汇总")
    print("="*70)
    
    total_passed = sum(r['passed'] for r in results)
    total_failed = sum(r['failed'] for r in results)
    total_tests = sum(r['total'] for r in results)
    successful_rounds = sum(1 for r in results if r['all_passed'])
    
    print(f"\n{'轮次':<8} {'时间':<10} {'通过':<10} {'失败':<8} {'耗时':<10} {'状态'}")
    print("-" * 70)
    
    for r in results:
        status = "✅ 全部通过" if r['all_passed'] else "⚠️ 有失败"
        print(f"第{r['round']}轮  {r['time']:<10} {r['passed']}/{r['total']:<8} {r['failed']:<8} {r['duration']:.1f}秒    {status}")
    
    print("-" * 70)
    print(f"\n总计: {successful_rounds}/10 轮全部通过")
    print(f"测试项: {total_passed}/{total_tests} 通过")
    if total_failed > 0:
        print(f"失败项: {total_failed}")
    
    print("\n" + "="*70)
    print(f"  测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return results

if __name__ == "__main__":
    results = main()
