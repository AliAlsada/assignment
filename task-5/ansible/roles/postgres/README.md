# postgres

Runs PostgreSQL as a Docker container that publishes its port, with its data in
`postgres_data_volume` on the server. The container runs as a system user with a fixed
uid and gid.

The port is published on the addresses in `postgres_publish_addresses`. The admin user
can connect from the server itself only. Over the network, only the
clients listed in `postgres_hba_entries` can connect.

Requires the `docker` role on the server.

## Variables

| Variable | Default | Description |
|---|---|---|
| `postgres_container_name` | `postgres` | Container name |
| `postgres_docker_image_name` | `postgres` | Image name |
| `postgres_docker_image_tag` | `17` | Image tag |
| `postgres_home_path` | `/opt/postgres/17` | Configuration directory |
| `postgres_data_volume` | `/srv/postgres/17` | Data directory |
| `postgres_uid`, `postgres_gid` | `2001` | User and group of the container |
| `postgres_admin_user` | `postgres` | Admin user |
| `postgres_admin_password` | `change-me` | Admin password, set it in `secrets.yml` |
| `postgres_publish_addresses` | `[127.0.0.1]` | Addresses of the server the port is published on |
| `postgres_admin_host` | `127.0.0.1` | Address the admin tasks connect to |
| `postgres_admin_address` | `172.17.0.1/32` | Source address of the admin tasks, the gateway of the docker network |
| `postgres_port` | `5432` | Port |
| `postgres_max_connections` | `100` | Maximum connections |
| `postgres_users` | `[]` | List of `{ name, password }` |
| `postgres_databases` | `[]` | List of `{ name, owner }` |
| `postgres_hba_entries` | `[]` | List of `{ type, database, user, address, method }` |

## Tags

`postgres`
