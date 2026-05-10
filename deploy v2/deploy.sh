#!/bin/bash
# ══════════════════════════════════════════════════════════
# THAMMEN — Deployment Guide
# ══════════════════════════════════════════════════════════
#
# Prerequisites:
#   - Ubuntu 22.04+ VPS (DigitalOcean $12/month recommended)
#   - Domain: thammen.qa (register at Q-CERT ~200 QAR/year)
#   - Python 3.11+
#
# Total setup time: ~30 minutes
# ══════════════════════════════════════════════════════════

# ── Step 1: Server Setup ──
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx

# ── Step 2: Create project directory ──
sudo mkdir -p /opt/thammen
sudo chown $USER:$USER /opt/thammen
cd /opt/thammen

# ── Step 3: Upload files ──
# Upload thammen_launch_v1.zip to server, then:
# unzip thammen_launch_v1.zip

# ── Step 4: Python environment ──
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn[standard] pillow

# ── Step 5: Download MoJ data and build database ──
curl -o moj_weekly.csv \
  "https://www.data.gov.qa/api/explore/v2.1/catalog/datasets/weekly-real-estates-sales-bulletin/exports/csv?lang=ar&timezone=Asia/Qatar&use_labels=true&delimiter=,"

python3 moj_db.py init moj_weekly.csv
python3 calibrate_construction_cost.py moj_weekly.db

# ── Step 6: Test API locally ──
python3 api.py &
sleep 3
curl -s http://localhost:8000/api/health
curl -s -X POST http://localhost:8000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"zone":56,"street":784,"building":2}' | python3 -m json.tool
kill %1

# ── Step 7: Create systemd service ──
sudo tee /etc/systemd/system/thammen.service << 'EOF'
[Unit]
Description=Thammen API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/thammen
ExecStart=/opt/thammen/venv/bin/uvicorn api:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
Environment=PYTHONPATH=/opt/thammen

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable thammen
sudo systemctl start thammen

# ── Step 8: Nginx reverse proxy ──
sudo tee /etc/nginx/sites-available/thammen << 'EOF'
server {
    listen 80;
    server_name thammen.qa www.thammen.qa;

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 30s;
    }

    # Frontend (React build)
    location / {
        root /opt/thammen/frontend/build;
        try_files $uri $uri/ /index.html;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/thammen /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# ── Step 9: SSL Certificate ──
sudo certbot --nginx -d thammen.qa -d www.thammen.qa

# ── Step 10: Weekly MoJ update (cron) ──
(crontab -l 2>/dev/null; echo "0 6 * * 0 /opt/thammen/update_moj.sh /opt/thammen") | crontab -

# ══════════════════════════════════════════════════════════
# DONE! Visit https://thammen.qa
# ══════════════════════════════════════════════════════════

echo "
✅ Thammen is live!

API:      https://thammen.qa/api/health
Evaluate: curl -X POST https://thammen.qa/api/evaluate \\
            -H 'Content-Type: application/json' \\
            -d '{\"zone\":56,\"street\":784,\"building\":2}'
"
