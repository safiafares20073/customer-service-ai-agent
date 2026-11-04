"""Shared bilingual rendering; never include auth objects or internal counters."""

import uuid

import streamlit as st

from yemen_customer_service.ui.presentation import (
    COPY,
    SUGGESTIONS,
    assistant_markdown,
    customer_text,
    message_direction,
)


def _submit_question(controller, question, locale):
    """The same trusted submission and ID lifecycle for typed and suggested input."""
    with st.spinner(COPY[locale]["working"]):
        controller.submit(question, st.session_state._submission_id, locale)
    st.session_state._submission_id = uuid.uuid4().hex


def _submit_suggestion(controller, question, locale, *, enabled):
    if (
        not enabled
        or controller.busy
        or controller.draft is not None
        or st.session_state.get("_suggestion_used", False)
    ):
        return False
    # Claim before any work, even if the backend declines without adding a message.
    # A queued click from another button/rerun cannot consume another submission ID.
    st.session_state._suggestion_used = True
    _submit_question(controller, question, locale)
    return True


def render_header():
    st.set_page_config(page_title="Customer Care | خدمة العملاء", page_icon="💬", layout="centered")
    st.set_option("client.showErrorDetails", "none")
    language = st.radio("Language / اللغة", ["English", "العربية"], horizontal=True, key="language")
    locale = "ar" if language == "العربية" else "en"
    t = COPY[locale]
    rtl = locale == "ar"
    # Constant trusted CSS only. Never interpolate messages, drafts, or model HTML.
    st.html("""<style>
    section.main, [data-testid="stMain"] {max-width:100%;}
    [data-testid="stChatMessage"] {border-radius:12px;}
    /* Native coral background retained; dark native foreground improves contrast. */
    button[kind="primary"] [data-testid="stMarkdownContainer"],
    button[kind="primary"] p {color:#0e1117;}
    [data-testid="stChatMessageContent"] {min-width:0;overflow-wrap:anywhere;}
    [class*="st-key-assistant_rtl_"] [data-testid="stMarkdownContainer"],
    [class*="st-key-assistant_rtl_"] :is(p,ul,ol,li,h1,h2,h3,h4,h5,h6,blockquote)
        {direction:rtl!important;text-align:right!important;}
    [class*="st-key-assistant_ltr_"] [data-testid="stMarkdownContainer"],
    [class*="st-key-assistant_ltr_"] :is(p,ul,ol,li,h1,h2,h3,h4,h5,h6,blockquote)
        {direction:ltr!important;text-align:left!important;}
    [class*="st-key-assistant_"] :is(ul,ol)
        {padding-inline-start:1.5rem;padding-inline-end:0;list-style-position:outside;}
    [class*="st-key-assistant_"] code
        {direction:ltr;unicode-bidi:isolate;display:inline-block;}
    </style>""")
    if rtl:
        st.html("""<style id="customer-direction">
        .stApp {direction:rtl!important;}
        .stApp, [data-testid="stMain"], [data-testid="stChatMessage"],
        [data-testid="stChatInput"], [data-testid="stHorizontalBlock"],
        [data-testid="stAlert"], label {direction:rtl;text-align:right;}
        [data-testid="stMarkdownContainer"] {direction:rtl;text-align:right;}
        [data-testid="stChatInput"] textarea,textarea,input {direction:rtl;text-align:right;}
        [data-testid="stMarkdownContainer"] li {text-align:right;}
        </style>""")
    else:
        st.html("""<style id="customer-direction">
        .stApp {direction:ltr!important;}
        .stApp, [data-testid="stMain"], [data-testid="stChatMessage"],
        [data-testid="stChatInput"], [data-testid="stHorizontalBlock"],
        [data-testid="stAlert"], label {direction:ltr;text-align:left;}
        [data-testid="stMarkdownContainer"] {direction:ltr;text-align:left;}
        [data-testid="stChatInput"] textarea,textarea,input {direction:ltr;text-align:left;}
        </style>""")
    st.title(t["title"])
    st.caption(t["subtitle"])
    st.info(t["disclosure"])
    return locale


def render_chat(controller, locale, *, enabled=True):
    t = COPY[locale]
    rtl = locale == "ar"
    for index, (role, content) in enumerate(controller.messages):
        with st.chat_message(role):
            if role == "assistant":
                direction = message_direction(content, locale)
                with st.container(key=f"assistant_{direction}_{index}"):
                    st.markdown(
                        assistant_markdown(content, locale),
                        unsafe_allow_html=False,
                        text_alignment="right" if direction == "rtl" else "left",
                    )
            else:
                st.text(
                    customer_text(content, locale, hide_internal=False),
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

    # Suggestions stay available near the input throughout the conversation.
    # A click is claimed until a clean rerender, blocking queued second clicks.
    st.caption(t["suggested"])
    for column, (key, label, question) in zip(st.columns(3), SUGGESTIONS[locale], strict=True):
        if column.button(
            label,
            key=f"suggestion_{key}",
            disabled=not enabled or controller.busy or controller.draft is not None,
            width="stretch",
        ) and _submit_suggestion(controller, question, locale, enabled=enabled):
            st.rerun()
    st.session_state["_suggestion_used"] = False

    request = st.chat_input(
        t["chat"],
        key="customer_message",
        max_chars=2000,
        disabled=not enabled or controller.busy or draft is not None,
    )
    if request:
        _submit_question(controller, request, locale)
        st.rerun()
    if draft is None and not controller.error:
        if controller.status == "ready":
            st.caption(t["ready"])
        elif controller.status == "completed":
            st.caption(t["done"])
