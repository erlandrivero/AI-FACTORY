# 🏭 AI Factory

AI Factory is a simple Python web application built with [Streamlit](https://streamlit.io/) to serve as a foundation for future AI-powered tools and agents using `crewai`, `crewai-tools`, and `openai`.

---

## 🚀 Getting Started

Follow these steps to set up and run the project on your local machine.

### 1. Clone or Download the Repository
```bash
git clone https://github.com/your-username/ai-factory.git
cd ai-factory
```

*(If you haven’t created a repository yet, you can skip this step and just work in the folder.)*

---

### 2. Create and Activate a Virtual Environment
It's best practice to use a virtual environment to keep your dependencies isolated.

```bash
# Create virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# Activate it (macOS/Linux)
source .venv/bin/activate
```

---

### 3. Install Dependencies
Install the required Python packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

### 4. Run the Streamlit App
```bash
streamlit run app.py
```

After running the above command, you’ll see a URL (e.g. `http://localhost:8501`).  
Open it in your browser to view the app.

---

## 🧰 Project Structure
```
ai-factory/
│
├── app.py               # Main Streamlit app
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignored files
├── README.md            # Project setup guide
└── .venv/               # Virtual environment (not committed to Git)
```

---

## 🔐 Environment Variables (Optional)
If you plan to use the OpenAI API or CrewAI, create a `.env` file in the project root with your keys:
```
OPENAI_API_KEY=your_api_key_here
```

*⚠️ Note: This file is ignored by Git for security.*

---

## 🧭 Next Steps
- Add more Streamlit pages or components.
- Integrate `crewai` and `openai` for AI-powered agents.
- Deploy to [Streamlit Cloud](https://streamlit.io/cloud) or another hosting service.

---

## 📜 License
This project is licensed under the MIT License. You are free to use and modify it.

---

👨‍💻 **Author:** Your Name  
🌐 [https://github.com/your-username](https://github.com/your-username)
