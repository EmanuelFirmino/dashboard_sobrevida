import streamlit as st


# ============================
#   CARREGAR USUÁRIOS AUTORIZADOS
# ============================
def load_users():
    return st.secrets.get("auth", {})

# ============================
#   TELA DE LOGIN
# ============================
def login_screen():
    st.title("Observatório - SobreVIDA")

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 560px;
            padding-top: 80px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    users = load_users()

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if username in users and password == users[username]:
            st.session_state["logged"] = True
            st.session_state["user"] = username
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")


# ============================
#   PROTEGER O APP
# ============================
def require_login():
    if "logged" not in st.session_state or not st.session_state["logged"]:
        login_screen()
        st.stop()


# ============================
#   LOGOUT
# ============================
def logout_button():
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
