import streamlit as st
from candidats import CANDIDATS, CRITERES
import os
from supabase import create_client
from datetime import datetime

# ─────────────────────────────────────────
# CONNEXION SUPABASE
# remplace par tes vraies clés !
# ─────────────────────────────────────────

SUPABASE_URL = st.secrets["https://uymukwogikrxzynujuwj.supabase.co"]
SUPABASE_KEY = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV5bXVrd29naWtyeHp5bnVqdXdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI2NzI5NjMsImV4cCI6MjA4ODI0ODk2M30.mG3lTMApQNh4LRtEU1S3LbI2OFMcaGgXsFCQd03JTwM"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─────────────────────────────────────────
# CONFIGURATION DE LA PAGE
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Élections Présidence COMET 2026",
    page_icon="🗳️",
    layout="wide"
)

st.markdown("""
<style>
    .titre-principal {
        text-align: center;
        color: #1a1a2e;
        font-size: 2.5rem;
        font-weight: bold;
    }
    .slogan {
        font-style: italic;
        color: #FFD700;
        text-align: center;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        padding: 10px 25px;
        font-size: 1rem;
        border: none;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# PAGE DE CONNEXION
# ─────────────────────────────────────────
def page_connexion():
    st.markdown("<h1 class='titre-principal'>🗳️ Élections Présidence COMET 2026</h1>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 👤 Connexion")
        st.info("Connecte-toi avec ton adresse Gmail pour donner ton avis sur les candidats.")

        email = st.text_input("📧 Ton adresse Gmail", placeholder="prenom.nom@gmail.com")

        if st.button("🔐 Se connecter"):
            if email.endswith("@gmail.com"):
                st.session_state["connecte"] = True
                st.session_state["user_email"] = email
                st.session_state["user_nom"] = "Anonyme"
                st.rerun()
            else:
                st.error("❌ Merci d'entrer une adresse Gmail valide (@gmail.com).")


# ─────────────────────────────────────────
# PAGE PRINCIPALE
# ─────────────────────────────────────────
def page_principale():
    st.markdown("<h1 class='titre-principal'>🗳️ Élections Présidence COMET 2026</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center'>Bienvenue ! Donne ton avis sur chaque candidat.</p>", unsafe_allow_html=True)
    st.markdown("---")

    col_a, col_b = st.columns([5, 1])
    with col_b:
        if st.button("🚪 Déconnexion"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    noms = [c["nom"] for c in CANDIDATS]
    candidat_choisi = st.selectbox("👇 Choisir un candidat à évaluer", noms)
    candidat = next(c for c in CANDIDATS if c["nom"] == candidat_choisi)
    afficher_fiche_candidat(candidat)


# ─────────────────────────────────────────
# FICHE CANDIDAT
# ─────────────────────────────────────────
def afficher_fiche_candidat(candidat):
    st.markdown("---")
    col_photo, col_info = st.columns([1, 2])

    with col_photo:
        if os.path.exists(candidat["photo"]):
            st.image(candidat["photo"], width=250)
        else:
            st.image("https://via.placeholder.com/250x300?text=" + candidat["nom"], width=250)

    with col_info:
        st.markdown(f"## {candidat['nom']}")
        st.markdown(f"<p class='slogan'>{candidat['slogan']}</p>", unsafe_allow_html=True)
        st.markdown(f"**À propos :** {candidat['description']}")

    st.markdown("---")
    st.markdown("### 📊 Ta note pour ce candidat")
    st.caption("Glisse le curseur pour donner une note de 1 à 10 pour chaque critère.")

    notes = {}
    cols = st.columns(len(CRITERES))
    for i, critere in enumerate(CRITERES):
        with cols[i]:
            notes[critere["id"]] = st.slider(
                critere["label"],
                min_value=1, max_value=10, value=5,
                key=f"note_{candidat['id']}_{critere['id']}"
            )

    st.markdown("### 💬 Ton commentaire (optionnel)")
    commentaire = st.text_area(
        "Exprime-toi librement sur ce candidat :",
        max_chars=500,
        key=f"comment_{candidat['id']}"
    )
    st.caption(f"{len(commentaire)}/500 caractères")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(f"✅ Soumettre mon évaluation de {candidat['nom']}", use_container_width=True):
            soumettre_evaluation(candidat, notes, commentaire)


# ─────────────────────────────────────────
# SOUMETTRE ET SAUVEGARDER DANS SUPABASE
# ─────────────────────────────────────────
def soumettre_evaluation(candidat, notes, commentaire):
    user_email = st.session_state["user_email"]
    today = datetime.now().strftime("%Y-%m-%d")

    donnees = {
        "email": user_email,
        "candidat_id": candidat["id"],
        "candidat_nom": candidat["nom"],
        "eloquence": notes["eloquence"],
        "charisme": notes["charisme"],
        "programme": notes["programme"],
        "leadership": notes["leadership"],
        "confiance": notes["confiance"],
        "moyenne": round(sum(notes.values()) / len(notes), 2),
        "commentaire": commentaire,
        "date": today
    }

    # Vérifier si la personne a déjà donné un avis aujourd'hui
    existant = supabase.table("evaluation").select("id").eq("email", user_email).eq("candidat_id", candidat["id"]).eq("date", today).execute()

    if existant.data:
        # Mettre à jour l'avis existant
        supabase.table("evaluation").update(donnees).eq("email", user_email).eq("candidat_id", candidat["id"]).eq("date", today).execute()
        st.success(f"✅ Ton avis sur **{candidat['nom']}** a été mis à jour !")
    else:
        # Créer un nouvel avis
        supabase.table("evaluation").insert(donnees).execute()
        st.success(f"🎉 Ton avis sur **{candidat['nom']}** a bien été enregistré !")

    # Affichage récapitulatif
    cols = st.columns(len(notes))
    for i, (critere_id, note) in enumerate(notes.items()):
        label = next(c["label"] for c in CRITERES if c["id"] == critere_id)
        with cols[i]:
            st.metric(label, f"{note}/10")

    st.markdown(f"**Note moyenne : {donnees['moyenne']}/10**")
    if commentaire:
        st.markdown(f"**Ton commentaire :** _{commentaire}_")
    st.info("📌 Tu pourras donner un nouvel avis demain !")


# ─────────────────────────────────────────
# LANCEMENT
# ─────────────────────────────────────────
def main():
    if "connecte" not in st.session_state:
        st.session_state["connecte"] = False

    if st.session_state["connecte"]:
        page_principale()
    else:
        page_connexion()

if __name__ == "__main__":
    main()

