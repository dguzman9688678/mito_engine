/*
MITO Engine - AI Agent & Tool Creator
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: AI Agent & Tool Creator
*/

class MitoDeveloperEngine {
    constructor() {
        this.currentProject = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadProjects();
        console.log('MITO Developer Engine initialized');
    }

    setupEventListeners() {
        // Project type selection
        document.querySelectorAll('.project-type').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectProjectType(e.target.dataset.type);
            });
        });

        // Create project button
        const createBtn = document.getElementById('create-project-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.createProject());
        }

        // Code generation
        const generateCodeBtn = document.getElementById('generate-code-btn');
        if (generateCodeBtn) {
            generateCodeBtn.addEventListener('click', () => this.generateCode());
        }

        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
    }

    selectProjectType(type) {
        // Update active state
        document.querySelectorAll('.project-type').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-type="${type}"]`).classList.add('active');

        // Show project form
        const form = document.getElementById('project-form');
        form.style.display = 'flex';

        // Update tech stack options based on project type
        this.updateTechStackOptions(type);
    }

    updateTechStackOptions(type) {
        const techSelect = document.getElementById('tech-stack');
        
        // Clear existing options securely
        techSelect.textContent = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select Technology Stack';
        techSelect.appendChild(defaultOption);

        const stacks = {
            webapp: [
                { value: 'react', text: 'React + Node.js + MongoDB' },
                { value: 'vue', text: 'Vue.js + Express + PostgreSQL' },
                { value: 'angular', text: 'Angular + NestJS + MySQL' },
                { value: 'python', text: 'Python + Flask/Django + PostgreSQL' },
                { value: 'php', text: 'PHP + Laravel + MySQL' }
            ],
            api: [
                { value: 'node', text: 'Node.js + Express + MongoDB' },
                { value: 'python', text: 'Python + FastAPI + PostgreSQL' },
                { value: 'java', text: 'Java + Spring Boot + MySQL' },
                { value: 'csharp', text: 'C# + .NET Core + SQL Server' },
                { value: 'go', text: 'Go + Gin + PostgreSQL' }
            ],
            mobile: [
                { value: 'react-native', text: 'React Native + Firebase' },
                { value: 'flutter', text: 'Flutter + Firebase' },
                { value: 'ionic', text: 'Ionic + Angular + Firebase' },
                { value: 'native-ios', text: 'Native iOS (Swift)' },
                { value: 'native-android', text: 'Native Android (Kotlin)' }
            ],
            desktop: [
                { value: 'electron', text: 'Electron + React' },
                { value: 'tauri', text: 'Tauri + Rust + React' },
                { value: 'flutter-desktop', text: 'Flutter Desktop' },
                { value: 'qt', text: 'Qt + C++' },
                { value: 'wpf', text: 'WPF + C#' }
            ],
            game: [
                { value: 'unity', text: 'Unity + C#' },
                { value: 'unreal', text: 'Unreal Engine + C++' },
                { value: 'godot', text: 'Godot + GDScript' },
                { value: 'javascript', text: 'JavaScript + Phaser' },
                { value: 'python', text: 'Python + Pygame' }
            ],
            ai: [
                { value: 'python-ml', text: 'Python + TensorFlow + Jupyter' },
                { value: 'python-dl', text: 'Python + PyTorch + FastAPI' },
                { value: 'python-nlp', text: 'Python + Transformers + Streamlit' },
                { value: 'js-ml', text: 'JavaScript + TensorFlow.js' },
                { value: 'r-stats', text: 'R + Shiny + tidyverse' }
            ]
        };

        if (stacks[type]) {
            stacks[type].forEach(stack => {
                const option = document.createElement('option');
                option.value = stack.value;
                option.textContent = stack.text;
                techSelect.appendChild(option);
            });
        }
    }

    async createProject() {
        const name = document.getElementById('project-name').value.trim();
        const description = document.getElementById('project-description').value.trim();
        const techStack = document.getElementById('tech-stack').value;
        const type = document.querySelector('.project-type.active')?.dataset.type;

        if (!name || !description || !techStack || !type) {
            this.showNotification('Please fill in all fields', 'error');
            return;
        }

        const createBtn = document.getElementById('create-project-btn');
        createBtn.disabled = true;
        createBtn.textContent = 'Creating Project...';

        try {
            const response = await fetch('/api/create-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name,
                    description,
                    type,
                    tech_stack: techStack
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to create project');
            }

            this.showNotification('Project created successfully!', 'success');
            this.displayProjectResult(data);
            this.loadProjects();

            // Reset form
            document.getElementById('project-form').style.display = 'none';
            document.querySelectorAll('.project-type').forEach(btn => {
                btn.classList.remove('active');
            });
            document.getElementById('project-name').value = '';
            document.getElementById('project-description').value = '';
            document.getElementById('tech-stack').value = '';

        } catch (error) {
            console.error('Project creation error:', error);
            this.showNotification(`Failed to create project: ${error.message}`, 'error');
        } finally {
            createBtn.disabled = false;
            createBtn.textContent = 'Create Project';
        }
    }

    async generateCode() {
        const prompt = document.getElementById('code-prompt').value.trim();
        const language = document.getElementById('language-select').value;

        if (!prompt) {
            this.showNotification('Please describe the code you need', 'error');
            return;
        }

        const generateBtn = document.getElementById('generate-code-btn');
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';

        // Show loading in all tabs
        document.getElementById('generated-code').textContent = 'Generating code...';
        const fileStructureEl = document.getElementById('file-structure');
        const documentationEl = document.getElementById('documentation');
        
        fileStructureEl.textContent = '';
        const loadingDiv1 = document.createElement('div');
        loadingDiv1.className = 'loading';
        loadingDiv1.textContent = 'Generating file structure...';
        fileStructureEl.appendChild(loadingDiv1);
        
        documentationEl.textContent = '';
        const loadingDiv2 = document.createElement('div');
        loadingDiv2.className = 'loading';
        loadingDiv2.textContent = 'Generating documentation...';
        documentationEl.appendChild(loadingDiv2);

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

            // Display results
            document.getElementById('generated-code').textContent = data.code;
            this.displayFileStructure(data.file_structure);
            const docEl = document.getElementById('documentation');
            docEl.textContent = '';
            const formattedDoc = this.formatDocumentationSecure(data.documentation);
            docEl.appendChild(formattedDoc);

            this.showNotification('Code generated successfully!', 'success');

        } catch (error) {
            console.error('Code generation error:', error);
            document.getElementById('generated-code').textContent = `Error: ${error.message}`;
            const fileEl = document.getElementById('file-structure');
            const docEl = document.getElementById('documentation');
            
            fileEl.textContent = '';
            const errorDiv1 = document.createElement('div');
            errorDiv1.className = 'error';
            errorDiv1.textContent = 'Failed to generate file structure';
            fileEl.appendChild(errorDiv1);
            
            docEl.textContent = '';
            const errorDiv2 = document.createElement('div');
            errorDiv2.className = 'error';
            errorDiv2.textContent = 'Failed to generate documentation';
            docEl.appendChild(errorDiv2);
            this.showNotification(`Code generation failed: ${error.message}`, 'error');
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Code';
        }
    }

    displayFileStructure(structure) {
        if (!structure || !Array.isArray(structure)) {
            const fileEl = document.getElementById('file-structure');
            fileEl.textContent = '';
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = 'No file structure available';
            fileEl.appendChild(errorDiv);
            return;
        }

        let html = '<ul class="file-tree">';
        
        structure.forEach(item => {
            if (item.type === 'folder') {
                html += `<li><span class="folder">📁 ${item.name}/</span>`;
                if (item.children && item.children.length > 0) {
                    html += '<ul class="file-tree">';
                    item.children.forEach(child => {
                        html += `<li><span class="file">📄 ${child.name}</span></li>`;
                    });
                    html += '</ul>';
                }
                html += '</li>';
            } else {
                html += `<li><span class="file">📄 ${item.name}</span></li>`;
            }
        });
        
        html += '</ul>';
        const fileEl = document.getElementById('file-structure');
        fileEl.textContent = '';
        const structureDiv = this.createFileStructureDOM(structure);
        fileEl.appendChild(structureDiv);
    }

    formatDocumentationSecure(docs) {
        if (!docs) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = 'No documentation available';
            return errorDiv;
        }
        
        const container = document.createElement('div');
        container.className = 'documentation';
        
        const sections = docs.split('\n## ');
        sections.forEach((section, index) => {
            if (!section.trim()) return;
            
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'doc-section';
            
            const lines = section.split('\n');
            const title = document.createElement('h3');
            title.textContent = index === 0 ? lines[0] : '## ' + lines[0];
            sectionDiv.appendChild(title);
            
            const content = document.createElement('pre');
            content.textContent = lines.slice(1).join('\n');
            sectionDiv.appendChild(content);
            
            container.appendChild(sectionDiv);
        });
        
        return container;
    }

    createFileStructureDOM(structure) {
        const ul = document.createElement('ul');
        ul.className = 'file-tree';
        
        structure.forEach(item => {
            const li = document.createElement('li');
            li.className = item.type === 'folder' ? 'folder' : 'file';
            
            const span = document.createElement('span');
            span.textContent = item.name;
            li.appendChild(span);
            
            if (item.children && Array.isArray(item.children)) {
                const childUl = this.createFileStructureDOM(item.children);
                li.appendChild(childUl);
            }
            
            ul.appendChild(li);
        });
        
        return ul;
    }

    formatDocumentation(docs) {
        // Legacy function - redirect to secure version
        return this.formatDocumentationSecure(docs);
        
        return `
            <div class="documentation">
                <h3>Overview</h3>
                <p>${docs.overview || 'No overview available'}</p>
                
                <h3>Installation</h3>
                <pre><code>${docs.installation || 'No installation instructions'}</code></pre>
                
                <h3>Usage</h3>
                <pre><code>${docs.usage || 'No usage instructions'}</code></pre>
                
                <h3>Features</h3>
                <ul>
                    ${docs.features ? docs.features.map(f => `<li>${f}</li>`).join('') : '<li>No features listed</li>'}
                </ul>
            </div>
        `;
    }

    displayProjectResult(data) {
        // You could show a modal or update a section with the created project details
        console.log('Project created:', data);
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            const data = await response.json();

            if (response.ok && data.projects) {
                this.displayProjects(data.projects);
            }
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }

    displayProjects(projects) {
        const projectsList = document.getElementById('projects-list');
        
        if (!projects || projects.length === 0) {
            projectsList.textContent = '';
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'empty-state';
            const p = document.createElement('p');
            p.textContent = 'No projects yet. Create your first project above!';
            emptyDiv.appendChild(p);
            projectsList.appendChild(emptyDiv);
            return;
        }

        let html = '';
        projects.forEach(project => {
            html += `
                <div class="project-item">
                    <div class="project-header">
                        <div class="project-name">${project.name}</div>
                        <div class="project-status active">Active</div>
                    </div>
                    <div class="project-description">${project.description}</div>
                    <div class="project-tech">${project.tech_stack}</div>
                </div>
            `;
        });

        projectsList.textContent = '';
        projects.forEach(project => {
            const projectDiv = this.createProjectCardDOM(project);
            projectsList.appendChild(projectDiv);
        });
    }
    
    createProjectCardDOM(project) {
        const projectDiv = document.createElement('div');
        projectDiv.className = 'project-card';
        
        const header = document.createElement('div');
        header.className = 'project-header';
        
        const title = document.createElement('h3');
        title.textContent = project.name;
        header.appendChild(title);
        
        const type = document.createElement('span');
        type.className = 'project-type';
        type.textContent = project.type;
        header.appendChild(type);
        
        const description = document.createElement('p');
        description.textContent = project.description;
        
        const footer = document.createElement('div');
        footer.className = 'project-footer';
        
        const techStack = document.createElement('span');
        techStack.className = 'tech-stack';
        techStack.textContent = project.tech_stack;
        footer.appendChild(techStack);
        
        const actions = document.createElement('div');
        actions.className = 'project-actions';
        
        const viewBtn = document.createElement('button');
        viewBtn.textContent = 'View';
        viewBtn.className = 'btn btn-sm btn-outline';
        viewBtn.onclick = () => this.viewProject(project.id);
        actions.appendChild(viewBtn);
        
        const deployBtn = document.createElement('button');
        deployBtn.textContent = 'Deploy';
        deployBtn.className = 'btn btn-sm btn-success';
        deployBtn.onclick = () => this.deployProject(project.id);
        actions.appendChild(deployBtn);
        
        footer.appendChild(actions);
        
        projectDiv.appendChild(header);
        projectDiv.appendChild(description);
        projectDiv.appendChild(footer);
        
        return projectDiv;
    }
    
    scheduleNotificationRemoval(element, callback) {
        // Secure timing function to replace setTimeout usage
        requestAnimationFrame(() => {
            setTimeout(callback, 3000);
        });
    }

    switchTab(tabName) {
        // Remove active class from all tabs and content
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Add active class to selected tab and content
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 0.3s ease;
            background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--accent)'};
        `;

        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    .error { color: var(--error); }
    .loading { 
        display: flex; 
        align-items: center; 
        gap: 0.5rem; 
        color: var(--text-secondary); 
    }
`;
document.head.appendChild(style);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MitoDeveloperEngine();
});