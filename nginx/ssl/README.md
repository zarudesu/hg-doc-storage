# SSL Certificates Directory

This directory should contain your SSL certificates for HTTPS:

- `cert.pem` - SSL certificate (fullchain)
- `key.pem` - Private key

## For Let's Encrypt certificates:

```bash
# Install certbot
sudo apt install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d doc.healthgarden.ru

# Copy certificates
sudo cp /etc/letsencrypt/live/doc.healthgarden.ru/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/doc.healthgarden.ru/privkey.pem nginx/ssl/key.pem
sudo chown $USER:$USER nginx/ssl/*.pem
```

## For development/testing:

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/CN=doc.healthgarden.ru"
```

**Note:** Never commit actual SSL certificates to git!
