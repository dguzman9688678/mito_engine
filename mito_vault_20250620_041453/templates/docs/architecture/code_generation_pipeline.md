# MITO Code Generation Pipeline Flow

```mermaid
flowchart TD
    A[User clicks Generate Code] --> B[Frontend captures input]
    B --> C[JavaScript sends POST to /api/generate-code]
    C --> D{Request validation}
    D -->|Valid| E[Initialize memory manager]
    D -->|Invalid| F[Return 400 error]
    E --> G[Select AI provider - LLaMA/OpenAI/Local]
    G --> H[Build enhanced prompt with requirements]
    H --> I[Send to AI API]
    I --> J{AI Response}
    J -->|Success| K[Process generated code]
    J -->|Error| L[Try fallback provider]
    K --> M[Add metadata and timestamp]
    M --> N[Return JSON response to frontend]
    N --> O[Frontend receives response]
    O --> P{Response success?}
    P -->|Yes| Q[Display code in UI]
    P -->|No| R[Show error message]
    L --> I

    style A fill:#e1f5fe
    style Q fill:#c8e6c9
    style R fill:#ffcdd2
    style F fill:#ffcdd2
```

## Current Pipeline Status:
- ✅ Backend API: Working (tested - returns code in 5.1s)
- ❓ Frontend Integration: Needs verification
- ✅ AI Providers: LLaMA and OpenAI active
- ✅ Memory System: Operational
- ✅ Error Handling: Active

## Troubleshooting Steps:
1. Check browser console for JavaScript errors
2. Verify network tab shows API calls
3. Check if response reaches frontend correctly