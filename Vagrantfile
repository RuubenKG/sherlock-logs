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
  appserver.vm.provision "shell", inline: <<-SHELL
   adduser --disabled-password --gecos "" devops || true
   usermod -aG sudo devops
   echo "devops:#{ENV['DEVOPS_PASSWORD']}" | chpasswd
   mkdir -p /home/devops/.ssh
  echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHhpYzH5ZYT8L0qI170hWb+rV0jyrNwbHHBf1lNj/Cyn devops-key" > /home/devops/.ssh/authorized_keys
  chmod 700 /home/devops/.ssh
  chmod 600 /home/devops/.ssh/authorized_keys
  chown -R devops:devops /home/devops
 SHELL
end

  config.vm.define "webserver1" do |webserver1|
  webserver1.vm.box = "ubuntu/jammy64"
  webserver1.vm.hostname = "WEBSERVER-1"
  webserver1.vm.network "private_network", ip: "192.168.56.11"
  webserver1.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 1
  end
  webserver1.vm.provision "shell", inline: <<-SHELL
   adduser --disabled-password --gecos "" devops || true
   usermod -aG sudo devops
   echo "devops:#{ENV['DEVOPS_PASSWORD']}" | chpasswd
   mkdir -p /home/devops/.ssh
  echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHhpYzH5ZYT8L0qI170hWb+rV0jyrNwbHHBf1lNj/Cyn devops-key" > /home/devops/.ssh/authorized_keys
  chmod 700 /home/devops/.ssh
  chmod 600 /home/devops/.ssh/authorized_keys
  chown -R devops:devops /home/devops
 SHELL
end

  config.vm.define "webserver2" do |webserver2|
  webserver2.vm.box = "ubuntu/jammy64"
  webserver2.vm.hostname = "WEBSERVER-2"
  webserver2.vm.network "private_network", ip: "192.168.56.12"
  webserver2.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 1
  end
  webserver2.vm.provision "shell", inline: <<-SHELL
   adduser --disabled-password --gecos "" devops || true
   usermod -aG sudo devops
   echo "devops:#{ENV['DEVOPS_PASSWORD']}" | chpasswd
   mkdir -p /home/devops/.ssh
  echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHhpYzH5ZYT8L0qI170hWb+rV0jyrNwbHHBf1lNj/Cyn devops-key" > /home/devops/.ssh/authorized_keys
  chmod 700 /home/devops/.ssh
  chmod 600 /home/devops/.ssh/authorized_keys
  chown -R devops:devops /home/devops
 SHELL
end

  config.vm.define "loadbalancer" do |loadbalancer|
  loadbalancer.vm.box = "ubuntu/jammy64"
  loadbalancer.vm.hostname = "LOADBALANCER"
  loadbalancer.vm.network "private_network", ip: "192.168.56.13"
  loadbalancer.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 2
  end
  loadbalancer.vm.provision "shell", inline: <<-SHELL
   adduser --disabled-password --gecos "" devops || true
   usermod -aG sudo devops
   echo "devops:#{ENV['DEVOPS_PASSWORD']}" | chpasswd
   mkdir -p /home/devops/.ssh
  echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHhpYzH5ZYT8L0qI170hWb+rV0jyrNwbHHBf1lNj/Cyn devops-key" > /home/devops/.ssh/authorized_keys
  chmod 700 /home/devops/.ssh
  chmod 600 /home/devops/.ssh/authorized_keys
  chown -R devops:devops /home/devops
 SHELL
end

  config.vm.define "backup" do |backup|
  backup.vm.box = "ubuntu/jammy64"
  backup.vm.hostname = "BACKUP"
  backup.vm.network "private_network", ip: "192.168.56.14"
  backup.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 1
  end
  backup.vm.provision "shell", inline: <<-SHELL
   adduser --disabled-password --gecos "" devops || true
   usermod -aG sudo devops
   echo "devops:#{ENV['DEVOPS_PASSWORD']}" | chpasswd
   mkdir -p /home/devops/.ssh
  echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHhpYzH5ZYT8L0qI170hWb+rV0jyrNwbHHBf1lNj/Cyn devops-key" > /home/devops/.ssh/authorized_keys
  chmod 700 /home/devops/.ssh
  chmod 600 /home/devops/.ssh/authorized_keys
  chown -R devops:devops /home/devops
 SHELL
end

  config.vm.define "jenkins" do |jenkins|
  jenkins.vm.box = "ubuntu/jammy64"
  jenkins.vm.hostname = "JENKINS"
  jenkins.vm.network "private_network", ip: "192.168.56.15"
  jenkins.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 1
  end
  jenkins.vm.provision "shell", inline: <<-SHELL
   adduser --disabled-password --gecos "" devops || true
   usermod -aG sudo devops
   echo "devops:#{ENV['DEVOPS_PASSWORD']}" | chpasswd
   mkdir -p /home/devops/.ssh
  echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHhpYzH5ZYT8L0qI170hWb+rV0jyrNwbHHBf1lNj/Cyn devops-key" > /home/devops/.ssh/authorized_keys
  chmod 700 /home/devops/.ssh
  chmod 600 /home/devops/.ssh/authorized_keys
  chown -R devops:devops /home/devops
 SHELL
end

config.vm.define "monitoring" do |monitoring|
  monitoring.vm.box = "ubuntu/jammy64"
  monitoring.vm.hostname = "MONITORING"
  monitoring.vm.network "private_network", ip: "192.168.56.16"
  monitoring.vm.provider "virtualbox" do |vb|
    vb.memory = 6144
    vb.cpus = 2
  end
  monitoring.vm.provision "shell", inline: <<-SHELL
   adduser --disabled-password --gecos "" devops || true
   usermod -aG sudo devops
   echo "devops:#{ENV['DEVOPS_PASSWORD']}" | chpasswd
   mkdir -p /home/devops/.ssh
  echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHhpYzH5ZYT8L0qI170hWb+rV0jyrNwbHHBf1lNj/Cyn devops-key" > /home/devops/.ssh/authorized_keys
  chmod 700 /home/devops/.ssh
  chmod 600 /home/devops/.ssh/authorized_keys
  chown -R devops:devops /home/devops
 SHELL
end

end