# AI Powered Corporate Agent

## Overview
The AI Powered Corporate Agent is an intelligent automation system designed to handle corporate tasks using AI models and APIs.  
It integrates natural language processing, data retrieval, and business logic to automate workflows such as communication, decision-making, and reporting.

## Project Structure
```
AI_POWERED_CORPORATE_AGENT/
├── app.py                # Main application entry point
├── checklists.py         # Checklist generation and processing
├── classify_docs.py      # Document classification logic
├── comment_doc.py        # Automated document commenting
├── detect_flags.py       # Detects flags or issues in data
├── load_references.py    # Loads and processes reference data
├── templates/            # Templates for various document types
├── templates_texts.json  # Template texts for automation
├── Data Sources.pdf      # Supporting reference documents
├── requirements.txt      # Python dependencies
```

## Installation

1. Clone the repository:
```
git clone https://github.com/2CentsCapitalHR/ai-engineer-task-titir232004.git
cd ai-engineer-task-titir232004
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

## Usage
Run the main application:
```
python app.py
```
The agent will start and be ready to handle corporate tasks based on the configurations provided.

## Configuration
Modify `config.py` to set API keys, model parameters, and operational settings:
```python
API_KEY = "your_api_key_here"
MODEL_NAME = "gpt-4"
LOGGING_ENABLED = True
```

## Features
1. **Natural Language Understanding** – Processes queries and commands.  
2. **Automated Decision-Making** – Uses AI models to recommend or execute actions.  
3. **Task Automation** – Schedules and executes business tasks.  
4. **Extensible Toolset** – Add new modules for different corporate workflows.  
5. **API Integrations** – Connects with business APIs for data access.  

## Requirements
- Python 3.8+  
- Internet connection for API calls  
- Dependencies in `requirements.txt`

## License
This project is licensed under the MIT License. See LICENSE for details.

