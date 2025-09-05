pipeline {
  agent any
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
          tar -C "$WORKSPACE" -c apps/myapp | \
            docker run --rm -i -w /workspace python:3.10-slim /bin/sh -euxc '\
              mkdir -p /workspace && tar -x -C /workspace && \
              python -m pip install --upgrade pip && \
              python -m pip install -r /workspace/apps/myapp/requirements.txt && \
              cd /workspace/apps/myapp && \
              python -m pytest -q'
        '''
      }
    }

    stage('Build & Push Image') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'harbor-cred', usernameVariable: 'H_USER', passwordVariable: 'H_PASS')]) {
          sh '''#!/bin/sh
            set -eux
            GIT_SHA=$(git rev-parse --short HEAD)
            IMAGE=192.168.86.75:80/library/myapp:${GIT_SHA}
            docker build -t ${IMAGE} apps/myapp
            echo $H_PASS | docker login 192.168.86.75:80 -u $H_USER --password-stdin
            docker push ${IMAGE}
          '''
        }
      }
    }

    stage('Update Helm Chart and Push to Git') {
      steps {
        sshagent(['github-ssh']) {
          sh '''#!/bin/sh
            set -eux
            GIT_SHA=$(git rev-parse --short HEAD)
            cd charts/myapp
            yq -i ".image.tag = \\"${GIT_SHA}\\"" values.yaml
            cd ../..
            git config user.email "ci-bot@example.com"
            git config user.name "ci-bot"
            git add charts/myapp/values.yaml
            git commit -m "ci: update image tag to ${GIT_SHA}" || true
            git push origin main
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
          kubectl --kubeconfig=/var/jenkins_home/.kube/config rollout status deployment/myapp -n default --timeout=120s
        '''
      }
    }

    stage('HTTP Smoke Test') {
      steps {
        sh '''#!/bin/sh
          set -eux
          POD=$(kubectl --kubeconfig=/var/jenkins_home/.kube/config get pod -l app=myapp -n default -o jsonpath="{.items[0].metadata.name}")
          kubectl --kubeconfig=/var/jenkins_home/.kube/config exec -n default $POD -- curl -s http://localhost:8080/health
        '''
      }
    }
  }
  post {
    always {
      sh '''#!/bin/sh
        echo "=== K8S PODS ==="
        kubectl --kubeconfig=/var/jenkins_home/.kube/config get pods -l app=myapp -n default -o wide || true
        echo "=== HELM VALUES ==="
        sed -n 1,120p charts/myapp/values.yaml || true
      '''
    }
  }
}

