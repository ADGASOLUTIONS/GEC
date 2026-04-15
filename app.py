import streamlit as st
import pandas as pd
from datetime import date
import os
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="GEC - ADGA SOLUTIONS", layout="wide")

# --- PARAMÈTRES EMAIL (À CONFIGURER) ---
EMAIL_EXPEDITEUR = "ton-email@gmail.com"  
MOT_DE_PASSE_APP = "xxxx xxxx xxxx xxxx" 

SERVICES_MAILS = {
    "Secrétariat": "secretariat.lta@gmail.com",
    "Direction Générale (DG)": "dg.lta@gmail.com",
    "Assistant de Direction (AD)": "ad.lta@gmail.com",
    "DAF": "daf.lta@gmail.com",
    "DRH": "drh.lta@gmail.com",
    "Commercial": "commercial.lta@gmail.com"
}

# --- FONCTION D'ENVOI DE NOTIFICATION ---
def envoyer_notification(destinataire_email, service_destinataire, objet_courrier):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_EXPEDITEUR
        msg['To'] = destinataire_email
        msg['Subject'] = f"🔔 Nouveau courrier GEC - Service {service_destinataire}"
        corps = f"Bonjour,\n\nUn nouveau courrier ({objet_courrier}) vous a été transféré.\n\nCordialement,\nADGA SOLUTIONS."
        msg.attach(MIMEText(corps, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_APP)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# --- SYSTÈME DE CONNEXION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align: center;'>🔐 Connexion GEC - LTA</h1>", unsafe_allow_html=True)
        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            with st.form("login_form"):
                service_user = st.selectbox("Sélectionnez votre Service", list(SERVICES_MAILS.keys()))
                pwd_input = st.text_input("Mot de passe", type="password")
                submitted = st.form_submit_button("Entrer dans l'espace")
                if submitted:
                    if pwd_input == "LTA2026":
                        st.session_state["password_correct"] = True
                        st.session_state["user_service"] = service_user
                        st.rerun()
                    else:
                        st.error("❌ Mot de passe incorrect")
        return False
    return True

if not check_password():
    st.stop()

# --- INITIALISATION SYSTÈME ---
UPLOAD_DIR = "archives_pdf"
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

DB_FILE = "registre_gec_adga.xlsx"
if not os.path.exists(DB_FILE):
    COLUMNS = ["ID", "Date", "Type", "Correspondant", "Objet", "Référence", "Fichier", "Localisation", "Statut", "Observations"]
    pd.DataFrame(columns=COLUMNS).to_excel(DB_FILE, index=False)

def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="700" type="application/pdf"></iframe>', unsafe_allow_html=True)

# --- BARRE LATÉRALE ---
role_actuel = st.session_state['user_service']
with st.sidebar:
    st.image("https://via.placeholder.com/150", caption="ADGA SOLUTIONS", use_container_width=True)
    st.info(f"📍 Service : {role_actuel}")
    if st.button("🚪 Déconnexion"):
        del st.session_state["password_correct"]
        st.rerun()

# --- CORPS PRINCIPAL ---
st.title(f"📂 Espace GEC - {role_actuel}")

# Chargement de la base à chaque action pour éviter les bugs d'affichage
df_all = pd.read_excel(DB_FILE).fillna("")

# 1. SECTION SECRÉTARIAT
if role_actuel == "Secrétariat":
    with st.expander("➕ Enregistrer un nouveau courrier", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            type_c = st.selectbox("Type", ["Arrivée", "Départ"])
            contact = st.text_input("Correspondant")
            ref = st.text_input("Référence")
        with col2:
            objet = st.text_area("Objet")
            up_file = st.file_uploader("Scan PDF", type=["pdf"])
        
        if st.button("🚀 Enregistrer et Envoyer au DG"):
            if contact and objet and up_file:
                new_id = len(df_all) + 1
                f_name = f"ID{new_id}_{up_file.name}"
                with open(os.path.join(UPLOAD_DIR, f_name), "wb") as f: f.write(up_file.getbuffer())
                
                # CRITIQUE : La localisation doit être EXACTEMENT le nom du service dans SERVICES_MAILS
                new_row = {"ID": new_id, "Date": date.today().strftime("%d/%m/%Y"), "Type": type_c, "Correspondant": contact, "Objet": objet, "Référence": ref, "Fichier": f_name, "Localisation": "Direction Générale (DG)", "Statut": "Nouveau / Attente DG", "Observations": "Enregistré par Secrétariat"}
                df_temp = pd.concat([df_all, pd.DataFrame([new_row])], ignore_index=True)
                df_temp.to_excel(DB_FILE, index=False)
                
                envoyer_notification(SERVICES_MAILS["Direction Générale (DG)"], "Direction Générale (DG)", objet)
                st.success("✅ Courrier envoyé au DG !")
                st.rerun()

# 2. GESTION DES FLUX (C'est ici que le DG verra ses courriers)
st.markdown("---")
# IMPORTANT : On rafraîchit le filtrage
mes_docs = df_all[df_all["Localisation"] == role_actuel]

if not mes_docs.empty:
    st.subheader(f"📥 Courriers reçus par votre service")
    st.dataframe(mes_docs[["ID", "Date", "Correspondant", "Objet", "Statut"]], use_container_width=True)
    
    c1, c2 = st.columns([1, 2])
    with c1:
        sel_id = st.selectbox("Sélectionner un courrier pour action", mes_docs["ID"])
        courrier_focus = mes_docs[mes_docs["ID"] == sel_id].iloc[0]
        
        if st.button("👁️ Ouvrir le document"): 
            st.session_state['view_pdf'] = courrier_focus['Fichier']
        
        st.markdown("---")
        dest = st.selectbox("Transférer à :", [s for s in SERVICES_MAILS.keys() if s != role_actuel])
        note = st.text_area("Vos instructions :")
        
        if st.button("✅ Confirmer le transfert"):
            # Mise à jour dans le DataFrame global
            df_all.loc[df_all["ID"] == sel_id, "Localisation"] = dest
            df_all.loc[df_all["ID"] == sel_id, "Statut"] = f"Traité par {role_actuel}"
            df_all.loc[df_all["ID"] == sel_id, "Observations"] = f"[{role_actuel}]: {note} | " + str(courrier_focus['Observations'])
            
            df_all.to_excel(DB_FILE, index=False)
            envoyer_notification(SERVICES_MAILS[dest], dest, courrier_focus['Objet'])
            st.success(f"Transmis à {dest}")
            st.rerun()
    with c2:
        if 'view_pdf' in st.session_state:
            path = os.path.join(UPLOAD_DIR, st.session_state['view_pdf'])
            if os.path.exists(path): display_pdf(path)
else:
    st.info(f"ℹ️ Aucun courrier en attente pour le service {role_actuel}.")

# 3. RECHERCHE / ARCHIVES
with st.expander("🔍 Archives de tous les courriers"):
    query = st.text_input("Recherche rapide...")
    if query:
        result = df_all[df_all.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)]
        st.dataframe(result, use_container_width=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>© 2026 ADGA SOLUTIONS</p>", unsafe_allow_html=True)
