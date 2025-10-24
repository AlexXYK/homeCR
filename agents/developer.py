"""Development Agent - Implements code improvements."""
from typing import Dict
from .base_agent import BaseAgent


class DevelopmentAgent(BaseAgent):
    """
    Development Agent:
    - Implements proposed improvements
    - Writes code changes
    - Creates tests for changes
    - Documents modifications
    """
    
    def __init__(self):
        super().__init__(
            name="Developer",
            role="Implementation Specialist",
            system_prompt="""You are the Development Agent for an OCR system.

Your responsibilities:
1. Implement proposed improvements
2. Write clean, maintainable code
3. Create appropriate tests
4. Document changes
5. Ensure backward compatibility

Follow best practices:
- Write clear, commented code
- Maintain existing code style
- Add error handling
- Consider edge cases
- Keep changes focused and minimal

You work with:
- Python 3.10+
- FastAPI
- Tesseract, Surya OCR
- Ollama vision models
- LangChain/LangGraph

Provide specific, implementable code."""
        )
    
    async def execute_task(self, task: Dict) -> Dict:
        """Execute a development task."""
        task_type = task.get("type")
        
        if task_type == "implement_solution":
            return await self._implement_solution(task)
        elif task_type == "create_test":
            return await self._create_test(task)
        elif task_type == "review_code":
            return await self._review_code(task)
        else:
            return {"status": "unknown_task_type", "task_type": task_type}
    
    async def _implement_solution(self, task: Dict) -> Dict:
        """Implement a proposed solution."""
        solution = task.get("solution", {})
        context = task.get("context", {})
        
        prompt = f"""Implement this solution:

Solution Description:
{solution.get('description', 'No description')}

Target Files:
{solution.get('target_files', 'Not specified')}

Requirements:
{solution.get('requirements', 'Not specified')}

Current Code Context:
{context.get('current_code', 'Not provided')}

Provide:
1. Complete code changes (show exact modifications)
2. Explanation of changes
3. Any new dependencies needed
4. Testing approach

Use Python f-strings, type hints, and async where appropriate."""
        
        response = await self.think(prompt, context=task)
        
        return {
            "status": "implemented",
            "code_changes": response,
            "solution": solution
        }
    
    async def _create_test(self, task: Dict) -> Dict:
        """Create a test for new functionality."""
        functionality = task.get("functionality", {})
        
        prompt = f"""Create a test for this functionality:

Functionality:
{functionality.get('description', 'No description')}

Test Requirements:
{functionality.get('test_requirements', 'Not specified')}

Write a pytest test that:
1. Tests the core functionality
2. Includes edge cases
3. Has clear assertions
4. Is maintainable

Provide complete test code."""
        
        response = await self.think(prompt, context=functionality)
        
        return {
            "status": "test_created",
            "test_code": response,
            "functionality": functionality
        }
    
    async def _review_code(self, task: Dict) -> Dict:
        """Review code changes."""
        code_changes = task.get("code_changes", "")
        
        prompt = f"""Review these code changes:

{code_changes}

Check for:
1. Correctness
2. Best practices
3. Potential bugs
4. Performance issues
5. Security concerns

Provide:
1. Overall assessment (APPROVE/REVISE/REJECT)
2. Specific issues found
3. Suggestions for improvement"""
        
        response = await self.think(prompt, context={"code": code_changes})
        
        return {
            "status": "reviewed",
            "review": response
        }

