"""
Mobile API - Push notifications and mobile-specific endpoints.
"""

from typing import Dict, List, Optional, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from backend.observability.logger import get_logger


class PushSubscription(BaseModel):
    """Push notification subscription."""
    endpoint: str
    keys: Dict[str, str]


class MobileNotification(BaseModel):
    """Mobile notification."""
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    tag: Optional[str] = None
    requireInteraction: bool = False
    actions: Optional[List[Dict[str, str]]] = None
    data: Optional[Dict[str, Any]] = None


class MobileAPIManager:
    """
    Manages mobile-specific features:
    - Push notifications
    - Device registration
    - Mobile-optimized responses
    
    Usage:
        mobile = MobileAPIManager()
        
        # Register device for push
        mobile.register_device(user_id, subscription)
        
        # Send notification
        mobile.send_notification(user_id, {
            "title": "Task Complete",
            "body": "Your code review is ready"
        })
    """
    
    def __init__(self):
        self.logger = get_logger()
        self._subscriptions: Dict[str, List[PushSubscription]] = {}
        self._devices: Dict[str, Dict[str, Any]] = {}
    
    def register_device(self, user_id: str, subscription: PushSubscription,
                       device_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a device for push notifications.
        
        Args:
            user_id: User ID
            subscription: Push subscription object
            device_info: Optional device information
            
        Returns:
            True if registered successfully
        """
        if user_id not in self._subscriptions:
            self._subscriptions[user_id] = []
        
        # Check if already registered
        for sub in self._subscriptions[user_id]:
            if sub.endpoint == subscription.endpoint:
                return True
        
        self._subscriptions[user_id].append(subscription)
        
        # Store device info
        device_id = subscription.endpoint.split('/')[-1][:16]
        self._devices[device_id] = {
            'user_id': user_id,
            'registered_at': datetime.now().isoformat(),
            'info': device_info or {},
            'last_active': datetime.now().isoformat()
        }
        
        self.logger.info(f"Device registered for user {user_id}: {device_id}")
        return True
    
    def unregister_device(self, user_id: str, endpoint: str) -> bool:
        """Unregister a device."""
        if user_id not in self._subscriptions:
            return False
        
        original_count = len(self._subscriptions[user_id])
        self._subscriptions[user_id] = [
            sub for sub in self._subscriptions[user_id]
            if sub.endpoint != endpoint
        ]
        
        return len(self._subscriptions[user_id]) < original_count
    
    def send_notification(self, user_id: str, notification: MobileNotification) -> bool:
        """
        Send push notification to user's devices.
        
        Args:
            user_id: Target user ID
            notification: Notification content
            
        Returns:
            True if sent to at least one device
        """
        if user_id not in self._subscriptions:
            return False
        
        success = False
        for subscription in self._subscriptions[user_id]:
            try:
                # In production, use web-push library
                # from pywebpush import webpush
                # webpush(subscription, notification.json())
                self.logger.info(f"Would send notification to {subscription.endpoint}")
                success = True
            except Exception as e:
                self.logger.error(f"Failed to send notification: {e}")
        
        return success
    
    def notify_task_complete(self, user_id: str, task_description: str,
                            result_summary: Optional[str] = None):
        """Send task completion notification."""
        return self.send_notification(user_id, MobileNotification(
            title="Task Complete",
            body=result_summary or f"Task finished: {task_description[:50]}...",
            tag="task-complete",
            requireInteraction=True,
            actions=[
                {"action": "view", "title": "View Result"},
                {"action": "dismiss", "title": "Dismiss"}
            ],
            data={"type": "task_complete", "timestamp": datetime.now().isoformat()}
        ))
    
    def notify_approval_needed(self, user_id: str, task_description: str,
                              task_id: str):
        """Send approval request notification."""
        return self.send_notification(user_id, MobileNotification(
            title="Approval Required",
            body=f"Review required: {task_description[:50]}...",
            tag=f"approval-{task_id}",
            requireInteraction=True,
            actions=[
                {"action": "approve", "title": "Approve"},
                {"action": "reject", "title": "Reject"},
                {"action": "view", "title": "View Details"}
            ],
            data={"type": "approval_needed", "task_id": task_id}
        ))
    
    def notify_code_review(self, user_id: str, file_name: str,
                          review_summary: str):
        """Send code review notification."""
        return self.send_notification(user_id, MobileNotification(
            title="Code Review Ready",
            body=f"{file_name}: {review_summary[:60]}...",
            tag="code-review",
            requireInteraction=True,
            actions=[
                {"action": "view", "title": "View Review"},
                {"action": "approve", "title": "Approve"}
            ],
            data={"type": "code_review", "file": file_name}
        ))
    
    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all registered devices for a user."""
        devices = []
        for device_id, info in self._devices.items():
            if info['user_id'] == user_id:
                devices.append({
                    'device_id': device_id,
                    **info
                })
        return devices
    
    def update_device_activity(self, device_id: str):
        """Update last active timestamp."""
        if device_id in self._devices:
            self._devices[device_id]['last_active'] = datetime.now().isoformat()


# Global instance
_mobile_manager: Optional[MobileAPIManager] = None


def get_mobile_manager() -> MobileAPIManager:
    """Get the global mobile API manager."""
    global _mobile_manager
    if _mobile_manager is None:
        _mobile_manager = MobileAPIManager()
    return _mobile_manager