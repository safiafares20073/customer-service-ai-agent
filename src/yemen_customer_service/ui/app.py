"""Customer UI. Never render the controller, backend Outcome, or raw exceptions."""

import os
import uuid

import streamlit as st

from yemen_customer_service.ui.chat import render_chat, render_header
from yemen_customer_service.ui.presentation import COPY
from yemen_customer_service.ui.service import Controller

locale = render_header()
t = COPY[locale]
if os.getenv("UI_PROVIDER", "fixture") == "fixture":
    st.caption(t["fixture"])

if (
    st.get_option("server.address") not in {"127.0.0.1", "localhost", "::1"}
    or os.getenv("ENABLE_DEMO_AUTH") != "true"
    or os.getenv("APP_ENV", "development") != "development"
    or os.getenv("UI_PROVIDER", "fixture") not in {"fixture", "openai"}
    or (os.getenv("UI_PROVIDER") == "openai" and os.getenv("UI_PAID_APPROVED") != "true")
):
    st.error(t["unavailable"])
    st.stop()

if "_controller" not in st.session_state:
    try:
        st.session_state._controller = Controller(
            os.getenv("DATABASE_PATH", "data/customer_service.sqlite3"),
            os.getenv("UI_CUSTOMER_ID", "demo-a"),
            demo_enabled=True,
        )
        st.session_state._submission_id = uuid.uuid4().hex
    except Exception:
        st.error(t["unavailable"])
        st.stop()

render_chat(st.session_state._controller, locale)
