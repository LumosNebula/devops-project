pipeline {
    agent any

    stages {
        stage('Declarative: Checkout SCM') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: '*/main']],
                          doGenerateSubmoduleConfigurations: false,
                          extensions: [],
                          userRemoteConfigs: [[credentialsId: 'github-ssh', url: 'git@github.com:LumosNebula/devops-project.git']]])
            }
        }

        stage('Test') {
            steps {
                script {
                    sh '''
                    #!/bin/bash
                    python3 -m venv venv
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    python -m unittest discover
                    '''
                }
            }
        }

        stage('Build & Push Image') {
            steps {
                echo 'Skipping due to earlier failure'
            }
        }

        stage('Update Helm Chart and Push to Git') {
            steps {
                echo 'Skipping due to earlier failure'
            }
        }

        stage('Trigger ArgoCD Refresh') {
            steps {
                echo 'Skipping due to earlier failure'
            }
        }

        stage('Wait for Deployment') {
            steps {
                echo 'Skipping due to earlier failure'
            }
        }

        stage('HTTP Smoke Test') {
            steps {
                echo 'Skipping due to earlier failure'
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
    }
}
