# Ollama Server On Kaggle

This project sets up a GPU-accelerated Ollama server on Kaggle with a public ngrok tunnel for remote access to AI models. It is specifically designed to work within Kaggle's notebook environment.

## Features

- **Kaggle-Optimized**: Specifically configured for Kaggle's GPU environment
- **GPU Acceleration**: Automatically configures CUDA and GPU layers for optimal performance
- **Static Domain**: Uses ngrok static domains for consistent URLs
- **Multiple Models**: Pre-configured to pull popular models (DeepSeek and Qwen Coder)
- **Non-interactive Setup**: Fully automated installation process
- **Real-time Monitoring**: Live output streaming from both Ollama and ngrok processes

## Prerequisites

- Kaggle account with GPU-enabled notebook
- ngrok account with auth token
- ngrok static domain (free tier available)

## Setup Instructions

### 1. Create Kaggle Notebook
Create a new Kaggle notebook with GPU enabled in the accelerator settings.

### 2. Configure Environment Variables
Set the following variables in your Kaggle notebook:

```python
STATIC_DOMAIN = "You need to set up a free static domain from ngrok"  # Your ngrok static domain
NGROK_TOKEN = 'This is your main auth token from ngrok'               # Your ngrok authentication token
```

### 3. Run Installation
Execute the main script to automatically install, configure and run the server.

### System Configuration
- Non-interactive debconf settings for automated installation
- Ollama installation using the official installer
- CUDA drivers and NVIDIA toolkit setup
- Python dependencies installation (pyngrok, aiohttp, nest_asyncio, requests)

### Environment Optimization
```bash
os.environ['CUDA_HOME'] = '/usr/local/cuda'
os.environ['OLLAMA_GPU_LAYERS'] = '100'
os.environ["OLLAMA_SCHED_SPREAD"] = "0,1"
```
Configure this to suit your needs and demands

### Model Installation
The script automatically pulls the following GPU-optimized models:
- `deepseek-r1:14b`
- `qwen3-coder:30b`

## Usage

Once running, you can access the Ollama API at:

```
https://[your-static-domain].ngrok-free.app/api/chat
```

The server will remain active as long as the notebook is running.

## API Examples

### Chat Completion
```bash
curl -X POST https://your-domain.ngrok-free.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1:14b",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### Model Listing
```bash
curl https://your-domain.ngrok-free.app/api/tags
```

### Common Issues

1. **GPU not detected**: Verify Kaggle notebook has GPU enabled
2. **Ngrok connection failures**: Check your auth token and static domain configuration
3. **Session timeouts**: Kaggle sessions have time limits

### Logs and Monitoring
- The script outputs real-time logs from both Ollama and ngrok
- Check ngrok dashboard for tunnel status: https://dashboard.ngrok.com/

#### Adding and Removing Models

The setup script includes predefined model configurations that can be easily customized based on your requirements. To modify the models being installed, edit the model pull commands in the script:

```python
# Example model installation commands
await run_process(['ollama', 'pull', 'deepseek-r1:14b'])
await run_process(['ollama', 'pull', 'qwen3-coder:30b'])
```

**To customize your model selection:**

1. **Add models**: Insert additional `await run_process(['ollama', 'pull', 'model-name:tag'])` lines with your desired models
2. **Remove models**: Comment out or delete the model pull commands for models you don't need
3. **Replace models**: Substitute the existing model names with your preferred alternatives


Ensure any models you add are compatible with Ollama and suitable for your hardware capabilities.
Either add or remove each model name of your choice from the script. 

## Support

For issues related to:
- Ollama: https://github.com/ollama/ollama
- Ngrok: https://ngrok.com/docs
- Kaggle: https://www.kaggle.com/docs/notebooks
Here is a short guidelines section for your README.md:

## Guidelines for Use

This setup is intended for personal, non-commercial experimentation and learning within Kaggle's notebook environment. 
Users are responsible for ensuring their usage complies with Kaggle's Terms of Use, including restrictions on content type, resource utilization, and external connectivity. 
Be mindful of session time limits, avoid processing sensitive or regulated data, and regularly review Kaggle's policies for updates. 
This implementation should not be used for competitive activities or commercial purposes.
