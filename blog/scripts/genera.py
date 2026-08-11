# -*- coding: utf-8 -*-
"""Generatore blog statico B&P Lux Property.
Legge blog/contenuti/*.json e scrive HTML completo in public/blog/.
Contenuto nell'HTML (niente JS per il testo) come da manuale SEO.
"""
import os, json, re, html, datetime, sys

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

def paras(lst): return "".join(f"<p>{inline(p)}</p>" for p in (lst or []))
def ul(lst):
    if not lst: return ""
    return "<ul>"+"".join(f"<li>{inline(x)}</li>" for x in lst)+"</ul>"
def table(tb):
    if not tb: return ""
    h="".join(f"<th>{inline(x)}</th>" for x in tb.get("headers",[]))
    rows="".join("<tr>"+"".join(f"<td>{inline(c)}</td>" for c in r)+"</tr>" for r in tb.get("rows",[]))
    return f'<div class="tbl"><table><thead><tr>{h}</tr></thead><tbody>{rows}</tbody></table></div>'

# ---------------- COMPONENTI ----------------
def cta_block():
    return f'''<section class="cta" aria-label="Contattaci">
  <div class="cta-in">
    <div class="cta-txt">
      <span class="kick">{esc(ent["cta"]["titolo"])}</span>
      <p>{esc(ent["cta"]["testo"])}</p>
    </div>
    <form class="cta-form" onsubmit="return bpLead(event)">
      <input name="nome" required placeholder="Nome e cognome" aria-label="Nome e cognome">
      <input name="email" type="email" required placeholder="Email" aria-label="Email">
      <input name="telefono" placeholder="Telefono / WhatsApp" aria-label="Telefono o WhatsApp">
      <input name="citta" placeholder="Citta dell'immobile" aria-label="Citta dell'immobile">
      <button type="submit" class="btn btn-gold">{esc(ent["cta"]["bottone"])}</button>
      <a class="wa" href="https://wa.me/{WA}?text={esc(WA_PREFILL).replace(' ','%20')}" target="_blank" rel="noopener">&#128241; {esc(ent["cta"]["whatsappTesto"])} ({esc(S["whatsappDisplay"])})</a>
    </form>
  </div>
</section>'''

def header():
    links="".join(f'<a href="/blog/categoria/{c}/">{esc(CATS[c]["name"])}</a>' for c in CAT_ORDER[:5])
    return f'''<header class="top"><div class="wrap top-in">
  <a class="brand" href="/blog/"><span class="bt">B&amp;P<small>Lux Property</small></span></a>
  <nav class="topnav">{links}<a class="btn btn-ghost" href="/">Sito &rarr;</a></nav>
</div></header>'''

def footer():
    cols="".join(f'<a href="/blog/categoria/{c}/">{esc(CATS[c]["name"])}</a>' for c in CAT_ORDER)
    return f'''<footer class="foot"><div class="wrap foot-in">
  <div><strong>B&amp;P Lux Property</strong><br><span class="muted">{esc(S["tagline"])}</span></div>
  <div class="foot-links">{cols}</div>
  <div class="muted">{esc(S["email"])} &middot; <a href="https://wa.me/{WA}" target="_blank" rel="noopener">WhatsApp {esc(S["whatsappDisplay"])}</a><br><a href="/privacy.html">Privacy</a> &middot; <a href="/termini.html">Termini</a></div>
</div></footer>'''

def page(title, desc, canonical, body, jsonld, extra_head=""):
    ld="".join(f'<script type="application/ld+json">{json.dumps(x,ensure_ascii=False)}</script>' for x in jsonld)
    return f'''<!doctype html><html lang="it"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:site_name" content="B&P Lux Property">
<meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/blog/blog.css">{extra_head}
{ld}
</head><body>
{header()}
{body}
{footer()}
<script src="/blog/blog.js" defer></script>
</body></html>'''

def art_url(slug): return f'{S["url"]}/blog/{slug}'
def card(a):
    c=CATS.get(a["category"],{})
    return f'''<a class="card" href="/blog/{a["slug"]}/">
  <span class="card-cat">{esc(c.get("name",""))}</span>
  <span class="card-h">{esc(a.get("h1") or a.get("title"))}</span>
  <span class="card-x">{esc(a.get("excerpt",""))}</span>
  <span class="card-go">Leggi &rarr;</span></a>'''

# ---------------- ARTICOLO ----------------
def render_article(a):
    c=CATS.get(a["category"],{})
    secs_html=""; toc=[]
    for i,sec in enumerate(a.get("sections",[])):
        sid=f"s{i+1}"; toc.append((sid,sec["h2"]))
        secs_html+=f'<section id="{sid}"><h2>{esc(sec["h2"])}</h2>{paras(sec.get("paragraphs"))}{ul(sec.get("list"))}{table(sec.get("table"))}</section>'
        if i==2: secs_html+=cta_block()   # CTA a meta
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
    heroimg=a.get("heroImage")
    hero_style=f' style="background-image:linear-gradient(180deg,rgba(22,20,15,.35),rgba(22,20,15,.78)),url({heroimg});background-size:cover;background-position:center"' if heroimg else ""
    hero_cls="hero art-hero"+(" has-img" if heroimg else "")
    body=f'''<main class="art">
<nav class="crumb"><a href="/blog/">Blog</a> / <a href="/blog/categoria/{a["category"]}/">{esc(c.get("name",""))}</a> / <span>{esc(a.get("h1") or a.get("title"))}</span></nav>
<div class="{hero_cls}"{hero_style}>
  <span class="kick">{esc(a.get("heroKicker") or c.get("name",""))}</span>
  <h1>{esc(a.get("h1") or a.get("title"))}</h1>
  <div class="meta">A cura di {esc(ent["author"]["name"])} &middot; agg. {esc(a.get("updatedAt",""))}</div>
</div>
<article class="body">
<p class="opening">{inline(a.get("opening",""))}</p>
{toc_html}
{secs_html}
{disc}
{src_html}
</article>
<section class="faqs"><h2>Domande frequenti</h2>{faq_html}</section>
{cta_block()}
<section class="related"><h2>Continua a leggere</h2><div class="cards">{rel_html}</div></section>
</main>'''
    # schema
    ld=[
      {"@context":"https://schema.org","@type":"BlogPosting","headline":a.get("h1") or a.get("title"),
       "description":a.get("metaDescription",""),"datePublished":a.get("publishedAt"),"dateModified":a.get("updatedAt"),
       "author":{"@type":"Organization","name":ent["author"]["name"]},
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
    open(out,"w",encoding="utf-8").write(page(title,a.get("metaDescription",""),art_url(a["slug"]),body,ld))

# ---------------- CATEGORIA ----------------
def render_category(cid):
    c=CATS[cid]; arts=[a for a in articles if a["category"]==cid]
    cards="".join(card(a) for a in arts) or '<p class="muted">Presto nuovi articoli in questa sezione.</p>'
    body=f'''<main class="hub">
<nav class="crumb"><a href="/blog/">Blog</a> / <span>{esc(c["name"])}</span></nav>
<div class="hero cat-hero"><span class="kick">Categoria</span><h1>{esc(c["h1"])}</h1><p class="lead">{esc(c["intro"])}</p></div>
<div class="cards">{cards}</div>
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
<section class="intro-band"><p>{esc(ent["blogHubIntro"])}</p></section>
<section class="cat-block"><div class="cat-head"><h2>In evidenza</h2></div><div class="cards">{feat_html}</div></section>
{cat_secs}
{agenzie}
{cta_block()}
</main>'''
    ld=[{"@context":"https://schema.org","@type":"Blog","name":"Blog B&P Lux Property","url":f'{S["url"]}/blog/',"description":ent["blogHubIntro"][:200]},
        {"@context":"https://schema.org","@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"url":art_url(a["slug"])} for i,a in enumerate(articles)]}]
    open(os.path.join(OUT,"index.html"),"w",encoding="utf-8").write(
        page("Blog affitti brevi | B&P Lux Property","Guide pratiche sugli affitti brevi: quanto rende, regole e fisco, Airbnb e Booking, gestione. Da un property manager Superhost.",f'{S["url"]}/blog/',body,ld))

# ---------------- SITEMAP ----------------
def sitemap():
    urls=[f'{S["url"]}/blog/']+[f'{S["url"]}/blog/categoria/{c}/' for c in CAT_ORDER if any(a["category"]==c for a in articles)]+[art_url(a["slug"])+"/" for a in articles]
    now=datetime.date(2026,8,11).isoformat()
    body='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for a in articles:
        body+=f'<url><loc>{art_url(a["slug"])}/</loc><lastmod>{a.get("updatedAt",now)}</lastmod></url>\n'
    for u in [f'{S["url"]}/blog/']+[f'{S["url"]}/blog/categoria/{c}/' for c in CAT_ORDER if any(a["category"]==c for a in articles)]:
        body+=f'<url><loc>{u}</loc><lastmod>{now}</lastmod></url>\n'
    body+='</urlset>\n'
    open(os.path.join(OUT,"sitemap.xml"),"w",encoding="utf-8").write(body)

BLOG_CSS=r''':root{--ivory:#F6F2E9;--paper:#FBF9F3;--charcoal:#16140F;--charcoal2:#211E17;--gold:#B0894E;--gold2:#C9A24B;--muted:#7d7466;--line:rgba(22,20,15,.12);--serif:'Cormorant Garamond',Georgia,serif;--sans:'Jost',system-ui,sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--sans);color:var(--charcoal);background:var(--ivory);line-height:1.65;font-weight:300;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.wrap{max-width:1120px;margin:0 auto;padding:0 22px}
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
.blog-hero,.cat-hero{max-width:1120px;margin:0 auto;padding:70px 22px 26px}
.hero h1{font-size:clamp(34px,5.2vw,58px);margin-bottom:8px}
.hero .lead{font-size:clamp(17px,2vw,21px)}
.hero-rule{width:120px;height:2px;background:var(--gold);margin:20px 0}
.intro-band{max-width:820px;margin:14px auto 8px;padding:0 22px}
.intro-band p{font-size:18px;color:#3c372e;line-height:1.75}
/* cards */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:22px}
.card{display:flex;flex-direction:column;background:var(--paper);border:1px solid var(--line);border-radius:4px;padding:24px 22px;transition:.28s}
.card:hover{transform:translateY(-3px);box-shadow:0 18px 40px rgba(22,20,15,.09);border-color:rgba(176,137,78,.5)}
.card-cat{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--gold);font-weight:500;margin-bottom:10px}
.card-h{font-family:var(--serif);font-size:22px;font-weight:600;line-height:1.15;margin-bottom:8px}
.card-x{font-size:14.5px;color:var(--muted);flex:1}
.card-go{font-size:13px;color:var(--gold);font-weight:500;margin-top:14px}
/* blocchi categoria */
.hub{padding-bottom:20px}
.cat-block{max-width:1120px;margin:44px auto 0;padding:0 22px}
.cat-head{display:flex;align-items:baseline;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:22px}
.cat-head h2{font-size:26px}
.cat-head a{font-size:14px;color:var(--gold);font-weight:500}
/* agenzie band */
.agenzie-band{background:var(--charcoal);color:var(--ivory);margin:64px 0 0;padding:64px 0}
.ab-in{max-width:900px}
.agenzie-band h2{color:#fff;font-size:clamp(26px,3.4vw,38px);margin-bottom:16px;max-width:760px}
.agenzie-band p{color:#d9d3c6;font-size:17px;max-width:720px;margin-bottom:18px}
.ab-points{list-style:none;display:flex;flex-wrap:wrap;gap:10px 26px;margin-bottom:26px}
.ab-points li{position:relative;padding-left:20px;color:#efe9dc;font-size:15px}
.ab-points li::before{content:"—";position:absolute;left:0;color:var(--gold2)}
/* cta */
.cta{max-width:1000px;margin:56px auto;padding:0 22px}
.cta-in{background:linear-gradient(180deg,#fff,#FBF6EC);border:1px solid var(--line);border-top:3px solid var(--gold);border-radius:6px;padding:34px 32px;display:grid;grid-template-columns:1fr 1fr;gap:26px;align-items:center;box-shadow:0 16px 44px rgba(22,20,15,.07)}
.cta .kick{font-family:var(--serif);font-size:26px;letter-spacing:0;text-transform:none;color:var(--charcoal);font-weight:600;display:block;margin-bottom:8px}
.cta-txt p{color:var(--muted);font-size:15.5px}
.cta-form{display:flex;flex-direction:column;gap:10px}
.cta-form input{padding:13px 14px;border:1px solid var(--line);border-radius:2px;font-family:var(--sans);font-size:15px;background:#fff}
.cta-form input:focus{outline:none;border-color:var(--gold)}
.cta-form .btn-gold{justify-content:center}
.cta-form .wa{font-size:13.5px;color:#1f7a44;text-align:center;font-weight:500}
.cta-form .wa:hover{text-decoration:underline}
/* articolo */
.art{max-width:760px;margin:0 auto;padding:0 22px 10px}
.crumb{font-size:13px;color:var(--muted);padding:22px 0 6px}
.crumb a:hover{color:var(--gold)}
.art-hero{padding:14px 0 8px}
.art-hero h1{font-size:clamp(30px,4.6vw,46px);margin:6px 0 10px}
.art-hero .meta{font-size:13px;color:var(--muted);letter-spacing:.02em}
.art-hero.has-img{border-radius:6px;padding:46px 30px;color:#fff;margin-bottom:10px}
.art-hero.has-img h1{color:#fff}.art-hero.has-img .meta{color:#e7e1d5}.art-hero.has-img .kick{color:var(--gold2)}
.body{font-size:17px;color:#2b271f}
.body .opening{font-size:20px;line-height:1.6;color:#3c372e;border-left:3px solid var(--gold);padding-left:18px;margin:18px 0 8px}
.body section{margin:30px 0}
.body h2{font-size:27px;margin-bottom:12px}
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
.disclaimer{font-size:13.5px;color:var(--muted);font-style:italic;background:var(--paper);border-left:3px solid var(--gold);padding:12px 16px;margin-top:22px}
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
.related{max-width:1120px;margin:20px auto 0;padding:0 22px}
.related h2{font-size:24px;margin-bottom:18px}
.foot{background:var(--charcoal);color:#b9b2a4;margin-top:60px;padding:40px 0;font-size:14px}
.foot-in{display:flex;flex-wrap:wrap;gap:26px;justify-content:space-between}
.foot strong{color:#fff;font-family:var(--serif);font-size:18px;font-weight:600}
.foot-links{display:flex;flex-direction:column;gap:6px}
.foot-links a:hover,.foot a:hover{color:var(--gold2)}
@media(max-width:820px){
  .topnav a:not(.btn){display:none}
  .cta-in{grid-template-columns:1fr;gap:18px}
  .cards{grid-template-columns:1fr}
  .agenzie-band{padding:48px 0}
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
      "Nome: "+enc(d.nome)+"%0AEmail: "+enc(d.email||"-")+"%0ATelefono: "+enc(d.telefono||"-")+"%0ACitta: "+enc(d.citta||"-")+"%0APagina: "+enc(location.pathname);
    window.open("https://wa.me/"+WA+"?text="+t,"_blank");
  }
  function enc(s){return encodeURIComponent(s||"");}
})();'''

def write_assets():
    os.makedirs(OUT,exist_ok=True)
    open(os.path.join(OUT,"blog.css"),"w",encoding="utf-8").write(BLOG_CSS)
    js=BLOG_JS.replace("%WA%",WA).replace("%HOOK%",S.get("ghlWebhook",""))
    open(os.path.join(OUT,"blog.js"),"w",encoding="utf-8").write(js)

def main():
    os.makedirs(OUT,exist_ok=True)
    write_assets()
    for a in articles: render_article(a)
    for cid in CAT_ORDER: render_category(cid)
    render_hub(); sitemap()
    print(f"Generati: {len(articles)} articoli + {len(CAT_ORDER)} categorie + hub + sitemap")
    if warn:
        print("\n== AVVISI cancello contenuto (%d) =="%len(warn))
        for w in warn: print("  -",w)
    else:
        print("Cancello contenuto: OK, nessun avviso")

if __name__=="__main__": main()
