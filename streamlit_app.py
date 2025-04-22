
import streamlit as st
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os, json
import pandas as pd

@dataclass
class Plant:
    name: str
    org_type: str
    notes: str = ""
    edible: bool = False
    planted: Optional[str] = None

@dataclass
class Task:
    name: str
    description: str = ""
    assignee: str = ""

@dataclass
class Supply:
    name: str
    quantity: int
    notes: str = ""

@dataclass
class Garden:
    name: str
    location: str
    size: float
    since: str
    owners: List[str]
    plants: Dict[str, Dict] = field(default_factory=dict)
    tasks: Dict[str, Dict] = field(default_factory=dict)
    supplies: Dict[str, Dict] = field(default_factory=dict)

@st.cache_resource
def init_firebase():
    if not os.path.exists("firebase_credentials.json"):
        st.error("Missing Firebase credentials.")
        return None
    try:
        cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase error: {e}")
        return None

def get_gardens(db): return [doc.id for doc in db.collection("gardens").stream()]
def get_garden_data(db, name): return db.collection("gardens").document(name).get().to_dict()
def update_garden_data(db, name, data): db.collection("gardens").document(name).update(data)
def save_garden(db, garden): db.collection("gardens").document(garden.name).set(json.loads(json.dumps(asdict(garden))))
def export_dict_to_csv(data, label): st.download_button("Download CSV", pd.DataFrame(data.values()).to_csv(index=False), f"{label}.csv")

def login_ui():
    with st.sidebar:
        st.title("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login") and email and password:
            try:
                user = auth.get_user_by_email(email)
                st.session_state.logged_in = True
                st.session_state.user = email
            except:
                st.error("Login failed")

def main():
    st.set_page_config(page_title="Garden Helper", page_icon="🌱", layout="wide")
    if not st.session_state.get("logged_in"): login_ui(); return
    st.title(f"🌱 Garden Helper (User: {st.session_state.user})")
    db = init_firebase()
    if not db: return
    page = st.sidebar.radio("Menu", ["Create Garden", "View Gardens"])

    if page == "Create Garden":
        with st.form("form"):
            name = st.text_input("Name")
            location = st.text_input("Location")
            size = st.number_input("Size", min_value=0.1)
            owners = st.text_input("Owners (comma-separated)")
            since = st.date_input("Since").strftime("%Y-%m-%d")
            if st.form_submit_button("Save") and name:
                g = Garden(name, location, size, since, owners.split(","))
                save_garden(db, g)
                st.success("Saved.")

    else:
        gardens = get_gardens(db)
        if not gardens: st.info("No gardens."); return
        selected = st.selectbox("Choose", gardens)
        data = get_garden_data(db, selected)
        st.subheader(f"🌿 {data['name']}")
        st.write(f"{data['location']} | {data['size']} acres | {data['since']} | Owners: {', '.join(data['owners'])}")
        with st.expander("Export"):
            export_dict_to_csv(data.get("plants", {}), "plants")
            export_dict_to_csv(data.get("tasks", {}), "tasks")
            export_dict_to_csv(data.get("supplies", {}), "supplies")

if __name__ == "__main__":
    main()
