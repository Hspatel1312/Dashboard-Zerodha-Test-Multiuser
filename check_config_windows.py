# check_config_windows.py - Windows Configuration validation script

import os
import sys
import subprocess
import requests
from datetime import datetime

def run_command(command):
    """Run a command and return True if successful"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_environment():
    """Check environment and configuration for Windows"""
    print("🔍 Investment System Configuration Check (Windows)")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version < (3, 8):
        issues.append("Python 3.8+ is required")
    else:
        print("   ✅ Python version is compatible")
    
    # Check pip
    pip_success, pip_out, pip_err = run_command("pip --version")
    if pip_success:
        print(f"📦 Pip: Available")
    else:
        issues.append("pip is not available")
    
    # Check curl (for health checks)
    curl_success, _, _ = run_command("curl --version")
    if curl_success:
        print("🌐 Curl: Available")
    else:
        print("🌐 Curl: Not available (using Python requests instead)")
    
    # Check required directories
    print("\n📁 Directory Structure:")
    required_dirs = ['backend', 'frontend', 'backend\\app', 'frontend']
    for dir_path in required_dirs:
        exists = os.path.exists(dir_path)
        status = "✅" if exists else "❌"
        print(f"   {status} {dir_path}")
        if not exists:
            issues.append(f"Missing directory: {dir_path}")
    
    # Check required files
    print("\n📄 Required Files:")
    required_files = [
        'backend\\app\\main.py',
        'backend\\app\\config.py',
        'backend\\app\\auth.py',
        'backend\\requirements.txt',
        'frontend\\streamlit_app.py',
        'frontend\\requirements.txt'
    ]
    
    for file_path in required_files:
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        print(f"   {status} {file_path}")
        if not exists:
            issues.append(f"Missing file: {file_path}")
    
    # Check environment variables (if .env exists)
    print("\n🔧 Environment Configuration:")
    env_file = 'backend\\.env'
    if os.path.exists(env_file):
        print(f"   ✅ Found .env file")
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            required_vars = [
                'ZERODHA_API_KEY',
                'ZERODHA_API_SECRET', 
                'ZERODHA_USER_ID',
                'ZERODHA_PASSWORD',
                'ZERODHA_TOTP_KEY'
            ]
            
            for var in required_vars:
                if var in env_content and not ('your_' in env_content.split(f'{var}=')[1].split('\n')[0]):
                    print(f"   ✅ {var} is configured")
                else:
                    print(f"   ⚠️ {var} needs configuration")
                    warnings.append(f"Configure {var} in .env file")
                    
        except Exception as e:
            warnings.append(f"Could not read .env file: {e}")
    else:
        print(f"   ⚠️ No .env file found")
        warnings.append("Create .env file from .env.example")
    
    # Check Python packages
    print("\n📦 Python Dependencies:")
    
    # Check backend dependencies
    backend_deps = ['fastapi', 'uvicorn', 'requests', 'pandas', 'kiteconnect']
    for dep in backend_deps:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")
            warnings.append(f"Install {dep}: pip install {dep}")
    
    # Check frontend dependencies
    frontend_deps = ['streamlit', 'plotly', 'requests']
    for dep in frontend_deps:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")
            warnings.append(f"Install {dep}: pip install {dep}")
    
    # Check internet connectivity
    print("\n🌐 Network Connectivity:")
    try:
        response = requests.get('https://httpbin.org/get', timeout=5)
        if response.status_code == 200:
            print("   ✅ Internet connection working")
        else:
            print("   ⚠️ Internet connection issues")
            warnings.append("Internet connectivity problems detected")
    except Exception as e:
        print(f"   ❌ Internet connection failed: {e}")
        issues.append("No internet connection")
    
    # Check CSV data source
    print("\n📊 CSV Data Source:")
    csv_url = "https://raw.githubusercontent.com/Hspatel1312/Stock-scanner/refs/heads/main/data/nifty_smallcap_momentum_scan.csv"
    try:
        response = requests.get(csv_url, timeout=10)
        if response.status_code == 200:
            print("   ✅ CSV data source accessible")
            lines = response.text.split('\n')
            print(f"   📈 CSV contains {len(lines)} lines")
            if len(lines) > 1:
                headers = lines[0].split(',')
                print(f"   📋 Headers: {', '.join(headers[:5])}...")
        else:
            print(f"   ❌ CSV data source returned {response.status_code}")
            issues.append("CSV data source not accessible")
    except Exception as e:
        print(f"   ❌ Cannot access CSV data: {e}")
        issues.append("CSV data source connection failed")
    
    # Check ports availability
    print("\n🔌 Port Availability:")
    
    # Check port 8000 (backend)
    port_8000_success, _, _ = run_command("netstat -an | findstr :8000")
    if port_8000_success:
        print("   ⚠️ Port 8000 is in use (backend port)")
        warnings.append("Port 8000 is busy - close existing backend services")
    else:
        print("   ✅ Port 8000 is available (backend)")
    
    # Check port 8501 (frontend)
    port_8501_success, _, _ = run_command("netstat -an | findstr :8501")
    if port_8501_success:
        print("   ⚠️ Port 8501 is in use (frontend port)")
        warnings.append("Port 8501 is busy - close existing Streamlit services")
    else:
        print("   ✅ Port 8501 is available (frontend)")
    
    # Check if services are running
    print("\n🚀 Running Services:")
    
    # Check backend
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend service running")
            health_data = response.json()
            if health_data.get('services', {}).get('investment_service', False):
                print("   ✅ Investment service initialized")
            else:
                print("   ⚠️ Investment service not initialized")
                warnings.append("Investment service initialization issue")
        else:
            print(f"   ❌ Backend returned {response.status_code}")
            warnings.append("Backend service issues")
    except Exception as e:
        print(f"   ⚠️ Backend not running")
        warnings.append("Backend service not running")
    
    # Check frontend
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print("   ✅ Frontend service running")
        else:
            print(f"   ❌ Frontend returned {response.status_code}")
            warnings.append("Frontend service issues")
    except Exception as e:
        print(f"   ⚠️ Frontend not running")
        warnings.append("Frontend service not running")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Configuration Check Summary")
    print("=" * 60)
    
    if not issues and not warnings:
        print("🎉 Perfect! All checks passed.")
        print("✅ Your Windows system is ready to run!")
        print("\n🚀 Next steps:")
        print("1. Run: startup.bat")
        print("2. Access dashboard at: http://localhost:8501")
    else:
        if issues:
            print(f"❌ {len(issues)} Critical Issues Found:")
            for issue in issues:
                print(f"   • {issue}")
        
        if warnings:
            print(f"⚠️ {len(warnings)} Warnings:")
            for warning in warnings:
                print(f"   • {warning}")
        
        print("\n🔧 Next Steps:")
        if issues:
            print("1. Fix critical issues above")
            print("2. Run this check again: python check_config_windows.py")
        
        if warnings and not issues:
            print("1. Install missing dependencies:")
            print("   cd backend && pip install -r requirements.txt")
            print("   cd frontend && pip install -r requirements.txt")
            print("2. Address warnings for optimal performance")
            print("3. Start the system with: startup.bat")
        
        if not any("service not running" in w for w in warnings):
            print("4. If services aren't running, start with: startup.bat")
    
    print(f"\n⏰ Check completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 Windows Tips:")
    print("• Use 'startup.bat' instead of 'startup.sh'")
    print("• Use backslashes (\\) in file paths")
    print("• Keep command windows open to see logs")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = check_environment()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)