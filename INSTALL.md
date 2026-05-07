# Installation Guide for AideBot

This document provides step‑by‑step instructions for deploying AideBot on a VPS (Ubuntu 24.04), configuring the domain for the API, and embedding the web widget into your website.

## Table of Contents

- [Prerequisites](#prerequisites)
- [1. Server Preparation](#1-server-preparation)
- [2. DNS Configuration](#2-dns-configuration)
- [3. Deploying the Bot](#3-deploying-the-bot)
- [4. Running the Bot as a System Service](#4-running-the-bot-as-a-system-service)
- [5. Setting up Nginx as a Reverse Proxy with SSL](#5-setting-up-nginx-as-a-reverse-proxy-with-ssl)
- [6. Configuring CORS](#6-configuring-cors)
- [7. Embedding the Widget](#7-embedding-the-widget)
- [8. Verification](#8-verification)
- [Managing the Bot](#managing-the-bot)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- A VPS with **Ubuntu 24.04** (or similar) and root access.
- A domain name pointing to your server (you will create a subdomain for the API, e.g. `api.your-site.com`).
- Your website where the widget will be embedded must use **HTTPS** (otherwise modern browsers may block mixed content).
- GigaChat API credentials (or another LLM provider).
- Telegram bot token and/or MAX bot token if you use those messengers.

---

## 1. Server Preparation

Connect to your server as `root`:

```bash
ssh root@your-server-ip
```

### Create a non‑root user (recommended)

```bash
adduser your-username
usermod -aG sudo your-username
```

Switch to the new user:

```bash
su - your-username
```

### Update system and install required packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx
```

---

## 2. DNS Configuration

In your domain’s DNS management panel (e.g., ISPmanager, Cloudflare, etc.), create an **A record** for a subdomain that will serve the API. For example:

| Name               | Type | Value          |
|--------------------|------|----------------|
| `api.your-site.com`| A    | `your-server-ip` |

Wait a few minutes for the DNS changes to propagate.

---

## 3. Deploying the Bot

Clone the repository and set up the Python environment.

```bash
git clone https://github.com/evbkv/aidebot.git
cd aidebot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure the bot

Copy the example configuration (if available) or edit `config.py` directly:

```bash
nano config.py
```

Set at least the following values:

- `GIGACHAT_CREDENTIALS` – your GigaChat API key.
- `TELEGRAM_BOT_TOKEN` – if you use Telegram.
- `MAX_BOT_TOKEN` – if you use MAX.
- `WEB_HOST = "0.0.0.0"` – so Flask listens on all interfaces.
- `WEB_PORT = 5000` (default, can be changed).
- `WEB_ALLOWED_ORIGINS` – you will add your website’s domain later.

Save the file.

### Test the bot manually

```bash
python main.py
```

You should see logs indicating that the web server started and Telegram/MAX polling began. Press `Ctrl+C` to stop it.

---

## 4. Running the Bot as a System Service

To keep the bot running after you log out, create a systemd service.

Create the service file:

```bash
sudo nano /etc/systemd/system/aidebot.service
```

Paste the following (adjust the paths and username):

```ini
[Unit]
Description=AideBot Service
After=network.target

[Service]
User=your-username
Group=your-username
WorkingDirectory=/home/your-username/aidebot
ExecStart=/home/your-username/aidebot/venv/bin/python /home/your-username/aidebot/main.py
Restart=always
RestartSec=10
Environment="PATH=/home/your-username/aidebot/venv/bin"

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable aidebot
sudo systemctl start aidebot
```

Check its status:

```bash
sudo systemctl status aidebot
```

View logs in real time:

```bash
journalctl -u aidebot -f
```

---

## 5. Setting up Nginx as a Reverse Proxy with SSL

We will use nginx to proxy requests from your subdomain to the local Flask instance and obtain a free SSL certificate via Let’s Encrypt.

### Create an nginx configuration for your subdomain

```bash
sudo nano /etc/nginx/sites-available/api.your-site.com
```

Paste the initial (HTTP) configuration:

```nginx
server {
    listen 80;
    server_name api.your-site.com;

    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/api.your-site.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Obtain an SSL certificate with Certbot

```bash
sudo certbot --nginx -d api.your-site.com
```

Follow the interactive prompts:

- Enter your email address.
- Agree to the terms.
- Choose whether to redirect HTTP to HTTPS (recommended: **2**).

Certbot will modify your nginx configuration to serve HTTPS and set up automatic renewal.

Verify that HTTPS works:

```bash
curl -I https://api.your-site.com/api/start
```

You should receive a `405 Method Not Allowed` response – this is normal because the endpoint expects `POST`/`OPTIONS`.

---

## 6. Configuring CORS

Edit the bot’s configuration file again:

```bash
nano /home/your-username/aidebot/config.py
```

Add your website’s origin (the site where the widget will be embedded) to `WEB_ALLOWED_ORIGINS`. For example:

```python
WEB_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "https://your-site.com",          # your main site
    "https://api.your-site.com",       # optional
    "null"
]
```

Save and restart the bot:

```bash
sudo systemctl restart aidebot
```

---

## 7. Embedding the Widget

### Option A: Using a customised script

If you have the `aidebot-widget.js` file locally, you can set the default API base inside it. Open the file and locate the `DEFAULT_CONFIG` object:

```javascript
const DEFAULT_CONFIG = {
    apiBase: 'https://api.your-site.com/api',
    autoOpenDelay: 5000,
    healthCheckInterval: 30000,
};
```

Then upload the file to your website (e.g., to `https://your-site.com/js/aidebot-widget.js`).

### Option B: Using data attributes (recommended for flexibility)

Include the script on your HTML page without modifying the file, and pass the configuration via `data-` attributes:

```html
<script src="https://your-site.com/path/to/aidebot-widget.js"
        data-api-base="https://api.your-site.com/api"
        data-auto-open-delay="5000"
        data-health-check-interval="30000"></script>
```

Make sure the script is placed **before the closing `</body>` tag** or where you want the widget to appear.

---

## 8. Verification

1. Open your website (e.g., `https://your-site.com`) in a browser.
2. Open the developer console (F12) and go to the **Network** tab.
3. Click the round icon to open the chat.
4. Enter a name and phone number, then click **Start**.
5. Send a test message.
6. Verify that requests are sent to `https://api.your-site.com/api/...` and that responses are returned without CORS errors.

If everything works, your AideBot is successfully deployed!

---

## Managing the Bot

- **Start**: `sudo systemctl start aidebot`
- **Stop**: `sudo systemctl stop aidebot`
- **Restart**: `sudo systemctl restart aidebot`
- **Status**: `sudo systemctl status aidebot`
- **Logs**: `journalctl -u aidebot -f`
- **Disable autostart**: `sudo systemctl disable aidebot`
- **Enable autostart**: `sudo systemctl enable aidebot`

---

## Troubleshooting

### 502 Bad Gateway from nginx

- Check that the bot is running: `sudo systemctl status aidebot`.
- Verify that Flask is listening on `127.0.0.1:5000`: `ss -tlnp | grep 5000`.
- Test locally: `curl http://127.0.0.1:5000/api/start -I`.
- Look at nginx error logs: `sudo tail -f /var/log/nginx/error.log`.

### CORS errors in the browser

- Ensure your website’s origin (e.g., `https://your-site.com`) is listed in `WEB_ALLOWED_ORIGINS`.
- Restart the bot after changing `config.py`.
- Check that the browser request includes the `Origin` header and the response includes `Access-Control-Allow-Origin`.

### Widget does not appear

- Verify that the script is correctly loaded (check Network tab).
- Ensure there is no JavaScript error in the console.
- If the server is unavailable, the icon becomes semi‑transparent and unclickable – check the health check logs.

### GigaChat errors

- Confirm that `GIGACHAT_CREDENTIALS` is up‑to‑date.
- Test the token with a separate script (see the main README).
- Update the `gigachat` library: `pip install --upgrade gigachat`.

---

For further assistance, please open an issue on the [GitHub repository](https://github.com/evbkv/aidebot).