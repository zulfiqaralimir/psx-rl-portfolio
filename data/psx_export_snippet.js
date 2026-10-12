// Paste into the DevTools console on https://dps.psx.com.pk/historical
// Downloads one CSV per ticker: <TICKER>.csv with columns date,open,high,low,close,volume
(async () => {
  const tickers = ['ATRL','BAFL','BOP','DGKC','EFERT','ENGROH','FATIMA','FCCL','FFC','HBL',
    'HUBC','KEL','LUCK','MARI','MCB','MEBL','MLCF','NBP','NRL','OGDC',
    'PAEL','POL','PPL','PSO','PTC','SAZEW','SEARL','SNGP','SYS','UBL'];
  const num = s => parseFloat(s.replace(/,/g, '')) || 0;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const failed = [];
  for (const [i, sym] of tickers.entries()) {
    try {
      const res = await fetch('/historical', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Requested-With': 'XMLHttpRequest' },
        body: new URLSearchParams({ symbol: sym, date: new Date().toISOString().slice(0, 10) }),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const doc = new DOMParser().parseFromString(await res.text(), 'text/html');
      const rows = [...doc.querySelectorAll('tr')].map(tr => {
        const td = tr.querySelectorAll('td');
        if (td.length < 6 || !td[0].dataset.order) return null;
        const d = new Date(parseInt(td[0].dataset.order, 10) * 1000).toISOString().slice(0, 10);
        return [d, num(td[1].textContent), num(td[2].textContent), num(td[3].textContent), num(td[4].textContent), num(td[5].textContent)].join(',');
      }).filter(Boolean);
      if (!rows.length) throw new Error('0 rows');
      const csv = 'date,open,high,low,close,volume\n' + rows.join('\n') + '\n';
      const a = Object.assign(document.createElement('a'), {
        href: URL.createObjectURL(new Blob([csv], { type: 'text/csv' })), download: sym + '.csv' });
      document.body.appendChild(a); a.click(); a.remove();
      console.log(`[${i + 1}/30] ${sym}: ${rows.length} rows`);
    } catch (e) { failed.push(sym); console.error(`[${i + 1}/30] ${sym} FAILED: ${e.message}`); }
    await sleep(1000);
  }
  console.log('Done. Failed:', failed.length ? failed.join(', ') : 'none');
})();

