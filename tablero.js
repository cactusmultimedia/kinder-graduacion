const http = require('node:http')
const fs = require('node:fs')
const path = require('node:path')

const PORT = 3456
const VAULT = __dirname

function parseFrontmatter(text) {
  const m = text.match(/^---\s*\n([\s\S]*?)\n---/)
  if (!m) return {}
  const fm = {}
  for (const line of m[1].split('\n')) {
    const sep = line.indexOf(':')
    if (sep === -1) continue
    const key = line.slice(0, sep).trim()
    let val = line.slice(sep + 1).trim()
    if (val.startsWith('[') && val.endsWith(']')) {
      try { val = JSON.parse(val) } catch {}
    }
    fm[key] = val
  }
  return fm
}

function scanNotes(dir) {
  const notes = []
  function walk(d) {
    let entries
    try { entries = fs.readdirSync(d, { withFileTypes: true }) } catch { return }
    for (const e of entries) {
      const p = path.join(d, e.name)
      if (e.isDirectory() && !e.name.startsWith('.') && e.name !== 'node_modules') walk(p)
      else if (e.name.endsWith('.md')) {
        const content = fs.readFileSync(p, 'utf-8')
        notes.push({
          file: path.relative(VAULT, p),
          content,
          frontmatter: parseFrontmatter(content),
        })
      }
    }
  }
  walk(VAULT)
  return notes
}

function buildData() {
  const notes = scanNotes(VAULT)
  const chats = notes.filter(n => n.file.startsWith('Chats/'))
  const proyectos = notes.filter(n => n.file.startsWith('Proyectos/'))
  const pendientes = chats.filter(n => n.frontmatter.estado === 'en-curso')
  const activos = proyectos.filter(n => n.frontmatter.estado === 'activo')

  const porProyecto = {}
  for (const c of chats) {
    const p = c.frontmatter.proyecto || 'sin-proyecto'
    if (!porProyecto[p]) porProyecto[p] = []
    porProyecto[p].push(c)
  }

  const sorted = (a, b) => (b.frontmatter.fecha || '').localeCompare(a.frontmatter.fecha || '')
  for (const key of Object.keys(porProyecto)) porProyecto[key].sort(sorted)

  return { pendientes, activos, chats, proyectos, porProyecto, total: notes.length }
}

function serveFile(res, filePath, type) {
  try {
    const data = fs.readFileSync(filePath)
    res.writeHead(200, { 'Content-Type': type })
    res.end(data)
  } catch {
    res.writeHead(404)
    res.end('Not found')
  }
}

const HTML = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tablero — archivado</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; background: #1a1b1e; color: #e4e4e7; padding: 2rem; line-height: 1.5; }
  h1 { font-size: 1.5rem; font-weight: 600; margin-bottom: 1.5rem; color: #f4f4f5; letter-spacing: -0.01em; }
  h2 { font-size: 1.125rem; font-weight: 600; margin: 1.5rem 0 0.75rem; color: #a1a1aa; text-transform: uppercase; letter-spacing: 0.04em; font-size: 0.75rem; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; max-width: 1200px; }
  .card { background: #25262b; border-radius: 8px; padding: 1rem; border: 1px solid #2e2f34; }
  table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
  th { text-align: left; padding: 0.5rem 0.5rem 0.5rem 0; color: #71717a; font-weight: 500; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.03em; border-bottom: 1px solid #2e2f34; }
  td { padding: 0.5rem 0.5rem 0.5rem 0; border-bottom: 1px solid #27272a; }
  a { color: #60a5fa; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .tag { display: inline-block; font-size: 0.7rem; padding: 0.125rem 0.5rem; border-radius: 9999px; background: #2e2f34; color: #a1a1aa; }
  .tag-en-curso { background: #1a3a3a; color: #5eead4; }
  .tag-completado { background: #1a2e1a; color: #86efac; }
  .stat { font-size: 0.75rem; color: #71717a; margin-top: 0.75rem; }
  .proj-list { display: flex; flex-wrap: wrap; gap: 0.5rem; }
  .proj-card { display: block; background: #1e1f23; border: 1px solid #2e2f34; border-radius: 6px; padding: 0.75rem; width: 200px; }
  .proj-card strong { display: block; margin-bottom: 0.25rem; }
  .proj-card small { color: #71717a; font-size: 0.75rem; }
  .empty { color: #52525b; font-style: italic; font-size: 0.875rem; padding: 0.5rem 0; }
  code { background: #1a1b1e; padding: 0.125rem 0.375rem; border-radius: 4px; font-size: 0.8rem; }
  .proyecto-group { margin-bottom: 1.25rem; }
  .proyecto-header { font-weight: 600; font-size: 0.8rem; color: #c4c4c7; margin-bottom: 0.25rem; border-bottom: 1px solid #2e2f34; padding-bottom: 0.25rem; display: flex; align-items: center; gap: 0.5rem; }
  .proyecto-header .count { color: #52525b; font-weight: 400; font-size: 0.7rem; }
  .proyecto-group table { font-size: 0.8rem; }
  .proyecto-group td:first-child { width: 85px; color: #71717a; }
  .sidebar { display: flex; flex-direction: column; gap: 2rem; }
  @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<h1>Tablero</h1>
<div class="grid" id="app">
  <div>
    <h2>Pendientes</h2>
    <div class="card"><table><thead><tr><th>Chat</th><th>Proyecto</th><th>Siguiente</th></tr></thead><tbody id="pendientes-body"></tbody></table></div>
    <h2>Proyectos activos</h2>
    <div class="card"><div class="proj-list" id="proyectos-list"></div></div>
  </div>
  <div class="sidebar">
    <div>
      <h2>Chats recientes</h2>
      <div class="card"><table><thead><tr><th>Fecha</th><th>Chat</th><th>Proyecto</th><th>Estado</th></tr></thead><tbody id="chats-body"></tbody></table></div>
    </div>
    <div>
      <h2>Historial por proyecto</h2>
      <div class="card" id="historial-por-proyecto"></div>
    </div>
  </div>
</div>
<script>
function esc(t) { return t || '&mdash;' }
function link(file, label) {
  return '<a href=\"' + encodeURI('/view/' + file) + '\">' + (label || file.replace(/^Chats\\//, '')) + '</a>'
}
async function load() {
  const r = await fetch('/api/data')
  const d = await r.json()

  const pb = document.getElementById('pendientes-body')
  if (d.pendientes.length === 0) {
    pb.innerHTML = '<tr><td colspan=\"3\" class=\"empty\">Nada pendiente</td></tr>'
  } else {
    pb.innerHTML = d.pendientes.map(function(p) {
      return '<tr><td>' + link(p.file) + '</td><td>' + esc(p.frontmatter.proyecto) + '</td><td>' + esc(p.frontmatter.siguiente) + '</td></tr>'
    }).join('')
  }

  const pl = document.getElementById('proyectos-list')
  if (d.activos.length === 0) {
    pl.innerHTML = '<span class=\"empty\">Ninguno</span>'
  } else {
    pl.innerHTML = d.activos.map(function(p) {
      var desc = (p.content.split('\\n').find(function(l) { return l.trim() && !l.startsWith('---') && !l.startsWith('#') }) || '').slice(0, 80)
      return '<div class=\"proj-card\"><strong>' + link(p.file, p.file.replace('Proyectos/', '').replace('.md', '')) + '</strong><small>' + desc + '</small></div>'
    }).join('')
  }

  var sorted = d.chats.slice().sort(function(a, b) {
    return (b.frontmatter.fecha || '').localeCompare(a.frontmatter.fecha || '')
  })
  var cb = document.getElementById('chats-body')
  cb.innerHTML = sorted.slice(0, 20).map(function(c) {
    return '<tr><td>' + esc(c.frontmatter.fecha) + '</td><td>' + link(c.file) + '</td><td>' + esc(c.frontmatter.proyecto) + '</td><td><span class=\"tag tag-' + (c.frontmatter.estado || '') + '\">' + esc(c.frontmatter.estado) + '</span></td></tr>'
  }).join('')

  var hp = document.getElementById('historial-por-proyecto')
  var proyKeys = Object.keys(d.porProyecto).sort()
  if (proyKeys.length === 0) {
    hp.innerHTML = '<span class=\"empty\">Aun no hay chats</span>'
  } else {
    hp.innerHTML = proyKeys.map(function(p) {
      var items = d.porProyecto[p]
      return '<div class=\"proyecto-group\">' +
        '<div class=\"proyecto-header\">' + (p === 'sin-proyecto' ? 'Sin proyecto' : p) + ' <span class=\"count\">' + items.length + '</span></div>' +
        '<table><tbody>' +
        items.slice(0, 8).map(function(c) {
          return '<tr><td>' + esc(c.frontmatter.fecha) + '</td><td>' + link(c.file) + '</td></tr>'
        }).join('') +
        (items.length > 8 ? '<tr><td></td><td class=\"empty\">... +' + (items.length - 8) + ' mas</td></tr>' : '') +
        '</tbody></table></div>'
    }).join('')
  }

  document.getElementById('stats').textContent = d.chats.length + ' chats · ' + d.proyectos.length + ' proyectos · ' + d.total + ' notas'
}
load()
</script>
</body>
</html>`

const server = http.createServer((req, res) => {
  if (req.url === '/' || req.url === '/tablero') {
    res.writeHead(200, { 'Content-Type': 'text/html' })
    res.end(HTML)
  } else if (req.url === '/api/data') {
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify(buildData()))
  } else if (req.url.startsWith('/view/')) {
    const file = path.join(VAULT, req.url.slice(6))
    if (!file.startsWith(VAULT)) { res.writeHead(403); res.end('Forbidden'); return }
    const ext = path.extname(file)
    const types = { '.md': 'text/markdown; charset=utf-8', '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml', '.pdf': 'application/pdf' }
    serveFile(res, file, types[ext] || 'text/plain')
  } else {
    res.writeHead(404)
    res.end('Not found')
  }
})

server.listen(PORT, () => {
  const url = `http://localhost:${PORT}`
  console.log(`Tablero en ${url}`)
  try { require('child_process').exec(`open ${url}`) } catch {}
})
