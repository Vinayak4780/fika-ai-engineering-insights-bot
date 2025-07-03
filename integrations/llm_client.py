"""
LLM client abstraction layer for pluggable AI providers
"""
import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    usage: Dict[str, int]
    model: str


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> LLMResponse:
        """Generate text from a prompt"""
        pass
    
    @abstractmethod
    def generate_structured_output(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured output following a schema"""
        pass


class GroqClient(BaseLLMClient):
    """Groq API client for Llama models"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama3-8b-8192")
        
        # Try to import Groq
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.available = True
        except ImportError:
            print("Groq package not installed. Run: pip install groq")
            self.available = False
    
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> LLMResponse:
        """Generate text using Groq API"""
        if not self.available:
            raise Exception("Groq client not available")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            model=self.model
        )
    
    def generate_structured_output(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured output using Groq API"""
        if not self.available:
            raise Exception("Groq client not available")
        
        # Add JSON formatting instructions to prompt since Groq doesn't support function calling
        json_prompt = f"""
{prompt}

Please respond with valid JSON that matches this schema:
{schema}

Important: Return ONLY the JSON object, no additional text or formatting.

Response:
"""
        
        response = self.generate_text(json_prompt)
        
        try:
            import json
            # Clean the response to extract just the JSON
            content = response.content.strip()
            # Remove any markdown formatting
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise Exception("Could not parse JSON from response")


class OpenAIClient(BaseLLMClient):
    """OpenAI API client"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        # Try to import OpenAI
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
            self.available = True
        except ImportError:
            print("OpenAI package not installed. Run: pip install openai")
            self.available = False
    
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> LLMResponse:
        """Generate text using OpenAI API"""
        if not self.available:
            raise Exception("OpenAI client not available")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            model=self.model
        )
    
    def generate_structured_output(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured output using function calling"""
        if not self.available:
            raise Exception("OpenAI client not available")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=[{
                "name": "generate_output",
                "description": "Generate structured output",
                "parameters": schema
            }],
            function_call={"name": "generate_output"}
        )
        
        import json
        return json.loads(response.choices[0].message.function_call.arguments)


class LocalLLMClient(BaseLLMClient):
    """Local LLM client using Ollama or similar"""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if local LLM service is available"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> LLMResponse:
        """Generate text using local LLM"""
        if not self.available:
            raise Exception("Local LLM service not available")
        
        import requests
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
        )
        
        result = response.json()
        
        return LLMResponse(
            content=result["response"],
            usage={"total_tokens": len(result["response"].split())},  # Approximate
            model=self.model
        )
    
    def generate_structured_output(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured output with local LLM"""
        # Add JSON formatting instructions to prompt
        json_prompt = f"""
{prompt}

Please respond with valid JSON that matches this schema:
{schema}

Response (JSON only):
"""
        
        response = self.generate_text(json_prompt)
        
        try:
            import json
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback: extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise Exception("Could not parse JSON from response")


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing and development"""
    
    def __init__(self):
        self.model = "mock-llama"
        self.available = True
    
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> LLMResponse:
        """Generate mock insights based on the prompt content"""
        if "insight" in prompt.lower() or "analyze" in prompt.lower():
            content = """
Based on the performance data analysis:

🔍 **Key Insights:**
1. **Steady Development Pace**: The team maintains consistent commit activity with healthy code churn rates
2. **Review Excellence**: Pull request review times are within industry standards, showing good collaboration
3. **Quality Focus**: Low change failure rate indicates robust testing and deployment practices
4. **Room for Optimization**: Lead time could be improved through better CI/CD pipeline optimization

📈 **Recommendations:**
- Consider implementing automated testing to reduce lead times
- Continue the strong code review culture
- Monitor file churn patterns to prevent technical debt accumulation
- Maintain current deployment frequency while focusing on quality

✅ **Positive Trends:**
- Consistent delivery cadence
- Good team collaboration metrics
- Stable deployment success rate
"""
        elif "churn" in prompt.lower():
            content = """
**Code Churn Analysis:**
- Moderate churn levels indicate healthy refactoring activity
- No files showing excessive modification patterns
- Churn distribution suggests balanced workload across the codebase
- Risk score within acceptable bounds for the team size and project complexity
"""
        else:
            content = "Analysis completed successfully. Key performance indicators are within expected ranges."
        
        return LLMResponse(
            content=content,
            usage={"total_tokens": len(content.split())},
            model=self.model
        )
    
    def generate_structured_output(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock structured output"""
        return {
            "insights": [
                "Strong development velocity",
                "Good code quality practices", 
                "Effective collaboration patterns"
            ],
            "recommendations": [
                "Continue current practices",
                "Monitor for optimization opportunities"
            ],
            "risk_level": "LOW"
        }


class LLMClientFactory:
    """Factory for creating LLM clients"""
    
    @staticmethod
    def create_client(provider: str = None) -> BaseLLMClient:
        """Create an LLM client based on configuration"""
        provider = provider or os.getenv("LLM_PROVIDER", "mock")
        
        if provider.lower() == "groq":
            return GroqClient()
        elif provider.lower() == "openai":
            return OpenAIClient()
        elif provider.lower() == "local":
            return LocalLLMClient()
        elif provider.lower() == "mock":
            return MockLLMClient()
        else:
            # Default to mock for testing
            return MockLLMClient()


class PromptTemplates:
    """Collection of prompt templates for different analysis tasks"""
    
    INSIGHT_GENERATION = """
You are an AI assistant that analyzes engineering team performance data and generates actionable insights.

Given the following performance metrics for {period}:

Basic Statistics:
- Total commits: {total_commits}
- Total pull requests: {total_pull_requests}
- Lines added: {lines_added}
- Lines deleted: {lines_deleted}
- Files changed: {files_changed}

DORA Metrics:
- Lead time: {lead_time_days:.1f} days
- Deployment frequency: {deployment_frequency:.2f} deploys/day
- Change failure rate: {change_failure_rate:.1f}%
- Mean time to recovery: {mttr_hours:.1f} hours

Code Quality:
- Total churn: {total_churn} lines
- Churn rate: {churn_rate:.1f} lines/commit
- Risk score: {risk_score:.1f}/100
- High-risk files: {high_risk_files}

Review Metrics:
- Average review time: {avg_review_time_hours:.1f} hours
- Review participation rate: {review_participation_rate:.1f}%
- PR cycle time: {pr_cycle_time_hours:.1f} hours
- Approval rate: {approval_rate:.1f}%

Generate 3-5 key insights and actionable recommendations based on this data. 
Focus on areas for improvement and positive trends to reinforce.
Keep insights concise and practical.
"""

    CHURN_ANALYSIS = """
Analyze the following code churn data for potential quality issues:

Files with high churn (>{threshold} lines changed):
{high_churn_files}

Total churn: {total_churn} lines
Churn rate: {churn_rate:.1f} lines per commit
Risk score: {risk_score:.1f}/100

Identify:
1. Files that may need refactoring
2. Potential architectural issues
3. Areas where code review should be intensified
4. Correlation between churn and potential defects

Provide specific, actionable recommendations.
"""

    TEAM_COMPARISON = """
Compare the performance of the following teams:

{team_data}

Identify:
1. Top performing team and why
2. Teams that need support
3. Best practices to share across teams
4. Resource allocation recommendations

Focus on constructive analysis that promotes collaboration.
"""


# Global LLM client instance
llm_client = LLMClientFactory.create_client()
