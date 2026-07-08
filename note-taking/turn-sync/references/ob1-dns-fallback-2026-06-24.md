# OB1 DNS Resolution Fallback (2026-06-24)

## Problem

The macOS system resolver (used by Python `socket.getaddrinfo` and `curl`)
cannot resolve `jhpuctiyosazlyrcnfuu.supabase.co` — the OB1 Supabase edge
function host. This occurs even though `dig` and `nslookup` resolve the
domain fine (returning IPs 104.18.38.10 and 172.64.149.246).

## Symptoms

```
# Python
socket.gaierror: [Errno 8] nodename nor servname provided, or not known

# curl
curl: (6) Could not resolve host: jhpuctiyosazlyrcnfuu.supabase.co

# ob1-pull
ERROR: <urlopen error [Errno 8] nodename nor servname provided, or not known>
```

## Root Cause

Tailscale MagicDNS (`100.100.100.100` as primary resolver) interferes with
resolution of specific external subdomains. The Tailscale resolver handles
`.ts.net` domains and common domains (google.com, github.com) correctly, but
certain Cloudflare-fronted subdomains like `jhpuctiyosazlyrcnfuu.supabase.co`
return NXDOMAIN through the system resolver while `dig`/`nslookup` (which use
their own resolution path) succeed.

## Verification

```bash
# System resolver (FAILS)
python3 -c "import socket; print(socket.getaddrinfo('jhpuctiyosazlyrcnfuu.supabase.co', 443, socket.AF_INET))"

# dig (WORKS)
dig jhpuctiyosazlyrcnfuu.supabase.co +short
# → 104.18.38.10, 172.64.149.246

# nslookup (WORKS)
nslookup jhpuctiyosazlyrcnfuu.supabase.co 100.100.100.100
# → 172.64.149.246, 104.18.38.10

# Other domains (WORKS — only this specific subdomain is affected)
python3 -c "import socket; print(socket.getaddrinfo('supabase.co', 443, socket.AF_INET))"
# → OK (76.76.21.21)
```

## Fix

Patched `~/Documents/=notes/bin/ob1-pull` with a `socket.getaddrinfo` monkeypatch
that falls back to resolved IPs when the system resolver fails for the OB1 host:

```python
OB1_HOST = "jhpuctiyosazlyrcnfuu.supabase.co"
OB1_FALLBACK_IPS = ["104.18.38.10", "172.64.149.246"]

_original_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == OB1_HOST:
        try:
            return _original_getaddrinfo(host, port, *args, **kwargs)
        except socket.gaierror:
            for ip in OB1_FALLBACK_IPS:
                try:
                    return _original_getaddrinfo(ip, port, *args, **kwargs)
                except socket.gaierror:
                    continue
    return _original_getaddrinfo(host, port, *args, **kwargs)

socket.getaddrinfo = _patched_getaddrinfo
```

## Verification After Fix

```bash
source ~/.hermes/.env
python3 ~/Documents/=notes/bin/ob1-pull --recent --limit 3
# Should return recent thoughts successfully
```

## Notes

- The fallback IPs are Cloudflare edge IPs and may change over time. If both
  fallback IPs fail, re-resolve with `dig jhpuctiyosazlyrcnfuu.supabase.co +short`
  and update `OB1_FALLBACK_IPS` in the script.
- Adding a `/etc/hosts` entry would also fix this system-wide but requires sudo
  and affects all applications. The script-level patch is more surgical.
- This issue may affect other Cloudflare-fronted Supabase subdomains on this
  machine. The patch is scoped to the OB1 host only to avoid unintended side
  effects.