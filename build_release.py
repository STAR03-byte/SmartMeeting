#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
FRONTEND_DIR = ROOT / "frontend"
BACKEND_DIR = ROOT / "backend"

def find_npm():
    npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
    if npm_cmd is None:
        raise RuntimeError("未找到 npm，请先安装 Node.js")
    return npm_cmd

def run_command(cmd, cwd=None, check=True):
    print(f"[执行] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"[错误] {result.stderr}")
        raise RuntimeError(f"命令失败: {' '.join(cmd)}")
    if result.stdout:
        print(result.stdout)
    return result

def clean_build():
    print("[步骤 1/5] 清理构建目录...")
    for d in [DIST_DIR, ROOT / "build", FRONTEND_DIR / "dist"]:
        if d.exists():
            shutil.rmtree(d)
            print(f"  已删除 {d}")

def build_frontend():
    print("[步骤 2/5] 构建前端生产版本...")
    npm = find_npm()
    run_command([npm, "install"], cwd=FRONTEND_DIR)
    run_command([npm, "run", "build"], cwd=FRONTEND_DIR)
    
    if not (FRONTEND_DIR / "dist").exists():
        raise RuntimeError("前端构建失败")
    print("  前端构建完成")

def copy_resources():
    print("[步骤 3/5] 复制资源文件...")
    
    dist_backend = DIST_DIR / "backend"
    dist_frontend = DIST_DIR / "frontend"
    dist_backend.mkdir(parents=True, exist_ok=True)
    dist_frontend.mkdir(parents=True, exist_ok=True)
    
    shutil.copytree(FRONTEND_DIR / "dist", dist_frontend / "dist", dirs_exist_ok=True)
    print("  复制前端 dist")
    
    shutil.copytree(BACKEND_DIR / "app", dist_backend / "app", dirs_exist_ok=True)
    print("  复制 backend/app")
    
    for file in ["main.py", "requirements.txt"]:
        src = BACKEND_DIR / file
        if src.exists():
            shutil.copy2(src, dist_backend / file)
            print(f"  复制 {file}")
    
    if (ROOT / "database").exists():
        shutil.copytree(ROOT / "database", DIST_DIR / "database", dirs_exist_ok=True)
        print("  复制 database")
    
    for doc_file in ["README.md", "LICENSE", ".env.example"]:
        src = ROOT / doc_file
        if src.exists():
            shutil.copy2(src, DIST_DIR / doc_file)
            print(f"  复制 {doc_file}")

def create_launcher():
    print("[步骤 4/5] 创建启动脚本...")
    
    launcher_bat = DIST_DIR / "启动 SmartMeeting.bat"
    launcher_bat.write_text("""@echo off
chcp 65001 >nul
echo ==========================================
echo    SmartMeeting 智能会议系统
echo ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
pip install -q -r backend\\requirements.txt

echo [2/3] 启动后端服务...
start "SmartMeeting 后端" python backend\\main.py

timeout /t 3 /nobreak >nul

echo [3/3] 启动前端服务...
start "SmartMeeting 前端" python -m http.server 5173 --directory frontend\\dist

echo.
echo ==========================================
echo  启动成功！
echo  后端地址: http://localhost:8000
echo  前端地址: http://localhost:5173
echo ==========================================
echo.
pause
start http://localhost:5173
""", encoding='utf-8')
    
    launcher_py = DIST_DIR / "launcher.pyw"
    launcher_py.write_text("""#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

DIST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = DIST_DIR / "backend"
FRONTEND_DIR = DIST_DIR / "frontend" / "dist"

def install_deps():
    print("[1/3] 检查依赖...")
    req_file = BACKEND_DIR / "requirements.txt"
    if req_file.exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)], check=False)
    print("  依赖检查完成")

def start_backend():
    print("[2/3] 启动后端...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR,
        env=env,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

def start_frontend():
    print("[3/3] 启动前端...")
    return subprocess.Popen(
        [sys.executable, "-m", "http.server", "5173", "--directory", str(FRONTEND_DIR)],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

def wait_backend():
    print("等待服务就绪...")
    import urllib.request
    for _ in range(20):
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1)
            print("  后端就绪")
            return True
        except:
            time.sleep(0.5)
    print("  后端启动较慢，请稍后再试")
    return False

def main():
    print("=" * 45)
    print("   SmartMeeting 智能会议系统")
    print("=" * 45)
    print()
    
    if sys.version_info < (3, 10):
        print("[错误] 需要 Python 3.10+")
        input("按回车退出...")
        return 1
    
    try:
        install_deps()
        backend_proc = start_backend()
        frontend_proc = start_frontend()
        wait_backend()
        
        print()
        print("=" * 45)
        print("  启动成功！")
        print("  后端: http://127.0.0.1:8000")
        print("  前端: http://localhost:5173")
        print("=" * 45)
        print()
        
        webbrowser.open("http://localhost:5173")
        
        print("按 Ctrl+C 停止服务")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\\n停止服务...")
        backend_proc.terminate()
        frontend_proc.terminate()
    except Exception as e:
        print(f"[错误] {e}")
        input("按回车退出...")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
""", encoding='utf-8')
    
    print("  启动脚本已创建")

def create_archive():
    print("[步骤 5/5] 创建安装包...")
    
    archive_name = "SmartMeeting-v1.0.0"
    archive_path = ROOT / f"{archive_name}.zip"
    
    if archive_path.exists():
        archive_path.unlink()
    
    shutil.make_archive(
        base_name=str(ROOT / archive_name),
        format='zip',
        root_dir=str(DIST_DIR),
        base_dir='.'
    )
    
    size_mb = archive_path.stat().st_size / 1024 / 1024
    print(f"  安装包已创建: {archive_path.name}")
    print(f"  文件大小: {size_mb:.1f} MB")

def main():
    print("=" * 50)
    print("   SmartMeeting 打包工具")
    print("=" * 50)
    print()
    
    try:
        clean_build()
        build_frontend()
        copy_resources()
        create_launcher()
        create_archive()
        
        print()
        print("=" * 50)
        print("   打包完成！")
        print("=" * 50)
        print(f"\\n输出文件: SmartMeeting-v1.0.0.zip")
        print(f"位置: {ROOT}")
        print("\\n使用方法:")
        print("1. 解压 SmartMeeting-v1.0.0.zip")
        print("2. 双击运行 '启动 SmartMeeting.bat' 或 'launcher.pyw'")
        print("3. 浏览器会自动打开应用")
        
    except Exception as e:
        print(f"\\n[错误] 打包失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
