# Entelechy Docker Server Installation Guide

This guide outlines the steps to install and configure Entelechy using Docker and `systemd` for automatic startup, with Nginx as a reverse proxy for HTTPS access.

This approach encapsulates all dependencies within a Docker container, avoiding complex native library and PostgreSQL initialization issues experienced with direct host installations.

## 1. Prerequisites

Ensure your server has the following prerequisites:

*   **Docker:** Install Docker Engine on your server. Follow the official Docker documentation for your operating system (e.g., [Install Docker Engine on Debian](https://docs.docker.com/engine/install/debian/) or [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)).
    *   Ensure your user is in the `docker` group to run Docker commands without `sudo`. (You may need to log out and back in after adding yourself to the group): `sudo usermod -aG docker your_username`
*   **Nginx:** Install Nginx: `sudo apt update && sudo apt install nginx` (for Debian/Ubuntu)

## 2. Project Setup

1.  **Navigate to Project Directory:**
    ```bash
    cd /mnt/data/code/entelechy
    ```
2.  **Environment Variables:** Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
3.  **Edit `.env`:** Open the `.env` file and configure your LLM API key, model, and other settings. This file will be mounted directly into the Docker container.
    *   You can leave `ENTELECHY_API_DATABASE_URL` commented out/empty if you wish to use the embedded PostgreSQL managed within the Docker container.
    *   The API will listen on port `8888` and the Control Plane on `9999` within the container, mapped to the same ports on your host.

## 3. Entelechy Docker `systemd` Service

This service manages the Entelechy Docker container, ensuring it starts automatically and can be controlled via `systemctl`.

1.  **Create Service File:** Create a file named `entelechy-docker.service` in `/etc/systemd/system/` with the following content. **Remember to replace `your_username` with the user who is in the `docker` group.**

    ```ini
    [Unit]
    Description=Entelechy Docker Container Service
    After=docker.service
    Requires=docker.service

    [Service]
    User=your_username # User must be in the docker group
    Group=docker
    WorkingDirectory=/mnt/data/code/entelechy
    EnvironmentFile=/mnt/data/code/entelechy/.env
    ExecStartPre=/usr/bin/docker pull ghcr.io/vectorize-io/entelechy:latest
    ExecStart=/usr/bin/docker run 
        --rm 
        --name entelechy-container 
        -p 8888:8888 
        -p 9999:9999 
        -v /mnt/data/code/entelechy/.env:/app/.env 
        -v entelechy_data:/home/debian/.pg0 
        --env-file /mnt/data/code/entelechy/.env 
        ghcr.io/vectorize-io/entelechy:latest
    ExecStop=/usr/bin/docker stop entelechy-container
    ExecStopPost=/usr/bin/docker rm entelechy-container
    Restart=on-failure
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

## 4. Nginx Configuration for HTTPS

This configures Nginx to serve `https://mindmods.org`, proxying requests to the Docker container's exposed ports.

1.  **Create Nginx Site Configuration:** Create a file named `mindmods.org.conf` in `/etc/nginx/sites-available/` with the following content. **You will need to replace the SSL certificate paths with your actual certificate locations (e.g., from Let's Encrypt).**

    ```nginx
    server {
        listen 80;
        listen [::]:80;
        server_name mindmods.org www.mindmods.org;

        # Redirect HTTP to HTTPS
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name mindmods.org www.mindmods.org;

        # SSL Configuration (Replace with your actual certificate paths)
        ssl_certificate /etc/letsencrypt/live/mindmods.org/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/mindmods.org/privkey.pem;
        ssl_trusted_certificate /etc/letsencrypt/live/mindmods.org/chain.pem;

        # Recommended SSL settings (adjust as needed)
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:10m;
        ssl_session_tickets off;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20';
        ssl_prefer_server_ciphers off;
        ssl_stapling on;
        ssl_stapling_verify on;
        add_header Strict-Transport-Security "max-age=63072000" always;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header X-Frame-Options DENY;

        # Proxy to Entelechy API for /mcp endpoint
        location /mcp/ {
            proxy_pass http://localhost:8888;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            # Websocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Proxy to Entelechy Control Plane for all other requests
        location / {
            proxy_pass http://localhost:9999;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            # Websocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
    ```

## 5. Integrating and Enabling All Services

1.  **Reload `systemd`:** Inform `systemd` about the new service file:
    ```bash
    sudo systemctl daemon-reload
    ```

2.  **Enable and Start Entelechy Docker Service:**
    ```bash
    sudo systemctl enable entelechy-docker.service
    sudo systemctl start entelechy-docker.service
    ```

3.  **Verify Entelechy Service Status:** Check if the service is running correctly:
    ```bash
    systemctl status entelechy-docker.service
    ```
    Look for `Active: active (running)`. If there are issues, use `journalctl -u entelechy-docker.service --no-pager` to inspect logs.

4.  **Activate Nginx Site:**
    *   **Create Symlink:**
        ```bash
        sudo ln -s /etc/nginx/sites-available/mindmods.org.conf /etc/nginx/sites-enabled/
        ```
    *   **Test Nginx Configuration:**
        ```bash
        sudo nginx -t
        ```
        Address any errors reported.
    *   **Reload Nginx:**
        ```bash
        sudo systemctl reload nginx
        ```

5.  **Configure SSL Certificates (Recommended: Certbot):**
    *   The Nginx configuration assumes SSL certificates are managed (e.g., by Certbot) and located in `/etc/letsencrypt/live/mindmods.org/`.
    *   **Install Certbot (if not already installed):**
        ```bash
        sudo snap install core; sudo snap refresh core
        sudo snap install --classic certbot
        sudo ln -s /snap/bin/certbot /usr/bin/certbot
        ```
    *   **Obtain and Configure Certificates:** Run Certbot to obtain free SSL certificates from Let's Encrypt and automatically configure Nginx for your domain:
        ```bash
        sudo certbot --nginx -d mindmods.org -d www.mindmods.org
        ```
        Follow the prompts. Certbot will automatically adjust your Nginx configuration for SSL and set up automatic renewals.

---