"""
MITO Engine - Complete System Flow Diagram Generator
Creates comprehensive visualization of user journey through all features and links
"""

import json
from datetime import datetime
from typing import Dict, Any, List

class MITOSystemFlowGenerator:
    """Generate complete system flow diagrams and documentation"""
    
    def __init__(self):
        self.system_map = {
            "entry_points": {
                "main_interface": {
                    "url": "/",
                    "description": "Main MITO Engine Interface",
                    "features": ["giant_workbench", "lab_mode", "agent_interactions"]
                },
                "lab_interfaces": {
                    "agent_lab": "/agent-lab",
                    "api_key_lab": "/api-key-lab", 
                    "tool_lab": "/tool-lab",
                    "unified_lab": "/unified-lab"
                }
            },
            "core_features": {
                "file_management": {
                    "backend": "file_manager.py",
                    "apis": ["/api/files", "/api/files/read", "/api/files/write", "/api/files/delete", "/api/files/search"],
                    "capabilities": ["browse_files", "edit_files", "upload_files", "download_files", "search_content"],
                    "user_flow": [
                        "User clicks 'File Browser' button",
                        "System loads file_manager backend",
                        "User navigates directory structure",
                        "User selects file for editing/viewing",
                        "Code editor opens with syntax highlighting",
                        "User makes changes and saves"
                    ]
                },
                "terminal_operations": {
                    "backend": "terminal_manager.py",
                    "apis": ["/api/terminal/execute", "/api/terminal/history", "/api/terminal/sessions"],
                    "capabilities": ["command_execution", "session_management", "command_history", "system_info"],
                    "user_flow": [
                        "User clicks 'Terminal' button",
                        "System initializes terminal_manager",
                        "Terminal interface opens",
                        "User types commands",
                        "System executes via subprocess",
                        "Results displayed in real-time"
                    ]
                },
                "code_editing": {
                    "backend": "code_editor.py",
                    "apis": ["/api/editor/open", "/api/editor/save", "/api/editor/format", "/api/editor/open-files"],
                    "capabilities": ["syntax_highlighting", "code_formatting", "multi_file_editing", "auto_completion"],
                    "user_flow": [
                        "User opens file from browser",
                        "Code editor loads with syntax detection",
                        "User edits with highlighting and completion",
                        "Auto-save triggers on changes",
                        "Format code on demand"
                    ]
                },
                "project_management": {
                    "backend": "project_manager.py", 
                    "apis": ["/api/projects/templates", "/api/projects/create", "/api/projects", "/api/projects/<id>/structure"],
                    "capabilities": ["template_selection", "project_creation", "structure_analysis", "dependency_management"],
                    "user_flow": [
                        "User clicks 'New Project'",
                        "Template gallery loads",
                        "User selects framework/template",
                        "Project scaffolding generated",
                        "Files and structure created automatically"
                    ]
                },
                "database_operations": {
                    "backend": "database_manager.py",
                    "apis": ["/api/database/connections", "/api/database/query", "/api/database/tables", "/api/database/stats"],
                    "capabilities": ["multi_db_support", "query_execution", "schema_management", "data_visualization"],
                    "user_flow": [
                        "User accesses 'Database' section",
                        "Connection manager loads",
                        "User selects/configures database",
                        "Query interface opens",
                        "Results displayed in tables/charts"
                    ]
                },
                "deployment_tools": {
                    "backend": "deployment_manager.py",
                    "apis": ["/api/deployment/targets", "/api/deployment/deploy", "/api/deployment/status/<id>", "/api/deployment/list"],
                    "capabilities": ["multi_platform_deployment", "status_monitoring", "rollback_support", "automated_builds"],
                    "user_flow": [
                        "User clicks 'Deploy' button",
                        "Deployment targets load",
                        "User selects platform (Replit/AWS/Docker)",
                        "Build process initiates",
                        "Real-time status updates",
                        "Deployment completion notification"
                    ]
                },
                "ai_interactions": {
                    "backend": "ai_providers.py",
                    "apis": ["/api/ai/chat", "/api/ai/generate", "/api/ai/analyze"],
                    "capabilities": ["multi_model_support", "code_generation", "analysis", "conversation"],
                    "user_flow": [
                        "User types in AI chat interface",
                        "System selects best available model",
                        "Request processed through provider",
                        "AI response with code/analysis",
                        "User can iterate and refine"
                    ]
                },
                "web_scraping": {
                    "backend": "web_scraper_manager.py",
                    "apis": ["/api/scraper/scrape", "/api/scraper/scrape-multiple", "/api/scraper/search", "/api/scraper/jobs"],
                    "capabilities": ["single_url_scraping", "batch_scraping", "search_integration", "data_extraction"],
                    "user_flow": [
                        "User enters URL to scrape",
                        "Scraper manager validates URL",
                        "Content extraction begins",
                        "Clean data displayed",
                        "Export options provided"
                    ]
                },
                "data_visualization": {
                    "backend": "visualization_manager.py",
                    "apis": ["/api/viz/charts", "/api/viz/charts/create", "/api/viz/dashboards", "/api/viz/reports/analytics"],
                    "capabilities": ["chart_creation", "dashboard_building", "report_generation", "data_analysis"],
                    "user_flow": [
                        "User uploads/selects data",
                        "Chart type selection interface",
                        "Data mapping and configuration",
                        "Chart generation and preview",
                        "Dashboard assembly and sharing"
                    ]
                },
                "authentication": {
                    "backend": "authentication_manager.py",
                    "apis": ["/api/auth/register", "/api/auth/login", "/api/auth/logout", "/api/auth/validate"],
                    "capabilities": ["user_registration", "secure_login", "session_management", "role_based_access"],
                    "user_flow": [
                        "User accesses protected feature",
                        "Login prompt appears",
                        "Credentials validated",
                        "Session established",
                        "Access granted to features"
                    ]
                }
            },
            "specialized_labs": {
                "agent_lab": {
                    "purpose": "AI Agent Development and Testing",
                    "features": ["agent_creation", "behavior_configuration", "testing_environment", "performance_monitoring"],
                    "user_journey": [
                        "Enter Agent Lab interface",
                        "Select agent template or create custom",
                        "Configure AI model and parameters", 
                        "Define agent goals and constraints",
                        "Test agent in sandbox environment",
                        "Deploy to production with monitoring"
                    ]
                },
                "api_key_lab": {
                    "purpose": "API Key Management and Testing",
                    "features": ["key_storage", "service_testing", "usage_monitoring", "security_validation"],
                    "user_journey": [
                        "Access API Key Lab",
                        "Add API keys for various services",
                        "Test connectivity and permissions",
                        "Monitor usage and quotas",
                        "Manage key rotation and security"
                    ]
                },
                "tool_lab": {
                    "purpose": "Custom Tool Development",
                    "features": ["tool_creation", "integration_testing", "workflow_automation", "tool_marketplace"],
                    "user_journey": [
                        "Open Tool Lab interface",
                        "Design custom tool or select template",
                        "Configure inputs/outputs and logic",
                        "Test tool functionality",
                        "Integrate with main workflow",
                        "Share or publish to marketplace"
                    ]
                }
            },
            "data_flow": {
                "user_input": [
                    "Mouse clicks and keyboard input",
                    "File uploads and drag-drop",
                    "API requests and webhook calls",
                    "Voice commands (if enabled)",
                    "Touch gestures (mobile)"
                ],
                "processing_layers": [
                    "Frontend JavaScript handlers",
                    "Flask route processing",
                    "Manager class methods",
                    "Database operations",
                    "External API calls",
                    "AI model inference"
                ],
                "output_channels": [
                    "Real-time UI updates",
                    "WebSocket notifications",
                    "File downloads",
                    "Email notifications",
                    "API responses",
                    "Generated reports"
                ]
            },
            "integration_points": {
                "external_services": [
                    "OpenAI GPT models",
                    "Cloud storage providers",
                    "Database systems",
                    "Deployment platforms",
                    "Authentication providers",
                    "Monitoring services"
                ],
                "internal_connections": [
                    "Cross-manager communication",
                    "Shared database access",
                    "Event system notifications",
                    "Cache layer coordination",
                    "Session state management"
                ]
            }
        }
    
    def generate_mermaid_flowchart(self) -> str:
        """Generate Mermaid flowchart showing complete user journey"""
        
        mermaid_content = """
graph TD
    %% Entry Points
    A[User Visits MITO Engine] --> B{Select Interface}
    B --> C[Main Workbench /]
    B --> D[Agent Lab /agent-lab]
    B --> E[API Key Lab /api-key-lab]
    B --> F[Tool Lab /tool-lab]
    B --> G[Unified Lab /unified-lab]
    
    %% Main Workbench Flow
    C --> H[Giant Workbench Interface]
    H --> I{Choose Feature}
    
    %% File Management Flow
    I --> J[File Browser]
    J --> K[file_manager.py]
    K --> L[/api/files/*]
    L --> M[Browse/Edit/Upload Files]
    M --> N[Code Editor Opens]
    N --> O[Syntax Highlighting]
    O --> P[Save Changes]
    
    %% Terminal Operations Flow
    I --> Q[Terminal Access]
    Q --> R[terminal_manager.py]
    R --> S[/api/terminal/*]
    S --> T[Command Execution]
    T --> U[Real-time Results]
    U --> V[Command History]
    
    %% Project Management Flow
    I --> W[New Project]
    W --> X[project_manager.py]
    X --> Y[/api/projects/*]
    Y --> Z[Template Selection]
    Z --> AA[Project Scaffolding]
    AA --> BB[Auto-generated Structure]
    
    %% Database Operations Flow
    I --> CC[Database Manager]
    CC --> DD[database_manager.py]
    DD --> EE[/api/database/*]
    EE --> FF[Connection Setup]
    FF --> GG[Query Interface]
    GG --> HH[Results Visualization]
    
    %% AI Interactions Flow
    I --> II[AI Chat Interface]
    II --> JJ[ai_providers.py]
    JJ --> KK[/api/ai/*]
    KK --> LL{Select AI Model}
    LL --> MM[OpenAI GPT]
    LL --> NN[Local Models]
    LL --> OO[Claude API]
    MM --> PP[AI Response]
    NN --> PP
    OO --> PP
    PP --> QQ[Code Generation]
    QQ --> RR[Analysis Results]
    
    %% Web Scraping Flow
    I --> SS[Web Scraper]
    SS --> TT[web_scraper_manager.py]
    TT --> UU[/api/scraper/*]
    UU --> VV[URL Input]
    VV --> WW[Content Extraction]
    WW --> XX[Data Processing]
    XX --> YY[Export Options]
    
    %% Visualization Flow
    I --> ZZ[Data Visualization]
    ZZ --> AAA[visualization_manager.py]
    AAA --> BBB[/api/viz/*]
    BBB --> CCC[Chart Creation]
    CCC --> DDD[Dashboard Building]
    DDD --> EEE[Report Generation]
    
    %% Deployment Flow
    I --> FFF[Deploy Project]
    FFF --> GGG[deployment_manager.py]
    GGG --> HHH[/api/deployment/*]
    HHH --> III{Select Platform}
    III --> JJJ[Replit Deploy]
    III --> KKK[AWS Deploy]
    III --> LLL[Docker Deploy]
    JJJ --> MMM[Build Process]
    KKK --> MMM
    LLL --> MMM
    MMM --> NNN[Live Application]
    
    %% Authentication Flow
    A --> OOO{User Authenticated?}
    OOO -->|No| PPP[Login/Register]
    PPP --> QQQ[authentication_manager.py]
    QQQ --> RRR[/api/auth/*]
    RRR --> SSS[Session Created]
    SSS --> C
    OOO -->|Yes| C
    
    %% Specialized Labs Flow
    D --> TTT[Agent Development]
    TTT --> UUU[AI Model Configuration]
    UUU --> VVV[Agent Testing]
    VVV --> WWW[Deployment]
    
    E --> XXX[API Key Management]
    XXX --> YYY[Service Testing]
    YYY --> ZZZ[Usage Monitoring]
    
    F --> AAAA[Tool Creation]
    AAAA --> BBBB[Integration Testing]
    BBBB --> CCCC[Workflow Automation]
    
    %% Styling
    classDef entryPoint fill:#e1f5fe
    classDef backend fill:#f3e5f5
    classDef api fill:#e8f5e8
    classDef feature fill:#fff3e0
    classDef output fill:#fce4ec
    
    class A,B,C,D,E,F,G entryPoint
    class K,R,X,DD,JJ,TT,AAA,GGG,QQQ backend
    class L,S,Y,EE,KK,UU,BBB,HHH,RRR api
    class M,T,Z,FF,LL,VV,CCC,III feature
    class P,U,BB,HH,PP,YY,EEE,NNN output
"""
        
        return mermaid_content
    
    def generate_user_journey_html(self) -> str:
        """Generate comprehensive HTML documentation of user journey"""
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MITO Engine - Complete System Flow</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}
        .header h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin: 0;
            font-weight: 300;
        }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9ff;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }}
        .section h2 {{
            color: #667eea;
            margin-top: 0;
            font-size: 1.5em;
        }}
        .flow-item {{
            background: white;
            margin: 15px 0;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .flow-item h3 {{
            color: #764ba2;
            margin: 0 0 10px 0;
            font-size: 1.2em;
        }}
        .api-list {{
            background: #e8f5e8;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.9em;
        }}
        .user-step {{
            background: #fff3e0;
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 3px solid #ff9800;
        }}
        .mermaid-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .integration-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .integration-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            font-style: italic;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MITO Engine v1.2.0</h1>
            <p>Complete System Flow & User Journey Documentation</p>
            <p><strong>Created by:</strong> Daniel Guzman | <strong>Contact:</strong> guzman.danield@outlook.com</p>
        </div>

        <div class="section">
            <h2>System Architecture Overview</h2>
            <div class="mermaid-container">
                <div class="mermaid">
                    {self.generate_mermaid_flowchart()}
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Entry Points & User Access</h2>
            <div class="flow-item">
                <h3>Main Interface (/) - Primary Entry Point</h3>
                <p>The main MITO Engine interface featuring the Giant Workbench with all core functionalities accessible from a single dashboard.</p>
                <div class="user-step">User lands on homepage → Sees integrated workbench → Accesses all features seamlessly</div>
            </div>
            <div class="flow-item">
                <h3>Specialized Laboratory Interfaces</h3>
                <ul>
                    <li><strong>Agent Lab (/agent-lab)</strong> - AI agent development and testing environment</li>
                    <li><strong>API Key Lab (/api-key-lab)</strong> - Secure API key management and service testing</li>
                    <li><strong>Tool Lab (/tool-lab)</strong> - Custom tool creation and workflow automation</li>
                    <li><strong>Unified Lab (/unified-lab)</strong> - Combined laboratory features in one interface</li>
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>Core Feature Flows</h2>
"""

        for feature_name, feature_data in self.system_map["core_features"].items():
            html_content += f"""
            <div class="flow-item">
                <h3>{feature_name.replace('_', ' ').title()}</h3>
                <p><strong>Backend:</strong> {feature_data['backend']}</p>
                <div class="api-list">
                    <strong>API Endpoints:</strong><br>
                    {' | '.join(feature_data['apis'])}
                </div>
                <p><strong>User Journey:</strong></p>
                <div>
"""
            for step in feature_data['user_flow']:
                html_content += f'<div class="user-step">{step}</div>'
            
            html_content += f"""
                </div>
                <p><strong>Capabilities:</strong> {', '.join(feature_data['capabilities'])}</p>
            </div>
"""

        html_content += f"""
        </div>

        <div class="section">
            <h2>Specialized Laboratory Workflows</h2>
"""

        for lab_name, lab_data in self.system_map["specialized_labs"].items():
            html_content += f"""
            <div class="flow-item">
                <h3>{lab_name.replace('_', ' ').title()}</h3>
                <p><strong>Purpose:</strong> {lab_data['purpose']}</p>
                <p><strong>Features:</strong> {', '.join(lab_data['features'])}</p>
                <p><strong>User Journey:</strong></p>
                <div>
"""
            for step in lab_data['user_journey']:
                html_content += f'<div class="user-step">{step}</div>'
            
            html_content += f"""
                </div>
            </div>
"""

        html_content += f"""
        </div>

        <div class="section">
            <h2>Data Flow & Processing</h2>
            <div class="integration-grid">
                <div class="integration-card">
                    <h3>User Input Methods</h3>
                    <ul>
"""
        for input_method in self.system_map["data_flow"]["user_input"]:
            html_content += f'<li>{input_method}</li>'

        html_content += f"""
                    </ul>
                </div>
                <div class="integration-card">
                    <h3>Processing Layers</h3>
                    <ul>
"""
        for layer in self.system_map["data_flow"]["processing_layers"]:
            html_content += f'<li>{layer}</li>'

        html_content += f"""
                    </ul>
                </div>
                <div class="integration-card">
                    <h3>Output Channels</h3>
                    <ul>
"""
        for output in self.system_map["data_flow"]["output_channels"]:
            html_content += f'<li>{output}</li>'

        html_content += f"""
                    </ul>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Integration Ecosystem</h2>
            <div class="integration-grid">
                <div class="integration-card">
                    <h3>External Service Integrations</h3>
                    <ul>
"""
        for service in self.system_map["integration_points"]["external_services"]:
            html_content += f'<li>{service}</li>'

        html_content += f"""
                    </ul>
                </div>
                <div class="integration-card">
                    <h3>Internal System Connections</h3>
                    <ul>
"""
        for connection in self.system_map["integration_points"]["internal_connections"]:
            html_content += f'<li>{connection}</li>'

        html_content += f"""
                    </ul>
                </div>
            </div>
        </div>

        <div class="timestamp">
            Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>

    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>
"""
        return html_content
    
    def generate_json_system_map(self) -> str:
        """Generate JSON representation of complete system map"""
        return json.dumps(self.system_map, indent=2)
    
    def save_documentation(self):
        """Save all documentation files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save HTML documentation
        html_file = f"MITO_System_Flow_Documentation_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_user_journey_html())
        
        # Save Mermaid flowchart
        mermaid_file = f"MITO_System_Flowchart_{timestamp}.mmd"
        with open(mermaid_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_mermaid_flowchart())
        
        # Save JSON system map
        json_file = f"MITO_System_Map_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_json_system_map())
        
        return {
            "html_documentation": html_file,
            "mermaid_flowchart": mermaid_file,
            "json_system_map": json_file,
            "timestamp": timestamp
        }

def main():
    """Generate complete MITO Engine system flow documentation"""
    generator = MITOSystemFlowGenerator()
    
    print("Generating MITO Engine System Flow Documentation...")
    
    # Save all documentation
    files = generator.save_documentation()
    
    print("Documentation generated successfully:")
    print(f"✓ HTML Documentation: {files['html_documentation']}")
    print(f"✓ Mermaid Flowchart: {files['mermaid_flowchart']}")
    print(f"✓ JSON System Map: {files['json_system_map']}")
    
    return files

if __name__ == "__main__":
    main()