# Service manager

A Simple web interface for managing systemd services on a virtual machine.

Supports service operations:

- start, stop, restart, reload, and
- log streaming.

Only allows management of delegated services. The list of managed services is controlled
via environment variables.

Service manager **does not support authentication**. It is expected that this is
implemented at a higher level, like on a reverse proxy.

## Usage

Service manager must run on the host as root. To deploy service manager:

- bundle the application code and requirements into an archive with `task zip`
- unzip the archive on the remote host under `/etc/service-manager/`
- provide env variables in `/etc/service-manager/.env`
- copy `/etc/service-manager/service-manager.service` to `/etc/systemd/system/`
- enable and start the service

## Configuration

Reference the `.env.example` to configure the application.
