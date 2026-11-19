# Sherlock Logs

The fourth project in the DevOps module. Sherlock Logs builds on the foundation
of the previous three tasks and adds monitoring and logging. Effective
monitoring provides real-time insight into infrastructure and application
health, enabling proactive issue resolution; logging provides the detailed
historical record needed for debugging, auditing, and compliance.

The monitoring side uses Prometheus (metrics collection) and Grafana
(visualization). The logging side uses the ELK stack — Elasticsearch, Logstash,
and Kibana — with Filebeat shipping logs from each machine.

For context on the previous three tasks, see `Context.md`, which contains the
original READMEs from Server Sorcery 101, Infrastructure Insight, and Automation
Alchemy.

## What changed in this project

This project extends an existing, working infrastructure rather than starting
fresh. The prior project already exposed some host information through a custom
diagnostic page, but it had no real monitoring pipeline and no logging at all.
Two things were added:

- **Monitoring** — every VM now runs exporters that Prometheus scrapes, and the
  application was rewritten to expose true Prometheus-format metrics (request
  rates, latencies, errors) rather than the human-readable JSON it served before.
- **Logging** — the application now emits structured JSON logs, which are
  shipped to a central ELK stack for storage, search, and visualization.

The backend application itself lives under `infrastructure-insight/backend/`
(carried over from the previous task and extended in place); the deployment
roles copy it from there, so the whole project builds from this single
repository with no external dependencies.

## VM Architecture

| VM | IP | Role |
|---|---|---|
| APPSERVER | 192.168.56.10 | Runs the FastAPI backend container |
| WEBSERVER-1 | 192.168.56.11 | Runs the nginx frontend container |
| WEBSERVER-2 | 192.168.56.12 | Runs the nginx frontend container |
| LOADBALANCER | 192.168.56.13 | nginx load balancer — only externally accessible VM |
| BACKUP | 192.168.56.14 | Weekly automated backups via rsync |
| JENKINS | 192.168.56.15 | Jenkins CI/CD server |
| MONITORING | 192.168.56.16 | Prometheus, Grafana, and the ELK stack |

## The application's endpoints

The backend serves four endpoints, and keeping them separate was the core of
the application rewrite:

- **`/metrics`** — Prometheus exposition format (plain text). Scraped by
  Prometheus. Exposes application behaviour only: request counts, latencies,
  errors, and one custom metric. It deliberately does *not* report host CPU/RAM
  — that is Node Exporter's job, not the application's.
- **`/api/info`** — the human-facing diagnostic JSON (hostname, OS, CPU,
  memory) that the frontend renders. This is the old `/metrics` body, relocated
  so the conventional `/metrics` path could belong to Prometheus. Its content is
  unchanged, so the only frontend change was the fetch URL.
- **`/health`** — unchanged liveness check.
- **`/boom`** — a deliberate endpoint that raises an exception and returns 500.
  Used to demonstrate the error-rate metric and the log-based alerting path.

## Monitoring vs. logging: pull vs. push

The two halves of this project use opposite data-flow models, on purpose:

- **Metrics are pulled.** Prometheus reaches out to each target on a schedule
  and scrapes `/metrics`. Targets are passive — they expose data and wait.
  Prometheus decides when and how often, which means a target that goes silent
  is immediately visible as a failed scrape.
- **Logs are pushed.** Logs are events that happen at unpredictable moments and
  would vanish if not captured. So the producer pushes them outward as they
  occur: the application writes a log line, and it is shipped toward storage.

## Security notes

- Exporter ports (`:9100` Node Exporter, `:8081` cAdvisor) are opened **only**
  to the monitoring VM (`192.168.56.16`) via `from_ip` UFW rules, not to the
  whole subnet. Metrics can reveal reconnaissance-useful detail, and there is
  exactly one legitimate consumer, so the ports are scoped to it.
- cAdvisor runs with `privileged: true`. This is a deliberate, documented
  exception: cAdvisor needs elevated access to read container statistics. Every
  other container mounts host paths read-only and follows least privilege.
- Inter-VM SSH is scoped by role: only BACKUP holds keys to the application
  tier (for rsync), and only Jenkins holds keys to its deploy targets. The
  monitoring VM cannot SSH to the application VMs — verified during testing.
- The Discord webhook used for alert notifications is kept out of version
  control (see setup step 1) and is `.gitignore`d.

## Setup and deployment

The entire stack builds from nothing with two commands plus one manual secret
file. Everything else is automated.

### Prerequisites

- VirtualBox and Vagrant (run from Windows PowerShell/CMD)
- WSL with Ansible installed (run all `ansible-playbook` commands here)
- A Discord webhook URL for alert notifications

### 1. Create the secret file

The Discord webhook is deliberately **not** in version control. Create
`inventory/group_vars/monitoring/main.yml` yourself:

```yaml
---
discord_webhook_url: "https://discord.com/api/webhooks/<id>/<token>"
```

To get a webhook: Discord → channel settings (gear) → Integrations →
Webhooks → New Webhook → Copy Webhook URL.

This path is listed in `.gitignore`. Without it the Alertmanager role fails
with `'discord_webhook_url' is undefined`.

### 2. Set the VM password and boot the machines

From PowerShell, in the project root:

```powershell
$env:DEVOPS_PASSWORD = "123abc"
vagrant up
```

The environment variable is read by the `Vagrantfile` to set the `devops`
user's password. It only applies to the shell session where it was set — if
you open a new window, set it again before running Vagrant.

`vagrant up` creates all seven VMs. Allow several minutes.

### 3. Configure everything with Ansible

From WSL, in the project root:

```bash
ansible-playbook -i inventory/hosts.ini playbook/site.yml -e "ansible_become_password=123abc"
```

This single playbook does everything: hardening, Docker, the application,
the load balancer, backups, Jenkins, and the full monitoring/logging stack.
`playbook/site.yml` imports `playbook/monitoring.yml` at the end, so
monitoring is part of the same run rather than a separate step.

### 4. Set up the Jenkins job (one-time, manual)

Jenkins itself is installed and configured by Ansible, but the first-run
wizard and job creation are done through the web UI:

1. Get the unlock key: `ssh devops@192.168.56.15` then
   `sudo cat /var/lib/jenkins/secrets/initialAdminPassword`
2. Open `http://192.168.56.15:8080`, paste it, install suggested plugins,
   create an admin user.
3. Add a credential (Manage Jenkins → Credentials → Global) of kind
   *Username with password* for the Gitea account.
4. New Item → **Pipeline** → in the Pipeline section choose
   **Pipeline script from SCM**, SCM **Git**, repository URL
   `https://gitea.kood.tech/ruubenkangur/sherlock-logs.git`, branch `*/main`,
   Script Path `Jenkinsfile`.
5. Build Now to verify, then push a commit to see it deploy automatically.

### Service URLs

| Service | URL | Credentials |
|---|---|---|
| Application | http://192.168.56.13 | — |
| Prometheus | http://192.168.56.16:9090 | — |
| Alertmanager | http://192.168.56.16:9093 | — |
| Grafana | http://192.168.56.16:3001 | admin / admin |
| Kibana | http://192.168.56.16:5601 | — |
| Jenkins | http://192.168.56.15:8080 | set during first-run wizard |

## Dashboards, alerts, and usage

### Grafana dashboards (metrics)

All three are provisioned as code from `roles/grafana/files/dashboards/`, so
they exist on a fresh build with no manual import.

- **VM Performance** — CPU, memory, root-filesystem usage, disk I/O and
  network throughput, per instance, from Node Exporter.
- **Docker Containers** — per-container CPU and memory, a running-container
  count across the fleet, and restarts in the last 15 minutes, from cAdvisor.
- **Application Performance** — request rate by endpoint, 4xx/5xx error rate,
  p50/p95/p99 latency from the histogram, and the custom in-progress gauge.
  All four panels come from the application's own `/metrics`.

> **Note on the Application Performance dashboard:** its panels are traffic-driven.
> The request-rate, error-rate, and latency panels use `rate()` over the
> application's counters, so they show "No data" when the application is idle
> and populate once traffic flows. To see them live, generate requests first:
> `for i in $(seq 1 40); do curl -s http://192.168.56.10:3000/api/info >/dev/null; done`
> and hit `http://192.168.56.10:3000/boom` a few times to populate the error panel.

### Kibana dashboards (logs)

Kibana has no provisioning equivalent, so the dashboards, their
visualizations, and the `sherlock-*` data view are exported as saved objects
to `roles/kibana/files/export.ndjson` and imported automatically by the
Kibana role via the saved-objects API. The role waits for Kibana's API to
answer before importing, because Kibana takes 30–90 seconds to start and the
import fails against a not-yet-ready instance.

- **System Logs** — syslog and auth entries (`tags: system`), grok-parsed,
  broken down by source host.
- **Docker Logs** — all container logs (`tags: docker`), with a per-container
  breakdown.
- **Application Logs** — narrowed to the backend container, showing request
  volume over time and the raw application log stream.

> **Note:** Kibana depends on Elasticsearch. If an Elasticsearch node is stopped
> (for example while testing the cluster-health alert), Kibana will fail to load
> until the cluster is healthy again. Bring all nodes back up before using Kibana.

### Log parsing

The application emits structured JSON logs, which Logstash parses with a `json`
filter. Some log lines are **not** JSON — uvicorn's plain-text access lines
(`GET /api/info HTTP/1.1 200 OK`) and multi-line Python exception tracebacks from
`/boom`. These arrive as individual non-JSON lines and are tagged
`_docker_jsonparsefailure` by Logstash. This is the expected handling of mixed
log formats: the lines are still ingested and searchable, only the JSON
structuring is skipped. The `json` filter uses `skip_on_invalid_json => true`
so a non-JSON line does not break the pipeline for the structured lines around it.

### Alerting

Two independent alerting paths run in parallel, both delivering to the same
Discord channel:

**Metric alerts** — Prometheus evaluates `alert_rules.yml`, fires to
Alertmanager, which forwards to a small `alertmanager-discord` bridge
container that translates Alertmanager's payload into Discord's webhook
format. Alertmanager and the bridge share a user-defined Docker network so
the bridge is reachable by name. `send_resolved: true` means each alert also
sends a `[RESOLVED]` message when the condition clears.

**Log-pattern alerts** — Logstash's pipeline has a conditional `http` output:
any event where `[level] == "ERROR"` is POSTed directly to the Discord
webhook, independently of Prometheus. This is what satisfies "Logstash sends
alert notifications based on log patterns."

The alert rules live in a single file, `roles/prometheus/files/alert_rules.yml`,
copied to the Prometheus container by the Prometheus role. (An earlier duplicate
templated copy was removed during development to keep one source of truth.)

### Alert rules and how to trigger them

| Alert | Condition | For | How to trigger |
|---|---|---|---|
| HighCpuUsage | CPU > 80% | 5m | `stress-ng --cpu 8 --timeout 400s` |
| HighMemoryUsage | Memory > 90% | 5m | `stress-ng --vm 2 --vm-bytes 90% --timeout 400s` |
| LowDiskSpace | Free disk < 20% | 2m | `fallocate -l 30G /tmp/large_file.img` |
| VmUnreachable | `up == 0` | 1m | `docker stop node_exporter` |
| ContainerRestartingRepeatedly | > 3 restarts in 15m | 1m | crash-looping container (see limitation below) |
| ContainerMemoryHigh | > 80% of container limit | 2m | `docker run --rm -m 128m polinux/stress stress --vm 1 --vm-bytes 105M --timeout 400s` |
| ElasticsearchClusterUnhealthy | cluster not green | 2m | `docker stop elasticsearch2` (see limitation below) |

Note the timing: an alert must hold its condition for the full `for:`
duration before firing, and Alertmanager's `group_wait` adds a further 30
seconds. A five-minute rule therefore takes about five and a half minutes to
reach Discord. Watching the Prometheus alerts page shows the intermediate
**Pending** state, which is useful confirmation that a rule is working before
it actually fires.

**Demonstrating the log alert:** the backend exposes the `/boom` endpoint,
which raises an exception. Hitting it returns a 500, which the request
middleware logs at ERROR level; Filebeat ships that line, Logstash matches it,
and a Discord message follows within a minute.

```bash
curl http://192.168.56.10:3000/boom
```

Note: hit `/boom` on the backend directly (port 3000) rather than through the
load balancer, so the request reaches the instrumented application.

## Resolved issue: cAdvisor per-container metrics

Early in development, container-level metrics silently stopped resolving.
cAdvisor reported only the root cgroup (`id="/"`) with no `name` label, so the
Docker Containers dashboard and the two container-level alerts — all of which
filter `{name!=""}` — matched nothing (an absent series in PromQL does not
evaluate, so panels stayed empty and alerts could not fire).

The root cause was **an unpinned Docker Engine upgrade switching the default
image store to the containerd snapshotter**, which reports its storage driver
as `overlayfs` (confirmed via `docker info`:
`Storage Driver: overlayfs / driver-type: io.containerd.snapshotter.v1`).
cAdvisor builds its layer-metadata lookup path from the driver name and expects
the classic `image/overlay2/layerdb` layout, which does not exist under the new
store; on the failed lookup it drops the affected containers entirely rather
than merely omitting disk statistics.

The fix, applied in the Docker role's `daemon.json`:

- `"features": { "containerd-snapshotter": false }` — reverts to the classic
  image store that cAdvisor understands.
- `cgroupns_mode: host` on the cAdvisor container — on cgroup v2, gives cAdvisor
  a host view of sibling containers' cgroups (without this it sees only its own
  cgroup as root).
- The Docker package version is now **pinned** so the default image store cannot
  shift again on a future rebuild.

After these changes cAdvisor emits per-container series with `name` labels, the
Docker dashboard populates, and `ContainerMemoryHigh` fires end to end.

## Known limitations

### ContainerRestartingRepeatedly

The rule uses the standard expression
`changes(container_start_time_seconds{name!=""}[15m]) > 3`. During testing it
became clear that cAdvisor (v0.49.1) does not model a container restart as a
single stable series whose start-time increments; instead each incarnation
appears as a **new container-ID series**, and cAdvisor also refreshes
`container_start_time_seconds` for long-running healthy containers across its
housekeeping cycles. As a result:

- The standard `changes()` expression under-detects synthetic crash-loops
  (recreated containers spread their events across many zero-change series).
- A sample-counting workaround (`count_over_time`) was tested and rejected
  because it fires on any container merely by uptime, producing false positives
  on healthy infrastructure.

The rule is retained in its canonical, recognizable form. Reliable per-container
restart counting would require a dedicated restart-count metric that cAdvisor
does not expose (such as the Docker/containerd event stream, or
kube-state-metrics in an orchestrated environment). This was verified
empirically by observing `changes(...)` return non-zero values for healthy
containers at rest.

### ElasticsearchClusterUnhealthy

The rule is `elasticsearch_cluster_health_status{color="green"} == 0`. In this
two-node cluster, stopping a data node can make the cluster briefly unavailable
rather than degrading cleanly to yellow, in which case the exporter (which
queries `elasticsearch1`) loses its data source and the metric becomes **absent**
rather than going to 0 — and an absent series cannot satisfy `== 0`. A more
robust form would be
`elasticsearch_cluster_health_status{color="green"} == 0 or absent(elasticsearch_cluster_health_status{color="green"})`,
and the exporter should always be pointed at a node that stays up during the
test (stop `elasticsearch2`, never `elasticsearch1`). A reliable yellow state can
be forced by creating an index that requires a replica the surviving node cannot
place.

## Deliverables and review

- All source code and configuration files are in this repository.
- The stack builds from nothing with `vagrant up` + the Ansible playbook, plus
  the one manual secret file and the one-time Jenkins job setup.

During the review, be prepared to:

- Spin up and configure the Monitoring and Logging VM using automation.
- Explain code and design choices.
- Discuss challenges — the cAdvisor/containerd-snapshotter diagnosis and the two
  documented alerting limitations above are the most substantial.