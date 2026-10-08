"""Experimental kernel boundary; no fabricated tool results."""
class AIOSKernel:
    def __init__(self, memory_manager, ai_client):
        self.memory = memory_manager
        self.ai_client = ai_client

    async def execute_goal(self, session_id, candidate_id, user_query, preferences):
        raise NotImplementedError("AI OS planning/execution is not implemented; use the legacy supervisor workflow.")
