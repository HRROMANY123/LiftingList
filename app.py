# app.py — Listing-Lift (FULL) — EXTREME Creativity (NO AI)
# Store: https://listing-lift.lemonsqueezy.com/
# Support: hromany@hotmail.com

import json
import re
import csv
import io
import hashlib
import random
from datetime import date
from pathlib import Path
import urllib.parse

import streamlit as st
import streamlit.components.v1 as components

# =========================
# CONFIG
# =========================
APP_TITLE = "Listing-Lift — Etsy Listing Writer + Tag Guard (Creative NO-AI)"
STORE_URL = "https://listing-lift.lemonsqueezy.com/"
SUPPORT_EMAIL = "hromany@hotmail.com"

PRO_USERS_FILE = "pro_users.json"
USAGE_FILE = "usage_log.json"

FREE_DAILY_LIMIT = 5
MAX_TITLE_LEN = 140
ETSY_TAG_MAX_LEN = 20
ETSY_TAG_COUNT = 13

# =========================
# EXAMPLE
# =========================
EXAMPLE_INPUT = {
    "product": "Minimalist Necklace",
    "material": "925 sterling silver",
    "style": "minimalist",
    "color": "gold",
    "audience": "her",
    "occasion": "birthday",
    "personalization": "Add initial letter",
    "keywords": "dainty necklace, initial charm, gift for her",
    "benefit": "Elegant everyday style + gift-ready packaging",
    "season": "Spring",
    "features": "Handmade with care\nGift-ready packaging\nTimeless minimalist look",
    "materials_desc": "Sterling silver, hypoallergenic",
    "sizing": "16-18 inch chain, adjustable",
    "shipping": "Processing 1-2 days, tracked shipping available",
    "paste_tags": "",
}

FORM_KEYS = [
    "product", "material", "style", "color",
    "audience", "occasion", "personalization",
    "keywords", "benefit", "season",
    "features", "materials_desc", "sizing", "shipping",
    "paste_tags",
]

# =========================
# Reset / Example
# =========================
def apply_example():
    for k, v in EXAMPLE_INPUT.items():
        st.session_state[k] = v
    st.session_state["creative_regen"] = 0
    st.rerun()

def reset_inputs():
    for k in FORM_KEYS:
        st.session_state[k] = ""
    st.session_state["season"] = "None"
    st.session_state["creative_regen"] = 0
    st.rerun()

# =========================
# JSON storage
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

def load_pro_users() -> set[str]:
    data = _read_json(PRO_USERS_FILE, default={})
    if isinstance(data, dict) and "emails" in data and isinstance(data["emails"], list):
        return {str(e).strip().lower() for e in data["emails"] if str(e).strip()}
    if isinstance(data, dict):
        out = set()
        for k, v in data.items():
            if v is True or v == 1:
                out.add(str(k).strip().lower())
        return out
    if isinstance(data, list):
        return {str(e).strip().lower() for e in data if str(e).strip()}
    return set()

def is_valid_email(email: str) -> bool:
    if not email:
        return False
    email = email.strip().lower()
    return re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email) is not None

def load_usage() -> dict:
    return _read_json(USAGE_FILE, default={})

def save_usage(usage: dict):
    _write_json(USAGE_FILE, usage)

def today_key() -> str:
    return date.today().isoformat()

def get_free_used(usage: dict, email: str) -> int:
    email = (email or "").strip().lower()
    return int(usage.get(today_key(), {}).get(email, 0))

def inc_free_used(usage: dict, email: str):
    email = (email or "").strip().lower()
    tk = today_key()
    usage.setdefault(tk, {})
    usage[tk][email] = int(usage[tk].get(email, 0)) + 1

# =========================
# UI helpers
# =========================
def copy_button(text: str, key: str, label="Copy"):
    safe_text = (text or "").replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    html = f"""
    <div style="display:flex; gap:8px; align-items:center;">
      <button
        style="border:1px solid #ddd; background:#fff; padding:6px 10px; border-radius:8px; cursor:pointer; font-size:14px; width: 100%;"
        onclick="navigator.clipboard.writeText(`{safe_text}`); this.innerText='Copied ✅'; setTimeout(()=>this.innerText='{label}', 1200);"
        id="{key}">
        {label}
      </button>
    </div>
    """
    components.html(html, height=44)

def build_lemon_link(base_url: str, email: str) -> str:
    base_url = (base_url or "").strip()
    if not base_url:
        return ""
    if not email:
        return base_url
    parsed = urllib.parse.urlparse(base_url)
    q = dict(urllib.parse.parse_qsl(parsed.query))
    q["checkout[email]"] = email
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(q, doseq=True)))

# =========================
# Base SEO logic (no AI)
# =========================
SEASONAL_PACKS = {
    "None": [],
    "Spring": ["spring", "easter", "mother's day", "fresh bloom", "new beginnings"],
    "Summer": ["summer", "beach", "vacation", "sun-kissed", "festival"],
    "Autumn": ["fall", "autumn", "halloween", "thanksgiving", "cozy season"],
    "Winter": ["winter", "christmas", "new year", "holiday", "snowy nights"],
}

STOPWORDS = {"a","an","the","and","or","of","for","to","with","in","on","at","by","from","this","that","your","you","is","are"}

def clean_kw(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def normalize(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9\s'-]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def split_keywords(s: str) -> list[str]:
    parts = [clean_kw(x) for x in (s or "").split(",")]
    return [p for p in parts if p]

# =========================
# Offline Keyword Expansion (EXTREME)
# =========================
SYNONYMS = {
    "minimalist": ["minimal", "simple", "clean", "modern", "understated"],
    "dainty": ["delicate", "fine", "subtle", "petite"],
    "necklace": ["pendant necklace", "chain necklace", "layering necklace"],
    "ring": ["band ring", "stacking ring", "statement ring"],
    "gift": ["gift idea", "present", "thoughtful gift"],
    "birthday": ["birthday gift", "birthday present", "birthday surprise"],
    "wedding": ["wedding gift", "bridal", "bride gift"],
    "boho": ["bohemian", "boho chic", "free spirit"],
    "gold": ["gold tone", "golden", "warm gold"],
    "silver": ["sterling silver", "silver tone", "cool silver"],
    "handmade": ["handcrafted", "artisan made", "made by hand"],
    "printable": ["instant download", "digital download", "ready to print"],
    "template": ["editable template", "customizable template", "fillable template"],
    "decor": ["home decor", "room decor", "wall decor"],
}

LONGTAIL_PATTERNS = [
    "{kw} for {audience}",
    "{kw} gift for {occasion}",
    "{kw} {style}",
    "{color} {kw}",
    "{material} {kw}",
    "{kw} with personalization",
    "unique {kw}",
    "modern {kw}",
    "minimal {kw}",
]

def expand_keywords(base_kws: list[str], product: str, material: str, style: str, color: str, audience: str, occasion: str, creativity: int, rng: random.Random) -> list[str]:
    # Start with base keywords
    kws = [clean_kw(k) for k in base_kws if clean_kw(k)]
    # Add product/material/style/color as candidates
    for t in [product, material, style, color]:
        t = clean_kw(t)
        if t:
            kws.append(t)

    # Expand synonyms a bit depending on creativity
    expanded = []
    for k in kws:
        expanded.append(k)
        k_norm = normalize(k)
        # if single-word keyword exists in synonyms
        if k_norm in SYNONYMS:
            syns = SYNONYMS[k_norm][:]
            rng.shuffle(syns)
            take = 1 if creativity <= 4 else (2 if creativity <= 7 else 3)
            expanded.extend(syns[:take])

    # Add long-tail patterns
    aud = clean_kw(audience) or "her"
    occ = clean_kw(occasion) or "birthday"
    mat = clean_kw(material) or ""
    sty = clean_kw(style) or ""
    col = clean_kw(color) or ""

    pool = []
    for k in expanded[:12]:
        kn = clean_kw(k)
        if not kn:
            continue
        for p in LONGTAIL_PATTERNS:
            phrase = p.format(kw=kn, audience=aud, occasion=occ, material=mat, style=sty, color=col).strip()
            phrase = re.sub(r"\s+", " ", phrase)
            pool.append(phrase)

    rng.shuffle(pool)
    take_pool = 3 if creativity <= 4 else (6 if creativity <= 7 else 10)

    out = expanded + pool[:take_pool]
    # Clean + dedupe keep order
    seen = set()
    final = []
    for x in out:
        xn = normalize(x)
        if xn and xn not in seen and len(final) < 40:
            seen.add(xn)
            final.append(clean_kw(x))
    return final

# =========================
# Titles (more variety)
# =========================
def title_variations(product: str, main_kws: list[str], material: str, style: str,
                     audience: str, occasion: str, personalization: str, color: str, season: str,
                     tone: str, creativity: int, rng: random.Random) -> list[str]:
    product = clean_kw(product)
    material = clean_kw(material)
    style = clean_kw(style)
    audience = clean_kw(audience)
    occasion = clean_kw(occasion)
    personalization = clean_kw(personalization)
    color = clean_kw(color)

    seasonal = SEASONAL_PACKS.get(season, [])
    season_kw = seasonal[0] if seasonal else ""

    kw1 = clean_kw(main_kws[0]) if len(main_kws) > 0 else ""
    kw2 = clean_kw(main_kws[1]) if len(main_kws) > 1 else ""

    vibe_words = {
        "Luxury": ["luxury", "premium", "elegant", "refined"],
        "Cozy": ["cozy", "warm", "comforting", "soft"],
        "Minimal": ["minimal", "clean", "simple", "modern"],
        "Playful": ["cute", "fun", "playful", "happy"],
        "Professional": ["professional", "clean", "smart", "polished"],
    }.get(tone, ["beautiful", "modern", "unique", "premium"])

    rng.shuffle(vibe_words)
    vibe1 = vibe_words[0]
    vibe2 = vibe_words[1] if len(vibe_words) > 1 else vibe1

    # More templates when creativity high
    templates_basic = [
        "{kw1} {product} - {material} {style} | {audience} {occasion}",
        "{product} {kw1} {kw2} | {personalization} {audience} Gift",
        "{kw1} {product} | {color} {style} - Perfect {occasion}",
        "{season} {kw1} {product} | Unique {audience} Gift - {material}",
        "{product} | {kw1} {style} {material} - {occasion} Gift Idea",
        "{kw1} {product} | {personalization} - {audience} {occasion} Gift",
    ]

    templates_extra = [
        "{vibe1} {product} | {kw1} + {kw2} | {occasion} Gift",
        "{product} — {vibe2} {style} | {material} | {audience}",
        "{kw1} {product} | {vibe1} {color} | {season} drop",
        "{product} for {audience} | {kw1} | {personalization}",
        "{vibe1} {product} | gift-ready | {occasion} | {material}",
        "{product} | {kw1} | {kw2} | {vibe2} style",
    ]

    templates = templates_basic[:]
    if creativity >= 6:
        templates += templates_extra

    # Fill
    def fill(t: str) -> str:
        out = t.format(
            kw1=kw1, kw2=kw2,
            product=product, material=material, style=style,
            audience=audience, occasion=occasion, personalization=personalization,
            color=color, season=season_kw, vibe1=vibe1, vibe2=vibe2
        )
        out = re.sub(r"\s+", " ", out).strip()
        out = re.sub(r"\|\s*\|", "|", out)
        out = out.strip(" -|")
        return out

    rng.shuffle(templates)
    titles = []
    for t in templates:
        cand = fill(t)
        if cand and cand not in titles:
            titles.append(cand)
    return titles[:10]

def title_score(title: str, product: str, main_kws: list[str]) -> int:
    score = 0
    t_norm = normalize(title)
    p_norm = normalize(product)
    if p_norm and p_norm in t_norm:
        score += 20

    kw_tokens = []
    for kw in (main_kws or []):
        kw_tokens += [w for w in normalize(kw).split() if w and w not in STOPWORDS]
    kw_tokens = list(dict.fromkeys(kw_tokens))
    hits = [w for w in kw_tokens if w in t_norm]
    score += min(25, 5 * len(hits))

    n = len(title)
    if 110 <= n <= MAX_TITLE_LEN:
        score += 18
    elif 90 <= n < 110:
        score += 10
    elif n > MAX_TITLE_LEN:
        score -= 25
    elif 0 < n < 90:
        score -= 8

    if " | " in title or " - " in title or " — " in title:
        score += 3

    return score

def rank_titles(titles: list[str], product: str, main_kws: list[str]) -> list[dict]:
    out = [{"title": t, "score": title_score(t, product, main_kws)} for t in titles]
    out.sort(key=lambda x: x["score"], reverse=True)
    return out

# =========================
# TAG GUARD + FIX
# =========================
def parse_tags(text: str) -> list[str]:
    if not text:
        return []
    raw = re.split(r"[,\n]+", text)
    return [clean_kw(x) for x in raw if clean_kw(x)]

def smart_trim_tag(tag: str, max_len: int = ETSY_TAG_MAX_LEN) -> str:
    t = normalize(tag)
    if not t:
        return ""
    if len(t) <= max_len:
        return t

    words = [w for w in t.split() if w]
    words2 = [w for w in words if w not in STOPWORDS]
    if words2:
        words = words2

    while words and len(" ".join(words)) > max_len:
        words.pop()

    t2 = " ".join(words).strip()
    if t2 and len(t2) <= max_len:
        return t2

    return t[:max_len].strip()

def dedupe_keep_order(items: list[str]) -> list[str]:
    out, seen = [], set()
    for x in items:
        k = normalize(x)
        if k and k not in seen:
            seen.add(k)
            out.append(x)
    return out

def token_overlap(tag: str) -> set[str]:
    return {w for w in normalize(tag).split() if w and w not in STOPWORDS}

def tag_guard_fix(tags: list[str], required_count: int = ETSY_TAG_COUNT) -> dict:
    original = tags[:]

    fixed = []
    for t in tags:
        tt = smart_trim_tag(t, ETSY_TAG_MAX_LEN)
        if tt:
            fixed.append(tt)

    fixed = dedupe_keep_order(fixed)

    kept = []
    seen_tokens = set()
    for t in fixed:
        toks = token_overlap(t)
        if toks and toks.issubset(seen_tokens) and len(kept) >= 8:
            continue
        kept.append(t)
        seen_tokens |= toks

    fixed = kept

    fillers = ["gift idea", "handmade", "custom", "unique gift", "for her", "for him", "home decor", "birthday gift"]
    i = 0
    while len(fixed) < required_count and i < len(fillers):
        ft = smart_trim_tag(fillers[i], ETSY_TAG_MAX_LEN)
        if ft and ft not in fixed:
            fixed.append(ft)
        i += 1

    fixed = fixed[:required_count]
    too_long = [t for t in fixed if len(t) > ETSY_TAG_MAX_LEN]
    dups = len(fixed) - len(set([t.lower() for t in fixed]))
    return {"original": original, "fixed": fixed, "audit": {"count": len(fixed), "dups": dups, "too_long": too_long}}

# =========================
# Creative Description Engine (EXTREME)
# =========================
def stable_seed(*parts: str) -> int:
    raw = "||".join([p or "" for p in parts])
    h = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def pick1(rng: random.Random, arr: list[str]) -> str:
    return rng.choice(arr) if arr else ""

def pickn_unique(rng: random.Random, arr: list[str], n: int) -> list[str]:
    pool = arr[:]
    rng.shuffle(pool)
    return pool[:max(0, min(n, len(pool)))]

TONES = ["Luxury", "Cozy", "Minimal", "Playful", "Professional"]

TONE_WORDS = {
    "Luxury": {
        "vibes": ["refined", "elegant", "luxury-inspired", "polished", "premium"],
        "sensory": ["silky", "glowing", "radiant", "sleek", "smooth"],
        "verbs": ["elevates", "enhances", "finishes", "completes", "transforms"],
        "promise": ["timeless", "high-end feel", "gift-worthy", "editorial look", "signature style"],
    },
    "Cozy": {
        "vibes": ["warm", "cozy", "comforting", "soft", "homey"],
        "sensory": ["soft", "gentle", "calm", "snug", "inviting"],
        "verbs": ["brightens", "warms", "lifts", "sweetens", "adds charm to"],
        "promise": ["feel-good", "easy to love", "everyday comfort", "cozy vibe", "sweet little detail"],
    },
    "Minimal": {
        "vibes": ["clean", "minimal", "modern", "simple", "understated"],
        "sensory": ["crisp", "clean", "light", "neat", "balanced"],
        "verbs": ["streamlines", "refines", "simplifies", "matches", "pairs with"],
        "promise": ["quiet luxury", "easy styling", "go-with-anything", "minimal charm", "modern classic"],
    },
    "Playful": {
        "vibes": ["cute", "fun", "playful", "cheerful", "bright"],
        "sensory": ["sparkly", "happy", "colorful", "bouncy", "sweet"],
        "verbs": ["pops", "sparks", "brings joy to", "adds fun to", "turns heads in"],
        "promise": ["smile-worthy", "giftable", "conversation starter", "feel-good", "instant favorite"],
    },
    "Professional": {
        "vibes": ["polished", "smart", "clean", "professional", "sleek"],
        "sensory": ["crisp", "smooth", "sharp", "clean", "structured"],
        "verbs": ["supports", "organizes", "simplifies", "improves", "keeps you on track with"],
        "promise": ["clear results", "time-saving", "stress-free", "efficient", "ready-to-use"],
    },
}

CATEGORY_DEFAULTS = {
    "Auto": {},
    "Jewelry": {
        "hero": ["necklace", "ring", "bracelet", "earrings", "pendant"],
        "benefits": ["lightweight", "skin-friendly", "gift-ready", "easy to style", "photo-ready"],
        "bullets": [
            "Comfortable for daily wear (lightweight feel)",
            "Gift-ready packaging included",
            "Designed to layer beautifully with other pieces",
            "A timeless style that matches many outfits",
            "Carefully made and quality-checked",
        ],
    },
    "Home": {
        "hero": ["decor", "wall decor", "mug", "sign", "candle", "home accent"],
        "benefits": ["cozy vibe", "room upgrade", "instant charm", "giftable", "statement look"],
        "bullets": [
            "Instantly upgrades your space with a clean look",
            "Thoughtful gift for housewarming or holidays",
            "Made with care for a neat, long-lasting finish",
            "Packed safely to arrive in great condition",
            "Easy to style in many rooms",
        ],
    },
    "Digital": {
        "hero": ["template", "printable", "planner", "svg", "pdf", "digital download"],
        "benefits": ["instant download", "easy edit", "time-saving", "clean layout", "ready to print"],
        "bullets": [
            "Instant download — use it right away",
            "Clean layout that’s easy to edit and personalize",
            "Designed to save time and reduce overwhelm",
            "Print-friendly and simple to use",
            "Perfect for personal use or gifting",
        ],
    },
    "Fashion": {
        "hero": ["shirt", "hoodie", "dress", "scarf", "bag", "accessory"],
        "benefits": ["comfortable fit", "easy styling", "everyday wear", "giftable", "photo-ready"],
        "bullets": [
            "Comfortable and easy to wear",
            "Pairs well with multiple outfits",
            "Made with attention to detail",
            "Great gift option for everyday style",
            "Ships safely and neatly packed",
        ],
    },
    "Art": {
        "hero": ["art print", "poster", "illustration", "wall art", "print"],
        "benefits": ["statement piece", "gallery vibe", "room upgrade", "giftable", "photo-ready"],
        "bullets": [
            "Creates an instant focal point in your space",
            "A thoughtful gift for art lovers",
            "Clean, modern look that photographs beautifully",
            "Carefully packed to protect during shipping",
            "Easy to style with many decor themes",
        ],
    }
}

HOOK_BANK = [
    "Imagine opening the package and feeling that instant “wow.”",
    "This is the kind of piece people notice — without trying too hard.",
    "A small detail that makes a big difference in your day.",
    "Made for the moments you’ll remember (and the photos you’ll love).",
    "If you love {vibe} style, this one is calling your name.",
    "A {sensory} touch that {verb} your look/space instantly.",
]

MICRO_STORIES = [
    "Picture it with your favorite outfit — effortless and put-together.",
    "It’s the finishing touch that makes everything feel intentional.",
    "It’s designed to feel personal, not mass-produced.",
    "It’s the kind of gift that looks expensive (and feels meaningful).",
    "Simple enough for everyday, special enough for celebrations.",
]

SOCIAL_PROOF_LINES = [
    "Buyers love pieces that are gift-ready and easy to style.",
    "A popular choice when you want something simple but premium-looking.",
    "Great for gifting — it’s the “safe win” that still feels special.",
    "People choose this when they want a clean, modern vibe.",
]

CTA_BANK = [
    "Want it gift-ready? Leave a note at checkout — I’ve got you.",
    "Need help choosing? Message me and I’ll reply fast.",
    "If you want a tiny custom tweak, send a message before ordering.",
    "Add to cart today — your future self will thank you.",
]

def smart_first_two_lines(product: str, main_kws: list[str], benefit: str, audience: str,
                          occasion: str, personalization: str, season: str,
                          tone: str, creativity: int, rng: random.Random) -> tuple[str, str]:
    product = clean_kw(product) or "This item"
    benefit = clean_kw(benefit)
    audience = clean_kw(audience)
    occasion = clean_kw(occasion)
    personalization = clean_kw(personalization)

    seasonal = SEASONAL_PACKS.get(season, [])
    season_kw = seasonal[0] if seasonal else ""

    twords = TONE_WORDS.get(tone, TONE_WORDS["Minimal"])
    vibe = pick1(rng, twords["vibes"])
    promise = pick1(rng, twords["promise"])

    kw = clean_kw(main_kws[0]) if main_kws else ""
    if benefit:
        line1 = f"{product}: {benefit}"
    else:
        if creativity >= 7 and vibe:
            line1 = f"{product}: a {vibe}, {promise} choice"
        else:
            line1 = f"{product}: {kw} designed to stand out" if kw else f"{product}: made to stand out"

    parts = []
    if audience:
        parts.append(f"Perfect for {audience}")
    if occasion:
        parts.append(f"{occasion} gifts")
    if personalization:
        parts.append(personalization)
    if season_kw and creativity >= 5:
        parts.append(season_kw)

    line2 = " • ".join(parts) if parts else "A thoughtful gift that feels premium and personal."
    return re.sub(r"\s+", " ", line1).strip(), re.sub(r"\s+", " ", line2).strip()

def build_bullets(product: str, category: str, audience: str, occasion: str, material: str, style: str, creativity: int, rng: random.Random) -> list[str]:
    base = CATEGORY_DEFAULTS.get(category, CATEGORY_DEFAULTS["Jewelry"]).get("bullets", CATEGORY_DEFAULTS["Jewelry"]["bullets"])[:] \
           if category in CATEGORY_DEFAULTS and category != "Auto" else CATEGORY_DEFAULTS["Jewelry"]["bullets"][:]

    # Add some dynamic bullets when creativity high
    dyn = []
    if creativity >= 6:
        if material:
            dyn.append(f"Materials: {clean_kw(material)} (carefully selected)")
        if style:
            dyn.append(f"Style: {clean_kw(style)} — designed to be easy to match")
        if occasion:
            dyn.append(f"Gift moment: ideal for {clean_kw(occasion)} surprises")
        if audience:
            dyn.append(f"Made with {clean_kw(audience)} in mind")

    pool = base + dyn
    pool = [clean_kw(x) for x in pool if clean_kw(x)]
    rng.shuffle(pool)
    take = 3 if creativity <= 4 else (4 if creativity <= 7 else 5)
    return pool[:take]

def creative_intro(product: str, tone: str, creativity: int, rng: random.Random) -> str:
    twords = TONE_WORDS.get(tone, TONE_WORDS["Minimal"])
    vibe = pick1(rng, twords["vibes"])
    sensory = pick1(rng, twords["sensory"])
    verb = pick1(rng, twords["verbs"])

    hook = pick1(rng, HOOK_BANK).format(vibe=vibe, sensory=sensory, verb=verb)
    if "look/space" in hook:
        hook = hook.replace("look/space", "look" if creativity % 2 == 0 else "space")

    product_clean = clean_kw(product) or "This item"
    if creativity >= 8:
        # stronger opener
        opener = f"{hook} {product_clean} brings a {vibe} feel with a {sensory} finish."
    else:
        opener = f"{product_clean} with a {vibe} vibe — {hook}"
    opener = re.sub(r"\s+", " ", opener).strip()
    return opener

def creative_story(tone: str, creativity: int, rng: random.Random) -> str:
    story = pick1(rng, MICRO_STORIES)
    if creativity >= 8 and rng.random() < 0.6:
        story2 = pick1(rng, SOCIAL_PROOF_LINES)
        return f"{story} {story2}"
    return story

def creative_cta(product: str, occasion: str, creativity: int, rng: random.Random) -> str:
    cta = pick1(rng, CTA_BANK)
    if creativity >= 9 and rng.random() < 0.4:
        cta2 = "If you’re ordering for a gift, I can make it feel extra special."
        return f"{cta} {cta2}"
    return cta

def full_description_extreme(
    product: str,
    main_kws: list[str],
    benefit: str,
    features: str,
    materials_desc: str,
    sizing: str,
    shipping: str,
    personalization: str,
    audience: str,
    occasion: str,
    season: str,
    tone: str,
    category: str,
    material: str,
    style: str,
    color: str,
    creativity: int,
    regen: int,
) -> str:
    rng = random.Random(stable_seed(product, audience, occasion, tone, category, str(creativity), str(regen), "desc"))

    intro = creative_intro(product, tone, creativity, rng)
    story = creative_story(tone, creativity, rng)
    l1, l2 = smart_first_two_lines(product, main_kws, benefit, audience, occasion, personalization, season, tone, creativity, rng)

    # bullets
    user_bullets = [clean_kw(x) for x in (features or "").split("\n") if clean_kw(x)]
    if user_bullets:
        bullets = user_bullets[:8]
    else:
        bullets = build_bullets(product, category if category != "Auto" else "Jewelry", audience, occasion, material, style, creativity, rng)

    # keywords line (expanded)
    kws_line = ", ".join([k for k in main_kws[:10] if k])

    # Optional vibe blocks (when creativity high)
    twords = TONE_WORDS.get(tone, TONE_WORDS["Minimal"])
    vibe = pick1(rng, twords["vibes"])
    promise = pick1(rng, twords["promise"])
    sensory = pick1(rng, twords["sensory"])

    mini_block = ""
    if creativity >= 7:
        mini_lines = [
            f"✨ Vibe: {vibe} • {promise}",
            f"📸 Photo-friendly: a {sensory} detail that stands out nicely",
        ]
        rng.shuffle(mini_lines)
        mini_block = "\n".join(mini_lines[:2])

    cta = creative_cta(product, occasion, creativity, rng)

    desc = [
        intro,
        story,
        "",
        l1,
        l2,
    ]

    if mini_block:
        desc += ["", mini_block]

    desc += [
        "",
        "✅ Why you'll love it:",
        *[f"• {b}" for b in bullets],
    ]

    if materials_desc:
        desc += ["", f"🧵 Materials: {clean_kw(materials_desc)}"]
    if sizing:
        desc += ["", f"📏 Size / Details: {clean_kw(sizing)}"]
    if personalization:
        desc += ["", f"✨ Personalization: {clean_kw(personalization)}"]
    if shipping:
        desc += ["", f"🚚 Shipping: {clean_kw(shipping)}"]
    if kws_line:
        desc += ["", f"🔎 Keywords: {kws_line}"]

    if creativity >= 8 and (color or style):
        extra = []
        if color:
            extra.append(f"Color notes: {clean_kw(color)}")
        if style:
            extra.append(f"Style notes: {clean_kw(style)}")
        desc += ["", " • ".join(extra)]

    desc += ["", cta, "", "📩 Questions? Email support anytime — I’m happy to help!"]
    return "\n".join(desc)

# =========================
# UI
# =========================
st.set_page_config(page_title="Listing-Lift", page_icon="🚀", layout="centered")
st.title(APP_TITLE)

if "creative_regen" not in st.session_state:
    st.session_state["creative_regen"] = 0

top1, top2 = st.columns([2, 1])
with top1:
    st.caption(f"Upgrade store: {STORE_URL}")
with top2:
    st.link_button("🛒 Buy / Upgrade", STORE_URL, use_container_width=True)

pro_users = load_pro_users()
usage = load_usage()

with st.sidebar:
    st.subheader("Account")
    email = st.text_input("Your email", placeholder="you@email.com").strip().lower()
    email_ok = bool(email) and is_valid_email(email)
    if email and not email_ok:
        st.warning("Please enter a valid email.")

    pro_active = email_ok and (email in pro_users)

    st.markdown("---")
    st.subheader("Plan")
    if pro_active:
        st.success("✅ Pro active (by email)")
        st.write("Unlimited generations.")
    else:
        st.info("Free plan")
        st.write(f"- {FREE_DAILY_LIMIT} generations/day")
        st.link_button("Open Listing-Lift Store", STORE_URL, use_container_width=True)

    st.markdown("---")
    st.subheader("Support")
    st.write(SUPPORT_EMAIL)
    copy_button(SUPPORT_EMAIL, key="copy_support_email_sidebar", label="Copy Support Email")

if not email_ok:
    st.info("Enter your email in the sidebar to enable Generate.")

tab_gen, tab_upgrade = st.tabs(["🚀 Generator", "💎 Upgrade / Pricing"])

# =========================
# Generator
# =========================
with tab_gen:
    st.subheader("Listing inputs")

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("✨ Load Example", use_container_width=True):
            apply_example()
    with b2:
        if st.button("🔄 Reset", use_container_width=True):
            reset_inputs()
    with b3:
        if st.button("🎲 Regenerate Creative Version", use_container_width=True):
            st.session_state["creative_regen"] = int(st.session_state.get("creative_regen", 0)) + 1
            st.success("Creative version changed ✅ (Generate again)")
            st.rerun()

    st.markdown("---")
    st.subheader("Creative Controls (NO AI)")

    cA, cB = st.columns(2)
    with cA:
        tone = st.selectbox("Tone", options=TONES, index=2)
    with cB:
        category = st.selectbox("Category", options=list(CATEGORY_DEFAULTS.keys()), index=0)

    creativity = st.slider("Creativity Level", min_value=1, max_value=10, value=8, help="Higher = more varied hooks, story, and sections")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Product type", key="product")
        st.text_input("Material", key="material")
        st.text_input("Style", key="style")
        st.text_input("Color (optional)", key="color")
    with col2:
        st.text_input("Target audience", key="audience")
        st.text_input("Occasion", key="occasion")
        st.text_input("Personalization (optional)", key="personalization")

    st.text_input("Main keywords (comma-separated)", key="keywords")
    st.text_input("Main benefit (for first line)", key="benefit")
    st.selectbox("Seasonality", options=list(SEASONAL_PACKS.keys()), key="season", index=0)

    st.markdown("---")
    st.subheader("Description details (optional)")
    st.text_area("Key features (one per line)", key="features", height=120)
    st.text_input("Materials text", key="materials_desc")
    st.text_input("Sizing / Details", key="sizing")
    st.text_input("Shipping policy snippet", key="shipping")

    st.markdown("---")
    st.subheader("Tag Guard (optional)")
    st.caption("Paste tags (comma or new lines). We will fix to 13 tags and 20 chars.")
    st.text_area("Paste Tags", key="paste_tags", height=90, placeholder="tag1, tag2, tag3 ...")

    gen = st.button("🚀 Generate Listing Pack", use_container_width=True)

    if gen:
        if not email_ok:
            st.error("Enter a valid email first.")
            st.stop()

        if not pro_active:
            used = get_free_used(usage, email)
            if used >= FREE_DAILY_LIMIT:
                st.error("Free limit reached for today. Upgrade to Pro for unlimited generations.")
                st.link_button("🛒 Upgrade", STORE_URL, use_container_width=True)
                st.stop()

        # Collect inputs
        product = st.session_state.get("product", "")
        material = st.session_state.get("material", "")
        style = st.session_state.get("style", "")
        color = st.session_state.get("color", "")
        audience = st.session_state.get("audience", "")
        occasion = st.session_state.get("occasion", "")
        personalization = st.session_state.get("personalization", "")
        keywords = st.session_state.get("keywords", "")
        benefit = st.session_state.get("benefit", "")
        season = st.session_state.get("season", "None")
        features = st.session_state.get("features", "")
        materials_desc = st.session_state.get("materials_desc", "")
        sizing = st.session_state.get("sizing", "")
        shipping = st.session_state.get("shipping", "")
        paste_tags = st.session_state.get("paste_tags", "")
        regen = int(st.session_state.get("creative_regen", 0))

        base_kws = split_keywords(keywords)

        # RNG for consistent but varied outputs
        rng = random.Random(stable_seed(product, audience, occasion, tone, category, str(creativity), str(regen), "main"))

        # Expand keywords offline for richer variety
        expanded_kws = expand_keywords(base_kws, product, material, style, color, audience, occasion, creativity, rng)

        # Titles
        raw_titles = title_variations(
            product, expanded_kws, material, style, audience, occasion, personalization, color, season,
            tone=tone, creativity=creativity, rng=rng
        )
        ranked = rank_titles(raw_titles, product, expanded_kws)
        best_title = ranked[0]["title"] if ranked else ""

        # Tags candidates (use expanded kws)
        base_tags = []
        for t in [product, material, style, color, audience, occasion, personalization]:
            if clean_kw(t):
                base_tags.append(t)
        base_tags += expanded_kws[:18]
        base_tags += ["gift", "handmade", "custom", "unique gift"]

        gen_fix = tag_guard_fix(base_tags, required_count=ETSY_TAG_COUNT)
        best_tags = gen_fix["fixed"]

        pasted_fix = None
        if str(paste_tags).strip():
            pasted_fix = tag_guard_fix(parse_tags(paste_tags), required_count=ETSY_TAG_COUNT)

        # Description (EXTREME)
        desc = full_description_extreme(
            product=product,
            main_kws=expanded_kws,
            benefit=benefit,
            features=features,
            materials_desc=materials_desc,
            sizing=sizing,
            shipping=shipping,
            personalization=personalization,
            audience=audience,
            occasion=occasion,
            season=season,
            tone=tone,
            category=category,
            material=material,
            style=style,
            color=color,
            creativity=creativity,
            regen=regen,
        )

        # Count free usage
        if not pro_active:
            inc_free_used(usage, email)
            save_usage(usage)
            used_now = get_free_used(usage, email)
        else:
            used_now = None

        st.success("✅ Generated (Extreme Creativity)")

        payload_all = (
            f"BEST TITLE:\n{best_title}\n\n"
            f"BEST 13 TAGS:\n{', '.join(best_tags)}\n\n"
            f"DESCRIPTION:\n{desc}"
        )

        st.subheader("✅ Quick Apply")
        c1, c2, c3 = st.columns(3)
        with c1:
            copy_button(best_title, key="copy_best_title", label="Copy Best Title")
        with c2:
            copy_button(", ".join(best_tags), key="copy_best_tags", label="Copy Best 13 Tags")
        with c3:
            copy_button(payload_all, key="copy_all", label="Copy ALL ✅")

        st.markdown("---")
        st.subheader("Tag Guard + Fix (Generated Tags)")
        l, r = st.columns(2)
        with l:
            st.markdown("**Before (raw)**")
            st.write(gen_fix["original"][:20])
        with r:
            st.markdown("**After (fixed)**")
            st.write(best_tags)
            copy_button(", ".join(best_tags), key="copy_fixed_generated", label="Copy Fixed Tags")
        st.caption(f"Audit: count={gen_fix['audit']['count']} | duplicates={gen_fix['audit']['dups']} | too_long={len(gen_fix['audit']['too_long'])}")

        if pasted_fix:
            st.markdown("---")
            st.subheader("Tag Guard + Fix (Your Pasted Tags)")
            l2, r2 = st.columns(2)
            with l2:
                st.markdown("**Before**")
                st.write(pasted_fix["original"])
            with r2:
                st.markdown("**After**")
                st.write(pasted_fix["fixed"])
                copy_button(", ".join(pasted_fix["fixed"]), key="copy_fixed_pasted", label="Copy Fixed Pasted Tags")

        st.markdown("---")
        st.subheader("1) Titles (Ranked)")
        for i, item in enumerate(ranked, start=1):
            t = item["title"]
            score = item["score"]
            n = len(t)
            if i == 1:
                st.success(f"🏆 Best Title (Score {score}) — {n}/{MAX_TITLE_LEN}")
            else:
                if n > MAX_TITLE_LEN:
                    st.error(f"Title {i} (Score {score}) — {n}/{MAX_TITLE_LEN} (OVER)")
                elif n >= 130:
                    st.warning(f"Title {i} (Score {score}) — {n}/{MAX_TITLE_LEN} (close)")
                else:
                    st.caption(f"Title {i} (Score {score}) — {n}/{MAX_TITLE_LEN}")

            a, b = st.columns([8, 2])
            with a:
                st.text_area(f"Title {i}", value=t, height=68, key=f"title_area_{i}")
            with b:
                copy_button(t, key=f"copy_title_{i}", label="Copy")

        st.markdown("---")
        st.subheader("2) Description")
        lines = desc.splitlines()
        if len(lines) >= 2:
            st.markdown("**Etsy preview (first 2 lines):**")
            st.info(f"{lines[0]}\n\n{lines[1]}")
        st.text_area("Full description", value=desc, height=320, key="desc_area")
        copy_button(desc, key="copy_desc", label="Copy Description")

        # Downloads
        export_data = {
            "best_title": best_title,
            "ranked_titles": ranked,
            "best_13_tags": best_tags,
            "description": desc,
            "creative_controls": {
                "tone": tone,
                "category": category,
                "creativity_level": creativity,
                "creative_version": regen,
            },
            "meta": {
                "product": product,
                "material": material,
                "style": style,
                "color": color,
                "audience": audience,
                "occasion": occasion,
                "personalization": personalization,
                "keywords_input": base_kws,
                "keywords_expanded": expanded_kws[:30],
                "season": season,
                "generated_on": date.today().isoformat(),
            }
        }
        json_bytes = json.dumps(export_data, ensure_ascii=False, indent=2).encode("utf-8")

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["SECTION", "KEY", "VALUE"])
        writer.writerow(["BEST", "Best Title", best_title])
        writer.writerow(["BEST", "Best 13 Tags", ", ".join(best_tags)])
        writer.writerow(["BEST", "Tone", tone])
        writer.writerow(["BEST", "Category", category])
        writer.writerow(["BEST", "Creativity", str(creativity)])
        writer.writerow(["BEST", "Creative Version", str(regen)])
        writer.writerow(["BEST", "Description", desc])
        writer.writerow([])
        writer.writerow(["RANKED_TITLES", "Title", "Score"])
        for x in ranked:
            writer.writerow(["RANKED_TITLES", x["title"], x["score"]])

        txt_bytes = payload_all.encode("utf-8")
        csv_bytes = csv_buffer.getvalue().encode("utf-8-sig")

        st.markdown("---")
        st.subheader("⬇️ Downloads")
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("Download JSON", data=json_bytes, file_name="listinglift_pack.json",
                               mime="application/json", use_container_width=True)
        with d2:
            st.download_button("Download CSV", data=csv_bytes, file_name="listinglift_pack.csv",
                               mime="text/csv", use_container_width=True)
        with d3:
            st.download_button("Download TXT", data=txt_bytes, file_name="listinglift_pack.txt",
                               mime="text/plain", use_container_width=True)

        if not pro_active and used_now is not None:
            st.caption(f"Free usage today: {used_now}/{FREE_DAILY_LIMIT}")

# =========================
# Upgrade tab
# =========================
with tab_upgrade:
    st.title("💎 Upgrade to Pro (Listing-Lift)")
    st.write("Buy from LemonSqueezy — Pro gives unlimited generations.")
    st.link_button("🛒 Open Listing-Lift Store", STORE_URL, use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Free")
        st.markdown(f"- {FREE_DAILY_LIMIT} generations/day\n- Downloads")
    with c2:
        st.markdown("### Pro")
        st.markdown("- ✅ Unlimited generations\n- ✅ Downloads JSON/CSV/TXT\n- ✅ Support by email")

    st.markdown("---")
    st.subheader("Support")
    st.write(SUPPORT_EMAIL)
    copy_button(SUPPORT_EMAIL, key="copy_support_email_upgrade", label="Copy Support Email")

st.markdown("---")
st.caption("Listing-Lift • Pro activation by email • No WhatsApp")