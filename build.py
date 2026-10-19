"""Embute o TSV de seções alteradas no index.html (página autocontida).

Uso: python build.py [entrada.tsv] [index.html]
"""
import sys

src = sys.argv[1] if len(sys.argv) > 1 else "secoes_alteradas_2turno.tsv"
page = sys.argv[2] if len(sys.argv) > 2 else "index.html"
OPEN = '<script id="dados" type="text/tab-separated-values">'
CLOSE = "</script>"

data = open(src, encoding="utf-8").read().strip()
if "</" in data:
    sys.exit("ERRO: o TSV contém '</', o que quebraria a tag <script>")

html = open(page, encoding="utf-8").read()
start = html.index(OPEN) + len(OPEN)
end = html.index(CLOSE, start)
html = html[:start] + "\n" + data + "\n" + html[end:]
open(page, "w", encoding="utf-8").write(html)
print(f"OK: {data.count(chr(10))} linhas embutidas em {page}")
