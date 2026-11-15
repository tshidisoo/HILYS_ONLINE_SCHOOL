# First server setup: HILYS ecosystem

This sets up the HILYS management system on a new Linux server: the API, reminders, the staff app, the teacher portal and the parent app's web version. The public website stays on Firebase; at the end its enquiry form is pointed at the new API.

Paste each block into the server's terminal, top to bottom. After each block, compare what you see with **You should see**. **If you see anything else, stop and send the output.**

## Before you start, you need

1. **A server** running Ubuntu 24.04, with at least 2 GB of memory, and its IP address.
2. **A domain**, for example `hilys.com`, with these DNS records pointing at the server's IP address: `api`, `admin`, `teachers`, `app`. (The website itself stays on Firebase.)
3. **An email address** for HTTPS certificate notices.
4. **The GitHub repository** `tshidisoo/HILYS_ONLINE_SCHOOL`, with the `ecosystem` work merged into a `live` branch.

Sign in to the server as root: `ssh root@YOUR-SERVER-IP`.

## Block 1: your values (typed once)

Change the three values in quotes, then paste the block. Every later block uses them.

```bash
cat > /root/hilys-vars.sh <<'VARS'
export DOMAIN="hilys.com"
export ADMIN_EMAIL="you@example.com"
export WEBSITE="https://hilys-languages.web.app"
VARS
. /root/hilys-vars.sh
echo "Domain is $DOMAIN, website is $WEBSITE"
```

**You should see:** `Domain is hilys.com, website is https://hilys-languages.web.app` (with your values).

If the terminal is ever closed, run `. /root/hilys-vars.sh` again before the next block.

## Block 2: system packages

```bash
apt-get update && apt-get install -y python3 python3-venv python3-dev build-essential git nginx postgresql redis-server \
  certbot python3-certbot-nginx libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b fonts-dejavu-core curl
curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs
node --version && psql --version && redis-cli ping
```

**You should see:** a Node version starting `v22`, `psql (PostgreSQL) 16`, and `PONG`.

## Block 3: database and user

```bash
. /root/hilys-vars.sh
DB_PASSWORD=$(openssl rand -hex 24)
sudo -u postgres psql -c "CREATE USER hilys WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE hilys OWNER hilys;"
echo "$DB_PASSWORD" > /root/hilys-db-password && chmod 600 /root/hilys-db-password
adduser --system --group --home /srv/hilys hilys
echo done
```

**You should see:** `CREATE ROLE`, `CREATE DATABASE`, then `done`.

## Block 4: get the code

```bash
cd /srv/hilys && sudo -u hilys git clone --branch live https://github.com/tshidisoo/HILYS_ONLINE_SCHOOL.git repo
ls /srv/hilys/repo/ecosystem
```

**You should see:** `backend`, `staff-app`, `teacher-portal`, `mobile`, `docs` among the names. If GitHub asks for a password, the repository is private: stop and send the output.

## Block 5: Python environment and packages

```bash
cd /srv/hilys/repo/ecosystem/backend
sudo -u hilys python3 -m venv .venv
sudo -u hilys .venv/bin/pip install --upgrade pip
sudo -u hilys .venv/bin/pip install -r requirements.txt
sudo -u hilys .venv/bin/python -c "import django, weasyprint; print('ok', django.get_version())"
```

**You should see:** `ok 5.2` followed by a number.

## Block 6: the environment file (secrets live only here)

```bash
. /root/hilys-vars.sh
cd /srv/hilys/repo/ecosystem/backend
cat > .env <<ENV
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=$(openssl rand -base64 48 | tr -d '\n=/+')
DJANGO_ALLOWED_HOSTS=api.$DOMAIN
FIELD_ENCRYPTION_KEY=$(.venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
POSTGRES_DB=hilys
POSTGRES_USER=hilys
POSTGRES_PASSWORD=$(cat /root/hilys-db-password)
POSTGRES_HOST=127.0.0.1
REDIS_URL=redis://127.0.0.1:6379/0
CORS_ALLOWED_ORIGINS=https://admin.$DOMAIN,https://teachers.$DOMAIN,https://app.$DOMAIN,$WEBSITE
PUBLIC_SITE_URL=$WEBSITE
API_PUBLIC_URL=https://api.$DOMAIN
EMAIL_ENABLED=0
PUSH_ENABLED=0
ENV
chown hilys:hilys .env && chmod 600 .env
cp .env /root/hilys-env-backup && chmod 600 /root/hilys-env-backup
grep -c "=" .env
```

**You should see:** `14`.

**Keep `/root/hilys-env-backup` safe.** The `FIELD_ENCRYPTION_KEY` unlocks children's encrypted notes: if it is lost, those notes cannot be read again.

## Block 7: database tables, Book 1, and the owner's login

```bash
cd /srv/hilys/repo/ecosystem/backend
sudo -u hilys .venv/bin/python manage.py migrate
sudo -u hilys .venv/bin/python manage.py import_book1
sudo -u hilys .venv/bin/python manage.py createsuperuser
```

The last command asks for a username, email and password: these are **your** owner login. Then:

```bash
cd /srv/hilys/repo/ecosystem/backend
sudo -u hilys .venv/bin/python manage.py shell -c "from users.models import User; u=User.objects.filter(is_superuser=True).first(); u.role='owner'; u.save(); print('owner:', u.username)"
sudo -u hilys .venv/bin/python manage.py collectstatic --noinput
```

**You should see:** `Book 1: 35 lessons`, then `owner:` and your username, then a line about static files copied. Do **not** run `seed_demo` here: it is for demo data only.

## Block 8: services (API, reminders worker, reminder schedule)

```bash
cat > /etc/systemd/system/hilys-backend.service <<'UNIT'
[Unit]
Description=HILYS API (gunicorn)
After=network.target postgresql.service redis-server.service

[Service]
User=hilys
Group=hilys
WorkingDirectory=/srv/hilys/repo/ecosystem/backend
ExecStart=/srv/hilys/repo/ecosystem/backend/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 60
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

cat > /etc/systemd/system/hilys-celery-worker.service <<'UNIT'
[Unit]
Description=HILYS reminders worker (celery)
After=network.target redis-server.service

[Service]
User=hilys
Group=hilys
WorkingDirectory=/srv/hilys/repo/ecosystem/backend
ExecStart=/srv/hilys/repo/ecosystem/backend/.venv/bin/celery -A config worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

cat > /etc/systemd/system/hilys-celery-beat.service <<'UNIT'
[Unit]
Description=HILYS reminder schedule (celery beat)
After=network.target redis-server.service

[Service]
User=hilys
Group=hilys
WorkingDirectory=/srv/hilys/repo/ecosystem/backend
ExecStart=/srv/hilys/repo/ecosystem/backend/.venv/bin/celery -A config beat -l info --schedule /srv/hilys/celerybeat-schedule
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now hilys-backend hilys-celery-worker hilys-celery-beat
sleep 3 && systemctl is-active hilys-backend hilys-celery-worker hilys-celery-beat
```

**You should see:** `active` three times.

## Block 9: build the staff app and the teacher portal

```bash
cd /srv/hilys/repo/ecosystem
sudo -u hilys bash -c "cd staff-app && npm ci && CI=true npm run build"
sudo -u hilys bash -c "cd teacher-portal && npm ci && CI=true npm run build"
ls staff-app/dist/index.html teacher-portal/dist/index.html
```

**You should see:** both `index.html` paths listed.

The parent app's web version is built on a computer with Flutter (`flutter build web --release --no-web-resources-cdn --dart-define=API_URL=https://api.YOUR-DOMAIN`) and its `build/web` folder copied to `/srv/hilys/parent-web` on the server. The phone apps go to the app stores separately.

## Block 10: nginx sites

```bash
. /root/hilys-vars.sh
cat > /etc/nginx/sites-available/hilys <<NGINX
server {
    listen 80;
    server_name api.$DOMAIN;
    client_max_body_size 10m;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /static/ { alias /srv/hilys/repo/ecosystem/backend/staticfiles/; }
}
server {
    listen 80;
    server_name admin.$DOMAIN;
    root /srv/hilys/repo/ecosystem/staff-app/dist;
    location /api/ { proxy_pass http://127.0.0.1:8000; proxy_set_header Host api.$DOMAIN; proxy_set_header X-Forwarded-Proto \$scheme; }
    location / { try_files \$uri /index.html; }
}
server {
    listen 80;
    server_name teachers.$DOMAIN;
    root /srv/hilys/repo/ecosystem/teacher-portal/dist;
    location /api/ { proxy_pass http://127.0.0.1:8000; proxy_set_header Host api.$DOMAIN; proxy_set_header X-Forwarded-Proto \$scheme; }
    location / { try_files \$uri /index.html; }
}
server {
    listen 80;
    server_name app.$DOMAIN;
    root /srv/hilys/parent-web;
    location / { try_files \$uri /index.html; }
}
NGINX
mkdir -p /srv/hilys/parent-web
ln -sf /etc/nginx/sites-available/hilys /etc/nginx/sites-enabled/hilys
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx && echo reloaded
```

**You should see:** `syntax is ok`, `test is successful`, then `reloaded`.

## Block 11: HTTPS

```bash
. /root/hilys-vars.sh
certbot --nginx --non-interactive --agree-tos -m "$ADMIN_EMAIL" --redirect -d api.$DOMAIN -d admin.$DOMAIN -d teachers.$DOMAIN -d app.$DOMAIN
```

**You should see:** `Successfully deployed certificate` for the four names. If certbot says a name does not point to this server, the DNS records are not ready yet: wait an hour and run the block again.

## Block 12: nightly encrypted backups (database and private files)

```bash
mkdir -p /srv/hilys/backups && chown hilys:hilys /srv/hilys/backups
openssl rand -hex 32 > /root/hilys-backup-passphrase && chmod 600 /root/hilys-backup-passphrase
cat > /usr/local/bin/hilys-backup <<'SH'
#!/bin/sh
set -e
STAMP=$(date +%Y-%m-%d)
cd /srv/hilys/backups
sudo -u postgres pg_dump hilys | gzip | openssl enc -aes-256-cbc -pbkdf2 -salt -pass file:/root/hilys-backup-passphrase -out db-$STAMP.sql.gz.enc
tar -czf - -C /srv/hilys/repo/ecosystem/backend media 2>/dev/null | openssl enc -aes-256-cbc -pbkdf2 -salt -pass file:/root/hilys-backup-passphrase -out media-$STAMP.tar.gz.enc || true
find /srv/hilys/backups -name "*.enc" -mtime +30 -delete
SH
chmod 700 /usr/local/bin/hilys-backup
echo "15 2 * * * root /usr/local/bin/hilys-backup" > /etc/cron.d/hilys-backup
/usr/local/bin/hilys-backup && ls -lh /srv/hilys/backups
```

**You should see:** a file named `db-` and today's date, ending `.enc`.

These backups are on the same server. **Copying them off the server every night** (to cloud storage you own) and **trying a restore once** are on your to-do list in the handover; they need an account only you can create. Keep a copy of `/root/hilys-backup-passphrase` somewhere safe: without it the backups cannot be opened.

## Block 13: point the website's form at the new API

On your own computer, in the HILYS repository, set `apiUrl` in `public/assets/site.js`:

```js
apiUrl: "https://api.hilys.com",
```

(with your domain), then deploy the website as usual with `firebase deploy --only hosting`.

## Block 14: checks that change nothing

```bash
. /root/hilys-vars.sh
curl -s -o /dev/null -w "API: %{http_code}\n" https://api.$DOMAIN/api/public/catalogue/
curl -s -o /dev/null -w "Staff app: %{http_code}\n" https://admin.$DOMAIN/
curl -s -o /dev/null -w "Teacher portal: %{http_code}\n" https://teachers.$DOMAIN/
curl -s -o /dev/null -w "Private data without login: %{http_code}\n" https://api.$DOMAIN/api/families/
systemctl is-active hilys-backend hilys-celery-worker hilys-celery-beat
```

**You should see:** `API: 200`, `Staff app: 200`, `Teacher portal: 200`, `Private data without login: 401`, and `active` three times.

Then open `https://admin.YOUR-DOMAIN` and sign in with the owner login from Block 7.

---

## Rollback (only for undoing this setup)

Use this only to remove everything this runbook created. **It deletes the HILYS database: every family, lesson, invoice and payment recorded on this server is lost.** Take a backup first (`/usr/local/bin/hilys-backup`) and copy it off the server.

```bash
systemctl disable --now hilys-backend hilys-celery-worker hilys-celery-beat
rm -f /etc/systemd/system/hilys-*.service /etc/nginx/sites-enabled/hilys /etc/nginx/sites-available/hilys /etc/cron.d/hilys-backup
systemctl daemon-reload && systemctl reload nginx
sudo -u postgres psql -c "DROP DATABASE hilys;" -c "DROP USER hilys;"
echo "Removed. /srv/hilys (code and backups) is left in place; delete it yourself when you are sure."
```

Also set `apiUrl` in `public/assets/site.js` back to `""` and redeploy the website, so its form falls back to WhatsApp.
