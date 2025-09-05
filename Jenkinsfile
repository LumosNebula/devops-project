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
        // 在独立 python 容器中运行测试，使用绝对路径并打印目录以便诊断
        sh '''#!/bin/sh
          set -eux
          echo "WORKSPACE env: $WORKSPACE"
          echo "Listing workspace top-level:"
          ls -la "$WORKSPACE" || true
          echo "Listing apps/myapp directory:"
          ls -la "$WORKSPACE/apps/myapp" || true

          docker run --rm -v "$WORKSPACE":/workspace -w /workspace python:3.10-slim \
            /bin/sh -c 'echo "Inside container, pwd=$(pwd)"; ls -la /workspace || true; ls -la /workspace/apps/myapp || true; \
                        python -m pip install --upgrade pip && \
                        python -m pip install -r /workspace/apps/myapp/requirements.txt && \
                        pytest -q /workspace/apps/myapp'
        '''
      }
    }

    stage('Build & Push Image') {
      steps {
        withCredentials([usernamePassword(credentialsId: env.HARBOR_CRED_ID, usernameVariable: 'H_USER', passwordVariable: 'H_PASS')]) {
          script {
            def GIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
            def IMAGE = "${REGISTRY}/${IMAGE_NAME}:${GIT_SHA}"
            sh '''
              echo "Building image ${IMAGE}"
              docker build -t ${IMAGE} apps/myapp
              echo $H_PASS | docker login 192.168.86.75:80 -u $H_USER --password-stdin
              docker push ${IMAGE}
            '''
            env.IMAGE_TAG = GIT_SHA
          }
        }
      }
    }

    stage('Update Helm Chart and Push to Git') {
      steps {
        sshagent([env.SSH_CRED_ID]) {
          script {
            sh '''#!/bin/sh
              set -eux
              GIT_SHA=$(git rev-parse --short HEAD)
              echo "DEBUG: updating chart with tag=${GIT_SHA}"
              if command -v yq >/dev/null 2>&1; then
                yq eval -i '.image.tag = "'"${GIT_SHA}"'"' ${CHART_PATH}/values.yaml
              else
                sed -i -E "s/^([[:space:]]*tag:).*/\\1 \\"${GIT_SHA}\\"/" ${CHART_PATH}/values.yaml
              fi
              echo "----- values.yaml AFTER update -----"
              sed -n '1,120p' ${CHART_PATH}/values.yaml
              echo "------------------------------------"
              git config user.email "870692011@qq.com"
              git config user.name "niuniu"
              git add ${CHART_PATH}/values.yaml
              git commit -m "ci: bump myapp image to ${GIT_SHA}" || true
              git push origin HEAD:main
            '''
          }
        }
      }
    }

    stage('Trigger ArgoCD Refresh') {
      steps {
        sh '''#!/bin/sh
          set -eux
          kubectl --kubeconfig="$KUBECONFIG" patch application myapp -n argocd \
            -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"manual"}}}' \
            --type=merge || true
        '''
      }
    }

    stage('Wait for Deployment') {
      steps {
        sh '''#!/bin/sh
          set -eux
          kubectl --kubeconfig="$KUBECONFIG" rollout status deployment/myapp --namespace=default --timeout=180s || true
        '''
      }
    }

    stage('HTTP Smoke Test') {
      steps {
        // 在单引号包裹的 sh 中，使用 $PF_PID 等 shell 变量让 shell 自己展开
        sh '''#!/bin/sh
          set -eux
          kubectl --kubeconfig="$KUBECONFIG" port-forward svc/myapp-svc 8080:80 -n default >/dev/null 2>&1 &
          PF_PID=$!
          sleep 2
          if curl -sS --fail http://127.0.0.1:8080/health; then
            echo "health OK"
          elif curl -sS --fail http://127.0.0.1:8080/; then
            echo "root OK"
          else
            echo "app did not respond" >&2
            kill -0 $PF_PID >/dev/null 2>&1 && kill $PF_PID || true
            exit 1
          fi
          kill -0 $PF_PID >/dev/null 2>&1 && kill $PF_PID || true
        '''
      }
    }
  }

  post {
    always {
      sh '''#!/bin/sh
        echo '=== K8S PODS ==='
        kubectl --kubeconfig=$KUBECONFIG get pods -l app=myapp -n default -o wide || true
        echo '=== HELM VALUES ==='
        sed -n '1,120p' $CHART_PATH/values.yaml || true
      '''
    }
  }
}

