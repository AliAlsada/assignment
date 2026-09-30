# traefik

Runs Traefik as a Docker container that publishes the HTTP and HTTPS ports. HTTPS uses
the self-signed certificate of Traefik, no certificate is configured. Each entry in `traefik_apps` is
rendered to one file in `traefik_apps_path`, and files that are no longer in the list
are removed. Traefik watches the directory, so a change to an app does not need a
restart.

Requires the `docker` role on the server.

## Variables

| Variable | Default | Description |
|---|---|---|
| `traefik_container_name` | `traefik` | Container name |
| `traefik_docker_image_name` | `traefik` | Image name |
| `traefik_docker_image_tag` | `v3.7` | Image tag |
| `traefik_config_path` | `/srv/traefik` | Configuration directory |
| `traefik_apps_path` | `/srv/traefik/apps` | One file per app |
| `traefik_http_port` | `80` | Port of the `web` entrypoint |
| `traefik_https_port` | `443` | Port of the `websecure` entrypoint |
| `traefik_log_level` | `INFO` | Log level |
| `traefik_access_log_enabled` | `true` | Write the access log |
| `traefik_apps` | `[]` | List of `{ name, routes: [{ rule }], healthcheck_path, backends: [{ url }] }` |

## Tags

`traefik`
