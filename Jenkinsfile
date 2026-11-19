pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from Gitea...'
                checkout scm
            }
        }

        stage('Deploy Backend') {
            steps {
                echo 'Shipping + deploying backend to appserver...'
                sh '''
                    ssh -o StrictHostKeyChecking=no devops@192.168.56.10 "mkdir -p ~/backend"
                    rsync -a --delete -e "ssh -o StrictHostKeyChecking=no" infrastructure-insight/backend/ devops@192.168.56.10:~/backend/
                    ssh -o StrictHostKeyChecking=no devops@192.168.56.10 "
                        cd ~/backend &&
                        docker build -t backend . &&
                        docker stop backend || true &&
                        docker rm backend || true &&
                        docker run -d -p 3000:3000 --name backend --restart always backend
                    "
                '''
            }
        }

        stage('Deploy Frontend') {
            steps {
                echo 'Shipping + deploying frontend to webservers...'
                sh '''
                    for host in 192.168.56.11 192.168.56.12; do
                        ssh -o StrictHostKeyChecking=no devops@$host "mkdir -p ~/frontend"
                        rsync -a --delete -e "ssh -o StrictHostKeyChecking=no" infrastructure-insight/frontend/ devops@$host:~/frontend/
                        ssh -o StrictHostKeyChecking=no devops@$host "
                            cd ~/frontend &&
                            docker build -t frontend . &&
                            docker stop frontend || true &&
                            docker rm frontend || true &&
                            docker run -d -p 80:80 --name frontend --restart always frontend
                        "
                    done
                '''
            }
        }

        stage('Deploy Monitoring Agents') {
            steps {
                echo 'Deploying monitoring agents to deployment targets...'
                sh '''
                    for host in 192.168.56.10 192.168.56.11 192.168.56.12; do
                        echo "--- Deploying agents to $host ---"

                        ssh -o StrictHostKeyChecking=no devops@$host "
                            docker stop node_exporter || true
                            docker rm node_exporter || true
                            docker run -d --name node_exporter --restart always \
                              --pid host -p 9100:9100 \
                              -v /proc:/host/proc:ro \
                              -v /sys:/host/sys:ro \
                              -v /:/rootfs:ro \
                              prom/node-exporter:v1.8.2 \
                              --path.procfs=/host/proc \
                              --path.sysfs=/host/sys \
                              --path.rootfs=/rootfs
                        "

                        ssh -o StrictHostKeyChecking=no devops@$host "
                            docker stop cadvisor || true
                            docker rm cadvisor || true
                            docker run -d --name cadvisor --restart always \
                              --privileged -p 8081:8080 \
                              --device /dev/kmsg \
                              -v /:/rootfs:ro \
                              -v /var/run:/var/run:ro \
                              -v /sys:/sys:ro \
                              -v /var/lib/docker/:/var/lib/docker:ro \
                              -v /dev/disk/:/dev/disk:ro \
                              -v /var/run/docker.sock:/var/run/docker.sock:ro \
                              -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
                              gcr.io/cadvisor/cadvisor:v0.49.1 \
                              --docker_only=true \
                              --store_container_labels=false \
                              --housekeeping_interval=10s
                        "
                    done
                '''
            }
        }

        
        stage('Verify') {
            steps {
                echo 'Verifying deployment...'
                sh '''
                    curl -f http://192.168.56.10:3000/health || exit 1
                    curl -f http://192.168.56.13 || exit 1
                '''
            }
        }
    }

    post {
        success { echo 'Pipeline completed successfully!' }
        failure { echo 'Pipeline failed!' }
    }
}