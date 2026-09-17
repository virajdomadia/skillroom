"""Build mockups/tracker.html — the Skillroom tracker artifact — from PRD.md, docs/*.md and docs/07-plan.md.

Run from the project root:  python mockups/tracker-build.py
Then publish mockups/tracker.html with the Artifact tool (capabilities: {db: {}, user: {}}), keeping the same URL.
Row status lives in the artifact db at rows/<id> = {status: "todo"|"doing"|"done", updated}.
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ["PRD.md", "docs/03-requirements.md", "docs/03-user-flows.md", "docs/04-technical-design.md",
        "docs/04-ui-mockups.md", "docs/05-architecture.md", "docs/06-data-and-api.md", "docs/07-plan.md"]
LINKS = {
    "variants": "https://claude.ai/artifact/JK9cTzwVjD4GrEqV36WPXi",
    "screens": "https://claude.ai/artifact/U7Uy3zAL3dnPWmffQnk6fB",
    "landing": "https://skillroom-viraj.vercel.app",
    "repo": "https://github.com/virajdomadia/skillroom",
}

def read(p): return (ROOT / p).read_text(encoding="utf-8")

# ── plan rows ──
rows, version, milestone = [], "", ""
for line in read("docs/07-plan.md").splitlines():
    m = re.match(r"^## (v\d) — (.+?) \(", line)
    if m: version = f"{m.group(1)} {m.group(2)}"; continue
    m = re.match(r"^### (Milestone [\d.]+) — (.+?) \(≈ ([\d.]+) h\)", line)
    if m: milestone = f"{m.group(1)} · {m.group(2)}"; continue
    if line.startswith("## Whole-product"): break
    m = re.match(r"^\| ([SFLAU]\d+) \| \*\*(.+?)\*\* \|(.*)\|$", line)
    if m:
        cells = [c.strip() for c in m.group(3).split("|")]
        est = next((c for c in cells if re.fullmatch(r"[\d.]+ h", c)), "")
        rows.append({"id": m.group(1), "part": m.group(2), "version": version, "milestone": milestone, "est": est, "done": cells[-1]})

docs = [{"name": p.split("/")[-1].replace(".md", ""), "path": p, "md": read(p)} for p in DOCS]

html = r'''<title>Skillroom Tracker</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Onest:wght@400;500;600;700&family=Caveat:wght@500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<style>
:root{--bg:#FBF9F3;--bg-2:#FFFFFF;--ink:#1C2833;--ink-2:#3E4A55;--muted:#7A8590;--line:#CBD6E0;--rule:#E4EBF2;--margin:#E0655F;--hl:#FFE86B;--pen:#2B3A8C;--mint:#2E7D4F;--amber:#B8860B;
  --font:"Onest",system-ui,sans-serif;--head:"Fraunces",Georgia,serif;--hand:"Caveat",cursive;--mono:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#171A1F;--bg-2:#1F2329;--ink:#EEF1F4;--ink-2:#C9D0D8;--muted:#8E98A3;--line:#3A424C;--rule:#232830;--margin:#FF8A80;--hl:#5A4F12;--pen:#9FB0FF;--mint:#6CCB91;--amber:#E2B84C}}
:root[data-theme="dark"]{--bg:#171A1F;--bg-2:#1F2329;--ink:#EEF1F4;--ink-2:#C9D0D8;--muted:#8E98A3;--line:#3A424C;--rule:#232830;--margin:#FF8A80;--hl:#5A4F12;--pen:#9FB0FF;--mint:#6CCB91;--amber:#E2B84C}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);background-image:repeating-linear-gradient(transparent 0 27px,var(--rule) 27px 28px);color:var(--ink);font-family:var(--font);font-size:14.5px;line-height:1.5;padding-inline:clamp(16px,3vw,40px);padding-block:0 80px;position:relative}
body::before{content:"";position:fixed;left:clamp(8px,2vw,28px);top:0;bottom:0;width:2px;background:var(--margin);opacity:.6;pointer-events:none}
a{color:var(--pen)}
.top{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px;padding-block:26px 14px;border-bottom:1.5px solid var(--ink)}
.top h1{margin:0;font-family:var(--head);font-size:clamp(28px,3vw,38px);font-weight:600;letter-spacing:-.02em;font-variation-settings:'opsz' 144}
.eyebrow{font-family:var(--hand);font-size:18px;color:var(--margin)}
.stats{display:flex;gap:22px;flex-wrap:wrap;font-family:var(--hand);font-size:17px;color:var(--margin)}
.stats b{color:var(--ink);font-family:var(--head);font-weight:600;font-size:22px;display:block;line-height:1}
.tabs{display:flex;gap:6px;flex-wrap:wrap;position:sticky;top:0;z-index:20;background:var(--bg);padding-block:10px;border-bottom:1.5px solid var(--ink)}
.tab{appearance:none;border:1.5px solid var(--ink);border-bottom:0;background:var(--bg-2);color:var(--ink);font:600 17px/1 var(--hand);padding:8px 14px;border-radius:6px 6px 0 0;cursor:pointer}
.tab[aria-selected="true"]{background:var(--hl)}
.tab:focus-visible{outline:3px solid var(--margin);outline-offset:2px}
.panel{display:none;padding-top:20px}.panel.on{display:block}
/* plan */
.ver{margin-top:22px}
.ver h2{font-family:var(--head);font-size:24px;font-weight:600;margin:0 0 4px;display:flex;align-items:baseline;gap:12px}
.ver h2 small{font-family:var(--hand);font-weight:500;font-size:17px;color:var(--margin)}
.ms{font-family:var(--hand);font-size:18px;color:var(--pen);margin:14px 0 4px}
.rows{display:flex;flex-direction:column}
.rw{display:grid;grid-template-columns:52px 1fr auto auto;gap:12px;align-items:center;border-top:1px dotted var(--line);padding:9px 4px}
.rw .id{font-family:var(--mono);font-size:12px;color:var(--muted)}
.rw .part{font-weight:700}
.rw .done{font-size:12.5px;color:var(--ink-2);margin-top:2px}
.rw .est{font-family:var(--hand);font-size:17px;color:var(--margin);white-space:nowrap}
.st{appearance:none;border:1.5px solid var(--muted);background:transparent;color:var(--muted);font:600 12px var(--head);letter-spacing:.12em;text-transform:uppercase;padding:4px 10px;border-radius:3px;cursor:pointer;display:inline-flex;gap:7px;align-items:center;min-width:104px;justify-content:center;transform:rotate(-3deg)}
.st[data-s="doing"]{border-color:var(--amber);color:var(--amber)}
.st[data-s="done"]{border-color:var(--mint);color:var(--mint)}
.st:disabled{cursor:default;opacity:.8}
.rw.done-row .part{background:linear-gradient(transparent 40%,var(--hl) 40% 90%,transparent 90%);display:inline}
.bar{height:10px;background:linear-gradient(90deg,var(--hl) var(--p,0%),transparent 0);border-bottom:1.5px solid var(--ink);margin:6px 0 4px;max-width:420px}
.note{font-family:var(--hand);font-size:17px;color:var(--pen);margin-top:14px}
/* docs */
.docnav{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}
.docnav button{appearance:none;border:1px solid var(--line);background:var(--bg-2);color:var(--ink-2);font:500 12px var(--mono);padding:6px 10px;border-radius:3px;cursor:pointer}
.docnav button[aria-selected="true"]{border-color:var(--margin);color:var(--margin);background:var(--bg-2)}
.md{max-width:920px;font-size:14.5px;background:var(--bg-2);padding:22px 28px;border:1px solid var(--line)}
.md h1{font-family:var(--head);font-weight:600;font-size:26px;letter-spacing:-.02em}.md h2{font-family:var(--head);font-weight:600;font-size:20px;margin-top:32px;padding-top:12px;border-top:1.5px solid var(--ink)}.md h3{font-size:15.5px;margin-top:22px}
.md p,.md li{color:var(--ink-2)}.md strong{color:var(--ink)}
.md code{font-family:var(--mono);font-size:12.5px;background:var(--bg);border:1px solid var(--line);border-radius:3px;padding:1px 5px}
.md pre{background:var(--bg);border:1px solid var(--line);border-radius:4px;padding:14px;overflow-x:auto;font-size:12.5px}
.md pre code{background:none;border:0;padding:0}
.md .tbl{overflow-x:auto}.md table{border-collapse:collapse;font-size:13px;min-width:600px}.md th,.md td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}.md th{background:var(--bg);font-family:var(--mono);font-weight:500;font-size:11.5px;letter-spacing:.04em}
.md pre.mermaid{background:var(--bg-2);text-align:center}
/* mockups + project */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.card{border:1px solid var(--line);padding:16px;background:var(--bg-2);position:relative;box-shadow:0 6px 16px -14px rgba(0,0,0,.4)}
.card::before{content:"";position:absolute;left:0;right:0;top:38px;height:1px;background:var(--margin);opacity:.45}
.card h3{margin:0 0 10px;font-family:var(--head);font-weight:600;font-size:18px}.card p{margin:0 0 12px;color:var(--ink-2);font-size:13.5px}
.card .k{font-family:var(--hand);font-size:17px;color:var(--margin);margin-bottom:6px}
.btnl{display:inline-block;font:700 13px var(--font);color:var(--bg);background:var(--ink);padding:8px 12px;border-radius:3px;text-decoration:none}
.kv{display:grid;grid-template-columns:160px 1fr;gap:8px 16px;font-size:13.5px;max-width:860px}
.kv dt{font-family:var(--hand);font-size:17px;color:var(--margin)}.kv dd{margin:0;color:var(--ink-2)}.kv dd b{color:var(--ink)}
@media (max-width:700px){.rw{grid-template-columns:44px 1fr;grid-auto-rows:auto}.rw .est,.rw .st{grid-column:2}.kv{grid-template-columns:1fr}}
</style>
<header class="top">
  <div><div class="eyebrow">Skillroom · project 5 of 6 · tracker</div><h1>Skillroom tracker</h1></div>
  <div class="stats"><div><b id="st-done">0</b>rows done</div><div><b id="st-total">0</b>rows</div><div><b id="st-hours">0 h</b>planned</div><div><b id="st-step">7</b>lifecycle steps done</div></div>
</header>
<nav class="tabs" role="tablist"><button class="tab" role="tab" aria-selected="true" data-p="plan">Plan</button><button class="tab" role="tab" aria-selected="false" data-p="docs">Docs</button><button class="tab" role="tab" aria-selected="false" data-p="mockups">Mockups</button><button class="tab" role="tab" aria-selected="false" data-p="project">Project</button></nav>

<section class="panel on" id="p-plan"><div id="plan"></div><div class="note" id="plan-note">Click a status stamp to cycle todo → doing → done. Status is shared with everyone who can open this page.</div></section>
<section class="panel" id="p-docs"><div class="docnav" id="docnav"></div><article class="md" id="doc"></article></section>
<section class="panel" id="p-mockups"><div class="cards" id="mock"></div></section>
<section class="panel" id="p-project"><dl class="kv" id="proj"></dl></section>

<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
  const D = JSON.parse(document.getElementById('data').textContent);
  const rows = D.rows, docs = D.docs, L = D.links;
  const status = {};
  let db = null, canWrite = true;

  const planEl = document.getElementById('plan');
  function renderPlan(){
    const byVer = {}; rows.forEach(r=>{ (byVer[r.version] ||= []).push(r); });
    planEl.innerHTML = '';
    for(const [ver, rs] of Object.entries(byVer)){
      const done = rs.filter(r=>status[r.id]?.status==='done').length;
      const hours = rs.reduce((a,r)=>a+parseFloat(r.est||0),0);
      const sec = document.createElement('div'); sec.className='ver';
      sec.innerHTML = `<h2>${ver} <small>${rs.length} rows · ≈ ${hours} h · ${done} done</small></h2><div class="bar" style="--p:${rs.length?done/rs.length*100:0}%"></div>`;
      let ms = '';
      rs.forEach(r=>{
        if(r.milestone!==ms){ ms=r.milestone; const h=document.createElement('div'); h.className='ms'; h.textContent=ms; sec.appendChild(h); }
        const s = status[r.id]?.status || 'todo';
        const el = document.createElement('div'); el.className='rw'+(s==='done'?' done-row':'');
        el.innerHTML = `<span class="id">${r.id}</span><div><div class="part">${r.part}</div><div class="done">${r.done}</div></div><span class="est">${r.est||''}</span><button class="st" data-s="${s}" data-id="${r.id}" ${canWrite?'':'disabled'}>${s}</button>`;
        sec.appendChild(el);
      });
      planEl.appendChild(sec);
    }
    const total = rows.length, done = rows.filter(r=>status[r.id]?.status==='done').length;
    document.getElementById('st-done').textContent = done; document.getElementById('st-total').textContent = total;
    document.getElementById('st-hours').textContent = Math.round(rows.reduce((a,r)=>a+parseFloat(r.est||0),0)) + ' h';
  }
  planEl.addEventListener('click', async e=>{
    const b = e.target.closest('.st'); if(!b || !db || !canWrite) return;
    const id = b.dataset.id, next = {todo:'doing', doing:'done', done:'todo'}[b.dataset.s];
    b.disabled = true;
    try{ await db.doc('rows/'+id).set({status: next, updated: new Date().toISOString()}); }
    catch(err){ if(err && (err.code==='not_granted' || err.code==='permission_denied')){ canWrite=false; document.getElementById('plan-note').textContent='Read-only for you — status can only be changed by editors.'; } }
    b.disabled = false;
  });
  renderPlan();
  (async()=>{
    db = await claude.use('db');
    if(!db){ document.getElementById('plan-note').textContent = 'Status is not available in this view.'; canWrite=false; renderPlan(); return; }
    const user = await claude.use('user'); const cw = user ? await user.can('data.write') : null; if(cw===false){ canWrite=false; document.getElementById('plan-note').textContent='Read-only for you — status can only be changed by editors.'; }
    db.collection('rows').onSnapshot(snap=>{ snap.docs.forEach(d=>{ if(d.exists) status[d.id]=d.data(); }); snap.docChanges().forEach(c=>{ if(c.type==='removed') delete status[c.doc.id]; }); renderPlan(); }, ()=>{});
  })();

  const nav = document.getElementById('docnav'), art = document.getElementById('doc');
  const renderer = new marked.Renderer();
  renderer.code = function(code, lang){ const c = typeof code==='object' ? code.text : code; const l = typeof code==='object' ? code.lang : lang; if(l==='mermaid') return '<pre class="mermaid">'+c.replace(/</g,'&lt;')+'</pre>'; return '<pre><code>'+c.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</code></pre>'; };
  renderer.table = function(header, body){ if(typeof header==='object'){ const t=header; const h='<tr>'+t.header.map(c=>'<th>'+marked.parseInline(c.text)+'</th>').join('')+'</tr>'; const b=t.rows.map(r=>'<tr>'+r.map(c=>'<td>'+marked.parseInline(c.text)+'</td>').join('')+'</tr>').join(''); return '<div class="tbl"><table><thead>'+h+'</thead><tbody>'+b+'</tbody></table></div>'; } return '<div class="tbl"><table><thead>'+header+'</thead><tbody>'+body+'</tbody></table></div>'; };
  function showDoc(i){ nav.querySelectorAll('button').forEach((b,j)=>b.setAttribute('aria-selected', i===j)); art.innerHTML = marked.parse(docs[i].md, {renderer, gfm:true}); art.querySelectorAll('a[href^="docs/"],a[href^="../"],a[href$=".md"]').forEach(a=>{ const n=a.getAttribute('href').split('/').pop().replace('.md',''); const k=docs.findIndex(d=>d.name===n); if(k>=0){ a.href='#'; a.onclick=e=>{e.preventDefault(); showDoc(k); window.scrollTo({top:0});}; } }); if(window.mermaid){ try{ mermaid.run({nodes: art.querySelectorAll('pre.mermaid')}); }catch(e){} } }
  docs.forEach((d,i)=>{ const b=document.createElement('button'); b.textContent=d.name; b.setAttribute('aria-selected', i===0); b.onclick=()=>showDoc(i); nav.appendChild(b); });
  showDoc(0);

  document.getElementById('mock').innerHTML = [
    ['Direction variants', 'Six directions (Workshop, Screening room, Notebook, Blueprint, Journal, Playground), six screens each, eight live motion candidates. Chosen: C · Notebook (2026-09-17).', L.variants, 'Open variants'],
    ['Screens · v1', 'Every v1 screen in Notebook: home, browse, course, player (resume), buy sheet, my learning, certificate + verify, sign in / apply, creator page, studio (courses, editor, lesson upload → processing → ready, failed, earnings), admin (dashboard, creators, courses + jobs), states.', L.screens, 'Open screens'],
    ['Landing · live', 'The existing landing page, deployed on Vercel from web/ (will move to skillroom.virajdomadia.com).', L.landing, 'Open landing'],
    ['Photos', 'CC photos from Wikimedia Commons in mockups/img/ with credits in CREDITS.md — Skillroom and its creators are fictional.', L.repo + '/blob/main/mockups/img/CREDITS.md', 'Credits'],
  ].map(([t,p,u,b])=>`<div class="card"><div class="k">mockup</div><h3>${t}</h3><p>${p}</p><a class="btnl" href="${u}" target="_blank" rel="noopener">${b} ↗</a></div>`).join('');

  document.getElementById('proj').innerHTML = [
    ['Name', '<b>Skillroom</b> · learn from people who do it · project 5 of 6, build fourth'],
    ['One-liner', 'A three-sided course platform (student / creator / admin) on our own video stack: upload → ffmpeg worker → encrypted adaptive HLS → a key server that only answers for enrolled students. No Mux, ₹0 per play.'],
    ['URLs', 'skillroom.virajdomadia.com · api.skillroom.virajdomadia.com · landing at skillroom-viraj.vercel.app until DNS'],
    ['Repo', `<a href="${L.repo}" target="_blank" rel="noopener">github.com/virajdomadia/skillroom</a> · web/ Next.js 15 + hls.js · api/ FastAPI + fpdf2 · worker/ ffmpeg on GitHub Actions`],
    ['Versions', '<b>v1 Classroom</b> 16 h → <b>v2 All-access</b> 11 h → <b>v3 Royalties</b> 8 h → <b>v4 Offline lessons</b> 3 h ≈ 38 h · add-ons after v4 only from time saved'],
    ['Unique feature', 'v4: the site installs as a PWA; a lesson downloads as encrypted segments and plays offline under a 48-h key lease — ₹0 per use, and "non-enrolled can never play" still holds'],
    ['Engine', 'Client upload to Blob → video_jobs → repository_dispatch → worker (ffmpeg: 240/480/720p, AES-128, poster, sprite) → Blob → manifest; API generates playlists and serves the key only after can_watch()'],
    ['Money', 'Razorpay one-off (v1) with idempotent mark_paid → enrollment + ledger (80/20); Subscriptions state machine (v2); pool split by subscriber-minutes (v3); payouts marked by admin'],
    ['Seed', '6 fictional Bengaluru creators · 6 courses · 24 lessons of real CC video from Commons through the real worker · ≤ 700 MB · ~40 enrollments with heartbeats; demo student, creator, admin'],
    ['Direction', 'C · Notebook — ruled paper with a red margin, Fraunces + Onest + Caveat, taped photos, sticky-note prices, contents with dotted leaders, stamps for state; signature = Develop + Stamp in the studio, Resume glide (sticky note) in the player'],
    ['Lifecycle', 'Steps 1–7 complete (2026-09-17). Next: step 8 = milestone 1.0, after Offcut (order 1 → 2 → 4 → 5 → 3 → 6)'],
    ['Rules', 'Lean setup, rich features · accounts just-in-time (Neon S2; Blob + GitHub dispatch token + Actions secrets S3; Razorpay F3; Resend L4) · one PR per row, every PR visible in the browser · tests only from 04 §13 · tracker updated per milestone'],
  ].map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join('');

  const tabs=[...document.querySelectorAll('.tab')];
  function show(p){ tabs.forEach(t=>t.setAttribute('aria-selected', t.dataset.p===p)); document.querySelectorAll('.panel').forEach(x=>x.classList.toggle('on', x.id==='p-'+p)); try{localStorage.setItem('sr-tab',p)}catch(e){} }
  tabs.forEach(t=>t.onclick=()=>show(t.dataset.p));
  let start='plan'; try{ start=localStorage.getItem('sr-tab')||'plan'; }catch(e){} show(start);
})();
</script>
'''
data = json.dumps({"rows": rows, "docs": docs, "links": LINKS}, ensure_ascii=False).replace("</", "<\\/")
out = ROOT / "mockups" / "tracker.html"
out.write_text(html.replace("__DATA__", data), encoding="utf-8", newline="\n")
print(f"wrote {out} · {len(rows)} rows · {len(docs)} docs")
for r in rows: print(" ", r["id"], r["est"], r["part"][:40])
