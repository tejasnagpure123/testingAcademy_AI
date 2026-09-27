"""Shared Streamlit layout and status components."""

from __future__ import annotations

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
                :root {
                    --ink:#152438; --blue:#1456a0; --cyan:#2b91aa; --mint:#2d8b72;
                    --line:#d5e1ec; --paper:#f3f7fb;
                }
                .stApp {
                    background: radial-gradient(ellipse at 92% 0%, #d9eaf5 0, transparent 32%),
                        var(--paper);
                    color:var(--ink);
                }
        h1, h2, h3 { color:var(--ink); letter-spacing:0; }
        .hero-kicker { color:#1456a0; font-size:.78rem; font-weight:700; text-transform:uppercase; }
        .hero-subtitle { color:#53677b; max-width:760px; font-size:1.05rem; }
                .status-strip {
                    border-left:4px solid #2b91aa; padding:.55rem .8rem;
                    background:#e8f2f8; border-radius:2px;
                }
                div[data-testid="stMetric"] {
                    background:#fff; border:1px solid var(--line);
                    border-radius:4px; padding:.65rem .8rem;
                }
        div.stButton > button[kind="primary"] { background:#1456a0; border-color:#1456a0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_configuration_status(status: dict[str, bool | str]) -> None:
    st.subheader("Configuration")
    for label, value in status.items():
        if isinstance(value, bool):
            st.write(f"{'Ready' if value else 'Not set'} · {label}")
        else:
            st.write(f"{label}: {value}")
