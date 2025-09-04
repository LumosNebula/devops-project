pipeline {
  agent any

  environment {
    REGISTRY = "192.168.86.75:80/library"
    IMAGE_NAME = "myapp"
    SSH_CRED_ID = "github-ssh"        // 你在 Jenkins 增加的 SSH 私钥 ID
    HARBOR_CRED_ID = "harbor-cred"    // 你在 Jenkins 增加的 Harbor 凭证 ID
    KUBECONFIG = "/var/jenkins_home/.kube/config"
    CHART_PATH = "charts/myapp"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build & Push Image') {
      steps {
        withCredentials([usernamePassword(credentialsId: env.HARBOR_CRED_ID, usernameVariable: 'H_USER', passwordVariable: 'H_PASS')]) {
          script {
            // use git short sha as the tag
            GIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
            IMAGE = "${REGISTRY}/${IMAGE_NAME}:${GIT_SHA}"
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
        // use SSH credential to push back to repo
        sshagent([env.SSH_CRED_ID]) {
          script {
            GIT_SHA = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
            // update values.yaml using yq (must be present in the Jenkins container)
            sh """
              yq eval -i '.image.tag = strenv(GIT_SHA)' ${CHART_PATH}/values.yaml
              git config user.email "870692011@qq.com"
              git config user.name "niuniu"
              git add ${CHART_PATH}/values.yaml
              git commit -m "ci: bump myapp image to ${GIT_SHA}" || echo "no changes to commit"
              git push origin HEAD:main
            """
          }
        }
      }
    }

    stage('Trigger ArgoCD Refresh') {
      steps {
        // force ArgoCD to re-evaluate repo (requires kubeconfig mounted)
        sh """
          kubectl --kubeconfig=${KUBECONFIG} patch application myapp -n argocd -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"manual"}}}' --type=merge || true
        """
      }
    }

    stage('Wait for Deployment') {
      steps {
        // wait for rollout to complete (up to 3 minutes)
        sh """
          kubectl --kubeconfig=${KUBECONFIG} rollout status deployment/myapp --namespace=default --timeout=180s || true
        """
      }
    }

    stage('Smoke Test') {
      steps {
        sh "kubectl --kubeconfig=${KUBECONFIG} get pods -l app=myapp -n default -o wide"
      }
    }
  }

  post {
    always {
      // print summary for easier debugging
      sh "echo '=== K8S PODS ===' ; kubectl --kubeconfig=${KUBECONFIG} get pods -l app=myapp -n default -o wide || true"
      sh "echo '=== HELM VALUES ===' ; sed -n '1,120p' ${CHART_PATH}/values.yaml || true"
    }
  }
}
