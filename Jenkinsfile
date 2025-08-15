pipeline {
  agent any
  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }
    stage('Build & Push') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'harbor-cred', usernameVariable: 'H_USER', passwordVariable: 'H_PASS')]) {
          sh '''
          GIT_SHA=$(git rev-parse --short HEAD)
          IMAGE=192.168.86.75:80/library/myapp:${GIT_SHA}
          echo "Building image ${IMAGE}"
          docker build -t ${IMAGE} apps/myapp
          echo $H_PASS | docker login 192.168.86.75:80 -u $H_USER --password-stdin
          docker push ${IMAGE}
          kubectl --kubeconfig=/var/jenkins_home/.kube/config set image deployment/myapp myapp=${IMAGE} --namespace=default || kubectl --kubeconfig=/var/jenkins_home/.kube/config apply -f k8s/deployment.yaml
          '''
        }
      }
    }
    stage('Smoke Test') {
      steps {
        sh 'kubectl --kubeconfig=/var/jenkins_home/.kube/config get pods -l app=myapp -o wide'
      }
    }
  }
}

