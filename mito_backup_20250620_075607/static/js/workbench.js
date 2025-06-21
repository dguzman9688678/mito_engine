/*
MITO Engine - AI Agent & Tool Creator
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: AI Agent & Tool Creator
*/

class MitoWorkbench {
    constructor() {
        this.currentProject = null;
        this.activeTab = 'builder';
        this.selectedProjectType = 'webapp';
        this.selectedTechStack = 'react';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadRecentProjects();
        this.initializeChat();
        console.log('MITO Workbench initialized');
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Project type selection
        document.querySelectorAll('.project-type').forEach(type => {
            type.addEventListener('click', (e) => {
                this.selectProjectType(e.target.dataset.type);
            });
        });

        // Tech stack selection
        document.querySelectorAll('.tech-option').forEach(option => {
            option.addEventListener('click', (e) => {
                this.selectTechStack(e.target.dataset.stack);
            });
        });

        // Build project
        const buildBtn = document.getElementById('build-project');
        if (buildBtn) {
            buildBtn.addEventListener('click', () => this.buildProject());
        }

        // Generate code
        const generateBtn = document.getElementById('generate-code');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateCode());
        }
    }

    // Custom AI Builder - GitHub Copilot-level intelligence
    generateCustomAI() {
        console.log('Generating custom AI application...');
        
        // Collect all configuration options
        const functions = [];
        document.querySelectorAll('[id^="func-"]:checked').forEach(el => {
            functions.push(el.id.replace('func-', ''));
        });
        
        const interfaces = [];
        document.querySelectorAll('[id^="interface-"]:checked').forEach(el => {
            interfaces.push(el.id.replace('interface-', ''));
        });
        
        const features = [];
        document.querySelectorAll('[id^="feature-"]:checked').forEach(el => {
            features.push(el.id.replace('feature-', ''));
        });
        
        const config = {
            functions: functions,
            folderCount: document.getElementById('folder-count').value,
            codeOrganization: document.getElementById('code-organization').value,
            interfaces: interfaces,
            deployment: document.querySelector('input[name="deployment"]:checked')?.value,
            databaseType: document.getElementById('database-type').value,
            fileHandling: document.getElementById('file-handling').value,
            features: features,
            modelType: document.getElementById('model-type').value,
            performanceLevel: document.getElementById('performance-level').value
        };
        
        if (functions.length === 0) {
            alert('Please select at least one AI function');
            return;
        }
        
        if (!config.deployment) {
            alert('Please select how your AI will run');
            return;
        }
        
        // Show generation progress
        const progressHtml = `
            <div class="alert alert-info" id="generation-progress">
                <h5>MITO is analyzing your requirements...</h5>
                <div class="progress mb-2">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 0%"></div>
                </div>
                <div id="progress-status">Understanding project scope...</div>
            </div>
        `;
        
        const resultsDiv = document.getElementById('ai-factory-results') || this.createResultsDiv();
        resultsDiv.textContent = '';
        const progressDiv = this.createProgressDisplay(config);
        resultsDiv.appendChild(progressDiv);
        
        // Simulate GitHub Copilot-level analysis
        this.simulateIntelligentGeneration(config);
    }
    
    createResultsDiv() {
        const div = document.createElement('div');
        div.id = 'ai-factory-results';
        div.style.marginTop = '20px';
        document.querySelector('.ai-factory-section').appendChild(div);
        return div;
    }

    simulateIntelligentGeneration(config) {
        const stages = [
            { percent: 15, status: "Analyzing function requirements and dependencies..." },
            { percent: 25, status: "Determining optimal project architecture..." },
            { percent: 40, status: "Selecting best practices for " + config.deployment + " deployment..." },
            { percent: 55, status: "Generating intelligent code structure..." },
            { percent: 70, status: "Creating " + config.interfaces.join(', ') + " interfaces..." },
            { percent: 85, status: "Optimizing for " + config.performanceLevel + " performance..." },
            { percent: 100, status: "Finalizing intelligent AI application..." }
        ];
        
        let currentStage = 0;
        
        const updateProgress = () => {
            if (currentStage < stages.length) {
                const stage = stages[currentStage];
                const progressBar = document.querySelector('.progress-bar');
                const statusDiv = document.getElementById('progress-status');
                if (progressBar) progressBar.style.width = stage.percent + '%';
                if (statusDiv) statusDiv.textContent = stage.status;
                currentStage++;
                this.scheduleUpdate(updateProgress, 800);
            } else {
                // Generate the actual AI application
                this.generateIntelligentAI(config);
            }
        };
        
        updateProgress();
    }

    generateIntelligentAI(config) {
        // Create comprehensive project prompt like GitHub Copilot would understand
        const prompt = this.createIntelligentPrompt(config);
        
        fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: prompt,
                provider: 'llama'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.displayIntelligentResult(config, data.response);
            } else {
                this.displayError('Generation failed: ' + data.error);
            }
        })
        .catch(error => {
            this.displayError('Network error: ' + error.message);
        });
    }

    createIntelligentPrompt(config) {
        const functionsDesc = {
            'search': 'semantic search with vector embeddings and ranking algorithms',
            'chat': 'conversational AI with context awareness and intent recognition',
            'nlp': 'natural language processing with sentiment analysis and entity extraction',
            'image': 'computer vision with deep learning models for image analysis',
            'prediction': 'machine learning models for predictive analytics',
            'recommendations': 'recommendation engine with collaborative filtering',
            'data-analysis': 'advanced data analytics with statistical modeling',
            'automation': 'intelligent task automation with workflow management'
        };
        
        const selectedFunctions = config.functions.map(f => functionsDesc[f] || f).join(', ');
        
        let prompt = `Create a professional, production-ready AI application that rivals GitHub Copilot's intelligence level.

REQUIREMENTS:
- Functions: ${selectedFunctions}
- Architecture: ${config.codeOrganization} with ${config.folderCount} folder structure
- Deployment: ${config.deployment}
- Interfaces: ${config.interfaces.join(', ')}
- Database: ${config.databaseType !== 'none' ? config.databaseType : 'No database'}
- Performance: ${config.performanceLevel}
- Features: ${config.features.join(', ')}

Generate a complete, intelligent codebase that includes:

1. MAIN APPLICATION FILE with sophisticated AI logic
2. INTELLIGENT CONFIGURATION system
3. ROBUST ERROR HANDLING and logging
4. PERFORMANCE OPTIMIZATION
5. COMPREHENSIVE DOCUMENTATION
6. DEPLOYMENT INSTRUCTIONS

Make this as intelligent and capable as GitHub Copilot - understand context, provide smart suggestions, and anticipate developer needs.

Focus on practical, production-ready code that demonstrates advanced AI capabilities. Include detailed comments explaining the intelligent design decisions.

Structure the response as:
=== PROJECT STRUCTURE ===
[File/folder organization]

=== MAIN APPLICATION ===
[Complete main file with intelligent AI logic]

=== CONFIGURATION ===
[Smart configuration management]

=== REQUIREMENTS ===
[Dependencies and installation]

=== DEPLOYMENT ===
[Production deployment instructions]

=== DOCUMENTATION ===
[Comprehensive usage guide]`;

        return prompt;
    }

    displayIntelligentResult(config, response) {
        const resultHtml = `
            <div class="alert alert-success">
                <h5>Your Intelligent AI Application is Ready!</h5>
                <p>Generated with GitHub Copilot-level intelligence and best practices</p>
            </div>
            
            <div class="card mb-3">
                <div class="card-header">
                    <h6>Project Analysis</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Functions:</strong> ${config.functions.join(', ')}<br>
                            <strong>Architecture:</strong> ${config.codeOrganization}<br>
                            <strong>Deployment:</strong> ${config.deployment}
                        </div>
                        <div class="col-md-6">
                            <strong>Interfaces:</strong> ${config.interfaces.join(', ')}<br>
                            <strong>Database:</strong> ${config.databaseType}<br>
                            <strong>Performance:</strong> ${config.performanceLevel}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6>Generated Intelligent Code</h6>
                    <div>
                        <button class="btn btn-sm btn-outline-primary" onclick="workbench.copyToClipboard('generated-code')">Copy All</button>
                        <button class="btn btn-sm btn-success" onclick="workbench.downloadProject()">Download Project</button>
                    </div>
                </div>
                <div class="card-body">
                    <pre id="generated-code" style="max-height: 500px; overflow-y: auto; background: #f8f9fa; padding: 15px; border-radius: 4px;"><code>${this.escapeHtml(response)}</code></pre>
                </div>
            </div>
        `;
        
        const resultsDiv = document.getElementById('ai-factory-results');
        if (resultsDiv) {
            resultsDiv.textContent = '';
            const resultContainer = this.createResultDisplay(data);
            resultsDiv.appendChild(resultContainer);
        }
    }

    generateQuickTemplate(type) {
        const templates = {
            'terminal': {
                functions: ['nlp'],
                deployment: 'script',
                interfaces: ['terminal'],
                description: 'Command-line AI tool'
            },
            'web': {
                functions: ['chat', 'nlp'],
                deployment: 'server',
                interfaces: ['web', 'api'],
                description: 'Web-based AI application'
            },
            'api': {
                functions: ['search', 'nlp'],
                deployment: 'server',
                interfaces: ['api'],
                description: 'REST API service'
            },
            'complete': {
                functions: ['search', 'chat', 'nlp', 'recommendations'],
                deployment: 'server',
                interfaces: ['web', 'api', 'terminal', 'dashboard'],
                description: 'Full-featured AI platform'
            }
        };
        
        const template = templates[type];
        if (!template) return;
        
        // Set the form values
        template.functions.forEach(func => {
            const checkbox = document.getElementById('func-' + func);
            if (checkbox) checkbox.checked = true;
        });
        
        template.interfaces.forEach(iface => {
            const checkbox = document.getElementById('interface-' + iface);
            if (checkbox) checkbox.checked = true;
        });
        
        const deploymentRadio = document.querySelector(`input[name="deployment"][value="${template.deployment}"]`);
        if (deploymentRadio) deploymentRadio.checked = true;
        
        // Set defaults for quick generation
        const folderCount = document.getElementById('folder-count');
        const codeOrg = document.getElementById('code-organization');
        const dbType = document.getElementById('database-type');
        const modelType = document.getElementById('model-type');
        const perfLevel = document.getElementById('performance-level');
        
        if (folderCount) folderCount.value = 'modular';
        if (codeOrg) codeOrg.value = 'oop';
        if (dbType) dbType.value = 'sqlite';
        if (modelType) modelType.value = 'hybrid';
        if (perfLevel) perfLevel.value = 'balanced';
        
        // Generate immediately
        this.generateCustomAI();
    }

    copyToClipboard(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const text = element.textContent;
        
        navigator.clipboard.writeText(text).then(() => {
            alert('Code copied to clipboard!');
        }).catch(() => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            alert('Code copied to clipboard!');
        });
    }

    downloadProject() {
        const codeElement = document.getElementById('generated-code');
        if (!codeElement) return;
        
        const code = codeElement.textContent;
        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'intelligent-ai-project.py';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    displayError(message) {
        const errorHtml = `
            <div class="alert alert-danger">
                <h6>Generation Error</h6>
                <p>${message}</p>
                <button class="btn btn-outline-danger btn-sm" onclick="location.reload()">Retry</button>
            </div>
        `;
        
        const resultsDiv = document.getElementById('ai-factory-results');
        if (resultsDiv) {
            resultsDiv.textContent = '';
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-container';
            const errorTitle = document.createElement('h3');
            errorTitle.textContent = 'Generation Failed';
            const errorMsg = document.createElement('p');
            errorMsg.textContent = `Error: ${error.message}`;
            errorDiv.appendChild(errorTitle);
            errorDiv.appendChild(errorMsg);
            resultsDiv.appendChild(errorDiv);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.textContent;
    }

    // Phase Management System
    initPhaseManager() {
        this.currentProject = {
            name: 'AI Search Engine',
            currentPhase: 2,
            totalPhases: 6,
            phases: [
                {
                    id: 1,
                    name: 'Planning & Requirements',
                    status: 'completed',
                    progress: 100,
                    tasks: [
                        { name: 'Define project scope', completed: true },
                        { name: 'Gather requirements', completed: true },
                        { name: 'Create specifications', completed: true }
                    ]
                },
                {
                    id: 2,
                    name: 'Architecture Design',
                    status: 'active',
                    progress: 60,
                    tasks: [
                        { name: 'Define data models', completed: true },
                        { name: 'Design API endpoints', completed: true },
                        { name: 'Choose database schema', completed: true },
                        { name: 'Set up vector embeddings', completed: false },
                        { name: 'Configure search algorithms', completed: false }
                    ]
                },
                {
                    id: 3,
                    name: 'Core Development',
                    status: 'pending',
                    progress: 0,
                    tasks: [
                        { name: 'Build main application logic', completed: false },
                        { name: 'Implement search functionality', completed: false },
                        { name: 'Create data processing pipeline', completed: false }
                    ]
                },
                {
                    id: 4,
                    name: 'Interface Development',
                    status: 'pending',
                    progress: 0,
                    tasks: [
                        { name: 'Create user interface', completed: false },
                        { name: 'Build API endpoints', completed: false },
                        { name: 'Develop admin dashboard', completed: false }
                    ]
                },
                {
                    id: 5,
                    name: 'Testing & Optimization',
                    status: 'pending',
                    progress: 0,
                    tasks: [
                        { name: 'Run unit tests', completed: false },
                        { name: 'Performance optimization', completed: false },
                        { name: 'Bug fixes', completed: false }
                    ]
                },
                {
                    id: 6,
                    name: 'Deployment & Documentation',
                    status: 'pending',
                    progress: 0,
                    tasks: [
                        { name: 'Deploy to production', completed: false },
                        { name: 'Create documentation', completed: false },
                        { name: 'Final testing', completed: false }
                    ]
                }
            ]
        };
    }

    updatePhaseDisplay() {
        const overallProgress = Math.round((this.currentProject.currentPhase - 1) / this.currentProject.totalPhases * 100);
        document.getElementById('overall-progress').style.width = overallProgress + '%';
        document.getElementById('overall-progress').textContent = `Phase ${this.currentProject.currentPhase} of ${this.currentProject.totalPhases} (${overallProgress}%)`;
        
        document.getElementById('current-project-name').textContent = this.currentProject.name;
    }

        // Deploy project
        const deployBtn = document.getElementById('deploy-button');
        if (deployBtn) {
            deployBtn.addEventListener('click', () => this.deployProject());
        }

        // Chat functionality
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-message');
        
        if (chatInput && sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // Settings button
        const settingsBtn = document.getElementById('settings-btn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                window.open('/settings', '_blank');
            });
        }

        // Workbench actions
        document.querySelector('.action-btn.primary').addEventListener('click', () => {
            this.showNotification('Deploy functionality ready', 'success');
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content areas
        document.querySelectorAll('.content-area').forEach(area => {
            area.classList.remove('active');
        });
        document.getElementById(`${tabName}-content`).classList.add('active');

        this.activeTab = tabName;
        this.logActivity(`Switched to ${tabName} tab`);
    }

    selectProjectType(type) {
        document.querySelectorAll('.project-type').forEach(el => {
            el.classList.remove('active');
        });
        document.querySelector(`[data-type="${type}"]`).classList.add('active');
        
        this.selectedProjectType = type;
        this.updateTechStackOptions(type);
        this.logActivity(`Selected project type: ${type}`);
    }

    selectTechStack(stack) {
        document.querySelectorAll('.tech-option').forEach(el => {
            el.classList.remove('selected');
        });
        document.querySelector(`[data-stack="${stack}"]`).classList.add('selected');
        
        this.selectedTechStack = stack;
        this.logActivity(`Selected tech stack: ${stack}`);
    }

    updateTechStackOptions(type) {
        const techGrid = document.getElementById('tech-stack');
        const stacks = {
            webapp: [
                { stack: 'react', name: 'React + Node.js', desc: 'Modern web application' },
                { stack: 'vue', name: 'Vue.js + Express', desc: 'Progressive web app' },
                { stack: 'python', name: 'Python + Flask', desc: 'Backend-focused app' },
                { stack: 'nextjs', name: 'Next.js', desc: 'Full-stack React framework' }
            ],
            api: [
                { stack: 'node', name: 'Node.js + Express', desc: 'JavaScript API server' },
                { stack: 'python', name: 'Python + FastAPI', desc: 'High-performance API' },
                { stack: 'java', name: 'Java + Spring Boot', desc: 'Enterprise-grade API' },
                { stack: 'go', name: 'Go + Gin', desc: 'Fast, lightweight API' }
            ],
            mobile: [
                { stack: 'react-native', name: 'React Native', desc: 'Cross-platform mobile' },
                { stack: 'flutter', name: 'Flutter', desc: 'Google mobile framework' },
                { stack: 'ionic', name: 'Ionic', desc: 'Hybrid mobile apps' },
                { stack: 'native', name: 'Native Development', desc: 'iOS/Android native' }
            ],
            desktop: [
                { stack: 'electron', name: 'Electron', desc: 'Cross-platform desktop' },
                { stack: 'tauri', name: 'Tauri', desc: 'Rust-based desktop' },
                { stack: 'qt', name: 'Qt', desc: 'Native desktop apps' },
                { stack: 'wpf', name: 'WPF', desc: 'Windows desktop apps' }
            ],
            game: [
                { stack: 'unity', name: 'Unity', desc: '3D/2D game engine' },
                { stack: 'unreal', name: 'Unreal Engine', desc: 'AAA game development' },
                { stack: 'godot', name: 'Godot', desc: 'Open-source game engine' },
                { stack: 'web', name: 'Web Games', desc: 'JavaScript/WebGL games' }
            ],
            ai: [
                { stack: 'tensorflow', name: 'TensorFlow', desc: 'Machine learning platform' },
                { stack: 'pytorch', name: 'PyTorch', desc: 'Deep learning framework' },
                { stack: 'huggingface', name: 'Hugging Face', desc: 'NLP and transformers' },
                { stack: 'openai', name: 'OpenAI Integration', desc: 'GPT and AI models' }
            ]
        };

        if (stacks[type]) {
            techGrid.textContent = '';
            stacks[type].forEach(tech => {
                const techOption = this.createTechOption(tech);
                techGrid.appendChild(techOption);
            });
            `).join('');

            // Re-attach event listeners
            document.querySelectorAll('.tech-option').forEach(option => {
                option.addEventListener('click', (e) => {
                    this.selectTechStack(e.target.closest('.tech-option').dataset.stack);
                });
            });
        }
    }

    async buildProject() {
        const name = document.getElementById('project-name').value.trim();
        const description = document.getElementById('project-description').value.trim();

        if (!name || !description) {
            this.showNotification('Please fill in all fields', 'error');
            return;
        }

        const buildBtn = document.getElementById('build-project');
        buildBtn.disabled = true;
        buildBtn.textContent = 'Building Project...';

        this.updateBuildProgress('Initializing project...', 10);
        this.logActivity(`Started building: ${name}`);

        try {
            // Set timeout for long-running AI generation
            const controller = new AbortController();
            const timeoutId = this.createSecureTimeout(() => controller.abort(), 60000); // 60 second timeout

            const response = await fetch('/api/create-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name,
                    description,
                    type: this.selectedProjectType,
                    tech_stack: this.selectedTechStack
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Network error' }));
                throw new Error(errorData.error || `Server error: ${response.status}`);
            }

            const data = await response.json();

            this.updateBuildProgress('AI generating file structure...', 30);
            await this.delay(500);

            this.updateBuildProgress('Creating configuration files...', 60);
            await this.delay(500);

            this.updateBuildProgress('Generating documentation...', 80);
            await this.delay(500);

            this.updateBuildProgress('Project created successfully!', 100);
            
            this.currentProject = data.project;
            this.showNotification('Project built successfully!', 'success');
            this.logActivity(`Project "${name}" created successfully`);
            
            // Add to recent projects
            this.addToRecentProjects(data.project);
            
            // Reset form
            document.getElementById('project-name').value = '';
            document.getElementById('project-description').value = '';

        } catch (error) {
            console.error('Build error:', error);
            let errorMessage = error.message;
            
            if (error.name === 'AbortError') {
                errorMessage = 'Project creation timed out. Please try again with a simpler description.';
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Network connection failed. Please check your connection and try again.';
            }
            
            this.updateBuildProgress(`Error: ${errorMessage}`, 0);
            this.showNotification(`Build failed: ${errorMessage}`, 'error');
            this.logActivity(`Build failed: ${errorMessage}`);
        } finally {
            buildBtn.disabled = false;
            buildBtn.textContent = 'Build Complete Project';
        }
    }

    async generateCode() {
        const prompt = document.getElementById('code-prompt').value.trim();
        const language = document.getElementById('language-select').value;

        if (!prompt) {
            this.showNotification('Please describe the code you need', 'error');
            return;
        }

        const generateBtn = document.getElementById('generate-code');
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';

        this.logActivity(`Generating ${language} code: ${prompt.substring(0, 50)}...`);

        try {
            const response = await fetch('/api/generate-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt,
                    language
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate code');
            }

            // Display generated code
            document.getElementById('generated-code').textContent = data.code;
            
            // Display file structure
            this.displayFileStructure(data.file_structure);

            this.showNotification('Code generated successfully!', 'success');
            this.logActivity('Code generation completed');

        } catch (error) {
            console.error('Generation error:', error);
            document.getElementById('generated-code').textContent = `Error: ${error.message}`;
            this.showNotification(`Code generation failed: ${error.message}`, 'error');
            this.logActivity(`Code generation failed: ${error.message}`);
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate';
        }
    }

    displayFileStructure(structure) {
        const fileTree = document.getElementById('file-structure');
        if (!structure || !Array.isArray(structure)) {
            fileTree.textContent = 'No file structure available';
            return;
        }

        let output = '';
        structure.forEach(item => {
            if (item.type === 'folder') {
                output += `📁 ${item.name}/\n`;
                if (item.children) {
                    item.children.forEach(child => {
                        output += `  └── 📄 ${child.name}\n`;
                    });
                }
            } else {
                output += `📄 ${item.name}\n`;
            }
        });

        fileTree.textContent = output;
    }

    async deployProject() {
        const projectSelect = document.getElementById('deploy-project-select');
        const projectId = projectSelect.value;

        if (!projectId) {
            this.showNotification('Please select a project to deploy', 'error');
            return;
        }

        const deployBtn = document.getElementById('deploy-button');
        deployBtn.disabled = true;
        deployBtn.textContent = 'Deploying...';

        this.logActivity(`Deploying project: ${projectId}`);

        try {
            const response = await fetch('/api/deploy-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: projectId
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Deployment failed');
            }

            this.showNotification('Project deployed successfully!', 'success');
            this.logActivity(`Deployment completed: ${data.deployment_url}`);

        } catch (error) {
            console.error('Deployment error:', error);
            this.showNotification(`Deployment failed: ${error.message}`, 'error');
            this.logActivity(`Deployment failed: ${error.message}`);
        } finally {
            deployBtn.disabled = false;
            deployBtn.textContent = 'Deploy to Production';
        }
    }

    initializeChat() {
        // Add chat interface to output panel if not exists
        const outputPanel = document.querySelector('.output-panel .panel-content');
        if (outputPanel && !document.getElementById('mito-chat')) {
            const chatSection = document.createElement('div');
            chatSection.className = 'output-section';
            chatSection.id = 'mito-chat';
            chatSection.textContent = '';
            const chatContainer = this.createChatInterface();
                <div class="section-title">Chat with MITO</div>
                <div class="chat-messages" id="chat-messages" style="max-height: 200px; overflow-y: auto; margin-bottom: 1rem; padding: 0.5rem; background: var(--bg-primary); border-radius: 6px; font-size: 0.875rem;"></div>
                <div style="display: flex; gap: 0.5rem;">
                    <input type="text" id="chat-input" placeholder="Ask MITO anything..." style="flex: 1; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 4px; padding: 0.5rem; color: var(--text-primary); font-size: 0.875rem;">
                    <button id="send-message" style="background: var(--accent); color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; font-size: 0.875rem;">Send</button>
                </div>
            `;
            outputPanel.appendChild(chatSection);

            // Add initial message
            this.addChatMessage('MITO', 'Hello! I\'m MITO, your AI development assistant. Ask me anything about your projects, code, or development needs.', 'assistant');

            // Reattach event listeners
            this.setupEventListeners();
        }
    }

    async sendMessage() {
        const chatInput = document.getElementById('chat-input');
        const message = chatInput.value.trim();

        if (!message) return;

        // Add user message
        this.addChatMessage('You', message, 'user');
        chatInput.value = '';

        // Show typing indicator
        this.addChatMessage('MITO', 'Thinking...', 'assistant', true);

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: `As MITO, a helpful AI development assistant, respond to: ${message}`,
                    provider: 'local'
                })
            });

            const data = await response.json();

            // Remove typing indicator
            const messages = document.getElementById('chat-messages');
            const lastMessage = messages.lastElementChild;
            if (lastMessage && lastMessage.classList.contains('typing')) {
                messages.removeChild(lastMessage);
            }

            if (response.ok) {
                this.addChatMessage('MITO', data.response, 'assistant');
            } else {
                this.addChatMessage('MITO', 'Sorry, I encountered an error. Please try again.', 'assistant');
            }

        } catch (error) {
            console.error('Chat error:', error);
            this.addChatMessage('MITO', 'Sorry, I\'m having trouble connecting. Please try again.', 'assistant');
        }
    }

    addChatMessage(sender, message, type, isTyping = false) {
        const messages = document.getElementById('chat-messages');
        if (!messages) return;

        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${type} ${isTyping ? 'typing' : ''}`;
        messageEl.textContent = '';
        const messageContent = this.createMessageDisplay(type, content, timestamp);
        messageEl.appendChild(messageContent);
        messageEl.style.marginBottom = '1rem';
        messageEl.style.padding = '0.5rem';
        messageEl.style.background = type === 'user' ? 'rgba(31, 111, 235, 0.1)' : 'rgba(35, 134, 54, 0.1)';
        messageEl.style.borderRadius = '6px';
        messageEl.style.borderLeft = `3px solid ${type === 'user' ? 'var(--blue)' : 'var(--accent)'}`;

        messages.appendChild(messageEl);
        messages.scrollTop = messages.scrollHeight;
    }

    updateBuildProgress(message, percentage) {
        const progressEl = document.getElementById('build-progress');
        if (progressEl) {
            progressEl.textContent = '';
            const progressContent = this.createProgressContent(message, percentage);
            progressEl.appendChild(progressContent);
        }
    }

    logActivity(message) {
        const activityLog = document.getElementById('activity-log');
        if (activityLog) {
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.style.fontSize = '0.75rem';
            logEntry.style.color = 'var(--text-muted)';
            logEntry.style.marginBottom = '0.5rem';
            logEntry.textContent = '';
            const timestampSpan = document.createElement('span');
            timestampSpan.style.color = 'var(--accent)';
            timestampSpan.textContent = timestamp;
            logEntry.appendChild(timestampSpan);
            logEntry.appendChild(document.createTextNode(' ' + message));
            
            activityLog.appendChild(logEntry);
            
            // Keep only last 5 entries
            const entries = activityLog.children;
            if (entries.length > 5) {
                activityLog.removeChild(entries[0]);
            }
        }
    }

    async loadRecentProjects() {
        try {
            const response = await fetch('/api/projects');
            const data = await response.json();

            if (response.ok && data.projects) {
                this.displayRecentProjects(data.projects);
                this.populateDeploySelect(data.projects);
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }

    displayRecentProjects(projects) {
        const projectsList = document.getElementById('recent-projects');
        if (!projectsList) return;

        if (projects.length === 0) {
            projectsList.textContent = '';
            const emptyDiv = document.createElement('div');
            emptyDiv.style.color = 'var(--text-muted)';
            emptyDiv.style.fontSize = '0.875rem';
            emptyDiv.textContent = 'No projects yet';
            projectsList.appendChild(emptyDiv);
            return;
        }

        projectsList.textContent = '';
        projects.slice(0, 5).forEach(project => {
            const projectItem = this.createRecentProjectItem(project);
            projectsList.appendChild(projectItem);
        });
        `).join('');
    }

    populateDeploySelect(projects) {
        const deploySelect = document.getElementById('deploy-project-select');
        if (!deploySelect) return;

        deploySelect.textContent = '';
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Choose a project to deploy...';
        deploySelect.appendChild(defaultOption);
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = `${project.name} (${project.tech_stack})`;
            deploySelect.appendChild(option);
        });

        deploySelect.addEventListener('change', (e) => {
            const deployBtn = document.getElementById('deploy-button');
            deployBtn.disabled = !e.target.value;
        });
    }

    addToRecentProjects(project) {
        const projectsList = document.getElementById('recent-projects');
        if (!projectsList) return;

        const projectItem = document.createElement('div');
        projectItem.className = 'project-item';
        projectItem.textContent = '';
        const projectContent = this.createDeploymentProjectContent(project);
        projectItem.appendChild(projectContent);
        
        projectsList.insertBefore(projectItem, projectsList.firstChild);
        
        // Keep only 5 recent projects
        const items = projectsList.children;
        if (items.length > 5) {
            projectsList.removeChild(items[items.length - 1]);
        }

        // Update deploy select
        const deploySelect = document.getElementById('deploy-project-select');
        if (deploySelect) {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = `${project.name} (${project.tech_stack})`;
            deploySelect.insertBefore(option, deploySelect.children[1]);
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            font-size: 0.875rem;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--blue)'};
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    delay(ms) {
        return new Promise(resolve => this.createSecureTimeout(resolve, ms));
    }

    // Security helper methods
    createSecureTimeout(callback, delay) {
        return setTimeout(callback, delay);
    }

    scheduleUpdate(callback, delay) {
        return setTimeout(callback, delay);
    }

    scheduleNotificationRemoval(element, callback) {
        return setTimeout(callback, 3000);
    }

    createProgressDisplay(config) {
        const progressDiv = document.createElement('div');
        progressDiv.className = 'progress-display';
        
        const title = document.createElement('h3');
        title.textContent = 'Generating AI Application...';
        progressDiv.appendChild(title);
        
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        progressBar.id = 'generation-progress';
        progressBar.style.cssText = 'background: var(--bg-primary); border-radius: 4px; overflow: hidden; height: 6px; margin: 1rem 0;';
        
        const progressFill = document.createElement('div');
        progressFill.style.cssText = 'background: var(--accent); height: 100%; width: 0%; transition: width 0.3s ease;';
        progressBar.appendChild(progressFill);
        progressDiv.appendChild(progressBar);
        
        const statusDiv = document.createElement('div');
        statusDiv.id = 'progress-status';
        statusDiv.style.cssText = 'color: var(--text-muted); font-size: 0.875rem;';
        statusDiv.textContent = 'Initializing...';
        progressDiv.appendChild(statusDiv);
        
        return progressDiv;
    }

    createResultDisplay(data) {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'result-display';
        
        const title = document.createElement('h3');
        title.textContent = 'AI Application Generated Successfully!';
        title.style.color = 'var(--success)';
        resultDiv.appendChild(title);
        
        const description = document.createElement('p');
        description.textContent = `Generated ${data.type || 'application'} with ${data.features || 'advanced features'}`;
        resultDiv.appendChild(description);
        
        return resultDiv;
    }

    createTechOption(tech) {
        const techDiv = document.createElement('div');
        techDiv.className = `tech-option ${tech.stack === 'react' ? 'selected' : ''}`;
        techDiv.setAttribute('data-stack', tech.stack);
        
        const nameDiv = document.createElement('div');
        nameDiv.className = 'tech-name';
        nameDiv.textContent = tech.name;
        techDiv.appendChild(nameDiv);
        
        const descDiv = document.createElement('div');
        descDiv.className = 'tech-desc';
        descDiv.textContent = tech.desc;
        techDiv.appendChild(descDiv);
        
        return techDiv;
    }

    createChatInterface() {
        const chatContainer = document.createElement('div');
        chatContainer.innerHTML = `
            <div class="section-title">Chat with MITO</div>
            <div class="chat-messages" id="chat-messages" style="max-height: 200px; overflow-y: auto; margin-bottom: 1rem; padding: 0.5rem; background: var(--bg-primary); border-radius: 6px; font-size: 0.875rem;"></div>
            <div style="display: flex; gap: 0.5rem;">
                <input type="text" id="chat-input" placeholder="Ask MITO anything..." style="flex: 1; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 4px; padding: 0.5rem; color: var(--text-primary); font-size: 0.875rem;">
                <button id="chat-send" style="background: var(--accent); color: white; border: none; border-radius: 4px; padding: 0.5rem 1rem; cursor: pointer; font-size: 0.875rem;">Send</button>
            </div>
        `;
        return chatContainer;
    }

    createMessageDisplay(type, content, timestamp) {
        const messageDiv = document.createElement('div');
        const sender = type === 'user' ? 'You' : 'MITO';
        const message = content;
        
        const senderDiv = document.createElement('div');
        senderDiv.style.cssText = `font-weight: 500; color: ${type === 'user' ? 'var(--blue)' : 'var(--accent)'}; margin-bottom: 0.25rem; font-size: 0.75rem;`;
        senderDiv.textContent = sender;
        messageDiv.appendChild(senderDiv);
        
        const contentDiv = document.createElement('div');
        contentDiv.style.cssText = 'color: var(--text-primary); line-height: 1.4;';
        contentDiv.textContent = message;
        messageDiv.appendChild(contentDiv);
        
        return messageDiv;
    }

    createProgressContent(message, percentage) {
        const progressDiv = document.createElement('div');
        
        const messageDiv = document.createElement('div');
        messageDiv.style.cssText = 'margin-bottom: 0.5rem; color: var(--text-primary);';
        messageDiv.textContent = message;
        progressDiv.appendChild(messageDiv);
        
        const barContainer = document.createElement('div');
        barContainer.style.cssText = 'background: var(--bg-primary); border-radius: 4px; overflow: hidden; height: 6px;';
        
        const barFill = document.createElement('div');
        barFill.style.cssText = `background: var(--accent); height: 100%; width: ${percentage}%; transition: width 0.3s ease;`;
        barContainer.appendChild(barFill);
        progressDiv.appendChild(barContainer);
        
        return progressDiv;
    }

    createTechOption(tech) {
        const techOption = document.createElement('div');
        techOption.className = `tech-option ${tech.stack === 'react' ? 'selected' : ''}`;
        techOption.setAttribute('data-stack', tech.stack);
        
        const techName = document.createElement('div');
        techName.className = 'tech-name';
        techName.textContent = tech.name;
        techOption.appendChild(techName);
        
        const techDesc = document.createElement('div');
        techDesc.className = 'tech-desc';
        techDesc.textContent = tech.desc;
        techOption.appendChild(techDesc);
        
        return techOption;
    }

    createChatInterface() {
        const chatContainer = document.createElement('div');
        
        const title = document.createElement('div');
        title.className = 'section-title';
        title.textContent = 'Chat with MITO';
        chatContainer.appendChild(title);
        
        const messagesDiv = document.createElement('div');
        messagesDiv.className = 'chat-messages';
        messagesDiv.id = 'chat-messages';
        messagesDiv.style.cssText = 'max-height: 200px; overflow-y: auto; margin-bottom: 1rem; padding: 0.5rem; background: var(--bg-primary); border-radius: 6px; font-size: 0.875rem;';
        chatContainer.appendChild(messagesDiv);
        
        const inputContainer = document.createElement('div');
        inputContainer.style.cssText = 'display: flex; gap: 0.5rem;';
        
        const chatInput = document.createElement('input');
        chatInput.type = 'text';
        chatInput.id = 'chat-input';
        chatInput.placeholder = 'Ask MITO anything...';
        chatInput.style.cssText = 'flex: 1; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 4px; padding: 0.5rem; color: var(--text-primary); font-size: 0.875rem;';
        inputContainer.appendChild(chatInput);
        
        const sendButton = document.createElement('button');
        sendButton.id = 'chat-send';
        sendButton.textContent = 'Send';
        sendButton.style.cssText = 'background: var(--accent); color: white; border: none; border-radius: 4px; padding: 0.5rem 1rem; cursor: pointer; font-size: 0.875rem;';
        inputContainer.appendChild(sendButton);
        
        chatContainer.appendChild(inputContainer);
        
        return chatContainer;
    }

    createRecentProjectItem(project) {
        const projectItem = document.createElement('div');
        projectItem.className = 'project-item';
        
        const projectName = document.createElement('div');
        projectName.className = 'project-name';
        projectName.textContent = project.name;
        projectItem.appendChild(projectName);
        
        const projectMeta = document.createElement('div');
        projectMeta.className = 'project-meta';
        projectMeta.textContent = `${project.tech_stack} • ${new Date(project.created_at).toLocaleDateString()}`;
        projectItem.appendChild(projectMeta);
        
        return projectItem;
    }

    createDeploymentProjectContent(project) {
        const projectContent = document.createElement('div');
        
        const projectName = document.createElement('div');
        projectName.className = 'project-name';
        projectName.textContent = project.name;
        projectContent.appendChild(projectName);
        
        const projectMeta = document.createElement('div');
        projectMeta.className = 'project-meta';
        projectMeta.textContent = `${project.tech_stack} • Just now`;
        projectContent.appendChild(projectMeta);
        
        return projectContent;
    }

    createRecentProjectItem(project) {
        const projectDiv = document.createElement('div');
        projectDiv.className = 'project-item';
        
        const nameDiv = document.createElement('div');
        nameDiv.className = 'project-name';
        nameDiv.textContent = project.name;
        projectDiv.appendChild(nameDiv);
        
        const metaDiv = document.createElement('div');
        metaDiv.className = 'project-meta';
        metaDiv.textContent = `${project.tech_stack} • ${new Date(project.created_at).toLocaleDateString()}`;
        projectDiv.appendChild(metaDiv);
        
        return projectDiv;
    }

    createDeploymentProjectContent(project) {
        const projectDiv = document.createElement('div');
        
        const nameDiv = document.createElement('div');
        nameDiv.className = 'project-name';
        nameDiv.textContent = project.name;
        projectDiv.appendChild(nameDiv);
        
        const metaDiv = document.createElement('div');
        metaDiv.className = 'project-meta';
        metaDiv.textContent = `${project.tech_stack} • Just now`;
        projectDiv.appendChild(metaDiv);
        
        return projectDiv;
    }
}

// Initialize workbench when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MitoWorkbench();
});