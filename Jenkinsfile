pipeline {
    agent any
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
                // This "binds" your secret file to a temporary variable (envFile)
                withCredentials([file(credentialsId: "${env.REPO_NAME}-env", variable: 'envFile')]) {
                    script {
                        sh "[ -f '${envFile}' ] && cp '${envFile}' .env"
                        sh "sed -i 's/\\r\$//' .env"
                        
                        // --- DIAGNOSTIC CHECK ---
                        // Confirm lib folder and its contents exist in Jenkins workspace
                        sh "ls -R lib/ || echo '❌ ERROR: lib folder missing in Jenkins workspace'"
                        
                        // 2. GLOBAL FIX: Sanitize all files in the app folder
                        sh "find . -type f -exec sed -i 's/\\r\$//' {} +"
                        
                        // 3. Build and Start
                        sh "docker compose down"
                        sh "docker compose build --no-cache service"
                        sh "docker compose up -d"
                        
                        // 3. Clean up the .env file after deployment (optional but safer)
                        sh "[ -f .env ] && rm .env"
                    }
                }
            }
        }
    }
    post {
        success { echo '🚀 Deployment successful!' }
        failure { echo '❌ Deployment failed. Check the logs.' }
    }
}
