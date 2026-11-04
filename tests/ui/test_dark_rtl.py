"""Presentation regression checks; computed Chromium checks are separate evidence."""

from pathlib import Path

import pytest

from yemen_customer_service.ui.presentation import assistant_markdown, message_direction


@pytest.mark.parametrize(
    "message,locale,expected",
    [
        ("السماعات متوفرة بسعر 25 USD ورقم المنتج `P-100`.", "ar", "rtl"),
        ("**Example Headphones** متوفرة لدينا مع إيصال أصلي.", "ar", "rtl"),
        ("Headphones cost USD 25 and are in stock.", "ar", "ltr"),
        ("The product سماعات is available for USD 25.", "en", "ltr"),
        ("السماعات متوفرة الآن.", "en", "rtl"),
        ("25 USD", "ar", "rtl"),
    ],
)
def test_message_direction_is_not_a_page_wide_override(message, locale, expected):
    assert message_direction(message, locale) == expected


def test_restore_native_colors_and_keep_safe_scoped_markdown():
    code = Path("src/yemen_customer_service/ui/chat.py").read_text()
    for unwanted in ["#f8fafc", "#0f172a", "#0f766e", "#ecfdf5", "color-scheme:light"]:
        assert unwanted not in code
    assert "border-radius:12px" in code
    assert "st-key-assistant_rtl_" in code and "st-key-assistant_ltr_" in code
    assert "padding-inline-start:1.5rem" in code
    assert "unsafe_allow_html=False" in code
    assert "**سماعات**" in assistant_markdown("**سماعات**\n\n- USD $25", "ar")
