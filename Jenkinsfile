pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = "python-webapp"
        DEPLOY_SERVER = "144.24.153.184"
        DEPLOY_USER = "virajith"
        DEPLOY_PATH = "/home/virajith/webapp"
        SSH_PORT = "4003"
        CONTAINER_NAME = "python-webapp-container"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '🔍 Checking out code from GitHub...'
                checkout scm
                sh 'ls -la'
            }
        }
        
        stage('Validate Files') {
            steps {
                echo '✅ Validating project files...'
                script {
                    sh """
                        echo "Checking required files..."
                        test -f app.py && echo "✓ app.py found" || exit 1
                        test -f requirements.txt && echo "✓ requirements.txt found" || exit 1
                        test -f Dockerfile && echo "✓ Dockerfile found" || exit 1
                        test -f templates/index.html && echo "✓ templates/index.html found" || exit 1
                        echo "All required files present!"
                    """
                }
            }
        }
        
        stage('Transfer Code to Server') {
            steps {
                echo '📤 Transferring code to deployment server...'
                sshagent(['deployment-server-ssh']) {
                    script {
                        sh """
                            # Create directories on deployment server
                            echo "Creating deployment directories..."
                            ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                                mkdir -p ${DEPLOY_PATH}/templates
                                echo "Directories created successfully"
                            '
                            
                            # Transfer application files
                            echo "Transferring files..."
                            scp -P ${SSH_PORT} -o StrictHostKeyChecking=no \
                                app.py requirements.txt Dockerfile \
                                ${DEPLOY_USER}@${DEPLOY_SERVER}:${DEPLOY_PATH}/
                            
                            # Transfer templates directory
                            scp -P ${SSH_PORT} -o StrictHostKeyChecking=no \
                                templates/index.html \
                                ${DEPLOY_USER}@${DEPLOY_SERVER}:${DEPLOY_PATH}/templates/
                            
                            # Verify files transferred
                            echo "Verifying files on remote server..."
                            ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} '
                                cd ${DEPLOY_PATH}
                                echo "Files in deployment directory:"
                                ls -la
                                echo ""
                                echo "Files in templates directory:"
                                ls -la templates/
                            '
                            
                            echo "✅ All files transferred successfully!"
                        """
                    }
                }
            }
        }
        
        stage('Build Docker Image on Server') {
            steps {
                echo '🏗️ Building Docker image on ARM64 server...'
                sshagent(['deployment-server-ssh']) {
                    script {
                        sh """
                            ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} << 'ENDSSH'
                                cd ${DEPLOY_PATH}
                                
                                echo "Building Docker image with ARM64 platform..."
                                docker build --platform linux/arm64 -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .
                                docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest
                                
                                echo "✅ Docker image built successfully!"
                                docker images | grep ${DOCKER_IMAGE}
ENDSSH
                        """
                    }
                }
            }
        }
        
        stage('Stop Old Container') {
            steps {
                echo '🛑 Stopping old container if exists...'
                sshagent(['deployment-server-ssh']) {
                    script {
                        sh """
                            ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} << 'ENDSSH'
                                # Stop and remove old container (ignore errors if it doesn't exist)
                                docker stop ${CONTAINER_NAME} 2>/dev/null || echo "No container to stop"
                                docker rm ${CONTAINER_NAME} 2>/dev/null || echo "No container to remove"
                                echo "✅ Old container cleaned up"
ENDSSH
                        """
                    }
                }
            }
        }
        
        stage('Deploy New Container') {
            steps {
                echo '🚀 Starting new container...'
                sshagent(['deployment-server-ssh']) {
                    script {
                        sh """
                            ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} << 'ENDSSH'
                                cd ${DEPLOY_PATH}
                                
                                echo "Starting container with volume bind..."
                                docker run -d \\
                                    --name ${CONTAINER_NAME} \\
                                    --restart unless-stopped \\
                                    --platform linux/arm64 \\
                                    -p 80:5000 \\
                                    -v ${DEPLOY_PATH}:/app:rw \\
                                    ${DOCKER_IMAGE}:latest
                                
                                echo "✅ Container started!"
                                echo "Waiting 5 seconds for container to initialize..."
                                sleep 5
ENDSSH
                        """
                    }
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                echo '🔍 Verifying deployment...'
                sshagent(['deployment-server-ssh']) {
                    script {
                        sh """
                            ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} << 'ENDSSH'
                                echo "============================================"
                                echo "Container Status:"
                                docker ps --filter name=${CONTAINER_NAME} --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"
                                
                                echo ""
                                echo "Container is running:" 
                                docker ps | grep ${CONTAINER_NAME} || exit 1
                                
                                echo ""
                                echo "Recent Logs:"
                                docker logs --tail 20 ${CONTAINER_NAME}
                                echo "============================================"
ENDSSH
                        """
                    }
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo '🏥 Running health checks...'
                script {
                    sh """
                        echo "Waiting 10 seconds for application to be ready..."
                        sleep 10
                        
                        echo "Testing health endpoint..."
                        curl -f -m 10 http://${DEPLOY_SERVER}/health || {
                            echo "❌ Health check failed!"
                            exit 1
                        }
                        
                        echo "Testing home page..."
                        curl -f -m 10 http://${DEPLOY_SERVER}/ || {
                            echo "❌ Home page check failed!"
                            exit 1
                        }
                        
                        echo "✅ All health checks passed!"
                    """
                }
            }
        }
        
        stage('Cleanup Old Images') {
            steps {
                echo '🧹 Cleaning up old Docker images...'
                sshagent(['deployment-server-ssh']) {
                    script {
                        sh """
                            ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} << 'ENDSSH'
                                echo "Removing unused Docker images..."
                                docker image prune -f
                                echo "✅ Cleanup complete!"
ENDSSH
                        """
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo '✅✅✅ DEPLOYMENT SUCCESSFUL! ✅✅✅'
            echo '============================================'
            echo "🌐 Application URL: http://${DEPLOY_SERVER}"
            echo "🏥 Health Check: http://${DEPLOY_SERVER}/health"
            echo "📦 Build Number: ${BUILD_NUMBER}"
            echo '============================================'
        }
        
        failure {
            echo '❌❌❌ DEPLOYMENT FAILED! ❌❌❌'
            echo 'Collecting debug information...'
            sshagent(['deployment-server-ssh']) {
                script {
                    sh """
                        ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} << 'ENDSSH' || true
                            echo "============================================"
                            echo "Container Status:"
                            docker ps -a | grep ${CONTAINER_NAME} || echo "Container not found"
                            
                            echo ""
                            echo "Last 50 lines of container logs:"
                            docker logs --tail 50 ${CONTAINER_NAME} 2>&1 || echo "No logs available"
                            
                            echo ""
                            echo "Docker Images:"
                            docker images | grep ${DOCKER_IMAGE} || echo "No images found"
                            echo "============================================"
ENDSSH
                    """ || true
                }
            }
        }
        
        always {
            echo '📊 Pipeline execution completed'
        }
    }
}