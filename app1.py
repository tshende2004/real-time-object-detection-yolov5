import streamlit as st
import sqlite3
import hashlib
import cv2
import pandas as pd
import tempfile
from datetime import datetime
import time
import os
from detector import Detector

#-------------------------------------------
# DATABASE
#-------------------------------------------
conn = sqlite3.connect(
    "users.db",
    check_same_thread=False
)

cursor = conn.cursor()


# Backend detector instance
@st.cache_resource
def load_detector():
    return Detector()

detector = load_detector()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

conn.commit()


#-------------------------------------------
# PASSWORD HASHING
#-------------------------------------------
def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


#-------------------------------------------
# REGISTER USER
#-------------------------------------------
def register_user(
    username,
    password
):

    try:

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (
                username,
                hash_password(password)
            )
        )

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False


#-------------------------------------------
# LOGIN USER
#-------------------------------------------
def login_user(
    username,
    password
):

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username=?
        AND password=?
        """,
        (
            username,
            hash_password(password)
        )
    )

    return cursor.fetchone()


#---------------------------------
# Forget Password
#---------------------------------
def reset_password(
    username,
    new_password
):

    cursor.execute(
        """
        UPDATE users
        SET password=?
        WHERE username=?
        """,
        (
            hash_password(new_password),
            username
        )
    )

    conn.commit()

    return cursor.rowcount > 0


#-------------------------------------------
# SESSION STATE
#-------------------------------------------
if "forgot_password" not in st.session_state:
    st.session_state.forgot_password = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "run" not in st.session_state:
    st.session_state.run = False

if "logs" not in st.session_state:
    st.session_state.logs = []

if "last_frame" not in st.session_state:
    st.session_state.last_frame = None

if "selected_video" not in st.session_state:
    st.session_state.selected_video = None

if "frame_pos" not in st.session_state:
    st.session_state.frame_pos = 0

#-------------------------------------------
# THUMBNAIL FUNCTION
#-------------------------------------------
def get_thumbnail(video_path):

    cap = cv2.VideoCapture(video_path)

    ret, frame = cap.read()

    cap.release()

    if ret:
        return frame

    return None

#-------------------------------------------
# DUMMY BACKEND
#-------------------------------------------



# UI CONFIG
st.set_page_config(layout="wide")

#-------------------------------------------
# LOGIN PAGE
#-------------------------------------------
if not st.session_state.logged_in:

    left, center, right = st.columns([1,2,1])

    with center:

        st.title("🔐 CCTV Monitoring Login")

        st.markdown(
            "### Welcome to CCTV Monitoring System"
        )

        st.caption(
            "Authorized users only"
        )

        login_tab, register_tab = st.tabs(
            [
                "Login",
                "Register"
            ]
        )

        # LOGIN TAB
        with login_tab:

            if not st.session_state.forgot_password:

                username = st.text_input(
                "Username",
                key="login_user"
                )

                password = st.text_input(
                "Password",
                type="password",
                key="login_pass"
                )

                btn_left, btn_center, btn_right = st.columns([1, 2, 1])

                with btn_center:

                    if st.button(
                        "Login",
                        use_container_width=True
                    ):

                        if not username or not password:

                            st.error(
                            "Username and Password cannot be empty"
                        )

                        elif login_user(
                            username,
                            password
                        ):

                            st.session_state.logged_in = True
                            st.session_state.username = username

                            st.success(
                            "Login Successful"
                            )

                            st.rerun()

                        else:

                            st.error(
                            "Invalid Username or Password"
                            )

                # FORGOT PASSWORD LINK
                forgot_left, forgot_right = st.columns([4, 1])

                with forgot_right:

                    if st.button(
                       "Forgot Password?",
                       key="forgot_password_btn"
                    ):

                       st.session_state.forgot_password = True
                       st.rerun()

            else:

                st.subheader(
                   "Reset Password"
                )

                username = st.text_input(
                   "Username",
                   key="reset_user"
                )

                new_password = st.text_input(
                   "New Password",
                   type="password",
                   key="reset_pass"
                )

                confirm_password = st.text_input(
                   "Confirm Password",
                   type="password",
                   key="reset_confirm"
                )

                btn_left, btn_center, btn_right = st.columns([1, 2, 1])

                with btn_center:

                    if st.button(
                       "Reset Password",
                        use_container_width=True
                    ):

                        if not username or not new_password:

                            st.error(
                                "Username and Password cannot be empty"
                            )

                        elif new_password != confirm_password:
 
                            st.error(
                               "Passwords do not match"
                            )

                        elif reset_password(
                            username,
                            new_password
                        ):

                            st.success(
                                "Password Updated Successfully"
                            )

                        else:

                            st.error(
                              "Username not found"
                            )

                btn_left, btn_center, btn_right = st.columns([1, 2, 1])

                with btn_center:

                    if st.button(
                       "Back to Login",
                        use_container_width=True
                    ):

                        st.session_state.forgot_password = False
                        st.rerun()

        # REGISTER TAB
        with register_tab:

            username = st.text_input(
                "New Username",
                key="register_user"
            )

            password = st.text_input(
                "Password",
                type="password",
                key="register_pass"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="confirm_pass"
            )

            btn_left, btn_center, btn_right = st.columns([1, 2, 1])

            with btn_center:

               if st.button(
                   "Register",
                   use_container_width=True
                ):

                    if not username or not password:

                        st.error(
                        "Username and Password cannot be empty"
                        )

                    elif password != confirm_password:

                       st.error(
                           "Passwords do not match"
                        )

                    elif register_user(
                        username,
                        password
                    ):

                        st.session_state.logged_in = True
                        st.session_state.username = username

                        st.success(
                            "Registration Successful"
                        )

                        st.rerun()

                    else:

                        st.error(
                        "Username already exists"
                         )

    st.stop()

header1, header2 = st.columns([8,1])

with header1:
    st.title("📹 CCTV Monitoring System")

with header2:

    st.write("")

    if st.button("🚪 Logout"):

        st.session_state.logged_in = False
        st.session_state.username = ""

        st.session_state.selected_video = None
        st.session_state.logs = []
        st.session_state.run = False

        st.rerun()

#-------------------------------------------
# SCREEN 1: VIDEO SELECTION
#-------------------------------------------
if st.session_state.selected_video is None:

    st.subheader("🎬 Select Input Source")

    input_type = st.radio(
        "Select Source",
        [
            "Dataset Videos",
            "Upload Videos",
            "Live Camera"
        ]
    )

    
    # DATASET VIDEOS
    if input_type == "Dataset Videos":

        video_folder = "videos"

        if not os.path.exists(video_folder):

            st.warning(
                "⚠️ 'videos' folder not found"
            )

        else:

            video_files = os.listdir(video_folder)

            cols = st.columns(4)

            for i, video in enumerate(video_files):

                video_path = os.path.join(
                    video_folder,
                    video
                )

                with cols[i % 4]:

                    thumb = get_thumbnail(
                        video_path
                    )

                    if thumb is not None:

                        st.image(
                            thumb,
                            channels="BGR",
                            width=180
                        )

                    st.caption(video)

                    if st.button(
                        "▶ Select",
                        key=video
                    ):

                        detector.reset()

                        st.session_state.selected_video = video_path

                        st.session_state.frame_pos = 0

                        st.session_state.run = False

                        st.session_state.last_frame = None

                        st.session_state.logs = []

                        st.empty()

                        st.rerun()

    # UPLOAD VIDEOS
    elif input_type == "Upload Videos":

        uploaded_files = st.file_uploader(
            "Upload Videos",
            accept_multiple_files=True
        )

        if uploaded_files:

            cols = st.columns(4)

            for i, file in enumerate(uploaded_files):

                with cols[i % 4]:

                    # temp preview file
                    preview_file = tempfile.NamedTemporaryFile(
                        delete=False
                    )

                    preview_file.write(
                        file.getbuffer()
                    )

                    thumb = get_thumbnail(
                        preview_file.name
                    )

                    if thumb is not None:

                        st.image(
                            thumb,
                            channels="BGR",
                            width=180
                        )

                    st.caption(file.name)

                    if st.button(
                        "▶ Select",
                        key=file.name
                    ):

                        detector.reset()
                        # temp processing file
                        tfile = tempfile.NamedTemporaryFile(
                            delete=False
                        )

                        tfile.write(
                            file.getbuffer()
                        )

                        st.session_state.selected_video = tfile.name

                        st.session_state.frame_pos = 0

                        st.session_state.run = False

                        st.session_state.last_frame = None

                        st.session_state.logs = []

                        st.empty()

                        st.rerun()

    # LIVE CAMERA
    elif input_type == "Live Camera":

        st.subheader("📷 Live Webcam Monitoring")

        st.info(
            "Use your laptop webcam for real-time monitoring."
        )

        if st.button("▶ Open Camera"):
            
            detector.reset()

            st.session_state.selected_video = 0

            st.session_state.frame_pos = 0

            st.session_state.run = False

            st.session_state.last_frame = None

            st.session_state.logs = []

            st.empty()

            st.rerun()

    st.stop()

#-------------------------------------------
# SCREEN 2: MONITORING
#-------------------------------------------

# SIDEBAR CONTROLS
st.sidebar.markdown(
    f"👤 **{st.session_state.username}**"
)

st.sidebar.header("Controls")

confidence_threshold = st.sidebar.slider(
    "Confidence Threshold",
    0.0,
    1.0,
    0.5
)

nms_threshold = st.sidebar.slider(
    "NMS Threshold",
    0.0,
    1.0,
    0.3
)

crowd_threshold = st.sidebar.slider(
    "Crowd Threshold",
    1,
    10,
    3
)

alerts_enabled = st.sidebar.checkbox(
    "Enable Alerts",
    value=True
)

#-------------------------------------------
# LAYOUT
#-------------------------------------------
col1, col2 = st.columns([2, 1])

frame_placeholder = col1.empty()

alert_placeholder = col2.empty()

count_placeholder = col2.empty()

#----------------------------------------
# BACK BUTTON
#----------------------------------------
if st.sidebar.button("🔙 Back"):

    frame_placeholder.empty()

    st.session_state.selected_video = None

    st.session_state.run = False

    st.session_state.frame_pos = 0

    st.session_state.last_frame = None

    st.session_state.logs = []

    st.rerun()

#--------------------------------------------
# VIDEO CAPTURE
#--------------------------------------------
cap = cv2.VideoCapture(
    st.session_state.selected_video
)

# only set frame position for videos
if st.session_state.selected_video != 0:

    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        st.session_state.frame_pos
    )

# PREVIEW BEFORE START
if (
    not st.session_state.run
    and st.session_state.selected_video != 0
):

    ret, frame = cap.read()

    if ret:

        frame_placeholder.image(
            frame,
            channels="BGR"
        )

#-----------------------------------------
# START / STOP BUTTONS
#------------------------------------------
st.markdown("---")

c1, c2, c3 = st.columns([1, 2, 1])

with c2:

    start_col, stop_col = st.columns(2)

    with start_col:

        if st.button("▶ Start Monitoring"):

            st.session_state.run = True

    with stop_col:

        if st.button("⏹ Stop Monitoring"):

            st.session_state.run = False

#----------------------------------------
# MAIN MONITORING LOOP
#----------------------------------------
if st.session_state.run:

    while (
        cap.isOpened()
        and st.session_state.run
    ):

        ret, frame = cap.read()

        if not ret:
            break

        processed_frame, active_anomalies = detector.process(
            frame,
            st.session_state.selected_video
        )


        person_count = len(
            detector.prev_pos
        )

        person_detected = person_count > 0

        confidence = 1.0

        if active_anomalies:
            anomaly = list(active_anomalies.keys())[0]
        else:
            anomaly = "Normal"

        
        # SHOW FRAME
        frame_placeholder.image(
            processed_frame,
            channels="BGR"
        )

        
        # SAVE LAST FRAME
        st.session_state.last_frame = processed_frame

        # save frame position only for videos
        if st.session_state.selected_video != 0:

            st.session_state.frame_pos = cap.get(
                cv2.CAP_PROP_POS_FRAMES
            )

        # -------------------------------
        # PEOPLE COUNT
        # -------------------------------
        count_placeholder.markdown(
            f"### 👥 People: {person_count}"
        )

        # -------------------------------
        # ALERTS
        # -------------------------------
        if alerts_enabled:
  
            alert_placeholder.empty()

            if anomaly != "Normal":

                alert_placeholder.error(
                    f"⚠️ {anomaly}"
                )

            elif person_detected:

                alert_placeholder.warning(
                    "🚨 Person Detected"
                )

        # -------------------------------
        # LOGS
        # -------------------------------
        st.session_state.logs.append({

            "Time": datetime.now().strftime(
                "%H:%M:%S"
            ),

            "Count": person_count,

            "Confidence": confidence,

            "Anomaly": anomaly
        })

        time.sleep(0.03)

    cap.release()


# =========================================================
# SHOW LAST FRAME AFTER STOP
# =========================================================
if (
    not st.session_state.run
    and st.session_state.last_frame is not None
):

    frame_placeholder.image(
        st.session_state.last_frame,
        channels="BGR"
    )


# =========================================================
# 📊 LOGS
# =========================================================
st.subheader("📊 Logs")

if st.session_state.logs:

    df = pd.DataFrame(
        st.session_state.logs
    )

    # -------------------------------
    # SHOW LOG TABLE
    # -------------------------------
    st.dataframe(df)

    # -------------------------------
    # DOWNLOAD REPORT
    # -------------------------------
    st.download_button(
        "Download Report",
        df.to_csv(index=False),
        "report.csv"
    )

else:

    st.write("No logs yet.")


# =========================================================
# ANALYTICS (ONLY AFTER STOP)
# =========================================================
if (
    not st.session_state.run
    and st.session_state.logs
):

    import plotly.express as px

    st.subheader("📈 Analytics Dashboard")

    # --------------------------------
    # CREATE 2 COLUMNS
    # --------------------------------
    graph1, graph2 = st.columns(2)

    # =================================
    # GRAPH 1
    # =================================
    with graph1:

        st.write("### 👥 People Count Over Time")

        fig1 = px.line(
            df,
            y="Count",
            title="People Count"
        )

        fig1.update_layout(
            xaxis_title="Frame Index",
            yaxis_title="People Count",
            height=400
        )

        st.plotly_chart(
            fig1,
            width="stretch"
        )

    # =================================
    # GRAPH 2
    # =================================
    with graph2:

        st.write("### 🚨 Anomaly Summary")

        anomaly_counts = (
            df["Anomaly"]
            .value_counts()
            .reset_index()
        )

        anomaly_counts.columns = [
            "Anomaly",
            "Count"
        ]

        fig2 = px.bar(
            anomaly_counts,
            x="Anomaly",
            y="Count",
            title="Detected Anomalies"
        )

        fig2.update_layout(
            height=400
        )

        st.plotly_chart(
            fig2,
            width="stretch"
        )