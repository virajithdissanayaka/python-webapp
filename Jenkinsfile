pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = "python-webapp"
        DOCKER_TAG = "${BUILD_NUMBER}"
        DEPLOY_SERVER = "144.24.153.184"     // deployment server IP
        DEPLOY_USER = "virajith"             // 🔥 changed from ubuntu → your actual SSH user
        DEPLOY_PATH = "/home/virajith/webapp" // adjust if needed
        SSH_PORT = "4003"                    // 🔥 custom SSH port
    }
    
    stages {

        stage('Checkout') {
            steps {
                echo '🔍 Checking out code from repository...'
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                echo '🏗️ Building Docker image...'
                script {
                    sh """
                        docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                    """
                }
            }
        }

        stage('Test') {
            steps {
                echo '🧪 Running tests...'
                script {
                    sh """
                        docker run --rm ${DOCKER_IMAGE}:${DOCKER_TAG} python -c "
import flask
print('Flask imported successfully')
print('Flask version:', flask.__version__)
"
                    """
                }
            }
        }

        stage('Save Docker Image') {
            steps {
                echo '💾 Saving Docker image to tar file...'
                script {
                    sh """
                        docker save ${DOCKER_IMAGE}:latest -o ${DOCKER_IMAGE}.tar
                        ls -lh ${DOCKER_IMAGE}.tar
                    """
                }
            }
        }

        stage('Deploy to Server') {
            steps {
                echo '🚀 Deploying to production server...'
                
                // 🔥 IMPORTANT: must match the Jenkins SSH credential ID
                sshagent(['deployment-server-ssh']) {
                    script {
                        sh """
                            echo "📦 Transferring Docker image..."
                            scp -P ${SSH_PORT} -o StrictHostKeyChecking=no ${DOCKER_IMAGE}.tar ${DEPLOY_USER}@${DEPLOY_SERVER}:${DEPLOY_PATH}/

                            echo "🔧 Deploying on remote server..."
                            ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} << 'ENDSSH'
                                cd ${DEPLOY_PATH}

                                echo "📥 Loading Docker image..."
                                docker load -i ${DOCKER_IMAGE}.tar

                                echo "🛑 Stopping old container..."
                                docker stop python-webapp-container 2>/dev/null || true
                                docker rm python-webapp-container 2>/dev/null || true

                                echo "▶️ Starting new container..."
                                docker run -d \\
                                    --name python-webapp-container \\
                                    --restart unless-stopped \\
                                    -p 80:5000 \\
                                    ${DOCKER_IMAGE}:latest

                                echo "🧹 Cleaning up..."
                                rm -f ${DOCKER_IMAGE}.tar
                                docker image prune -f

                                echo "✅ Deployment complete!"
ENDSSH
                        """
                    }
                }
            }
        }

        stage('Health Check') {
            steps {
                echo '🏥 Performing health check...'
                script {
                    sh """
                        echo "Waiting 10 seconds for application to start..."
                        sleep 10

                        curl -f http://${DEPLOY_SERVER}/health || exit 1
                        curl -f http://${DEPLOY_SERVER}/ || exit 1

                        echo "✅ All health checks passed!"
                    """
                }
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline completed successfully!'
            echo "🌐 URL: http://${DEPLOY_SERVER}"
            echo "🏥 Health: http://${DEPLOY_SERVER}/health"
        }
        failure {
            echo '❌ Pipeline failed!'
        }
        always {
            echo '🧹 Cleaning workspace...'
            sh """
                docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} 2>/dev/null || true
                rm -f ${DOCKER_IMAGE}.tar
            """
        }
    }
}
