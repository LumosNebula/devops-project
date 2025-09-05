pipeline {
    agent any

    stages {
        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                script {
                    echo 'Running unit tests in virtual environment...'
                    sh '''
                   
                    python3 -m venv venv
                    source venv/bin/activate

                    
                    pip install --upgrade pip
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi

                 
                    python -m unittest discover
                    '''
                }
            }
        }

        stage('Build & Push Image') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                echo 'Building and pushing Docker image...'
              
            }
        }

        stage('Update Helm Chart and Push to Git') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                echo 'Updating Helm chart and pushing to Git...'
             
            }
        }

        stage('Trigger ArgoCD Refresh') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                echo 'Triggering ArgoCD refresh...'

            }
        }

        stage('Wait for Deployment') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                echo 'Waiting for deployment...'

            }
        }

        stage('HTTP Smoke Test') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                echo 'Running HTTP smoke test...'
            
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
