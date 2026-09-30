# app

Copies the application from `app_source_path`, builds its image on the server and runs
it as a Docker container that publishes its port, as a user without privileges.

The application code is in the `app` directory at the root of the project.

Requires the `docker` role on the server.

## Variables

| Variable | Default | Description |
|---|---|---|
| `app_container_name` | `app` | Container name |
| `app_home_path` | `/opt/app` | Build and configuration directory |
| `app_source_path` | `app` directory of the project | Directory with `app.py` and the `Dockerfile` |
| `app_docker_image_name` | `app` | Image name |
| `app_docker_image_tag` | `1.0.0` | Image tag |
| `app_uid`, `app_gid` | `2002` | User and group of the container |
| `app_listen_address` | `127.0.0.1` | Address of the server the port is published on |
| `app_listen_port` | `8000` | Port |
| `app_vars` | `{}` | Environment variables: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` |

## Tags

`app`
