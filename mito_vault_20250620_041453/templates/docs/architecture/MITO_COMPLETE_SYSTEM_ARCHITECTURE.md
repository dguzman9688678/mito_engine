# MITO Engine Complete System Architecture

## Main System Overview

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Giant Workbench UI]
        B[Mobile Interface]
        C[Chat Interface]
        D[Code Editor Display]
        E[Whiteboard Canvas]
        F[File Upload Zone]
    end
    
    subgraph "API Gateway Layer"
        G[Flask App Router]
        H[/api/generate]
        I[/api/generate-code]
        J[/api/generate-image]
        K[/api/create-project]
        L[/api/upload-file]
        M[/api/whiteboard]
    end
    
    subgraph "Core Processing Layer"
        N[MITO Agent Core]
        O[AI Provider Manager]
        P[Memory Manager]
        Q[File Processor]
        R[Project Generator]
        S[Image Generator]
        T[Notification Manager]
    end
    
    subgraph "AI Provider Layer"
        U[OpenAI GPT-3.5]
        V[LLaMA via Groq]
        W[Claude API]
        X[Local Fallback]
    end
    
    subgraph "Data Layer"
        Y[Memory Database]
        Z[File System]
        AA[Session Storage]
        BB[Knowledge Base]
        CC[Generated Code Cache]
    end
    
    A --> G
    B --> G
    C --> H
    D --> I
    E --> M
    F --> L
    
    G --> N
    H --> O
    I --> O
    J --> S
    K --> R
    L --> Q
    M --> Q
    
    N --> P
    N --> T
    O --> U
    O --> V
    O --> W
    O --> X
    
    P --> Y
    Q --> Z
    R --> Z
    S --> CC
    T --> AA
    
    style N fill:#ff6b6b
    style O fill:#4ecdc4
    style P fill:#45b7d1
```

## Code Generation Pipeline with Failure Points

```mermaid
sequenceDiagram
    participant U as User Chat
    participant F as Frontend JS
    participant A as API Router
    participant M as MITO Agent
    participant AI as AI Provider
    participant DB as Memory DB
    participant DOM as Code Display
    
    Note over U,DOM: Code Generation Request Flow
    
    U->>F: "generate code for calculator"
    
    rect rgb(255, 200, 200)
        Note over F: FAILURE POINT 1: Chat detection
        F->>F: Check if code generation request
        alt contains "generate" AND "code"
            F->>F: triggerCodeGeneration()
        else
            F->>A: POST /api/generate (generic chat)
            Note over A: PIPELINE DIVERGENCE
        end
    end
    
    rect rgb(200, 255, 200)
        Note over F,A: FIXED PIPELINE
        F->>A: POST /api/generate-code
        A->>A: Route detection logic
        alt "generate" + "code" detected
            A->>A: handle_code_generation_request()
        else
            A->>M: ai_generate() - generic response
            Note over M: FAILURE: Generic AI response
        end
    end
    
    A->>M: Initialize memory context
    M->>DB: Fetch conversation history
    DB-->>M: Return context
    
    M->>AI: Enhanced prompt with context
    
    rect rgb(255, 255, 200)
        Note over AI: PROVIDER SELECTION
        AI->>AI: Check provider availability
        alt OpenAI available
            AI->>AI: Use GPT-3.5
        else LLaMA available
            AI->>AI: Use Groq API
        else All providers down
            AI->>AI: Local fallback response
            Note over AI: FAILURE: Generic response
        end
    end
    
    AI-->>M: Generated code response
    M->>DB: Store in memory
    M-->>A: JSON response with code
    
    rect rgb(255, 200, 200)
        Note over A,DOM: FRONTEND DISPLAY ISSUES
        A-->>F: Response with code field
        F->>F: Check data.success && data.code
        alt Code exists
            F->>DOM: Direct DOM manipulation
            DOM->>DOM: Update main-code-display element
        else No code field
            F->>F: Show error message
            Note over F: FAILURE: Undefined display
        end
    end
```

## Memory Management & Context Flow

```mermaid
graph LR
    subgraph "Memory Input Sources"
        A[User Messages]
        B[Generated Code]
        C[File Uploads]
        D[System Events]
        E[API Responses]
    end
    
    subgraph "Memory Processing"
        F[Memory Manager]
        G[Context Builder]
        H[Session Manager]
        I[Knowledge Indexer]
    end
    
    subgraph "Memory Storage"
        J[Active Sessions]
        K[Conversation History]
        L[Code Snippets]
        M[File Metadata]
        N[User Preferences]
    end
    
    subgraph "Memory Retrieval"
        O[Context Queries]
        P[Similarity Search]
        Q[Session Restoration]
        R[Knowledge Lookup]
    end
    
    A --> F
    B --> F
    C --> F
    D --> F
    E --> F
    
    F --> G
    F --> H
    F --> I
    
    G --> J
    H --> K
    I --> L
    F --> M
    F --> N
    
    O --> P
    P --> Q
    Q --> R
    
    R --> F
```

## File Processing & Knowledge Pipeline

```mermaid
flowchart TD
    A[File Upload] --> B{File Type Detection}
    
    B -->|Text/Code| C[Text Extractor]
    B -->|PDF| D[PDF Parser]
    B -->|Image| E[Image Analyzer]
    B -->|Office Docs| F[Document Parser]
    
    C --> G[Content Analysis]
    D --> G
    E --> G
    F --> G
    
    G --> H[AI Processing]
    H --> I[Knowledge Extraction]
    I --> J[Metadata Generation]
    
    J --> K[Store in Knowledge Base]
    K --> L[Index for Search]
    
    subgraph "Processing Issues"
        M[Large File Timeout]
        N[Unsupported Format]
        O[Memory Overflow]
        P[AI Processing Failure]
    end
    
    B -.->|Failure| N
    G -.->|Timeout| M
    H -.->|Error| P
    I -.->|Memory| O
    
    style M fill:#ffcccc
    style N fill:#ffcccc
    style O fill:#ffcccc
    style P fill:#ffcccc
```

## AI Provider Integration & Failover

```mermaid
stateDiagram-v2
    [*] --> ProviderSelection
    
    ProviderSelection --> OpenAI : Primary
    ProviderSelection --> LLaMA : Secondary
    ProviderSelection --> Claude : If Available
    ProviderSelection --> Local : Last Resort
    
    state OpenAI {
        [*] --> CheckAPI
        CheckAPI --> SendRequest : API Key Valid
        CheckAPI --> RateLimit : Too Many Requests
        CheckAPI --> Failure : Invalid Key/Network
        SendRequest --> Success : Response Received
        SendRequest --> Timeout : No Response
        RateLimit --> Wait
        Wait --> SendRequest
    }
    
    state LLaMA {
        [*] --> GroqAPI
        GroqAPI --> GroqSuccess : Response OK
        GroqAPI --> GroqFail : API Error
    }
    
    state Claude {
        [*] --> ClaudeCheck
        ClaudeCheck --> ClaudeDisabled : No API Key
    }
    
    state Local {
        [*] --> GenerateLocal
        GenerateLocal --> LocalResponse : Always Available
    }
    
    Failure --> LLaMA
    Timeout --> LLaMA
    GroqFail --> Claude
    ClaudeDisabled --> Local
    
    Success --> [*]
    GroqSuccess --> [*]
    LocalResponse --> [*]
```

## Image Generation Pipeline

```mermaid
graph TB
    A[Image Request] --> B[Prompt Analysis]
    B --> C{Provider Available?}
    
    C -->|OpenAI DALL-E| D[DALL-E API]
    C -->|Local Generation| E[SVG Generator]
    
    D --> F[Image URL Response]
    E --> G[SVG Creation]
    
    F --> H[Display in UI]
    G --> H
    
    subgraph "Image Processing Issues"
        I[DALL-E Rate Limit]
        J[Invalid Prompt]
        K[Network Timeout]
        L[SVG Generation Error]
    end
    
    D -.->|Error| I
    B -.->|Bad Input| J
    D -.->|Timeout| K
    E -.->|Error| L
    
    I --> E
    J --> E
    K --> E
```

## Autonomous Task Execution

```mermaid
graph LR
    subgraph "Task Queue"
        A[System Initialization]
        B[Capability Check]
        C[Provider Optimization]
        D[Knowledge Indexing]
        E[User Greeting]
    end
    
    subgraph "MITO Agent Core"
        F[Task Scheduler]
        G[Priority Manager]
        H[Execution Engine]
        I[Status Monitor]
    end
    
    subgraph "Task Execution"
        J[Background Processing]
        K[System Optimization]
        L[Memory Cleanup]
        M[Health Checks]
        N[Notification Generation]
    end
    
    A --> F
    B --> F
    C --> F
    D --> F
    E --> F
    
    F --> G
    G --> H
    H --> I
    
    H --> J
    H --> K
    H --> L
    H --> M
    H --> N
    
    N --> O[Notification Manager]
    O --> P[User Alerts]
```

## System Diagnostic Flow

```mermaid
flowchart TD
    A[Diagnostic Request] --> B[System Introspection]
    
    B --> C[Check AI Providers]
    B --> D[Check Memory Usage]
    B --> E[Test API Endpoints]
    B --> F[Analyze Frontend Integration]
    
    C --> G{Providers Available?}
    D --> H{Memory < 80%?}
    E --> I{APIs Responding?}
    F --> J{Frontend Connected?}
    
    G -->|No| K[Provider Issues Found]
    G -->|Yes| L[Providers OK]
    
    H -->|No| M[High Memory Usage]
    H -->|Yes| N[Memory OK]
    
    I -->|No| O[API Failures Detected]
    I -->|Yes| P[APIs Operational]
    
    J -->|No| Q[Frontend Disconnected]
    J -->|Yes| R[Frontend OK]
    
    K --> S[Generate Diagnostic Report]
    L --> S
    M --> S
    N --> S
    O --> S
    P --> S
    Q --> S
    R --> S
    
    S --> T[Return to User]
```

## Complete Data Flow Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        A[Chat Input]
        B[Code Editor]
        C[File Upload]
        D[Whiteboard]
    end
    
    subgraph "Request Processing"
        E[Route Detection]
        F[Authentication]
        G[Rate Limiting]
        H[Request Validation]
    end
    
    subgraph "Core Engine"
        I[MITO Agent]
        J[Memory Context]
        K[AI Provider Selection]
        L[Response Generation]
    end
    
    subgraph "External Services"
        M[OpenAI API]
        N[Groq API]
        O[File System]
        P[Database]
    end
    
    subgraph "Response Pipeline"
        Q[Response Processing]
        R[Frontend Integration]
        S[UI Updates]
        T[Memory Storage]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    
    E --> F
    F --> G
    G --> H
    
    H --> I
    I --> J
    J --> K
    K --> L
    
    L --> M
    L --> N
    L --> O
    L --> P
    
    M --> Q
    N --> Q
    O --> Q
    P --> Q
    
    Q --> R
    R --> S
    S --> T
    T --> J
```

## Current System Issues & Gaps

### 🔴 Critical Issues:
1. **Chat Pipeline Disconnect**: Generic AI responses instead of code generation
2. **Frontend Scope Errors**: JavaScript function references breaking
3. **Memory Context Loss**: Sessions not properly maintained
4. **Provider Failover**: No graceful degradation between AI services

### 🟡 Performance Issues:
1. **Slow API Responses**: 5-8 second generation times
2. **Memory Leaks**: Cleanup not running efficiently
3. **File Processing**: Large files causing timeouts

### 🟢 Working Systems:
1. **Code Generation API**: Direct endpoint functional
2. **File Upload**: Basic processing working
3. **AI Providers**: OpenAI and LLaMA active
4. **MITO Agent**: Background tasks executing

### 💡 Autonomous vs Conversational Gap:
- **Conversational**: Working via generic chat responses
- **Autonomous**: Task queue active but not integrated with user requests
- **Gap**: No bridge between user intents and autonomous task execution