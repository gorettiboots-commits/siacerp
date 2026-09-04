"""
Verificar estado del proyecto Supabase.
"""
import json
import urllib.request
import urllib.error

url = 'https://makeccmgamhumiktuhxh.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ha2VjY21nYW1odW1pa3R1aHhoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY2NzE5NDQsImV4cCI6MjEwMjI0Nzk0NH0.1FNnNidBK_WGzqcFd95p_XgxYj26z-E2fY59bs4JXT8'

print("Verificando estado de Supabase...")
print(f"URL: {url}\n")

endpoints = [
    ("Auth Settings", "/auth/v1/settings"),
    ("Auth Health", "/auth/v1/health"),
    ("REST v1", "/rest/v1/"),
]

for name, path in endpoints:
    try:
        req = urllib.request.Request(f"{url}{path}")
        req.add_header("apikey", key)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("utf-8")[:100]
            print(f"[OK] {name}: {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:100]
        print(f"[{e.code}] {name}: {body}")
    except Exception as e:
        print(f"[ERR] {name}: {e}")

print("\nSi ves errores 502/521, el proyecto esta PAUSADO.")
print("Ve a https://supabase.com/dashboard y reactiva el proyecto.")
