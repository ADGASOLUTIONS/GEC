import streamlit as st
import pandas as pd
from datetime import date
import os
import base64

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="GEC - ADGA SOLUTIONS", layout="wide")

# --- STYLE CSS POUR LE DESIGN ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1E3A8A; color: white; }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- INITIALISATION DU SYSTÈME ---
UPLOAD_DIR = "archives_pdf"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

DB_FILE = "registre_gec_adga.xlsx"
SERVICES = ["Secrétariat", "Direction Générale (DG)", "Assistant de Direction (AD)", "DAF", "DRH", "Commercial"]

# Création ou mise à jour de la base de données
COLUMNS = ["ID", "Date", "Type", "Correspondant", "Objet", "Référence", "Fichier", "Localisation", "Statut", "Observations"]

if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=COLUMNS).to_excel(DB_FILE, index=False)
else:
    # Vérification de sécurité : si le fichier existe mais qu'il manque 'Observations'
    df_check = pd.read_excel(DB_FILE)
    if "Observations" not in df_check.columns:
        df_check["Observations"] = ""
        df_check.to_excel(DB_FILE, index=False)

# --- FONCTION DE VISUALISATION PDF ---
def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    # Remplace par le lien de ton logo ADGA SOLUTION
    st.image("https://via.placeholder.com/150", caption="ADGA SOLUTIONS", use_container_width=True)
    st.markdown("---")
    st.write("**👤 Utilisateur :** Durcin Henri D. ODJO")
    st.write("**🏢 Entreprise :** LTA")
    st.markdown("---")
    role_actuel = st.selectbox("🔑 Changer de service (Simulation) :", SERVICES)
    st.markdown("---")
    st.caption("Développé par **ADGA SOLUTIONS**")

# --- CORPS PRINCIPAL ---
st.title(f"📂 GEC - Espace {role_actuel}")
st.markdown(f"Gestion du circuit de courrier pour **Logistique et Travaux en Afrique (LTA)**")

# --- 1. INTERFACE SECRÉTARIAT (ENREGISTREMENT) ---
if role_actuel == "Secrétariat":
    with st.expander("➕ Enregistrer un nouveau courrier entrant/sortant", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            type_c = st.selectbox("Type de courrier", ["Arrivée", "Départ"])
            contact = st.text_input("Expéditeur / Destinataire")
            ref = st.text_input("Référence du document")
        with col2:
            objet = st.text_area("Objet du courrier")
            uploaded_file = st.file_uploader("Joindre le scan (PDF obligatoire)", type=["pdf"])
        
        if st.button("🚀 Enregistrer et Envoyer au DG"):
            if contact and objet and uploaded_file:
                df = pd.read_excel(DB_FILE)
                new_id = len(df) + 1
                file_name = f"ID{new_id}_{uploaded_file.name}"
                
                # Sauvegarde du fichier physique
                with open(os.path.join(UPLOAD_DIR, file_name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Ajout dans Excel
                new_data = {
                    "ID": new_id, "Date": date.today().strftime("%d/%m/%Y"),
                    "Type": type_c, "Correspondant": contact, "Objet": objet,
                    "Référence": ref, "Fichier": file_name,
                    "Localisation": "Direction Générale (DG)", 
                    "Statut": "Nouveau / En attente DG",
                    "Observations": "Enregistré par Secrétariat"
                }
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=False)
                df.to_excel(DB_FILE, index=False)
                st.success(f"✅ Courrier ID {new_id} envoyé à la Direction Générale !")
                st.rerun()
            else:
                st.error("⚠️ Veuillez remplir tous les champs et joindre le fichier PDF.")

# --- 2. GESTION DES FLUX (POUR TOUS LES SERVICES) ---
st.markdown("---")
st.subheader(f"📥 Courriers en attente dans votre service")

full_df = pd.read_excel(DB_FILE).fillna("")
# Filtrer les courriers présents dans le service de l'utilisateur actuel
mes_courriers = full_df[full_df["Localisation"] == role_actuel]

if not mes_courriers.empty:
    # Affichage du tableau simplifié
    st.dataframe(mes_courriers[["ID", "Date", "Type", "Correspondant", "Objet", "Observations", "Statut"]], use_container_width=True)
    
    st.markdown("### ⚙️ Action sur le courrier sélectionné")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        id_choisi = st.selectbox("Sélectionner l'ID", mes_courriers["ID"])
        courrier_focus = mes_courriers[mes_courriers["ID"] == id_choisi].iloc[0]
        
        st.write("**Détails :**")
        st.write(f"🔹 **Objet :** {courrier_focus['Objet']}")
        st.write(f"🔹 **Réf :** {courrier_focus['Référence']}")
        
        if st.button("👁️ Visualiser le document"):
            st.session_state['view_pdf'] = courrier_focus['Fichier']
        
        st.markdown("---")
        st.write("**📤 Transférer le dossier**")
        destinataire = st.selectbox("Vers le service :", [s for s in SERVICES if s != role_actuel])
        note = st.text_area("Vos instructions / annotations :")
        
        if st.button("✅ Valider le transfert"):
            # Mise à jour de la base de données
            full_df.loc[full_df["ID"] == id_choisi, "Localisation"] = destinataire
            full_df.loc[full_df["ID"] == id_choisi, "Statut"] = f"Transmis par {role_actuel}"
            
            # Accumulation des notes
            anciennes_notes = str(full_df.loc[full_df["ID"] == id_choisi, "Observations"].values[0])
            nouvelle_note = f"[{role_actuel}]: {note} | " + anciennes_notes
            full_df.loc[full_df["ID"] == id_choisi, "Observations"] = nouvelle_note
            
            full_df.to_excel(DB_FILE, index=False)
            st.success(f"Courrier transféré au service {destinataire}")
            st.rerun()

    with c2:
        if 'view_pdf' in st.session_state:
            path_pdf = os.path.join(UPLOAD_DIR, st.session_state['view_pdf'])
            if os.path.exists(path_pdf):
                display_pdf(path_pdf)
            else:
                st.error("Fichier introuvable sur le serveur.")
else:
    st.info(f"💡 Aucun courrier n'est actuellement en attente au service {role_actuel}.")

# --- RECHERCHE GLOBALE (HISTORIQUE) ---
with st.expander("🔍 Rechercher un courrier dans tout le système (Archives)"):
    search_query = st.text_input("Tapez un mot-clé (Nom, Objet, Référence...)")
    if search_query:
        resultats = full_df[full_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
        st.dataframe(resultats, use_container_width=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>© 2026 ADGA SOLUTIONS | Logiciel de Gestion de Courrier pour LTA</p>", unsafe_allow_html=True)