# Optimized installation with checks for existing packages
import subprocess
import sys
import os

def check_command_exists(cmd):
    """Check if a command exists in the system"""
    try:
        subprocess.run([cmd, '--version'], capture_output=True, check=False)
        return True
    except FileNotFoundError:
        return False

def check_python_package(package):
    """Check if a Python package is installed"""
    try:
        __import__(package.split('==')[0].replace('-', '_'))
        return True
    except ImportError:
        return False

def check_path_exists(path):
    """Check if a path exists"""
    return os.path.exists(path)

print("Checking for existing installations...")

# Check and install Ollama only if not present
if not check_command_exists('ollama'):
    print("Installing Ollama...")
    !echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections
    !curl -fsSL https://ollama.ai/install.sh | sudo sh
else:
    print("✓ Ollama already installed, skipping...")

# Check CUDA toolkit before installing
cuda_needed = False
if not check_path_exists('/usr/local/cuda'):
    print("CUDA not found, will install...")
    cuda_needed = True
else:
    print("✓ CUDA already present, skipping...")

# Install system dependencies only if needed
if cuda_needed:
    print("Installing CUDA and GPU drivers...")
    !echo "keyboard-configuration keyboard-configuration/layoutcode string us" | sudo debconf-set-selections
    !echo "keyboard-configuration keyboard-configuration/variantcode string" | sudo debconf-set-selections
    !sudo apt-get update -y
    !sudo DEBIAN_FRONTEND=noninteractive apt-get install -y cuda-drivers ocl-icd-opencl-dev nvidia-cuda-toolkit
else:
    print("✓ GPU drivers already configured")

# Check and install Python packages only if needed
packages_to_install = []
for pkg in ['pyngrok==6.1.0', 'aiohttp', 'nest_asyncio', 'requests']:
    pkg_name = pkg.split('==')[0]
    if not check_python_package(pkg_name):
        packages_to_install.append(pkg)
    else:
        print(f"✓ {pkg_name} already installed")

if packages_to_install:
    print(f"Installing Python packages: {', '.join(packages_to_install)}")
    !pip install -q {' '.join(packages_to_install)}
else:
    print("✓ All Python packages already installed")

# Verify GPU setup
print("\nVerifying GPU setup...")
!nvidia-smi

print("Starting main script...")
import os
import time
import asyncio
import nest_asyncio
import aiohttp
import requests
import subprocess
from pyngrok import ngrok, conf

# Apply nest_asyncio for Jupyter compatibility
nest_asyncio.apply()

# Configure GPU environment - ESSENTIAL FOR GPU ACCELERATION
os.environ['LD_LIBRARY_PATH'] = '/usr/local/cuda/lib64:/usr/lib64-nvidia:/usr/local/nvidia/lib64'
os.environ['CUDA_HOME'] = '/usr/local/cuda'
os.environ['OLLAMA_GPU_LAYERS'] = '100'  # Enable GPU acceleration
os.environ["OLLAMA_SCHED_SPREAD"] = "0,1"
# Ngrok configuration
STATIC_DOMAIN = "You need to set up a free static domain from ngrok"
NGROK_TOKEN = 'This is your main auth token from ngrok'

async def run_process(cmd):
    """Run a command and stream its output"""
    print('>>>', ' '.join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    async def _pipe(stream):
        async for line in stream:
            print(line.decode().rstrip())
    await asyncio.gather(_pipe(proc.stdout), _pipe(proc.stderr))
    return proc

async def wait_for_url(url, timeout=30):
    """Wait for a URL to become available"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            async with aiohttp.ClientSession() as sess:
                resp = await sess.get(url)
                if resp.status < 500:
                    return
        except:
            pass
        await asyncio.sleep(1)
    raise RuntimeError(f"Timeout waiting for {url}")

async def check_model_exists(model_name):
    """Check if an Ollama model is already pulled"""
    try:
        proc = await asyncio.create_subprocess_exec(
            'ollama', 'list',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        model_list = stdout.decode()
        return model_name in model_list
    except:
        return False

async def pull_model_if_needed(model_name):
    """Pull model only if it's not already present"""
    if await check_model_exists(model_name):
        print(f"✓ Model {model_name} already exists, skipping download...")
        return
    print(f"Pulling model {model_name}...")
    await run_process(['ollama', 'pull', model_name])

def setup_ngrok_config():
    """Create ngrok config file for static domain"""
    # Create config directory
    os.makedirs('/root/.config/ngrok', exist_ok=True)
    
    # Create config content
    config_content = f"""authtoken: {NGROK_TOKEN}
version: '2'
tunnels:
  ollama:
    proto: http
    addr: 11434
    domain: {STATIC_DOMAIN}
    host_header: rewrite
"""
    # Write config file
    with open('/root/.config/ngrok/ngrok.yml', 'w') as f:
        f.write(config_content)
    print("ngrok config file created for static domain")

async def start_ngrok():
    """Start ngrok with config file"""
    command = "ngrok start --all"
    print(f"Starting ngrok: {command}")
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    # Print output in real-time
    async def print_output(stream, prefix):
        while True:
            line = await stream.readline()
            if not line:
                break
            print(f"{prefix}: {line.decode().strip()}")
    
    # Monitor output
    asyncio.create_task(print_output(process.stdout, "ngrok stdout"))
    asyncio.create_task(print_output(process.stderr, "ngrok stderr"))
    
    return process

async def get_tunnel_url(timeout=60):
    """Get the tunnel URL from ngrok API"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                tunnels = response.json()['tunnels']
                for t in tunnels:
                    if STATIC_DOMAIN in t['public_url']:
                        print(f"Tunnel verified: {t['public_url']}")
                        return t['public_url']
        except:
            pass
        await asyncio.sleep(2)
    
    print(f"Using static domain URL: https://{STATIC_DOMAIN}")
    return f"https://{STATIC_DOMAIN}"

async def main():
    # Clean up existing processes
    subprocess.run(["pkill", "-f", "ollama"], stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-f", "ngrok"], stderr=subprocess.DEVNULL)
    subprocess.run(["fuser", "-k", "11434/tcp"], stderr=subprocess.DEVNULL)
    print("Cleaned up existing processes")

    # Set up ngrok config for static domain
    setup_ngrok_config()
    
    # Start Ollama server with GPU support
    print("Starting Ollama server with GPU acceleration...")
    serve_task = asyncio.create_task(run_process(['ollama', 'serve']))
    
    # Wait for Ollama API
    await wait_for_url('http://127.0.0.1:11434/v1/models')
    
    # Pull models (GPU-optimized) only if not already present
    print("Checking and pulling GPU-optimized models...")
    await pull_model_if_needed('deepseek-r1:14b')
    await pull_model_if_needed('qwen3-coder:30b')
    
    # Start ngrok with static domain
    ngrok_process = await start_ngrok()
    
    # Get tunnel URL
    public_url = await get_tunnel_url()
    print(f'ngrok URL: {public_url}')   
    print(f"Ready! Use this endpoint: {public_url}/api/chat")
    print("Keep this notebook running to maintain the connection")
    print("GPU acceleration is enabled")

    # Keep both processes running
    await asyncio.gather(
        serve_task,
        ngrok_process.wait()
    )

if __name__ == '__main__':
    asyncio.run(main())
