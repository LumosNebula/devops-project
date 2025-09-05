pipeline {
    agent any
    environment {
        H_PASS = credentials('harbor-password') // Harbor 密码
    }
    stages {
        stage('Checkout SCM') {
            steps {
                checkout([
                    $class: 'GitSCM',
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
                echo "Running unit tests inside Docker..."
                sh '''
                docker run --rm -v $PWD:/workspace -w /workspace python:3.10-slim bash -c "
                    python -m pip install --upgrade pip &&
                    python -m pip install -r apps/myapp/requirements.txt &&
                    pytest apps/myapp -q
                "
                '''
            }
        }

        stage('Build & Push Image') {
            steps {
                script {
                    def GIT_SHA = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    def IMAGE = "192.168.86.75:80/library/myapp:${GIT_SHA}"
                    sh "docker build -t ${IMAGE} apps/myapp"
                    sh "echo ${H_PASS} | docker login 192.168.86.75:80 -u admin --password-stdin"
                    sh "docker push ${IMAGE}"
                }
            }
        }

        stage('Update Helm Chart and Push to Git') {
            steps {
                sshagent(credentials: ['github-ssh']) {
                    script {
                        def GIT_SHA = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                        sh """
                        cd charts/myapp
                        yq -i .image.tag="${GIT_SHA}" values.yaml
                        cd ../..
                        git config user.email ci-bot@example.com
                        git config user.name ci-bot
                        git add charts/myapp/values.yaml
                        git commit -m "ci: update image tag to ${GIT_SHA}" || echo "No changes to commit"
                        git push origin main || echo "Push failed, maybe detached HEAD"
                        """
                    }
                }
            }
        }

        stage('Trigger ArgoCD Refresh') {
            steps {
                echo "Trigger ArgoCD refresh (implement your curl/kubectl command here)"
            }
        }

        stage('Wait for Deployment') {
            steps {
                echo "Wait for deployment (kubectl rollout status or sleep)"
            }
        }

        stage('HTTP Smoke Test') {
            steps {
                echo "Perform HTTP smoke test (curl or pytest requests)"
            }
        }
    }

    post {
        always {
            echo "=== K8S PODS ==="
            sh 'kubectl --kubeconfig=/var/jenkins_home/.kube/config get pods -l app=myapp -n default -o wide'
            echo "=== HELM VALUES ==="
            sh 'sed -n 1,120p charts/myapp/values.yaml'
        }
    }
}
