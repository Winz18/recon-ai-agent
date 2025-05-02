import autogen
from typing import Dict, List, Optional, Union

class ReconPlanner:
    """
    Agent chuyên trách xây dựng kế hoạch cho việc thu thập thông tin.
    Lập kế hoạch dựa trên tên miền mục tiêu và các công cụ có sẵn.
    """
    
    def __init__(
        self,
        llm_config: Dict,
        team_members: Optional[List[autogen.ConversableAgent]] = None
    ):
        """
        Khởi tạo ReconPlanner.
        
        Args:
            llm_config: Cấu hình LLM cho agent
            team_members: Danh sách các agent khác trong team (nếu có)
        """
        self.llm_config = llm_config
        self.team_members = team_members or []
        
        # Tạo agent planner
        self.agent = autogen.AssistantAgent(
            name="Reconnaissance_Planner",
            llm_config=llm_config,
            system_message="""You are a Reconnaissance Planner for penetration testing. 
            Your role is to analyze targets and create organized, methodical plans for information gathering.
            
            Your responsibilities include:
            1. Breaking down reconnaissance tasks into logical steps
            2. Prioritizing which information to gather first
            3. Identifying potential security implications from gathered data
            4. Deciding when enough information has been collected
            
            You think strategically, considering how each piece of information relates 
            to potential vulnerabilities or attack vectors. You are methodical, thorough,
            and focused on creating a complete picture of the target.
            
            You communicate clearly and provide reasoning for why each step in your plan is important."""
        )
    
    def create_plan(self, target_domain: str, available_tools: List[str]) -> Dict:
        """
        Tạo kế hoạch thu thập thông tin cho tên miền mục tiêu.
        
        Args:
            target_domain: Tên miền mục tiêu
            available_tools: Danh sách các công cụ có sẵn
            
        Returns:
            Dictionary chứa kế hoạch với các bước thực hiện
        """
        # Tạo user proxy đặc biệt để lấy kế hoạch
        user_proxy = autogen.UserProxyAgent(
            name="Plan_Requester",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            llm_config=False,
        )
        
        # Tạo prompt yêu cầu kế hoạch
        prompt = f"""Generate a reconnaissance plan for target domain: {target_domain}
        
        Available tools: {', '.join(available_tools)}
        
        The plan should include:
        1. A clear sequence of steps to follow
        2. Which tools to use at each step
        3. What information to look for
        4. How findings might relate to potential vulnerabilities
        5. Success criteria for each step
        
        Format your plan as a structured JSON object with numbered steps."""
        
        # Gửi prompt đến planner
        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=prompt
        )
        
        # Parse kết quả trong nội dung của tin nhắn cuối cùng
        # Lý tưởng nhất là parse JSON, nhưng có thể cần xử lý thêm
        plan_text = self.agent.last_message()["content"]
        
        # Trả về kế hoạch dưới dạng dictionary
        return {
            "target_domain": target_domain,
            "available_tools": available_tools,
            "plan": plan_text
        }