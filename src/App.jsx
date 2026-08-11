import { useEffect, useRef, useState } from 'react'
import { animate, stagger, onScroll, utils, createScope } from 'animejs'
import { T } from './i18n.js'

export default function App() {
  const root = useRef(null)
  const [lang, setLang] = useState('it')
  const [scrolled, setScrolled] = useState(false)
  const [sent, setSent] = useState(false)
  const [sending, setSending] = useState(false)
  const [formErr, setFormErr] = useState(false)
  const t = T[lang]
  const f = t.portfolio.featured

  useEffect(() => {
    const onScrollWin = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScrollWin)
    return () => window.removeEventListener('scroll', onScrollWin)
  }, [])

  useEffect(() => {
    const r = root.current
    if (!r) return
    console.log('[fx]', { animate: typeof animate, onScroll: typeof onScroll, heroAnim: r.querySelectorAll('.hero-anim').length, reveal: r.querySelectorAll('.reveal').length })
    // Hero entrance (staggered)
    animate(r.querySelectorAll('.hero-anim'), { opacity: [0, 1], y: [30, 0], delay: stagger(110, { start: 150 }), duration: 1000, ease: 'out(4)' })
    animate(r.querySelector('.hero-bg'), { scale: [1.14, 1.04], duration: 2800, ease: 'out(3)' })
    animate(r.querySelector('.hero-rule'), { scaleX: [0, 1], duration: 1200, delay: 450, ease: 'inOut(3)' })
    // Scroll reveals
    r.querySelectorAll('.reveal').forEach((el) => {
      animate(el, { opacity: [0, 1], y: [28, 0], duration: 850, ease: 'out(3)', autoplay: onScroll({ target: el, enter: 'bottom-=60 top' }) })
    })
    // Animated counters
    r.querySelectorAll('.stat-num').forEach((el) => {
      const n = +el.dataset.n
      const obj = { v: 0 }
      animate(obj, { v: n, duration: 1700, ease: 'out(4)', modifier: utils.round(0), onUpdate: () => { el.textContent = obj.v }, autoplay: onScroll({ target: el, enter: 'bottom-=20 top' }) })
    })
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    setFormErr(false); setSending(true)
    const payload = Object.fromEntries(new FormData(e.target).entries())
    payload.source = 'sito-home'; payload.lang = lang
    try {
      const r = await fetch('/api/lead', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (!r.ok) throw new Error('bad')
      setSent(true)
    } catch (_) { setFormErr(true) } finally { setSending(false) }
  }

  return (
    <div ref={root}>
      <a className="wa-float" href="https://wa.me/393467259098?text=Ciao%20B%26P%20Lux%20Property%2C%20vorrei%20informazioni%20sulla%20gestione%20del%20mio%20immobile." target="_blank" rel="noreferrer" aria-label="WhatsApp">
        <svg viewBox="0 0 32 32" aria-hidden="true"><path d="M16 .5C7.4.5.5 7.4.5 16c0 2.8.7 5.4 2 7.8L.5 31.5l7.9-2c2.3 1.2 4.9 1.9 7.6 1.9 8.6 0 15.5-6.9 15.5-15.5S24.6.5 16 .5zm0 28c-2.4 0-4.7-.7-6.7-1.9l-.5-.3-4.7 1.2 1.3-4.6-.3-.5C3.7 20.3 3 18.2 3 16 3 8.8 8.8 3 16 3s13 5.8 13 13-5.8 12.5-13 12.5zm7.1-9.4c-.4-.2-2.3-1.1-2.6-1.3-.4-.1-.6-.2-.9.2s-1 1.3-1.2 1.5c-.2.2-.4.3-.8.1-.4-.2-1.6-.6-3.1-1.9-1.1-1-1.9-2.3-2.1-2.7-.2-.4 0-.6.2-.8.2-.2.4-.4.6-.7.2-.2.2-.4.3-.6.1-.2 0-.5 0-.7-.1-.2-.9-2.1-1.2-2.9-.3-.8-.6-.7-.9-.7h-.8c-.2 0-.6.1-1 .5s-1.4 1.3-1.4 3.3 1.4 3.8 1.6 4.1c.2.2 2.8 4.3 6.8 6 .9.4 1.7.6 2.2.8.9.3 1.8.2 2.4.2.7-.1 2.3-.9 2.6-1.9.3-.9.3-1.7.2-1.9-.1-.1-.3-.2-.7-.4z"/></svg>
      </a>
      {/* HEADER */}
      <header className={scrolled ? 'scrolled' : ''}>
        <div className="wrap nav">
          <a className="brand" href="#top">
            <img src="/assets/logo.png" alt="B&P Lux Property" />
            <span className="bt">B&amp;P<small>Lux Property</small></span>
          </a>
          <nav><ul>
            <li><a href="#proprietari">{t.nav.prop}</a></li>
            <li><a href="#agenzie">{t.nav.agencies}</a></li>
            <li><a href="#metodo">{t.nav.method}</a></li>
            <li><a href="#portfolio">{t.nav.portfolio}</a></li>
            <li><a href="#founder">{t.nav.about}</a></li>
            <li><a href="#contatti">{t.nav.contact}</a></li>
          </ul></nav>
          <div className="head-right">
            <button className="lang" onClick={() => setLang(lang === 'it' ? 'en' : 'it')} aria-label="language">
              <span className={lang === 'it' ? 'on' : ''}>IT</span>/<span className={lang === 'en' ? 'on' : ''}>EN</span>
            </button>
            <a href="#contatti" className="btn btn-gold">{t.nav.cta}</a>
          </div>
        </div>
      </header>

      {/* HERO */}
      <span id="top"></span>
      <section className="hero">
        <div className="hero-bg"></div>
        <div className="wrap">
          <span className="eyebrow hero-anim">{t.hero.eyebrow}</span>
          <h1 className="hero-anim">{t.hero.titleA} <span className="gold">{t.hero.titleB}</span></h1>
          <div className="hero-rule hero-anim"></div>
          <p className="hero-anim">{t.hero.sub}</p>
          <div className="hero-cta hero-anim">
            <a href="#contatti" className="btn btn-gold">{t.hero.cta1} →</a>
            <a href="#metodo" className="btn btn-ghost">{t.hero.cta2}</a>
          </div>
        </div>
      </section>

      {/* STATS */}
      <section className="stats">
        <div className="wrap grid4">
          {t.stats.map((s, i) => (
            <div className="reveal" key={i}>
              <div className="statline"><span className="stat-num" data-n={s.n}>0</span><span className="suf">{s.suffix}</span></div>
              <div className="l">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* PER I PROPRIETARI */}
      <section id="proprietari">
        <div className="wrap">
          <div className="sec-head reveal">
            <span className="eyebrow">{t.prop.eyebrow}</span>
            <h2>{t.prop.title}</h2>
            <p>{t.prop.sub}</p>
          </div>
          <div className="pillars">
            {t.prop.cards.map((c, i) => (
              <div className="pillar reveal" key={i}>
                <span className="tag">{c.tag}</span>
                <h3>{c.title}</h3>
                <ul>{c.items.map((it, j) => <li key={j}>{it}</li>)}</ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* METODO */}
      <section id="metodo" className="steps">
        <div className="wrap">
          <div className="sec-head reveal">
            <span className="eyebrow">{t.method.eyebrow}</span>
            <h2 style={{ color: '#fff' }}>{t.method.title}</h2>
          </div>
          <div className="grid4 stepgrid">
            {t.method.steps.map((s, i) => (
              <div className="step reveal" key={i}>
                <div className="num">{String(i + 1).padStart(2, '0')}</div>
                <h3>{s.t}</h3><p>{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PORTFOLIO */}
      <section id="portfolio">
        <div className="wrap">
          <div className="sec-head reveal">
            <span className="eyebrow">{t.portfolio.eyebrow}</span>
            <h2>{t.portfolio.title}</h2><p>{t.portfolio.sub}</p>
          </div>

          <div className="feat-listing reveal">
            <div className="fl-gallery">
              <div className="fl-main" style={{ backgroundImage: 'url(/assets/dozza/dozza-1.jpg)' }}></div>
              <div className="fl-grid">
                <div style={{ backgroundImage: 'url(/assets/dozza/dozza-2.jpg)' }}></div>
                <div style={{ backgroundImage: 'url(/assets/dozza/dozza-3.jpg)' }}></div>
                <div style={{ backgroundImage: 'url(/assets/dozza/dozza-4.jpg)' }}></div>
                <div style={{ backgroundImage: 'url(/assets/dozza/dozza-5.jpg)' }}></div>
              </div>
            </div>
            <div className="fl-info">
              <span className="fl-badge">★ {f.badge}</span>
              <h3>{f.title}</h3>
              <div className="fl-loc">{f.loc} · {f.meta}</div>
              <div className="fl-rate"><b>{f.rating}</b><span className="stars">★★★★★</span><span className="fl-rn">{f.reviews} {f.revsWord} · {f.host}</span></div>
              <p className="fl-desc">{f.desc}</p>
              <ul className="fl-amen">{f.amen.map((a, i) => <li key={i}>{a}</li>)}</ul>
              <div className="fl-foot">
                <a className="btn btn-gold" href={f.url} target="_blank" rel="noopener noreferrer">{f.cta} →</a>
                <span className="fl-cin">CIN {f.cin}</span>
              </div>
            </div>
          </div>

          <div className="fl-reviews">
            {f.revs.map((r, i) => (
              <div className="rev reveal" key={i}>
                <div className="rev-stars">★★★★★</div>
                <p>{r.t}</p>
                <div className="rev-who">{r.n} · {r.d}</div>
              </div>
            ))}
          </div>

          <div className="pf-cta reveal"><a className="btn btn-gold" href="#contatti">{t.nav.cta}</a></div>
        </div>
      </section>

      {/* AGENZIE */}
      <section id="agenzie" className="agenzie">
        <div className="wrap">
          <div className="sec-head reveal">
            <span className="eyebrow">{t.agenzie.eyebrow}</span>
            <h2>{t.agenzie.title}</h2>
            <p>{t.agenzie.sub}</p>
          </div>
          <div className="pillars">
            {t.agenzie.cards.map((c, i) => (
              <div className="pillar reveal" key={i}>
                <span className="tag">{c.tag}</span>
                <h3>{c.title}</h3>
                <ul>{c.items.map((it, j) => <li key={j}>{it}</li>)}</ul>
              </div>
            ))}
          </div>
          <div className="ag-cta reveal"><a href="/agenzie-immobiliari" className="btn btn-gold">{t.agenzie.cta}</a></div>
        </div>
      </section>

      {/* FOUNDERS */}
      <section id="founder" className="founders">
        <div className="wrap">
          <div className="sec-head reveal">
            <span className="eyebrow">{t.founders.eyebrow}</span>
            <h2>{t.founders.title}</h2><p>{t.founders.sub}</p>
          </div>
          <div className="fgrid">
            {t.founders.people.map((p, i) => (
              <div className="founder reveal" key={i}>
                <div className="pic">{p.img ? <img src={p.img} alt={p.name} /> : p.in}</div>
                <div><h3>{p.name}</h3><div className="role">{p.role}</div><p>{p.bio}</p></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* REVIEWS */}
      <section id="recensioni">
        <div className="wrap">
          <div className="sec-head reveal"><span className="eyebrow">{t.reviews.eyebrow}</span><h2>{t.reviews.title}</h2></div>
          <div className="tgrid">
            {t.reviews.items.map((r, i) => (
              <div className="quote reveal" key={i}><p>“{r.q}”</p><div className="who">{r.w}</div></div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA + FORM */}
      <section id="contatti" className="cta">
        <div className="wrap cta-grid">
          <div className="reveal">
            <span className="eyebrow">{t.cta.eyebrow}</span>
            <h2>{t.cta.title}</h2>
            <p>{t.cta.sub}</p>
            <a className="wa" href="https://wa.me/393467259098" target="_blank" rel="noreferrer">✆ WhatsApp +39 346 725 9098 →</a>
          </div>
          <form className="reveal" onSubmit={submit}>
            {sent ? <div className="ok">{t.cta.ok}</div> : <>
              <label>{t.cta.f.name}</label><input name="name" required placeholder="Mario Rossi" />
              <label>{t.cta.f.email}</label><input name="email" required type="email" placeholder="mario@email.it" />
              <label>{t.cta.f.tel}</label><input name="phone" required placeholder="+39 ..." />
              <label>{t.cta.f.addr}</label><input name="address" placeholder="Via, città" />
              <label>{t.cta.f.msg}</label><textarea name="message" rows="3"></textarea>
              <button type="submit" className="btn btn-dark" disabled={sending}>{sending ? '…' : t.cta.f.send}</button>
              {formErr && <div className="note" style={{ color: '#c0392b' }}>{t.cta.f.err}</div>}
              <div className="note">{t.cta.f.note}</div>
            </>}
          </form>
        </div>
      </section>

      {/* FOOTER */}
      <footer>
        <div className="wrap">
          <div className="fcols">
            <div>
              <div className="brand"><img src="/assets/logo.png" alt="" style={{ height: 40, width: 40 }} /><span className="bt" style={{ color: '#fff' }}>B&amp;P<small>Lux Property</small></span></div>
              <p style={{ maxWidth: '30ch', marginTop: 10 }}>{t.footer.tagline}</p>
            </div>
            <div>
              <p className="fh">{t.footer.contacts}</p>
              <p>info@bpluxproperty.com</p><p><a href="https://wa.me/393467259098" target="_blank" rel="noreferrer">+39 346 725 9098</a></p><p>Instagram · Facebook</p>
            </div>
            <div>
              <p className="fh">{t.footer.legal}</p>
              <p><a href="/privacy.html">{t.footer.privacy}</a></p><p><a href="/termini.html">{t.footer.terms}</a></p>
            </div>
          </div>
          <div>© {new Date().getFullYear()} B&amp;P Lux Property — Bertocchi &amp; Puggioni. {t.footer.rights}</div>
        </div>
      </footer>
    </div>
  )
}
