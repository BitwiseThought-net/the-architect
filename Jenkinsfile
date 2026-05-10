pipeline {
    agent any
    options {
        // Disables concurrent builds and aborts the previous running build
        disableConcurrentBuilds(abortPrevious: true)
    }
    stages {
        stage('Setup Variables') {
            steps {
                script {
                    // Explicitly assign to the env object so withCredentials can see it
                    env.REPO_NAME = env.GIT_URL.tokenize('/').last().split("\\.")[0]
                }
            }
        }
        stage('Deploy') {
            steps {
                withCredentials([
                    file(credentialsId: "${env.REPO_NAME}-env", variable: 'ENV_SECRET')
                ]) {
                    script {
                        // --- PREPARE WORKSPACE ---
                        sh "mkdir -p plugins"
                        sh "touch plugins/__init__.py"
                        
                        sh "[ -f requirements.txt ] && sed -i 's/\\r\$//' requirements.txt"
                        sh "[ -f '${ENV_SECRET}' ] && cp '${ENV_SECRET}' .env && sed -i 's/\\r\$//' .env"

                        if (fileExists('docker-compose.yml')) {
                            // Using down/up to refresh file-mount handles
                            sh "docker compose down"
                            sh "docker compose up -d --build"
                        } else {
                            error "No docker-compose.yml found, aborting deployment."
                        }

                        // Clean up sensitive .env file
                        sh "[ -f .env ] && rm .env"
                    }
                }
            }
        }
    }
    post {
        success { echo '🚀 Deployment successful!' }
        failure { echo '❌ Deployment failed. Check the logs for pip or Docker errors.' }
    }
}
