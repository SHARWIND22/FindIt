import sqlite3
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "lostfound.db"


def text_similarity(text1, text2):
    if not text1 or not text2:
        return 0

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5)
    )

    try:
        vectors = vectorizer.fit_transform([text1.lower(), text2.lower()])
        score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
        return score * 100
    except ValueError:
        return 0


def location_similarity(loc1, loc2):
    return SequenceMatcher(
        None,
        loc1.lower().strip(),
        loc2.lower().strip()
    ).ratio() * 100


def calculate_match(lost, found):

    description_score = text_similarity(
        lost["description"],
        found["description"]
    )

    name_score = text_similarity(
        lost["item_name"],
        found["item_name"]
    )

    location_score = location_similarity(
        lost["location"],
        found["location"]
    )

    category_score = (
        100 if lost["category"].lower() == found["category"].lower()
        else 0
    )

    final_score = (
        description_score * 0.45 +
        name_score * 0.25 +
        location_score * 0.20 +
        category_score * 0.10
    )

    reasons = []

    if description_score >= 40:
        reasons.append("Similar item descriptions")

    if name_score >= 40:
        reasons.append("Similar item names")

    if location_score >= 60:
        reasons.append("Similar locations")

    if category_score == 100:
        reasons.append("Same item category")

    return round(final_score, 2), reasons


def find_matches(item_id):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    new_item = conn.execute(
        "SELECT * FROM items WHERE id = ?",
        (item_id,)
    ).fetchone()

    if not new_item:
        conn.close()
        return []

    opposite_type = (
        "found" if new_item["item_type"] == "lost" else "lost"
    )

    opposite_items = conn.execute(
        """
        SELECT * FROM items
        WHERE item_type = ?
        AND status = 'open'
        """,
        (opposite_type,)
    ).fetchall()

    results = []

    for other in opposite_items:

        if new_item["item_type"] == "lost":
            lost, found = new_item, other
        else:
            lost, found = other, new_item

        score, reasons = calculate_match(lost, found)

        if score >= 35:

            explanation = ", ".join(reasons)

            conn.execute(
                """
                INSERT OR IGNORE INTO matches
                (lost_item_id, found_item_id, similarity_score, explanation)
                VALUES (?, ?, ?, ?)
                """,
                (lost["id"], found["id"], score, explanation)
            )

            results.append({
                "lost_id": lost["id"],
                "found_id": found["id"],
                "score": score,
                "explanation": explanation
            })

    conn.commit()
    conn.close()

    return results


if __name__ == "__main__":
    print("AI Matching Engine Ready!")