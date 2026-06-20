# Podcast Buddy | AI-Powered News Conversationalist

**Podcast Buddy** is a local-first AI application that transforms real-time news into engaging podcast-style conversations between two virtual hosts. It combines modern web technologies, real-time news retrieval, and machine learning powered summarization to generate informative and natural-sounding discussions.

---

##  Tech Stack

This project leverages a modern and efficient technology stack for local execution and fast performance.

### Backend

* Python 3.10+
* Transformers (Hugging Face)
* ThreadingHTTPServer
* Server-Sent Events (SSE)

### Frontend

* HTML5
* CSS3
* Vanilla JavaScript
* Canvas API for audio visualization

### Data Sources

* SerpAPI (Google News)

### Machine Learning

* DistilBART CNN 12-6
* Extractive summarization fallback system

---

##  Key Features

* Automated news collection from Google News
* AI-powered news summarization
* Dynamic podcast-style conversations
* Dual-host conversation system (Aarav & Meera)
* Customizable topic and language settings
* Real-time audio waveform visualization
* Local-first architecture
* Offline fallback summarization
* Responsive web interface

---

##  Project Structure

```text
podcast-buddy/
│
├── podcast_buddy/
│   ├── static/
│   ├── ai_chat.py
│   ├── cli.py
│   ├── config.py
│   ├── episode.py
│   ├── news.py
│   ├── script.py
│   ├── storage.py
│   ├── summarizer.py
│   └── web.py
│
├── tests/
├── data.json
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

##  Getting Started

### Prerequisites

* Python 3.10 or higher
* SerpAPI account and API key

Get your API key from:

https://serpapi.com/

---

##  Installation

### Clone the Repository

```powershell
git clone https://github.com/Badalsha57/Podcast-Buddy.git
cd Podcast-Buddy
```

### Create and Activate Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

```powershell
pip install -r requirements.txt
```

### Configure Environment Variables

```powershell
Copy-Item .env.example .env
```

Open `.env` and add:

```env
SERPAPI_KEY=your_api_key_here
```

---

##  Run the Application

```powershell
python -m podcast_buddy
```

Or:

```powershell
python -m podcast_buddy.web
```

Then open:

```text
http://localhost:8000
```

---

##  How It Works

1. Fetches real-time news using SerpAPI.
2. Summarizes articles using DistilBART.
3. Generates a structured conversation between two AI hosts.
4. Streams results to the web interface.
5. Displays conversation and audio visualization.

---

##  Privacy

Podcast Buddy is designed with a local-first philosophy.

* News processing occurs locally.
* Summarization runs on your machine.
* No conversation data is stored remotely.
* API usage is limited to news retrieval through SerpAPI.

---

##  Running Tests

```powershell
pytest
```

---

## 📸 Features Preview

* Real-time News Summaries
* AI Podcast Generation
* Dual Host Conversations
* Audio Wave Visualization
* Local Machine Learning Inference

---

##  Contributing

Contributions, issues, and feature requests are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push the branch
5. Open a Pull Request

---

##  License

This project is released under the MIT License.

---

##  Author

**Badal Kumar Sharma**

B.Tech CSE Student
Ajay Binay Institute of Technology, Cuttack, Odisha

GitHub: https://github.com/Badalsha57
