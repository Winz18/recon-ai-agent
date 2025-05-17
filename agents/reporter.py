import autogen
import json
import os
import datetime
import re
from typing import Dict, List, Optional, Tuple, Any

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
            HTTP security headers, and understanding the attack surface of web applications.
              IMPORTANT: Go beyond just listing findings. You must:
            
            1. IDENTIFY VULNERABILITIES: Point out specific security issues and explain their implications.
               Example: "The missing X-Frame-Options header creates a vulnerability to clickjacking attacks
               that could trick users into performing unintended actions."
            
            2. CONNECT RELATED INFORMATION: Look for patterns and relationships between different findings.
               Example: "The domain was registered recently (per WHOIS data) and has minimal DNS records,
               suggesting this may be a newly deployed system that could have security gaps typical of
               new deployments."
               
            3. ASSIGN RISK LEVELS: Categorize findings by severity (Critical, High, Medium, Low) based on:
               - Potential impact if exploited
               - Likelihood of exploitation
               - Presence of mitigating factors
               
            4. PRIORITIZE RECOMMENDATIONS: Offer specific, actionable recommendations prioritized by:
               - Impact on security posture
               - Implementation complexity
               - Long-term sustainability

            5. PERFORM DEEPER ANALYSIS:
               - When analyzing HTTP headers, explicitly identify missing security headers and
                 their implications (e.g., "Missing Content-Security-Policy allows XSS attacks")
               - For DNS information, identify unusual records or configurations that might
                 indicate security risks
               - When examining WHOIS data, note discrepancies, recent changes, or privacy
                 protections that might be security-relevant
               - Look for correlations between subdomain information and other data points
               - Reference known vulnerabilities (CVEs) if applicable
               - Identify outdated technologies and their associated vulnerabilities
               - Analyze SPF, DKIM, and DMARC records for email security issues
               - Check for subdomains that might be vulnerable to takeover
               
            6. EVALUATE ATTACK SURFACE:
               - Identify potential entry points based on collected information
               - Highlight areas where further testing would be most beneficial
               - Note any unusual or concerning services exposed
               - Analyze potential for social engineering based on discovered information
               - Consider supply chain vulnerabilities if third-party services are identified
               - Evaluate protection against common attack vectors (XSS, CSRF, injection, etc.)
               - Assess the organization's security posture compared to industry standards
               
            7. CONTEXTUALIZE FINDINGS:
               - Compare findings against industry best practices
               - Consider the organization type (e.g., financial, healthcare, government)
               - Assess whether security controls are proportional to likely threats
               - Identify areas where security-in-depth principles are not being followed
               - Note compliance implications (GDPR, HIPAA, PCI-DSS, etc.) when applicable
               
            Your analysis should reflect a deep understanding of modern web security, threat modeling,
            and defensive best practices. Be thorough in connecting related pieces of information to
            provide a holistic security assessment."""
        )
        
    def generate_report(self, 
                        target_domain: str,
                        collected_data: Dict,
                        output_format: str = "markdown",
                        save_report: bool = True,
                        save_raw_data: bool = True,
                        report_type: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Tạo báo cáo từ dữ liệu thu thập được.
        
        Args:
            target_domain: Tên miền mục tiêu
            collected_data: Dữ liệu thu thập được (DNS, WHOIS, HTTP headers, subdomains...)
            output_format: Định dạng đầu ra ("markdown", "json", "html")
            save_report: Có lưu báo cáo hay không
            save_raw_data: Có lưu dữ liệu thô hay không
            report_type: Loại báo cáo ("standard", "comprehensive", "targeted_web", etc.)
            
        Returns:
            Tuple chứa:
              - Báo cáo dạng chuỗi theo định dạng được chỉ định
              - Đường dẫn đến file báo cáo (nếu được lưu)
        """
        # Kiểm tra và tạo thư mục lưu báo cáo nếu cần
        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        raw_data_dir = os.path.join(report_dir, "raw_data")
        
        if save_report and not os.path.exists(report_dir):
            os.makedirs(report_dir)
            
        if save_raw_data and not os.path.exists(raw_data_dir):
            os.makedirs(raw_data_dir)
            
        # Lưu dữ liệu thô nếu được yêu cầu
        raw_data_path = None
        if save_raw_data:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_data_filename = f"raw_{target_domain.replace('.', '_')}_{timestamp}.json"
            raw_data_path = os.path.join(raw_data_dir, raw_data_filename)
            
            with open(raw_data_path, "w", encoding="utf-8") as f:
                json.dump(collected_data, f, indent=2)
                
        # Tạo user proxy đặc biệt để yêu cầu báo cáo
        user_proxy = autogen.UserProxyAgent(
            name="Report_Requester",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config={"use_docker": False},  # Disable Docker usage
            llm_config=False,
        )
        
        # Chuyển đổi dữ liệu thu thập được thành chuỗi JSON
        collected_data_str = json.dumps(collected_data, indent=2)
        
        # Điều chỉnh prompt theo định dạng đầu ra
        format_instructions = ""
        if output_format.lower() == "markdown":
            format_instructions = """Use Markdown formatting with proper headings (# for title, ## for sections, etc.), 
            lists, and code blocks. Make sure to format tables properly with Markdown syntax for better readability."""
        elif output_format.lower() == "html":
            format_instructions = """Format your report as HTML with proper structure:
            - Include <html>, <head>, and <body> tags
            - Use <h1> for the title, <h2> for major sections, <h3> for subsections
            - Style with simple CSS for readability (inside a <style> tag) 
              including responsive design and a clean, professional layout
            - Use <table> for structured data with proper headers and styling
            - Include <div> sections for each main category of findings
            - Use color coding for risk levels (red for Critical, orange for High, etc.)
            - Add collapsible sections for detailed technical information
            - Include a table of contents with anchor links
            - Format code and technical details in <pre> or <code> tags"""
        elif output_format.lower() == "json":
            format_instructions = """Return your report as a well-structured JSON object with the following schema:
            {
              "report_title": "Security Reconnaissance Report",
              "target_domain": "domain.com",
              "report_date": "YYYY-MM-DD",
              "scan_timestamp": "YYYY-MM-DDTHH:MM:SSZ",
              "executive_summary": { 
                "overview": "text", 
                "risk_level": "Low/Medium/High/Critical",
                "key_findings_count": {
                  "critical": 0,
                  "high": 0,
                  "medium": 0,
                  "low": 0
                }
              },
              "methodology": { 
                "description": "text", 
                "tools_used": ["tool1", "tool2"] 
              },
              "findings": {
                "infrastructure": { 
                  "description": "text", 
                  "ip_addresses": [],
                  "hosting_details": {},
                  "security_implications": [],
                  "risk_level": "Low/Medium/High/Critical"
                },
                "domain_registration": { 
                  "description": "text", 
                  "registration_date": "",
                  "expiry_date": "",
                  "registrar": "",
                  "privacy_protection": true|false,
                  "security_implications": [],
                  "risk_level": "Low/Medium/High/Critical"
                },
                "subdomains": { 
                  "count": 0, 
                  "details": [],
                  "security_implications": [],
                  "risk_level": "Low/Medium/High/Critical"
                },
                "web_server": { 
                  "description": "text", 
                  "server_type": "",
                  "technologies": [],
                  "security_implications": [],
                  "risk_level": "Low/Medium/High/Critical"
                },
                "security_headers": { 
                  "description": "text", 
                  "present_headers": {},
                  "missing_headers": [],
                  "header_issues": [],
                  "security_implications": [],
                  "risk_level": "Low/Medium/High/Critical"
                }
              },
              "vulnerabilities": [
                { 
                  "id": "VULN-001",
                  "title": "Vulnerability Name",
                  "description": "text", 
                  "affected_area": "Area of impact",
                  "severity": "Low/Medium/High/Critical",
                  "evidence": "text",
                  "cwe_id": "CWE-XXX",
                  "remediation": "text"
                }
              ],
              "correlations": [
                {
                  "description": "Correlation between different findings",
                  "related_elements": ["element1", "element2"],
                  "security_implication": "text",
                  "risk_level": "Low/Medium/High/Critical"
                }
              ],
              "recommendations": [
                { 
                  "id": "REC-001",
                  "title": "Recommendation Title", 
                  "description": "text", 
                  "priority": "Low/Medium/High",
                  "implementation_complexity": "Low/Medium/High",
                  "related_vulnerabilities": ["VULN-001"] 
                }
              ],
              "next_steps": [
                "Suggested next reconnaissance activities"
              ],
              "raw_data_reference": "Path to raw data file if stored"
            }"""
        else:
            # Default to text
            format_instructions = "Provide a plain text report with clear section breaks and consistent formatting."
        
        # Tạo prompt yêu cầu báo cáo
        report_type_info = ""
        if report_type:
            report_type_info = f" This is a {report_type} report."
        
        prompt = f"""Generate a security reconnaissance report for target domain: {target_domain}{report_type_info}
        
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
        4. Security Implications: Potential vulnerabilities or security concerns (with severity ratings)
        5. Recommendations: Suggestions to improve security posture (prioritized)
        
        {format_instructions}
        
        Make sure to create a professional, well-structured report that highlights
        important security findings and clearly identifies vulnerabilities and risks.
        
        IMPORTANT:
        1. Explicitly identify security vulnerabilities based on the findings
        2. Connect related pieces of information to provide deeper insights
        3. Assign appropriate risk levels to each finding
        4. Provide prioritized, actionable recommendations"""
            # Gửi prompt đến reporter
        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=prompt
        )
        
        # Lấy báo cáo từ tin nhắn cuối cùng
        try:
            # Try to get the last message from the agent in response to the user_proxy
            report = self.agent.last_message(user_proxy)["content"]
        except (ValueError, KeyError, AttributeError, TypeError):
            # Fallback: get the last message in the conversation history
            if chat_result and "report" in chat_result:
                report = chat_result["report"]
            elif hasattr(self.agent, 'messages') and self.agent.messages:
                # Get the last message where the agent is the sender
                agent_messages = [msg for msg in self.agent.messages if msg.get("role") == "assistant"]
                if agent_messages:
                    report = agent_messages[-1].get("content", "Failed to retrieve report.")
                else:
                    report = "Failed to retrieve report."
            else:
                report = "Failed to retrieve report."
        
        # Nếu format là JSON, đảm bảo đầu ra là JSON hợp lệ
        if output_format.lower() == "json":
            report = self._ensure_valid_json(report)
        
        # Lưu báo cáo nếu được yêu cầu
        report_path = None
        if save_report:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Xác định phần mở rộng phù hợp
            extension = ".txt"  # Mặc định
            if output_format.lower() == "markdown":
                extension = ".md"
            elif output_format.lower() == "html":
                extension = ".html"
            elif output_format.lower() == "json":
                extension = ".json"
                
            # Add report_type to filename if provided
            report_name = f"report_{target_domain.replace('.', '_')}"
            if report_type:
                report_name += f"_{report_type}"
            report_filename = f"{report_name}_{timestamp}{extension}"
            
            report_path = os.path.join(report_dir, report_filename)
            
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
                
        return report, report_path
    
    def _ensure_valid_json(self, json_str: str) -> str:
        """
        Đảm bảo chuỗi đầu ra là JSON hợp lệ.
        
        Args:
            json_str: Chuỗi JSON cần kiểm tra
            
        Returns:
            Chuỗi JSON hợp lệ
        """
        # Tìm JSON trong đầu ra (đôi khi LLM sẽ bọc JSON trong các thẻ code)
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, json_str)
        
        if json_match:
            json_str = json_match.group(1).strip()
        
        # Kiểm tra xem chuỗi đã là JSON hợp lệ chưa
        try:
            json_obj = json.loads(json_str)
            return json.dumps(json_obj, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # Nếu không phải JSON hợp lệ, tạo một JSON đơn giản
            return json.dumps({
                "report_title": "Security Reconnaissance Report - Error",
                "report_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "error": "Could not generate valid JSON report",
                "raw_content": json_str[:1000]  # Giới hạn kích thước
            }, indent=2, ensure_ascii=False)
          
    def summarize_findings(self, 
                          collected_data: Dict, 
                          max_length: int = 500,
                          include_risk_assessment: bool = True,
                          output_format: str = "text") -> str:
        """
        Tạo tóm tắt ngắn gọn từ dữ liệu thu thập được.
        
        Args:
            collected_data: Dữ liệu thu thập được
            max_length: Độ dài tối đa của tóm tắt
            include_risk_assessment: Có thêm đánh giá rủi ro tổng thể hay không
            output_format: Định dạng đầu ra ("text", "json", "markdown", "html")
            
        Returns:
            Chuỗi tóm tắt các phát hiện chính
        """        
        # Tạo user proxy đặc biệt để yêu cầu tóm tắt
        user_proxy = autogen.UserProxyAgent(
            name="Summary_Requester",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config={"use_docker": False},  # Disable Docker usage
            llm_config=False,
        )
        
        # Chuyển đổi dữ liệu thu thập được thành chuỗi JSON
        collected_data_str = json.dumps(collected_data, indent=2)
        
        # Tạo prompt phụ thuộc vào định dạng đầu ra
        format_specific = ""
        if output_format.lower() == "json":
            format_specific = """Return your summary as a JSON object with the following structure:
            {
              "summary": "Text summary of findings",
              "risk_assessment": "Critical/High/Medium/Low",
              "risk_justification": "Brief justification for risk level",
              "key_vulnerabilities": [
                {"name": "Vulnerability name", "severity": "Critical/High/Medium/Low"}
              ],
              "top_recommendations": [
                "First recommendation", "Second recommendation"
              ]
            }"""
        elif output_format.lower() == "markdown":
            format_specific = "Format your summary with Markdown, using headings (##) for main sections."
        elif output_format.lower() == "html":
            format_specific = "Format your summary with basic HTML tags (<h2> for sections, <ul> for lists)."
        
        # Tạo prompt yêu cầu tóm tắt
        risk_prompt = """
        Also include a risk assessment rating (Critical, High, Medium, or Low) with a one-sentence justification.
        """ if include_risk_assessment else ""
        
        prompt = f"""Provide a brief summary of the key reconnaissance findings from this data:
        ```
        {collected_data_str}
        ```
        
        Focus only on the most important security-relevant facts.
        Your summary should be concise (maximum {max_length} characters) but include critical findings
        and potential security implications. Prioritize actionable security insights.
        {risk_prompt}
        If you identify specific vulnerabilities, highlight them clearly.
        
        {format_specific}"""
          # Gửi prompt đến reporter
        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=prompt
        )
        
        # Lấy tóm tắt từ tin nhắn cuối cùng
        try:
            # Try to get the last message from the agent in response to the user_proxy
            summary = self.agent.last_message(user_proxy)["content"]
        except (ValueError, KeyError, AttributeError, TypeError):
            # Fallback: get the last message in the conversation history
            if chat_result and "summary" in chat_result:
                summary = chat_result["summary"]
            elif hasattr(self.agent, 'messages') and self.agent.messages:
                # Get the last message where the agent is the sender
                agent_messages = [msg for msg in self.agent.messages if msg.get("role") == "assistant"]
                if agent_messages:
                    summary = agent_messages[-1].get("content", "Failed to retrieve summary.")
                else:
                    summary = "Failed to retrieve summary."
            else:
                summary = "Failed to retrieve summary."
        
        # Xử lý đầu ra dựa trên định dạng
        if output_format.lower() == "json":
            return self._ensure_valid_json(summary)
        
        # Đảm bảo không vượt quá độ dài tối đa cho các định dạng khác
        return summary[:max_length] if len(summary) > max_length else summary
    
    def get_vulnerabilities(self, collected_data: Dict) -> List[Dict[str, Any]]:
        """
        Phân tích và trích xuất các lỗ hổng tiềm ẩn từ dữ liệu thu thập được.
        
        Args:
            collected_data: Dữ liệu thu thập được từ quá trình reconnaissance
            
        Returns:
            Danh sách các lỗ hổng với thông tin chi tiết
        """
        # Tạo user proxy đặc biệt 
        user_proxy = autogen.UserProxyAgent(
            name="Vulnerability_Analyzer",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config={"use_docker": False},
            llm_config=False,
        )
        
        # Chuyển đổi dữ liệu thu thập được thành chuỗi JSON
        collected_data_str = json.dumps(collected_data, indent=2)
        
        # Prompt yêu cầu phân tích lỗ hổng
        prompt = f"""Analyze the following reconnaissance data and identify potential security vulnerabilities:
        ```
        {collected_data_str}
        ```
        
        For each vulnerability you identify, provide:
        1. A clear title/name for the vulnerability
        2. A detailed description of the vulnerability 
        3. The severity level (Critical, High, Medium, Low)
        4. How it could be exploited
        5. Recommended mitigation steps
        
        Return the results as a well-structured JSON array of vulnerability objects.
        Each object should have the following structure:
        
        [
          {{
            "title": "Descriptive vulnerability name",
            "description": "Detailed explanation of the vulnerability",
            "severity": "Critical/High/Medium/Low",
            "exploitation_vector": "How this could be exploited",
            "evidence": "Evidence from the reconnaissance data",
            "mitigation": "Recommended fix or mitigation"
          }}
        ]
        
        Focus only on legitimate vulnerabilities that are supported by evidence in the data.
        Do not speculate beyond what the data shows."""
          # Gửi prompt đến agent
        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=prompt
        )
        
        # Lấy kết quả từ tin nhắn cuối cùng
        try:
            # Try to get the last message from the agent in response to the user_proxy
            results = self.agent.last_message(user_proxy)["content"]
        except (ValueError, KeyError, AttributeError, TypeError):
            # Fallback: get the last message in the conversation history
            if hasattr(self.agent, 'messages') and self.agent.messages:
                # Get the last message where the agent is the sender
                agent_messages = [msg for msg in self.agent.messages if msg.get("role") == "assistant"]
                if agent_messages:
                    results = agent_messages[-1].get("content", "[]")
                else:
                    results = "[]"
            else:
                try:
                    results = self.agent.last_message()["content"] 
                except (AttributeError, TypeError):
                    return []
        
        # Trích xuất JSON từ kết quả
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, results)
        
        if json_match:
            results = json_match.group(1).strip()
        
        try:
            vulnerabilities = json.loads(results)
            return vulnerabilities
        except json.JSONDecodeError:
            return []
    
    def export_report_as_json(self, markdown_report: str) -> Dict[str, Any]:
        """
        Chuyển đổi báo cáo Markdown thành cấu trúc JSON.
        
        Args:
            markdown_report: Báo cáo ở định dạng Markdown
            
        Returns:
            Báo cáo ở định dạng JSON
        """
        # Tạo user proxy đặc biệt để chuyển đổi
        user_proxy = autogen.UserProxyAgent(
            name="Format_Converter",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config={"use_docker": False},
            llm_config=False,
        )
        
        # Prompt yêu cầu chuyển đổi
        prompt = f"""Convert the following Markdown report into a structured JSON object:
        ```markdown
        {markdown_report}
        ```
        
        The JSON object should have the following structure:
        {{
          "report_title": "Title from the report",
          "target_domain": "Domain from the report or current date",
          "report_date": "Date from the report or current date",
          "executive_summary": {{ 
            "overview": "Text from executive summary", 
            "risk_level": "Risk level mentioned in the report"
          }},
          "methodology": {{ 
            "description": "Methodology description", 
            "tools_used": ["tool1", "tool2"] 
          }},
          "findings": {{
            "infrastructure": {{ 
              "description": "Description from report", 
              "details": {{ ... details extracted from report ... }}
            }},
            "domain_registration": {{ 
              "description": "Description from report", 
              "details": {{ ... details extracted from report ... }}
            }},
            "subdomains": {{ 
              "count": 0, 
              "details": [ ... array of subdomains from report ... ]
            }},
            "web_server": {{ 
              "description": "Description from report", 
              "details": {{ ... details extracted from report ... }}
            }},
            "security_headers": {{ 
              "description": "Description from report", 
              "details": {{ ... details extracted from report ... }}
            }}
          }},
          "vulnerabilities": [
            {{ 
              "title": "Vulnerability name from report",
              "description": "Description from report", 
              "severity": "Severity from report"
            }}
          ],
          "recommendations": [
            {{ 
              "title": "Recommendation from report", 
              "description": "Description from report", 
              "priority": "Priority from report"
            }}
          ]
        }}
        
        Extract as much information as possible from the markdown and organize it according to this structure.
        Return only valid JSON, with no additional text or explanation."""
          # Gửi prompt đến agent
        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=prompt
        )
        
        # Lấy kết quả từ tin nhắn cuối cùng
        try:
            # Try to get the last message from the agent in response to the user_proxy
            result = self.agent.last_message(user_proxy)["content"]
        except (ValueError, KeyError, AttributeError, TypeError):
            # Fallback: get the last message in the conversation history
            if hasattr(self.agent, 'messages') and self.agent.messages:
                # Get the last message where the agent is the sender
                agent_messages = [msg for msg in self.agent.messages if msg.get("role") == "assistant"]
                if agent_messages:
                    result = agent_messages[-1].get("content", "{}")
                else:
                    result = "{}"
            else:
                try:
                    result = self.agent.last_message()["content"]
                except (AttributeError, TypeError):
                    return {"error": "Failed to convert report"}
        
        # Tìm JSON trong kết quả
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        json_match = re.search(json_pattern, result)
        
        if json_match:
            result = json_match.group(1).strip()
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw_content": result[:1000]}
    
    def save_raw_data(self, target_domain: str, collected_data: Dict) -> str:
        """
        Lưu dữ liệu thô vào thư mục raw_data.
        
        Args:
            target_domain: Tên miền mục tiêu
            collected_data: Dữ liệu thu thập được
            
        Returns:
            Đường dẫn đến file dữ liệu thô
        """
        # Tạo thư mục nếu cần
        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        raw_data_dir = os.path.join(report_dir, "raw_data")
        
        if not os.path.exists(raw_data_dir):
            os.makedirs(raw_data_dir)
        
        # Tạo tên file với timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_{target_domain.replace('.', '_')}_{timestamp}.json"
        filepath = os.path.join(raw_data_dir, filename)
        
        # Ghi dữ liệu ra file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(collected_data, f, indent=2, ensure_ascii=False)
            
        return filepath
