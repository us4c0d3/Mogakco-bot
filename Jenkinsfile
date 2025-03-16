pipeline {
    agent any
    
    environment {
        VENV_PATH = ".venv"
        ENV_KEY = "mogakcobot-secret-keys"
        DB_KEY = "db-secrets"
        TEST_ENV_KEY = "test-secret-keys"
    }
    
    stages {
        stage('Remove old files') {
            steps {
                script {
                    sh '''
                    if [ -f bot.log ]; then
                        rm bot.log
                    fi
                    '''
                    sh '''
                    rm -rf .venv .env db.env
                    '''
                }
            }
        }
        
        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [],
                    userRemoteConfigs: [[
                        url: 'https://github.com/us4c0d3/Mogakco-bot.git',
                    ]]
                ])
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                script {
                    sh '''
                    python3 -m venv ${VENV_PATH}
                    . ${VENV_PATH}/bin/activate
                    pip install -r requirements.txt
                    '''
                }
            }
        }
        
        stage('Download .env file') {
            steps {
                withCredentials([file(credentialsId: ENV_KEY, variable: 'envFile')]) {
                    script {
                        sh 'cp ${envFile} .env' 
                    }
                }
                withCredentials([file(credentialsId: DB_KEY, variable: 'dbEnvFile')]) {
                    script {
                        sh 'cp ${dbEnvFile} db.env'
                    }
                }
            }
        }
        
        stage('Restart Bot Service') {
            steps {
                script{
                    sh '''
                    sudo systemctl restart mogakco-bot
                    ''' 
                }
            }
        }
    }
    
    post {
        always {
            script{
                sh '''
                deactivate || true
                '''
            }
        }
    }
}
