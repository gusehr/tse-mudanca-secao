"""Embute o TSV de seções alteradas no index.html (página autocontida).

Sem argumentos, usa a extração mais recente (secoes_alteradas_2turno_AAAA-MM-DD.tsv)
e atualiza a data de extração exibida na página.

Uso: python build.py [entrada.tsv] [index.html]
"""
import glob, re, sys

src = sys.argv[1] if len(sys.argv) > 1 else max(glob.glob("secoes_alteradas_2turno_????-??-??.tsv"))
page = sys.argv[2] if len(sys.argv) > 2 else "index.html"
OPEN = '<script id="dados" type="text/tab-separated-values">'
CLOSE = "</script>"

m = re.search(r"(\d{4})-(\d{2})-(\d{2})\.tsv$", src)
if not m:
    sys.exit("ERRO: o nome do TSV precisa terminar em AAAA-MM-DD.tsv (data da extração)")
date = f"{m[3]}/{m[2]}/{m[1]}"

data = open(src, encoding="utf-8").read().strip()
if "</" in data:
    sys.exit("ERRO: o TSV contém '</', o que quebraria a tag <script>")

html = open(page, encoding="utf-8").read()
start = html.index(OPEN) + len(OPEN)
end = html.index(CLOSE, start)
html = html[:start] + "\n" + data + "\n" + html[end:]
html, n = re.subn(r'(class="data-extracao">)[^<]*', rf"\g<1>{date}", html)
if n == 0:
    sys.exit("ERRO: nenhum elemento class=\"data-extracao\" encontrado na página")
open(page, "w", encoding="utf-8").write(html)
print(f"OK: {data.count(chr(10))} linhas de {src} embutidas em {page}; data de extração {date} ({n} lugares)")
