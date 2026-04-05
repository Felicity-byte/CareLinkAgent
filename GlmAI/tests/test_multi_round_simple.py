# -*- coding: utf-8 -*-
"""
多轮测试脚本 - 10轮完整测试 (简化版)
"""
import sys
import os
import time
import subprocess
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

GLM_DIR = r"D:\Trea\medical systems\CareLinkAgent\GlmAI"
SERVER_SCRIPT = os.path.join(GLM_DIR, "connect", "server.py")
TEST_SCRIPT = os.path.join(GLM_DIR, "tests", "test_streaming.py")

def run_command(cmd, cwd=None, timeout=300):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )
        return result.stdout + result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "命令超时", -1
    except Exception as e:
        return str(e), -1

def kill_python():
    """清理Python进程"""
    print("\n[清理] 正在清理旧进程...")
    run_command("taskkill /F /IM python.exe 2>nul")
    time.sleep(2)
    print("  [OK] 清理完成")

def start_server():
    """启动服务器（后台）"""
    print("\n[启动] 正在启动AI服务器...")
    
    # 使用PowerShell启动后台进程
    ps_cmd = f'''
    $process = Start-Process -FilePath "python" -ArgumentList "{SERVER_SCRIPT}" -WorkingDirectory "{GLM_DIR}" -PassThru -WindowStyle Hidden
    $process.Id
    '''
    
    output, code = run_command(f'powershell -Command "{ps_cmd}"')
    
    if code == 0:
        print("  [OK] 服务器启动命令已执行")
        print("  等待服务器初始化...")
        time.sleep(12)  # 等待服务器启动和RAG加载
        return True
    else:
        print(f"  [ERROR] 启动失败: {output}")
        return False

def stop_server():
    """停止服务器"""
    print("\n[关闭] 正在关闭AI服务器...")
    run_command("taskkill /F /IM python.exe 2>nul")
    time.sleep(2)
    print("  [OK] 服务器已关闭")

def run_tests(round_num):
    """运行测试"""
    print(f"\n[测试] 开始执行第 {round_num} 轮测试...")
    print("-" * 70)
    
    start_time = time.time()
    output, code = run_command(f'python "{TEST_SCRIPT}"', cwd=GLM_DIR, timeout=600)
    duration = time.time() - start_time
    
    # 解析结果
    passed = output.count("✅ 通过") + output.count("通过")
    failed = output.count("❌ 失败") + output.count("失败")
    total = passed + failed if (passed + failed) > 0 else 21
    
    # 检查是否全部通过
    all_passed = "全部通过" in output or (failed == 0 and passed > 0)
    
    print(f"\n[结果] 第 {round_num} 轮测试完成")
    print(f"  通过: {passed}/{total}")
    print(f"  耗时: {duration:.1f}秒")
    print(f"  状态: {'✅ 全部通过' if all_passed else '⚠️ 有失败项'}")
    
    return {
        'round': round_num,
        'passed': passed,
        'failed': failed,
        'total': total,
        'duration': duration,
        'all_passed': all_passed,
        'time': datetime.now().strftime("%H:%M:%S")
    }

def main():
    """主函数"""
    print("="*70)
    print("  AI服务多轮测试 (10轮)")
    print("="*70)
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = []
    start_round = 13
    
    for i in range(10):
        round_num = start_round + i
        
        print(f"\n{'='*70}")
        print(f"  第 {round_num} 轮测试")
        print("="*70)
        
        # 1. 清理
        kill_python()
        
        # 2. 启动服务器
        if not start_server():
            results.append({
                'round': round_num,
                'passed': 0,
                'failed': 0,
                'total': 21,
                'duration': 0,
                'all_passed': False,
                'time': datetime.now().strftime("%H:%M:%S")
            })
            continue
        
        # 3. 运行测试
        result = run_tests(round_num)
        results.append(result)
        
        # 4. 关闭服务器
        stop_server()
        
        # 5. 间隔
        if i < 9:
            print(f"\n[等待] 5秒后开始下一轮...")
            time.sleep(5)
    
    # 汇总
    print("\n" + "="*70)
    print("  多轮测试汇总")
    print("="*70)
    
    successful_rounds = sum(1 for r in results if r['all_passed'])
    total_passed = sum(r['passed'] for r in results)
    total_tests = sum(r['total'] for r in results)
    
    print(f"\n{'轮次':<8} {'时间':<10} {'通过':<10} {'耗时':<10} {'状态'}")
    print("-" * 60)
    
    for r in results:
        status = "✅ 全部通过" if r['all_passed'] else "⚠️ 有失败"
        print(f"第{r['round']}轮  {r['time']:<10} {r['passed']}/{r['total']:<8} {r['duration']:.1f}秒    {status}")
    
    print("-" * 60)
    print(f"\n总计: {successful_rounds}/10 轮全部通过")
    print(f"测试项: {total_passed}/{total_tests} 通过")
    
    print("\n" + "="*70)
    print(f"  测试完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

if __name__ == "__main__":
    main()
