import streamlit as st

def detect_screen_size():
    st.markdown("""
        <script>
            function sendScreenSize() {
                const width = window.innerWidth;
                const height = window.innerHeight;
                window.parent.postMessage(
                    {isStreamlitMessage: true, width: width, height: height},
                    "*"
                );
            }
            window.onload = sendScreenSize;
            window.onresize = sendScreenSize;
        </script>
    """, unsafe_allow_html=True)

def screen_size_listener():
    message = st.experimental_get_query_params()
    return message

def is_small_screen():
    return st.session_state.get("screen_width", 1920) <= 1024
    
def sync_screen_size():
    detect_screen_size()

    st.markdown("""
        <script>
            window.addEventListener("message", (event) => {
                if (event.data && event.data.width) {
                    const width = event.data.width;
                    const height = event.data.height;

                    const data = {
                        width: width,
                        height: height,
                    };

                    fetch("/_stcore/setComponentValue", {
                        method: "POST",
                        body: JSON.stringify(data),
                        headers: {"Content-Type": "application/json"},
                    });
                }
            });
        </script>
    """, unsafe_allow_html=True)
