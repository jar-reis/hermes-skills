---created: 2026-06-24
updated: 2026-06-24
author: Hermes
---

# OB1 DNS Resolution Fallback

## Problem

The macOS system resolver (used by Python `socket.getaddrinfo`, `curl`, and most
applications) cannot resolve `jhpuctiyosazlyrcnfuu.supabase.co` (the OB1 Supabase
edge function URL). This causes OB1 captures and pulls to fail with:

```
ERROR: <urlopen error [Errno 8] nodename nor servname provided, or not known>
```

However, `dig` and `nslookup` resolve the domain fine:
```
$ nslookup jhpuctiyosazlyrcnfuu.supabase.co 100.100.100.100
Name: jhpuctiyosazlyrcnfuu.supabase.co
Address: 172.64.149.246
Address: 104.18.38.10
```

## Root Cause

Tailscale MagicDNS (100.100.100.100) interferes with resolution of specific
subdomains. The system resolver routes through Tailscale first, and certain
Cloudflare-fronted subdomains fail in the Tailscale DNS pipeline while
succeeding via standard DNS queries.

This is NOT a Tailscale-wide failure — `google.com`, `supabase.co` (apex),
and `github.com` all resolve fine. Only specific subdomains are affected.

## Fix

The `ob1-pull` script (`~/Documents/=notes/bin/ob1-pull`) is patched with a
`socket.getaddrinfo` fallback. When the system resolver fails for the OB1
host, it falls back to resolved IPs:

```python
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

## Verification

After patching, verify OB1 is reachable:
```bash
source ~/.hermes/.env
python3 ~/Documents/=notes/bin/ob1-pull --recent --limit 1
```

Should return recent thoughts instead of a DNS error.

## Diagnostic Commands

If OB1 is unreachable, check whether DNS is the issue:
```bash
# These work (use their own DNS resolution):
nslookup jhpuctiyosazlyrcnfuu.supabase.co
dig jhpuctiyosazlyrcnfuu.supabase.co +short

# This fails (uses system resolver):
python3 -c "import socket; socket.getaddrinfo('jhpuctiyosazlyrcnfuu.supabase.co', 443)"

# This also fails:
curl -v https://jhpuctiyosazlyrcnfuu.supabase.co/
```

If the pattern matches, the fallback patch handles it automatically.

## Generalization

This pattern applies to any Tailscale-affected subdomain. The same approach
can be used for other services that experience selective DNS failure:
1. Resolve the domain via `nslookup` or `dig`
2. Patch `socket.getaddrinfo` to fall back to the resolved IPs
3. The patch is transparent — if the system resolver works, it's used first

## IPs may change

Cloudflare-fronted IPs can change. If the fallback IPs stop working, re-resolve:
```bash
nslookup jhpuctiyosazlyrcnfuu.supabase.co 100.100.100.100
```
And update `OB1_FALLBACK_IPS` in the `ob1-pull` script.