pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = "192.168.86.75:80"
        APP_NAME = "myapp"
        HELM_CHART_PATH = "charts/myapp"
        DOCKERFILE_PATH = "apps/myapp/Dockerfile"
        APP_PATH = "apps/myapp"
        PYTHON_VENV = "venv"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: 'main']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [[$class: 'CloneOption', noTags: false, shallow: false, depth: 0, reference: '', timeout: 60]],
                    userRemoteConfigs: [[
                        url: 'git@github.com:LumosNebula/devops-project.git',
                        credentialsId: 'github-ssh'
                    ]]
                ])
            }
        }

        stage('Test') {
            steps {
                echo "Running unit tests in virtual environment..."
                sh """
                python3 -m venv ${PYTHON_VENV}
                . ${PYTHON_VENV}/bin/activate
                pip install --upgrade pip
                if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
                python -m unittest discover
                """
            }
        }

        stage('Build & Push Image') {
            steps {
                echo "Building and pushing Docker image..."
                script {
                    IMAGE_TAG = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                    sh """
                    docker build -t ${DOCKER_REGISTRY}/library/${APP_NAME}:${IMAGE_TAG} -f ${DOCKERFILE_PATH} ${APP_PATH}
                    docker push ${DOCKER_REGISTRY}/library/${APP_NAME}:${IMAGE_TAG}
                    """
                }
            }
        }

        stage('Update Helm Chart and Push to Git') {
            steps {
                script {
                    IMAGE_TAG = sh(script: "git rev-parse HEAD", returnStdout: true).trim()
                    sh """
                    sed -i "s|tag: .*|tag: ${IMAGE_TAG}|" ${HELM_CHART_PATH}/values.yaml
                    git config user.email "jenkins@example.com"
                    git config user.name "Jenkins"
                    git add ${HELM_CHART_PATH}/values.yaml
                    git commit -m "Update Helm chart image tag to ${IMAGE_TAG}" || echo "No changes to commit"
                    git push origin main
                    """
                }
            }
        }

        stage('Trigger ArgoCD Refresh') {
            steps {
                echo "Triggering ArgoCD refresh..."
                sh "argocd app sync ${APP_NAME} || echo 'ArgoCD sync skipped or failed'"
            }
        }

        stage('Wait for Deployment') {
            steps {
                echo "Waiting for Kubernetes deployment..."
                sh """
                kubectl rollout status deployment/${APP_NAME} -n default --timeout=120s
                """
            }
        }

        stage('HTTP Smoke Test') {
            steps {
                echo "Running HTTP smoke test..."
                sh """
                STATUS_CODE=\$(curl -o /dev/null -s -w "%{http_code}" http://myapp.default.svc.cluster.local:8080/health)
                if [ "\$STATUS_CODE" != "200" ]; then
                    echo "Smoke test failed with status \$STATUS_CODE"
                    exit 1
                fi
                """
            }
        }
    }

    post {
        always {
            echo "=== K8S PODS ==="
            sh "kubectl --kubeconfig=/var/jenkins_home/.kube/config get pods -l app=${APP_NAME} -n default -o wide"
            echo "=== HELM VALUES ==="
            sh "cat ${HELM_CHART_PATH}/values.yaml"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}
