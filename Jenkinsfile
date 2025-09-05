pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = "192.168.86.75:80"
        IMAGE_NAME = "myapp"
        KUBECONFIG = "/var/jenkins_home/.kube/config"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: 'main']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [],
                    userRemoteConfigs: [[
                        url: 'git@github.com:LumosNebula/devops-project.git',
                        credentialsId: 'github-ssh'
                    ]]
                ])
            }
        }

        stage('Test') {
            steps {
                echo 'Running unit tests in virtual environment...'
                sh '''
#!/bin/bash
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi
python -m unittest discover || exit 1
'''
            }
        }

        stage('Build & Push Image') {
            steps {
                echo 'Building and pushing Docker image...'
                sh '''
docker build -t $DOCKER_REGISTRY/library/$IMAGE_NAME:$GIT_COMMIT .
docker push $DOCKER_REGISTRY/library/$IMAGE_NAME:$GIT_COMMIT
'''
            }
        }

        stage('Update Helm Chart and Push to Git') {
            steps {
                echo 'Updating Helm chart and pushing to Git...'
                sh '''
sed -i "s|tag: .*|tag: \"$GIT_COMMIT\"|" charts/myapp/values.yaml
git config user.name "jenkins"
git config user.email "jenkins@example.com"
git add charts/myapp/values.yaml
git commit -m "Update image tag to $GIT_COMMIT" || true
git push origin main || true
'''
            }
        }

        stage('Trigger ArgoCD Refresh') {
            steps {
                echo 'Triggering ArgoCD refresh...'
                sh 'argocd app refresh myapp || true'
            }
        }

        stage('Wait for Deployment') {
            steps {
                echo 'Waiting for deployment to complete...'
                sh 'kubectl --kubeconfig=$KUBECONFIG rollout status deployment/myapp -n default'
            }
        }

        stage('HTTP Smoke Test') {
            steps {
                echo 'Running HTTP smoke test...'
                sh 'curl -f http://myapp.default.svc.cluster.local/health'
            }
        }
    }

    post {
        always {
            echo '=== K8S PODS ==='
            sh 'kubectl --kubeconfig=$KUBECONFIG get pods -l app=myapp -n default -o wide'
            echo '=== HELM VALUES ==='
            sh 'sed -n 1,120p charts/myapp/values.yaml'
        }
        failure {
            echo 'Pipeline failed!'
        }
        success {
            echo 'Pipeline finished successfully!'
        }
    }
}
