pipeline {
  agent any
  environment {
    REGISTRY = "192.168.86.75:80/library"
    APP_NAME = "myapp"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Test') {
      steps {
        sh '''
        echo "Running unit tests..."
        pip install -r apps/myapp/requirements.txt
        pytest apps/myapp/tests --maxfail=1 --disable-warnings -q
        '''
      }
    }

    stage('Build & Push Image') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'harbor-cred', usernameVariable: 'H_USER', passwordVariable: 'H_PASS')]) {
          sh '''
          GIT_SHA=$(git rev-parse --short HEAD)
          IMAGE=${REGISTRY}/${APP_NAME}:${GIT_SHA}
          echo "Building image ${IMAGE}"
          docker build -t ${IMAGE} apps/myapp
          echo $H_PASS | docker login ${REGISTRY} -u $H_USER --password-stdin
          docker push ${IMAGE}
          echo ${IMAGE} > image.txt
          '''
        }
      }
    }

    stage('Update Helm Chart and Push to Git') {
      steps {
        sshagent(['github-ssh']) {
          sh '''
          set -e
          GIT_SHA=$(git rev-parse --short HEAD)
          IMAGE=${REGISTRY}/${APP_NAME}:${GIT_SHA}

          git checkout main
          git pull origin main

          sed -i "s|tag: .*|tag: \\"${GIT_SHA}\\"|" charts/myapp/values.yaml

          git config user.email "ci-bot@example.com"
          git config user.name "ci-bot"
          git add charts/myapp/values.yaml
          git commit -m "ci: update image tag to ${GIT_SHA}" || echo "No changes to commit"
          git push origin main
          '''
        }
      }
    }

    stage('Trigger ArgoCD Refresh') {
      steps {
        sh '''
        argocd app sync myapp || echo "ArgoCD sync skipped"
        '''
      }
    }

    stage('Wait for Deployment') {
      steps {
        sh '''
        kubectl --kubeconfig=/var/jenkins_home/.kube/config rollout status deployment/${APP_NAME} -n default --timeout=120s
        '''
      }
    }

    stage('HTTP Smoke Test') {
      steps {
        sh '''
        APP_IP=$(kubectl --kubeconfig=/var/jenkins_home/.kube/config get svc ${APP_NAME} -n default -o jsonpath='{.spec.clusterIP}')
        curl -sf http://$APP_IP:80/health || (echo "Smoke test failed" && exit 1)
        '''
      }
    }
  }

  post {
    always {
      sh '''
      echo "=== K8S PODS ==="
      kubectl --kubeconfig=/var/jenkins_home/.kube/config get pods -l app=${APP_NAME} -n default -o wide
      echo "=== HELM VALUES ==="
      sed -n 1,120p charts/myapp/values.yaml
      '''
    }
  }
}
