# TLS Setup — physicsforge.toolchant.com

This document covers the one-time certificate bootstrap and ongoing renewal
for the production deployment. Certificates are issued by Let's Encrypt via
certbot's webroot method.

## Prerequisites

- The server's public IP is pointed at `physicsforge.toolchant.com` in DNS
  and the record has propagated.
- Ports 80 and 443 are open in the firewall / security group.
- Docker and Docker Compose are installed on the host.
- The repo is checked out and `.env` is populated.

---

## Step 1 — Start the stack without ssl.conf

The nginx container will fail to start if `ssl.conf` references a certificate
that does not exist yet. Temporarily move it aside so nginx starts with the
HTTP-only config:

```bash
mv nginx/conf.d/ssl.conf nginx/conf.d/ssl.conf.disabled
```

Start only the services nginx needs to serve the ACME challenge:

```bash
docker compose up -d postgres api frontend nginx
```

Confirm nginx is serving on port 80:

```bash
curl -I http://physicsforge.toolchant.com/
# Expected: 301 redirect (the / → HTTPS redirect in default.conf)
```

---

## Step 2 — Issue the certificate

Run certbot once in standalone webroot mode against the running nginx:

```bash
docker compose run --rm certbot \
  certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --email admin@toolchant.com \
    --agree-tos \
    --no-eff-email \
    -d physicsforge.toolchant.com
```

On success certbot writes the certificate into the `letsencrypt` named volume
at `/etc/letsencrypt/live/physicsforge.toolchant.com/`.

---

## Step 3 — Enable the HTTPS config and reload

Restore `ssl.conf` and reload nginx to start serving HTTPS:

```bash
mv nginx/conf.d/ssl.conf.disabled nginx/conf.d/ssl.conf
docker compose exec nginx nginx -s reload
```

Verify:

```bash
curl -I https://physicsforge.toolchant.com/
# Expected: 200 OK (or 304) with strict-transport-security header
```

---

## Step 4 — Start the certbot renewal service

The certbot service in the compose file runs a renewal loop every 12 hours.
Start it alongside the rest of the stack:

```bash
docker compose up -d certbot
```

nginx reloads every 6 hours (built into its compose command) to pick up any
newly renewed certificate without manual intervention.

---

## Normal startup (after first-run bootstrap)

Once the certificate exists in the `letsencrypt` volume, the full stack starts
cleanly with a single command:

```bash
docker compose up -d
```

---

## Certificate renewal mechanics

| Component | What it does |
|-----------|-------------|
| `certbot` container | Calls `certbot renew` every 12 hours; writes renewed cert to `letsencrypt` volume |
| `nginx` container | Calls `nginx -s reload` every 6 hours; picks up the new cert without downtime |
| `certbot_webroot` volume | Shared between certbot (write) and nginx (read) for ACME `/.well-known/acme-challenge/` files |
| `letsencrypt` volume | Shared between certbot (write) and nginx (read) for certificate files |

Let's Encrypt certificates are valid for 90 days; certbot only renews when
fewer than 30 days remain, so most renewal attempts are no-ops.

---

## Troubleshooting

**nginx fails to start with "cannot load certificate"**
The `letsencrypt` volume is empty — go back to Step 1 and issue the cert first.

**certbot says "domain not reachable"**
Check that port 80 is open, DNS has propagated, and the nginx container is
running (`docker compose ps`).

**Certificate renewed but nginx still serving the old one**
Force a reload: `docker compose exec nginx nginx -s reload`

**Check certificate expiry**
```bash
docker compose exec nginx \
  openssl x509 -in /etc/letsencrypt/live/physicsforge.toolchant.com/fullchain.pem \
  -noout -dates
```
