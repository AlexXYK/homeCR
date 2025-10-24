"""Testing Agent - Runs benchmarks and identifies issues."""
from typing import Dict, List
from .base_agent import BaseAgent


class TestingAgent(BaseAgent):
    """
    Testing Agent is responsible for:
    - Running OCR benchmarks
    - Analyzing test results
    - Identifying performance issues
    - Suggesting areas for improvement
    """
    
    def __init__(self):
        super().__init__(
            name="Tester",
            role="Quality Assurance & Benchmarking Specialist",
            system_prompt="""You are the Testing Agent for an OCR system.

Your responsibilities:
1. Design and run comprehensive tests
2. Analyze test results to identify issues
3. Find patterns in failures
4. Prioritize problems by severity and frequency
5. Suggest specific test cases for edge cases

Focus on:
- Accuracy metrics (CER, WER)
- Processing speed
- Edge cases and failure modes
- Regression detection
- Coverage across document types

Be data-driven and specific in your analysis."""
        )
    
    async def execute_task(self, task: Dict) -> Dict:
        """Execute a testing task."""
        task_type = task.get("type")
        
        if task_type == "analyze_results":
            return await self._analyze_results(task)
        elif task_type == "identify_issues":
            return await self._identify_issues(task)
        elif task_type == "suggest_tests":
            return await self._suggest_tests(task)
        else:
            return {"status": "unknown_task_type", "task_type": task_type}
    
    async def _analyze_results(self, task: Dict) -> Dict:
        """Analyze test results and provide insights."""
        results = task.get("results", {})
        
        prompt = f"""Analyze these OCR test results:

Overall Metrics:
- Total Tests: {results.get('total_tests', 0)}
- Average Accuracy: {results.get('avg_accuracy', 0):.1%}
- Average CER: {results.get('avg_cer', 0):.3f}
- Average Processing Time: {results.get('avg_time', 0):.2f}s

Dataset Breakdown:
{results.get('by_dataset', 'No breakdown available')}

Provide:
1. Key insights from the data
2. Areas performing well
3. Areas needing improvement
4. Specific recommendations"""
        
        response = await self.think(prompt, context=results)
        
        return {
            "status": "analyzed",
            "insights": response,
            "data": results
        }
    
    async def _identify_issues(self, task: Dict) -> Dict:
        """Identify specific issues from test failures."""
        failures = task.get("failures", [])
        
        prompt = f"""These test cases failed:

{chr(10).join(f"{i+1}. {failure}" for i, failure in enumerate(failures[:10]))}

Analyze and identify:
1. Common patterns in failures
2. Root causes
3. Which document types are most problematic
4. Specific improvements needed"""
        
        response = await self.think(prompt, context={"failures": failures})
        
        return {
            "status": "issues_identified",
            "issues": response,
            "failure_count": len(failures)
        }
    
    async def _suggest_tests(self, task: Dict) -> Dict:
        """Suggest additional test cases."""
        current_coverage = task.get("coverage", {})
        
        prompt = f"""Current test coverage:

{chr(10).join(f"- {category}: {count} tests" for category, count in current_coverage.items())}

Suggest 5-10 specific test cases that would improve coverage, focusing on:
- Edge cases
- Common failure scenarios
- Real-world document types
- Stress testing

Be specific about what each test should validate."""
        
        response = await self.think(prompt, context=current_coverage)
        
        return {
            "status": "tests_suggested",
            "suggestions": response
        }

