pipeline {
    agent any
    environment {
        DOCKER_REGISTRY = "192.168.86.75:80"
        IMAGE_NAME = "myapp"
        GIT_COMMIT = "${env.GIT_COMMIT}"
    }
    stages {
        stage('Checkout SCM') {
            steps {
                checkout([$class: 'GitSCM', 
                    branches: [[name: '*/main']], 
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
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
python -m unittest discover || exit 1
'''
            }
        }
        stage('Build & Push Image') {
            steps {
                echo 'Building and pushing Docker image...'
                sh '''
docker build -t $DOCKER_REGISTRY/library/$IMAGE_NAME:$GIT_COMMIT -f apps/myapp/Dockerfile apps/myapp
docker push $DOCKER_REGISTRY/library/$IMAGE_NAME:$GIT_COMMIT
'''
            }
        }
        stage('Update Helm Chart and Push to Git') {
            steps {
                sh '''
sed -i "s|tag: .*|tag: \"$GIT_COMMIT\"|" charts/myapp/values.yaml
git add charts/myapp/values.yaml
git commit -m "Update Helm chart image tag to $GIT_COMMIT"
git push origin main
'''
            }
        }
        stage('Trigger ArgoCD Refresh') {
            steps {
                sh 'argocd app sync myapp'
            }
        }
        stage('Wait for Deployment') {
            steps {
                sh '''
kubectl --kubeconfig=/var/jenkins_home/.kube/config rollout status deployment/myapp -n default
'''
            }
        }
        stage('HTTP Smoke Test') {
            steps {
                sh 'curl -f http://myapp.default.svc.cluster.local/health'
            }
        }
    }
    post {
        always {
            echo '=== K8S PODS ==='
            sh 'kubectl --kubeconfig=/var/jenkins_home/.kube/config get pods -l app=myapp -n default -o wide'
            echo '=== HELM VALUES ==='
            sh 'sed -n 1,120p charts/myapp/values.yaml'
            echo 'Pipeline finished!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
