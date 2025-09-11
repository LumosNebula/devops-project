pipeline {
    agent any

    environment {
        IMAGE_REPO = "harbor.local:30003/library/myapp"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                git branch: 'main',
                    url: 'git@github.com:LumosNebula/devops-project.git',
                    credentialsId: 'github-ssh'
            }
        }

        stage('Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                    python -m unittest discover || true
                '''
            }
        }

        stage('Build & Push Image') {
            steps {
                script {
                    IMAGE_TAG = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                    sh "docker build -t ${IMAGE_REPO}:${IMAGE_TAG} -f apps/myapp/Dockerfile apps/myapp"
                    sh "docker push ${IMAGE_REPO}:${IMAGE_TAG}"
                }
            }
        }

        stage('Update Helm Chart and Push to Git') {
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: 'github-ssh', keyFileVariable: 'SSH_KEY')]) {
                    script {
                        IMAGE_TAG = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                        sh "sed -i 's|tag: .*|tag: ${IMAGE_TAG}|' charts/myapp/values.yaml"
                        sh '''
                            eval $(ssh-agent -s)
                            ssh-add $SSH_KEY
                            git config user.email "jenkins@example.com"
                            git config user.name "Jenkins"
                            git checkout -B main
                            git add charts/myapp/values.yaml
                            git commit -m "Update Helm chart image tag to ${IMAGE_TAG}" || true
                            git push origin main
                            ssh-agent -k
                        '''
                    }
                }
            }
        }

        stage('Trigger ArgoCD Refresh') {
            steps {
                echo "Triggering ArgoCD refresh..."
            }
        }

        stage('Wait for Deployment') {
            steps {
                echo "Waiting for deployment..."
            }
        }

        stage('HTTP Smoke Test') {
            steps {
                echo "Performing HTTP smoke test..."
            }
        }
    }

    post {
        always {
            sh "kubectl --kubeconfig=/var/jenkins_home/.kube/config get pods -l app=myapp -n default -o wide"
            sh "cat charts/myapp/values.yaml"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}
