"""Public login page; agent access requires native OIDC plus a private invitation."""

import time
import uuid

import streamlit as st

from yemen_customer_service.hosting.auth import authorize_native_user
from yemen_customer_service.hosting.controller import HostedController
from yemen_customer_service.hosting.settings import GOOGLE_ISSUER, Settings
from yemen_customer_service.hosting.store import HostedStore
from yemen_customer_service.storage.database import Database
from yemen_customer_service.ui.chat import render_chat, render_header

locale = render_header()
ar = locale == "ar"


def safe_stop():
    st.error("الخدمة غير متاحة حاليًا." if ar else "This service is currently unavailable.")
    st.stop()


def sign_out():
    controller = st.session_state.get("_controller")
    if controller is not None:
        controller.logout()
    st.session_state.clear()
    st.logout()


try:
    settings = Settings.load()
    if st.get_option("server.address") != "127.0.0.1":
        raise ValueError("Hosted origin must remain private")
except Exception:
    safe_stop()

if not st.user.get("is_logged_in", False):
    # No database, controller or provider is constructed for an anonymous visitor.
    st.info("الدخول للمراجعين المدعوين فقط." if ar else "Access is for invited reviewers only.")
    label = "تسجيل الدخول" if ar else "Sign in"
    if settings.issuer == GOOGLE_ISSUER:
        label = "تسجيل الدخول باستخدام Google" if ar else "Sign in with Google"
    if st.button(label, key="hosted_login"):
        st.login("reviewer")
    st.stop()

if st.button("تسجيل الخروج" if ar else "Sign out", key="hosted_logout"):
    try:
        sign_out()
    except Exception:
        safe_stop()

try:
    store = HostedStore(Database(settings.data_dir / "customer_service.sqlite3"))
    login = authorize_native_user(st.user.to_dict(), settings, time.time(), store=store)
    previous = st.session_state.get("_controller")
    if previous and previous.login != login:
        previous.logout()
        st.session_state.clear()
    if "_controller" not in st.session_state:
        st.session_state._controller = HostedController(store, login, settings)
        st.session_state._submission_id = uuid.uuid4().hex
    controller = st.session_state._controller
    controller.validate()
except Exception:
    st.error(
        "انتهت الجلسة أو لم يُصرّح بالدخول."
        if ar
        else "Access is not permitted or your session expired."
    )
    st.stop()

st.caption(
    "عرض تجريبي ببيانات مصطنعة فقط. لا توجد طلبات عملاء محمّلة."
    if ar
    else "Synthetic demonstration only. No customer orders are preloaded."
)
enabled = controller.available
if not enabled:
    st.info(
        "المحادثة غير متاحة مؤقتًا؛ يمكنك تسجيل الخروج أو إلغاء المسودة."
        if ar
        else "Chat is temporarily unavailable; you can sign out or cancel a draft."
    )
render_chat(controller, locale, enabled=enabled)
