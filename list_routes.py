from app.main import app
import json

routes = []
for r in app.routes:
    if hasattr(r, 'path'):
        methods = list(getattr(r, 'methods', []))
        routes.append({'path': r.path, 'methods': methods, 'name': getattr(r, 'name', '')})

print(f"Total routes: {len(routes)}")
for r in sorted(routes, key=lambda x: x['path']):
    if r['methods']:
        print(f"{','.join(r['methods']):12} {r['path']}")
    else:
        print(f"MOUNT        {r['path']}")
