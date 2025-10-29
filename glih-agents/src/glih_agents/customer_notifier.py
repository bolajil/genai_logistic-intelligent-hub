from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CustomerNotifier:
    """Generate and send proactive customer notifications for Lineage Logistics."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.default_channel = config.get('customer_notification_channel', 'email')
        self.notification_tone = config.get('customer_notification_tone', 'professional')
        self.proactive_updates = config.get('customer_proactive_updates', True)
    
    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Retrieve customer preferences and profile."""
        # Simulated customer profiles (in production, would query customer database)
        profiles = {
            'CUST-001': {
                'name': 'Whole Foods Market',
                'contact_name': 'Sarah Johnson',
                'email': 'sarah.johnson@wholefoods.com',
                'phone': '+1-555-0101',
                'channel': 'email',
                'preferred_tone': 'professional',
                'notification_frequency': 'all_updates',
                'webhook_url': None
            },
            'CUST-002': {
                'name': 'Restaurant Depot',
                'contact_name': 'Mike Chen',
                'email': 'mike.chen@restaurantdepot.com',
                'phone': '+1-555-0202',
                'channel': 'sms',
                'preferred_tone': 'concise',
                'notification_frequency': 'critical_only',
                'webhook_url': None
            },
            'CUST-003': {
                'name': 'Amazon Fresh',
                'contact_name': 'API Integration',
                'email': 'logistics@amazonfresh.com',
                'phone': None,
                'channel': 'webhook',
                'preferred_tone': 'technical',
                'notification_frequency': 'all_updates',
                'webhook_url': 'https://api.amazonfresh.com/webhooks/lineage'
            }
        }
        
        return profiles.get(customer_id, {
            'name': 'Valued Customer',
            'contact_name': 'Customer',
            'email': 'customer@example.com',
            'phone': None,
            'channel': self.default_channel,
            'preferred_tone': self.notification_tone,
            'notification_frequency': 'all_updates',
            'webhook_url': None
        })
    
    def get_notification_template(self, notification_type: str) -> str:
        """Get template for notification type."""
        templates = {
            'delay': """Your shipment {shipment_id} is experiencing a delay. 
                        New estimated delivery: {new_eta}. 
                        Reason: {reason}. 
                        We apologize for any inconvenience.""",
            
            'arrival': """Your shipment {shipment_id} has arrived at {location}. 
                         Estimated delivery: {eta}. 
                         All items are in good condition.""",
            
            'issue': """We've detected an issue with shipment {shipment_id}. 
                        Issue: {issue_description}. 
                        Action taken: {action_taken}. 
                        We're monitoring closely and will keep you updated.""",
            
            'delivered': """Your shipment {shipment_id} has been successfully delivered. 
                           Delivery time: {delivery_time}. 
                           Thank you for choosing Lineage Logistics.""",
            
            'temperature_breach': """Temperature monitoring alert for shipment {shipment_id}. 
                                    Current temperature: {temperature}°C (Expected: {expected_range}°C). 
                                    Action: {action}. 
                                    Product quality: {quality_status}."""
        }
        
        return templates.get(notification_type, "Update regarding your shipment {shipment_id}.")
    
    def generate_message(self, event: Dict[str, Any], customer: Dict[str, Any], template: str) -> str:
        """Generate personalized message based on event and customer preferences."""
        # Format template with event details
        message = template.format(**event)
        
        # Adjust tone based on customer preference
        tone = customer.get('preferred_tone', 'professional')
        
        if tone == 'concise':
            # Shorten message for SMS
            lines = message.split('.')
            message = '. '.join(lines[:2]) + '.'
        elif tone == 'technical':
            # Add technical details for API consumers
            message += f"\n\nTechnical Details: Event ID: {event.get('event_id')}, Timestamp: {event.get('timestamp')}"
        
        # Add greeting and signature for email
        if customer.get('channel') == 'email':
            greeting = f"Dear {customer.get('contact_name', 'Customer')},\n\n"
            signature = "\n\nBest regards,\nLineage Logistics Operations Team\n\nFor questions, contact: support@lineagelogistics.com"
            message = greeting + message + signature
        
        return message
    
    def send_notification(self, customer: Dict[str, Any], message: str, event: Dict[str, Any]) -> Dict[str, str]:
        """Send notification via customer's preferred channel."""
        channel = customer.get('channel', 'email')
        
        if channel == 'email':
            return self._send_email(customer.get('email'), message, event)
        elif channel == 'sms':
            return self._send_sms(customer.get('phone'), message, event)
        elif channel == 'webhook':
            return self._send_webhook(customer.get('webhook_url'), event)
        else:
            return {'status': 'error', 'message': f'Unknown channel: {channel}'}
    
    def _send_email(self, email: str, message: str, event: Dict[str, Any]) -> Dict[str, str]:
        """Send email notification (simulated)."""
        logger.info(f"Sending email to {email}")
        # In production, would use SMTP or email service API
        return {
            'status': 'sent',
            'channel': 'email',
            'recipient': email,
            'message_id': f"email-{datetime.now().timestamp()}"
        }
    
    def _send_sms(self, phone: str, message: str, event: Dict[str, Any]) -> Dict[str, str]:
        """Send SMS notification (simulated)."""
        logger.info(f"Sending SMS to {phone}")
        # In production, would use Twilio or AWS SNS
        return {
            'status': 'sent',
            'channel': 'sms',
            'recipient': phone,
            'message_id': f"sms-{datetime.now().timestamp()}"
        }
    
    def _send_webhook(self, webhook_url: str, event: Dict[str, Any]) -> Dict[str, str]:
        """Send webhook notification (simulated)."""
        logger.info(f"Sending webhook to {webhook_url}")
        # In production, would POST to webhook URL
        return {
            'status': 'sent',
            'channel': 'webhook',
            'recipient': webhook_url,
            'message_id': f"webhook-{datetime.now().timestamp()}"
        }
    
    def log_communication(self, event: Dict[str, Any], message: str, customer: Dict[str, Any], delivery_result: Dict[str, str]):
        """Log communication for tracking and compliance."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'shipment_id': event.get('shipment_id'),
            'customer_id': event.get('customer_id'),
            'customer_name': customer.get('name'),
            'notification_type': event.get('type'),
            'channel': customer.get('channel'),
            'message': message,
            'delivery_status': delivery_result.get('status'),
            'message_id': delivery_result.get('message_id')
        }
        
        logger.info(f"Communication logged: {log_entry}")
        return log_entry
    
    def notify_customer(self, event: Dict[str, Any], llm_generate_fn=None) -> Dict[str, Any]:
        """Main entry point: generate and send customer notification."""
        logger.info(f"Processing notification for shipment {event.get('shipment_id')}")
        
        # 1. Determine notification type
        notification_type = event.get('type')
        if not notification_type:
            return {
                'status': 'error',
                'message': 'Notification type not specified',
                'timestamp': datetime.now().isoformat()
            }
        
        # 2. Retrieve customer profile
        customer_id = event.get('customer_id')
        customer = self.get_customer_profile(customer_id)
        
        # 3. Check if notification should be sent based on customer preferences
        if customer.get('notification_frequency') == 'critical_only' and event.get('severity', 'low') not in ['high', 'critical']:
            logger.info(f"Skipping non-critical notification for customer {customer_id} (preference: critical_only)")
            return {
                'status': 'skipped',
                'reason': 'customer_preference',
                'customer_id': customer_id,
                'timestamp': datetime.now().isoformat()
            }
        
        # 4. Get template
        template = self.get_notification_template(notification_type)
        
        # 5. Generate personalized message
        if llm_generate_fn and notification_type in ['delay', 'issue', 'temperature_breach']:
            # Use LLM for more nuanced messaging on sensitive topics
            try:
                prompt = f"""Generate a professional customer notification for Lineage Logistics:
                
                Customer: {customer.get('name')}
                Contact: {customer.get('contact_name')}
                Tone: {customer.get('preferred_tone')}
                
                Shipment ID: {event.get('shipment_id')}
                Notification Type: {notification_type}
                Details: {event.get('details', {})}
                
                Template: {template}
                
                Generate a clear, professional notification that:
                1. Informs the customer of the situation
                2. Explains what action we're taking
                3. Provides next steps or timeline
                4. Maintains customer confidence
                
                Keep it concise (2-3 sentences for {customer.get('channel')}).
                """
                message = llm_generate_fn(prompt)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}, using template")
                message = self.generate_message(event, customer, template)
        else:
            message = self.generate_message(event, customer, template)
        
        # 6. Send notification
        delivery_result = self.send_notification(customer, message, event)
        
        # 7. Log communication
        log_entry = self.log_communication(event, message, customer, delivery_result)
        
        # 8. Prepare response
        response = {
            'status': 'success',
            'shipment_id': event.get('shipment_id'),
            'customer_id': customer_id,
            'customer_name': customer.get('name'),
            'notification_type': notification_type,
            'channel': customer.get('channel'),
            'message': message,
            'delivery_status': delivery_result.get('status'),
            'message_id': delivery_result.get('message_id'),
            'log_entry': log_entry,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Notification sent successfully via {customer.get('channel')}")
        return response


def notify_customer(event: dict, config: dict = None, llm_generate_fn=None) -> dict:
    """Convenience function for backward compatibility."""
    if config is None:
        config = {
            'customer_notification_channel': 'email',
            'customer_notification_tone': 'professional',
            'customer_proactive_updates': True
        }
    
    notifier = CustomerNotifier(config)
    return notifier.notify_customer(event, llm_generate_fn)
