# AI Sage Content Generator

The AI Sage Content Generator is a Streamlit-based web application that generates conversations on given topics using various AI personas and then creates articles in a desired style (e.g., New York Times style) based on these conversations.

![image](https://github.com/user-attachments/assets/28e1a48d-ea2d-4bb0-9d59-60506e029b1a)

## Features

- Selection of AI personas and topic input through a web interface
- Generation of conversations between various AI personas (philosophers, scientists, ethicists, etc.)
- Conversation initiation with user-specified topics, topics extracted from URLs, or automatically selected topics
- Creation of New York Times style articles based on generated conversations
- Real-time visualization of conversation progress and step-by-step processes
- Calculation of token usage and costs
- Optional storage of generated content in a Notion database

## Technology Stack

- **Python**: Main programming language
- **Streamlit**: Framework for developing interactive web applications
- **LangChain**: Framework for developing applications using large language models (LLMs)
- **LangGraph**: Library for implementing graph structures based on LangChain
- **Anthropic Claude**: High-performance conversational AI model
- **Pydantic**: Data validation and settings management
- **Tiktoken**: OpenAI's tokenization library
- **Requests**: HTTP library
- **Beautiful Soup**: Library for web scraping
- **python-dotenv**: Environment variable management
- **Notion Client**: Library for Notion API integration (optional)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Step-by-Step Installation

1. **Clone this repository:**

```bash
git clone https://github.com/your-username/ai-sage-content-generator.git
```

2. **Navigate to the project directory:**

```bash
cd ai-sage-content-generator
```

3. **Create a virtual environment (recommended):**

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

4. **Install the required packages:**

```bash
pip install -r requirements.txt
```

5. **Configure environment variables:**

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API keys
# Required: ANTHROPIC_API_KEY
# Optional: NOTION_TOKEN, NOTION_DATABASE_ID
```

Example `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
NOTION_TOKEN=secret_xxxxx (optional)
NOTION_DATABASE_ID=xxxxx (optional)
```

6. **Verify installation:**

```bash
python test_integration.py
```

This will check that all dependencies are installed and the project is properly configured.

## Usage

### Web Interface (Recommended)

1. **Start the Streamlit web application:**

```bash
streamlit run app.py
```

2. **Open your browser:**
   - The app will automatically open at `http://localhost:8501`
   - Or manually navigate to the URL shown in the terminal

3. **Use the application:**
   - **Select AI Personas:** Choose from the sidebar (Warren Buffett, Elon Musk, Ray Dalio, etc.)
   - **Choose Topic Input Method:**
     - Direct Input: Type your topic
     - URL Input: Paste a URL to extract the topic
     - Auto Topic: Let the system choose
   - **Start Conversation:** Click the button to begin
   - **Monitor Progress:** Watch the real-time conversation and progress bar
   - **Review Results:** See the generated New York Times style article, metadata, token usage, and costs

### Command Line Interface

For a CLI version without the web interface:

```bash
python main.py
```

Follow the prompts to:
1. Select AI personas (comma-separated numbers)
2. Choose topic input method
3. View the conversation in real-time
4. Review the final article and statistics

### Running Tests

**Unit Tests:**
```bash
pytest test_unit.py -v
```

**Integration Tests:**
```bash
python test_integration.py
```

## MVP Features

✅ **Core Functionality**
- Multi-persona AI conversations (10 pre-configured personas)
- 3 topic input methods (direct, URL, auto-select)
- Real-time conversation generation
- New York Times style article generation
- Automatic metadata generation (title, subtitle, description, slug)

✅ **Technical Features**
- Token usage tracking
- Cost calculation (Claude 3.5 Sonnet / Opus)
- Progress monitoring
- Optional Notion integration
- Streamlit web UI
- CLI interface

✅ **Quality Assurance**
- Unit tests for core functions
- Integration tests for system verification
- Error handling and graceful degradation

## Precautions

- **API Costs:** This project uses Anthropic's Claude API. API usage incurs costs based on token consumption.
  - Default limit: 5 messages or $50 per conversation
  - Monitor costs in real-time during generation
- **API Keys:** Never commit your `.env` file to version control. The `.gitignore` is configured to exclude it.
- **Notion Integration:** Optional feature. The system works perfectly without Notion credentials.
- **Network Required:** Internet connection needed for API calls and URL topic extraction.

## Troubleshooting

### Common Issues

**1. Import Errors**
```
ModuleNotFoundError: No module named 'xxx'
```
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

**2. Missing API Key**
```
Error: ANTHROPIC_API_KEY not found
```
**Solution:** Configure your `.env` file
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

**3. Notion Connection Failed**
```
Notion에 저장 중 오류 발생
```
**Solution:** This is normal if Notion is not configured. The system will continue without Notion integration.

**4. Web Scraping Failed**
```
URL에서 주제를 가져오는데 실패했습니다
```
**Solution:** Try a different URL or use direct topic input instead.

### Getting Help

- Check the [Technical Requirements Document (TRD.md)](./TRD.md) for detailed specifications
- Run integration tests: `python test_integration.py`
- Check logs for specific error messages

## License

This project is distributed under the MIT License. See the LICENSE file for details.

## Contributing

Bug reports, feature suggestions, and pull requests are always welcome. If you'd like to contribute to the project, please open an issue to start a discussion.
