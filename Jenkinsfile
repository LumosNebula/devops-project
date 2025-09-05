pipeline {
    agent any

    environment {
        REGISTRY = "192.168.86.75:80"
        HARBOR_USER = "admin"
        HARBOR_PASS = "niuniu"
        KUBECONFIG = "/var/jenkins_home/.kube/config"
        IMAGE_NAME = "myapp"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: 'main']],
                    userRemoteConfigs: [[
                        url: 'git@github.com:LumosNebula/devops-project.git',
                        credentialsId: 'github-ssh'
                    ]]
                ])
            }
        }

        stage('Test') {
            steps {
                script {
                    echo "Running unit tests..."
                    sh "python3 -m pip install --upgrade pip"
                    sh "python3 -m pip install -r apps/myapp/requirements.txt"
                    // 可以加上具体的测试命令，例如 pytest
                    sh "pytest apps/myapp/tests"
                }
            }
        }

        stage('Build & Push Image') {
            steps {
                script {
                    sh """
                        docker build -t $REGISTRY/library/$IMAGE_NAME:latest apps/myapp
                        echo $HARBOR_PASS | docker login $REGISTRY -u $HARBOR_USER --password-stdin
                        docker push $REGISTRY/library/$IMAGE_NAME:latest
                    """
                }
            }
        }

        stage('Update Helm Chart and Push to Git') {
            steps {
                script {
                    sh """
                        sed -i "s|repository: .*|repository: '$REGISTRY/library/$IMAGE_NAME'|g" charts/myapp/values.yaml
                        sed -i "s|tag: .*|tag: 'latest'|g" charts/myapp/values.yaml
                        git config user.name "jenkins"
                        git config user.email "jenkins@example.com"
                        git add charts/myapp/values.yaml
                        git commit -m "Update Helm values for $IMAGE_NAME"
                        git push origin main
                    """
                }
            }
        }

        stage('Trigger ArgoCD Refresh') {
            steps {
                script {
                    sh "argocd app sync myapp"
                }
            }
        }

        stage('Wait for Deployment') {
            steps {
                script {
                    sh """
                        kubectl --kubeconfig=$KUBECONFIG rollout status deployment/$IMAGE_NAME -n default
                    """
                }
            }
        }

        stage('HTTP Smoke Test') {
            steps {
                script {
                    sh """
                        STATUS_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://myapp.default.svc.cluster.local/health)
                        if [ "$STATUS_CODE" != "200" ]; then
                            echo "Smoke test failed with status $STATUS_CODE"
                            exit 1
                        fi
                    """
                }
            }
        }
    }

    post {
        always {
            echo "=== K8S PODS ==="
            sh "kubectl --kubeconfig=$KUBECONFIG get pods -l app=$IMAGE_NAME -n default -o wide"
            echo "=== HELM VALUES ==="
            sh "sed -n 1,120p charts/myapp/values.yaml"
        }

        success {
            echo "Pipeline completed successfully!"
        }

        failure {
            echo "Pipeline failed!"
        }
    }
}
