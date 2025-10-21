import os
import pandas as pd
import numpy as np
import streamlit as st
from collections import Counter

st.set_page_config(page_title="EatEase 🍽️", page_icon="🍕", layout="wide")

# -------------------------------------------
# Utility Functions
# -------------------------------------------
def numeric_clean(series):
    s = series.fillna("").astype(str)
    s = (
        s.str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(r"[^0-9.]", "", regex=True)
        .str.strip()
    )
    s = s.replace("", np.nan)
    return pd.to_numeric(s, errors="coerce")

def emoji_thumb(cuisine):
    icons = {
        "biryani": "🍛", "pizza": "🍕", "burger": "🍔", "dessert": "🍰",
        "coffee": "☕", "dosa": "🥞", "chinese": "🥡", "salad": "🥗",
        "shawarma": "🌯", "seafood": "🍤"
    }
    for k, v in icons.items():
        if k in (cuisine or "").lower():
            return v
    return "🍽️"

def ambience_text(r):
    if r >= 4.5: return "Elegant & Calm"
    if r >= 4.0: return "Cozy & Vibrant"
    if r >= 3.5: return "Family Friendly"
    return "Simple Ambience"

def support_text(r):
    if r >= 4.5: return "Excellent service"
    if r >= 4.0: return "Friendly staff"
    if r >= 3.5: return "Average response"
    return "Basic support"

# -------------------------------------------
# Load Data
# -------------------------------------------
@st.cache_data
def load_data():
    path = "swiggy.csv"
    if not os.path.exists(path):
        st.error("⚠️ 'swiggy.csv' not found. Please keep it beside app.py.")
        st.stop()

    chunks = []
    for chunk in pd.read_csv(path, chunksize=10000, dtype=str, low_memory=False, on_bad_lines='skip'):
        chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True)
    df = df.fillna("")

    for c in ["name", "city", "cuisine", "rating", "rating_count", "cost"]:
        if c not in df.columns:
            df[c] = ""

    df["rating"] = numeric_clean(df["rating"]).fillna(3.5)
    df["rating_count"] = numeric_clean(df["rating_count"]).fillna(0).astype(int)
    cnum = numeric_clean(df["cost"])
    df["cost"] = cnum.fillna(cnum.median(skipna=True))

    df["city_clean"] = df["city"].str.lower().str.strip()
    df["cuisine_clean"] = df["cuisine"].str.lower().str.replace(r"\s*,\s*", ",", regex=True)
    df = df[df["name"].str.strip() != ""].drop_duplicates(subset=["name", "city"])
    return df.reset_index(drop=True)

with st.spinner("🍽️ Loading restaurant data..."):
    df = load_data()

# -------------------------------------------
# Session Storage
# -------------------------------------------
if "feedbacks" not in st.session_state:
    st.session_state.feedbacks = [
        {"name": "Arjun", "rating": 5, "comment": "Great app! Found new cafes 🍕"},
        {"name": "Meera", "rating": 4, "comment": "Smooth and clean interface 🥗"},
        {"name": "Rohit", "rating": 5, "comment": "Loved the biryani picks 🍛"},
    ]
if "chat" not in st.session_state:
    st.session_state.chat = []

# -------------------------------------------
# CSS Styling
# -------------------------------------------
BG_URL = "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1600&auto=format&fit=crop"

st.markdown(f"""
<style>
.block-container {{
  padding-top: 0.5rem !important;  /* Moved title slightly down */
  padding-bottom: 0rem !important;
}}
[data-testid="stAppViewContainer"] {{
  background: linear-gradient(rgba(255,255,255,0.94), rgba(255,255,255,0.94)),
              url('{BG_URL}');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  color: #052b36;
  font-weight: 500;
}}
h1, h2, h3, h4, h5, h6, label, p, div {{
  color: #041f29 !important;
}}
.hero {{
  text-align:center;
  margin-top:20px;  /* Added to fix title visibility */
  padding:10px 20px;
}}
.title {{
  font-size:48px;
  font-weight:900;
  color:#012f39;
}}
.subtitle {{
  font-size:18px;
  color:#043744;
  margin-top:-5px;
}}
.food-icons {{
  font-size:38px;
  display:flex;
  justify-content:center;
  gap:12px;
  margin-top:10px;
}}
.card {{
  background:#fff;
  border-radius:12px;
  padding:12px;
  box-shadow:0 6px 15px rgba(0,0,0,0.1);
  margin:10px 0;
}}
.card-small {{
  background:#fff;
  border-radius:10px;
  padding:10px;
  min-width:240px;
  text-align:center;
  color:#043744;
  box-shadow:0 4px 12px rgba(0,0,0,0.1);
}}
.chip {{
  background:#fff;
  border-radius:30px;
  padding:10px 16px;
  margin:5px;
  font-weight:700;
  color:#03363e;
  display:inline-block;
  box-shadow:0 4px 10px rgba(0,0,0,0.08);
}}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------
# Header Section (Centered)
# -------------------------------------------
st.markdown("""
<div class="hero">
  <div class="title">🍽️ EatEase</div>
  <div class="subtitle">Find your next favorite restaurant — simple, fast & fun!</div>
  <div class="food-icons">🍕🍔🥗🍝🍰🍛🍤</div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------
# Filters
# -------------------------------------------
c1, c2, c3, c4 = st.columns([2,3,2,2])
with c1:
    city = st.selectbox("City", ["(Any)"] + sorted(df["city"].unique().tolist()))
with c2:
    cuisines = sorted({c.strip().title() for s in df["cuisine"] for c in s.split(",") if c.strip()})
    selected_cuis = st.multiselect("Cuisines", cuisines)
with c3:
    meal = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])
with c4:
    tz = st.selectbox("Timezone", ["IST (Asia/Kolkata)", "UTC", "Local"])

r1, r2, r3 = st.columns([1.5, 1.5, 2])
with r1:
    min_rating = st.slider("Min Rating", 0.0, 5.0, 3.5, 0.1)
with r2:
    max_cost = st.slider("Max Cost (₹)", 100, 50000, 5000, 100)
with r3:
    search = st.text_input("Search restaurant or dish (optional)")

# -------------------------------------------
# Recommendation logic
# -------------------------------------------
def recommend(df, city, cuisines, min_rating, max_cost, meal, search):
    data = df[(df["rating"] >= min_rating) & (df["cost"] <= max_cost)]
    if city != "(Any)":
        data = data[data["city_clean"] == city.lower()]
    if cuisines:
        data = data[data["cuisine_clean"].apply(lambda s: any(c.lower() in s for c in cuisines))]
    if search:
        q = search.lower()
        data = data[data["name"].str.lower().str.contains(q) | data["cuisine"].str.lower().str.contains(q)]
    return data.sort_values("rating", ascending=False).head(20)

if st.button("🔍 Show Recommendations"):
    recs = recommend(df, city, selected_cuis, min_rating, max_cost, meal, search)
    if recs.empty:
        st.warning("No matches found. Try adjusting filters 🍴")
    else:
        for _, r in recs.iterrows():
            st.markdown(
                f"<div class='card'><b>{emoji_thumb(r['cuisine'])} {r['name']}</b><br>"
                f"{r['city']} • {r['cuisine']}<br>⭐ {r['rating']:.1f} | ₹{int(r['cost'])}<br>"
                f"Ambience: {ambience_text(r['rating'])} • Service: {support_text(r['rating'])}</div>",
                unsafe_allow_html=True
            )

# -------------------------------------------
# Trending + We Think You’ll Love
# -------------------------------------------
st.markdown("<h4 style='text-align:center;'>🔥 Trending Cuisines</h4>", unsafe_allow_html=True)
top_cuis = [c for c, _ in Counter([c.strip().title() for s in df["cuisine"] for c in s.split(",") if c.strip()]).most_common(10)]
st.markdown(''.join(f"<span class='chip'>{c}</span>" for c in top_cuis), unsafe_allow_html=True)

st.markdown("<h4 style='text-align:center;'>💖 We Think You'll Love</h4>", unsafe_allow_html=True)
fav_items = ["Cheesy Margherita Pizza 🍕", "Chicken Dum Biryani 🍛", "Cold Coffee ☕", "Chocolate Brownie 🍫", "Pasta Alfredo 🍝", "French Fries 🍟"]
st.markdown('<div style="display:flex;justify-content:center;flex-wrap:wrap;gap:10px;">' + ''.join(f"<div class='card-small'>{x}</div>" for x in fav_items) + '</div>', unsafe_allow_html=True)

# -------------------------------------------
# Feedback + Chat Beside (with spacing fix)
# -------------------------------------------
colA, spacer, colB = st.columns([1, 0.2, 1])  # Added gap between them
with colA:
    st.markdown("<h4>💬 Customer Feedback</h4>", unsafe_allow_html=True)
    fname = st.text_input("Your name")
    ftext = st.text_area("Your feedback")
    frate = st.slider("Your Rating", 1, 5, 5)
    if st.button("Submit Feedback"):
        st.session_state.feedbacks.append({"name": fname or "Anonymous", "rating": frate, "comment": ftext})
        st.success("Thanks for your feedback 💛")
    for f in st.session_state.feedbacks[-3:]:
        st.markdown(f"<div class='card-small'><b>“{f['comment']}”</b><br>⭐ {f['rating']} — {f['name']}</div>", unsafe_allow_html=True)

with colB:
    st.markdown("<h4>🤖 Ask EatEase</h4>", unsafe_allow_html=True)
    msg = st.text_input("Ask (e.g., Best biryani in Trichy?)")
    if st.button("Send"):
        if msg.strip():
            reply = "Use filters above to explore restaurants!"
            if "biryani" in msg.lower():
                reply = "🍛 Trichy’s best biryani spots are under Lunch/Dinner!"
            elif "coffee" in msg.lower():
                reply = "☕ Try cafes under Breakfast!"
            st.session_state.chat.append(("You", msg))
            st.session_state.chat.append(("EatEase", reply))
            st.rerun()
    for who, text in st.session_state.chat[-4:]:
        st.markdown(f"<div class='card-small'><b>{who}:</b> {text}</div>", unsafe_allow_html=True)

# -------------------------------------------
# Footer
# -------------------------------------------
st.markdown("""
<hr style='border:1px solid #ccc;'>
<p style='text-align:center;color:#012c36;margin-top:5px;font-weight:600;'>
Thanks for visiting <b>EatEase</b> — made with ❤️ by <b>Santhiya</b>
</p>
""", unsafe_allow_html=True)
