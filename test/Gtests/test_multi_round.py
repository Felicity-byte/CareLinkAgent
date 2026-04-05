# -*- coding: utf-8 -*-
"""
AI服务多轮启动/关闭测试脚本
每轮测试: 启动服务器 -> 运行测试 -> 关闭服务器
"""
import sys
import os
import time
import subprocess

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GLM_AI_DIR = os.path.dirname(SCRIPT_DIR)
SERVER_SCRIPT = os.path.join(GLM_AI_DIR, 'connect', 'server.py')
TEST_SCRIPT = os.path.join(SCRIPT_DIR, 'test_streaming.py')

sys.path.insert(0, GLM_AI_DIR)
import grpc
import connect.medical_ai_pb2_grpc as medical_ai_grpc


def kill_port_process(port=50053):
    """关闭占用端口的进程"""
    try:
        result = subprocess.run(
            f'Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess',
            shell=True, capture_output=True, text=True
        )
        pids = result.stdout.strip().split('\n')
        killed = []
        for pid in pids:
            pid = pid.strip()
            if pid and pid.isdigit():
                subprocess.run(f'Stop-Process -Id {pid} -Force', shell=True)
                killed.append(pid)
        if killed:
            print(f"  已终止进程: {', '.join(killed)}")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"  清理端口时出错: {e}")
        return False


def check_server_ready(port=50053, timeout=5):
    """检查服务器是否就绪"""
    try:
        channel = grpc.insecure_channel(f'localhost:{port}')
        grpc.channel_ready_future(channel).result(timeout=timeout)
        channel.close()
        return True
    except:
        return False


def start_server():
    """启动AI服务器"""
    print("  正在启动AI服务器...")
    
    kill_port_process()
    
    process = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT],
        cwd=GLM_AI_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    )
    
    print(f"  服务器进程PID: {process.pid}")
    
    for i in range(60):
        time.sleep(1)
        if check_server_ready(timeout=1):
            print(f"  服务器启动成功 (等待{i+1}秒)")
            return process
        
        if process.poll() is not None:
            print(f"  服务器进程意外退出，返回码: {process.returncode}")
            return None
    
    print("  服务器启动超时")
    process.kill()
    return None


def stop_server(process):
    """关闭AI服务器"""
    if process:
        print("  正在关闭AI服务器...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        
    kill_port_process()
    print("  服务器已关闭")


def run_single_test():
    """运行单次测试"""
    print("  正在运行测试...")
    
    try:
        result = subprocess.run(
            [sys.executable, TEST_SCRIPT],
            cwd=GLM_AI_DIR,
            capture_output=True,
            text=True,
            timeout=600,
            encoding='utf-8',
            errors='replace'
        )
        
        output = result.stdout
        error_output = result.stderr
        
        passed = False
        passed_count = 0
        total_count = 21
        issues = []
        
        lines = output.split('\n')
        for line in lines:
            if '总计:' in line and '通过' in line:
                try:
                    parts = line.split('总计:')[1].strip()
                    if '通过' in parts:
                        passed_count = int(parts.split('/')[0].strip())
                        total_str = parts.split('/')[1].split('通过')[0].strip()
                        total_count = int(total_str)
                        passed = passed_count == total_count
                except:
                    pass
            
            if '发现的优化建议' in line:
                for issue_line in lines[lines.index(line)+1:]:
                    if issue_line.strip() and '===' not in issue_line:
                        issues.append(issue_line.strip())
                    else:
                        break
        
        return {
            'passed': passed,
            'passed_count': passed_count,
            'failed_count': total_count - passed_count,
            'total_count': total_count,
            'output': output,
            'error': error_output,
            'issues': issues
        }
        
    except subprocess.TimeoutExpired:
        return {
            'passed': False,
            'passed_count': 0,
            'failed_count': 21,
            'total_count': 21,
            'output': '',
            'error': '测试超时',
            'issues': ['测试执行超时']
        }
    except Exception as e:
        return {
            'passed': False,
            'passed_count': 0,
            'failed_count': 21,
            'total_count': 21,
            'output': '',
            'error': str(e),
            'issues': [f'测试执行异常: {str(e)}']
        }


def run_multi_round_tests(rounds=10, start_round=13):
    """运行多轮测试"""
    results = []
    
    print("="*70)
    print("  AI服务多轮启动/关闭测试")
    print(f"  共 {rounds} 轮测试，从第 {start_round} 轮开始")
    print("="*70)
    
    for i in range(rounds):
        round_num = start_round + i
        print(f"\n{'='*70}")
        print(f"  第 {round_num} 轮测试")
        print("="*70)
        
        round_start = time.time()
        server_process = None
        server_error = None
        test_result = None
        
        try:
            server_process = start_server()
            
            if server_process is None:
                server_error = "服务器启动失败"
                print(f"  [ERROR] {server_error}")
            else:
                time.sleep(2)
                test_result = run_single_test()
        
        except Exception as e:
            server_error = str(e)
            print(f"  [ERROR] 测试过程异常: {e}")
        
        finally:
            stop_server(server_process)
        
        round_duration = time.time() - round_start
        
        round_result = {
            'round': round_num,
            'server_started': server_process is not None,
            'server_error': server_error,
            'test_result': test_result,
            'duration': round_duration
        }
        results.append(round_result)
        
        if test_result:
            status = "✅ 通过" if test_result['passed'] else "❌ 失败"
            print(f"\n  第 {round_num} 轮结果: {status}")
            print(f"  测试通过: {test_result['passed_count']}/{test_result['total_count']}")
            print(f"  耗时: {round_duration:.1f}秒")
            if test_result['issues']:
                print(f"  发现问题: {len(test_result['issues'])} 项")
        else:
            print(f"\n  第 {round_num} 轮结果: ❌ 失败 ({server_error})")
        
        time.sleep(2)
    
    print("\n" + "="*70)
    print("  多轮测试汇总")
    print("="*70)
    
    total_passed = sum(1 for r in results if r['test_result'] and r['test_result']['passed'])
    total_tests = sum(r['test_result']['passed_count'] for r in results if r['test_result'])
    total_possible = sum(r['test_result']['total_count'] for r in results if r['test_result'])
    
    print(f"\n  轮次    服务器启动    测试结果      耗时")
    print("  " + "-"*50)
    for r in results:
        server_status = "✅" if r['server_started'] else "❌"
        if r['test_result']:
            test_status = f"{r['test_result']['passed_count']}/{r['test_result']['total_count']}"
        else:
            test_status = "失败"
        print(f"  第{r['round']:02d}轮   {server_status}           {test_status:<12} {r['duration']:.1f}s")
    
    print("  " + "-"*50)
    print(f"\n  服务器启动成功率: {total_passed}/{len(results)} ({total_passed/len(results)*100:.0f}%)")
    
    if total_possible > 0:
        print(f"  测试总通过率: {total_tests}/{total_possible} ({total_tests/total_possible*100:.1f}%)")
    else:
        print(f"  测试总通过率: 0/0 (0%)")
    
    all_issues = []
    for r in results:
        if r['test_result'] and r['test_result']['issues']:
            all_issues.extend(r['test_result']['issues'])
    
    if all_issues:
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        print("\n  发现的问题汇总:")
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
            print(f"    - {issue} (出现{count}次)")
    
    return results


if __name__ == "__main__":
    results = run_multi_round_tests(rounds=10, start_round=13)
