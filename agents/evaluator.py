"""Evaluation Agent - Analyzes results and suggests optimizations."""
from typing import Dict
from .base_agent import BaseAgent


class EvaluationAgent(BaseAgent):
    """
    Evaluation Agent:
    - Analyzes test results
    - Identifies root causes of issues
    - Proposes specific solutions
    - Suggests optimizations
    """
    
    def __init__(self):
        super().__init__(
            name="Evaluator",
            role="Performance Analyst & Optimization Specialist",
            system_prompt="""You are the Evaluation Agent for an OCR system.

Your responsibilities:
1. Deep analysis of performance data
2. Root cause analysis of failures
3. Propose specific technical solutions
4. Suggest optimization strategies
5. Research new techniques and models

Consider:
- Algorithm improvements
- Model parameter tuning
- Preprocessing enhancements
- Post-processing refinements
- Resource optimization

Be technically specific and provide actionable recommendations."""
        )
    
    async def execute_task(self, task: Dict) -> Dict:
        """Execute an evaluation task."""
        task_type = task.get("type")
        
        if task_type == "root_cause_analysis":
            return await self._analyze_root_cause(task)
        elif task_type == "propose_solution":
            return await self._propose_solution(task)
        elif task_type == "research_techniques":
            return await self._research_techniques(task)
        else:
            return {"status": "unknown_task_type", "task_type": task_type}
    
    async def _analyze_root_cause(self, task: Dict) -> Dict:
        """Perform root cause analysis on an issue."""
        issue = task.get("issue", {})
        context_data = task.get("context", {})
        
        prompt = f"""Perform root cause analysis on this OCR issue:

Issue Description:
{issue.get('description', 'No description')}

Symptoms:
{issue.get('symptoms', 'No symptoms listed')}

Context:
{context_data}

Provide:
1. Likely root cause(s)
2. Why this is happening
3. Which component is responsible
4. Similar known issues in OCR systems"""
        
        response = await self.think(prompt, context=task)
        
        return {
            "status": "analyzed",
            "root_cause": response,
            "issue": issue
        }
    
    async def _propose_solution(self, task: Dict) -> Dict:
        """Propose a solution for an identified issue."""
        issue = task.get("issue", {})
        root_cause = task.get("root_cause", "")
        
        prompt = f"""Propose a solution for this issue:

Issue: {issue.get('description', 'No description')}
Root Cause: {root_cause}

Provide:
1. Specific technical solution
2. Which files/components need modification
3. Estimated impact on performance
4. Implementation complexity (Low/Medium/High)
5. Potential risks
6. Testing approach to validate fix

Be specific enough that a Development Agent could implement it."""
        
        response = await self.think(prompt, context=task)
        
        return {
            "status": "solution_proposed",
            "solution": response,
            "issue": issue
        }
    
    async def _research_techniques(self, task: Dict) -> Dict:
        """Research new techniques for improvement."""
        area = task.get("area", "general OCR improvement")
        
        prompt = f"""Research and suggest techniques for: {area}

Consider:
1. Latest OCR research and best practices
2. Model improvements (preprocessing, models, post-processing)
3. Existing successful implementations
4. Feasibility with current tech stack (Tesseract, Surya, Ollama vision models)

Provide:
1. Top 3-5 promising techniques
2. Brief description of each
3. Expected benefits
4. Implementation effort
5. Compatibility with our system"""
        
        response = await self.think(prompt, context={"area": area})
        
        return {
            "status": "research_complete",
            "techniques": response,
            "area": area
        }

