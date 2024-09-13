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

1. Clone this repository:

```bash
git clone https://github.com/your-username/ai-sage-content-generator.git
```

2. Navigate to the project directory:

```bash
cd ai-sage-content-generator
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file and set the necessary environment variables:

```
ANTHROPIC_API_KEY=your_api_key_here
NOTION_TOKEN=your_notion_token_here (optional)
NOTION_DATABASE_ID=your_notion_database_id_here (optional)
```

5. Create a `personas.json` file and define AI personas.

## Usage

1. Run the Streamlit app with the following command:

```bash
streamlit run app.py
```

2. Access the local URL displayed in your web browser (usually `http://localhost:8501`).
3. Follow these steps in the web interface:
   - Select AI personas to participate in the conversation from the sidebar.
   - Choose the topic input method (direct input, URL input, or automatic topic selection).
   - Click the "Start Conversation" button to begin the process.
4. Monitor the real-time generated conversation and progress.
5. Once the process is complete, review the generated New York Times style article, metadata, token usage, and costs.

## Precautions

- This project uses Anthropic's API. Be aware that API usage may incur costs.
- Be careful not to include sensitive information in the `personas.json` file.
- To use the Notion integration feature, you need a Notion API token and database ID.

## License

This project is distributed under the MIT License. See the LICENSE file for details.

## Contributing

Bug reports, feature suggestions, and pull requests are always welcome. If you'd like to contribute to the project, please open an issue to start a discussion.
