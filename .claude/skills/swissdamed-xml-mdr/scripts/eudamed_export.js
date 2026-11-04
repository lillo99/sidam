// Export dati UDI-DI da EUDAMED (sito pubblico) -> file JSON nei Download.
// Uso: aprire https://ec.europa.eu/tools/eudamed/#/screen/search-device in Chrome o Edge,
// premere F12 -> scheda "Console", incollare tutto questo testo e premere Invio.
// (Se Chrome blocca l'incolla, scrivere prima: allow pasting  e premere Invio.)
// Non serve login né diritti di amministratore: legge solo dati pubblici.
(async () => {
  const UDI = [
    // SUCTION DEVICES (8033178CANCSUMPWR, 8033178CARDASUCUE) + PROTEK DUO+ (8033178CANCVENOVENOCE)
    "08033178004695", "08033178004701", "08033178013154", "08033178114622", "08033178010726", "08033178113878",
    "08033178113618", "08033178018708", "08033178113861", "08033178019446", "08033178019408", "08033178018739",
    "08033178013673", "08033178013697", "08033178018678", "08033178013710", "08033178018661", "08033178018647",
    "08033178004466", "08033178018654", "08033178018746", "08033178018722", "08033178018715", "08033178018753",
  ];
  const API = "https://ec.europa.eu/tools/eudamed/api/devices";
  const q = "languageIso2Code=en&iso2Code=en";
  const out = { exportedAt: new Date().toISOString(), devices: [], errors: [] };
  const get = async (url) => {
    const r = await fetch(url, { headers: { Accept: "application/json" }, credentials: "include" });
    if (!r.ok) throw new Error(r.status + " " + url);
    return r.json();
  };
  const basics = {};
  for (const [i, di] of UDI.entries()) {
    console.log(`(${i + 1}/${UDI.length}) ${di}`);
    try {
      const s = await get(`${API}/udiDiData?primaryDi=${di}&page=0&pageSize=25&size=25&${q}`);
      const hit = (s.content || []).find((x) => (x.primaryDi || "").includes(di)) || (s.content || [])[0];
      if (!hit) { out.errors.push({ di, error: "non trovato", search: s }); continue; }
      const detail = await get(`${API}/udiDiData/${hit.uuid}?${q}`);
      let basic = null;
      try { basic = await get(`${API}/basicUdiData/udiDiData/${hit.uuid}?${q}`); }
      catch (e) { out.errors.push({ di, error: "basic: " + e.message }); }
      if (basic) basics[basic.basicUdi?.code || basic.basicUdi || hit.basicUdi || di] = basic;
      out.devices.push({ di, search: hit, detail, basic });
    } catch (e) {
      out.errors.push({ di, error: e.message });
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  out.basics = basics;
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "eudamed_export_" + new Date().toISOString().slice(0, 10) + ".json";
  document.body.appendChild(a); a.click(); a.remove();
  console.log(`Fatto: ${out.devices.length} dispositivi, ${out.errors.length} errori. File salvato nei Download.`);
})();
