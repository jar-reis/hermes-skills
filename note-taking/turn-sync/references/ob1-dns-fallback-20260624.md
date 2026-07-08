# OB1 DNS Fallback — Tailscale MagicDNS Interference

**Date:** 2026-06-24
**Problem:** macOS system resolver (Python `socket.getaddrinfo`, `curl`) cannot resolve `jhpuctiyosazlyrcnfuu.supabase.co` (OB1 Supabase edge function URL), even though `dig` and `nslookup` resolve it correctly to `104.18.38.10` and `172.64.149.246`.

## Root Cause

Tailscale's MagicDNS (`100.100.100.100` as primary DNS) interferes with resolution of specific external subdomains. The system resolver (used by Python's `socket.getaddrinfo` and `curl`) fails with `nodename nor servname provided, or not known`, while `dig` and `nslookup` (which use their own resolver) succeed.

This was NOT a Supabase outage — the edge function responded correctly when reached via IP with SNI. It was purely a DNS resolution issue.

## Symptoms

```
# dig resolves fine
dig jhpuctiyosazlyrcnfuu.supabase.co +short
→ 104.18.38.10
→ 172.64.149.246

# But Python and curl fail
python3 -c "import socket; socket.getaddrinfo('jhpuctiyosazlyrcnfuu.supabase.co', 443)"
→ socket.gaierror: [Errno 8] nodename nor servname provided, or not known

curl -v https://jhpuctiyosazlyrcnfuu.supabase.co/
→ Could not resolve host
```

## Fix Applied

Patched `~/Documents/=notes/bin/ob1-pull` with a `socket.getaddrinfo` fallback:

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

The patch tries the normal hostname first. Only if `gaierror` is raised does it fall back to the resolved IPs. This preserves SNI/Host headers (urllib uses the original URL for the Host header) while routing the TCP connection to the fallback IP.

## Verification

```bash
source ~/.hermes/.env 2>/dev/null
python3 ~/Documents/=notes/bin/ob1-pull --recent --limit 3
# Should return OB1 thoughts successfully
```

## Generalization

This pattern may affect other Supabase subdomains or Cloudflare-fronted services when Tailscale MagicDNS is active. If you see `nodename nor servname` for a domain that `dig` can resolve, apply the same `getaddrinfo` fallback pattern. The `/etc/hosts` approach requires sudo and is less portable; the Python monkey-patch is self-contained and survives across invocations of the script.