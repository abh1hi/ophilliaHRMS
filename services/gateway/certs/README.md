# SSL Certificates

Place your SSL certificate files here:
- `server.crt` — SSL certificate
- `server.key` — SSL private key

## Generate self-signed certs for development

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout server.key -out server.crt \
  -subj "/C=IN/ST=Local/L=Local/O=OphilliaHRMS/CN=localhost"
```

## Enable HTTPS

1. Generate or obtain certs and place them in this directory
2. In `nginx/nginx.conf`, uncomment the SSL lines in the server block
3. Optionally uncomment the HTTP→HTTPS redirect block
4. Restart the gateway: `docker compose restart gateway`
