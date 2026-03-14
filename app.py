# ══════════════════════════════════════════════════════════════════
#  Anilma Site Operations Manager  —  Python / Streamlit Edition
#  Run with:  streamlit run app.py
# ══════════════════════════════════════════════════════════════════

import streamlit as st
import hashlib
from datetime import date, datetime

# ── Page config (must be first Streamlit call) ────────────────────
st.set_page_config(
    page_title="Anilma Site Ops",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Try importing pyrebase4 ───────────────────────────────────────
try:
    import pyrebase4 as pyrebase
    PYREBASE_OK = True
except ImportError:
    PYREBASE_OK = False

# ─────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────────────────────────

TODAY = date.today().isoformat()

FIREBASE_CONFIG = {
    "apiKey":            "AIzaSyAzd_8Pi6VkQ0mWNVuuSZMADV0ZHPuqeDM",
    "authDomain":        "anilma-operations.firebaseapp.com",
    "databaseURL":       "https://anilma-operations-default-rtdb.europe-west1.firebasedatabase.app",
    "projectId":         "anilma-operations",
    "storageBucket":     "anilma-operations.firebasestorage.app",
    "messagingSenderId": "926744167711",
    "appId":             "1:926744167711:web:b41cbf99dd2f8e124e5c2a"
}

# Financial data is stored locally — never sent to Firebase
LOCAL_FINANCIAL = {
    "1": {"budget": 85_000_000, "spent": 12_750_000},
    "2": {"budget": 45_000_000, "spent": 30_600_000},
    "3": {"budget": 28_000_000, "spent": 22_960_000},
}

COO_DEFAULT_PASSWORD = "Anilma@2024"

SEED = {
    "sites": {
        "1": {"id":"1","name":"Marina Tower","type":"new","location":"Marina District",
              "startDate":"2025-01-15","targetDate":"2026-12-31","progress":15,
              "description":"42-floor residential tower"},
        "2": {"id":"2","name":"Harbour Bridge Retrofit","type":"ongoing","location":"Harbour District",
              "startDate":"2023-06-01","targetDate":"2026-06-30","progress":68,
              "description":"Structural reinforcement project"},
        "3": {"id":"3","name":"Westside Commercial Hub","type":"ongoing","location":"West Business Park",
              "startDate":"2022-03-10","targetDate":"2026-05-15","progress":82,
              "description":"Mixed-use commercial complex"},
    },
    "works": {
        "1": {"id":"1","siteId":"1","task":"Excavation Level B2","date":TODAY,
              "status":"in-progress","assignedTo":"Team Alpha","priority":"high","notes":""},
        "2": {"id":"2","siteId":"1","task":"Rebar installation Column Grid A","date":TODAY,
              "status":"pending","assignedTo":"Team Beta","priority":"high","notes":""},
        "3": {"id":"3","siteId":"2","task":"Concrete pouring – Section 7","date":TODAY,
              "status":"completed","assignedTo":"Team Gamma","priority":"medium","notes":""},
        "4": {"id":"4","siteId":"3","task":"Facade cladding west wing","date":TODAY,
              "status":"in-progress","assignedTo":"Team Delta","priority":"medium","notes":""},
    },
    "milestones": {
        "1": {"id":"1","siteId":"1","milestone":"Foundation Complete",
              "targetDate":"2026-04-30","completion":45,"status":"in-progress"},
        "2": {"id":"2","siteId":"1","milestone":"Structure to Level 10",
              "targetDate":"2026-09-30","completion":0,"status":"pending"},
        "3": {"id":"3","siteId":"2","milestone":"Bridge Deck Reinforcement",
              "targetDate":"2026-03-31","completion":78,"status":"in-progress"},
        "4": {"id":"4","siteId":"3","milestone":"Interior Fit-Out Complete",
              "targetDate":"2026-04-15","completion":91,"status":"in-progress"},
    },
    "materials": {
        "1": {"id":"1","siteId":"1","name":"Portland Cement","qty":320,"unit":"bags",
              "minStock":500,"category":"Concrete","supplier":"BuildCo"},
        "2": {"id":"2","siteId":"1","name":"Steel Rebar 16mm","qty":18,"unit":"tons",
              "minStock":20,"category":"Steel","supplier":"SteelPro"},
        "3": {"id":"3","siteId":"2","name":"Structural Steel","qty":145,"unit":"tons",
              "minStock":100,"category":"Steel","supplier":"SteelPro"},
        "4": {"id":"4","siteId":"3","name":"Glass Panels","qty":12,"unit":"pcs",
              "minStock":50,"category":"Facade","supplier":"GlassTech"},
    },
    "personnel": {
        "1":  {"id":"1","siteId":"1","name":"Robert Chen","role":"Site Foreman",
               "present":True,"contact":"+1 555-0101"},
        "2":  {"id":"2","siteId":"1","name":"Sarah Williams","role":"Safety Officer",
               "present":True,"contact":"+1 555-0102"},
        "3":  {"id":"3","siteId":"1","name":"Mike Torres","role":"Crane Operator",
               "present":False,"contact":"+1 555-0103"},
        "4":  {"id":"4","siteId":"1","name":"James Liu","role":"Project Manager",
               "present":True,"contact":"+1 555-0104"},
        "5":  {"id":"5","siteId":"2","name":"Ana Gomez","role":"Site Foreman",
               "present":True,"contact":"+1 555-0201"},
        "6":  {"id":"6","siteId":"2","name":"David Park","role":"Project Manager",
               "present":True,"contact":"+1 555-0202"},
        "7":  {"id":"7","siteId":"3","name":"Michael O'Brien","role":"Project Manager",
               "present":True,"contact":"+1 555-0301"},
        "8":  {"id":"8","siteId":"3","name":"Elena Vasquez","role":"Safety Officer",
               "present":False,"contact":"+1 555-0302"},
    },
    "incidents": {
        "1": {"id":"1","siteId":"1","type":"near-miss",
              "description":"Unsecured rebar end on Level 2",
              "date":"2026-03-10","severity":"low","resolved":True},
        "2": {"id":"2","siteId":"2","type":"delay",
              "description":"Crane mechanical fault – 2 hr downtime",
              "date":"2026-03-09","severity":"medium","resolved":True},
        "3": {"id":"3","siteId":"3","type":"quality",
              "description":"Concrete slump test failed – Batch #44",
              "date":"2026-03-08","severity":"high","resolved":False},
    },
}

# ─────────────────────────────────────────────────────────────────
#  FIREBASE HELPERS
# ─────────────────────────────────────────────────────────────────

@st.cache_resource
def get_db():
    if not PYREBASE_OK:
        return None
    try:
        firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
        return firebase.database()
    except Exception:
        return None

db = get_db()

def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def fb_list(path: str) -> list:
    if not db:
        return []
    try:
        result = db.child(path).get()
        val = result.val()
        if not val:
            return []
        if isinstance(val, dict):
            items = []
            for k, v in val.items():
                if isinstance(v, dict):
                    items.append({"id": k, **v})
            return items
        elif isinstance(val, list):
            items = []
            for i, v in enumerate(val):
                if v and isinstance(v, dict):
                    items.append({"id": str(i), **v})
            return items
        return []
    except Exception:
        return []

def fb_push(path: str, data: dict):
    if not db:
        return None
    try:
        return db.child(path).push(data)
    except Exception as e:
        st.error(f"Save failed: {e}")

def fb_set(path: str, data):
    if not db:
        return
    try:
        db.child(path).set(data)
    except Exception as e:
        st.error(f"Set failed: {e}")

def fb_update(path: str, data: dict):
    if not db:
        return
    try:
        db.child(path).update(data)
    except Exception as e:
        st.error(f"Update failed: {e}")

def fb_remove(path: str):
    if not db:
        return
    try:
        db.child(path).remove()
    except Exception as e:
        st.error(f"Delete failed: {e}")

def fb_get_val(path: str):
    if not db:
        return None
    try:
        return db.child(path).get().val()
    except Exception:
        return None

def seed_db():
    if not db:
        return
    try:
        seeded = fb_get_val("_seeded")
        if seeded:
            return
        for collection, items in SEED.items():
            for item_id, item in items.items():
                db.child(collection).child(item_id).set(item)
        # Seed default COO credential
        db.child("credentials").child("coo_default").set({
            "id": "coo_default",
            "name": "COO – Anilma",
            "username": "coo",
            "passwordHash": hash_pw(COO_DEFAULT_PASSWORD),
            "role": "coo",
            "siteId": None,
            "active": True,
            "createdAt": TODAY
        })
        fb_set("_seeded", True)
    except Exception:
        pass

# ─────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────

def stock_status(qty, min_stock):
    try:
        r = float(qty) / float(min_stock)
        return "critical" if r < 0.8 else "low" if r < 1.0 else "ok"
    except Exception:
        return "ok"

def fmt_money(n):
    try:
        return f"${float(n):,.0f}"
    except Exception:
        return "$0"

def badge(text, kind="default"):
    colours = {
        "completed":  ("#dcfce7", "#16a34a"),
        "in-progress":("#dbeafe", "#2563eb"),
        "pending":    ("#f1f5f9", "#64748b"),
        "ok":         ("#dcfce7", "#16a34a"),
        "low":        ("#fef3c7", "#d97706"),
        "critical":   ("#fee2e2", "#dc2626"),
        "high":       ("#fee2e2", "#dc2626"),
        "medium":     ("#fef3c7", "#d97706"),
        "resolved":   ("#dcfce7", "#16a34a"),
        "open":       ("#fee2e2", "#dc2626"),
        "active":     ("#dcfce7", "#16a34a"),
        "disabled":   ("#f1f5f9", "#94a3b8"),
        "foreman":    ("#ffedd5", "#c2410c"),
        "pm":         ("#dbeafe", "#1d4ed8"),
        "coo":        ("#f3e8ff", "#7c3aed"),
        "approved":   ("#dcfce7", "#16a34a"),
        "ordered":    ("#dbeafe", "#2563eb"),
        "default":    ("#f1f5f9", "#64748b"),
    }
    bg, fg = colours.get(text, colours.get(kind, colours["default"]))
    return f'<span style="background:{bg};color:{fg};padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;white-space:nowrap">{text}</span>'

def kpi(label, value, sub=""):
    st.markdown(f"""
    <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:18px 20px;margin-bottom:4px">
        <p style="color:#94a3b8;font-size:10px;font-weight:700;text-transform:uppercase;
                  letter-spacing:1px;margin:0 0 4px">{label}</p>
        <p style="color:#0f172a;font-size:26px;font-weight:800;margin:0">{value}</p>
        <p style="color:#94a3b8;font-size:11px;margin:4px 0 0">{sub}</p>
    </div>""", unsafe_allow_html=True)

def prog_bar(pct, colour="#3b82f6"):
    p = max(0, min(int(pct), 100))
    st.markdown(f"""
    <div style="background:#f1f5f9;border-radius:99px;height:7px;overflow:hidden;margin:4px 0">
        <div style="background:{colour};height:7px;width:{p}%;border-radius:99px"></div>
    </div>""", unsafe_allow_html=True)

def divider():
    st.markdown("<hr style='border:none;border-top:1px solid #f1f5f9;margin:12px 0'>",
                unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────

for key, default in {
    "user": None,
    "fin": dict(LOCAL_FINANCIAL),
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Seed on first load
if db and "seeded" not in st.session_state:
    seed_db()
    st.session_state["seeded"] = True

# ─────────────────────────────────────────────────────────────────
#  LOGIN SCREEN
# ─────────────────────────────────────────────────────────────────

def show_login():
    st.markdown("""
    <div style="text-align:center;padding:50px 0 20px">
        <div style="font-size:3.5rem">🏗️</div>
        <h1 style="margin:8px 0 4px;font-size:1.9rem;color:#0f172a">Anilma Site Operations</h1>
        <p style="color:#94a3b8;margin:0">Sign in with your credentials</p>
    </div>""", unsafe_allow_html=True)

    if not PYREBASE_OK:
        st.error("⚠️ pyrebase4 is not installed. Run: pip install pyrebase4")
        return

    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login"):
            username = st.text_input("Username", placeholder="Enter your username",
                                     autocomplete="username")
            password = st.text_input("Password", type="password",
                                     placeholder="Enter your password",
                                     autocomplete="current-password")
            submitted = st.form_submit_button("Sign In →", use_container_width=True,
                                              type="primary")

        if submitted:
            if not username.strip() or not password:
                st.error("Please enter both username and password.")
            else:
                credentials = fb_list("credentials")
                hashed = hash_pw(password)
                cred = next(
                    (c for c in credentials
                     if c.get("username", "").lower() == username.lower().strip()
                     and c.get("passwordHash") == hashed
                     and c.get("active", True) is not False),
                    None
                )
                if not cred:
                    st.error("⚠️ Incorrect username or password.")
                else:
                    role = cred.get("role", "foreman")
                    site = None
                    if role != "coo":
                        sites = fb_list("sites")
                        site = next((s for s in sites if s["id"] == cred.get("siteId")), None)
                        if not site:
                            st.error("Your assigned site was not found. Contact your COO.")
                            return
                    st.session_state.user = {
                        "username": cred["username"],
                        "name":     cred.get("name", username),
                        "role":     role,
                        "site":     site,
                        "siteId":   cred.get("siteId"),
                    }
                    st.rerun()

        st.markdown("""
        <p style="text-align:center;color:#94a3b8;font-size:12px;margin-top:8px">
            Credentials are provided by your COO.<br>
            <b>Default COO login:</b> username <code>coo</code> · password <code>Anilma@2024</code>
        </p>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
#  COO ▸ DASHBOARD TAB
# ─────────────────────────────────────────────────────────────────

def tab_dashboard(sites, works, milestones, materials, personnel, incidents, requests):
    today_works  = [w for w in works      if w.get("date") == TODAY]
    low_stock    = [m for m in materials  if stock_status(m.get("qty",0), m.get("minStock",1)) != "ok"]
    open_inc     = [i for i in incidents  if not i.get("resolved")]
    done_today   = [w for w in today_works if w.get("status") == "completed"]
    all_present  = [p for p in personnel  if p.get("present")]
    pending_reqs = [r for r in requests   if r.get("status") == "pending"]

    # Alerts
    if open_inc:
        st.error(f"⚠️ {len(open_inc)} unresolved incident{'s' if len(open_inc)>1 else ''} — action required")
    if pending_reqs:
        st.warning(f"📝 {len(pending_reqs)} material request{'s' if len(pending_reqs)>1 else ''} awaiting your approval — go to Requests tab")

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Active Sites",   len(sites),                          "All operational")
    with c2: kpi("On Site Today",  len(all_present),                    f"of {len(personnel)} registered")
    with c3: kpi("Stock Alerts",   len(low_stock),                      "Items below threshold")
    with c4: kpi("Tasks Today",    f"{len(done_today)}/{len(today_works)}", "Completed")

    st.markdown("### Site Overview")
    cols = st.columns(max(len(sites), 1))
    for i, site in enumerate(sites):
        fin  = st.session_state.fin.get(site["id"], {})
        sp   = [p for p in personnel if p.get("siteId") == site["id"]]
        sw   = [w for w in today_works if w.get("siteId") == site["id"]]
        ms   = next((m for m in milestones if m.get("siteId") == site["id"]
                     and m.get("status") == "in-progress"), None)
        pr   = len([p for p in sp if p.get("present")])
        done = len([w for w in sw if w.get("status") == "completed"])
        active = len([w for w in sw if w.get("status") == "in-progress"])
        pct  = int(site.get("progress", 0))
        colour = "#22c55e" if pct > 70 else "#3b82f6" if pct > 30 else "#f59e0b"

        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{site['name']}**")
                st.caption(f"📍 {site.get('location','')}")
                prog_bar(pct, colour)
                st.caption(f"Progress: {pct}%")
                if ms:
                    st.caption(f"📌 {ms.get('milestone')} — {ms.get('completion')}%")
                if fin.get("budget"):
                    ca, cb = st.columns(2)
                    ca.metric("Budget",    fmt_money(fin["budget"]))
                    cb.metric("Spent",     fmt_money(fin["spent"]))
                ca2, cb2, cc2 = st.columns(3)
                ca2.metric("On Site", f"{pr}/{len(sp)}")
                cb2.metric("Done",    done)
                cc2.metric("Active",  active)

    st.divider()
    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("#### 📋 Today's Works")
        if today_works:
            for w in today_works:
                s = next((x for x in sites if x["id"] == w.get("siteId")), {})
                ca, cb = st.columns([4, 1])
                ca.markdown(f"**{w.get('task')}**  \n*{s.get('name','')} · {w.get('assignedTo','')}*")
                cb.markdown(badge(w.get("status", "pending")), unsafe_allow_html=True)
        else:
            st.info("No tasks planned for today")

    with c_right:
        st.markdown("#### 🏁 Upcoming Milestones")
        upcoming = [m for m in milestones if m.get("status") != "completed"][:5]
        for m in upcoming:
            s = next((x for x in sites if x["id"] == m.get("siteId")), {})
            st.markdown(f"**{m.get('milestone')}**  \n*{s.get('name','')} · target: {m.get('targetDate','')}*")
            prog_bar(m.get("completion", 0))
            st.caption(f"{m.get('completion', 0)}% complete")

    if low_stock:
        st.divider()
        st.markdown("#### 📦 Materials Requiring Attention")
        for m in low_stock:
            s   = next((x for x in sites if x["id"] == m.get("siteId")), {})
            st_s = stock_status(m.get("qty", 0), m.get("minStock", 1))
            ca, cb, cc, cd, ce = st.columns([3, 2, 1, 1, 1])
            ca.markdown(f"**{m.get('name')}**")
            cb.caption(s.get("name", ""))
            cc.markdown(f"{m.get('qty')} {m.get('unit','')}")
            cd.caption(f"min: {m.get('minStock')}")
            ce.markdown(badge(st_s), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
#  COO ▸ SITES TAB
# ─────────────────────────────────────────────────────────────────

def tab_sites(sites):
    ca, cb = st.columns([5, 1])
    ca.markdown(f"**{len(sites)} sites registered**")
    if cb.button("➕ Add Site", type="primary", use_container_width=True):
        st.session_state["add_site"] = True

    if st.session_state.get("add_site"):
        with st.form("add_site"):
            st.subheader("Add New Site")
            c1, c2 = st.columns(2)
            s_name   = c1.text_input("Site Name *")
            s_type   = c2.selectbox("Type", ["new", "ongoing", "finishing"])
            location = st.text_input("Location *")
            c3, c4   = st.columns(2)
            s_start  = c3.date_input("Start Date", value=date.today())
            s_target = c4.date_input("Target Date", value=date.today())
            progress = st.slider("Current Progress %", 0, 100, 0)
            desc     = st.text_area("Description")
            st.markdown("**💰 Financial (COO-only — never shared)**")
            c5, c6 = st.columns(2)
            budget = c5.number_input("Budget ($)", min_value=0, value=0, step=100_000)
            spent  = c6.number_input("Amount Spent ($)", min_value=0, value=0, step=10_000)
            cs, cc = st.columns(2)
            if cs.form_submit_button("Add Site", type="primary", use_container_width=True):
                if s_name and location:
                    new_ref = fb_push("sites", {
                        "name": s_name, "type": s_type, "location": location,
                        "startDate": s_start.isoformat(), "targetDate": s_target.isoformat(),
                        "progress": progress, "description": desc
                    })
                    if new_ref and budget > 0:
                        new_id = new_ref["name"]
                        st.session_state.fin[new_id] = {"budget": budget, "spent": spent}
                    st.session_state["add_site"] = False
                    st.success("✅ Site added!")
                    st.rerun()
                else:
                    st.error("Name and Location are required.")
            if cc.form_submit_button("Cancel", use_container_width=True):
                st.session_state["add_site"] = False
                st.rerun()

    for site in sites:
        fin = st.session_state.fin.get(site["id"], {})
        pct = int(site.get("progress", 0))
        colour = "#22c55e" if pct > 70 else "#3b82f6" if pct > 30 else "#f59e0b"
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f"### {site['name']}")
            c2.markdown(badge(site.get("type",""), "default"), unsafe_allow_html=True)
            prog_bar(pct, colour)
            st.caption(f"{pct}% complete")
            ca, cb, cc, cd = st.columns(4)
            ca.caption(f"📍 {site.get('location','')}")
            cb.caption(f"Start: {site.get('startDate','')}")
            cc.caption(f"Target: {site.get('targetDate','')}")
            cd.caption(site.get("description",""))
            if fin.get("budget"):
                cf1, cf2, cf3 = st.columns(3)
                cf1.metric("Budget",    fmt_money(fin["budget"]))
                cf2.metric("Spent",     fmt_money(fin["spent"]))
                cf3.metric("Remaining", fmt_money(fin["budget"] - fin["spent"]))

            # Edit form inside expander
            with st.expander("✏️ Edit this site"):
                with st.form(f"edit_site_{site['id']}"):
                    ec1, ec2 = st.columns(2)
                    e_name   = ec1.text_input("Name",     value=site.get("name",""))
                    e_type   = ec2.selectbox("Type", ["new","ongoing","finishing"],
                                            index=["new","ongoing","finishing"].index(site.get("type","new")))
                    e_loc    = st.text_input("Location",  value=site.get("location",""))
                    ec3, ec4 = st.columns(2)
                    e_prog   = ec3.slider("Progress %", 0, 100, pct)
                    e_desc   = ec4.text_input("Description", value=site.get("description",""))
                    if fin.get("budget"):
                        ef1, ef2 = st.columns(2)
                        e_bud = ef1.number_input("Budget", value=float(fin["budget"]), step=100_000.0)
                        e_spt = ef2.number_input("Spent",  value=float(fin["spent"]),  step=10_000.0)
                    else:
                        e_bud = e_spt = 0
                    if st.form_submit_button("Save Changes", type="primary"):
                        fb_update(f"sites/{site['id']}", {
                            "name": e_name, "type": e_type, "location": e_loc,
                            "progress": e_prog, "description": e_desc
                        })
                        if e_bud > 0:
                            st.session_state.fin[site["id"]] = {"budget": e_bud, "spent": e_spt}
                        st.success("Saved!")
                        st.rerun()

            if st.button(f"🗑️ Delete {site['name']}", key=f"del_site_{site['id']}",
                         help="Permanently delete this site"):
                confirm_key = f"confirm_del_{site['id']}"
                if st.session_state.get(confirm_key):
                    fb_remove(f"sites/{site['id']}")
                    st.session_state.fin.pop(site["id"], None)
                    st.success("Site deleted.")
                    st.rerun()
                else:
                    st.session_state[confirm_key] = True
                    st.warning("⚠️ Click delete again to confirm.")

# ─────────────────────────────────────────────────────────────────
#  COO ▸ WORKS TAB
# ─────────────────────────────────────────────────────────────────

def tab_works(sites, works):
    site_map = {s["id"]: s["name"] for s in sites}

    c1, c2, c3 = st.columns([2, 2, 1])
    d_filter  = c1.date_input("Date", value=date.today())
    s_options = ["All Sites"] + [s["name"] for s in sites]
    s_filter  = c2.selectbox("Site", s_options)
    if c3.button("➕ Add Task", type="primary", use_container_width=True):
        st.session_state["add_work"] = True

    if st.session_state.get("add_work"):
        with st.form("add_work"):
            task     = st.text_input("Task Description *")
            c1f, c2f = st.columns(2)
            site_id  = c1f.selectbox("Site", list(site_map.keys()),
                                     format_func=lambda x: site_map[x])
            assigned = c2f.text_input("Assigned To")
            c3f, c4f, c5f = st.columns(3)
            w_date   = c3f.date_input("Date", value=date.today())
            priority = c4f.selectbox("Priority", ["high", "medium", "low"])
            notes    = c5f.text_input("Notes (optional)")
            cs, cc = st.columns(2)
            if cs.form_submit_button("Add Task", type="primary", use_container_width=True) and task:
                fb_push("works", {
                    "task": task, "siteId": site_id, "assignedTo": assigned,
                    "date": w_date.isoformat(), "priority": priority,
                    "notes": notes, "status": "pending"
                })
                st.session_state["add_work"] = False
                st.success("Task added!")
                st.rerun()
            if cc.form_submit_button("Cancel", use_container_width=True):
                st.session_state["add_work"] = False
                st.rerun()

    filtered = [w for w in works if w.get("date") == d_filter.isoformat()]
    if s_filter != "All Sites":
        sid = next((k for k, v in site_map.items() if v == s_filter), None)
        filtered = [w for w in filtered if w.get("siteId") == sid]

    STATUS_CYCLE = {"pending": "in-progress", "in-progress": "completed", "completed": "pending"}

    for w in filtered:
        s = next((x for x in sites if x["id"] == w.get("siteId")), {})
        with st.container(border=True):
            ca, cb, cc, cd = st.columns([4, 2, 1, 1])
            ca.markdown(f"**{w.get('task')}**  \n*{s.get('name','')} · {w.get('assignedTo','')}*")
            ca.markdown(badge(w.get("priority","medium")), unsafe_allow_html=True)
            cb.markdown(badge(w.get("status","pending")), unsafe_allow_html=True)
            if cc.button("↻", key=f"cyc_{w['id']}", help="Cycle status"):
                fb_update(f"works/{w['id']}",
                          {"status": STATUS_CYCLE.get(w.get("status","pending"), "pending")})
                st.rerun()
            if cd.button("🗑", key=f"del_w_{w['id']}"):
                fb_remove(f"works/{w['id']}")
                st.rerun()

    if not filtered:
        st.info("No works found. Click '+ Add Task' to add one.")

# ─────────────────────────────────────────────────────────────────
#  COO ▸ MILESTONES TAB
# ─────────────────────────────────────────────────────────────────

def tab_milestones(sites, milestones):
    site_map = {s["id"]: s["name"] for s in sites}
    c1, c2 = st.columns([3, 1])
    s_filter = c1.selectbox("Site", ["All Sites"] + [s["name"] for s in sites])
    if c2.button("➕ Add Milestone", type="primary", use_container_width=True):
        st.session_state["add_ms"] = True

    if st.session_state.get("add_ms"):
        with st.form("add_ms"):
            ms_name  = st.text_input("Milestone Name *")
            c1f, c2f = st.columns(2)
            ms_site  = c1f.selectbox("Site", list(site_map.keys()),
                                     format_func=lambda x: site_map[x])
            ms_date  = c2f.date_input("Target Date", value=date.today())
            ms_prog  = st.slider("Current Completion %", 0, 100, 0)
            cs, cc = st.columns(2)
            if cs.form_submit_button("Add Milestone", type="primary", use_container_width=True) and ms_name:
                status = "completed" if ms_prog==100 else "in-progress" if ms_prog>0 else "pending"
                fb_push("milestones", {
                    "milestone": ms_name, "siteId": ms_site,
                    "targetDate": ms_date.isoformat(),
                    "completion": ms_prog, "status": status
                })
                st.session_state["add_ms"] = False
                st.success("Milestone added!")
                st.rerun()
            if cc.form_submit_button("Cancel", use_container_width=True):
                st.session_state["add_ms"] = False
                st.rerun()

    for site in sites:
        if s_filter != "All Sites" and site["name"] != s_filter:
            continue
        site_ms = [m for m in milestones if m.get("siteId") == site["id"]]
        if not site_ms:
            continue
        st.subheader(site["name"])
        for m in site_ms:
            with st.container(border=True):
                ca, cb = st.columns([5, 1])
                ca.markdown(f"**{m.get('milestone')}**  \n*Target: {m.get('targetDate','')}*")
                pct = int(m.get("completion", 0))
                cb.markdown(f"**{pct}%**")
                prog_bar(pct)
                new_pct = st.slider("Update", 0, 100, pct,
                                    key=f"ms_sl_{m['id']}", label_visibility="hidden")
                if new_pct != pct:
                    status = "completed" if new_pct==100 else "in-progress" if new_pct>0 else "pending"
                    fb_update(f"milestones/{m['id']}",
                              {"completion": new_pct, "status": status})
                    st.rerun()

# ─────────────────────────────────────────────────────────────────
#  COO ▸ MATERIALS TAB
# ─────────────────────────────────────────────────────────────────

def tab_materials(sites, materials):
    site_map = {s["id"]: s["name"] for s in sites}
    c1, c2 = st.columns([4, 1])
    s_filter = c1.selectbox("Site", ["All Sites"] + [s["name"] for s in sites])
    if c2.button("➕ Add Material", type="primary", use_container_width=True):
        st.session_state["add_mat"] = True

    if st.session_state.get("add_mat"):
        with st.form("add_mat"):
            c1f, c2f = st.columns(2)
            m_name   = c1f.text_input("Material Name *")
            m_site   = c2f.selectbox("Site", list(site_map.keys()),
                                     format_func=lambda x: site_map[x])
            c3f, c4f, c5f, c6f = st.columns(4)
            m_qty    = c3f.number_input("Current Qty", min_value=0.0, value=0.0)
            m_unit   = c4f.selectbox("Unit", ["m³","tons","pcs","m","m²","kg","L","bags"])
            m_min    = c5f.number_input("Min Stock", min_value=0.0, value=0.0)
            m_sup    = c6f.text_input("Supplier")
            cs, cc = st.columns(2)
            if cs.form_submit_button("Add", type="primary", use_container_width=True) and m_name:
                fb_push("materials", {
                    "name": m_name, "siteId": m_site, "qty": m_qty,
                    "unit": m_unit, "minStock": m_min, "supplier": m_sup, "category": ""
                })
                st.session_state["add_mat"] = False
                st.rerun()
            if cc.form_submit_button("Cancel", use_container_width=True):
                st.session_state["add_mat"] = False
                st.rerun()

    filtered = materials
    if s_filter != "All Sites":
        sid = next((k for k, v in site_map.items() if v == s_filter), None)
        filtered = [m for m in materials if m.get("siteId") == sid]

    for m in filtered:
        s    = next((x for x in sites if x["id"] == m.get("siteId")), {})
        st_s = stock_status(m.get("qty", 0), m.get("minStock", 1))
        with st.container(border=True):
            ca, cb = st.columns([4, 1])
            ca.markdown(f"**{m.get('name')}**  \n*{s.get('name','')} · {m.get('supplier','')}*")
            cb.markdown(badge(st_s), unsafe_allow_html=True)
            pct = min(int(float(m.get("qty",0)) / max(float(m.get("minStock",1)),1) * 100), 100)
            colour = "#ef4444" if st_s=="critical" else "#f59e0b" if st_s=="low" else "#22c55e"
            prog_bar(pct, colour)
            cc2, cd2 = st.columns([2, 3])
            cc2.caption(f"Stock: {m.get('qty')} {m.get('unit','')}  |  Min: {m.get('minStock')}")
            with st.form(f"qty_f_{m['id']}"):
                cf1, cf2 = st.columns([2, 1])
                new_qty = cf1.number_input("Update Qty", value=float(m.get("qty",0)),
                                           min_value=0.0, label_visibility="visible")
                if cf2.form_submit_button("Save", use_container_width=True):
                    fb_update(f"materials/{m['id']}", {"qty": new_qty})
                    st.rerun()

# ─────────────────────────────────────────────────────────────────
#  COO ▸ REQUESTS TAB
# ─────────────────────────────────────────────────────────────────

def tab_requests(sites, requests):
    pending = [r for r in requests if r.get("status") == "pending"]
    others  = [r for r in requests if r.get("status") != "pending"]

    if pending:
        st.markdown(f"#### ⏳ Pending Approval ({len(pending)})")
        for r in pending:
            s = next((x for x in sites if x["id"] == r.get("siteId")), {})
            with st.container(border=True):
                ca, cb, cc = st.columns([5, 1, 1])
                ca.markdown(
                    f"**{r.get('name')}** — {r.get('qty')} {r.get('unit','')}  \n"
                    f"*{s.get('name','')} · by {r.get('requestedBy','')} · {r.get('date','')}*"
                )
                if r.get("notes"):
                    ca.caption(f"📝 {r['notes']}")
                if cb.button("✓ Approve", key=f"apr_{r['id']}", type="primary"):
                    fb_update(f"materialRequests/{r['id']}", {"status": "approved"})
                    st.rerun()
                if cc.button("Ordered", key=f"ord_{r['id']}"):
                    fb_update(f"materialRequests/{r['id']}", {"status": "ordered"})
                    st.rerun()
    else:
        st.info("No pending requests from field staff.")

    if others:
        st.divider()
        st.markdown("#### ✅ Approved / Ordered")
        for r in others:
            s = next((x for x in sites if x["id"] == r.get("siteId")), {})
            ca, cb = st.columns([5, 1])
            ca.markdown(
                f"**{r.get('name')}** — {r.get('qty')} {r.get('unit','')}  \n"
                f"*{s.get('name','')} · {r.get('date','')}*"
            )
            cb.markdown(badge(r.get("status","approved")), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
#  COO ▸ PERSONNEL TAB
# ─────────────────────────────────────────────────────────────────

def tab_personnel(sites, personnel):
    site_map = {s["id"]: s["name"] for s in sites}
    c1, c2 = st.columns([4, 1])
    s_filter = c1.selectbox("Site", ["All Sites"] + [s["name"] for s in sites])
    if c2.button("➕ Add Person", type="primary", use_container_width=True):
        st.session_state["add_per"] = True

    if st.session_state.get("add_per"):
        with st.form("add_per"):
            c1f, c2f = st.columns(2)
            p_name   = c1f.text_input("Full Name *")
            p_role   = c2f.text_input("Role (e.g. Site Foreman)")
            c3f, c4f = st.columns(2)
            p_site   = c3f.selectbox("Site", list(site_map.keys()),
                                     format_func=lambda x: site_map[x])
            p_con    = c4f.text_input("Contact Number")
            cs, cc = st.columns(2)
            if cs.form_submit_button("Add Person", type="primary", use_container_width=True) and p_name:
                fb_push("personnel", {
                    "name": p_name, "role": p_role, "siteId": p_site,
                    "contact": p_con, "present": True
                })
                st.session_state["add_per"] = False
                st.rerun()
            if cc.form_submit_button("Cancel", use_container_width=True):
                st.session_state["add_per"] = False
                st.rerun()

    for site in sites:
        if s_filter != "All Sites" and site["name"] != s_filter:
            continue
        sp = [p for p in personnel if p.get("siteId") == site["id"]]
        if not sp:
            continue
        pr = len([p for p in sp if p.get("present")])
        st.subheader(f"{site['name']}  —  {pr}/{len(sp)} present today")
        for p in sp:
            with st.container(border=True):
                ca, cb, cc = st.columns([4, 2, 1])
                ca.markdown(f"**{p.get('name')}**  \n*{p.get('role','')} · {p.get('contact','')}*")
                is_pr = p.get("present", False)
                cb.markdown("✅ Present" if is_pr else "❌ Absent")
                if cc.button("Toggle", key=f"tog_{p['id']}", use_container_width=True):
                    fb_update(f"personnel/{p['id']}", {"present": not is_pr})
                    st.rerun()

# ─────────────────────────────────────────────────────────────────
#  COO ▸ INCIDENTS TAB
# ─────────────────────────────────────────────────────────────────

def tab_incidents(sites, incidents):
    site_map = {s["id"]: s["name"] for s in sites}
    c1, c2 = st.columns([4, 1])
    open_count = len([i for i in incidents if not i.get("resolved")])
    c1.markdown(f"**{open_count} open incidents**")
    if c2.button("➕ Log Incident", type="primary", use_container_width=True):
        st.session_state["add_inc"] = True

    if st.session_state.get("add_inc"):
        with st.form("add_inc"):
            c1f, c2f = st.columns(2)
            inc_site = c1f.selectbox("Site", list(site_map.keys()),
                                     format_func=lambda x: site_map[x])
            inc_type = c2f.selectbox("Type",
                                     ["near-miss","injury","damage","delay","quality"])
            desc = st.text_area("Description *")
            c3f, c4f = st.columns(2)
            inc_date = c3f.date_input("Date", value=date.today())
            severity = c4f.selectbox("Severity", ["low","medium","high"])
            cs, cc = st.columns(2)
            if cs.form_submit_button("Log Incident", type="primary", use_container_width=True) and desc:
                fb_push("incidents", {
                    "siteId": inc_site, "type": inc_type, "description": desc,
                    "date": inc_date.isoformat(), "severity": severity, "resolved": False
                })
                st.session_state["add_inc"] = False
                st.rerun()
            if cc.form_submit_button("Cancel", use_container_width=True):
                st.session_state["add_inc"] = False
                st.rerun()

    open_inc   = [i for i in incidents if not i.get("resolved")]
    closed_inc = [i for i in incidents if i.get("resolved")]

    if open_inc:
        st.markdown(f"#### 🔴 Open ({len(open_inc)})")
        for inc in open_inc:
            s = next((x for x in sites if x["id"] == inc.get("siteId")), {})
            with st.container(border=True):
                ca, cb = st.columns([5, 1])
                ca.markdown(
                    f"**{inc.get('description')}**  \n"
                    f"*{s.get('name','')} · {inc.get('type','')} · {inc.get('date','')}*"
                )
                ca.markdown(badge(inc.get("severity","low")), unsafe_allow_html=True)
                if cb.button("✓ Resolve", key=f"res_{inc['id']}", type="primary"):
                    fb_update(f"incidents/{inc['id']}", {"resolved": True})
                    st.rerun()

    if closed_inc:
        with st.expander(f"✅ Resolved Incidents ({len(closed_inc)})"):
            for inc in closed_inc:
                s = next((x for x in sites if x["id"] == inc.get("siteId")), {})
                st.markdown(
                    f"**{inc.get('description')}**  \n"
                    f"*{s.get('name','')} · {inc.get('date','')}*"
                )
                divider()

# ─────────────────────────────────────────────────────────────────
#  COO ▸ CREDENTIALS TAB
# ─────────────────────────────────────────────────────────────────

def tab_credentials(sites, credentials):
    site_map = {s["id"]: s["name"] for s in sites}
    c1, c2 = st.columns([5, 1])
    c1.markdown("Manage login credentials for site foremen and project managers")
    if c2.button("➕ New Login", type="primary", use_container_width=True):
        st.session_state["add_cred"] = True

    ic1, ic2, ic3 = st.columns(3)
    ic1.info("**🔑 Access Control**\n\nOnly credentials created here allow sign-in. Role cannot be self-selected.")
    ic2.warning("**🦺 Foreman**\n\nAttendance, Stock levels, Material requests, Today's work plan.")
    ic3.success("**📋 Project Manager**\n\nWorks planning, Milestones, Team view, Request approvals.")

    if st.session_state.get("add_cred"):
        with st.form("add_cred"):
            st.subheader("Create Field Staff Login")
            c1f, c2f = st.columns(2)
            full_name = c1f.text_input("Full Name *")
            username  = c2f.text_input("Username *", help="What they type to sign in")
            c3f, c4f  = st.columns(2)
            password  = c3f.text_input("Password *", type="password")
            role      = c4f.selectbox("Role", ["foreman","pm"],
                                      format_func=lambda x: "🦺 Site Foreman" if x=="foreman"
                                                            else "📋 Project Manager")
            cred_site = st.selectbox("Assigned Site *", list(site_map.keys()),
                                     format_func=lambda x: site_map[x])
            cs, cc = st.columns(2)
            if cs.form_submit_button("Create Login", type="primary", use_container_width=True):
                if full_name and username and password and cred_site:
                    existing = fb_list("credentials")
                    if any(c.get("username","").lower() == username.lower() for c in existing):
                        st.error("That username already exists.")
                    else:
                        fb_push("credentials", {
                            "name":         full_name,
                            "username":     username.lower().strip(),
                            "passwordHash": hash_pw(password),
                            "role":         role,
                            "siteId":       cred_site,
                            "active":       True,
                            "createdAt":    TODAY
                        })
                        st.session_state["add_cred"] = False
                        st.success(f"✅ Login created for {full_name}!")
                        st.rerun()
                else:
                    st.error("All fields are required.")
            if cc.form_submit_button("Cancel", use_container_width=True):
                st.session_state["add_cred"] = False
                st.rerun()

    if not credentials:
        st.info("No logins created yet. Click '+ New Login' to create the first field staff account.")

    cols = st.columns(2)
    for i, cred in enumerate(credentials):
        site = next((s for s in sites if s["id"] == cred.get("siteId")), {})
        active = cred.get("active", True)
        with cols[i % 2]:
            with st.container(border=True):
                role_icon = "🦺" if cred.get("role") == "foreman" else "📋" if cred.get("role") == "pm" else "👔"
                st.markdown(
                    f"{'✅' if active else '❌'} **{cred.get('name')}** {role_icon}  \n"
                    f"*@{cred.get('username')}*"
                )
                st.markdown(badge(cred.get("role","foreman")) + "&nbsp;" +
                            badge("active" if active else "disabled"),
                            unsafe_allow_html=True)
                st.caption(f"Site: {site.get('name','—')}  |  Created: {cred.get('createdAt','—')}")
                ca, cb = st.columns(2)
                if ca.button("Toggle Active", key=f"tog_c_{cred['id']}", use_container_width=True):
                    fb_update(f"credentials/{cred['id']}", {"active": not active})
                    st.rerun()
                if cb.button("🗑️ Delete", key=f"del_c_{cred['id']}", use_container_width=True):
                    fb_remove(f"credentials/{cred['id']}")
                    st.success("Deleted.")
                    st.rerun()

# ─────────────────────────────────────────────────────────────────
#  COO DASHBOARD  (full)
# ─────────────────────────────────────────────────────────────────

def coo_dashboard():
    user = st.session_state.user

    with st.sidebar:
        st.markdown("### 🏗️ Site Ops")
        st.markdown(f"**{user['name']}**")
        st.caption("COO · Confidential")
        st.divider()
        tab = st.radio("", [
            "📊 Dashboard", "🏗️ Sites", "📋 Works", "🏁 Milestones",
            "📦 Materials", "📝 Requests", "👥 Personnel",
            "⚠️ Incidents", "🔑 Credentials"
        ], label_visibility="hidden")
        st.divider()
        if st.button("Sign Out", use_container_width=True):
            st.session_state.user = None
            st.rerun()
        st.caption(f"📅 {TODAY}")

    # Load data
    sites       = fb_list("sites")
    works       = fb_list("works")
    milestones  = fb_list("milestones")
    materials   = fb_list("materials")
    personnel   = fb_list("personnel")
    incidents   = fb_list("incidents")
    requests    = fb_list("materialRequests")
    credentials = fb_list("credentials")

    # Refresh button (top-right)
    _, rcol = st.columns([9, 1])
    if rcol.button("🔄", help="Refresh data"):
        st.rerun()

    if   "📊 Dashboard"  in tab: tab_dashboard(sites, works, milestones, materials, personnel, incidents, requests)
    elif "🏗️ Sites"      in tab: tab_sites(sites)
    elif "📋 Works"      in tab: tab_works(sites, works)
    elif "🏁 Milestones" in tab: tab_milestones(sites, milestones)
    elif "📦 Materials"  in tab: tab_materials(sites, materials)
    elif "📝 Requests"   in tab: tab_requests(sites, requests)
    elif "👥 Personnel"  in tab: tab_personnel(sites, personnel)
    elif "⚠️ Incidents"  in tab: tab_incidents(sites, incidents)
    elif "🔑 Credentials"in tab: tab_credentials(sites, credentials)

# ─────────────────────────────────────────────────────────────────
#  FOREMAN APP
# ─────────────────────────────────────────────────────────────────

def foreman_app():
    user = st.session_state.user
    site = user.get("site", {})
    sid  = site.get("id")

    st.markdown(f"## 🦺 Site Foreman  ·  {site.get('name','')}")
    st.caption(f"{user.get('name','')}  ·  {TODAY}")

    all_personnel = fb_list("personnel")
    all_materials = fb_list("materials")
    all_works     = fb_list("works")
    all_requests  = fb_list("materialRequests")

    personnel   = [p for p in all_personnel if p.get("siteId") == sid]
    materials   = [m for m in all_materials if m.get("siteId") == sid]
    today_works = [w for w in all_works     if w.get("siteId") == sid and w.get("date") == TODAY]
    requests    = [r for r in all_requests  if r.get("siteId") == sid]

    _, rcol = st.columns([9, 1])
    if rcol.button("🔄", help="Refresh"):
        st.rerun()

    t1, t2, t3, t4 = st.tabs(["👥 Attendance", "📦 Stock", "📝 Requests", "📋 Works"])

    # ── Attendance ───────────────────────────────────────────────
    with t1:
        present = [p for p in personnel if p.get("present")]
        ca, cb, cc = st.columns(3)
        ca.metric("Present", len(present))
        cb.metric("Absent",  len(personnel) - len(present))
        cc.metric("Total",   len(personnel))
        st.divider()
        for p in personnel:
            with st.container(border=True):
                ca, cb = st.columns([4, 1])
                ca.markdown(f"**{p.get('name')}**  \n*{p.get('role','')}*")
                is_pr = p.get("present", False)
                if cb.button("✅ Present" if is_pr else "❌ Absent",
                             key=f"fa_tog_{p['id']}", use_container_width=True,
                             type="primary" if is_pr else "secondary"):
                    fb_update(f"personnel/{p['id']}", {"present": not is_pr})
                    st.rerun()

    # ── Stock ─────────────────────────────────────────────────────
    with t2:
        st.caption("Update current stock levels below")
        for m in materials:
            st_s = stock_status(m.get("qty", 0), m.get("minStock", 1))
            with st.container(border=True):
                ca, cb = st.columns([4, 1])
                ca.markdown(f"**{m.get('name')}**  \n*{m.get('supplier','')} · min: {m.get('minStock')} {m.get('unit','')}*")
                cb.markdown(badge(st_s), unsafe_allow_html=True)
                pct = min(int(float(m.get("qty",0)) / max(float(m.get("minStock",1)),1) * 100), 100)
                colour = "#ef4444" if st_s=="critical" else "#f59e0b" if st_s=="low" else "#22c55e"
                prog_bar(pct, colour)
                with st.form(f"fqty_{m['id']}"):
                    cf1, cf2 = st.columns([3, 1])
                    new_qty = cf1.number_input(
                        f"Qty ({m.get('unit','')})", value=float(m.get("qty",0)),
                        min_value=0.0, label_visibility="visible"
                    )
                    if cf2.form_submit_button("Save", use_container_width=True):
                        fb_update(f"materials/{m['id']}", {"qty": new_qty})
                        st.success("Updated!")
                        st.rerun()

    # ── Requests ──────────────────────────────────────────────────
    with t3:
        st.subheader("Request Materials")
        with st.form("req_form"):
            mat_name = st.text_input("Material name *")
            c1f, c2f = st.columns(2)
            qty_req  = c1f.number_input("Quantity *", min_value=0.1, value=1.0)
            unit_req = c2f.selectbox("Unit", ["m³","tons","pcs","m","m²","kg","L","bags"])
            notes_req = st.text_input("Reason / Notes (optional)")
            if st.form_submit_button("Submit Request", type="primary",
                                     use_container_width=True) and mat_name:
                fb_push("materialRequests", {
                    "siteId": sid, "name": mat_name, "qty": qty_req,
                    "unit": unit_req, "notes": notes_req,
                    "requestedBy": user.get("name",""), "date": TODAY, "status": "pending"
                })
                st.success("✅ Request submitted!")
                st.rerun()

        pending_r = [r for r in requests if r.get("status") == "pending"]
        approved_r = [r for r in requests if r.get("status") != "pending"]
        if pending_r:
            st.divider()
            st.markdown(f"**⏳ Pending ({len(pending_r)})**")
            for r in pending_r:
                st.warning(f"**{r.get('name')}** — {r.get('qty')} {r.get('unit','')} · {r.get('date','')}")
        if approved_r:
            st.divider()
            st.markdown("**✅ Approved / Ordered**")
            for r in approved_r:
                st.success(f"**{r.get('name')}** — {r.get('qty')} {r.get('unit','')} · {r.get('status','')}")

    # ── Works (read-only) ─────────────────────────────────────────
    with t4:
        st.caption("Today's work plan — read only. Set by your Project Manager.")
        if not today_works:
            st.info("No tasks planned for today.")
        for w in today_works:
            with st.container(border=True):
                ca, cb = st.columns([4, 1])
                ca.markdown(f"**{w.get('task')}**  \n*{w.get('assignedTo','Unassigned')}*")
                ca.markdown(badge(w.get("priority","medium")), unsafe_allow_html=True)
                cb.markdown(badge(w.get("status","pending")), unsafe_allow_html=True)

    st.divider()
    if st.button("Sign Out"):
        st.session_state.user = None
        st.rerun()

# ─────────────────────────────────────────────────────────────────
#  PROJECT MANAGER APP
# ─────────────────────────────────────────────────────────────────

def pm_app():
    user = st.session_state.user
    site = user.get("site", {})
    sid  = site.get("id")

    st.markdown(f"## 📋 Project Manager  ·  {site.get('name','')}")
    st.caption(f"{user.get('name','')}  ·  {TODAY}")

    all_works      = fb_list("works")
    all_milestones = fb_list("milestones")
    all_personnel  = fb_list("personnel")
    all_requests   = fb_list("materialRequests")

    works      = [w for w in all_works      if w.get("siteId") == sid]
    milestones = [m for m in all_milestones if m.get("siteId") == sid]
    personnel  = [p for p in all_personnel  if p.get("siteId") == sid]
    requests   = [r for r in all_requests   if r.get("siteId") == sid]

    _, rcol = st.columns([9, 1])
    if rcol.button("🔄", help="Refresh"):
        st.rerun()

    t1, t2, t3, t4 = st.tabs(["📋 Works", "🏁 Milestones", "👥 Team", "📝 Requests"])

    STATUS_CYCLE = {"pending": "in-progress", "in-progress": "completed", "completed": "pending"}

    # ── Works ─────────────────────────────────────────────────────
    with t1:
        c1, c2 = st.columns([3, 1])
        d_filter = c1.date_input("Date", value=date.today())
        if c2.button("➕ Add Task", type="primary", use_container_width=True):
            st.session_state["pm_add_work"] = True

        if st.session_state.get("pm_add_work"):
            with st.form("pm_add_work"):
                task      = st.text_input("Task *")
                c1f, c2f  = st.columns(2)
                assigned  = c1f.text_input("Assigned To")
                priority  = c2f.selectbox("Priority", ["high","medium","low"])
                notes     = st.text_input("Notes")
                cs, cc = st.columns(2)
                if cs.form_submit_button("Add", type="primary", use_container_width=True) and task:
                    fb_push("works", {
                        "task": task, "siteId": sid, "assignedTo": assigned,
                        "date": d_filter.isoformat(), "priority": priority,
                        "notes": notes, "status": "pending"
                    })
                    st.session_state["pm_add_work"] = False
                    st.rerun()
                if cc.form_submit_button("Cancel", use_container_width=True):
                    st.session_state["pm_add_work"] = False
                    st.rerun()

        day_works = [w for w in works if w.get("date") == d_filter.isoformat()]
        ca, cb, cc2 = st.columns(3)
        ca.metric("Done",    len([w for w in day_works if w.get("status")=="completed"]))
        cb.metric("Active",  len([w for w in day_works if w.get("status")=="in-progress"]))
        cc2.metric("Pending", len([w for w in day_works if w.get("status")=="pending"]))
        st.divider()
        for w in day_works:
            with st.container(border=True):
                ca, cb, cc2 = st.columns([4, 2, 1])
                ca.markdown(f"**{w.get('task')}**  \n*{w.get('assignedTo','Unassigned')}*")
                ca.markdown(badge(w.get("priority","medium")), unsafe_allow_html=True)
                cb.markdown(badge(w.get("status","pending")), unsafe_allow_html=True)
                if cc2.button("↻", key=f"pm_cyc_{w['id']}", help="Cycle status"):
                    fb_update(f"works/{w['id']}",
                              {"status": STATUS_CYCLE.get(w.get("status","pending"),"pending")})
                    st.rerun()

    # ── Milestones ────────────────────────────────────────────────
    with t2:
        st.caption("Drag sliders to update milestone progress")
        for m in milestones:
            with st.container(border=True):
                ca, cb = st.columns([5, 1])
                ca.markdown(f"**{m.get('milestone')}**  \n*Target: {m.get('targetDate','')}*")
                pct = int(m.get("completion", 0))
                cb.markdown(f"**{pct}%**")
                prog_bar(pct)
                new_pct = st.slider("", 0, 100, pct,
                                    key=f"pm_ms_{m['id']}", label_visibility="hidden")
                if new_pct != pct:
                    status = "completed" if new_pct==100 else "in-progress" if new_pct>0 else "pending"
                    fb_update(f"milestones/{m['id']}",
                              {"completion": new_pct, "status": status})
                    st.rerun()

    # ── Team (read-only) ──────────────────────────────────────────
    with t3:
        present = [p for p in personnel if p.get("present")]
        ca, cb = st.columns(2)
        ca.metric("Present", len(present))
        cb.metric("Total",   len(personnel))
        st.caption("Attendance is updated by the site foreman.")
        st.divider()
        for p in personnel:
            ca, cb = st.columns([4, 1])
            ca.markdown(f"**{p.get('name')}**  \n*{p.get('role','')}*")
            cb.markdown("✅ On site" if p.get("present") else "❌ Absent")

    # ── Requests ──────────────────────────────────────────────────
    with t4:
        pending  = [r for r in requests if r.get("status") == "pending"]
        approved = [r for r in requests if r.get("status") != "pending"]

        if not requests:
            st.info("No material requests from the site foreman yet.")
        if pending:
            st.markdown(f"**⏳ Pending Approval ({len(pending)})**")
            for r in pending:
                with st.container(border=True):
                    ca, cb = st.columns([5, 1])
                    ca.markdown(
                        f"**{r.get('name')}** — {r.get('qty')} {r.get('unit','')}  \n"
                        f"*by {r.get('requestedBy','')} · {r.get('date','')}*"
                    )
                    if r.get("notes"):
                        ca.caption(r["notes"])
                    if cb.button("✓ Approve", key=f"pm_apr_{r['id']}", type="primary"):
                        fb_update(f"materialRequests/{r['id']}", {"status": "approved"})
                        st.rerun()
        if approved:
            st.divider()
            st.markdown("**✅ Processed**")
            for r in approved:
                st.success(
                    f"**{r.get('name')}** — {r.get('qty')} {r.get('unit','')} · {r.get('status','')}"
                )

    st.divider()
    if st.button("Sign Out"):
        st.session_state.user = None
        st.rerun()

# ─────────────────────────────────────────────────────────────────
#  MAIN ROUTING
# ─────────────────────────────────────────────────────────────────

if not PYREBASE_OK:
    st.error("⚠️ **pyrebase4 is not installed.**")
    st.code("pip install pyrebase4")
    st.stop()

user = st.session_state.get("user")

if not user:
    show_login()
elif user.get("role") == "coo":
    coo_dashboard()
elif user.get("role") == "foreman":
    foreman_app()
elif user.get("role") == "pm":
    pm_app()
else:
    st.error("Unknown role. Please sign out and sign in again.")
    if st.button("Sign Out"):
        st.session_state.user = None
        st.rerun()
