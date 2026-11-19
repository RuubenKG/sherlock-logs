# CONTEXT

This md file contains the README for the previous DevOps projects, 'Server Sorcery 101' 'Infrastructure Insight' and 'Automation Alchemy', this will serve as context on what has come before. I highly recommend to read this text through as it will serve as a foundation on what has been done before Automation Alchemy.

## Infrastructure Insight

> A containerized infrastructure monitoring application deployed across multiple virtual machines with load balancing and automated backups. Built as the second project in the DevOps module, extending the foundation established in Server Sorcery 101.

---

## Table of Contents

- [Foundation — Server Sorcery 101](#foundation--server-sorcery-101)
- [What is Infrastructure Insight?](#what-is-infrastructure-insight)
- [Application Architecture](#application-architecture)
- [How it was Built](#how-it-was-built)
- [Docker and Nginx](#docker-and-nginx)
- [Extras](#extras)
- [Deployment Guide](#deployment-guide)

---

## Foundation — Server Sorcery 101

This project builds on top of Server Sorcery 101 which established the VM infrastructure. Understanding that foundation is essential context.

### Requirements

| Tool | Version |
|---|---|
| VirtualBox | 7.2+ |
| Vagrant | 2.4+ |
| OS | Windows 10/11 |
| Auth | SSH key pair |

### VM Architecture

| Hostname | IP | Role |
|---|---|---|
| APPSERVER | 192.168.56.10 | Backend — all business logic runs here |
| WEBSERVER-1 | 192.168.56.11 | Serves frontend, handles HTTP traffic from loadbalancer |
| WEBSERVER-2 | 192.168.56.12 | Serves frontend, handles HTTP traffic from loadbalancer |
| LOADBALANCER | 192.168.56.13 | Single entry point — distributes traffic between webservers |

The loadbalancer is the only VM accessible from a browser. The appserver and webservers should only receive traffic routed through it, keeping internal VMs protected from direct external access.

All VMs run Ubuntu 22.04 (jammy64) and are defined in the Vagrantfile. The appserver receives more resources because it runs the backend and handles all metric computation. The webservers and loadbalancer only serve files and forward traffic which requires significantly less processing power.

```ruby
Vagrant.configure("2") do |config|
  config.vm.boot_timeout = 300

  config.vm.define "appserver" do |appserver|
    appserver.vm.box = "ubuntu/jammy64"
    appserver.vm.hostname = "APPSERVER"
    appserver.vm.network "private_network", ip: "192.168.56.10"
    appserver.vm.provider "virtualbox" do |vb|
      vb.memory = 2048
      vb.cpus = 2
    end
  end

  config.vm.define "webserver1" do |webserver1|
    webserver1.vm.box = "ubuntu/jammy64"
    webserver1.vm.hostname = "WEBSERVER-1"
    webserver1.vm.network "private_network", ip: "192.168.56.11"
    webserver1.vm.provider "virtualbox" do |vb|
      vb.memory = 1024
      vb.cpus = 1
    end
  end

  config.vm.define "webserver2" do |webserver2|
    webserver2.vm.box = "ubuntu/jammy64"
    webserver2.vm.hostname = "WEBSERVER-2"
    webserver2.vm.network "private_network", ip: "192.168.56.12"
    webserver2.vm.provider "virtualbox" do |vb|
      vb.memory = 1024
      vb.cpus = 1
    end
  end

  config.vm.define "loadbalancer" do |loadbalancer|
    loadbalancer.vm.box = "ubuntu/jammy64"
    loadbalancer.vm.hostname = "LOADBALANCER"
    loadbalancer.vm.network "private_network", ip: "192.168.56.13"
    loadbalancer.vm.provider "virtualbox" do |vb|
      vb.memory = 1024
      vb.cpus = 2
    end
  end
end
```

### Security Configuration

#### User Management

Each VM has a dedicated `devops` user with administrator privileges. Root access is disabled — all privileged actions require explicit `sudo` with password confirmation, following the principle of least privilege.

#### SSH Hardening

| Setting | Value | Reason |
|---|---|---|
| `PasswordAuthentication` | no | Only SSH key pairs work — eliminates brute force entirely |
| `PermitRootLogin` | no | Root cannot be accessed remotely |
| `AllowUsers` | devops vagrant | Any other user is rejected before authentication begins |

#### Firewall (UFW)

UFW (Uncomplicated Firewall) manages iptables rules — iptables being the Linux kernel's built-in packet filtering system. UFW is active on all VMs with a **default deny incoming** policy.

| VM | Allowed Ports |
|---|---|
| Appserver | 22 (SSH), 3000 (backend API) |
| Webservers | 22 (SSH), 80 (HTTP) |
| Loadbalancer | 22 (SSH), 80 (HTTP) |

#### Additional Security

| Feature | Details |
|---|---|
| Umask 027 | Removes read access from others entirely. Default 022 allows group members to read files |
| Hostname resolution | Handled via `/etc/hosts` — `ping APPSERVER` resolves to `192.168.56.10` without DNS |
| Static IPs | Assigned through Vagrant, persist after every reboot |
| Auto updates | Configured via `/etc/apt/apt.conf.d/20auto-upgrades` |
| Netdata monitoring | Real time metrics dashboard at `http://192.168.56.10:19999` |

#### Network Interfaces (active on all VMs)

| Interface | Purpose |
|---|---|
| `lo` | Loopback — required for internal communication |
| `enp0s3` | NAT adapter for internet access |
| `enp0s8` | Private network for inter-VM communication |

### Server Sorcery 101 Extras

**Fail2Ban** — Bans IPs after 3 failed SSH attempts within 10 minutes for 1 hour. Installed on all 4 VMs.

**WireGuard VPN** — Hub and spoke topology. Appserver is the hub (`10.10.0.1`), webservers and loadbalancer are clients (`10.10.0.2–4`).

---

## What is Infrastructure Insight?

A diagnostic web application that displays live infrastructure metrics — hostname, OS type, CPU usage, memory usage and more — pulled directly from the appserver and rendered in a browser through the loadbalancer.

---

## Application Architecture

| VM | IP | Container Role |
|---|---|---|
| APPSERVER | 192.168.56.10 | FastAPI backend — collects and serves metrics |
| WEBSERVER-1 | 192.168.56.11 | nginx frontend — serves the UI |
| WEBSERVER-2 | 192.168.56.12 | nginx frontend — serves the UI |
| LOADBALANCER | 192.168.56.13 | nginx — distributes traffic between webservers |

### Traffic Flow

```
Browser → Loadbalancer:80
  → Webserver1:80 or Webserver2:80  (round robin)
    → nginx serves HTML/CSS/JS to browser
      → browser JS fetches /metrics from webserver
        → webserver nginx proxies to Appserver:3000
          → FastAPI returns JSON metrics
            → browser renders metrics on page
```

---

## How it was Built

### Backend — Python / FastAPI

Python was chosen for its `psutil` library which makes retrieving system metrics trivial, and `FastAPI` which is the modern standard for building Python APIs.

The backend exposes two endpoints:

| Endpoint | Returns |
|---|---|
| `GET /metrics` | hostname, OS info, CPU and memory data as JSON |
| `GET /health` | `{"status": "healthy"}` for health checks |

### Frontend — JavaScript / nginx

JavaScript handles browser-based metric fetching and DOM manipulation. `app.js` fetches from `/metrics` every 5 seconds and updates the page without a full reload.

The browser cannot call appserver directly due to **CORS** — browsers block requests to different origins for security. Instead the frontend fetches `/metrics` from the same webserver, and nginx proxies that request to appserver internally. The browser never communicates with appserver directly.

### Deploying Files to VMs

Files are transferred from Windows using `scp` (Secure Copy Protocol), which transfers files securely over SSH:

```bash
scp -r "C:\path\to\backend" devops@192.168.56.10:~/
scp -r "C:\path\to\frontend" devops@192.168.56.11:~/
```

---

## Docker and Nginx

### Docker

Docker containerizes both the backend and frontend so they run identically regardless of what's installed on the host VM. Each VM runs one container from its respective image.

- A **Dockerfile** is the blueprint that defines how to build an image
- A **container** is a running instance of that image
- The `--restart always` flag ensures containers automatically restart after a crash or VM reboot

**Backend Dockerfile**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 3000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
```

**Frontend Dockerfile**

```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
COPY style.css /usr/share/nginx/html/style.css
COPY app.js /usr/share/nginx/html/app.js
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Nginx Configuration

Both the frontend and loadbalancer use nginx but configured differently.

**Loadbalancer nginx.conf** — distributes traffic between webservers

```nginx
upstream webservers {
    server 192.168.56.11:80;
    server 192.168.56.12:80;
}

server {
    listen 80;
    location / {
        proxy_pass http://webservers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        add_header X-Served-By $upstream_addr always;
    }
}
```

**Webserver nginx.conf** — serves static files and proxies metrics to appserver

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /metrics {
        proxy_pass http://192.168.56.10:3000/metrics;
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Verify nginx:

```bash
cat /etc/nginx/conf.d/default.conf
sudo systemctl status nginx
```

---

## Extras

### Enhanced UI/UX

The metrics dashboard is styled after the intermission screen from DOOM 2 — dark background with bone imagery, custom DOOM fonts, red text and background music that plays on first interaction.
```
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢁⣴⣦⢠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⡀⠀⡀⠀⠀⠀⠀⠀⠀⢠⠘⣿⣿⡇⠠⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀
⣼⣱⣿⣿⡇⢰⠆⠀⠀⠀⠀⠀⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⣎⢸⣿⡄⢠⡀⠀
⠙⠦⣍⠩⠰⠁⠀⠀⠀⠀⠀⠀⣿⣿⣿⡁⠀⠀⠀⠀⠀⠀⠀⠈⠳⠬⠑⠸⠃⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣠⣀⣉⣏⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⠀⡀⠀⠀⠀
⠀⠀⠀⠀⣀⣀⣀⣷⡆⠛⠛⠛⢛⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡷⠀⡇
⠀⠀⠀⠀⠹⣮⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠅⠀⠠⠬⢍⡹⣿⣿⠿⠁⠘⠀
⠀⠀⠀⠀⠀⠀⠑⠓⠛⠛⠺⠟⠉⠁⢹⣿⣿⡟⠀⣤⢀⡀⢀⠳⠍⠀⠐⠁⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⠀⢻⡸⣿⡆⣇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⡟⠀⠀⣧⢹⣿⣸⡄⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢠⢇⣾⣷⡼⡄⠀⠀⠀⢸⣿⣿⠀⠀⠀⡝⢀⣿⣇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠸⡼⣿⣿⡇⣇⠀⠀⠀⢸⣿⣿⠀⠀⢠⢁⣿⣿⡏⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠱⡜⢿⣿⡜⣆⠀⠀⢸⣿⣿⠀⡤⣣⣾⣿⡟⠁⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠙⣮⢿⣿⣮⠢⠀⢸⣿⣿⣧⣼⣿⡿⠟⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⢧⢻⣿⡇⠀⣸⣿⣿⣿⡿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢀⡀⠀⠀⠀⠀⢠⡀⢠⣘⣓⣠⣤⣾⣿⣿⣿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⡾⢺⣷⣾⠙⡧⠈⢳⡸⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⣠⣷⣿⣿⢷⡆⠀⠀
⣧⣿⠛⡏⢸⠀⠀⠀⢷⡸⠿⠛⣁⢰⣿⣿⠀⠀⠀⠀⠀⠀⢹⡟⣿⡿⢃⣸⠀⠀
⠈⠙⠦⣁⠟⠀⠀⠀⠀⠙⠐⠀⢡⣾⠇⣿⠀⠀⠀⠀⠀⠀⠀⠙⠧⠔⠋⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠹⡿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
```⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣦⡵⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀

Load and Balance, until it is done...

## Load Balancing Algorithm

nginx uses **Round Robin** by default — requests alternate evenly between webservers in order.

An alternative is **Least Connections** which sends each new request to whichever server has the fewest active connections — more intelligent under uneven load.

```nginx
upstream webservers {
    least_conn;
    server 192.168.56.11:80;
    server 192.168.56.12:80;
}
```

Round Robin was kept for this project because both webservers have identical resources and serve identical content, so least connections offers no practical advantage here.

Verify load balancing is working:

```bash
curl -I http://192.168.56.13
```

The `X-Served-By` header alternates between `192.168.56.11:80` and `192.168.56.12:80`.

### Backup VM

A fifth VM (`192.168.56.14`) performs weekly automated backups of `/home/devops` and `/etc` from all 4 VMs using `rsync`.

rsync is preferred over scp because it only copies files that have changed since the last backup, saving time and storage.

```ruby
config.vm.define "backup" do |backup|
  backup.vm.box = "ubuntu/jammy64"
  backup.vm.hostname = "BACKUP"
  backup.vm.network "private_network", ip: "192.168.56.14"
  backup.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 1
  end
end
```

**Automated backups run every Sunday at 2AM via cron:**

```
0 2 * * 0 /opt/backups/backup.sh
```

**Restore `/home/devops` on appserver:**

```bash
ssh devops@192.168.56.14
rsync -avz -e "ssh -o StrictHostKeyChecking=no" \
    /opt/backups/<timestamp>/appserver/home/ \
    devops@192.168.56.10:/home/devops/
```

**Restore `/etc` on appserver:**

```bash
rsync -avz -e "ssh -o StrictHostKeyChecking=no" \
    /opt/backups/<timestamp>/appserver/etc/ \
    devops@192.168.56.10:/etc/
```

---

## Deployment Guide

### Prerequisites

- VirtualBox 7.2+
- Vagrant 2.4+
- SSH key pair at `C:\Users\<username>\.ssh\id_ed25519`

### Step 1 — Start the VMs

```bash
vagrant up
```

### Step 2 — Copy application files

```bash
scp -r "C:\path\to\backend" devops@192.168.56.10:~/
scp -r "C:\path\to\frontend" devops@192.168.56.11:~/
scp -r "C:\path\to\frontend" devops@192.168.56.12:~/
scp "C:\path\to\loadbalancer\nginx.conf" devops@192.168.56.13:~/
```

### Step 3 — Open port 3000 on appserver

```bash
ssh devops@192.168.56.10
sudo ufw allow 3000/tcp
```

### Step 4 — Deploy backend

```bash
cd ~/backend
docker build -t backend .
docker run -d -p 3000:3000 --name backend --restart always backend
docker ps
```

### Step 5 — Deploy frontend (repeat on both webservers)

```bash
ssh devops@192.168.56.11
cd ~/frontend
docker build -t frontend .
docker run -d -p 80:80 --name frontend --restart always frontend
docker ps
```

```bash
ssh devops@192.168.56.12
cd ~/frontend
docker build -t frontend .
docker run -d -p 80:80 --name frontend --restart always frontend
docker ps
```

### Step 6 — Configure loadbalancer

```bash
ssh devops@192.168.56.13
sudo cp ~/nginx.conf /etc/nginx/conf.d/default.conf
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl status nginx
```

> The default nginx site must be removed — it overrides the custom config and shows the nginx welcome page instead.

### Step 7 — Verify

```bash
curl http://192.168.56.13
curl http://192.168.56.13/metrics
curl -I http://192.168.56.13
```

Open `http://192.168.56.13` in your browser. The metrics dashboard should load and the `Served by` tag shows which webserver handled the request.

### Backup VM Deployment

```bash
# Start backup VM
vagrant up backup

# Generate SSH key on backup VM
ssh devops@192.168.56.14
ssh-keygen -t ed25519 -C "backup-key"
cat ~/.ssh/id_ed25519.pub

# Add backup key to all other VMs (run on each)
echo "<backup-public-key>" | sudo tee -a /home/devops/.ssh/authorized_keys

# Run a manual backup
/opt/backups/backup.sh
ls /opt/backups/

# Verify cron job
crontab -l
```


# Automation Alchemy 🔮

The third project in the DevOps module. This project automates everything from the previous two projects (Server Sorcery 101 and Infrastructure Insight) using Ansible, and adds a CI/CD pipeline using Jenkins. To get the important context needed to understand the project, read `Context.md`, that file contains the previous README text that was featured in Server101 and Infrastructure Insight.

For the the review, the project can be only tested during the review session.

## Architecture

| VM | IP | Role |
|---|---|---|
| APPSERVER | 192.168.56.10 | Runs the FastAPI backend container |
| WEBSERVER-1 | 192.168.56.11 | Runs the nginx frontend container |
| WEBSERVER-2 | 192.168.56.12 | Runs the nginx frontend container |
| LOADBALANCER | 192.168.56.13 | nginx load balancer — only externally accessible VM |
| BACKUP | 192.168.56.14 | Weekly automated backups via rsync |
| JENKINS | 192.168.56.15 | Jenkins CI/CD server |

---

## Project Structure

automation-alchemy/
├── inventory/
│   └── hosts.ini                 ← all VM IPs grouped by role
├── playbook/
│   └── site.yml                  ← master playbook, runs everything
├── roles/
│   ├── common/                   ← security config for all VMs
│   ├── appserver/                ← opens port 3000
│   ├── webserver/                ← opens port 80
│   ├── loadbalancer/             ← opens port 80
│   ├── docker/                   ← installs Docker
│   ├── deploy_backend/           ← copies and runs backend container
│   ├── deploy_frontend/          ← copies and runs frontend container
│   ├── backup/                   ← sets up backup script and cron job
│   └── jenkins/                  ← installs Jenkins and Java
├── infrastructure-insight/       ← application source code
├── Vagrantfile                   ← creates all 6 VMs
├── Context.md                    ← previous README's for Server101 and Infrastructure Insight
├── Documentation.md              ← Day by day documentation on how project was made
├── Jenkinsfile                   ← CI/CD pipeline definition
└── README.md

---

## Requirements

- VirtualBox 7.2+
- Vagrant 2.4+
- Ansible (installed in WSL)
- SSH key pair at `C:\Users\<username>\.ssh\id_ed25519`

---

## Setup and Deployment

### Step 1 — Set the devops password

The devops user password is set via an environment variable so it never appears in any file.

**PowerShell:**
```powershell
$env:DEVOPS_PASSWORD = "yourpassword"
```

### Step 2 — Start the VMs

```powershell
cd "C:\path\to\automation-alchemy"
vagrant up
```

This creates all 6 VMs and automatically bootstraps the devops user on each one.

### Step 3 — Clear known hosts (if rebuilding)

In WSL:
```bash
ssh-keygen -f '/home/username/.ssh/known_hosts' -R '192.168.56.10'
ssh-keygen -f '/home/username/.ssh/known_hosts' -R '192.168.56.11'
ssh-keygen -f '/home/username/.ssh/known_hosts' -R '192.168.56.12'
ssh-keygen -f '/home/username/.ssh/known_hosts' -R '192.168.56.13'
ssh-keygen -f '/home/username/.ssh/known_hosts' -R '192.168.56.14'
ssh-keygen -f '/home/username/.ssh/known_hosts' -R '192.168.56.15'
```

### Step 4 — Run Ansible

```bash
cd /mnt/c/path/to/automation-alchemy
ansible-playbook -i inventory/hosts.ini playbook/site.yml -e "ansible_become_password=yourpassword"
```

This single command configures all 6 VMs, deploys the application and sets up the backup and Jenkins SSH keys automatically.

### Step 5 — Access the application

Open your browser and go to: http://192.168.56.13

---

## Jenkins CI/CD Setup

Jenkins is installed automatically by Ansible but requires one-time manual configuration through the browser.

### Initial setup

1. Open `http://192.168.56.15:8080`
2. Get the initial admin password:
```bash
ssh devops@192.168.56.15
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```
3. Paste the password and click **Continue**
4. Click **Install suggested plugins**
5. Create an admin user

### Create the pipeline

1. Click **New Item**
2. Name: `automation-alchemy`, type: **Pipeline**, click **OK**
3. Under **Build Triggers** check **Poll SCM**, schedule: `* * * * *`
4. Under **Pipeline** select **Pipeline script from SCM**
5. SCM: **Git**
6. Repository URL: `https://gitea.kood.tech/ruubenkangur/automation-alchemy`
7. Add credentials with your Gitea username and password
8. Branch: `*/main`
9. Script Path: `Jenkinsfile`
10. Click **Save**

### How the pipeline works

When code is pushed to the main branch Jenkins automatically:

1. Checks out the latest code from Gitea
2. Builds a new Docker image on appserver
3. Stops the old container and starts the new one
4. Builds new Docker images on both webservers
5. Stops old containers and starts new ones
6. Verifies the application is responding via `curl`

---

## Backup

The backup VM automatically backs up `/home/devops` and `/etc` from all 4 application VMs every Sunday at 2AM.

To run a manual backup:
```bash
ssh devops@192.168.56.14
/opt/backups/backup.sh
```

To restore from backup:
```bash
ssh devops@192.168.56.14
rsync -avz -e "ssh -o StrictHostKeyChecking=no" \
    /opt/backups/<timestamp>/appserver/home/ \
    devops@192.168.56.10:/home/devops/
```

---

## Security

All VMs are configured with:
- SSH key authentication only — password login disabled
- Root login disabled
- UFW firewall with default deny policy
- Only required ports open per VM
- Umask 027
- Fail2Ban intrusion prevention
- Automatic security updates