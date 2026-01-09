"""
Streamlit app for testing the /chat API with polling.

This app demonstrates:
- Sending a new message to start a workflow
- Polling for updates until completion
- Displaying progress and status in real-time
"""

import streamlit as st
import requests
import time
from typing import Optional, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"


def send_new_message(message: str) -> Optional[Dict[str, Any]]:
    """
    Send a new message to start a workflow.

    Args:
        message: User message to process

    Returns:
        API response or None if error
    """
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json={"message": message},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error sending message: {e}")
        return None


def poll_workflow(thread_id: str) -> Optional[Dict[str, Any]]:
    """
    Poll an existing workflow for updates.

    Args:
        thread_id: Thread ID to poll

    Returns:
        API response or None if error
    """
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json={"thread_id": thread_id},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error polling workflow: {e}")
        return None


def display_response(response: Dict[str, Any]):
    """Display API response in a structured format."""
    col1, col2, col3 = st.columns(3)

    with col1:
        status = response["status"].upper()
        if status == "COMPLETED":
            st.metric("Status", status, delta="Done", delta_color="normal")
        elif status == "FAILED":
            st.metric("Status", status, delta="Error", delta_color="inverse")
        else:
            st.metric("Status", status, delta="Running", delta_color="off")

    with col2:
        progress = response.get("progress", {})
        current = progress.get("current", 0)
        total = progress.get("total", 4)
        st.metric("Progress", f"{current}/{total}")

    with col3:
        st.metric("Current Node", response.get("current_node", "Unknown"))

    # Display message
    st.info(response.get("message", "No message"))

    # Display thread ID
    st.text(f"Thread ID: {response['thread_id']}")

    # Progress bar
    progress = response.get("progress", {})
    current = progress.get("current", 0)
    total = progress.get("total", 4)
    st.progress(current / total if total > 0 else 0)

    # Display data if available
    data = response.get("data", {})
    if data:
        with st.expander("Workflow Data", expanded=True):
            st.json(data)


def main():
    st.set_page_config(
        page_title="Chat API Polling Test",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 Polling-Based Chat API Test")
    st.markdown("Test the `/chat` endpoint with automatic polling functionality")

    # Initialize session state
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "polling" not in st.session_state:
        st.session_state.polling = False
    if "responses" not in st.session_state:
        st.session_state.responses = []

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_url = st.text_input("API Base URL", value=API_BASE_URL)
        poll_interval = st.slider("Poll Interval (seconds)", 1, 10, 2)

        st.divider()

        st.header("📊 Session Info")
        if st.session_state.thread_id:
            st.success(f"Active Thread ID:")
            st.code(st.session_state.thread_id, language=None)
            if st.button("🔄 Reset Session"):
                st.session_state.thread_id = None
                st.session_state.polling = False
                st.session_state.responses = []
                st.rerun()
        else:
            st.info("No active workflow")

    # Main content area
    st.header("💬 Send a Message")

    # Input form
    with st.form("message_form", clear_on_submit=True):
        user_message = st.text_area(
            "Enter your message:",
            placeholder="e.g., Analyze Q4 sales report",
            height=100
        )
        submitted = st.form_submit_button("🚀 Send Message")

    # Handle form submission
    if submitted and user_message:
        with st.spinner("Sending message..."):
            response = send_new_message(user_message)

            if response:
                st.session_state.thread_id = response["thread_id"]
                st.session_state.polling = True
                st.session_state.responses = [response]
                st.success("Message sent! Starting to poll...")
                time.sleep(0.5)
                st.rerun()

    # Display current workflow status
    if st.session_state.thread_id and st.session_state.responses:
        st.header("📈 Workflow Status")

        # Get latest response
        latest_response = st.session_state.responses[-1]

        # Display response
        display_response(latest_response)

        # Auto-poll if still running
        if st.session_state.polling and latest_response["status"] == "running":
            with st.spinner(f"Polling for updates (every {poll_interval}s)..."):
                time.sleep(poll_interval)

                # Poll for update
                poll_response = poll_workflow(st.session_state.thread_id)

                if poll_response:
                    st.session_state.responses.append(poll_response)

                    # Stop polling if completed or failed
                    if poll_response["status"] in ["completed", "failed"]:
                        st.session_state.polling = False

                        if poll_response["status"] == "completed":
                            st.success("✅ Workflow completed successfully!")
                        else:
                            st.error("❌ Workflow failed!")

                    st.rerun()

        # Show polling history
        if len(st.session_state.responses) > 1:
            with st.expander(f"📜 Polling History ({len(st.session_state.responses)} updates)", expanded=False):
                for idx, resp in enumerate(reversed(st.session_state.responses)):
                    st.subheader(f"Update #{len(st.session_state.responses) - idx}")
                    st.json(resp)
                    st.divider()

    # Manual polling option
    if st.session_state.thread_id and not st.session_state.polling:
        st.divider()
        st.header("🔍 Manual Polling")

        if st.button("🔄 Poll Now"):
            with st.spinner("Polling..."):
                poll_response = poll_workflow(st.session_state.thread_id)

                if poll_response:
                    st.session_state.responses.append(poll_response)
                    st.rerun()

    # Footer
    st.divider()
    st.markdown("---")
    st.caption("Built with Streamlit | Testing Polling-Based LangGraph Chat API")


if __name__ == "__main__":
    main()
