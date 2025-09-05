pipeline {
    agent any  // 在任何可用节点上运行

    environment {
        REGISTRY = "192.168.86.75:80"
        IMAGE_NAME = "myapp"
        HARBOR_CREDENTIALS = credentials('harbor-password') // Harbor 密码凭证
        KUBECONFIG = "/var/jenkins_home/.kube/config"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                checkout([$class: 'GitSCM', 
                    branches: [[name: 'main']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [],
                    userRemoteConfigs: [[url: 'git@github.com:LumosNebula/devops-project.git', credentialsId: 'github-ssh']]
                ])
            }
        }

        stage('Test') {
            steps {
                echo "Running unit tests..."
                // 使用 python3 -m pip 避免找不到 pip
                sh 'python3 -m pip install --upgrade pip'
                sh 'python3 -m pip install -r apps/myapp/requirements.txt'
                // 可以加你的单元测试命令
                sh 'pytest apps/myapp/tests || true' 
            }
        }

        stage('Build & Push Image') {
            steps {
                script {
                    def commitHash = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    def imageTag = "${commitHash}"
                    env.IMAGE_TAG = imageTag

                    sh """
                    docker build -t ${REGISTRY}/library/${IMAGE_NAME}:${IMAGE_TAG} apps/myapp
                    echo ${HARBOR_CREDENTIALS_PSW} | docker login ${REGISTRY} -u ${HARBOR_CREDENTIALS_USR} --password-stdin
                    docker push ${REGISTRY}/library/${IMAGE_NAME}:${IMAGE_TAG}
                    """
                }
            }
        }

        stage('Update Helm Chart and Push to Git') {
            steps {
                script {
                    sh """
                    sed -i 's|tag:.*|tag: "${IMAGE_TAG}"|' charts/myapp/values.yaml
                    git config user.email "jenkins@example.com"
                    git config user.name "jenkins"
                    git add charts/myapp/values.yaml
                    git commit -m "Update helm chart image tag to ${IMAGE_TAG}" || echo "No changes to commit"
                    git push origin main
                    """
                }
            }
        }

        stage('Trigger ArgoCD Refresh') {
            steps {
                sh """
                curl -X POST http://argocd.example.com/api/v1/applications/myapp/sync \
                     -H "Authorization: Bearer ${ARGOCD_TOKEN}"
                """
            }
        }

        stage('Wait for Deployment') {
            steps {
                echo "Waiting for deployment to complete..."
                sh "kubectl --kubeconfig=${KUBECONFIG} rollout status deployment/myapp -n default"
            }
        }

        stage('HTTP Smoke Test') {
            steps {
                echo "Running HTTP smoke test..."
                sh "curl -f http://myapp.example.com/health || exit 1"
            }
        }
    }

    post {
        always {
            echo "=== K8S PODS ==="
            sh "kubectl --kubeconfig=${KUBECONFIG} get pods -l app=myapp -n default -o wide"
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
