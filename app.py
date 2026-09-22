import streamlit as st
import os
import random
import smtplib
from email.mime.text import MIMEText

# Files ke paths
VOTERS_FILE = "voters.txt"
CANDIDATES_FILE = "candidates.txt"
VOTED_LOG_FILE = "voted_log.txt"       
VOTES_COUNT_FILE = "votes_count.txt"   

# ⚠️ !!! ADMIN CONFIGURATION (APNI DETAILS BIILKUL SAHI LIKHEIN) !!!
 # 🔒 Passwords safely linked to Streamlit Secure Vault (Hacker Proof)
SENDER_EMAIL = st.secrets["SENDER_EMAIL"]          
SENDER_APP_PASSWORD = st.secrets["SENDER_APP_PASSWORD"]   
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]             
            # Final results lock password

st.set_page_config(page_title="OTP Secure IT Society Elections", page_icon="🗳️", layout="centered")
st.title("🗳️ IT Society Secure OTP Voting System")
st.write("Official automated election portal for IT Department.")

# Fixed SMTP Email Function with Direct IP to bypass local DNS/URL issues
def send_otp_email(receiver_email, otp_code):
    try:
        msg = MIMEText(f"Dear Voter,\n\nYour secure OTP for the IT Society Election is: {otp_code}\n\nDo not share this code with anyone.\n\nBest regards,\nIT Society Election Committee")
        msg['Subject'] = '🗳️ Your Secure Voting OTP'
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email

        # 🌟 FIXED: Direct Google SMTP server integration on standard Port 587
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure connection activation
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Error: {str(e)}")
        return False

def load_list(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def get_grouped_candidates():
    lines = load_list(CANDIDATES_FILE)
    grouped = {}
    for line in lines:
        if ":" in line:
            post, name = line.split(":", 1)
            post, name = post.strip(), name.strip()
            if post not in grouped:
                grouped[post] = []
            grouped[post].append(name)
    return grouped

allowed_voters = [v.lower() for v in load_list(VOTERS_FILE)]
grouped_candidates = get_grouped_candidates()

if not os.path.exists(VOTED_LOG_FILE):
    open(VOTED_LOG_FILE, "w").close()

if not os.path.exists(VOTES_COUNT_FILE) or os.path.getsize(VOTES_COUNT_FILE) == 0:
    with open(VOTES_COUNT_FILE, "w") as f:
        for post, names in grouped_candidates.items():
            for name in names:
                f.write(f"{post}|{name}:0\n")

# Session States for memory handling
if "otp_status" not in st.session_state:
    st.session_state.otp_status = "NOT_SENT"
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None
if "verified_email" not in st.session_state:
    st.session_state.verified_email = None

menu = st.sidebar.selectbox("Menu", ["Cast Your Vote", "Transparency Dashboard", "🔒 Admin Results Desk"])

if menu == "Cast Your Vote":
    st.subheader("🔑 Step 1: Request Secure OTP")
    
    is_disabled = st.session_state.otp_status in ["SENT", "VERIFIED"]
    email = st.text_input("Enter your official University Email:", disabled=is_disabled).strip().lower()
    
    if st.session_state.otp_status == "NOT_SENT":
        if st.button("Send Verification OTP"):
            voted_list = [v.lower() for v in load_list(VOTED_LOG_FILE)]
            
            if email not in allowed_voters:
                st.error("❌ Access Denied: This email is not in the IT Department voters list.")
            elif email in voted_list:
                st.warning("⚠️ Already Voted: This email has already submitted a ballot.")
            else:
                otp = str(random.randint(100000, 999999))
                st.info("🔄 Sending secure OTP... Please wait.")
                
                if send_otp_email(email, otp):
                    st.session_state.generated_otp = otp
                    st.session_state.otp_status = "SENT"
                    st.session_state.verified_email = email
                    st.rerun()
                else:
                    st.error("❌ Failed to send email. Check Admin SMTP details or App Password.")

    if st.session_state.otp_status == "SENT" and st.session_state.verified_email:
        st.success(f"📩 OTP successfully sent to: {st.session_state.verified_email}")
        user_otp = st.text_input("Enter the 6-Digit OTP received in your email:", type="default").strip()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Verify OTP & Open Ballot"):
                if user_otp == st.session_state.generated_otp:
                    st.session_state.otp_status = "VERIFIED"
                    st.rerun()
                else:
                    st.error("❌ Invalid OTP Code. Please try again.")
        with col2:
            if st.button("❌ Cancel / Reset"):
                st.session_state.otp_status = "NOT_SENT"
                st.session_state.generated_otp = None
                st.session_state.verified_email = None
                st.rerun()

    if st.session_state.otp_status == "VERIFIED":
        st.write("---")
        st.subheader("🗳️ Digital Ballot Paper")
        st.info(f"Voting anonymously as verified user: {st.session_state.verified_email}")
        
        voter_selections = {}
        if grouped_candidates:
            for post, names in grouped_candidates.items():
                st.write(f"### 🎖️ {post}")
                voter_selections[post] = st.radio(f"Select Candidate for {post}:", names, key=post)
                st.write("---")
            
            if st.button("Submit Secure Ballot"):
                with open(VOTED_LOG_FILE, "a") as f:
                    f.write(f"{st.session_state.verified_email}\n")
                
                votes_data = {}
                if os.path.exists(VOTES_COUNT_FILE):
                    with open(VOTES_COUNT_FILE, "r") as f:
                        for line in f:
                            if ":" in line:
                                key, count = line.strip().split(":")
                                votes_data[key] = int(count)
                
                for post, selected_name in voter_selections.items():
                    vote_key = f"{post}|{selected_name}"
                    if vote_key in votes_data:
                        votes_data[vote_key] += 1
                
                with open(VOTES_COUNT_FILE, "w") as f:
                    for key, count in votes_data.items():
                        f.write(f"{key}:{count}\n")
                
                st.balloons()
                st.success("🎉 All your votes have been securely and anonymously cast!")
                
                st.session_state.otp_status = "NOT_SENT"
                st.session_state.generated_otp = None
                st.session_state.verified_email = None
                st.info("System refreshed. Ready for the next voter.")
        else:
            st.error("No candidate data found.")

elif menu == "Transparency Dashboard":
    st.subheader("📊 Live Election Transparency Audit")
    voted_list = load_list(VOTED_LOG_FILE)
    st.info(f"📈 **Total Ballots Safely Cast:** {len(voted_list)}")
    st.write("---")
    st.write("### 👥 Verified Voters Log")
    if voted_list:
        for v in voted_list:
            st.text(f"✔️ {v}")
    else:
        st.info("No votes cast yet.")

elif menu == "🔒 Admin Results Desk":
    st.subheader("🔒 Final Results Room")
    password = st.text_input("Enter Admin Password to unlock results:", type="password")
    
    if password == ADMIN_PASSWORD:
        st.success("🔓 Results Unlocked Successfully!")
        votes_data = {}
        if os.path.exists(VOTES_COUNT_FILE):
            with open(VOTES_COUNT_FILE, "r") as f:
                for line in f:
                    if ":" in line:
                        key, count = line.strip().split(":")
                        votes_data[key] = int(count)
        
        for post, names in grouped_candidates.items():
            st.write(f"## 📊 Results: {post}")
            cols = st.columns(len(names))
            for i, name in enumerate(names):
                vote_key = f"{post}|{name}"
                count = votes_data.get(vote_key, 0)
                cols[i].metric(label=name, value=f"{count} Votes")
            st.write("---")
    elif password:
        st.error("❌ Incorrect Admin Password.")








