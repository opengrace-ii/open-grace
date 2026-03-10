"""
Email Tool for TaskForge.
Handles email checking and basic operations using IMAP.
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from tools.base_tool import BaseTool, ToolOutput


class EmailToolInput(BaseModel):
    """Input schema for EmailTool."""
    action: str = Field(..., description="Action to perform: check, read, search")
    server: Optional[str] = Field(default="imap.gmail.com", description="IMAP server address")
    username: Optional[str] = Field(default=None, description="Email username")
    password: Optional[str] = Field(default=None, description="Email password or app password")
    folder: Optional[str] = Field(default="INBOX", description="Email folder to check")
    limit: Optional[int] = Field(default=10, description="Maximum number of emails to retrieve")
    subject_filter: Optional[str] = Field(default=None, description="Filter by subject keywords")


class EmailTool(BaseTool):
    """
    Tool for email operations.
    
    Supported actions:
    - check: Check for new emails and return count + summaries
    - read: Read specific email content
    - search: Search emails by subject or content
    
    Note: For Gmail, you need to use an App Password, not your regular password.
    Enable 2FA and generate an App Password at: https://myaccount.google.com/apppasswords
    """
    
    name = "email"
    description = "Check and read emails via IMAP (Gmail, Outlook, etc.)"
    input_schema = EmailToolInput
    
    VALID_ACTIONS = ["check", "read", "search"]
    
    def run(self, action: str, server: str = "imap.gmail.com", 
            username: Optional[str] = None, password: Optional[str] = None,
            folder: str = "INBOX", limit: int = 10,
            subject_filter: Optional[str] = None, **kwargs) -> ToolOutput:
        """Execute email operation."""
        try:
            action = action.lower()
            if action not in self.VALID_ACTIONS:
                return ToolOutput(
                    success=False,
                    error=f"Invalid action '{action}'. Valid actions: {', '.join(self.VALID_ACTIONS)}"
                )
            
            # For security, don't require credentials in the tool call
            # User should set environment variables or we'll use defaults for demo
            if not username:
                return ToolOutput(
                    success=False,
                    error="Email username required. Set EMAIL_USER environment variable or provide username."
                )
            
            if not password:
                return ToolOutput(
                    success=False,
                    error="Email password required. Set EMAIL_PASS environment variable or provide password. For Gmail, use App Password."
                )
            
            method = getattr(self, f"_action_{action}")
            result = method(server, username, password, folder, limit, subject_filter)
            
            return ToolOutput(success=True, result=result)
            
        except Exception as e:
            return ToolOutput(
                success=False,
                error=f"Email operation error: {str(e)}"
            )
    
    def _action_check(self, server: str, username: str, password: str,
                      folder: str, limit: int, subject_filter: Optional[str]) -> dict:
        """Check for new emails."""
        mail = imaplib.IMAP4_SSL(server)
        mail.login(username, password)
        mail.select(folder)
        
        # Search for all emails
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()
        total_count = len(email_ids)
        
        # Get recent emails
        recent_emails = []
        for i in range(min(limit, len(email_ids))):
            email_id = email_ids[-(i+1)]  # Get from newest
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject = self._decode_header(msg["Subject"])
                    from_addr = self._decode_header(msg["From"])
                    date = msg["Date"]
                    
                    # Apply subject filter if provided
                    if subject_filter and subject_filter.lower() not in subject.lower():
                        continue
                    
                    recent_emails.append({
                        "id": email_id.decode(),
                        "subject": subject,
                        "from": from_addr,
                        "date": date
                    })
        
        mail.close()
        mail.logout()
        
        return {
            "total_emails": total_count,
            "checked": len(recent_emails),
            "recent_emails": recent_emails,
            "folder": folder
        }
    
    def _action_read(self, server: str, username: str, password: str,
                     folder: str, limit: int, subject_filter: Optional[str]) -> dict:
        """Read email content."""
        # Similar to check but includes body content
        mail = imaplib.IMAP4_SSL(server)
        mail.login(username, password)
        mail.select(folder)
        
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()
        
        emails = []
        for i in range(min(limit, len(email_ids))):
            email_id = email_ids[-(i+1)]
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject = self._decode_header(msg["Subject"])
                    from_addr = self._decode_header(msg["From"])
                    date = msg["Date"]
                    
                    if subject_filter and subject_filter.lower() not in subject.lower():
                        continue
                    
                    # Get email body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode()
                                    break
                                except:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode()
                        except:
                            body = "[Unable to decode message body]"
                    
                    # Truncate body for summary
                    body_preview = body[:500] + "..." if len(body) > 500 else body
                    
                    emails.append({
                        "id": email_id.decode(),
                        "subject": subject,
                        "from": from_addr,
                        "date": date,
                        "body_preview": body_preview.strip()
                    })
        
        mail.close()
        mail.logout()
        
        return {
            "emails_read": len(emails),
            "emails": emails,
            "folder": folder
        }
    
    def _action_search(self, server: str, username: str, password: str,
                       folder: str, limit: int, subject_filter: Optional[str]) -> dict:
        """Search emails by subject."""
        if not subject_filter:
            return {
                "error": "subject_filter required for search action",
                "emails_found": 0,
                "emails": []
            }
        
        return self._action_read(server, username, password, folder, limit, subject_filter)
    
    def _decode_header(self, header: Optional[str]) -> str:
        """Decode email header."""
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_string = ""
        
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(charset or 'utf-8')
                except:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string
