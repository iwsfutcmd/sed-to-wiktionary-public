"""Fill site/template.html with data/intermediate/sed_all.json -> site/index.html (self-contained)."""
import json
from paths import SITE, INTER
data = json.loads((INTER / "sed_all.json").read_text(encoding="utf-8"))
t = (SITE / "template.html").read_text(encoding="utf-8")
(SITE / "index.html").write_text(t.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
print(len(data), "entries")
