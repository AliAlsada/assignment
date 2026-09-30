# docker

Installs Docker from the Ubuntu packages and configures the log rotation.

A published port of a container does not pass through the incoming rules of UFW. The
`baseline` role handles this with `baseline_firewall_docker_enabled`: the traffic to the
containers is dropped, except for the entries in `baseline_firewall_forwarded_ports`.

## Variables

| Variable | Default | Description |
|---|---|---|
| `docker_packages` | `[docker.io, python3-docker]` | Packages to install |
| `docker_log_driver` | `json-file` | Log driver |
| `docker_log_max_size` | `10m` | Maximum size of a log file |
| `docker_log_max_file` | `3` | Number of log files to keep |

## Tags

`docker`
