import { useEffect, useRef, useState } from 'react'
import { animate, stagger, onScroll, utils, createScope } from 'animejs'
import { T } from './i18n.js'

export default function App() {
  const root = useRef(null)
  const [lang, setLang] = useState('it')
  const [scrolled, setScrolled] = useState(false)
  const [sent, setSent] = useState(false)
  const t = T[lang]

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

  const submit = (e) => { e.preventDefault(); setSent(true) }

  return (
    <div ref={root}>
      {/* HEADER */}
      <header className={scrolled ? 'scrolled' : ''}>
        <div className="wrap nav">
          <a className="brand" href="#top">
            <img src="/assets/logo.png" alt="B&P Lux Property" />
            <span className="bt">B&amp;P<small>Lux Property</small></span>
          </a>
          <nav><ul>
            <li><a href="#proprietari">{t.nav.prop}</a></li>
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
          <div className="pf">
            {t.portfolio.cards.map((c, i) => (
              <div className="card reveal" key={i}>
                <div className="ph" style={{ backgroundImage: `url(/assets/prop${i + 1}.jpg)` }}></div>
                <div className="body"><h3>{c.t}</h3><div className="meta"><span>{c.m}</span><span className="cin">CIN ······</span></div></div>
              </div>
            ))}
          </div>
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
                <div className="pic">{p.in}</div>
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
            <a className="wa" href="https://wa.me/39XXXXXXXXXX">✆ WhatsApp →</a>
          </div>
          <form className="reveal" onSubmit={submit}>
            {sent ? <div className="ok">{t.cta.ok}</div> : <>
              <label>{t.cta.f.name}</label><input required placeholder="Mario Rossi" />
              <label>{t.cta.f.email}</label><input required type="email" placeholder="mario@email.it" />
              <label>{t.cta.f.tel}</label><input required placeholder="+39 ..." />
              <label>{t.cta.f.addr}</label><input placeholder="Via, città" />
              <label>{t.cta.f.msg}</label><textarea rows="3"></textarea>
              <button type="submit" className="btn btn-dark">{t.cta.f.send}</button>
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
              <p>info@bpluxproperty.com</p><p>+39 ··· ······</p><p>Instagram · Facebook</p>
            </div>
            <div>
              <p className="fh">{t.footer.legal}</p>
              <p><a href="#">{t.footer.privacy}</a></p><p><a href="#">{t.footer.terms}</a></p><p>P.IVA ···········</p>
            </div>
          </div>
          <div>© {new Date().getFullYear()} B&amp;P Lux Property — Bertocchi &amp; Puggioni. {t.footer.rights}</div>
        </div>
      </footer>
    </div>
  )
}
