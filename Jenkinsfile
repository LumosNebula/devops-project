pipeline {
    agent any
    environment {
        REGISTRY = "192.168.86.75:80"
        IMAGE_NAME = "myapp"
        HARBOR_USER = "admin"
        HARBOR_PASSWORD = credentials('harbor-password') // Jenkins 凭据ID
        GIT_CREDENTIALS_ID = 'github-ssh'
    }
    stages {
        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                echo "Running unit tests..."
                // 使用 docker 运行测试，保证 pip 可用
                script {
                    docker.image('python:3.10-slim').inside {
                        sh '''
                            python -m pip install --upgrade pip
                            pip install -r apps/myapp/requirements.txt
                            cd apps/myapp
                            python -m pytest -q
                        '''
                    }
                }
            }
        }

        stage('Build & Push Image') {
            steps {
                script {
                    def gitSha = sh(returnStdout: true, script: "git rev-parse --short HEAD").trim()
                    def imageTag = "${REGISTRY}/library/${IMAGE_NAME}:${gitSha}"
                    echo "Building Docker image ${imageTag}"
                    sh "docker build -t ${imageTag} apps/myapp"
                    sh "echo ${HARBOR_PASSWORD} | docker login ${REGISTRY} -u ${HARBOR_USER} --password-stdin"
                    sh "docker push ${imageTag}"
                    env.IMAGE_TAG = gitSha
                }
            }
        }

        stage('Update Helm Chart and Push to Git') {
            steps {
                sshagent([GIT_CREDENTIALS_ID]) {
                    script {
                        sh """
                            cd charts/myapp
                            yq -i '.image.tag = "${env.IMAGE_TAG}"' values.yaml
                            cd ../..
                            git config user.email "ci-bot@example.com"
                            git config user.name "ci-bot"
                            git add charts/myapp/values.yaml
                            git commit -m "ci: update image tag to ${env.IMAGE_TAG}" || echo "No changes to commit"
                            git push origin main || echo "Push failed, check branch name"
                        """
                    }
                }
            }
        }

        stage('Trigger ArgoCD Refresh') {
            steps {
                script {
                    // 如果有 ArgoCD CLI 或 API，可放这里刷新应用
                    echo "Triggering ArgoCD refresh..."
                    // sh "argocd app refresh myapp"
                }
            }
        }

        stage('Wait for Deployment') {
            steps {
                script {
                    echo "Waiting for deployment to be ready..."
                    sh "kubectl --kubeconfig=/var/jenkins_home/.kube/config rollout status deployment/myapp -n default"
                }
            }
        }

        stage('HTTP Smoke Test') {
            steps {
                script {
                    echo "Running HTTP smoke test..."
                    sh '''
                        curl -f http://myapp.default.svc.cluster.local/health || exit 1
                    '''
                }
            }
        }
    }

    post {
        always {
            node {  // 确保 sh 有 node 上下文
                echo "=== K8S PODS ==="
                sh "kubectl --kubeconfig=/var/jenkins_home/.kube/config get pods -l app=myapp -n default -o wide"
                echo "=== HELM VALUES ==="
                sh "sed -n 1,120p charts/myapp/values.yaml"
            }
        }
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}
