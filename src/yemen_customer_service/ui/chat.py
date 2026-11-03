"""Shared bilingual rendering; never include auth objects or internal counters."""

import uuid

import streamlit as st

from yemen_customer_service.ui.presentation import COPY, customer_text


def render_header():
    st.set_page_config(page_title="Customer Care | خدمة العملاء", page_icon="💬", layout="centered")
    st.set_option("client.showErrorDetails", "none")
    language = st.radio("Language / اللغة", ["English", "العربية"], horizontal=True, key="language")
    locale = "ar" if language == "العربية" else "en"
    t = COPY[locale]
    rtl = locale == "ar"
    # Constant trusted CSS only. Never interpolate messages, drafts, or model HTML.
    st.html("""<style>
    section.main, [data-testid="stMain"] {max-width: 100%;}
    [data-testid="stChatMessage"] {border-radius: 12px;}
    </style>""")
    if rtl:
        st.html("""<style id="customer-direction">
        [data-testid="stMain"] {direction:rtl;text-align:right;}
        textarea, input {direction:rtl;text-align:right;}</style>""")
    else:
        st.html("""<style id="customer-direction">
        [data-testid="stMain"] {direction:ltr;text-align:left;}
        textarea, input {direction:ltr;text-align:left;}</style>""")
    st.title(t["title"])
    st.caption(t["subtitle"])
    st.info(t["disclosure"])
    return locale


def render_chat(controller, locale, *, enabled=True):
    t = COPY[locale]
    rtl = locale == "ar"
    for role, content in controller.messages:
        with st.chat_message(role):
            st.text(
                customer_text(content, locale, hide_internal=role != "user"),
                text_alignment="right" if rtl else "left",
            )
    if not controller.messages:
        with st.chat_message("assistant"):
            st.text(t["greeting"], text_alignment="right" if rtl else "left")

    if controller.error:
        st.warning(controller.error)

    draft = controller.draft
    if draft is not None:
        st.subheader(t["review"])
        st.info(t["review_note"])
        # Stable widget keys for the current draft; no internal task/reference values.
        if st.session_state.get("_draft_generation") != controller.revision:
            st.session_state.draft_subject = draft["subject"]
            st.session_state.draft_message = draft["message"]
            st.session_state.draft_order = draft["order_id"]
            st.session_state._draft_generation = controller.revision

        def edited():
            valid = controller.edit(
                st.session_state.draft_subject,
                st.session_state.draft_message,
                st.session_state.draft_order,
                locale,
            )
            if valid:
                current = controller.draft
                st.session_state.draft_subject = current["subject"]
                st.session_state.draft_message = current["message"]
                st.session_state.draft_order = current["order_id"]
            st.session_state._draft_generation = controller.revision

        st.text_input(t["subject"], key="draft_subject", max_chars=120, on_change=edited)
        st.text_area(t["message"], key="draft_message", max_chars=2000, on_change=edited)
        st.text_input(t["order"], key="draft_order", max_chars=64, on_change=edited)
        left, right = st.columns(2)
        if left.button(
            t["confirm"],
            type="primary",
            disabled=not enabled or bool(controller.error) or controller.busy,
            key="confirm_ticket",
            width="stretch",
        ):
            with st.spinner(t["working"]):
                controller.decide(confirm=True, revision=controller.revision, locale=locale)
            st.rerun()
        if right.button(
            t["cancel"], disabled=controller.busy, key="cancel_ticket", width="stretch"
        ):
            with st.spinner(t["working"]):
                controller.decide(confirm=False, revision=controller.revision, locale=locale)
            st.rerun()

    request = st.chat_input(
        t["chat"],
        key="customer_message",
        max_chars=2000,
        disabled=not enabled or controller.busy or draft is not None,
    )
    if request:
        with st.spinner(t["working"]):
            controller.submit(request, st.session_state._submission_id, locale)
        st.session_state._submission_id = uuid.uuid4().hex
        st.rerun()
    if draft is None and not controller.error:
        if controller.status == "ready":
            st.caption(t["ready"])
        elif controller.status == "completed":
            st.caption(t["done"])
