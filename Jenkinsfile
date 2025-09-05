pipeline {
  agent any

  environment {
    REGISTRY = "192.168.86.75:80/library"
    IMAGE_NAME = "myapp"
    SSH_CRED_ID = "github-ssh"
    HARBOR_CRED_ID = "harbor-cred"
    KUBECONFIG = "/var/jenkins_home/.kube/config"
    CHART_PATH = "charts/myapp"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Test') {
      steps {
        sh """
          cd apps/myapp
          pip install -r requirements.txt pytest
          pytest -v
        """
      }
    }

    stage('Build & Push Image') {
      steps {
        withCredentials([usernamePassword(credentialsId: env.HARBOR_CRED_ID, usernameVariable: 'H_USER', passwordVariable: 'H_PASS')]) {
          script {
            def GIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
            def IMAGE = "${REGISTRY}/${IMAGE_NAME}:${GIT_SHA}"
            sh """
              echo "Building image ${IMAGE}"
              docker build -t ${IMAGE} apps/myapp
              echo \$H_PASS | docker login 192.168.86.75:80 -u \$H_USER --password-stdin
              docker push ${IMAGE}
            """
          }
        }
      }
    }

    stage('Update Helm Chart and Push to Git') {
      steps {
        sshagent([env.SSH_CRED_ID]) {
          script {
            def GIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
            sh """set -eux
              echo "DEBUG: updating chart with tag=${GIT_SHA}"
              if command -v yq >/dev/null 2>&1; then
                yq eval -i '.image.tag = \"${GIT_SHA}\"' ${CHART_PATH}/values.yaml
              else
                sed -i -E 's/^([[:space:]]*tag:).*/\\1 \"${GIT_SHA}\"/' ${CHART_PATH}/values.yaml
              fi
              git config user.email "870692011@qq.com"
              git config user.name "niuniu"
              git add ${CHART_PATH}/values.yaml
              git commit -m 'ci: bump myapp image to ${GIT_SHA}' || true
              git push origin HEAD:main
            """
          }
        }
      }
    }

    stage('Trigger ArgoCD Refresh') {
      steps {
        sh """
          kubectl --kubeconfig=${KUBECONFIG} patch application myapp -n argocd -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"manual"}}}' --type=merge || true
        """
      }
    }

    stage('Wait for Deployment') {
      steps {
        sh """
          kubectl --kubeconfig=${KUBECONFIG} rollout status deployment/myapp --namespace=default --timeout=180s || true
        """
      }
    }

    stage('HTTP Smoke Test') {
      steps {
        sh """set -eux
          kubectl --kubeconfig=${KUBECONFIG} port-forward svc/myapp-svc 8080:80 -n default >/dev/null 2>&1 &
          PF_PID=$!
          sleep 2
          if curl -sS --fail http://127.0.0.1:8080/health; then
            echo "health OK"
          elif curl -sS --fail http://127.0.0.1:8080/; then
            echo "root OK"
          else
            echo "app did not respond" >&2
            kill $PF_PID || true
            exit 1
          fi
          kill $PF_PID || true
        """
      }
    }
  }

  post {
    always {
      sh "echo '=== K8S PODS ===' ; kubectl --kubeconfig=${KUBECONFIG} get pods -l app=myapp -n default -o wide || true"
      sh "echo '=== HELM VALUES ===' ; sed -n '1,120p' ${CHART_PATH}/values.yaml || true"
    }
  }
}

