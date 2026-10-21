"""Export real ZAP passive results; redact ephemeral authentication material."""
import collections
import json
import pathlib
import re
import time
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'zap'
OUT.mkdir(parents=True, exist_ok=True)

def fetch(path):
    request = urllib.request.Request('http://127.0.0.1:8090/' + path, headers={'Host': 'zap'})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode('utf-8')

def redact(text):
    text = re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[REDACTED_JWT]', text)
    return re.sub(r'Lab![0-9a-f-]{36}', '[REDACTED_PASSWORD]', text)

deadline = time.monotonic() + 120
while int(json.loads(fetch('JSON/pscan/view/recordsToScan/'))['recordsToScan']):
    if time.monotonic() >= deadline:
        raise RuntimeError('ZAP passive queue did not finish within 120 seconds')
    time.sleep(1)
version = json.loads(fetch('JSON/core/view/version/'))['version']
alerts = json.loads(redact(fetch('JSON/core/view/alerts/?baseurl=http%3A%2F%2Fjuice-shop%3A3000')))
native = redact(fetch('OTHER/core/other/htmlreport/'))
(OUT / 'zap-report.html').write_text(native, encoding='utf-8')
(OUT / 'zap-alerts.json').write_text(json.dumps(alerts, indent=2, ensure_ascii=False), encoding='utf-8')
grouped = collections.Counter((a['risk'], a['alert'], a['pluginId']) for a in alerts['alerts'])
summary = {
    'generatedAt': datetime.now(timezone.utc).isoformat(), 'version': version,
    'mode': 'Passive analysis of TC-BL-001 HTTP traffic; no spider or active scan',
    'target': 'http://juice-shop:3000', 'recordsToScan': 0,
    'instanceCount': len(alerts['alerts']),
    'groups': [dict(risk=r, alert=a, pluginId=p, instances=n) for (r, a, p), n in grouped.items()],
    'redaction': 'Ephemeral JWT and Lab! passwords removed from exported reports'
}
(ROOT / 'evidence' / 'zap-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2))
