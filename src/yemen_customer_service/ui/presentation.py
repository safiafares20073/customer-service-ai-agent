"""Customer-facing translations and plain-text filtering; no debug/accounting views."""

import os
import re

from yemen_customer_service.agent.tracing import safe_text

COPY = {
    "en": {
        "title": "How can we help?",
        "subtitle": "Products, store policies, orders and support.",
        "disclosure": "Synthetic store and demonstration customer. "
        "Do not enter real personal information.",
        "fixture": "Scripted demonstration responses. This is not a live AI service.",
        "chat": "Ask about a product, a policy, or your order…",
        "working": "Working on your request…",
        "ready": "Ready to help",
        "done": "Request completed",
        "review": "Review your support ticket",
        "review_note": "Check the exact draft below. Nothing is created until you confirm.",
        "subject": "Subject",
        "message": "Message",
        "order": "Order ID (optional)",
        "confirm": "Confirm ticket",
        "cancel": "Cancel",
        "cancelled": "Ticket request cancelled.",
        "edited": "Draft updated. Review the current version before confirming.",
        "unavailable": "This local demonstration is unavailable. Please contact the operator.",
        "denied": "We could not verify access to that order. Please check your order details.",
        "error": "We could not complete this request. Please contact support before trying again.",
        "invalid": "Please check the subject, message and optional order ID.",
        "greeting": "Welcome! Ask about headphones, returns, or your own order.",
        "fallback": "Please contact support for help with this request.",
    },
    "ar": {
        "title": "كيف يمكننا مساعدتك؟",
        "subtitle": "المنتجات وسياسات المتجر والطلبات والدعم.",
        "disclosure": "متجر وعميل تجريبيان ببيانات مصطنعة. لا تدخل معلومات شخصية حقيقية.",
        "fixture": "ردود تجريبية معدة مسبقًا. هذه ليست خدمة ذكاء اصطناعي مباشرة.",
        "chat": "اسأل عن منتج أو سياسة المتجر أو طلبك…",
        "working": "نعمل على طلبك…",
        "ready": "جاهزون للمساعدة",
        "done": "اكتمل الطلب",
        "review": "راجع تذكرة الدعم",
        "review_note": "راجع المسودة أدناه. لن تُنشأ التذكرة حتى تؤكدها.",
        "subject": "الموضوع",
        "message": "الرسالة",
        "order": "رقم الطلب (اختياري)",
        "confirm": "تأكيد التذكرة",
        "cancel": "إلغاء",
        "cancelled": "تم إلغاء طلب التذكرة.",
        "edited": "تم تحديث المسودة. راجع النسخة الحالية قبل التأكيد.",
        "unavailable": "العرض المحلي غير متاح. يرجى التواصل مع المسؤول.",
        "denied": "تعذر التحقق من صلاحية الوصول إلى الطلب. يرجى مراجعة بيانات طلبك.",
        "error": "تعذر إكمال الطلب. يرجى التواصل مع الدعم قبل المحاولة مجددًا.",
        "invalid": "يرجى مراجعة الموضوع والرسالة ورقم الطلب الاختياري.",
        "greeting": "مرحبًا! اسأل عن السماعات أو الإرجاع أو طلبك الخاص.",
        "fallback": "يرجى التواصل مع الدعم للمساعدة في هذا الطلب.",
    },
}

INTERNAL = re.compile(
    r"api[_ -]?key|access_reference|confirmation_reference|session_token|task_id|pricing_version|"
    r"max_turns|turn_limit|budget|token usage|input.tokens|output.tokens|cost_usd|"
    r"ميزانية|رمز الوصول|تكلفة الاستدعاء|traceback|sqlite3|provider_error",
    re.I,
)


def customer_text(value: str, locale: str, *, hide_internal: bool = True) -> str:
    if hide_internal and INTERNAL.search(value):
        return COPY[locale]["fallback"]
    for key in ("OPENAI_API_KEY", "LLM_API_KEY", "CS_SESSION_TOKEN"):
        secret = os.getenv(key)
        if secret and len(secret) >= 8:
            value = value.replace(secret, "[redacted]")
    return safe_text(value)


def outcome_message(status: str, answer: str, locale: str) -> str:
    if status == "completed":
        return customer_text(answer, locale)
    if status == "confirmation_declined":
        return COPY[locale]["cancelled"]
    if status == "access_denied":
        return COPY[locale]["denied"]
    if status == "awaiting_confirmation":
        return COPY[locale]["review_note"]
    return COPY[locale]["error"]
