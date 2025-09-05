pipeline {
  agent any

  environment {
    REGISTRY = "192.168.86.75:80"
    REPO = "library/myapp"
    KUBECONFIG = "/var/jenkins_home/.kube/config"
    HARBOR_CRED = "harbor-cred"
    GITHUB_CRED = "github-ssh"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Test') {
      steps {
        sh '''#!/bin/sh
          set -eux
          echo "WORKSPACE: $WORKSPACE"
          echo "Local workspace listing:"
          ls -la "$WORKSPACE" || true
          echo "apps/myapp listing:"
          ls -la "$WORKSPACE/apps/myapp" || true

          # 用 tar 打包 apps/myapp，传到容器内再解包，避免挂载问题
          tar -C "$WORKSPACE" -c apps/myapp | \
            docker run --rm -i -w /workspace python:3.10-slim /bin/sh -c '\
              mkdir -p /workspace && tar -x -C /workspace && \
              echo "Inside container: ls /workspace/apps/myapp:" && ls -la /workspace/apps/myapp || true && \
              python -m pip install --upgrade pip && \
              python -m pip install -r /workspace/apps/myapp/requirements.txt && \
              pytest -q /workspace/apps/myapp'
        '''
      }
    }

    stage('Build & Push Image') {
      steps {
        withCredentials([usernamePassword(credentialsId: "${HARBOR_CRED}", usernameVariable: 'H_USER', passwordVariable: 'H_PASS')]) {
          sh '''#!/bin/sh
            set -eux
            GIT_SHA=$(git rev-parse --short HEAD)
            IMAGE=${REGISTRY}/${REPO}:${GIT_SHA}
            echo "Building image ${IMAGE}"
            docker build -t ${IMAGE} apps/myapp
            echo $H_PASS | docker login ${REGISTRY} -u $H_USER --password-stdin
            docker push ${IMAGE}
          '''
        }
      }
    }

    stage('Update Helm Chart and Push to Git') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: "${GITHUB_CRED}", keyFileVariable: 'GIT_SSH_KEY')]) {
          sh '''#!/bin/sh
            set -eux
            GIT_SHA=$(git rev-parse --short HEAD)
            IMAGE=${REGISTRY}/${REPO}:${GIT_SHA}
            echo "Updating Helm values.yaml with ${IMAGE}"
            sed -i "s|tag:.*|tag: \\"${GIT_SHA}\\"|" charts/myapp/values.yaml

            git config --global user.email "ci@jenkins"
            git config --global user.name "Jenkins CI"
            git add charts/myapp/values.yaml
            git commit -m "ci: update image tag to ${GIT_SHA}" || echo "No changes to commit"
            GIT_SSH_COMMAND="ssh -i $GIT_SSH_KEY -o StrictHostKeyChecking=no" git push origin main
          '''
        }
      }
    }

    stage('Trigger ArgoCD Refresh') {
      steps {
        sh '''#!/bin/sh
          set -eux
          argocd app sync myapp || true
        '''
      }
    }

    stage('Wait for Deployment') {
      steps {
        sh '''#!/bin/sh
          set -eux
          kubectl --kubeconfig=${KUBECONFIG} rollout status deployment/myapp -n default --timeout=120s
        '''
      }
    }

    stage('HTTP Smoke Test') {
      steps {
        sh '''#!/bin/sh
          set -eux
          kubectl --kubeconfig=${KUBECONFIG} port-forward svc/myapp 18080:80 -n default &
          PF_PID=$!
          sleep 5
          curl -f http://localhost:18080/health
          kill $PF_PID || true
        '''
      }
    }
  }

  post {
    always {
      sh '''
        echo "=== K8S PODS ==="
        kubectl --kubeconfig=${KUBECONFIG} get pods -l app=myapp -n default -o wide || true

        echo "=== HELM VALUES ==="
        sed -n 1,120p charts/myapp/values.yaml || true
      '''
    }
  }
}
