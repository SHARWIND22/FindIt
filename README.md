# 🔍 FindIt – AI-Powered Campus Lost & Found

FindIt is an intelligent campus Lost and Found management system that helps students report lost belongings, discover found items, and recover their possessions using AI-powered matching.

Instead of manually searching through reports, FindIt automatically compares lost and found item descriptions to identify potential matches.

## 🚀 Features

- **Report Lost Items:** Students can report belongings they have lost.
- **Report Found Items:** Students can report items they have discovered.
- **AI-Based Matching:** Uses TF-IDF and text similarity to identify potential matches.
- **Similarity Score:** Displays a percentage indicating how closely two reports match.
- **Smart Search:** Search items by name, description, or location.
- **Category Filters:** Filter items by category and Lost/Found status.
- **Image Uploads:** Attach images to item reports.
- **Return Tracking:** Mark matched items as successfully returned.
- **Dashboard:** View lost, found, and returned item statistics.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| SQLite | Database |
| Scikit-learn | AI text similarity |
| TF-IDF | Text feature extraction |
| HTML | Frontend structure |
| CSS | Frontend styling |
| JavaScript | Browser-side functionality |

## 🧠 How AI Matching Works

FindIt uses a text-based matching engine.

1. A student submits a lost or found item report.
2. The system retrieves existing reports of the opposite type.
3. TF-IDF converts item descriptions into numerical text features.
4. Cosine similarity compares descriptions.
5. Additional comparisons evaluate item names, locations, and categories.
6. A weighted similarity score is calculated.
7. Potential matches are stored and displayed on the AI Matches dashboard.

### Matching Weights

| Parameter | Weight |
|---|---:|
| Description Similarity | 45% |
| Item Name Similarity | 25% |
| Location Similarity | 20% |
| Category Match | 10% |

## 📂 Project Structure

```text
FindIt/
│
├── app.py
├── database.py
├── matching.py
├── requirements.txt
│
├── database/
│   └── lostfound.db
│
├── uploads/
│
├── templates/
│   ├── index.html
│   ├── report.html
│   └── matches.html
│
└── static/
    ├── css/
    ├── js/
    └── images/
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd FindIt
```

### 2. Create a virtual environment

```bash
python -m venv finditenv
```

### 3. Activate the environment

Windows:

```powershell
finditenv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python app.py
```

### 6. Open in browser

```text
http://127.0.0.1:5000
```

## 🎯 Project Objective

To simplify the campus Lost and Found process through an intelligent digital platform that reduces the effort required to identify and recover missing belongings.

## 🔮 Future Enhancements

- Image-based item recognition.
- Student authentication.
- Email notifications for potential matches.
- Real-time notifications.
- Advanced AI matching.
- Administrative dashboard.

## 👨‍💻 Developed During

**AI VibeX 1.0 – Hackathon**

Mangalore Institute of Technology & Engineering (MITE)

---

⭐ If you find this project interesting, consider giving the repository a star!