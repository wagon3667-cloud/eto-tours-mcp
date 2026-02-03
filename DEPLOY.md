# Deploy (Ubuntu 22.04)

Ниже минимальный боевой деплой на VM. Поднимаем:
- HTTP API на `:8080`
- MCP по HTTP/SSE на `:8081`

## 1. Установка

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git

# исходники
git clone <YOUR_REPO_URL> eto-tours-mcp
cd eto-tours-mcp

# venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 2. .env (не коммитим)

Создай `.env` рядом с кодом:
```
MODSEARCH_URL=https://tourvisor.ru/xml/modsearch.php
MODRESULT_URL=https://search3.tourvisor.ru/modresult.php
LISTDEV_URL=https://tourvisor.ru/xml/listdev.php
LISTCOUNTRY_URL=https://tourvisor.ru/xml/listcountry.php
LISTDEP_URL=https://tourvisor.ru/xml/listdep.php
LISTMEAL_URL=https://tourvisor.ru/xml/listmeal.php
LISTROOM_URL=https://tourvisor.ru/xml/listroom.php
LISTOPERATOR_URL=https://tourvisor.ru/xml/listoperator.php

DEFAULT_SESSION=...
DEFAULT_REFERRER=...
ETO_HEADERS_JSON={"Cookie":"tv-user-id=...; tv-session-id=...","Referer":"https://tourvisor.ru/"}
```

## 3. systemd сервисы

`/etc/systemd/system/eto-tours-api.service`
```
[Unit]
Description=eto-tours API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/eto-tours-mcp
EnvironmentFile=/opt/eto-tours-mcp/.env
ExecStart=/opt/eto-tours-mcp/.venv/bin/uvicorn api:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/eto-tours-mcp-http.service`
```
[Unit]
Description=eto-tours MCP HTTP/SSE
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/eto-tours-mcp
EnvironmentFile=/opt/eto-tours-mcp/.env
ExecStart=/opt/eto-tours-mcp/.venv/bin/python mcp_http.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Активировать:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now eto-tours-api eto-tours-mcp-http
sudo systemctl status eto-tours-api eto-tours-mcp-http
```

## 4. Порты

Если включен UFW:
```bash
sudo ufw allow 8080
sudo ufw allow 8081
```

## 5. Проверка

```bash
curl http://127.0.0.1:8080/health
curl -X POST http://127.0.0.1:8080/search_tours \
  -H 'Content-Type: application/json' \
  -d '{"country":"Египет","city_from":"Москва","date_from":"2026-03-01","date_to":"2026-03-31","nights":10,"adults":2}'
```

## 6. Обновление

```bash
cd /opt/eto-tours-mcp
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart eto-tours-api eto-tours-mcp-http
```
