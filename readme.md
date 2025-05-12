# Resume Screener Backend

A powerful AI-driven resume screening service that processes resumes, extracts key information, and matches candidates to job descriptions using NLP and ML.

## 🚀 Features

- **Resume Parsing:** Extract key information from PDF resumes
- **Job Description Matching:** NLP-powered candidate ranking
- **API-Driven:** RESTful endpoints for seamless integration
- **Scalable:** High-performance architecture
- **ATS-Friendly:** Optimized for ATS standards

## 🛠️ Tech Stack

- **Language:** Python 3.8+
- **Framework:** FastAPI/Flask
- **Libraries:**
    - **NLP:** spaCy, NLTK, Hugging Face Transformers
    - **ML:** scikit-learn, TensorFlow
    - **PDF:** PyPDF2, pdfplumber
- **Database:** PostgreSQL/SQLite

## 📋 Prerequisites

- Python 3.8+
- pip
- virtualenv
- Docker (optional)
- Database system (optional)

## 🚀 Quick Start

1. **Clone the repo:**
```bash
git clone https://github.com/RohanKP1/resume-screener-backend.git
cd resume-screener-backend
```

2. **Set up environment:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure .env:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/resume_screener
OPENAI_API_KEY=your_openai_api_key
PORT=8000
```

4. **Run the app:**
```bash
python main.py
```

## 📁 Project Structure

```
resume-screener-backend/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── .env                # Configuration
├── /src/               # Source code
└── README.md           # Documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - See LICENSE file

## 📧 Contact

Issues: [GitHub Issues](https://github.com/RohanKP1/resume-screener-backend/issues)
Email: rohankp5922@gmail.com
