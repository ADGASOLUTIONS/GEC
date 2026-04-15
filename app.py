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

# --- PARAMÈTRES EMAIL (À CONFIGURER AVEC TON CODE GOOGLE) ---
EMAIL_EXPEDITEUR = "ton-email@gmail.com"  
MOT_DE_PASSE_APP = "xxxx xxxx xxxx xxxx" 

# Dictionnaire pour les notifications (Emails réels des services de LTA)
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

        corps = f"""
        Bonjour l'équipe {service_destinataire},
        
        Un nouveau courrier concernant "{objet_courrier}" vient de vous être transféré dans le logiciel GEC.
        
        Veuillez vous connecter pour le traiter.
        Lien : https://gecdeadgasolutions.streamlit.app/
        
        Cordialement,
        Système GEC - ADGA SOLUTIONS.
        """
        msg.attach(MIMEText(corps, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_APP)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        return False

# --- SYSTÈME DE CONNEXION SIMPLIFIÉ ---
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h1 style='text-align: center;'>🔐 Connexion GEC - LTA</h1>", unsafe_allow_html=True)
        col_l, col_m, col_r = st.columns([1, 2, 1])
        with col_m:
            with st.form("login_form"):
                # On ne demande que le service et le mot de passe
                service_user = st.selectbox("Sélectionnez votre Service", list(SERVICES_MAILS.keys()))
                pwd_input = st.text_input("Mot de passe", type="password")
                submitted = st.form_submit_button("Entrer dans l'espace")
                
                if submitted:
                    # MOT DE PASSE UNIQUE : LTA2026
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
    st.markdown("---")
    st.write(f"**👤 Connecté en tant que :**")
    st.info(f"📍 {role_actuel}")
    st.write("**🏢 Entreprise :** LTA")
    st.markdown("---")
    
    if st.button("🚪 Déconnexion"):
        del st.session_state["password_correct"]
        st.rerun()
    st.caption("Développé par **ADGA SOLUTIONS**")

# --- CORPS PRINCIPAL ---
st.title(f"📂 Espace GEC - {role_actuel}")

# 1. SECTION ENREGISTREMENT (RÉSERVÉ AU SECRÉTARIAT)
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
                df = pd.read_excel(DB_FILE)
                new_id = len(df) + 1
                f_name = f"ID{new_id}_{up_file.name}"
                with open(os.path.join(UPLOAD_DIR, f_name), "wb") as f: f.write(up_file.getbuffer())
                
                new_row = {"ID": new_id, "Date": date.today().strftime("%d/%m/%Y"), "Type": type_c, "Correspondant": contact, "Objet": objet, "Référence": ref, "Fichier": f_name, "Localisation": "Direction Générale (DG)", "Statut": "Nouveau / Attente DG", "Observations": "Enregistré par Secrétariat"}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=False)
                df.to_excel(DB_FILE, index=False)
                
                # Notification Email auto au DG
                envoyer_notification(SERVICES_MAILS["Direction Générale (DG)"], "Direction Générale (DG)", objet)
                
                st.success("✅ Enregistré ! Notification envoyée à la Direction Générale.")
                st.rerun()

# 2. GESTION DES FLUX
st.markdown("---")
df_all = pd.read_excel(DB_FILE).fillna("")
mes_docs = df_all[df_all["Localisation"] == role_actuel]

if not mes_docs.empty:
    st.subheader(f"📥 Courriers à traiter ({len(mes_docs)})")
    st.dataframe(mes_docs[["ID", "Date", "Correspondant", "Objet", "Statut"]], use_container_width=True)
    
    c1, c2 = st.columns([1, 2])
    with c1:
        sel_id = st.selectbox("Sélectionner l'ID", mes_docs["ID"])
        courrier = mes_docs[mes_docs["ID"] == sel_id].iloc[0]
        
        if st.button("👁️ Visualiser le PDF"): 
            st.session_state['view_pdf'] = courrier['Fichier']
        
        st.markdown("---")
        dest = st.selectbox("Transférer au service :", [s for s in SERVICES_MAILS.keys() if s != role_actuel])
        note = st.text_area("Annotation / Instruction :")
        
        if st.button("✅ Valider le transfert"):
            df_all.loc[df_all["ID"] == sel_id, ["Localisation", "Statut"]] = [dest, f"Transmis par {role_actuel}"]
            df_all.loc[df_all["ID"] == sel_id, "Observations"] = f"[{role_actuel}]: {note} | " + str(courrier['Observations'])
            df_all.to_excel(DB_FILE, index=False)
            
            # Notification Email au service suivant
            envoyer_notification(SERVICES_MAILS[dest], dest, courrier['Objet'])
            
            st.success(f"Dossier transmis avec succès à : {dest}")
            st.rerun()
    with c2:
        if 'view_pdf' in st.session_state:
            path = os.path.join(UPLOAD_DIR, st.session_state['view_pdf'])
            if os.path.exists(path): display_pdf(path)
else:
    st.info(f"💡 Aucun courrier en attente pour le service {role_actuel}.")

# 3. ARCHIVES
with st.expander("🔍 Rechercher dans les archives (Tous les services)"):
    query = st.text_input("Mot-clé (Objet, Nom, Réf...)")
    if query:
        result = df_all[df_all.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)]
        st.dataframe(result, use_container_width=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>© 2026 ADGA SOLUTIONS | Système GEC | adgasolutions@gmail.com </p>", unsafe_allow_html=True)
