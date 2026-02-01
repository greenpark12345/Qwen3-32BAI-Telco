# 5G Network Problem Diagnosis Solver

Automated diagnosis tool based on rule engine and AI assistance.

## 📋 Features

### Core Functions
- **Rule Engine Diagnosis**: Automated diagnosis of standard questions based on expert rules
- **AI-Assisted Analysis**: Intelligent analysis of non-standard questions using Large Language Models
- **Checkpoint Resume**: Support for resuming from interruptions, automatic progress saving
- **Case Matching**: (Optional) Similarity matching based on historical cases

### Supported Question Types
1. **Standard Questions**: Structured questions containing complete Drive Test data
2. **Non-standard Telecom Questions**: Questions containing partial telecom data
3. **Non-telecom Questions**: General network technology questions

### Diagnosis Capabilities
- Weak Coverage Diagnosis
- Overshooting Diagnosis
- Overlap Coverage Diagnosis
- Frequent Handover Diagnosis
- PCI Conflict Diagnosis
- High Speed Diagnosis
- Low RB (Resource Block) Diagnosis
- Neighbor Interference Diagnosis

## 📁 Project Structure

```
5g_solver/
├── run.bat              # Windows startup script
├── run.sh               # Linux/Mac startup script
├── main.py              # Main entry program
├── config.txt           # Configuration file (API keys, etc.)
├── requirements.txt     # Dependencies list
├── README.md            # Documentation
└── src/                 # Source code directory
    ├── config_loader.py     # Configuration loader
    ├── prompts.py           # AI prompt templates
    ├── data_parser.py       # Data parser module
    ├── rule_engine.py       # Rule engine module
    ├── ai_client.py         # AI API client
    ├── case_library.py      # Case library module (optional)
    └── solver.py            # Core solver
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `config.txt` file to set your API key and parameters:

```ini
# API Configuration
OPENROUTER_API_KEY = your-api-key-here
MODEL = qwen/qwen3-32b
API_URL = https://openrouter.ai/api/v1/chat/completions

# Concurrency Configuration
MAX_WORKERS = 8

# Test Data File
TEST_FILE = phase_2_test.csv
```

### 3. Prepare Data Files

Ensure the test data file is in the working directory:
- `phase_2_test.csv` - Test dataset (863 questions)

### 4. Run the Program

```bash
# Method 1: Using startup script (Windows)
Double click run.bat

# Method 2: High command line
python main.py
```

## ⚙️ Configuration

### config.txt Options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| OPENROUTER_API_KEY | OpenRouter API Key | Yes | - |
| MODEL | AI Model to use | No | qwen/qwen3-32b |
| API_URL | API Endpoint URL | No | https://openrouter.ai/api/v1/chat/completions |
| MAX_WORKERS | Number of concurrent threads | No | 8 |
| OUTPUT_DIR | Output directory | No | output |
| TEST_FILE | Test data file path | No | phase_2_test.csv |
| TRAIN_FILE | Training data file (Optional, for case library) | No | - |

## 📊 Output Files

After running, the following files will be generated in `output/` directory:

| File | Description |
|------|-------------|
| submission.csv | Final submission file |
| progress.json | Progress save file (for checkpoint resume) |
| case_cache.json | Case library cache (if used) |
| solve_log.jsonl | Detailed log file |

## 🔧 Requirements

- Python 3.8+
- requests >= 2.25.0

## 📝 Usage Examples

### Basic Usage

```bash
# Run directly
python main.py
```

### Checkpoint Resume

If the program is interrupted, running it again will automatically continue from the last progress:

```bash
# Automatically detects progress.json and resumes
python main.py
```

### Clear Cache and Restart

```bash
# Windows
del output\progress.json

# Linux/Mac
rm output/progress.json
```

## ⚠️ Notes

1. **API Key Security**: Do not commit `config.txt` containing real API keys to public repositories
2. **Network Stability**: AI calls require stable network connection; the program has built-in retry mechanisms
3. **Concurrency Control**: High `MAX_WORKERS` might trigger API rate limits; 8-16 is recommended

## 🐛 F.A.Q

### Q: Missing configuration file error
A: Ensure `config.txt` is in the current working directory or program directory.

### Q: Frequent API call failures
A: Check network connection or reduce `MAX_WORKERS` value.

### Q: How to use case library feature?
A: Add `TRAIN_FILE = train.csv` in `config.txt` and ensure the file exists.

## 📄 License

MIT License

---

*This tool is for learning and competition use only*
