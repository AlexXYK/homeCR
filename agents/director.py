"""Director Agent - Oversees all operations."""
from typing import Dict, List
from .base_agent import BaseAgent


class DirectorAgent(BaseAgent):
    """
    Director Agent acts like a CEO.
    - Sets priorities
    - Approves major changes
    - Coordinates other agents
    - Makes high-level decisions
    """
    
    def __init__(self):
        super().__init__(
            name="Director",
            role="System Overseer & Decision Maker",
            system_prompt="""You are the Director Agent overseeing an OCR system development project.

Your responsibilities:
1. Prioritize improvements based on impact
2. Approve or reject proposed changes from other agents
3. Coordinate testing, development, and evaluation agents
4. Make strategic decisions about system direction
5. Ensure changes align with goals: accuracy >95%, speed <5s, universal handling

Always consider:
- Risk vs reward of changes
- Impact on existing functionality
- Resource usage (don't overload Ollama server)
- User experience improvements

Be concise but thorough in your decisions."""
        )
    
    async def execute_task(self, task: Dict) -> Dict:
        """Execute a director task."""
        task_type = task.get("type")
        
        if task_type == "approve_change":
            return await self._approve_change(task)
        elif task_type == "set_priority":
            return await self._set_priority(task)
        elif task_type == "coordinate":
            return await self._coordinate_agents(task)
        else:
            return {"status": "unknown_task_type", "task_type": task_type}
    
    async def _approve_change(self, task: Dict) -> Dict:
        """Review and approve/reject a proposed change."""
        proposed_change = task.get("proposed_change", {})
        test_results = task.get("test_results", {})
        
        prompt = f"""Review this proposed change to the OCR system:

Proposal:
{proposed_change.get('description', 'No description')}

Test Results:
- Before: {test_results.get('before', 'N/A')}
- After: {test_results.get('after', 'N/A')}
- Improvement: {test_results.get('improvement', 'N/A')}

Should this change be approved? Respond with:
1. APPROVE or REJECT
2. Brief reasoning (2-3 sentences)

Format:
Decision: [APPROVE/REJECT]
Reasoning: [Your reasoning]"""
        
        response = await self.think(prompt, context=task)
        
        # Parse response
        decision = "REJECT"  # Default to safe
        if "APPROVE" in response.upper():
            decision = "APPROVE"
        
        return {
            "status": "reviewed",
            "decision": decision,
            "reasoning": response,
            "proposal": proposed_change
        }
    
    async def _set_priority(self, task: Dict) -> Dict:
        """Set priorities for improvement areas."""
        issues = task.get("issues", [])
        
        prompt = f"""Given these issues identified in the OCR system:

{chr(10).join(f"{i+1}. {issue}" for i, issue in enumerate(issues))}

Rank them by priority (1 = highest) considering:
- Impact on accuracy
- User experience
- Implementation difficulty
- Resource requirements

Respond with ranked list and brief justification."""
        
        response = await self.think(prompt, context={"issues": issues})
        
        return {
            "status": "prioritized",
            "ranking": response
        }
    
    async def _coordinate_agents(self, task: Dict) -> Dict:
        """Coordinate activities of other agents."""
        agent_statuses = task.get("agent_statuses", {})
        
        prompt = f"""Current agent statuses:

{chr(10).join(f"- {agent}: {status}" for agent, status in agent_statuses.items())}

What should each agent focus on next? Provide clear, actionable directions."""
        
        response = await self.think(prompt, context=agent_statuses)
        
        return {
            "status": "coordinated",
            "directives": response
        }

