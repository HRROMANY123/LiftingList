import streamlit as st
import json
import re
from datetime import datetime, date
from pathlib import Path
import streamlit.components.v1 as components

# =========================
# CONFIG
# =========================
APP_TITLE = "Etsy SEO Helper (Templates Pro)"
PRO_USERS_FILE = "pro_users.json"
USAGE_FILE = "usage_log.json"       # tracks free users daily usage by email
FREE_DAILY_LIMIT = 5               # free generations per day per email
MAX_TITLE_LEN = 140

# =========================
# UTIL: JSON helpers
# =========================
def _read_json(path: str, default):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default

def _write_json(path: str, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_pro_users():
    data = _read_json(PRO_USERS_FILE, default={})
    # supports {"emails": ["a@b.com"]} OR {"a@b.com": true}
    if isinstance(data, dict) and "emails" in data and isinstance(data["emails"], list):
        return set([e.strip().lower() for e in data["emails"] if isinstance(e, str)])
    if isinstance(data, dict):
        return set([k.strip().lower() for k, v in data.items() if v is True or v == 1])
    if isinstance(data, list):
        return set([e.strip().lower() for e in data if isinstance(e, str)])
    return set()

def is_valid_email(email: str) -> bool:
    if not email:
        return False
    email = email.strip().lower()
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email) is not None

def load_usage():
    return _read_json(USAGE_FILE, default={})

def save_usage(usage: dict):
    _write_json(USAGE_FILE, usage)

def today_key():
    return date.today().isoformat()

def get_free_used(usage: dict, email: str) -> int:
    email = (email or "").strip().lower()
    return int(usage.get(today_key(), {}).get(email, 0))

def inc_free_used(usage: dict, email: str):
    email = email.strip().lower()
    tk = today_key()
    usage.setdefault(tk, {})
    usage[tk][email] = int(usage[tk].get(email, 0)) + 1

# =========================
# UTIL: Copy button (JS)
# =========================
def copy_button(text: str, key: str, label="Copy"):
    # A tiny HTML+JS snippet using Clipboard API
    safe_text = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    html = f"""
    <div style="display:flex; gap:8px; align-items:center;">
      <button
        style="
          border:1px solid #ddd; background:#fff; padding:6px 10px; border-radius:8px;
          cursor:pointer; font-size:14px;
        "
        onclick="navigator.clipboard.writeText(`{safe_text}`); this.innerText='Copied ✅'; setTimeout(()=>this.innerText='{label}', 1200);"
        id="{key}">
        {label}
      </button>
    </div>
    """
    components.html(html, height=44)

# =========================
# SEO Template Logic (No AI)
# =========================
BUYER_INTENT_WORDS = [
    "gift", "personalized", "custom", "handmade", "unique", "premium",
    "best gift", "for her", "for him", "for kids", "anniversary", "birthday",
    "wedding", "bridal", "housewarming", "christmas gift", "mothers day", "fathers day"
]

SEASONAL_PACKS = {
    "None": [],
    "Spring": ["spring", "easter", "mother's day"],
    "Summer": ["summer", "beach", "vacation"],
    "Autumn": ["fall", "autumn", "halloween", "thanksgiving"],
    "Winter": ["winter", "christmas", "new year"],
}

def clean_kw(s: str):
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def split_keywords(s: str):
    # split by commas
    parts = [clean_kw(x) for x in (s or "").split(",")]
    parts = [p for p in parts if p]
    return parts

def title_variations(product: str, main_kws: list, material: str, style: str, audience: str,
                     occasion: str, personalization: str, color: str, season: str):
    product = clean_kw(product)
    material = clean_kw(material)
    style = clean_kw(style)
    audience = clean_kw(audience)
    occasion = clean_kw(occasion)
    personalization = clean_kw(personalization)
    color = clean_kw(color)

    # pick 2–3 strong keywords
    kws = [k for k in main_kws if k]
    top = kws[:3] if len(kws) >= 3 else kws

    seasonal = SEASONAL_PACKS.get(season, [])
    season_kw = seasonal[0] if seasonal else ""

    # templates
    templates = [
        "{kw1} {product} - {material} {style} | {audience} {occasion}",
        "{product} {kw1} {kw2} | {personalization} {audience} Gift",
        "{kw1} {kw2} {product} | {color} {style} - Perfect {occasion}",
        "{season} {kw1} {product} | Unique {audience} Gift - {material}",
        "{product} | {kw1} {style} {material} - {occasion} Gift Idea",
        "{kw1} {product} | {personalization} - {audience} {occasion} Gift",
        "{kw1} {kw2} {product} | Handmade {style} - {audience}",
        "{product} {kw1} | Premium {material} - {color} {occasion}",
    ]

    # safe kw slots
    kw1 = top[0] if len(top) > 0 else ""
    kw2 = top[1] if len(top) > 1 else ""
    kw3 = top[2] if len(top) > 2 else ""

    def fill(t):
        out = t.format(
            kw1=kw1, kw2=kw2, kw3=kw3,
            product=product,
            material=material,
            style=style,
            audience=audience,
            occasion=occasion,
            personalization=personalization,
            color=color,
            season=season_kw
        )
        # cleanup double spaces, stray separators
        out = re.sub(r"\s+", " ", out).strip()
        out = re.sub(r"\|\s*\|", "|", out)
        out = re.sub(r"\s+\|", " |", out)
        out = re.sub(r"\|\s+", "| ", out)
        out = out.strip(" -|")
        return out

    titles = []
    for t in templates:
        cand = fill(t)
        if cand and cand not in titles:
            titles.append(cand)

    # ensure max 8, prioritize unique
    return titles[:8]

def make_long_tail_tags(product: str, main_kws: list, material: str, style: str, audience: str, occasion: str, season: str):
    product = clean_kw(product)
    material = clean_kw(material)
    style = clean_kw(style)
    audience = clean_kw(audience)
    occasion = clean_kw(occasion)
    seasonal = SEASONAL_PACKS.get(season, [])

    kws = [k for k in main_kws if k]
    # Build long-tail phrases (3–5 words)
    candidates = []
    base_parts = [style, material, product]
    base = " ".join([p for p in base_parts if p]).strip()

    if kws:
        candidates.append(f"{kws[0]} {base}".strip())
    if len(kws) > 1:
        candidates.append(f"{kws[0]} {kws[1]} {product}".strip())
    if audience:
        candidates.append(f"{base} for {audience}".strip())
    if occasion:
        candidates.append(f"{occasion} {product} {style}".strip())
    if seasonal:
        candidates.append(f"{seasonal[0]} {product} gift".strip())

    # Clean, unique, <= 20 chars? Etsy tags often 20 chars max,
    # but user asked improvements not strict enforcement. We'll keep reasonable length.
    out = []
    for c in candidates:
        c = re.sub(r"\s+", " ", c).strip().lower()
        if c and c not in out:
            out.append(c)
    return out[:13]

def make_buyer_intent_tags(audience: str, occasion: str):
    audience = clean_kw(audience).lower()
    occasion = clean_kw(occasion).lower()

    tags = []
    # pick a curated subset
    base = ["gift", "personalized", "custom", "handmade", "unique"]
    tags.extend(base)

    if audience:
        tags.append(f"for {audience}".strip())
    if occasion:
        tags.append(f"{occasion} gift".strip())

    # ensure unique, lowercase
    out = []
    for t in tags:
        t = re.sub(r"\s+", " ", t).strip().lower()
        if t and t not in out:
            out.append(t)
    return out[:13]

def make_seasonality_tags(season: str):
    seasonal = SEASONAL_PACKS.get(season, [])
    out = []
    for s in seasonal:
        s = clean_kw(s).lower()
        if s and s not in out:
            out.append(s)
    return out[:13]

def strong_first_two_lines(product: str, main_kws: list, benefit: str, audience: str, occasion: str, personalization: str, season: str):
    product = clean_kw(product)
    benefit = clean_kw(benefit)
    audience = clean_kw(audience)
    occasion = clean_kw(occasion)
    personalization = clean_kw(personalization)

    kws = [k for k in main_kws if k]
    kw = kws[0] if kws else ""

    seasonal = SEASONAL_PACKS.get(season, [])
    season_kw = seasonal[0] if seasonal else ""

    # 2 lines optimized for Etsy search preview
    line1 = f"{product}: {benefit}" if benefit else f"{product}: {kw} designed to stand out" if kw else f"{product}: made to stand out"
    # add reason + audience + occasion + personalization
    parts = []
    if audience:
        parts.append(f"Perfect for {audience}")
    if occasion:
        parts.append(f"{occasion} gifts")
    if personalization:
        parts.append(personalization)
    if season_kw:
        parts.append(season_kw)

    line2 = " • ".join(parts) if parts else "A thoughtful gift that feels premium and personal."

    # clean
    line1 = re.sub(r"\s+", " ", line1).strip()
    line2 = re.sub(r"\s+", " ", line2).strip()
    return line1, line2

def full_description(product: str, main_kws: list, benefit: str, features: str, materials: str,
                     sizing: str, shipping: str, personalization: str, audience: str, occasion: str, season: str):
    l1, l2 = strong_first_two_lines(product, main_kws, benefit, audience, occasion, personalization, season)

    # body template
    bullets = [clean_kw(x) for x in (features or "").split("\n") if clean_kw(x)]
    bullets = bullets[:8]

    kws_line = ", ".join([k for k in main_kws[:8] if k])
    desc = []
    desc.append(l1)
    desc.append(l2)
    desc.append("")
    desc.append("✅ Why you'll love it:")
    if bullets:
        for b in bullets:
            desc.append(f"• {b}")
    else:
        desc.append("• High quality, made with care")
        desc.append("• Unique look that matches multiple styles")
        desc.append("• Great as a gift or for everyday use")

    if materials:
        desc.append("")
        desc.append(f"🧵 Materials: {clean_kw(materials)}")

    if sizing:
        desc.append("")
        desc.append(f"📏 Size / Details: {clean_kw(sizing)}")

    if personalization:
        desc.append("")
        desc.append(f"✨ Personalization: {clean_kw(personalization)}")

    if shipping:
        desc.append("")
        desc.append(f"🚚 Shipping: {clean_kw(shipping)}")

    if kws_line:
        desc.append("")
        desc.append(f"🔎 Keywords: {kws_line}")

    desc.append("")
    desc.append("📩 Questions? Message me anytime — I’m happy to help!")
    return "\n".join(desc)

# =========================
# UI
# =========================
st.set_page_config(page_title=APP_TITLE, layout="centered")
st.title(APP_TITLE)

st.caption("Templates-only (No AI): better Titles + Tags + first 2 lines for Etsy search preview.")

pro_users = load_pro_users()

with st.sidebar:
    st.subheader("Account")
    email = st.text_input("Your email (required for Free/Pro)", placeholder="you@email.com").strip().lower()
    pro_active = bool(email) and (email in pro_users)

    if email and not is_valid_email(email):
        st.warning("Please enter a valid email.")

    st.markdown("---")
    st.subheader("Plan")
    if pro_active:
        st.success("✅ Pro active (by email)")
        st.write("Unlimited generations.")
    else:
        st.info("Free plan (daily limit)")
        st.write(f"Free limit: **{FREE_DAILY_LIMIT} generations/day** per email.")
        st.write("Upgrade to Pro (by email) after payment — manual activation.")

# Block if no email
if not email or not is_valid_email(email):
    st.warning("Enter a valid email in the sidebar to use the generator.")
    st.stop()

# Usage gating (Free)
usage = load_usage()
used = get_free_used(usage, email)

if (not pro_active) and used >= FREE_DAILY_LIMIT:
    st.error("Free limit reached for today. Upgrade to Pro (by email) for unlimited generations.")
    st.stop()

# Inputs
st.subheader("Listing inputs")
col1, col2 = st.columns(2)
with col1:
    product = st.text_input("Product type", placeholder="e.g., Minimalist Necklace, Printable Wall Art, Leather Wallet")
    material = st.text_input("Material", placeholder="e.g., 925 sterling silver, oak wood, leather")
    style = st.text_input("Style", placeholder="e.g., minimalist, boho, modern, vintage")
    color = st.text_input("Color (optional)", placeholder="e.g., gold, black, pastel")
with col2:
    audience = st.text_input("Target audience", placeholder="e.g., her, him, mom, dad, kids, couples")
    occasion = st.text_input("Occasion", placeholder="e.g., birthday, wedding, anniversary, housewarming")
    personalization = st.text_input("Personalization (optional)", placeholder="e.g., add name, custom text, choose size")

keywords = st.text_input("Main keywords (comma-separated)", placeholder="e.g., dainty necklace, initial charm, gift for her")
benefit = st.text_input("Main benefit (for first line)", placeholder="e.g., Elegant look + perfect everyday wear")
season = st.selectbox("Seasonality", options=list(SEASONAL_PACKS.keys()), index=0)

st.markdown("---")
st.subheader("Description details (optional)")
features = st.text_area("Key features (one per line)", placeholder="• Handmade\n• High quality finish\n• Gift-ready packaging", height=120)
materials_desc = st.text_input("Materials text", placeholder="e.g., Sterling silver, hypoallergenic")
sizing = st.text_input("Sizing / Details", placeholder="e.g., 16-18 inches chain, A4 size, 300 DPI")
shipping = st.text_input("Shipping policy snippet", placeholder="e.g., Processing 1-2 days, tracked shipping available")

# Generate button
gen = st.button("🚀 Generate SEO Pack", use_container_width=True)

if gen:
    main_kws = split_keywords(keywords)

    titles = title_variations(
        product=product,
        main_kws=main_kws,
        material=material,
        style=style,
        audience=audience,
        occasion=occasion,
        personalization=personalization,
        color=color,
        season=season
    )

    long_tail = make_long_tail_tags(product, main_kws, material, style, audience, occasion, season)
    buyer_intent = make_buyer_intent_tags(audience, occasion)
    seasonal_tags = make_seasonality_tags(season)

    desc = full_description(
        product=product,
        main_kws=main_kws,
        benefit=benefit,
        features=features,
        materials=materials_desc,
        sizing=sizing,
        shipping=shipping,
        personalization=personalization,
        audience=audience,
        occasion=occasion,
        season=season
    )

    # increment usage for Free users only
    if not pro_active:
        inc_free_used(usage, email)
        save_usage(usage)
        used = get_free_used(usage, email)

    st.success("✅ Generated")

    # -------- Titles with counter + copy
    st.subheader("1) Titles (with 140-char counter + Copy)")
    if not titles:
        st.warning("Add at least a Product type and/or Keywords to generate better titles.")
    else:
        for i, t in enumerate(titles, start=1):
            n = len(t)
            # status color
            if n > MAX_TITLE_LEN:
                st.error(f"Title {i} — {n}/{MAX_TITLE_LEN} (OVER limit)")
            elif n >= 130:
                st.warning(f"Title {i} — {n}/{MAX_TITLE_LEN} (close to limit)")
            else:
                st.caption(f"Title {i} — {n}/{MAX_TITLE_LEN}")

            c1, c2 = st.columns([8, 2])
            with c1:
                st.text_area(
                    label=f"Title {i}",
                    value=t,
                    height=68,
                    key=f"title_area_{i}"
                )
            with c2:
                copy_button(t, key=f"copy_title_{i}", label="Copy")

            st.divider()

    # -------- Tags improvements
    st.subheader("2) Tags (Improved)")
    tcol1, tcol2, tcol3 = st.columns(3)
    with tcol1:
        st.markdown("**Long-tail**")
        st.write(long_tail if long_tail else ["(Add more keywords for better long-tail tags)"])
    with tcol2:
        st.markdown("**Buyer Intent**")
        st.write(buyer_intent)
    with tcol3:
        st.markdown("**Seasonality**")
        st.write(seasonal_tags if seasonal_tags else ["None"])

    # One-click copy for tag packs
    st.markdown("**Copy tag packs:**")
    ctag1, ctag2, ctag3 = st.columns(3)
    with ctag1:
        copy_button(", ".join(long_tail), key="copy_longtail", label="Copy Long-tail")
    with ctag2:
        copy_button(", ".join(buyer_intent), key="copy_intent", label="Copy Intent")
    with ctag3:
        copy_button(", ".join(seasonal_tags), key="copy_season", label="Copy Seasonal")

    # -------- Description first 2 lines emphasis
    st.subheader("3) Description (First 2 lines optimized)")
    lines = desc.splitlines()
    if len(lines) >= 2:
        st.markdown("**Etsy Search Preview (First 2 lines):**")
        st.info(f"{lines[0]}\n\n{lines[1]}")
    st.text_area("Full Description", value=desc, height=260)

    copy_button(desc, key="copy_desc", label="Copy Description")

    # -------- Free usage note
    if not pro_active:
        st.caption(f"Free usage today: {used}/{FREE_DAILY_LIMIT} generations")

st.markdown("---")
st.caption("Admin note: Add Pro emails in pro_users.json to activate Pro by email.")