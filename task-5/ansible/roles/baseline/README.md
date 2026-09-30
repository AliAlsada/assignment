# baseline

Base configuration for every server: packages, admin users, SSH, IP forwarding and the
UFW firewall.

A router sets `baseline_ip_forward_enabled` and lists the traffic it passes in
`baseline_firewall_forwarded_ports`. Everything else it would route is dropped.

A server with Docker sets `baseline_firewall_docker_enabled`. A published port of a
container does not pass through the incoming rules of UFW, so the traffic to the
containers is dropped, except for the entries in `baseline_firewall_forwarded_ports`.

Other roles do not manage the firewall. A server opens a port by adding an entry to
`baseline_firewall_allowed_ports` in its `group_vars`.

## Variables

| Variable | Default | Description |
|---|---|---|
| `baseline_packages` | `[curl, ufw]` | Packages to install |
| `baseline_admin_group` | `sudonopass` | Group with sudo without a password |
| `baseline_admin_users` | `[]` | List of `{ name, pubkeys }` |
| `baseline_ssh_permit_root_login` | `no` | Root login over SSH |
| `baseline_ssh_password_authentication` | `no` | Password login over SSH |
| `baseline_ip_forward_enabled` | `false` | Route traffic between the interfaces of the server |
| `baseline_firewall_enabled` | `true` | Manage UFW |
| `baseline_firewall_allowed_ports` | `[]` | Ports of the server itself: list of `{ src, port, proto }`, `proto` defaults to `tcp` |
| `baseline_firewall_forwarded_ports` | `[]` | Traffic the server routes to other servers or to its containers: list of `{ src, dest, port, proto }` |
| `baseline_firewall_docker_enabled` | `false` | Filter the traffic to the Docker containers |
| `baseline_firewall_docker_interface` | `docker0` | Bridge interface of Docker |

## Tags

`baseline`, `users`, `ssh`, `firewall`
