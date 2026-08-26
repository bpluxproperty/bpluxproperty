# -*- coding: utf-8 -*-
"""Generatore blog statico B&P Lux Property.
Legge blog/contenuti/*.json e scrive HTML completo in public/blog/.
Contenuto nell'HTML (niente JS per il testo) come da manuale SEO.
"""
import os, json, re, html, datetime, sys, zlib

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))          # .../blog
SITE=os.path.abspath(os.path.join(ROOT,".."))                               # .../SITO_REACT
CONT=os.path.join(ROOT,"contenuti")
OUT=os.path.join(SITE,"public","blog")
ART_DIR=os.path.join(CONT,"articoli")

def load(p):
    with open(p,encoding="utf-8") as f: return json.load(f)

ent=load(os.path.join(CONT,"entita.json"))
S=ent["site"]; CATS={c["id"]:c for c in ent["categories"]}
CAT_ORDER=[c["id"] for c in sorted(ent["categories"],key=lambda x:x["order"])]
WA=S["whatsapp"]; WA_PREFILL=ent["cta"]["whatsappPrefill"]

articles=[]
for fn in sorted(os.listdir(ART_DIR)):
    if fn.endswith(".json"):
        try: articles.append(load(os.path.join(ART_DIR,fn)))
        except Exception as e: print("  ! JSON invalido:",fn,e)
BY={a["slug"]:a for a in articles}

# ---------------- CANCELLO DI CONTENUTO ----------------
warn=[]
def gate(a):
    s=a["slug"]
    t=a.get("title","")
    if len(t)>60: warn.append(f"[{s}] title {len(t)}>60")
    md=a.get("metaDescription","")
    if not(90<=len(md)<=170): warn.append(f"[{s}] metaDescription {len(md)} fuori 120-160")
    if a.get("h1","")==t: warn.append(f"[{s}] h1 == title")
    if len(a.get("sections",[]))<5: warn.append(f"[{s}] sezioni {len(a.get('sections',[]))}<5")
    if len(a.get("faq",[]))<4: warn.append(f"[{s}] faq {len(a.get('faq',[]))}<4")
    for r in a.get("related",[]):
        if r==s: warn.append(f"[{s}] related verso se stesso")
        elif r not in BY: warn.append(f"[{s}] related inesistente: {r}")
for a in articles: gate(a)

# ---------------- FORMATTAZIONE INLINE ----------------
def esc(x): return html.escape(x or "",quote=True)
LINK_RE=re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+|/[^\s)]+)\)")
INTERNAL_RE=re.compile(r"(?<![\w/])(/agenzie-immobiliari|/blog/[a-z0-9\-/]+)")
def inline(t):
    t=esc(t)
    # link markdown [testo](url)
    def _l(m):
        url=m.group(2); ext=url.startswith("http")
        rel=' target="_blank" rel="noopener"' if ext else ''
        return f'<a href="{url}"{rel}>{m.group(1)}</a>'
    t=LINK_RE.sub(_l,t)
    # grassetto **testo**
    t=re.sub(r"\*\*([^*]+)\*\*",r"<strong>\1</strong>",t)
    # autolink percorsi interni nudi
    t=INTERNAL_RE.sub(lambda m:f'<a href="{m.group(1)}">{m.group(1).strip("/").replace("/"," ")}</a>' if not re.search(r'href="[^"]*$',t[:m.start()]) else m.group(1),t)
    return t

KEY_TERMS=["property manager","prezzi dinamici","imposta di soggiorno","cedolare secca","self check-in","Alloggiati Web","CIN","Superhost","recensioni","occupazione"]
_BOLD={"n":0,"done":set()}
MAXBOLD=5
def auto_bold_raw(t):
    if not t or _BOLD["n"]>=MAXBOLD: return t
    masks=[]
    def _mask(m): masks.append(m.group(0)); return f"\x00{len(masks)-1}\x00"
    t=LINK_RE.sub(_mask,t)
    for term in KEY_TERMS:
        if _BOLD["n"]>=MAXBOLD: break
        if term in _BOLD["done"]: continue
        m=re.compile(r"(?<![0-9A-Za-zàèéìòùÀÈÉÌÒÙ])("+re.escape(term)+r")(?![0-9A-Za-zàèéìòùÀÈÉÌÒÙ])",re.I).search(t)
        if m:
            t=t[:m.start()]+"**"+m.group(1)+"**"+t[m.end():]
            _BOLD["n"]+=1; _BOLD["done"].add(term)
    for i,orig in enumerate(masks): t=t.replace(f"\x00{i}\x00",orig)
    return t
LINK_MAP=[("property manager","property-manager-affitti-brevi"),("CIN","cin-affitti-brevi-come-ottenerlo"),("cedolare secca","cedolare-secca-affitti-brevi"),("pulizie e biancheria","pulizie-e-biancheria-affitti-brevi"),("imposta di soggiorno","imposta-di-soggiorno-affitti-brevi"),("Alloggiati Web","alloggiati-web-comunicazione-ospiti"),("prezzi dinamici","prezzi-dinamici-affitti-brevi"),("self check-in","self-check-in-affitti-brevi"),("channel manager","channel-manager-affitti-brevi"),("home staging","home-staging-affitti-brevi"),("foto professionali","foto-professionali-affitti-brevi"),("Superhost","come-diventare-superhost")]
_LINK={"n":0,"done":set()}
_SELF={"slug":""}
MAXLINK=4
def auto_link_raw(t):
    if not t or _LINK["n"]>=MAXLINK: return t
    masks=[]
    def _mask(m): masks.append(m.group(0)); return f"\x01{len(masks)-1}\x01"
    t=LINK_RE.sub(_mask,t)
    for term,slug in LINK_MAP:
        if _LINK["n"]>=MAXLINK: break
        if slug in _LINK["done"] or slug==_SELF["slug"]: continue
        m=re.compile(r"(?<![0-9A-Za-zàèéìòùÀÈÉÌÒÙ])("+re.escape(term)+r")(?![0-9A-Za-zàèéìòùÀÈÉÌÒÙ])",re.I).search(t)
        if m:
            t=t[:m.start()]+f"[{m.group(1)}](/blog/{slug}/)"+t[m.end():]
            _LINK["n"]+=1; _LINK["done"].add(slug)
    for i,orig in enumerate(masks): t=t.replace(f"\x01{i}\x01",orig)
    return t
def pullquote_for(a):
    # Cita solo osservazioni di esperienza, mai la presentazione aziendale, e rimuove la frase
    # dal paragrafo di origine: altrimenti il lettore la ritrova identica poco piu sotto.
    pat=re.compile(r"[^.!?]*\b(nostra esperienza|Nella nostra|da property manager|Superhost|lo vediamo di continuo|nel nostro lavoro|l'errore (?:più|piu|che)|abbiamo (?:visto|imparato))\b[^.!?]*[.!?]",re.I)
    selfpres=re.compile(r"(B&P Lux Property|gestiamo (?:affitti|appartamenti|case|immobili)|lavoriamo ogni giorno|con base in Emilia-Romagna|siamo Superhost|come Superhost e)",re.I)
    for sec in a.get("sections",[]):
        for i,p in enumerate(sec.get("paragraphs",[])):
            hay,off=p,0
            if i==0:
                m0=re.search(r"[.!?]\s+",p)
                if not m0: continue
                off=m0.end(); hay=p[off:]
            m=pat.search(hay)
            if not m: continue
            q=m.group(0).strip()
            if not (45<=len(q)<=210): continue
            if selfpres.search(q): continue
            rest=(p[:off+m.start()]+p[off+m.end():]).strip()
            if len(rest.split())<12: continue
            sec["paragraphs"][i]=re.sub(r"\s{2,}"," ",rest)
            return f'<blockquote class="pull"><p>{inline(q)}</p></blockquote>'
    return ""
def paras(lst, ab=False): return "".join(f"<p>{inline(auto_bold_raw(auto_link_raw(p)) if ab else p)}</p>" for p in (lst or []))
def ul(lst, ab=False):
    if not lst: return ""
    return "<ul>"+"".join(f"<li>{inline(auto_bold_raw(auto_link_raw(x)) if ab else x)}</li>" for x in lst)+"</ul>"
def table(tb):
    if not tb: return ""
    h="".join(f"<th>{inline(x)}</th>" for x in tb.get("headers",[]))
    rows="".join("<tr>"+"".join(f"<td>{inline(c)}</td>" for c in r)+"</tr>" for r in tb.get("rows",[]))
    return f'<div class="tbl"><table><thead><tr>{h}</tr></thead><tbody>{rows}</tbody></table></div>'

# ---------------- HELPER PREMIUM ----------------
from urllib.parse import quote as _q
WA_LINK='https://wa.me/'+WA+'?text='+_q(WA_PREFILL)
WA_SVG='<svg viewBox="0 0 24 24" width="26" height="26" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15l-1.3 4.9 5-1.3A10 10 0 1 0 12 2zm0 2a8 8 0 1 1-4.1 14.9l-.3-.2-2.6.7.7-2.5-.2-.3A8 8 0 0 1 12 4zm4.4 9.7c-.2-.1-1.4-.7-1.6-.8-.2-.1-.4-.1-.5.1l-.7.9c-.1.2-.3.2-.5.1a6.5 6.5 0 0 1-3.2-2.8c-.1-.2 0-.4.1-.5l.4-.5c.1-.1.1-.3 0-.4l-.7-1.7c-.2-.4-.4-.4-.5-.4h-.5c-.2 0-.4.1-.6.3-.7.7-.8 1.7-.4 2.7a9 9 0 0 0 3.9 4.1c1.4.7 2 .7 2.7.6.5-.1 1.4-.6 1.6-1.1.2-.5.2-1 .1-1.1z"/></svg>'
HERO_POOL={
 "dozza-emilia-romagna":["/assets/dozza/dozza-1.jpg","/assets/dozza/dozza-5.jpg","/assets/dozza/dozza-2.jpg"],
 "gestione":["/blog/assets/ai/gestione.jpg","/blog/assets/ai/citta-2.jpg"],
 "quanto-rende":["/blog/assets/ai/quanto-rende.jpg","/blog/assets/ai/citta-1.jpg"],
 "citta":["/blog/assets/ai/citta-1.jpg","/blog/assets/ai/citta-2.jpg","/blog/assets/ai/citta-3.jpg"],
 "normativa-fisco":["/blog/assets/ai/fisco.jpg","/blog/assets/ai/quanto-rende.jpg"],
 "piattaforme":["/blog/assets/ai/piattaforme.jpg","/blog/assets/ai/citta-3.jpg"],
 "affitti-brevi":["/blog/assets/ai/guida.jpg","/blog/assets/ai/citta-2.jpg"],
 "preparare-casa":["/blog/assets/ai/preparare-casa.jpg","/blog/assets/ai/citta-1.jpg"],
}
def hero_for(a):
    if a.get("heroImage"): return a["heroImage"]
    pool=HERO_POOL.get(a.get("category"),["/assets/prop1.jpg"])
    return pool[sum(ord(ch) for ch in a["slug"])%len(pool)]
def reading_time(a):
    w=len((a.get("opening","")).split())
    for s in a.get("sections",[]):
        for p in s.get("paragraphs",[]): w+=len(p.split())
        for l in (s.get("list") or []): w+=len(l.split())
    for q in a.get("faq",[]): w+=len(q.get("a","").split())
    return max(3,round(w/200))
def cta_inline():
    return f'''<div class="cta-inline">
  <div><strong>Non hai tempo di gestirlo? Lo facciamo noi.</strong><span>A costo iniziale zero: siamo a percentuale. Ti costruiamo la rendita, poi resta tua.</span></div>
  <div class="ci-btns"><a class="btn btn-gold" href="#contatti-blog">Parlaci del tuo immobile</a><a class="btn btn-wa" href="{WA_LINK}" target="_blank" rel="noopener">WhatsApp</a></div>
</div>'''
def side_bar(a):
    seen={a["slug"]}; links=[]
    for r in a.get("related",[]):
        if r in BY and r not in seen: seen.add(r); links.append(BY[r])
    for x in articles:
        if len(links)>=5: break
        if x["category"]==a["category"] and x["slug"] not in seen: seen.add(x["slug"]); links.append(x)
    links_html="".join(f'<li><a href="/blog/{x["slug"]}/">{esc(x.get("h1") or x.get("title"))}</a></li>' for x in links)
    cats_html="".join(f'<a href="/blog/categoria/{cid}/">{esc(CATS[cid]["name"])}</a>' for cid in CAT_ORDER)
    return f'''<aside class="side">
  <div class="side-card side-val">
    <span class="sv-k">Valutazione gratuita</span>
    <p>Scopri quanto può rendere il tuo immobile come affitto breve. La calcoliamo noi, sui numeri reali.</p>
    <a class="btn btn-gold" href="#contatti-blog">Richiedi la valutazione</a>
  </div>
  {calc_card()}
  <div class="side-card side-wa">
    <span class="sw-t">Preferisci WhatsApp?</span>
    <a class="btn btn-wa" href="{WA_LINK}" target="_blank" rel="noopener">{WA_SVG}<span>Scrivici ora</span></a>
    <img src="/blog/assets/wa-qr.png" alt="QR per scrivere a B&P Lux Property su WhatsApp" width="128" height="128" loading="lazy">
    <span class="sw-q">Inquadra il QR per scriverci</span>
  </div>
  <div class="side-card side-list">
    <span class="sl-k">Articoli utili</span>
    <ul>{links_html}</ul>
  </div>
  <div class="side-card side-cats">
    <span class="sl-k">Esplora per categoria</span>
    <div class="sc-tags">{cats_html}</div>
  </div>
  {newsletter_box()}
  <a class="side-card side-dozza" href="/blog/dove-dormire-a-dozza-appartamento/">
    <span class="sd-k">Il nostro immobile</span>
    <strong>Loft nel centro di Dozza</strong>
    <span class="sd-r">&#9733; 4,97 &middot; Superhost</span>
    <span class="sd-go">Scoprilo &rarr;</span>
  </a>
</aside>'''
def share_box(a):
    u=_q(art_url(a["slug"])+"/"); t=_q(a.get("h1") or a.get("title"))
    return f'''<div class="share"><span>Condividi</span>
  <a href="https://wa.me/?text={t}%20{u}" target="_blank" rel="noopener">WhatsApp</a>
  <a href="https://www.facebook.com/sharer/sharer.php?u={u}" target="_blank" rel="noopener">Facebook</a>
  <a href="https://www.linkedin.com/sharing/share-offsite/?url={u}" target="_blank" rel="noopener">LinkedIn</a>
  <a href="https://twitter.com/intent/tweet?url={u}&text={t}" target="_blank" rel="noopener">X</a>
</div>'''
AUTORI = ent.get("autori", [])
def autore_per(a):
    """Firma l'articolo con il co-founder competente per la categoria (deterministico)."""
    if not AUTORI: return None
    cat = a.get("category", "")
    # le guide citta sono la categoria piu numerosa: si dividono fra i due founder,
    # altrimenti una firma da sola coprirebbe metà del blog
    if cat == "citta" and len(AUTORI) > 1:
        return AUTORI[zlib.crc32(a.get("slug", "").encode()) % 2]
    for au in AUTORI:
        if cat in au.get("categorie", []): return au
    return AUTORI[zlib.crc32(a.get("slug", "").encode()) % len(AUTORI)]

def author_box(au=None):
    if not au:
        o = ent["author"]
        return f'''<div class="authorbox">
  <div class="ab-badge">B&amp;P</div>
  <div class="ab-txt"><strong>{esc(o["name"])}</strong><span>{esc(o["role"])}</span><p>{esc(o["bio"])}</p></div>
</div>'''
    comp = " &middot; ".join(esc(c) for c in au.get("competenze", [])[:3])
    return f'''<div class="authorbox">
  <img class="ab-img" src="{au["foto"]}" alt="{esc(au["nome"])}" width="72" height="72" loading="lazy">
  <div class="ab-txt"><strong>{esc(au["nome"])}</strong><span>{esc(au["ruolo"])}</span><p>{esc(au["bio"])}</p>
  <p class="ab-comp">Si occupa di: {comp}. <a href="/blog/autori/">Chi scrive su questo blog &rarr;</a></p></div>
</div>'''

def calc_card():
    return '''<a class="side-card side-calc" href="/blog/calcolatore-rendita/">
  <span class="sd-k">Strumento gratuito</span>
  <strong>Calcolatore di rendita</strong>
  <span class="sc-go">Stima quanto può rendere il tuo immobile &rarr;</span>
</a>'''
def newsletter_box():
    return '''<div class="side-card side-news">
  <span class="sl-k">Newsletter</span>
  <p>Consigli sugli affitti brevi, ogni tanto. Niente spam.</p>
  <form class="news-form" onsubmit="return bpNews(event)"><input name="email" type="email" required placeholder="La tua email" aria-label="Email"><button class="btn btn-gold" type="submit">Iscriviti</button></form>
</div>'''
def trust_strip():
    return '''<section class="trust"><div class="wrap trust-in">
  <div class="tr"><strong>4,97&#9733;</strong><span>oltre 30 recensioni</span></div>
  <div class="tr"><strong>Superhost</strong><span>su Airbnb</span></div>
  <div class="tr"><strong>360&deg;</strong><span>gestione completa</span></div>
  <div class="tr"><strong>0&euro;</strong><span>costi iniziali, solo a %</span></div>
</div></section>'''

# ---------------- COMPONENTI ----------------
def cta_block(cid=""):
    idattr=f' id="{cid}"' if cid else ""
    return f'''<section class="cta"{idattr} aria-label="Contattaci">
  <div class="cta-in">
    <div class="cta-txt">
      <span class="kick">{esc(ent["cta"]["titolo"])}</span>
      <p>{esc(ent["cta"]["testo"])}</p>
    </div>
    <form class="cta-form" onsubmit="return bpLead(event)">
      <input name="nome" required placeholder="Nome e cognome" aria-label="Nome e cognome">
      <input name="email" type="email" required placeholder="Email" aria-label="Email">
      <input name="telefono" placeholder="Telefono / WhatsApp" aria-label="Telefono o WhatsApp">
      <input name="citta" placeholder="Città dell'immobile" aria-label="Città dell'immobile">
      <button type="submit" class="btn btn-gold">{esc(ent["cta"]["bottone"])}</button>
      <a class="wa" href="https://wa.me/{WA}?text={esc(WA_PREFILL).replace(' ','%20')}" target="_blank" rel="noopener">&#128241; {esc(ent["cta"]["whatsappTesto"])} ({esc(S["whatsappDisplay"])})</a>
    </form>
  </div>
</section>'''

def header():
    links="".join(f'<a href="/blog/categoria/{c}/">{esc(CATS[c]["name"])}</a>' for c in CAT_ORDER[:4])
    return f'''<header class="top"><div class="wrap top-in">
  <a class="brand" href="/blog/"><span class="bt">B&amp;P<small>Lux Property</small></span></a>
  <nav class="topnav">{links}<a class="nav-guida" href="/blog/guida-proprietario/">Guida proprietario</a><a class="nav-rec" href="/blog/recensioni-b-p-lux-property/">Recensioni</a><a class="nav-calc" href="/blog/calcolatore-rendita/">Calcolatore</a><a class="btn btn-ghost" href="/">Sito &rarr;</a></nav>
</div></header>'''

def footer():
    cols="".join(f'<a href="/blog/categoria/{c}/">{esc(CATS[c]["name"])}</a>' for c in CAT_ORDER)
    return f'''<section class="foot-news"><div class="wrap foot-news-in">
  <div class="fn-txt"><span class="fn-k">Iscriviti alla newsletter</span><p>Consigli sugli affitti brevi e novità dal blog, ogni tanto. Niente spam.</p></div>
  <form class="news-form" onsubmit="return bpNews(event)"><input name="email" type="email" required placeholder="La tua email" aria-label="Email"><button class="btn btn-gold" type="submit">Iscriviti</button></form>
</div></section>
<footer class="foot"><div class="wrap foot-in">
  <div><strong>B&amp;P Lux Property</strong><br><span class="muted">{esc(S["tagline"])}</span></div>
  <div class="foot-links">{cols}<a href="/blog/calcolatore-rendita/">Calcolatore rendita</a></div>
  <div class="muted">{esc(S["email"])} &middot; <a href="https://wa.me/{WA}" target="_blank" rel="noopener">WhatsApp {esc(S["whatsappDisplay"])}</a><br><a href="/privacy.html">Privacy</a> &middot; <a href="/termini.html">Termini</a></div>
</div></footer>'''

def page(title, desc, canonical, body, jsonld, extra_head="", og_image=None):
    ld="".join(f'<script type="application/ld+json">{json.dumps(x,ensure_ascii=False)}</script>' for x in jsonld)
    ogimg=og_image or (S["url"]+"/blog/og/_default.png")
    return f'''<!doctype html><html lang="it"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:site_name" content="B&P Lux Property">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{ogimg}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{ogimg}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/blog/blog.css">{extra_head}
{ld}
</head><body>
{header()}
{body}
{footer()}
<a class="fab-wa" href="{WA_LINK}" target="_blank" rel="noopener" aria-label="Scrivici su WhatsApp">{WA_SVG}</a>
<script src="/blog/blog.js" defer></script>
</body></html>'''

def art_url(slug): return f'{S["url"]}/blog/{slug}'
def card(a):
    c=CATS.get(a["category"],{})
    return f'''<a class="card cat-{a["category"]}" href="/blog/{a["slug"]}/">
  <span class="card-cat">{esc(c.get("name",""))}</span>
  <span class="card-h">{esc(a.get("h1") or a.get("title"))}</span>
  <span class="card-x">{esc(a.get("excerpt",""))}</span>
  <span class="card-go">Leggi &rarr;</span></a>'''

# ---------------- ARTICOLO ----------------
def render_article(a):
    c=CATS.get(a["category"],{})
    _BOLD["n"]=0; _BOLD["done"]=set()
    _LINK["n"]=0; _LINK["done"]=set(); _SELF["slug"]=a["slug"]
    au=autore_per(a)
    pq=pullquote_for(a); nsec=len(a.get("sections",[]))
    pq_at=(nsec-2) if nsec>=4 else -1
    if pq_at==2: pq_at=3
    secs_html=""; toc=[]
    for i,sec in enumerate(a.get("sections",[])):
        sid=f"s{i+1}"; toc.append((sid,sec["h2"]))
        secs_html+=f'<section id="{sid}"><h2>{esc(sec["h2"])}</h2>{paras(sec.get("paragraphs"),True)}{ul(sec.get("list"),True)}{table(sec.get("table"))}</section>'
        if i==2: secs_html+=cta_inline()   # CTA a meta
        if pq and i==pq_at: secs_html+=pq
    toc_html=""
    if len(toc)>=5:
        toc_html='<nav class="toc"><span>In questa guida</span><ol>'+"".join(f'<li><a href="#{i}">{esc(h)}</a></li>' for i,h in toc)+'</ol></nav>'
    faq_html="".join(f'<details><summary>{esc(q["q"])}</summary><p>{inline(q["a"])}</p></details>' for q in a.get("faq",[]))
    rel=[BY[r] for r in a.get("related",[]) if r in BY]
    rel_html="".join(card(r) for r in rel)
    src_html=""
    if a.get("sources"):
        items="".join(f'<li>{("<a href=\""+esc(s["url"])+"\" target=\"_blank\" rel=\"noopener\">"+esc(s["label"])+"</a>") if s.get("url") else esc(s.get("label",""))} — {esc(s.get("ente",""))}{(", "+esc(str(s["data"]))) if s.get("data") else ""}</li>' for s in a["sources"])
        src_html=f'<section class="sources"><h2>Fonti</h2><ul>{items}</ul></section>'
    disc='<p class="disclaimer">Contenuto informativo, aggiornato alla data di pubblicazione: non sostituisce una consulenza professionale. Per il tuo caso specifico, verifica con un professionista o contattaci.</p>' if a.get("disclaimer") else ""
    hero=hero_for(a); rt=reading_time(a)
    tldr=f'<aside class="tldr"><span class="tldr-k">In sintesi</span><p>{inline(a.get("excerpt",""))}</p></aside>' if a.get("excerpt") else ""
    hero_style=f'background-image:linear-gradient(180deg,rgba(22,20,15,.30),rgba(22,20,15,.82)),url({hero})'
    body=f'''<main class="art-wrap cat-{a["category"]}">
<nav class="crumb wrap"><a href="/blog/">Blog</a> / <a href="/blog/categoria/{a["category"]}/">{esc(c.get("name",""))}</a> / <span>{esc(a.get("h1") or a.get("title"))}</span></nav>
<div class="art-hero-img" style="{hero_style}">
  <div class="ahi-in wrap">
    <span class="kick">{esc(a.get("heroKicker") or c.get("name",""))}</span>
    <h1>{esc(a.get("h1") or a.get("title"))}</h1>
    <div class="meta">A cura di <a class="by" href="/blog/autori/">{esc(au["nome"]) if au else esc(ent["author"]["name"])}</a>{" &middot; "+esc(au["ruolo"]) if au else ""} &middot; {rt} min di lettura &middot; agg. {esc(a.get("updatedAt",""))}</div>
  </div>
</div>
<div class="art-grid wrap">
  <article class="body">
    <p class="opening">{inline(auto_bold_raw(a.get("opening","")))}</p>
    {toc_html}
    {secs_html}
    {tldr}
    {disc}
    {share_box(a)}
    {author_box(au)}
    {src_html}
    <section class="faqs"><h2>Domande frequenti</h2>{faq_html}</section>
  </article>
  {side_bar(a)}
</div>
{cta_block("contatti-blog")}
<section class="related wrap"><h2>Continua a leggere</h2><div class="cards">{rel_html}</div></section>
</main>'''
    # schema
    ld=[
      {"@context":"https://schema.org","@type":"BlogPosting","headline":a.get("h1") or a.get("title"),
       "description":a.get("metaDescription",""),"datePublished":a.get("publishedAt"),"dateModified":a.get("updatedAt"),
       "author":({"@type":"Person","name":au["nome"],"jobTitle":au["ruolo"],"url":S["url"]+"/blog/autori/","worksFor":{"@type":"Organization","name":S["name"],"url":S["url"]}} if au else {"@type":"Organization","name":S["name"]}),
       "publisher":{"@type":"Organization","name":"B&P Lux Property","url":S["url"]},
       "mainEntityOfPage":art_url(a["slug"])},
      {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q["q"],"acceptedAnswer":{"@type":"Answer","text":q["a"]}} for q in a.get("faq",[])]},
      {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":1,"name":"Blog","item":f'{S["url"]}/blog/'},
        {"@type":"ListItem","position":2,"name":c.get("name",""),"item":f'{S["url"]}/blog/categoria/{a["category"]}/'},
        {"@type":"ListItem","position":3,"name":a.get("h1") or a.get("title"),"item":art_url(a["slug"])}]}]
    title=a.get("title")
    out=os.path.join(OUT,a["slug"],"index.html")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    open(out,"w",encoding="utf-8").write(page(title,a.get("metaDescription",""),art_url(a["slug"]),body,ld,og_image=f'{S["url"]}/blog/og/{a["slug"]}.png'))

# ---------------- CATEGORIA ----------------
def render_category(cid):
    c=CATS[cid]; arts=[a for a in articles if a["category"]==cid]
    cards="".join(card(a) for a in arts) or '<p class="muted">Presto nuovi articoli in questa sezione.</p>'
    body=f'''<main class="hub">
<nav class="crumb wrap"><a href="/blog/">Blog</a> / <span>{esc(c["name"])}</span></nav>
<div class="hero cat-hero"><span class="kick">Categoria</span><h1>{esc(c["h1"])}</h1><p class="lead">{esc(c["intro"])}</p></div>
<div class="cat-block"><div class="cards">{cards}</div></div>
{cta_block()}
</main>'''
    ld=[{"@context":"https://schema.org","@type":"CollectionPage","name":c["h1"],"description":c["intro"]},
        {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
          {"@type":"ListItem","position":1,"name":"Blog","item":f'{S["url"]}/blog/'},
          {"@type":"ListItem","position":2,"name":c["name"],"item":f'{S["url"]}/blog/categoria/{cid}/'}]}]
    out=os.path.join(OUT,"categoria",cid,"index.html"); os.makedirs(os.path.dirname(out),exist_ok=True)
    open(out,"w",encoding="utf-8").write(page(f'{c["name"]} | Blog B&P Lux Property',c["intro"][:155],f'{S["url"]}/blog/categoria/{cid}/',body,ld))

# ---------------- HUB /blog ----------------
def render_hub():
    feat=articles[:3]
    feat_html="".join(card(a) for a in feat)
    cat_secs=""
    for cid in CAT_ORDER:
        arts=[a for a in articles if a["category"]==cid]
        if not arts: continue
        cat_secs+=f'''<section class="cat-block"><div class="cat-head"><h2>{esc(CATS[cid]["name"])}</h2><a href="/blog/categoria/{cid}/">Vedi tutti &rarr;</a></div><div class="cards">{"".join(card(a) for a in arts[:3])}</div></section>'''
    agenzie=f'''<section class="agenzie-band"><div class="wrap ab-in">
  <span class="kick gold">Per le agenzie immobiliari</span>
  <h2>Hai immobili invenduti o sfitti? Falli rendere mentre restano sul mercato.</h2>
  <p>Affida a noi gli appartamenti che la tua agenzia non riesce a vendere o affittare: li gestiamo come affitti brevi di lusso <strong>mentre restano in vendita</strong>. Tu incassi una rendita passiva, a costo zero e in white-label &mdash; il cliente resta tuo. Della burocrazia 2026 (CIN, cedolare, P.IVA) ci occupiamo noi.</p>
  <ul class="ab-points"><li>Rendita passiva sull'invenduto</li><li>0&euro; costi iniziali, solo a percentuale</li><li>White-label: non tocchiamo il tuo cliente</li></ul>
  <a class="btn btn-gold" href="/agenzie-immobiliari">Scopri la partnership per agenzie &rarr;</a>
</div></section>'''
    body=f'''<main class="hub">
<div class="hero blog-hero"><span class="kick">Il blog di B&amp;P Lux Property</span>
  <h1>Affitti brevi, senza giri di parole.</h1>
  <p class="lead">Guide pratiche su rendita, regole, Airbnb, Booking e gestione &mdash; scritte da chi gestisce case vere ogni giorno.</p></div>
{trust_strip()}
<section class="guida-band"><div class="wrap gb-in">
  <div><span class="kick gold">Guida del proprietario</span><h2>Hai una seconda casa? Falla diventare un secondo stipendio.</h2><p>Il percorso completo, passo dopo passo, per metterla a reddito &mdash; oppure la gestiamo noi a costo iniziale zero.</p></div>
  <a class="btn btn-gold" href="/blog/guida-proprietario/">Apri la guida &rarr;</a>
</div></section>
<section class="intro-band"><p>{esc(ent["blogHubIntro"])}</p></section>
<section class="calc-hl"><div class="wrap calc-hl-in">
  <div><span class="kick">Strumento gratuito</span><h2>Quanto può rendere il tuo immobile?</h2><p>Fai una stima in trenta secondi con il nostro calcolatore. Poi, se vuoi, ti prepariamo l'analisi precisa e gratuita.</p></div>
  <a class="btn btn-gold" href="/blog/calcolatore-rendita/">Prova il calcolatore &rarr;</a>
</div></section>
<section class="cat-block"><div class="cat-head"><h2>In evidenza</h2></div><div class="cards">{feat_html}</div></section>
{cat_secs}
{agenzie}
{cta_block()}
</main>'''
    ld=[{"@context":"https://schema.org","@type":"Blog","name":"Blog B&P Lux Property","url":f'{S["url"]}/blog/',"description":ent["blogHubIntro"][:200]},
        {"@context":"https://schema.org","@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"url":art_url(a["slug"])} for i,a in enumerate(articles)]}]
    open(os.path.join(OUT,"index.html"),"w",encoding="utf-8").write(
        page("Blog affitti brevi | B&P Lux Property","Guide pratiche sugli affitti brevi: quanto rende, regole e fisco, Airbnb e Booking, gestione. Da un property manager Superhost.",f'{S["url"]}/blog/',body,ld))

# ---------------- GUIDA DEL PROPRIETARIO (pilastro) ----------------
GUIDE_PHASES=[
 ("Decidere e valutare","Capire se conviene, con quale formula partire e quanto può rendere.",["come-iniziare-affitti-brevi-guida","affitto-breve-o-lungo-cosa-conviene","conviene-comprare-casa-per-affitto-breve","casa-vacanze-o-affitto-breve-differenze","come-calcolare-rendita-affitto-breve","quanto-si-guadagna-affitti-brevi-italia","quanto-tempo-serve-gestire-affitto-breve"]),
 ("Regole, fisco e burocrazia","CIN, tasse e adempimenti spiegati semplici, senza sorprese.",["cin-affitti-brevi-come-ottenerlo","cedolare-secca-affitti-brevi","imposta-di-soggiorno-affitti-brevi","alloggiati-web-comunicazione-ospiti","contratto-locazione-breve","terzo-immobile-partita-iva-affitti-brevi","affitti-brevi-e-condominio","assicurazione-affitti-brevi","comunicazione-istat-affitti-brevi","tasse-affitti-brevi-quanto-si-paga","adempimenti-affitti-brevi-checklist","regole-affitti-brevi-emilia-romagna","quando-serve-commercialista-affitti-brevi"]),
 ("Preparare l'immobile","Rendere la casa pronta, sicura e desiderabile per gli ospiti.",["arredare-casa-per-affitti-brevi","kit-di-benvenuto-affitti-brevi","smart-home-affitti-brevi","foto-professionali-affitti-brevi","dotazioni-must-have-affitti-brevi","aumentare-posti-letto-affitto-breve","scorte-e-consumabili-affitti-brevi","wifi-e-internet-affitti-brevi","sicurezza-alloggio-affitti-brevi","checklist-primo-ospite-affitti-brevi","home-staging-affitti-brevi","serratura-smart-affitti-brevi"]),
 ("Pubblicare e prezzare","Annuncio, portali giusti e prezzo che riempie il calendario.",["come-funziona-airbnb-host","airbnb-o-booking","annuncio-perfetto-airbnb","prezzi-dinamici-affitti-brevi","commissioni-airbnb-quanto-trattiene","channel-manager-affitti-brevi","crea-account-host-airbnb","come-creare-annuncio-airbnb","griglia-foto-annuncio-airbnb","usare-ai-per-annuncio-airbnb","pubblicare-casa-su-booking","programma-genius-booking","politica-cancellazione-airbnb","promozioni-e-sconti-airbnb","come-e-quando-paga-airbnb","aumentare-tariffa-media-affitti-brevi","ranking-airbnb-come-farsi-trovare"]),
 ("Gestire gli ospiti","Check-in, pulizie, recensioni e assistenza, anche a distanza.",["check-in-check-out-affitti-brevi","self-check-in-affitti-brevi","pulizie-e-biancheria-affitti-brevi","recensioni-5-stelle-affitti-brevi","come-gestire-recensioni-negative-affitti-brevi","cauzione-e-danni-affitti-brevi","gestione-affitti-brevi-a-distanza","messaggi-automatici-ospiti-airbnb","regole-della-casa-affitti-brevi","guida-di-benvenuto-ospiti","manutenzione-affitti-brevi"]),
 ("Crescere e ottimizzare","Alzare rendita, occupazione e reputazione. O delegare tutto.",["come-diventare-superhost","come-aumentare-prenotazioni-airbnb","come-destagionalizzare-affitti-brevi","errori-affitti-brevi-da-evitare","gestione-affitti-brevi-fai-da-te-o-agenzia","quanto-costa-property-manager-affitti-brevi","property-manager-affitti-brevi","nicchie-affitti-brevi","affidare-casa-a-gestore-domande"]),
]
def render_guida():
    steps=""; n=0
    for i,(titolo,intro,slugs) in enumerate(GUIDE_PHASES):
        arts=[BY[s] for s in slugs if s in BY]
        if not arts: continue
        n+=len(arts)
        cards="".join(card(a) for a in arts)
        steps+=f'''<section class="guide-phase" id="fase-{i+1}"><div class="gp-head"><span class="gp-num">{i+1}</span><div><h2>{esc(titolo)}</h2><p>{esc(intro)}</p></div></div><div class="cards">{cards}</div></section>'''
    body=f'''<main class="hub guida">
<nav class="crumb wrap"><a href="/blog/">Blog</a> / <span>Guida del proprietario</span></nav>
<div class="guida-hero"><div class="wrap">
  <span class="kick">Guida del proprietario</span>
  <h1>Hai una seconda casa? Trasformala in un secondo stipendio.</h1>
  <p class="lead">Il percorso completo, passo dopo passo, per mettere a reddito il tuo appartamento con gli affitti brevi: dalle regole alla gestione, {n} guide pratiche. E se non hai tempo, la costruiamo noi a costo iniziale zero.</p>
  <div class="gh-btns"><a class="btn btn-gold" href="#contatti-blog">Fatti aiutare da noi</a><a class="btn btn-ghost-d" href="#fase-1">Inizia la guida &darr;</a></div>
</div></div>
{steps}
{cta_block("contatti-blog")}
</main>'''
    ld=[{"@context":"https://schema.org","@type":"CollectionPage","name":"Guida del proprietario per gli affitti brevi","description":"Guida passo dopo passo per mettere a reddito la tua seconda casa con gli affitti brevi."},
        {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Blog","item":S["url"]+"/blog/"},{"@type":"ListItem","position":2,"name":"Guida del proprietario","item":S["url"]+"/blog/guida-proprietario/"}]}]
    out=os.path.join(OUT,"guida-proprietario","index.html"); os.makedirs(os.path.dirname(out),exist_ok=True)
    open(out,"w",encoding="utf-8").write(page("Guida del proprietario: mettere a reddito casa | B&P Lux Property","Guida completa passo dopo passo per mettere a reddito la tua seconda casa con gli affitti brevi: regole, fisco, preparazione, gestione. O la gestiamo noi a costo iniziale zero.",S["url"]+"/blog/guida-proprietario/",body,ld))

# ---------------- RECENSIONI / REPUTAZIONE ----------------
REP=ent.get("reputazione",{})
DZ=ent["dozza"]
def _quotes(limit=None):
    qs=REP.get("citazioni",[])[:limit] if limit else REP.get("citazioni",[])
    return "".join(f'''<figure class="rv-card"><blockquote><p>&laquo;{esc(q["testo"])}&raquo;</p></blockquote><figcaption><strong>{esc(q["autore"])}</strong><span>{esc(q.get("paese",""))} &middot; recensione verificata su {esc(q["fonte"])}</span></figcaption></figure>''' for q in qs)
def _scores():
    ab=REP.get("airbnb",{}); bk=REP.get("booking",{})
    cats="".join(f'<div class="score"><span class="score-n">{esc(v)}</span><span class="score-l">{esc(k)}</span></div>' for k,v in bk.get("categorie",[]))
    badges="".join(f'<span class="rv-badge">{esc(b)}</span>' for b in ab.get("badge",[]))
    return f'''<div class="plat-grid">
  <div class="plat"><span class="plat-k">Airbnb</span><span class="plat-v">{esc(ab.get("rating",""))}<small>/{ab.get("su",5)}</small></span><span class="plat-n">{ab.get("recensioni",0)} recensioni</span><div class="rv-badges">{badges}</div></div>
  <div class="plat"><span class="plat-k">Booking.com</span><span class="plat-v">{esc(bk.get("rating",""))}<small>/{bk.get("su",10)}</small></span><span class="plat-n">{bk.get("recensioni",0)} recensioni &middot; {esc(bk.get("giudizio",""))}</span></div>
</div>
<div class="score-grid">{cats}</div>
<p class="rv-note">Punteggi per categoria rilevati dall'annuncio pubblico su Booking.com. Le valutazioni cambiano nel tempo: puoi verificarle in qualsiasi momento direttamente sugli annunci.</p>'''

def render_recensioni():
    ab=REP.get("airbnb",{}); bk=REP.get("booking",{})
    body=f'''<main class="hub guida cat-dozza-emilia-romagna">
<nav class="crumb wrap"><a href="/blog/">Blog</a> / <span>Recensioni degli appartamenti</span></nav>
<div class="guida-hero"><div class="wrap">
  <span class="kick">Recensioni verificate</span>
  <h1>Cosa dicono gli ospiti degli appartamenti che gestiamo</h1>
  <p class="lead">Non chiediamo di fiderti sulla parola: i punteggi qui sotto sono quelli pubblici dei nostri annunci su Airbnb e Booking, e le recensioni sono scritte dagli ospiti dopo il soggiorno. Puoi controllarle tu, in due clic.</p>
  <div class="gh-btns"><a class="btn btn-gold" href="{DZ["airbnb"]}" target="_blank" rel="noopener">Verifica su Airbnb</a><a class="btn btn-ghost-d" href="{DZ["booking"]}" target="_blank" rel="noopener">Verifica su Booking</a></div>
</div></div>
<section class="guide-phase wrap"><div class="gp-head"><span class="gp-num">1</span><div><h2>I punteggi, piattaforma per piattaforma</h2><p>Media reale sugli annunci del {esc(DZ["nome"])}, il nostro appartamento nel centro storico.</p></div></div>
{_scores()}
</section>
<section class="guide-phase wrap"><div class="gp-head"><span class="gp-num">2</span><div><h2>Le parole degli ospiti</h2><p>Recensioni pubbliche, riportate testualmente. Nessuna raccolta a pagamento, nessun testo modificato.</p></div></div>
<div class="rv-grid">{_quotes()}</div>
</section>
<section class="guide-phase wrap"><div class="gp-head"><span class="gp-num">3</span><div><h2>Perché queste recensioni contano per te</h2><p>Se stai valutando di affidarci la tua casa, questo è il metro di giudizio più onesto.</p></div></div>
<div class="tldr"><p>Un punteggio alto e costante non nasce dal caso: nasce da pulizia curata, risposte rapide, istruzioni chiare e una casa che mantiene le promesse dell'annuncio. Sono esattamente le cose che facciamo ogni giorno sugli immobili che gestiamo — e sono le stesse che, applicate al tuo, alzano tariffa e occupazione.</p></div>
<p>Nota di trasparenza: le recensioni in questa pagina riguardano gli <strong>alloggi che gestiamo</strong> e sono scritte dagli ospiti che ci hanno soggiornato. I punteggi sono quelli mostrati pubblicamente da Airbnb e Booking alla data indicata e possono cambiare con i soggiorni successivi.</p>
<p>Se invece cerchi opinioni sul nostro lavoro come property manager, le trovi nella pagina dedicata: <a href="/blog/recensioni-b-p-lux-property/">recensioni e reputazione di B&amp;P Lux Property</a>.</p>
{cta_block("contatti-blog")}
</main>'''
    ld=[{"@context":"https://schema.org","@type":"LodgingBusiness","name":DZ["nome"],
         "address":{"@type":"PostalAddress","streetAddress":DZ.get("indirizzo",""),"postalCode":DZ.get("cap",""),"addressLocality":DZ.get("citta",""),"addressRegion":"Emilia-Romagna","addressCountry":"IT"},
         "url":S["url"]+"/blog/recensioni-appartamenti/","sameAs":[DZ["airbnb"],DZ["booking"]],
         "aggregateRating":{"@type":"AggregateRating","ratingValue":ab.get("rating","").replace(",","."),"bestRating":"5","reviewCount":ab.get("recensioni",0)}},
        {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Blog","item":S["url"]+"/blog/"},{"@type":"ListItem","position":2,"name":"Recensioni degli appartamenti","item":S["url"]+"/blog/recensioni-appartamenti/"}]}]
    out=os.path.join(OUT,"recensioni-appartamenti","index.html"); os.makedirs(os.path.dirname(out),exist_ok=True)
    open(out,"w",encoding="utf-8").write(page(f'Recensioni dei nostri appartamenti: {ab.get("rating","")}/5 su Airbnb',f'Le recensioni verificate degli ospiti sugli appartamenti che gestiamo: {ab.get("rating","")}/5 su Airbnb ({ab.get("recensioni",0)} recensioni) e {bk.get("rating","")}/10 su Booking. Verificabili sugli annunci.',S["url"]+"/blog/recensioni-appartamenti/",body,ld))

FAQ_REP=[("B&P Lux Property è affidabile?","Sì, ed è verificabile: gli appartamenti che gestiamo hanno lo status Superhost su Airbnb, il badge «{}» e una media di {} su 5 in {} recensioni pubbliche, oltre a {} su 10 su Booking.com. Non sono numeri dichiarati da noi: sono quelli mostrati dalle piattaforme sui nostri annunci, che puoi aprire e controllare in qualsiasi momento."),
 ("Che recensioni ha B&P Lux Property?","Le recensioni riguardano gli alloggi che gestiamo e le scrivono gli ospiti dopo il soggiorno. Su Booking i punteggi per categoria migliori sono Staff, Servizi e Posizione (10/10), con un rapporto qualità-prezzo di 9,6. Su Airbnb la media è {} su 5 in {} recensioni."),
 ("Cosa fa esattamente B&P Lux Property?","Gestiamo affitti brevi per conto dei proprietari, a 360 gradi: annuncio e foto, prezzi dinamici, comunicazione con gli ospiti, check-in, pulizie e biancheria, adempimenti e recensioni. Il proprietario resta proprietario: noi facciamo funzionare la casa come struttura ricettiva."),
 ("Quanto costa affidare la casa a B&P Lux Property?","A costo iniziale zero: lavoriamo a percentuale sugli incassi, quindi guadagniamo solo se guadagni tu. Non chiediamo canoni fissi di attivazione e, quando vuoi, con una fee di uscita ti lasciamo il business già avviato: da quel momento la rendita è tua."),
 ("Dove operate?","Il nostro immobile di riferimento è a Dozza, nel cuore dell'Emilia-Romagna tra Imola e Bologna, e lavoriamo in questa zona e in Italia. Se hai una casa altrove, scrivici: valutiamo l'immobile e ti diciamo onestamente se possiamo seguirla bene."),
 ("Le recensioni che pubblicate sono vere?","Sì. Sono recensioni pubbliche degli ospiti, riportate testualmente e con la fonte indicata, e i punteggi sono quelli che vedi sugli annunci Airbnb e Booking. In fondo a ogni pagina trovi i link diretti agli annunci per verificarle da solo: non pubblichiamo testimonianze che non siano verificabili.")]
def render_reputazione():
    ab=REP.get("airbnb",{}); bk=REP.get("booking",{})
    badge=(ab.get("badge") or ["Superhost"])[-1]
    fq=[]
    fq.append((FAQ_REP[0][0],FAQ_REP[0][1].format(badge,ab.get("rating",""),ab.get("recensioni",0),bk.get("rating",""))))
    fq.append((FAQ_REP[1][0],FAQ_REP[1][1].format(ab.get("rating",""),ab.get("recensioni",0))))
    for q,a in FAQ_REP[2:]: fq.append((q,a))
    faq_html="".join(f'<details class="faq-i"><summary>{esc(q)}</summary><div><p>{esc(a)}</p></div></details>' for q,a in fq)
    body=f'''<main class="hub guida cat-gestione">
<nav class="crumb wrap"><a href="/blog/">Blog</a> / <span>Recensioni e reputazione</span></nav>
<div class="guida-hero"><div class="wrap">
  <span class="kick">Recensioni e reputazione</span>
  <h1>B&amp;P Lux Property: recensioni, opinioni e reputazione</h1>
  <p class="lead">Stai valutando se affidarci la tua casa e vuoi capire con chi hai a che fare. Giusto. Qui trovi chi siamo, cosa facciamo e — soprattutto — le prove verificabili del nostro lavoro, con i link per controllarle da solo.</p>
  <div class="gh-btns"><a class="btn btn-gold" href="#contatti-blog">Parlaci del tuo immobile</a><a class="btn btn-ghost-d" href="/blog/recensioni-appartamenti/">Vedi le recensioni degli ospiti</a></div>
</div></div>
<section class="guide-phase wrap"><div class="gp-head"><span class="gp-num">1</span><div><h2>Chi siamo, in breve</h2><p>Un property manager, non un portale.</p></div></div>
<p>B&amp;P Lux Property gestisce <strong>affitti brevi</strong> per conto dei proprietari. Ci occupiamo dell'immobile a 360 gradi — annuncio, foto, prezzi, ospiti, pulizie, biancheria, adempimenti e recensioni — mentre la casa resta tua. Siamo <strong>Superhost</strong> su Airbnb e gestiamo un appartamento nel centro storico di {esc(DZ.get("citta","Dozza"))}, in Emilia-Romagna, che è anche il nostro banco di prova quotidiano.</p>
<p>Il modello è semplice e senza sorprese: <strong>costo iniziale zero</strong>, lavoriamo a percentuale sugli incassi. Guadagniamo solo se guadagni tu e, quando vuoi, con una fee di uscita ti lasciamo il business già avviato.</p>
</section>
<section class="guide-phase wrap"><div class="gp-head"><span class="gp-num">2</span><div><h2>Le prove, non le promesse</h2><p>Questi numeri sono pubblici sugli annunci che gestiamo: aprili e controllali.</p></div></div>
{_scores()}
</section>
<section class="guide-phase wrap"><div class="gp-head"><span class="gp-num">3</span><div><h2>Cosa dicono gli ospiti</h2><p>Recensioni pubbliche reali, riportate testualmente e con la fonte.</p></div></div>
<div class="rv-grid">{_quotes(3)}</div>
<p><a href="/blog/recensioni-appartamenti/">Leggi tutte le recensioni degli appartamenti &rarr;</a></p>
</section>
<section class="guide-phase wrap"><div class="gp-head"><span class="gp-num">4</span><div><h2>Come verificare tutto in due minuti</h2><p>La reputazione si controlla, non si crede.</p></div></div>
<ul>
<li><strong>Apri l'annuncio su Airbnb</strong>: trovi media, numero di recensioni, badge Superhost e i testi degli ospiti. <a href="{DZ["airbnb"]}" target="_blank" rel="noopener">Vai all'annuncio</a>.</li>
<li><strong>Apri l'annuncio su Booking</strong>: trovi il punteggio complessivo e quello per categoria. <a href="{DZ["booking"]}" target="_blank" rel="noopener">Vai all'annuncio</a>.</li>
<li><strong>Controlla il codice identificativo</strong>: l'alloggio è registrato con CIN <strong>{esc(DZ["cin"])}</strong>, indicato anche sugli annunci.</li>
<li><strong>Guarda come lavoriamo</strong>: le {len(articles)} guide di questo blog raccontano il metodo, non slogan.</li>
</ul>
<div class="tldr"><p>Per trasparenza: le recensioni pubblicate qui sono degli <strong>ospiti</strong> sugli alloggi che gestiamo, non testimonianze di proprietari. Stiamo raccogliendo anche quelle dei proprietari che seguiamo e le pubblicheremo con nome e riferimento verificabile, come facciamo con tutto il resto.</p></div>
</section>
<section class="guide-phase wrap"><div class="gp-head"><span class="gp-num">5</span><div><h2>Domande frequenti su di noi</h2><p>Le risposte che cerchi prima di affidare una casa a qualcuno.</p></div></div>
<div class="faq">{faq_html}</div>
</section>
{cta_block("contatti-blog")}
</main>'''
    ld=[{"@context":"https://schema.org","@type":"Organization","name":S["name"],"url":S["url"],"email":S["email"],"telephone":"+"+WA,
         "description":ent["author"]["bio"],"areaServed":"IT","sameAs":[DZ["airbnb"],DZ["booking"]],
         "address":{"@type":"PostalAddress","addressLocality":DZ.get("citta",""),"addressRegion":"Emilia-Romagna","addressCountry":"IT"}},
        {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in fq]},
        {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Blog","item":S["url"]+"/blog/"},{"@type":"ListItem","position":2,"name":"Recensioni e reputazione","item":S["url"]+"/blog/recensioni-b-p-lux-property/"}]}]
    out=os.path.join(OUT,"recensioni-b-p-lux-property","index.html"); os.makedirs(os.path.dirname(out),exist_ok=True)
    open(out,"w",encoding="utf-8").write(page("B&P Lux Property: recensioni, opinioni e reputazione","Recensioni e opinioni su B&P Lux Property: chi siamo, cosa facciamo e le prove verificabili del nostro lavoro (Superhost, "+str(ab.get("rating",""))+"/5 su Airbnb, "+str(bk.get("rating",""))+"/10 su Booking).",S["url"]+"/blog/recensioni-b-p-lux-property/",body,ld))

def render_autori():
    cards = ""
    for au in AUTORI:
        comp = "".join(f"<li>{esc(c)}</li>" for c in au.get("competenze", []))
        cards += f'''<article class="au-card">
  <img src="{au["foto"]}" alt="{esc(au["nome"])}" width="120" height="120" loading="lazy">
  <div><h2>{esc(au["nome"])}</h2><span class="au-role">{esc(au["ruolo"])}</span>
  <p>{esc(au["bio"])}</p><span class="au-k">Si occupa di</span><ul class="au-comp">{comp}</ul></div>
</article>'''
    body = f'''<main class="hub guida">
<nav class="crumb wrap"><a href="/blog/">Blog</a> / <span>Chi scrive</span></nav>
<div class="guida-hero"><div class="wrap">
  <span class="kick">Chi scrive su questo blog</span>
  <h1>Le persone dietro le guide di B&amp;P Lux Property</h1>
  <p class="lead">Questo blog non e scritto da una redazione anonima: lo firmiamo noi due, che gestiamo affitti brevi ogni giorno. Qui trovi chi siamo, di cosa ci occupiamo e come verificare il nostro lavoro.</p>
</div></div>
<section class="guide-phase wrap"><div class="au-grid">{cards}</div>
<div class="tldr"><p>Ogni articolo porta la firma di chi se ne occupa per competenza: le guide su rendita, fisco e gestione sono curate da Davide, quelle su annunci, prezzi, allestimento e territorio da Stefano. Non pubblichiamo contenuti che non passino da uno di noi due.</p></div>
<p>La nostra reputazione e verificabile: i punteggi pubblici degli alloggi che gestiamo sono raccolti nella pagina <a href="/blog/recensioni-b-p-lux-property/">recensioni e reputazione</a>, con i link diretti agli annunci su Airbnb e Booking.</p>
</section>
{cta_block("contatti-blog")}
</main>'''
    ld = [{"@context":"https://schema.org","@type":"AboutPage","name":"Chi scrive sul blog di B&P Lux Property",
           "mainEntity":[{"@type":"Person","name":au["nome"],"jobTitle":au["ruolo"],
                          "worksFor":{"@type":"Organization","name":S["name"],"url":S["url"]},
                          "knowsAbout":au.get("competenze",[])} for au in AUTORI]},
          {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":"Blog","item":S["url"]+"/blog/"},
            {"@type":"ListItem","position":2,"name":"Chi scrive","item":S["url"]+"/blog/autori/"}]}]
    out = os.path.join(OUT, "autori", "index.html"); os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page(
      "Chi scrive sul blog di B&P Lux Property",
      "Le persone dietro le guide: Davide Bertocchi e Stefano Puggioni, co-founder di B&P Lux Property, property manager e Superhost su Airbnb.",
      S["url"]+"/blog/autori/", body, ld))

# ---------------- SITEMAP ----------------
def sitemap():
    urls=[f'{S["url"]}/blog/']+[f'{S["url"]}/blog/categoria/{c}/' for c in CAT_ORDER if any(a["category"]==c for a in articles)]+[art_url(a["slug"])+"/" for a in articles]
    now=datetime.date(2026,8,11).isoformat()
    body='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for a in articles:
        body+=f'<url><loc>{art_url(a["slug"])}/</loc><lastmod>{a.get("updatedAt",now)}</lastmod></url>\n'
    for u in [f'{S["url"]}/blog/',f'{S["url"]}/blog/guida-proprietario/',f'{S["url"]}/blog/calcolatore-rendita/',f'{S["url"]}/blog/recensioni-appartamenti/',f'{S["url"]}/blog/recensioni-b-p-lux-property/',f'{S["url"]}/blog/autori/']+[f'{S["url"]}/blog/categoria/{c}/' for c in CAT_ORDER if any(a["category"]==c for a in articles)]:
        body+=f'<url><loc>{u}</loc><lastmod>{now}</lastmod></url>\n'
    body+='</urlset>\n'
    open(os.path.join(OUT,"sitemap.xml"),"w",encoding="utf-8").write(body)

# ---------------- CALCOLATORE ----------------
CALC_CITIES=[("Milano","A"),("Venezia","A"),("Firenze","A"),("Como","A"),("Sorrento","A"),
 ("Roma","B"),("Bologna","B"),("Verona","B"),("Napoli","B"),("Matera","B"),("Siena","B"),("Bolzano","B"),("La Spezia / Cinque Terre","B"),
 ("Torino","C"),("Genova","C"),("Rimini","C"),("Bergamo","C"),("Padova","C"),("Trento","C"),("Bari","C"),("Lecce","C"),("Palermo","C"),("Catania","C"),("Cagliari","C"),("Salerno","C"),("Pisa","C"),("Perugia","C"),
 ("Altra città / provincia","D")]
CALC_SCRIPT='''<script>
(function(){
 var ADR={A:[110,175],B:[85,130],C:[65,100],D:[50,80]};
 var OCC={centro:[0.60,0.74],semicentro:[0.50,0.64],fuori:[0.40,0.54],turistica:[0.45,0.62]};
 var BEDS={"2":1,"4":1.35,"6":1.7,"8":2.05};
 function g(id){return document.getElementById(id);}
 function r5(n){return Math.round(n/500)*500;}
 function f(n){return n.toLocaleString("it-IT");}
 var b=g("cGo"); if(!b) return;
 b.addEventListener("click",function(){
   var o=g("cCitta").selectedOptions[0], tier=(o&&o.getAttribute("data-tier"))||"C";
   var occ=OCC[g("cPos").value], adr=ADR[tier], bm=BEDS[g("cBeds").value];
   var low=r5(adr[0]*bm*365*occ[0]), high=r5(adr[1]*bm*365*occ[1]);
   g("cRange").innerHTML="&euro; "+f(low)+" &ndash; &euro; "+f(high)+" <small>/ anno (lordo)</small>";
   var occp=Math.round((occ[0]+occ[1])/2*100);
   g("cSub").innerHTML="Occupazione indicativa ~"+occp+"% &middot; netto stimato &euro; "+f(r5(low*0.62))+" &ndash; &euro; "+f(r5(high*0.62))+" /anno, dopo i costi di gestione";
   g("cOut").hidden=false; g("cOut").scrollIntoView({behavior:"smooth",block:"nearest"});
 });
})();
</script>'''
def render_calculator():
    opts="".join('<option data-tier="%s">%s</option>'%(t,esc(n)) for n,t in CALC_CITIES)
    ui='''<main class="art-wrap">
<nav class="crumb wrap"><a href="/blog/">Blog</a> / <span>Calcolatore di rendita</span></nav>
<div class="art-hero-img" style="background-image:linear-gradient(180deg,rgba(22,20,15,.5),rgba(22,20,15,.86)),url(/assets/prop2.jpg)">
  <div class="ahi-in wrap"><span class="kick">Strumento gratuito</span><h1>Calcolatore di rendita affitto breve</h1><div class="meta">Una stima indicativa in trenta secondi &middot; poi l'analisi precisa e gratuita sul tuo immobile</div></div>
</div>
<div class="calc wrap">
  <div class="calc-card">
    <div class="calc-form">
      <label>Città / provincia<select id="cCitta">__OPTS__</select></label>
      <label>Posti letto<select id="cBeds"><option value="2">1-2</option><option value="4">3-4</option><option value="6">5-6</option><option value="8">7+</option></select></label>
      <label>Posizione<select id="cPos"><option value="centro">In centro</option><option value="semicentro">Semicentro</option><option value="fuori">Fuori / periferia</option><option value="turistica">Localita turistica (mare/montagna)</option></select></label>
      <button class="btn btn-gold" id="cGo" type="button">Calcola la stima</button>
    </div>
    <div class="calc-out" id="cOut" hidden>
      <span class="co-k">Stima ricavo lordo annuo</span>
      <div class="co-range" id="cRange">&mdash;</div>
      <div class="co-sub" id="cSub"></div>
      <p class="co-note">Stima indicativa basata su medie di mercato per città, tipologia e zona: <strong>non è un preventivo</strong>. Il dato reale dipende dal singolo immobile.</p>
      <div class="co-lead">
        <strong>Vuoi il numero preciso sul tuo immobile?</strong>
        <p>Te lo calcoliamo gratis, con i dati reali della tua zona e della tua casa. Lasciaci un recapito:</p>
        <form class="cta-form" onsubmit="return bpLead(event)">
          <input name="nome" required placeholder="Nome e cognome" aria-label="Nome e cognome">
          <input name="email" type="email" required placeholder="Email" aria-label="Email">
          <input name="telefono" placeholder="Telefono / WhatsApp" aria-label="Telefono">
          <input name="citta" placeholder="Città e zona dell'immobile" aria-label="Città immobile">
          <button class="btn btn-gold" type="submit">Richiedi l'analisi gratuita</button>
          <a class="wa" href="__WA__" target="_blank" rel="noopener">Oppure scrivici su WhatsApp</a>
        </form>
      </div>
    </div>
  </div>
  <p class="calc-disc">I valori sono stime indicative a scopo informativo, non un'offerta contrattuale. La rendita reale dipende da stagionalità, qualità dell'immobile, gestione e concorrenza locale.</p>
</div>
'''
    tail='<section class="related wrap"><h2>Approfondisci</h2><div class="cards">'+ "".join(card(BY[s]) for s in ["quanto-rende-affitto-breve-bologna","property-manager-affitti-brevi","affitto-breve-o-lungo-cosa-conviene"] if s in BY) +'</div></section></main>'
    body=ui.replace("__OPTS__",opts).replace("__WA__",WA_LINK)+CALC_SCRIPT+tail
    ld=[{"@context":"https://schema.org","@type":"WebApplication","name":"Calcolatore di rendita affitti brevi","applicationCategory":"FinanceApplication","operatingSystem":"Web","offers":{"@type":"Offer","price":"0","priceCurrency":"EUR"}},
        {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Blog","item":S["url"]+"/blog/"},{"@type":"ListItem","position":2,"name":"Calcolatore di rendita","item":S["url"]+"/blog/calcolatore-rendita/"}]}]
    out=os.path.join(OUT,"calcolatore-rendita","index.html"); os.makedirs(os.path.dirname(out),exist_ok=True)
    open(out,"w",encoding="utf-8").write(page("Calcolatore rendita affitti brevi | B&P Lux Property","Calcola una stima gratuita di quanto può rendere il tuo immobile come affitto breve per città, posti letto e posizione. Poi l'analisi precisa e gratuita.",S["url"]+"/blog/calcolatore-rendita/",body,ld,og_image=S["url"]+"/blog/og/_calcolatore.png"))

# ---------------- OG IMAGES ----------------
def make_og():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as e:
        print("OG: PIL non disponibile, salto:",e); return
    ogdir=os.path.join(OUT,"og"); os.makedirs(ogdir,exist_ok=True)
    def font(paths,size):
        for p in paths:
            try: return ImageFont.truetype(p,size)
            except Exception: pass
        return ImageFont.load_default()
    SER=["C:/Windows/Fonts/georgiab.ttf","C:/Windows/Fonts/timesbd.ttf","georgiab.ttf"]
    SANS=["C:/Windows/Fonts/arial.ttf","arial.ttf"]
    def wrap(d,t,fn,maxw):
        out=[];cur=""
        for w in t.split():
            s=(cur+" "+w).strip()
            if d.textlength(s,font=fn)<=maxw: cur=s
            else:
                if cur: out.append(cur)
                cur=w
        if cur: out.append(cur)
        return out[:4]
    def one(path,kicker,title):
        im=Image.new("RGB",(1200,630),(22,20,15)); d=ImageDraw.Draw(im)
        d.rectangle([36,36,1164,594],outline=(176,137,78),width=2)
        d.text((72,84),(kicker or "").upper(),font=font(SANS,26),fill=(201,162,75))
        tf=font(SER,58); y=152
        for ln in wrap(d,title,tf,1030):
            d.text((72,y),ln,font=tf,fill=(244,238,225)); y+=72
        d.text((72,514),"B&P LUX PROPERTY",font=font(SER,34),fill=(201,162,75))
        d.text((74,560),"bpluxproperty.com/blog",font=font(SANS,22),fill=(150,145,135))
        im.save(path,"PNG",optimize=True)
    for a in articles:
        one(os.path.join(ogdir,a["slug"]+".png"),CATS.get(a["category"],{}).get("name",""),a.get("h1") or a.get("title"))
    one(os.path.join(ogdir,"_default.png"),"Blog B&P Lux Property","Affitti brevi, senza giri di parole")
    one(os.path.join(ogdir,"_calcolatore.png"),"Strumento gratuito","Calcolatore di rendita affitto breve")
    print("OG: generate",len(articles)+2,"immagini")

BLOG_CSS=r''':root{--ivory:#F6F2E9;--paper:#FBF9F3;--charcoal:#16140F;--charcoal2:#211E17;--gold:#B0894E;--gold2:#C9A24B;--muted:#5f574a;--line:rgba(22,20,15,.12);--maxw:1120px;--pad:clamp(20px,4vw,34px);--serif:'Cormorant Garamond',Georgia,serif;--sans:'Jost',system-ui,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--sans);color:var(--charcoal);background:var(--ivory);line-height:1.68;font-weight:400;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 var(--pad)}
h1,h2,h3{font-family:var(--serif);font-weight:600;line-height:1.12;color:var(--charcoal)}
.kick{display:inline-block;font-family:var(--sans);font-size:12px;letter-spacing:.3em;text-transform:uppercase;color:var(--gold);font-weight:500;margin-bottom:14px}
.kick.gold{color:var(--gold2)}
.muted{color:var(--muted)}
.lead{font-size:19px;color:var(--muted);max-width:620px;margin-top:10px}
.btn{display:inline-flex;align-items:center;gap:8px;font-family:var(--sans);font-weight:500;font-size:14px;letter-spacing:.02em;padding:14px 26px;border-radius:2px;cursor:pointer;border:1px solid transparent;transition:.25s}
.btn-gold{background:var(--gold);color:#fff}.btn-gold:hover{background:var(--charcoal);transform:translateY(-2px)}
.btn-ghost{background:transparent;color:var(--charcoal);border-color:var(--charcoal)}.btn-ghost:hover{background:var(--charcoal);color:var(--ivory)}
/* header */
.top{position:sticky;top:0;z-index:50;background:rgba(246,242,233,.9);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.top-in{display:flex;align-items:center;justify-content:space-between;height:66px}
.brand .bt{font-family:var(--serif);font-weight:700;font-size:22px;letter-spacing:.02em}
.brand small{display:block;font-family:var(--sans);font-size:9px;letter-spacing:.34em;color:var(--gold);font-weight:500;margin-top:-3px;text-transform:uppercase}
.topnav{display:flex;gap:22px;align-items:center;font-size:14px;font-weight:400}
.topnav a:hover{color:var(--gold)}
/* hero */
.hero{padding:64px 0 30px}
.blog-hero,.cat-hero{max-width:var(--maxw);margin:0 auto;padding:clamp(40px,7vw,72px) var(--pad) 24px}
.hero h1{font-size:clamp(34px,5.2vw,58px);margin-bottom:8px}
.hero .lead{font-size:clamp(17px,2vw,21px)}
.hero-rule{width:120px;height:2px;background:var(--gold);margin:20px 0}
.intro-band{max-width:var(--maxw);margin:22px auto 8px;padding:0 var(--pad)}
.intro-band p{font-size:18px;color:#3c372e;line-height:1.75;max-width:760px}
/* cards */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:22px}
.card{--acc:var(--gold);display:flex;flex-direction:column;background:var(--paper);border:1px solid var(--line);border-top:3px solid var(--acc);border-radius:4px;padding:22px 22px;transition:.28s}
.cat-quanto-rende{--acc:#4d7c5a}.cat-normativa-fisco{--acc:#4a6785}.cat-piattaforme{--acc:#3f7d78}.cat-gestione{--acc:#a15c43}.cat-affitti-brevi{--acc:#7a5a86}.cat-preparare-casa{--acc:#6f6c37}.cat-dozza-emilia-romagna{--acc:#8a4a4a}
.card:hover{transform:translateY(-3px);box-shadow:0 18px 40px rgba(22,20,15,.09);border-color:rgba(176,137,78,.5)}
.card-cat{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--acc,var(--gold));font-weight:600;margin-bottom:10px}
.card-h{font-family:var(--serif);font-size:22px;font-weight:600;line-height:1.15;margin-bottom:8px}
.card-x{font-size:14.5px;color:var(--muted);flex:1}
.card-go{font-size:13px;color:var(--acc,var(--gold));font-weight:600;margin-top:14px}
/* blocchi categoria */
.hub{padding-bottom:20px}
.cat-block{max-width:var(--maxw);margin:44px auto 0;padding:0 var(--pad)}
.cat-head{display:flex;align-items:baseline;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:22px}
.cat-head h2{font-size:26px}
.cat-head a{font-size:14px;color:var(--gold);font-weight:500}
/* agenzie band */
.agenzie-band{background:var(--charcoal);color:var(--ivory);margin:64px 0 0;padding:64px 0}
.ab-in{max-width:var(--maxw)}
.agenzie-band h2{color:#fff;font-size:clamp(26px,3.4vw,38px);margin-bottom:16px;max-width:760px}
.agenzie-band p{color:#d9d3c6;font-size:17px;max-width:720px;margin-bottom:18px}
.ab-points{list-style:none;display:flex;flex-wrap:wrap;gap:10px 26px;margin-bottom:26px}
.ab-points li{position:relative;padding-left:20px;color:#efe9dc;font-size:15px}
.ab-points li::before{content:"—";position:absolute;left:0;color:var(--gold2)}
/* cta */
.cta{max-width:var(--maxw);margin:52px auto;padding:0 var(--pad)}
.cta-in{background:linear-gradient(180deg,#fff,#FBF6EC);border:1px solid var(--line);border-top:3px solid var(--gold);border-radius:6px;padding:34px 32px;display:grid;grid-template-columns:1fr 1fr;gap:26px;align-items:center;box-shadow:0 16px 44px rgba(22,20,15,.07)}
.cta .kick{font-family:var(--serif);font-size:26px;letter-spacing:0;text-transform:none;color:var(--charcoal);font-weight:600;display:block;margin-bottom:8px}
.cta-txt p{color:var(--muted);font-size:15.5px}
.cta-form{display:flex;flex-direction:column;gap:10px}
.cta-form input{padding:13px 14px;border:1px solid var(--line);border-radius:2px;font-family:var(--sans);font-size:16px;background:#fff}
.cta-form input:focus{outline:none;border-color:var(--gold)}
.cta-form .btn-gold{justify-content:center}
.cta-form .wa{font-size:13.5px;color:#1f7a44;text-align:center;font-weight:500}
.cta-form .wa:hover{text-decoration:underline}
/* articolo */
.art{max-width:760px;margin:0 auto;padding:0 22px 10px}
.crumb{font-size:13px;color:var(--muted);padding-top:22px;padding-bottom:6px}
.crumb a:hover{color:var(--gold)}
.art-hero{padding:14px 0 8px}
.art-hero h1{font-size:clamp(30px,4.6vw,46px);margin:6px 0 10px}
.art-hero .meta{font-size:13px;color:var(--muted);letter-spacing:.02em}
.art-hero.has-img{border-radius:6px;padding:46px 30px;color:#fff;margin-bottom:10px}
.art-hero.has-img h1{color:#fff}.art-hero.has-img .meta{color:#e7e1d5}.art-hero.has-img .kick{color:var(--gold2)}
.body{font-size:17px;color:#26221b}
.body p a,.body li a{color:var(--gold);text-decoration:underline;text-underline-offset:2px;text-decoration-thickness:1px;font-weight:500}
.body p a:hover,.body li a:hover{color:var(--charcoal)}
.body strong{font-weight:600;color:var(--charcoal)}
.body .opening{font-size:20px;line-height:1.6;color:#3c372e;border-left:3px solid var(--gold);padding-left:18px;margin:18px 0 8px}
.body section{margin:30px 0}
.body h2{font-size:27px;margin-bottom:12px}
.body section[id]>h2::before{content:"";display:block;width:40px;height:3px;background:var(--acc,var(--gold));border-radius:2px;margin-bottom:14px}
.body p{margin:12px 0}
.body ul{margin:12px 0 12px 4px;list-style:none}
.body li{position:relative;padding:5px 0 5px 22px}
.body li::before{content:"";position:absolute;left:0;top:13px;width:7px;height:7px;background:var(--gold);border-radius:50%}
.tbl{overflow-x:auto;margin:16px 0}
.body table{width:100%;border-collapse:collapse;font-size:15px}
.body th,.body td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--line)}
.body th{background:var(--charcoal);color:var(--ivory);font-family:var(--sans);font-weight:500;font-size:13px;letter-spacing:.04em}
.body tbody tr:nth-child(even){background:var(--paper)}
.toc{background:var(--paper);border:1px solid var(--line);border-radius:4px;padding:18px 22px;margin:20px 0}
.toc span{font-family:var(--sans);font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);font-weight:500}
.toc ol{margin:10px 0 0 18px;font-size:15px}
.toc a{color:#3c372e}.toc a:hover{color:var(--gold)}
.disclaimer{font-size:14px;color:#4a4234;background:var(--paper);border-left:3px solid var(--gold);padding:14px 18px;margin-top:22px;border-radius:0 4px 4px 0}
.disclaimer::before{content:"NOTA";display:block;font-family:var(--sans);font-size:11px;letter-spacing:.18em;color:var(--gold);font-weight:600;margin-bottom:4px}
.tldr{background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--acc,var(--gold));border-radius:0 6px 6px 0;padding:16px 20px;margin:22px 0}
.tldr-k{display:block;font-family:var(--sans);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--acc,var(--gold));font-weight:600;margin-bottom:6px}
.tldr p{margin:0;color:#3c372e;font-size:16px;font-weight:400}
.pull{margin:34px 0;padding:4px 0 4px 24px;border-left:4px solid var(--acc,var(--gold))}
.pull p{font-family:var(--serif);font-size:clamp(21px,2.8vw,29px);line-height:1.32;color:var(--charcoal);font-weight:600;margin:0}
.sources{margin-top:26px;font-size:14px}.sources h2{font-size:20px}.sources ul{margin-top:8px;color:var(--muted)}.sources li{margin:6px 0}
.sources a{color:var(--gold);text-decoration:underline}
.faqs{max-width:760px;margin:36px auto 0;padding:0 22px}
.faqs h2{font-size:26px;margin-bottom:14px}
.faqs details{border:1px solid var(--line);border-radius:4px;margin-bottom:10px;padding:2px 18px;background:var(--paper)}
.faqs details[open]{border-color:var(--gold)}
.faqs summary{cursor:pointer;font-weight:500;font-family:var(--sans);padding:15px 0;list-style:none;display:flex;justify-content:space-between;gap:14px}
.faqs summary::-webkit-details-marker{display:none}
.faqs summary::after{content:"+";color:var(--gold);font-size:22px;line-height:1}
.faqs details[open] summary::after{content:"\2212"}
.faqs details p{padding:0 0 16px;color:var(--muted)}
.related{max-width:var(--maxw);margin:20px auto 0;padding:0 var(--pad)}
.related h2{font-size:24px;margin-bottom:18px}
.foot{background:var(--charcoal);color:#b9b2a4;margin-top:60px;padding:40px 0;font-size:14px}
.foot-in{display:flex;flex-wrap:wrap;gap:26px;justify-content:space-between}
.foot strong{color:#fff;font-family:var(--serif);font-size:18px;font-weight:600}
.foot-links{display:flex;flex-direction:column;gap:6px}
.foot-links a:hover,.foot a:hover{color:var(--gold2)}
/* ===== premium: hero foto, 2 colonne, sidebar, share, autore, fab ===== */
.art-wrap .crumb{padding-top:20px;padding-bottom:0}
.art-hero-img{background-size:cover;background-position:center;color:#fff;margin-top:14px;min-height:clamp(280px,42vw,380px);display:flex;align-items:flex-end;padding:0 0 clamp(24px,4vw,36px)}
.ahi-in{width:100%}
.art-hero-img .kick{color:var(--gold2)}
.art-hero-img h1{color:#fff;font-size:clamp(30px,4.4vw,48px);max-width:900px;margin-bottom:10px}
.art-hero-img .meta{font-size:13px;color:#e7e1d5;letter-spacing:.02em}
.art-grid{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:48px;align-items:start;margin-top:40px}
.art-grid .body{max-width:none;margin:0}
.body .faqs{max-width:none;padding:0;margin:38px 0 0}
.body .faqs h2{font-size:26px;margin-bottom:14px}
.side{position:sticky;top:84px;display:flex;flex-direction:column;gap:18px}
.side-card{background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:20px}
.side-val{background:linear-gradient(180deg,#fff,#FBF6EC);border-top:3px solid var(--gold)}
.side-val .sv-k{display:block;font-family:var(--serif);font-size:21px;font-weight:600;color:var(--charcoal);margin-bottom:6px}
.side-val p{font-size:14px;color:var(--muted);margin-bottom:14px}
.side-val .btn{width:100%;justify-content:center}
.side-wa{text-align:center}
.side-wa .sw-t{display:block;font-weight:500;margin-bottom:12px}
.btn-wa{background:#1f7a44;color:#fff;justify-content:center}.btn-wa:hover{background:#17603a;transform:translateY(-2px)}
.side-wa .btn-wa{width:100%}
.side-wa img{margin:14px auto 6px;display:block;border:1px solid var(--line);border-radius:6px;background:#fff;padding:6px}
.side-wa .sw-q{font-size:12px;color:var(--muted)}
.sl-k{display:block;font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);font-weight:500;margin-bottom:12px}
.side-list ul{list-style:none}
.side-list li{border-bottom:1px solid var(--line);padding:9px 0}
.side-list li:last-child{border-bottom:0}
.side-list a{font-family:var(--serif);font-size:16px;line-height:1.25;color:var(--charcoal)}
.side-list a:hover{color:var(--gold)}
.sc-tags{display:flex;flex-wrap:wrap;gap:8px}
.sc-tags a{font-size:12px;border:1px solid var(--line);border-radius:20px;padding:6px 12px;color:var(--charcoal)}
.sc-tags a:hover{border-color:var(--gold);color:var(--gold)}
.side-dozza{display:block;background:var(--charcoal);color:var(--ivory);border-color:var(--charcoal);transition:.25s}
.side-dozza .sd-k{display:block;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold2);margin-bottom:8px}
.side-dozza strong{display:block;font-family:var(--serif);font-size:20px;font-weight:600;color:#fff;margin-bottom:6px}
.side-dozza .sd-r{display:block;color:var(--gold2);font-size:14px;margin-bottom:12px}
.side-dozza .sd-go{font-size:13px;color:var(--ivory)}
.side-dozza:hover{transform:translateY(-2px);box-shadow:0 16px 40px rgba(22,20,15,.18)}
.cta-inline{display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap;background:linear-gradient(180deg,#fff,#FBF6EC);border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:6px;padding:18px 22px;margin:28px 0}
.cta-inline strong{display:block;font-family:var(--serif);font-size:20px;color:var(--charcoal)}
.cta-inline span{font-size:14px;color:var(--muted)}
.ci-btns{display:flex;gap:10px;flex-wrap:wrap}
.ci-btns .btn{padding:11px 18px}
.share{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:30px 0 6px;font-size:13px;color:var(--muted)}
.share a{color:var(--gold);font-weight:500;border-bottom:1px solid rgba(176,137,78,.4)}
.share a:hover{color:var(--charcoal)}
.au-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:22px;margin:8px 0 18px}
.au-card{display:flex;gap:18px;background:var(--paper);border:1px solid var(--line);border-top:3px solid var(--gold);border-radius:6px;padding:22px}
.au-card img{width:120px;height:120px;border-radius:50%;object-fit:cover;flex:0 0 120px}
.au-card h2{margin:0;font-size:22px}
.au-role{display:block;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--gold);margin:2px 0 8px}
.au-k{display:block;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-top:10px}
.au-comp{margin:4px 0 0;padding-left:18px;font-size:14px;color:var(--muted)}
@media(max-width:520px){.au-card{flex-direction:column}.au-card img{width:96px;height:96px;flex:0 0 96px}}
.ab-img{width:72px;height:72px;border-radius:50%;object-fit:cover;flex:0 0 72px;border:2px solid var(--gold)}
.ab-comp{font-size:13px;color:var(--muted);margin-top:8px}
.ab-comp a{color:var(--gold);text-decoration:underline}
.meta a.by{color:inherit;text-decoration:underline;text-decoration-color:var(--gold)}
.authorbox{display:flex;gap:16px;align-items:flex-start;background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:20px;margin:22px 0}
.ab-badge{flex:none;width:52px;height:52px;border-radius:50%;background:var(--charcoal);color:var(--gold);display:flex;align-items:center;justify-content:center;font-family:var(--serif);font-weight:700;font-size:18px;border:2px solid var(--gold)}
.ab-txt strong{font-family:var(--serif);font-size:19px;color:var(--charcoal)}
.ab-txt span{display:block;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin:2px 0 8px}
.ab-txt p{font-size:14px;color:var(--muted);margin:0}
.fab-wa{position:fixed;right:20px;bottom:20px;z-index:90;width:56px;height:56px;border-radius:50%;background:#1f7a44;color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 12px 30px rgba(0,0,0,.28);transition:.2s}
.fab-wa:hover{transform:scale(1.08)}
/* trust strip */
.trust{background:var(--charcoal);color:var(--ivory)}
.trust-in{display:flex;flex-wrap:wrap;justify-content:center;gap:22px 54px;padding:22px}
.trust .tr{text-align:center}
.trust .tr strong{display:block;font-family:var(--serif);font-size:26px;color:var(--gold2);line-height:1}
.trust .tr span{font-size:12.5px;color:#c9c2b4}
/* calc highlight in hub */
.calc-hl{max-width:var(--maxw);margin:44px auto 0;padding:0 var(--pad)}
.calc-hl-in{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;background:linear-gradient(135deg,var(--charcoal),var(--charcoal2));color:var(--ivory);border-radius:8px;padding:30px 34px}
.calc-hl-in .kick{color:var(--gold2)}
.calc-hl-in h2{color:#fff;font-size:26px;margin-bottom:6px}
.calc-hl-in p{color:#d9d3c6;font-size:15px;max-width:560px;margin:0}
.nav-calc{color:var(--gold);font-weight:500}
.nav-calc:hover{color:var(--charcoal)}
.nav-guida{color:var(--gold);font-weight:600}
.nav-guida:hover{color:var(--charcoal)}
/* separazioni hub: divisori tra le sezioni */
.hub .cat-block{margin-top:54px;padding-top:40px;border-top:1px solid var(--line)}
/* banda guida in hub */
.guida .guide-phase.wrap{padding-left:var(--pad);padding-right:var(--pad)}
.plat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr));gap:16px;margin:8px 0 18px}
.plat{background:var(--paper);border:1px solid var(--line);border-top:3px solid var(--gold);border-radius:6px;padding:18px 20px;display:flex;flex-direction:column;gap:4px}
.plat-k{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.plat-v{font-family:'Cormorant Garamond',Georgia,serif;font-size:40px;line-height:1;color:var(--charcoal)}
.plat-v small{font-size:17px;color:var(--muted)}
.plat-n{font-size:14px;color:var(--muted)}
.rv-badges{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.rv-badge{font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;border:1px solid var(--gold);color:var(--gold);border-radius:20px;padding:3px 10px}
.score-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,120px),1fr));gap:10px;margin:0 0 14px}
.score{background:#fff;border:1px solid var(--line);border-radius:6px;padding:12px 10px;text-align:center}
.score-n{display:block;font-family:'Cormorant Garamond',Georgia,serif;font-size:28px;font-weight:600;color:var(--charcoal)}
.score-l{display:block;font-size:12.5px;color:var(--muted);margin-top:2px}
.rv-note{font-size:13.5px;color:var(--muted)}
.rv-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,290px),1fr));gap:18px;margin:8px 0 6px}
.rv-card{margin:0;background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:0 6px 6px 0;padding:20px 22px;display:flex;flex-direction:column;gap:12px}
.rv-card blockquote{margin:0}
.rv-card blockquote p{font-family:'Cormorant Garamond',Georgia,serif;font-size:19px;line-height:1.5;color:var(--charcoal);margin:0}
.rv-card figcaption{display:flex;flex-direction:column;gap:2px;font-size:13px}
.rv-card figcaption strong{color:var(--charcoal);font-weight:500}
.rv-card figcaption span{color:var(--muted)}
.guida-band{max-width:var(--maxw);margin:36px auto 0;padding:0 var(--pad)}
.gb-in{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;background:linear-gradient(135deg,#2a2015,var(--charcoal));color:var(--ivory);border:1px solid rgba(201,162,75,.35);border-radius:8px;padding:28px 32px}
.gb-in .kick{color:var(--gold2)}
.gb-in h2{color:#fff;font-size:clamp(22px,2.6vw,27px);margin:4px 0}
.gb-in p{color:#d9d3c6;font-size:15px;max-width:640px;margin:0}
/* pagina Guida del proprietario */
.guida-hero{background:linear-gradient(135deg,var(--charcoal),var(--charcoal2));color:var(--ivory);margin-top:8px}
.guida-hero .wrap{padding:clamp(44px,6vw,66px) var(--pad) clamp(38px,5vw,54px)}
.guida-hero .kick{color:var(--gold2)}
.guida-hero h1{color:#fff;font-size:clamp(30px,4.6vw,50px);max-width:18ch;margin-bottom:12px}
.guida-hero .lead{color:#d9d3c6;max-width:660px}
.gh-btns{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}
.btn-ghost-d{background:transparent;color:var(--ivory);border-color:rgba(255,255,255,.55)}
.btn-ghost-d:hover{background:#fff;color:var(--charcoal)}
.guida .guide-phase{padding:46px 0 6px;border-top:1px solid var(--line)}
.guida .guide-phase:first-of-type{border-top:0;padding-top:38px}
.gp-head{display:flex;align-items:flex-start;gap:18px;max-width:var(--maxw);margin:0 auto 22px;padding:0 var(--pad)}
.gp-num{flex:none;width:44px;height:44px;border-radius:50%;background:var(--gold);color:#fff;font-family:var(--serif);font-weight:700;font-size:22px;display:flex;align-items:center;justify-content:center}
.gp-head h2{font-size:26px;margin:0}
.gp-head p{color:var(--muted);font-size:15px;margin-top:3px}
.guida .guide-phase .cards{max-width:var(--maxw);margin:0 auto;padding:0 var(--pad)}
/* newsletter */
.foot-news{background:var(--charcoal2);color:var(--ivory);border-top:1px solid rgba(255,255,255,.08)}
.foot-news-in{display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;padding:26px 22px}
.foot-news .fn-k{font-family:var(--serif);font-size:22px;color:#fff}
.foot-news p{color:#c9c2b4;font-size:14px;margin-top:2px}
.news-form{display:flex;gap:8px;flex-wrap:wrap}
.news-form input{padding:12px 14px;border:1px solid var(--line);border-radius:2px;font-family:var(--sans);font-size:16px;min-width:220px;background:#fff;color:var(--charcoal)}
.side-news .news-form{flex-direction:column}
.side-news .news-form input{min-width:0;width:100%}
.side-news .news-form .btn{width:100%;justify-content:center}
.side-news p{font-size:14px;color:var(--muted);margin-bottom:12px}
/* side calc card */
.side-calc{display:block;background:linear-gradient(135deg,var(--gold),#8a6a29);color:#fff;border-color:transparent;transition:.25s}
.side-calc .sd-k{display:block;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#3a2c0f;margin-bottom:6px}
.side-calc strong{display:block;font-family:var(--serif);font-size:21px;color:#fff;margin-bottom:6px}
.side-calc .sc-go{font-size:13px;color:#3a2c0f}
.side-calc:hover{transform:translateY(-2px);box-shadow:0 16px 40px rgba(176,137,78,.35)}
/* calcolatore page */
.calc{max-width:820px;margin:36px auto 0}
.calc-card{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:28px;box-shadow:0 16px 44px rgba(22,20,15,.07)}
.calc-form{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.calc-form label{display:flex;flex-direction:column;gap:6px;font-size:13px;font-weight:500;color:var(--charcoal)}
.calc-form select{padding:12px;border:1px solid var(--line);border-radius:3px;font-family:var(--sans);font-size:16px;background:#fff}
.calc-form .btn-gold{grid-column:1/-1;justify-content:center}
.calc-out{margin-top:24px;border-top:1px solid var(--line);padding-top:22px}
.co-k{font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);font-weight:500}
.co-range{font-family:var(--serif);font-size:clamp(30px,5vw,44px);color:var(--charcoal);margin:6px 0}
.co-range small{font-family:var(--sans);font-size:15px;color:var(--muted)}
.co-sub{font-size:14px;color:var(--muted)}
.co-note{font-size:13px;color:var(--muted);background:var(--ivory);border-left:3px solid var(--gold);padding:10px 14px;margin:16px 0}
.co-lead{background:#fff;border:1px solid var(--line);border-radius:6px;padding:20px;margin-top:8px}
.co-lead strong{font-family:var(--serif);font-size:20px}
.co-lead p{font-size:14px;color:var(--muted);margin:6px 0 12px}
.co-lead .cta-form{display:flex;flex-direction:column;gap:10px}
.co-lead .cta-form input{padding:12px 14px;border:1px solid var(--line);border-radius:2px;font-family:var(--sans);font-size:16px}
.co-lead .wa{font-size:13.5px;color:#1f7a44;text-align:center}
.calc-disc{font-size:12px;color:var(--muted);text-align:center;margin-top:14px}
@media(max-width:560px){.calc-form{grid-template-columns:1fr}}
@media(max-width:900px){
  .art-grid{grid-template-columns:1fr;gap:30px}
  .side{position:static}
}
@media(max-width:820px){
  .topnav a:not(.btn){display:none}
  .topnav{gap:12px}
  .top-in .btn{padding:8px 15px;font-size:13px;letter-spacing:0}
  .cta-in{grid-template-columns:1fr;gap:18px}
  .agenzie-band{padding:48px 0}
  .cta-inline{flex-direction:column;align-items:flex-start}
}
@media(max-width:600px){
  input,select,textarea{font-size:16px}
  .cta-in{padding:24px 22px}
  .calc-hl-in{padding:24px}
  .calc-card{padding:22px}
  .co-lead{padding:16px}
  .authorbox{padding:18px}
  .body .opening{font-size:18px;padding-left:14px}
  .cards{gap:16px}
  .cat-head h2{font-size:22px}
  .foot-news-in,.calc-hl-in{gap:16px}
}'''

BLOG_JS='''(function(){
  var WA="%WA%", HOOK="%HOOK%";
  window.bpLead=function(e){
    e.preventDefault();
    var f=e.target, d={};
    Array.prototype.forEach.call(f.elements,function(el){if(el.name)d[el.name]=el.value;});
    d.fonte="blog "+location.pathname;
    var done=function(){f.innerHTML='<p style="font-family:Cormorant Garamond,serif;font-size:22px;color:#16140F">Grazie! Ti ricontattiamo a breve.</p>';};
    if(HOOK){
      var ok=false; try{ ok=navigator.sendBeacon(HOOK,new Blob([JSON.stringify(d)],{type:"application/json"})); }catch(e){}
      if(ok){done();} else { waFallback(d); }
    } else { waFallback(d); }
    return false;
  };
  function waFallback(d){
    var t="Ciao B&P! Richiesta dal blog.%0A"+
      "Nome: "+enc(d.nome)+"%0AEmail: "+enc(d.email||"-")+"%0ATelefono: "+enc(d.telefono||"-")+"%0ACittà: "+enc(d.citta||"-")+"%0APagina: "+enc(location.pathname);
    window.open("https://wa.me/"+WA+"?text="+t,"_blank");
  }
  function enc(s){return encodeURIComponent(s||"");}
  window.bpNews=function(e){
    e.preventDefault(); var f=e.target, em=(f.email&&f.email.value)||"";
    var d={email:em,fonte:"newsletter "+location.pathname};
    var ok=false; try{ if(HOOK) ok=navigator.sendBeacon(HOOK,new Blob([JSON.stringify(d)],{type:"application/json"})); }catch(_){}
    if(!ok && !HOOK){ window.open("https://wa.me/"+WA+"?text="+enc("Ciao B&P, iscrivimi alla newsletter: "+em),"_blank"); }
    f.innerHTML='<p style="color:#1f7a44;font-weight:500;margin:0">Iscrizione ricevuta, grazie!</p>';
    return false;
  };
})();'''

def write_assets():
    os.makedirs(OUT,exist_ok=True)
    open(os.path.join(OUT,"blog.css"),"w",encoding="utf-8").write(BLOG_CSS)
    js=BLOG_JS.replace("%WA%",WA).replace("%HOOK%",S.get("ghlWebhook",""))
    open(os.path.join(OUT,"blog.js"),"w",encoding="utf-8").write(js)

def main():
    os.makedirs(OUT,exist_ok=True)
    write_assets()
    make_og()
    for a in articles: render_article(a)
    for cid in CAT_ORDER: render_category(cid)
    render_hub(); render_calculator(); render_guida(); render_recensioni(); render_reputazione(); render_autori(); sitemap()
    print(f"Generati: {len(articles)} articoli + {len(CAT_ORDER)} categorie + hub + guida + 2 pagine recensioni + autori + sitemap")
    if warn:
        print("\n== AVVISI cancello contenuto (%d) =="%len(warn))
        for w in warn: print("  -",w)
    else:
        print("Cancello contenuto: OK, nessun avviso")

if __name__=="__main__": main()
