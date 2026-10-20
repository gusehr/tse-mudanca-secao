"""Embute o TSV de seções alteradas no index.html (página autocontida).

Sem argumentos, usa a extração mais recente (secoes_alteradas_2turno_AAAA-MM-DD.tsv),
atualiza a data de extração exibida na página e embute os municípios que constavam
em extrações anteriores mas não na escolhida (para links antigos explicarem a saída).

Uso: python build.py [entrada.tsv] [index.html]
"""
import glob, re, sys

PATTERN = "secoes_alteradas_2turno_????-??-??.tsv"
src = sys.argv[1] if len(sys.argv) > 1 else max(glob.glob(PATTERN))
page = sys.argv[2] if len(sys.argv) > 2 else "index.html"
CLOSE = "</script>"

def br_date(path):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})\.tsv$", path)
    return m and f"{m[3]}/{m[2]}/{m[1]}"

def cities(path):
    with open(path, encoding="utf-8") as f:
        next(f)
        return {tuple(line.split("\t")[1:3]) for line in f if line.strip()}

def embed(html, tag_id, content):
    open_tag = f'<script id="{tag_id}" type="text/tab-separated-values">'
    start = html.index(open_tag) + len(open_tag)
    end = html.index(CLOSE, start)
    return html[:start] + "\n" + content + "\n" + html[end:]

date = br_date(src)
if not date:
    sys.exit("ERRO: o nome do TSV precisa terminar em AAAA-MM-DD.tsv (data da extração)")

data = open(src, encoding="utf-8").read().strip()
if "</" in data:
    sys.exit("ERRO: o TSV contém '</', o que quebraria a tag <script>")

# municípios de extrações anteriores ausentes na atual, com a última data em que apareceram
current = cities(src)
last_seen = {}
for old in sorted(p for p in glob.glob(PATTERN) if p[-14:] < src[-14:]):
    for c in cities(old) - current:
        last_seen[c] = br_date(old)
removed = "UF\tMunicípio\tÚltima extração\n" + "\n".join(f"{uf}\t{mun}\t{d}" for (uf, mun), d in sorted(last_seen.items()))

html = open(page, encoding="utf-8").read()
html = embed(html, "dados", data)
html = embed(html, "anteriores", removed)
html, n = re.subn(r'(class="data-extracao">)[^<]*', rf"\g<1>{date}", html)
if n == 0:
    sys.exit("ERRO: nenhum elemento class=\"data-extracao\" encontrado na página")
open(page, "w", encoding="utf-8").write(html)
print(f"OK: {data.count(chr(10))} linhas de {src} embutidas em {page}; data de extração {date} ({n} lugares); {len(last_seen)} municípios só em extrações anteriores")
