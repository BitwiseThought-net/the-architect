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
                    file(credentialsId: "${env.REPO_NAME}-env", variable: 'ENV_SECRET'),
                    file(credentialsId: "${env.REPO_NAME}-team-json", variable: 'TEAM_JSON'),
                    file(credentialsId: "${env.REPO_NAME}-plugins-discord-bot-py", variable: 'DISCORD_BOT_PY')
                ]) {
                    script {
                        // --- PREPARE PLUGINS DIRECTORY ---
                        // Ensure plugins folder and __init__.py exist so Docker doesn't throw mount errors
                        sh "mkdir -p plugins"
                        sh "touch plugins/__init__.py"

                        sh "[ -f '${TEAM_JSON}' ] && cp '${TEAM_JSON}' team.json"
                        sh "[ -f '${ENV_SECRET}' ] && cp '${ENV_SECRET}' .env"
                        sh "[ -f '${DISCORD_BOT_PY}' ] && cp '${DISCORD_BOT_PY}' .env"
                        sh "sed -i 's/\\r\$//' .env"

                        sh '''
                        if [ -f docker-compose.yml ]; then
                            # We use down to ensure old "stale" file-mount handles are released
                            docker compose down
                            docker compose up -d --build
                        else
                            echo "No docker-compose.yml found, skipping..."
                            exit 0
                        fi
                        '''
                        
                        // 3. Clean up the .env file after deployment (optional but safer)
                        //sh "[ -f .env ] && rm .env"
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
