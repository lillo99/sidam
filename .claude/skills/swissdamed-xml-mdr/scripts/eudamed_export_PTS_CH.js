// Export EUDAMED dei 30 PTS "solo Svizzera" (legacy MDD) -> file JSON nei Download.
// Funziona su:
//  A) sito pubblico  https://ec.europa.eu/tools/eudamed/#/screen/search-device   (consigliato, prova prima qui)
//  B) EUDAMED secure https://webgate.ec.europa.eu/eudamed/secure#/devices/udiDi/management (con login)
// Uso: aprire la pagina in Chrome/Edge, F12 -> Console, incollare tutto e premere Invio
// (se Chrome blocca l'incolla scrivere prima:  allow pasting  e Invio).
// Su EUDAMED secure: PRIMA aprire a mano il dettaglio di un dispositivo qualsiasi,
// così lo script vede quali indirizzi API usa la pagina e li riusa.
(async () => {
  const PTS = [ // [UDI-DI, REF] dal file Swissdamed del 29.10
    ["08033178314596", "AB1184"],
    ["08033178354974", "AB2627"],
    ["08033178360807", "AB2900"],
    ["08033178375771", "AB3814"],
    ["08033178380195", "AB3814TMP"],
    ["08033178375788", "AB3815"],
    ["08033178380201", "AB3815TMP"],
    ["08033178385107", "AB4376"],
    ["08033178390071", "AB4670"],
    ["08033178391887", "AB4744"],
    ["08033178391894", "AB4745"],
    ["08033178312387", "C22909"],
    ["08033178312400", "C22911"],
    ["08033178314619", "C22996"],
    ["08033178331562", "C23522"],
    ["08033178393614", "C24680"],
    ["08033178377539", "IN01861"],
    ["08033178383363", "IN01953"],
    ["08033178397612", "IN02192"],
    ["08033178398091", "IN02197"],
    ["08033178398251", "IN02199"],
    ["08033178399036", "IN02203"],
    ["08033178241175", "025985602"],
    ["08033178260312", "074705000"],
    ["08033178261135", "074709000"],
    ["08033178224888", "081049"],
    ["08033178213523", "082442"],
    ["08033178253598", "083600"],
    ["08033178228879", "083614"],
    ["08033178252690", "097534"]
  ];
  const EXTRA_REF = ["IN01558"]; // in lista PTS ma non nell'XML: cercato solo per REF
  const q = "languageIso2Code=en&iso2Code=en";
  const out = { exportedAt: new Date().toISOString(), page: location.href, base: null, devices: [], notFound: [], errors: [], apiSeen: [] };
  const get = async (url) => {
    const r = await fetch(url, { headers: { Accept: "application/json" }, credentials: "include" });
    if (!r.ok) throw new Error(r.status + " " + url);
    const t = await r.text();
    try { return JSON.parse(t); } catch (e) { throw new Error("risposta non JSON " + url); }
  };
  // indirizzi API già usati dalla pagina -> basi candidate
  const seen = performance.getEntriesByType("resource").map((e) => e.name).filter((u) => /\/api\//.test(u));
  out.apiSeen = [...new Set(seen)].slice(0, 200);
  const cands = [];
  if (location.host === "ec.europa.eu") cands.push("https://ec.europa.eu/tools/eudamed/api/devices");
  for (const u of seen) { const m = u.match(/^(.*?\/api)\//); if (m) cands.push(m[1] + "/devices"); }
  cands.push(location.origin + "/eudamed/secure/api/devices", location.origin + "/eudamed/api/devices",
             location.origin + "/tools/eudamed/api/devices");
  const bases = [...new Set(cands)];
  const search = async (base, k, v) => {
    const s = await get(`${base}/udiDiData?${k}=${encodeURIComponent(v)}&page=0&pageSize=25&size=25&${q}`);
    return s.content || s.items || s.results || (Array.isArray(s) ? s : []);
  };
  for (const b of bases) {
    try { await search(b, "primaryDi", PTS[0][0]); out.base = b; break; }
    catch (e) { out.errors.push({ test: b, error: e.message }); }
  }
  if (!out.base) console.warn("Nessuna API trovata: il file conterrà solo gli indirizzi visti (apiSeen). Mandamelo lo stesso.");
  const fetchAll = async (hit) => {
    const r = { search: hit, detail: null, basic: null };
    try { r.detail = await get(`${out.base}/udiDiData/${hit.uuid}?${q}`); } catch (e) { r.detailError = e.message; }
    try { r.basic = await get(`${out.base}/basicUdiData/udiDiData/${hit.uuid}?${q}`); } catch (e) { r.basicError = e.message; }
    return r;
  };
  const items = PTS.map(([di, ref]) => ({ di, ref })).concat(EXTRA_REF.map((ref) => ({ di: null, ref })));
  for (const [i, it] of items.entries()) {
    console.log(`(${i + 1}/${items.length}) ${it.di || "-"} ${it.ref}`);
    if (!out.base) { out.notFound.push(it); continue; }
    try {
      let hits = [];
      if (it.di) hits = (await search(out.base, "primaryDi", it.di)).filter((x) => JSON.stringify(x).includes(it.di));
      for (const k of ["reference", "referenceNumber", "catalogNumber"]) {
        if (hits.length) break;
        try { hits = (await search(out.base, k, it.ref)).filter((x) => JSON.stringify(x).includes(it.ref)); } catch (e) {}
      }
      if (!hits.length) { out.notFound.push(it); continue; }
      for (const h of hits) out.devices.push({ ...it, ...(await fetchAll(h)) });
    } catch (e) { out.errors.push({ ...it, error: e.message }); }
    await new Promise((r) => setTimeout(r, 300));
  }
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "eudamed_PTS_CH_" + new Date().toISOString().slice(0, 10) + ".json";
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  console.log(`Fatto: ${out.devices.length} trovati, ${out.notFound.length} non trovati, ${out.errors.length} errori. API: ${out.base}`);
})();
