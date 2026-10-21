"""Coleta a tabela 'SEÇÕES ELEITORAIS ALTERADAS NO SEGUNDO TURNO' do SIG/TSE
navegando pelo link 'Próximo' e grava em TSV.

Uso: python scrape.py [saida.tsv]
Sem argumento, grava em secoes_alteradas_2turno_AAAA-MM-DD_HHMM.tsv (hora local do fim da coleta).
"""
import asyncio, re, sys, random
from datetime import datetime
from playwright.async_api import async_playwright

BASE = "https://sig.tse.jus.br/ords/dwapr/r/seai/sig-eleicao-eleitorado/"
TABLE = "table.t-Report-report"
PAGTXT = ".t-Report-paginationText"
NEXT = "a.t-Report-paginationLink--next"

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

async def read_page(page):
    return await page.evaluate("""(sel) => {
      const t = document.querySelector(sel);
      const head = [...t.querySelectorAll('thead th, tr:first-child th')].map(th => th.innerText);
      const rows = [...t.querySelectorAll('tbody tr')].filter(tr => tr.querySelector('td'))
        .map(tr => [...tr.querySelectorAll('td')].map(td => td.innerText));
      return {head, rows};
    }""", TABLE)

async def range_text(page):
    return clean(await page.locator(PAGTXT).first.inner_text())

async def main(out):
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome", headless=False)
        ctx = await b.new_context(locale="pt-BR", viewport={"width": 1400, "height": 900})
        page = await ctx.new_page()
        await page.goto(BASE + "eleitorado-eleicao", wait_until="networkidle", timeout=90000)
        await page.click("a.a-TreeView-label:text-is('Capilaridade')")
        await page.wait_for_load_state("networkidle")
        await page.click("button:has-text('Tabelas detalhadas')[onclick*='alteradas']")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_selector(TABLE)

        header, rows, pageno = None, [], 0
        total = None
        while True:
            pageno += 1
            rt = await range_text(page)
            m = re.search(r"(\d+)\s*-\s*(\d+)\s*de\s*(\d+)", rt.replace(".", ""))
            if m: total = int(m.group(3))
            data = await read_page(page)
            if header is None:
                header = [clean(h) for h in data["head"]]
            got = [[clean(c) for c in r] for r in data["rows"]]
            rows.extend(got)
            print(f"pág {pageno}: {rt} -> +{len(got)} (acum {len(rows)})", flush=True)

            nxt = page.locator(NEXT).first
            if await nxt.count() == 0 or not await nxt.is_visible():
                break
            await nxt.click()
            # espera o AJAX trocar o texto "linha(s) X - Y de N"
            await page.wait_for_function(
                "([sel, old]) => { const e = document.querySelector(sel); return e && e.innerText.replace(/\\s+/g,' ').trim() !== old; }",
                arg=[PAGTXT, rt], timeout=60000)
            await page.wait_for_selector(TABLE)
            await asyncio.sleep(random.uniform(0.6, 1.2))  # gentileza com o servidor
        await b.close()

    out = out or f"secoes_alteradas_2turno_{datetime.now():%Y-%m-%d_%H%M}.tsv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(c.replace("\t", " ") for c in r) + "\n")
    print(f"OK: {len(rows)} linhas (total informado pelo site: {total}) -> {out}")
    if total is not None and total != len(rows):
        print("ATENÇÃO: contagem diferente do total informado!")
        sys.exit(1)

asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None))
