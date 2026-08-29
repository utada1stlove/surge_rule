#!/bin/sh
set -eu

staging_dir=${1:-/tmp/surge-profile-deploy}
nginx_site=/etc/nginx/sites-available/eb-latexme
nginx_backup=/etc/nginx/sites-available/eb-latexme.before-surge-profile

install -d -m 0755 /usr/local/libexec/surge-profile
install -d -m 0700 /etc/surge-profile
install -d -m 0755 /var/lib/surge-profile
install -m 0755 "$staging_dir/render-private-profiles.py" /usr/local/libexec/surge-profile/render-private-profiles.py
install -m 0755 "$staging_dir/surge-profilectl.py" /usr/local/sbin/surge-profilectl
install -m 0644 "$staging_dir/surge-profile-render.service" /etc/systemd/system/surge-profile-render.service
install -m 0644 "$staging_dir/surge-profile-render.timer" /etc/systemd/system/surge-profile-render.timer

if [ ! -e /etc/surge-profile/config.json ]; then
    private_path=$(openssl rand -hex 32)
    install -m 0600 "$staging_dir/config.json.example" /etc/surge-profile/config.json
    sed -i "s/__PRIVATE_PATH__/${private_path}/g" /etc/surge-profile/config.json
fi

if [ ! -e /etc/surge-profile/secrets.json ]; then
    install -m 0600 "$staging_dir/secrets.json.example" /etc/surge-profile/secrets.json
fi

private_path=$(python3 -c 'import json, urllib.parse; value=json.load(open("/etc/surge-profile/config.json"))["public_base_url"]; print(urllib.parse.urlsplit(value).path.strip("/").split("/")[-1])')
install -m 0600 "$staging_dir/surge-profile-location.conf.example" /etc/nginx/snippets/surge-profile-private.conf
sed -i "s/__PRIVATE_PATH__/${private_path}/g" /etc/nginx/snippets/surge-profile-private.conf

if ! grep -q "surge-profile-private.conf" "$nginx_site"; then
    cp -a "$nginx_site" "$nginx_backup"
    sed -i "/charset utf-8;/a\\    include /etc/nginx/snippets/surge-profile-private.conf;" "$nginx_site"
fi

if ! nginx -t; then
    if [ -e "$nginx_backup" ]; then
        cp -a "$nginx_backup" "$nginx_site"
    fi
    nginx -t
    exit 1
fi

systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/surge-profile-render.service /etc/systemd/system/surge-profile-render.timer
systemctl reload nginx
systemctl enable --now surge-profile-render.timer

systemctl is-enabled surge-profile-render.timer
systemctl is-active surge-profile-render.timer
surge-profilectl status
