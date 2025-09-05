pipeline {
    agent any
    environment {
        PATH = "/usr/bin:$PATH"
        HARBOR_USERNAME = 'admin'
        HARBOR_PASSWORD = 'niuniu'
        DOCKER_REGISTRY = "192.168.86.75:80"
        KUBECONFIG = "/var/jenkins_home/.kube/config"
    }
    stages {
        stage('Checkout SCM') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: 'main']],
                    userRemoteConfigs: [[url: 'git@github.com:LumosNebula/devops-project.git', credentialsId: 'github-ssh']]
                ])
            }
        }

        stage('Test') {
            steps {
                script {
                    echo "Running unit tests..."
                    sh """
                        /usr/bin/python3 -m pip install --upgrade pip
                        /usr/bin/python3 -m pip install -r apps/myapp/requirements.txt
                        /usr/bin/python3 -m pytest apps/myapp/tests
                    """
                }
            }
        }

        stage('Build & Push Image') {
            steps {
                script {
                    def imageTag = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    def imageName = "${DOCKER_REGISTRY}/library/myapp:${imageTag}"

                    sh """
                        docker login -u ${HARBOR_USERNAME} -p ${HARBOR_PASSWORD} ${DOCKER_REGISTRY}
                        docker build -t ${imageName} apps/myapp
                        docker push ${imageName}
                    """

                    // 保存镜像信息供后续 Helm 更新
                    env.IMAGE_NAME = imageName
                }
            }
        }

        stage('Update Helm Chart and Push to Git') {
            steps {
                script {
                    def chartPath = "charts/myapp/values.yaml"
                    sh """
                        sed -i "s|repository:.*|repository: '${DOCKER_REGISTRY}/library/myapp'|" ${chartPath}
                        sed -i "s|tag:.*|tag: '${env.IMAGE_NAME.split(':')[-1]}'|" ${chartPath}
                    """
                    sh "git add ${chartPath} && git commit -m 'Update Helm values with new image ${env.IMAGE_NAME}' || echo 'No changes to commit'"
                    sh "git push origin main"
                }
            }
        }

        stage('Trigger ArgoCD Refresh') {
            steps {
                script {
                    sh "argocd app sync myapp || echo 'ArgoCD sync failed, check manually'"
                }
            }
        }

        stage('Wait for Deployment') {
            steps {
                script {
                    sh """
                        kubectl --kubeconfig=${KUBECONFIG} rollout status deployment/myapp -n default
                    """
                }
            }
        }

        stage('HTTP Smoke Test') {
            steps {
                script {
                    sh """
                        STATUS_CODE=\$(curl -s -o /dev/null -w "%{http_code}" http://myapp.default.svc.cluster.local/health)
                        if [ "\$STATUS_CODE" != "200" ]; then
                            echo "Smoke test failed with HTTP code \$STATUS_CODE"
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
            sh "kubectl --kubeconfig=${KUBECONFIG} get pods -l app=myapp -n default -o wide"

            echo "=== HELM VALUES ==="
            sh "sed -n 1,120p charts/myapp/values.yaml"

            echo "Pipeline finished!"
        }

        failure {
            echo "Pipeline failed!"
        }
    }
}
