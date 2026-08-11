// Serverless function (Vercel) — riceve il form del sito e crea il contatto in GoHighLevel.
// Il token resta lato server (variabili d'ambiente su Vercel), MAI nel browser.
// Env richieste su Vercel:  GHL_TOKEN  e  GHL_LOCATION
export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'method_not_allowed' })

  const token = process.env.GHL_TOKEN
  const locationId = process.env.GHL_LOCATION || 'dBDJJALoNI6Gps2GwMqb'
  if (!token) return res.status(500).json({ error: 'not_configured' })

  let b = req.body
  if (typeof b === 'string') { try { b = JSON.parse(b) } catch { b = {} } }
  b = b || {}

  const name = String(b.name || '').trim()
  const email = String(b.email || '').trim()
  const phone = String(b.phone || '').trim()
  const address = String(b.address || '').trim()
  const message = String(b.message || '').trim()
  const source = String(b.source || 'sito-web').trim()

  if (!name || !email) return res.status(400).json({ error: 'missing_fields' })

  const parts = name.split(' ')
  const firstName = parts.shift() || name
  const lastName = parts.join(' ')

  const H = {
    Authorization: `Bearer ${token}`,
    Version: '2021-07-28',
    'Content-Type': 'application/json',
    Accept: 'application/json',
  }

  try {
    const r = await fetch('https://services.leadconnectorhq.com/contacts/', {
      method: 'POST',
      headers: H,
      body: JSON.stringify({
        locationId, firstName, lastName, name, email, phone,
        address1: address,
        source,
        tags: ['lead-sito-web', 'proprietario'],
      }),
    })
    const data = await r.json().catch(() => ({}))

    // contatto duplicato = lead comunque valido: lo trattiamo come successo
    const dup = r.status === 400 && /duplicat/i.test(JSON.stringify(data || {}))
    if (!r.ok && !dup) return res.status(502).json({ error: 'ghl_error', status: r.status })

    // se c'è un messaggio, lo salvo come nota sul contatto
    const contactId = data?.contact?.id || data?.contact?._id || (dup ? data?.meta?.contactId : null)
    if (message && contactId) {
      await fetch(`https://services.leadconnectorhq.com/contacts/${contactId}/notes`, {
        method: 'POST', headers: H, body: JSON.stringify({ body: message }),
      }).catch(() => {})
    }

    return res.status(200).json({ ok: true })
  } catch (e) {
    return res.status(502).json({ error: 'network' })
  }
}
