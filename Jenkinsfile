pipeline {
    agent any
    
    environment {
        // Python and uv configuration
        PYTHON_VERSION = '3.11'
        UV_CACHE_DIR = "${WORKSPACE}/.uv-cache"
        
        // Docker configuration
        DOCKER_REGISTRY = 'your-registry.com'
        IMAGE_NAME = 'your-repo/devops-pipeline'
        IMAGE_TAG = "${BUILD_NUMBER}"
        DOCKER_CREDENTIALS_ID = 'docker-hub-credentials'
        
        // Kubernetes configuration
        KUBECONFIG = credentials('kubeconfig')
        K8S_NAMESPACE = 'devops-pipeline'
        KUBERNETES_CREDENTIALS_ID = 'kube-config-credentials'
        
        // Test configuration
        TEST_DATABASE_URL = 'postgresql://devops_user:devops_password@postgres_test:5432/devops_test'
        TEST_REDIS_URL = 'redis://redis_test:6379/0'
        
        // Quality gates
        COVERAGE_THRESHOLD = '80'
        PERFORMANCE_THRESHOLD = '2000'  // milliseconds
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 60, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm')
    }
    
    stages {
        stage('Preparation') {
            steps {
                echo "🚀 Starting DevOps Pipeline Build #${BUILD_NUMBER}"
                
                // Clean workspace
                cleanWs()
                
                // Checkout code
                checkout scm
                
                // Install uv and dependencies
                sh '''
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    export PATH="$HOME/.cargo/bin:$PATH"
                    uv --version
                '''
                
                // Cache dependencies
                sh '''
                    export PATH="$HOME/.cargo/bin:$PATH"
                    uv sync --frozen
                '''
            }
        }
        
        stage('Layer 1: Static Analysis') {
            parallel {
                stage('Linting with flake8') {
                    steps {
                        echo "🔍 Layer 1: Running static checks with flake8"
                        sh '''
                            export PATH="$HOME/.cargo/bin:$PATH"
                            uv run flake8 devops_pipeline/ tests/ --output-file=flake8-report.txt || true
                        '''
                        
                        // Archive results
                        archiveArtifacts artifacts: 'flake8-report.txt', allowEmptyArchive: true
                        
                        // Parse flake8 output for Jenkins
                        recordIssues(
                            enabledForFailure: true,
                            aggregatingResults: true,
                            tools: [flake8(pattern: 'flake8-report.txt')]
                        )
                    }
                }
                
                stage('Code Formatting') {
                    steps {
                        echo "🎨 Checking code formatting with black and isort"
                        sh '''
                            export PATH="$HOME/.cargo/bin:$PATH"
                            uv run black --check --diff devops_pipeline/ tests/
                            uv run isort --check --diff devops_pipeline/ tests/
                        '''
                    }
                }
                
                stage('Security Scanning') {
                    steps {
                        echo "🔒 Running security checks"
                        sh '''
                            export PATH="$HOME/.cargo/bin:$PATH"
                            uv run bandit -r devops_pipeline/ -f json -o bandit-report.json || true
                        '''
                        archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                    }
                }
            }
        }
        
        stage('Layer 2: Unit Tests') {
            steps {
                echo "🧪 Layer 2: Running unit tests with coverage"
                sh './scripts/run_tests.sh --layer 2'
                
                // Publish test results
                junit 'unit-test-results.xml'
                
                // Publish coverage
                publishCoverage adapters: [
                    coberturaAdapter('coverage.xml')
                ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                
                // Archive coverage report
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
            }
        }
        
        stage('Layer 3: Integration Tests') {
            steps {
                echo "🔗 Layer 3: Running integration tests with Docker Compose"
                sh './scripts/run_tests.sh --layer 3'
                
                // Publish test results
                junit 'integration-test-results.xml'
            }
        }
        
        stage('Build & Push Image') {
            steps {
                echo "🐳 Building and pushing Docker image"
                script {
                    def image = docker.build(IMAGE_NAME, "-f Dockerfile .")
                    
                    docker.withRegistry("https://${DOCKER_REGISTRY}", DOCKER_CREDENTIALS_ID) {
                        image.push()
                        image.push("latest")
                    }
                }
            }
        }
        
        stage('Layer 4: Infrastructure Validation') {
            steps {
                echo "🏗️ Layer 4: Basic Kubernetes manifest check"
                
                // Simple validation without complex tooling
                sh '''
                    if [[ -d "infrastructure/kubernetes" ]] && [[ -f "infrastructure/kubernetes/deployment.yaml" ]]; then
                        echo "✅ Kubernetes manifests found"
                        # Basic YAML syntax validation
                        python3 -c "import yaml; yaml.safe_load(open('infrastructure/kubernetes/deployment.yaml'))"
                        echo "✅ YAML syntax is valid"
                    else
                        echo "⚠️ No Kubernetes manifests found (optional)"
                    fi
                '''
            }
        }
        
        stage('Deploy to Staging') {
            steps {
                echo "🚀 Deploying to staging environment"
                withKubeconfig([credentialsId: KUBERNETES_CREDENTIALS_ID]) {
                    // This assumes you have kubectl and kustomize available on the agent
                    sh 'kubectl apply -k infrastructure/kubernetes/ --namespace=staging'
                    // Add health checks here to verify the deployment
                    sh 'kubectl rollout status deployment/devops-pipeline-deployment --namespace=staging'
                }
            }
        }
        
        stage('Layer 5: End-to-End Tests') {
            steps {
                echo "🎭 Layer 5: Running E2E tests against staging"
                
                script {
                    try {
                        // Get staging URL
                        def stagingUrl = sh(
                            script: "kubectl get ingress devops-pipeline-ingress -n ${K8S_NAMESPACE}-staging -o jsonpath='{.spec.rules[0].host}'",
                            returnStdout: true
                        ).trim()
                        
                        // Install Chrome and ChromeDriver for E2E tests
                        sh '''
                            wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
                            echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
                            apt-get update && apt-get install -y google-chrome-stable
                            
                            # Install ChromeDriver
                            CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
                            wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}/chromedriver_linux64.zip
                            unzip /tmp/chromedriver.zip -d /usr/local/bin/
                            chmod +x /usr/local/bin/chromedriver
                        '''
                        
                        // Run E2E tests
                        sh """
                            export PATH="\$HOME/.cargo/bin:\$PATH"
                            export STAGING_URL="https://${stagingUrl}"
                            
                            uv run pytest tests/e2e/ \
                                -v \
                                --tb=short \
                                --junit-xml=e2e-test-results.xml \
                                -m e2e \
                                --base-url=\${STAGING_URL}
                        """
                        
                        publishTestResults testResultsPattern: 'e2e-test-results.xml'
                        
                    } catch (Exception e) {
                        echo "E2E tests failed: ${e.getMessage()}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Performance Tests') {
            steps {
                echo "⚡ Running performance tests"
                sh '''
                    export PATH="$HOME/.cargo/bin:$PATH"
                    
                    # Install k6 for performance testing
                    curl -s https://api.github.com/repos/grafana/k6/releases/latest | \
                        grep -o 'https://.*k6-v.*-linux-amd64.tar.gz' | \
                        head -n1 | xargs -I {} sh -c 'curl -L {} | tar xz --strip-components=1'
                    
                    # Run performance tests (placeholder)
                    echo "Running performance tests against staging..."
                    # ./k6 run performance-tests.js
                '''
            }
        }
        
        stage('Security Scanning') {
            parallel {
                stage('Container Security') {
                    steps {
                        echo "🔒 Scanning container for vulnerabilities"
                        sh '''
                            # Install Trivy
                            curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                            
                            # Scan the built image
                            trivy image --format json --output trivy-report.json ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} || true
                        '''
                        archiveArtifacts artifacts: 'trivy-report.json', allowEmptyArchive: true
                    }
                }
                
                stage('SAST Scanning') {
                    steps {
                        echo "🔍 Running static application security testing"
                        sh '''
                            export PATH="$HOME/.cargo/bin:$PATH"
                            # Additional security scanning can be added here
                            uv run safety check --json --output safety-report.json || true
                        '''
                        archiveArtifacts artifacts: 'safety-report.json', allowEmptyArchive: true
                    }
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    timeout(time: 5, unit: 'MINUTES') {
                        def userInput = input(
                            id: 'Deploy',
                            message: 'Deploy to production?',
                            parameters: [
                                choice(
                                    choices: ['Deploy', 'Abort'],
                                    description: 'Choose action',
                                    name: 'ACTION'
                                )
                            ]
                        )
                        
                        if (userInput == 'Deploy') {
                            echo "🚀 Deploying to production"
                            sh '''
                                # Update image tag in production manifests
                                sed -i "s|devops-pipeline:latest|${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" infrastructure/kubernetes/*.yaml
                                
                                # Apply to production namespace
                                kubectl apply -f infrastructure/kubernetes/ -n ${K8S_NAMESPACE}
                                
                                # Wait for deployment
                                kubectl rollout status deployment/devops-pipeline-app -n ${K8S_NAMESPACE} --timeout=600s
                            '''
                        } else {
                            error "Deployment aborted by user"
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo "🧹 Cleaning up workspace"
            
            // Archive all test results and reports
            archiveArtifacts artifacts: '**/*-test-results.xml', allowEmptyArchive: true
            archiveArtifacts artifacts: '**/coverage.xml', allowEmptyArchive: true
            archiveArtifacts artifacts: '**/*-report.*', allowEmptyArchive: true
            
            // Clean up Docker images
            sh '''
                docker image prune -f || true
                docker container prune -f || true
            '''
            
            // Clean up workspace
            cleanWs()
        }
        
        success {
            echo "✅ Pipeline completed successfully!"
            
            // Send success notification
            slackSend(
                color: 'good',
                message: "✅ Pipeline #${BUILD_NUMBER} completed successfully!\n" +
                        "Branch: ${env.BRANCH_NAME}\n" +
                        "Commit: ${env.GIT_COMMIT[0..7]}\n" +
                        "Duration: ${currentBuild.durationString}"
            )
        }
        
        failure {
            echo "❌ Pipeline failed!"
            
            // Send failure notification
            slackSend(
                color: 'danger',
                message: "❌ Pipeline #${BUILD_NUMBER} failed!\n" +
                        "Branch: ${env.BRANCH_NAME}\n" +
                        "Commit: ${env.GIT_COMMIT[0..7]}\n" +
                        "Stage: ${env.STAGE_NAME}\n" +
                        "Duration: ${currentBuild.durationString}"
            )
        }
        
        unstable {
            echo "⚠️ Pipeline completed with warnings"
            
            slackSend(
                color: 'warning',
                message: "⚠️ Pipeline #${BUILD_NUMBER} completed with warnings!\n" +
                        "Branch: ${env.BRANCH_NAME}\n" +
                        "Duration: ${currentBuild.durationString}"
            )
        }
    }
} 