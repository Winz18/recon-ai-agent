import autogen
import json
from typing import Dict, List, Optional

class ReconReporter:
    """
    Agent chuyên trách tổng hợp và báo cáo kết quả từ quá trình reconnaissance.
    """
    
    def __init__(self, llm_config: Dict):
        """
        Khởi tạo ReconReporter.
        
        Args:
            llm_config: Cấu hình LLM cho agent
        """
        self.llm_config = llm_config
        
        # Tạo agent reporter
        self.agent = autogen.AssistantAgent(
            name="Reconnaissance_Reporter",
            llm_config=llm_config,
            system_message="""You are a Reconnaissance Reporter specializing in security assessments.
            Your role is to analyze collected data and create comprehensive, well-structured reports.
            
            Your responsibilities include:
            1. Organizing reconnaissance findings into logical categories
            2. Identifying potential security issues and vulnerabilities
            3. Connecting different pieces of information to paint a complete picture
            4. Providing a risk assessment based on the gathered information
            5. Suggesting potential next steps for deeper security testing
            
            Your reports should be:
            - Clear and well-structured with proper headings
            - Technical but accessible to security professionals
            - Focused on actionable insights and security implications
            - Free of false positives or exaggerated claims
            - Based strictly on the evidence provided
            
            You excel at spotting security issues in DNS configurations, domain registrations,
            HTTP security headers, and understanding the attack surface of web applications."""
        )

    def generate_report(self, 
                      target_domain: str,
                      collected_data: Dict,
                      output_format: str = "markdown") -> str:
        """
        Tạo báo cáo từ dữ liệu thu thập được.
        
        Args:
            target_domain: Tên miền mục tiêu
            collected_data: Dữ liệu thu thập được (DNS, WHOIS, HTTP headers, subdomains...)
            output_format: Định dạng đầu ra (markdown, json, text)
            
        Returns:
            Báo cáo dạng chuỗi theo định dạng được chỉ định
        """
        # Tạo user proxy đặc biệt để yêu cầu báo cáo
        user_proxy = autogen.UserProxyAgent(
            name="Report_Requester",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            llm_config=False,
        )
        
        # Chuyển đổi dữ liệu thu thập được thành chuỗi JSON
        collected_data_str = json.dumps(collected_data, indent=2)
        
        # Tạo prompt yêu cầu báo cáo
        prompt = f"""Generate a security reconnaissance report for target domain: {target_domain}
        
        The report should be in {output_format} format.
        
        Here is the collected data:
        ```
        {collected_data_str}
        ```
        
        Your report should include:
        1. Executive Summary: Brief overview of findings and risk level
        2. Methodology: Tools and techniques used
        3. Findings: Detailed analysis of discoveries
           - Infrastructure Information (IP addresses, hosting details)
           - Domain Registration Analysis
           - Identified Subdomains
           - Web Server Configuration
           - Security Headers Analysis
        4. Security Implications: Potential vulnerabilities or security concerns
        5. Recommendations: Suggestions to improve security posture
        
        Make sure to create a professional, well-structured report that highlights
        important security findings. Use {output_format} formatting appropriately."""
        
        # Gửi prompt đến reporter
        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=prompt
        )
        
        # Lấy báo cáo từ tin nhắn cuối cùng
        report = self.agent.last_message()["content"]
        
        return report
        
    def summarize_findings(self, collected_data: Dict, max_length: int = 500) -> str:
        """
        Tạo tóm tắt ngắn gọn từ dữ liệu thu thập được.
        
        Args:
            collected_data: Dữ liệu thu thập được
            max_length: Độ dài tối đa của tóm tắt
            
        Returns:
            Chuỗi tóm tắt các phát hiện chính
        """
        # Tạo user proxy đặc biệt để yêu cầu tóm tắt
        user_proxy = autogen.UserProxyAgent(
            name="Summary_Requester",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            llm_config=False,
        )
        
        # Chuyển đổi dữ liệu thu thập được thành chuỗi JSON
        collected_data_str = json.dumps(collected_data, indent=2)
        
        # Tạo prompt yêu cầu tóm tắt
        prompt = f"""Provide a brief summary of the key reconnaissance findings from this data:
        ```
        {collected_data_str}
        ```
        
        Focus only on the most important security-relevant facts.
        Your summary should be concise (maximum {max_length} characters) but include critical findings
        and potential security implications. Prioritize actionable security insights."""
        
        # Gửi prompt đến reporter
        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=prompt
        )
        
        # Lấy tóm tắt từ tin nhắn cuối cùng
        summary = self.agent.last_message()["content"]
        
        # Đảm bảo không vượt quá độ dài tối đa
        return summary[:max_length] if len(summary) > max_length else summary