from ai_providers import ai_generate

class AdvancedProjectManager:
    def __init__(self, industry: str, specializations):
        self.industry = industry
        self.specializations = specializations

    def initialize_project(self, project_data):
        prompt = self.create_initialization_prompt(project_data)
        response = ai_generate(prompt)
        # Parse and return as needed for your platform
        return {"raw_response": response}

    def create_initialization_prompt(self, project_data):
        # Build a prompt string based on project_data and self.industry, self.specializations
        return f"Initialize a new {self.industry} project with data: {project_data}"

# Example subclasses use the same pattern, no changes needed unless they previously used OpenAI directly.