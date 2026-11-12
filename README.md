# 🔍 FindIt – AI-Powered Campus Lost & Found

FindIt is a smart campus Lost and Found management system developed for **Mangalore Institute of Technology & Engineering (MITE)**. It helps students report lost belongings, discover found items, search campus reports, and request the return of their belongings through an organized digital platform.

FindIt uses text-based AI matching to compare lost and found reports and identify possible matches. It also provides a claim-request workflow for ownership verification and a built-in campus guide that helps students understand how to use the platform.

---

## 🚀 Features

### 1. Lost & Found Reporting
- **Report Lost Items:** Students can submit details of belongings they have lost.
- **Report Found Items:** Students can report items they have discovered on campus.
- **Student Details:** Reports can include student name, USN, branch, year, and contact information.
- **Item Details:** Add item name, category, description, location, date, and an image.
- **Image Uploads:** Attach an image to help other students recognize an item.

### 2. AI-Based Item Matching
- Automatically compares new lost and found reports.
- Uses TF-IDF text feature extraction and cosine similarity.
- Considers item description, item name, location, and category.
- Calculates a similarity score to show how closely two reports match.
- Displays potential matches on the AI Matches page.

### 3. Smart Search and Filters
- Search reports by item name, description, location, or USN.
- Filter reports by Lost or Found status.
- Filter reports by item category.
- View recently reported items from the dashboard.

### 4. Item Details
- Open a report to view its complete information.
- Review the item description, category, location, date, and available image.
- Access the claim-request process for an item.

### 5. Claim Request and Ownership Verification
- Students can submit a claim request for an item they believe belongs to them.
- Claim requests collect student details and contact information.
- Students can provide ownership proof and an explanation to support their request.
- Administrators can review submitted claims.
- Administrators can approve or reject claim requests and provide an admin note.
- Approval of a claim request is part of the verification process; the physical handover of an item should be confirmed separately by the administrator.

### 6. Admin Login and Claim Management
- Protected admin login for claim management.
- View submitted claim requests.
- Review claimant details and ownership proof.
- Approve or reject claims.
- Add an administrative note during review.

### 7. Campus Location Selection
- Interactive campus map using Leaflet and OpenStreetMap.
- Students can select a campus location while submitting a report.
- Includes campus locations such as Main Block, PG Block, hostels, gyms, Food Court, Supermarket, Ground, and Basketball Court.
- The selected location is saved with the report to help identify where an item was lost or found.

> **Map note:** Map markers are approximate campus positions and should be verified against the actual campus layout before being used for precise navigation.

### 8. FindIt Guide – Smart Campus Recovery Assistant
- Built-in chatbot available from the dashboard.
- Guides students on reporting lost items and reporting found items.
- Explains how to search reports and view AI matches.
- Explains the claim-request and ownership-verification process.
- Uses predefined, rule-based responses and works without an external AI API key.

> **Assistant note:** FindIt Guide is a rule-based help assistant. It is not a live generative AI chatbot.

### 9. Dashboard and Visual Experience
- Dashboard showing lost, found, and successfully returned item counts.
- Recently reported item cards.
- Animated background and visual effects.
- Responsive layout for different screen sizes.
- Recovery-rate donut graphic currently uses illustrative demo figures and is not a live database statistic.

---

## 🧠 How AI Matching Works

FindIt uses a text-based matching engine to identify possible connections between lost and found reports.

1. A student submits a lost or found item report.
2. The system retrieves existing reports of the opposite type.
3. TF-IDF converts item descriptions into numerical text features.
4. Cosine similarity compares the text descriptions.
5. Additional comparisons evaluate item names, locations, and categories.
6. A weighted similarity score is calculated.
7. Potential matches that meet the matching threshold are stored and displayed on the AI Matches page.

### Matching Weights

| Parameter | Weight |
|---|---:|
| Description Similarity | 45% |
| Item Name Similarity | 25% |
| Location Similarity | 20% |
| Category Match | 10% |

The similarity score is an indication of how closely two reports match. It does not independently prove ownership.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework and application routes |
| SQLite | Database storage |
| Scikit-learn | Text processing and similarity calculations |
| TF-IDF | Text feature extraction |
| Cosine Similarity | Comparing report descriptions |
| HTML | Frontend structure |
| CSS | Styling, responsive layout, and animations |
| JavaScript | Interactive features and FindIt Guide |
| Pillow | Image processing support |
| Leaflet | Interactive campus map |
| OpenStreetMap | Map tile data |

---

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
│   └── (uploaded item images)
│
├── templates/
│   ├── index.html
│   ├── report.html
│   ├── matches.html
│   ├── item_details.html
│   ├── claim_request.html
│   ├── admin_login.html
│   └── admin_claims.html
│
└── static/
    ├── css/
    ├── js/
    └── images/
        ├── mite-logo.png
        └── campus.png
```

The database and upload folders may be created or populated when the application is initialized and used.

---

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd FindIt
```

Replace `YOUR_REPOSITORY_URL` with the URL of your Git repository.

### 2. Create a virtual environment

```bash
python -m venv finditenv
```

### 3. Activate the environment

**Windows PowerShell:**

```powershell
.\finditenv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
finditenv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the admin login

Set environment variables before starting the application.

**Windows PowerShell:**

```powershell
$env:FLASK_SECRET_KEY = "replace-with-a-long-random-secret"
$env:ADMIN_USERNAME = "admin"
$env:ADMIN_PASSWORD = "replace-with-a-strong-password"
```

Use your own strong secret key and admin password. Do not publish real credentials in the repository.

### 6. Run the application

```bash
python app.py
```

### 7. Open FindIt in your browser

```text
http://127.0.0.1:5000
```

---

## 🔐 Admin Access

The administrator can sign in using the credentials configured through environment variables.

Admin access is used to review claim requests and manage the claim-verification process. Keep the admin password and Flask secret key private.

---

## 🎯 Project Objective

The objective of FindIt is to simplify the campus Lost and Found process through an intelligent digital platform. By combining structured item reports, AI-based text matching, campus location selection, and claim verification, FindIt aims to reduce the time and effort required to identify and recover missing belongings.

---

## 🧪 Current Scope and Limitations

- AI matching is based on report text and does not currently perform image-based recognition.
- Similarity scores indicate possible matches and should not be treated as proof of ownership.
- Claim requests require administrator review.
- A claim approval does not itself confirm that the item has been physically handed over.
- FindIt Guide provides predefined rule-based assistance rather than unrestricted generative AI responses.
- Campus map markers are approximate and should be checked against the real campus layout.
- The recovery donut graphic on the dashboard is illustrative demo data, not a live recovery-rate calculation.

---

## 🔮 Future Enhancements

- Image-based item recognition.
- Student authentication.
- More advanced AI-based matching.
- Improved campus map accuracy and location selection.
- Enhanced reporting and analytics for administrators.

---

## 👨‍💻 Developed During

**AI VibeX 1.0 – Hackathon**  
**Mangalore Institute of Technology & Engineering (MITE)**  
Moodbidri, Karnataka, India

---

⭐ If you find this project interesting, consider giving the repository a star!
