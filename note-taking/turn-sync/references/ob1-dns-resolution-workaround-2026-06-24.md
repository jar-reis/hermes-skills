# OB1 DNS Resolution Workaround (2026-06-24)

## Problem

On macOS with Tailscale active, the system DNS resolver (used by Python's
`socket.getaddrinfo()` and `curl`) fails to resolve the OB1 Supabase subdomain
`jhpuctiyosazlyrcnfuu.supabase.co`, even though `dig` and `nslookup` resolve it
fine via the same DNS servers.

## Symptoms

- `ob1-pull --recent` returns: `ERROR: <urlopen error [Errno 8] nodename nor servname provided, or not known>`
- `curl https://jhpuctiyosazlyrcnfuu.supabase.co/` returns: `Could not resolve host`
- `python3 -c "import socket; socket.getaddrinfo('jhpuctiyosazlyrcnfuu.supabase.co', 443)"` raises `socket.gaierror`
- `dig jhpuctiyosazlyrcnfuu.supabase.co +short` works fine (returns 104.18.38.10, 172.64.149.246)
- `nslookup jhpuctiyosazlyrcnfuu.supabase.co 100.100.100.100` works fine
- `nslookup jhpuctiyosazlyrcnfuu.supabase.co 192.168.4.1` works fine

## Root Cause

Tailscale's MagicDNS resolver (100.100.100.100) is the primary system resolver
(check `scutil --dns`). It handles Tailscale domain resolution but interferes
with certain external subdomains. The `dig` and `nslookup` tools have their own
resolver implementations that bypass the system resolver, which is why they work.

## Fix Applied

Patched `~/Documents/=notes/bin/ob1-pull` with a `socket.getaddrinfo` monkeypatch
that falls back to resolved IPs (104.18.38.10, 172.64.149.246) when the system
resolver fails for this specific domain:

```python
import socket

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

## Alternative Fixes

1. **Add /etc/hosts entry** (requires sudo):
   ```
   echo "104.18.38.10 jhpuctiyosazlyrcnfuu.supabase.co" | sudo tee -a /etc/hosts
   ```
   This is the most durable fix but requires manual sudo access.

2. **Flush DNS cache** (may be temporary):
   ```bash
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```
   This did NOT fix the issue on 2026-06-24, but may help in other cases.

3. **Use curl --resolve** for one-off calls:
   ```bash
   curl --resolve "jhpuctiyosazlyrcnfuu.supabase.co:443:104.18.38.10" https://jhpuctiyosazlyrcnfuu.supabase.co/...
   ```

## Verification

After patching:
```bash
source ~/.hermes/.env
python3 ~/Documents/=notes/bin/ob1-pull --recent --limit 3
# Should return recent thoughts without DNS errors
```

## Scope

Only `jhpuctiyosazlyrcnfuu.supabase.co` is affected. Other external domains
(google.com, github.com, cloudflare.com, supabase.co itself) resolve fine.
This suggests a Tailscale MagicDNS bug with specific long subdomains, not a
general DNS failure.