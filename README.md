# 🛠️ Inventory BI System

## 📌 Overview
This project is a desktop-based inventory management and business intelligence system designed to track, manage, and analyze supply data in real time. It provides a user-friendly interface combined with backend APIs to support inventory operations and reporting.

---

## 🚀 Features
- Real-time inventory tracking  
- Search and filtering functionality  
- Add and subtract inventory quantities  
- Transaction history tracking  
- CSV and PDF report generation  
- Role-based access (admin, clerk, viewer)  
- Excel data import functionality  

---

## 🧰 Technologies Used
- **Python**
- **FastAPI** (Backend API)
- **PySide6 (Qt)** (Desktop UI)
- **SQLAlchemy** (Database ORM)
- **pandas** (Data processing)
- **ReportLab** (PDF generation)

---

## 📊 Key Highlights
- Built RESTful APIs for managing inventory data and transactions  
- Designed a desktop UI with real-time search and filtering  
- Processed and managed structured inventory datasets using pandas  
- Implemented role-based access control for system users  
- Developed reporting features for analytics and decision-making  

---

## ▶️ How to Run

### Backend
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

### Desktop
cd desktop
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
