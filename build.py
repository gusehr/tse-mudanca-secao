"""Embute o TSV de seções alteradas no index.html (página autocontida).

Sem argumentos, usa a extração mais recente (secoes_alteradas_2turno_AAAA-MM-DD_HHMM.tsv),
atualiza a data e hora de extração exibidas na página e embute os municípios que constavam
em extrações anteriores mas não na escolhida (para links antigos explicarem a saída).

Uso: python build.py [entrada.tsv] [index.html]
"""
import glob, re, sys

PATTERN = "secoes_alteradas_2turno_????-??-??_????.tsv"
CLOSE = "</script>"

def stamp(path):
    """(AAAA, MM, DD, HH, MM) a partir do nome do arquivo, ou None."""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})\.tsv$", path)
    return m and m.groups()

def br_datetime(path):
    y, mo, d, h, mi = stamp(path)
    return f"{d}/{mo}/{y} às {h}:{mi}"

def cities(path):
    with open(path, encoding="utf-8") as f:
        next(f)
        return {tuple(line.split("\t")[1:3]) for line in f if line.strip()}

def embed(html, tag_id, content):
    open_tag = f'<script id="{tag_id}" type="text/tab-separated-values">'
    start = html.index(open_tag) + len(open_tag)
    end = html.index(CLOSE, start)
    return html[:start] + "\n" + content + "\n" + html[end:]

src = sys.argv[1] if len(sys.argv) > 1 else max(glob.glob(PATTERN), key=stamp)
page = sys.argv[2] if len(sys.argv) > 2 else "index.html"
if not stamp(src):
    sys.exit("ERRO: o nome do TSV precisa terminar em AAAA-MM-DD_HHMM.tsv (data e hora da extração)")
when = br_datetime(src)

data = open(src, encoding="utf-8").read().strip()
if "</" in data:
    sys.exit("ERRO: o TSV contém '</', o que quebraria a tag <script>")

# municípios de extrações anteriores ausentes na atual, com a última extração em que apareceram
current = cities(src)
last_seen = {}
for old in sorted((p for p in glob.glob(PATTERN) if stamp(p) < stamp(src)), key=stamp):
    for c in cities(old) - current:
        last_seen[c] = br_datetime(old)
removed = "UF\tMunicípio\tÚltima extração\n" + "\n".join(f"{uf}\t{mun}\t{d}" for (uf, mun), d in sorted(last_seen.items()))

html = open(page, encoding="utf-8").read()
html = embed(html, "dados", data)
html = embed(html, "anteriores", removed)
html, n = re.subn(r'(class="data-extracao">)[^<]*', rf"\g<1>{when}", html)
if n == 0:
    sys.exit("ERRO: nenhum elemento class=\"data-extracao\" encontrado na página")
open(page, "w", encoding="utf-8").write(html)
print(f"OK: {data.count(chr(10))} linhas de {src} embutidas em {page}; extração de {when} ({n} lugares); {len(last_seen)} municípios só em extrações anteriores")
