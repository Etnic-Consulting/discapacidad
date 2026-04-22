"""SMT-ONIC Framework Dashboard v2.1 — salud del equipo multi-agente.

NO muestra KPIs del proyecto SMT-ONIC (caracterizados, victimas, mapas).
SOLO muestra la salud de la interaccion entre clip, ollama y Wilson Herrera.

Datos: consume el API del framework en :8096 (no toca PostgreSQL).
Lanzar: streamlit run .framework/dashboard.py --server.port 8097
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8096"
REFRESH_SECS = 10

st.set_page_config(
    page_title="SMT-ONIC — Framework v2.1",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --- API helpers --------------------------------------------------------------

@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def api_get(path: str) -> dict | None:
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.session_state["_api_error"] = str(e)
        return None


def fmt_age(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


HB_COLORS = {"ok": "🟢", "warn": "🟡", "stale": "🔴", "unknown": "⚪"}


# --- Header -------------------------------------------------------------------

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
left, right = st.columns([6, 1])
with left:
    st.markdown("### 🛰️ SMT-ONIC — Framework v2.1")
    st.caption(f"Salud del equipo multi-agente · auto-refresh {REFRESH_SECS}s · {now}")
with right:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- Health check de API ------------------------------------------------------

health = api_get("/framework/health")
if not health:
    st.error(
        f"API del framework no responde en {API_BASE}. "
        "Lanzar con: `bash .framework/api/run_api.sh`"
    )
    if "_api_error" in st.session_state:
        st.code(st.session_state["_api_error"])
    st.stop()

# --- Overview -----------------------------------------------------------------

overview = api_get("/framework/overview") or {}
config = api_get("/framework/config") or {}
queue = api_get("/framework/queue") or {}
pizarra = api_get("/framework/pizarra?limit=80") or {}

director = overview.get("director", {})
agents = overview.get("agents", [])
activity = overview.get("activity", [])

# --- KPIs top -----------------------------------------------------------------

c1, c2, c3, c4, c5, c6 = st.columns(6)
qs = overview.get("queue_summary", {})
c1.metric("📋 En cola", qs.get("pending", 0))
c2.metric("🔄 En curso", qs.get("in_progress", 0))
c3.metric("✅ Completadas", qs.get("completed", 0))
c4.metric("⛔ Bloqueadas", overview.get("open_blocks", 0))
c5.metric("🛡️ Audits pendientes", overview.get("open_audit_requests", 0))
c6.metric("⚠️ Hallazgos abiertos", overview.get("open_findings", 0))

st.divider()

# --- Equipo -------------------------------------------------------------------

st.markdown("#### 👥 Equipo")

cols = st.columns(len(activity) or 1)
agent_lookup = {a["id"]: a for a in agents}
agent_lookup[director.get("id", "director")] = director

for col, act in zip(cols, activity):
    aid = act["agent"]
    info = agent_lookup.get(aid, {})
    color = info.get("color", "#888")
    name = info.get("name", aid)
    role = info.get("role", "")
    hb = HB_COLORS.get(act["heartbeat_status"], "⚪")
    with col:
        st.markdown(
            f"<div style='border-left:4px solid {color};padding-left:10px;'>"
            f"<b>{hb} {name}</b><br>"
            f"<span style='color:#888;font-size:12px'>{role}</span><br>"
            f"<span style='font-size:13px'>1h: <b>{act['messages_last_hour']}</b> · 24h: <b>{act['messages_last_24h']}</b></span><br>"
            f"<span style='color:#888;font-size:12px'>último: {fmt_age(act['seconds_since_last'])} atrás</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.divider()

# --- Tabs ---------------------------------------------------------------------

tab_pizarra, tab_queue, tab_routing, tab_costs, tab_health, tab_config = st.tabs(
    ["💬 Pizarra", "📋 Cola", "🧭 Routing", "💰 Costos", "🩺 Salud Ops", "⚙️ Config"]
)

# Pizarra (unica fuente — chat + eventos)
with tab_pizarra:
    msgs = pizarra.get("messages", [])
    st.caption(f"Mensajes: {pizarra.get('count', 0)} (más recientes primero)")
    for m in msgs:
        actor = m.get("actor") or "?"
        info = agent_lookup.get(actor, {})
        color = info.get("color", "#888")
        ts = m.get("ts") or ""
        try:
            ts_disp = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%m-%d %H:%M:%S")
        except Exception:
            ts_disp = ts
        tag = m.get("tag") or "—"
        body = (m.get("body") or "").strip()
        para = m.get("para")
        para_str = f" → {para}" if para else ""
        st.markdown(
            f"<div style='border-left:3px solid {color};padding:6px 10px;margin:4px 0;background:#f8f9fa'>"
            f"<span style='color:#666;font-size:11px'>{ts_disp}</span> "
            f"<b style='color:{color}'>{actor}</b>{para_str} "
            f"<span style='background:#222;color:#fff;padding:1px 6px;border-radius:3px;font-size:10px'>{tag}</span>"
            f"<div style='font-size:13px;margin-top:3px'>{body[:500]}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("##### 🗣️ Chat — Wilson asigna en lenguaje natural (F7)")
    chat_input = st.text_area(
        "Escribe la tarea en lenguaje natural",
        placeholder="ej: hay que arreglar el bug del feed que muestra convocatorias vencidas",
        height=80,
        key="chat_input",
    )
    if st.button("Enviar (no operativo hasta F7)"):
        st.info(
            "El endpoint POST /framework/chat se implementa en F7 "
            "(Ollama parsea NL → Claude rutea → tarea creada en cola)."
        )

# Cola
with tab_queue:
    tasks = queue.get("tasks", [])
    st.caption(
        f"Total: {queue.get('count', 0)} · "
        f"by_status: {queue.get('by_status', {})} · "
        f"bloqueadas por dependencias: {queue.get('blocked', 0)}"
    )

    by_priority = queue.get("by_priority", {})
    if by_priority:
        st.markdown("**Por prioridad** (abiertas = pending + in_progress + blocked)")
        prio_cols = st.columns(max(len(by_priority), 1))
        for col, prio in zip(prio_cols, sorted(by_priority.keys())):
            data = by_priority[prio]
            bs = data.get("by_status", {})
            open_n = bs.get("pending", 0) + bs.get("in_progress", 0) + bs.get("blocked", 0)
            done_n = bs.get("completed", 0)
            col.metric(prio, f"{open_n} abiertas", f"{done_n} ✓ / {data.get('total', 0)} total", delta_color="off")
    if tasks:
        rows = [
            {
                "id": t.get("id", ""),
                "phase": t.get("phase", ""),
                "owner": t.get("owner", ""),
                "tier": t.get("model_tier", ""),
                "P": t.get("priority", ""),
                "Q": t.get("quadrant", ""),
                "status": t.get("status", ""),
                "avance %": t.get("progress_pct", 0),
                "tiempo": t.get("elapsed_str", "—"),
                "title": (t.get("title") or "")[:80],
                "deps": ",".join(t.get("depends_on", []) or []),
            }
            for t in tasks
        ]
        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "avance %": st.column_config.ProgressColumn(
                    "avance %",
                    help="0=pending/blocked · 50=in_progress · 100=completed",
                    min_value=0,
                    max_value=100,
                    format="%d%%",
                ),
                "tiempo": st.column_config.TextColumn(
                    "tiempo",
                    help="Derivado de pizarra: desde el primer evento del task_id hasta ENTREGADO (o ahora si sigue in_progress)",
                ),
            },
        )

# Routing (preview F6)
with tab_routing:
    by_tier = queue.get("by_tier", {})
    by_owner = queue.get("by_owner", {})
    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown("**Tareas por tier**")
        st.bar_chart(by_tier or {"(vacío)": 0})
    with c_b:
        st.markdown("**Tareas por owner**")
        st.bar_chart(by_owner or {"(vacío)": 0})
    st.info("Detalle de escalados/degradados disponible en F6.")

# Costos (preview F4)
with tab_costs:
    rates_cfg = config.get("rates", {})
    budgets = (rates_cfg.get("budgets") or {})
    st.markdown("##### Tarifas vigentes (USD por millón de tokens)")
    rate_rows = [
        {
            "modelo": k,
            "tier": v.get("tier"),
            "input $/MTok": v.get("input_per_mtok"),
            "output $/MTok": v.get("output_per_mtok"),
            "cache_write ×": v.get("cache_write_multiplier"),
            "cache_read ×": v.get("cache_read_multiplier"),
            "batch ×": v.get("batch_multiplier"),
        }
        for k, v in (rates_cfg.get("models") or {}).items()
    ]
    st.dataframe(rate_rows, use_container_width=True, hide_index=True)

    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.metric("Día (warn)", f"${budgets.get('daily_warn_usd', 0):.2f}")
    cc2.metric("Día (hard)", f"${budgets.get('daily_hard_usd', 0):.2f}")
    cc3.metric("Mes (warn)", f"${budgets.get('monthly_warn_usd', 0):.2f}")
    cc4.metric("Mes (hard)", f"${budgets.get('monthly_hard_usd', 0):.2f}")
    st.info("Cálculo de costo real por llamada se implementa en F4 (cost_calculator.py).")

# Salud Ops (preview F5)
with tab_health:
    st.markdown("##### Estado de checks API")
    checks = health.get("checks", {})
    for name, ok in checks.items():
        st.write(("✅" if ok else "❌") + f" {name}")
    th = config.get("thresholds", {})
    infra = th.get("infra", {})
    st.markdown("##### Contenedores requeridos (configurado)")
    st.write(infra.get("docker_required_containers", []))
    st.markdown("##### Modelos Ollama requeridos")
    st.write(infra.get("ollama_required_models", []))
    st.info("Probes en vivo (docker ps, ollama tags, GPU temp) se implementan en F5.")

# Config (read-only)
with tab_config:
    st.caption(
        "Editar archivos en `.framework/config/*.json`. "
        "Cambios vigentes en ≤5s sin reiniciar API."
    )
    for name in ("actors", "tiers", "thresholds", "rates"):
        with st.expander(f"{name}.json", expanded=(name == "actors")):
            st.json(config.get(name, {}))

# --- Footer + auto refresh ----------------------------------------------------

st.divider()
st.caption(
    f"Director: **{director.get('name', '?')}** · "
    f"Agentes: {', '.join(a['id'] for a in agents)} · "
    f"API: {API_BASE} · "
    f"Status: {health.get('status', '?')}"
)

# auto refresh
st.markdown(
    f"<script>setTimeout(function(){{window.location.reload();}}, {REFRESH_SECS * 1000});</script>",
    unsafe_allow_html=True,
)
