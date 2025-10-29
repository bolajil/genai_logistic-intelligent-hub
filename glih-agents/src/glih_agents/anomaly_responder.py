from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AnomalyResponder:
    """Detect and respond to cold chain anomalies for Lineage Logistics."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.temp_threshold = config.get('anomaly_temperature_threshold_c', 2.0)
        self.temp_critical = config.get('anomaly_temperature_critical_c', 5.0)
        self.response_target = config.get('anomaly_response_time_target_minutes', 5)
        self.notification_channels = config.get('anomaly_notification_channels', ['email'])
        
        # Temperature ranges by product type (from config)
        self.temp_ranges = config.get('lineage', {}).get('temperature_ranges', {})
    
    def detect_anomaly(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect if event represents an anomaly."""
        anomaly_type = None
        severity = None
        details = {}
        
        # Temperature anomaly detection
        if 'temperature' in event and 'product_type' in event:
            temp = event['temperature']
            product = event['product_type']
            
            # Get expected range for product type
            if product in self.temp_ranges:
                min_temp, max_temp = self.temp_ranges[product]
                
                if temp < min_temp or temp > max_temp:
                    deviation = max(abs(temp - min_temp), abs(temp - max_temp))
                    
                    if deviation >= self.temp_critical:
                        severity = 'critical'
                    elif deviation >= self.temp_threshold:
                        severity = 'high'
                    else:
                        severity = 'medium'
                    
                    anomaly_type = 'temperature_breach'
                    details = {
                        'current_temp': temp,
                        'expected_range': [min_temp, max_temp],
                        'deviation': deviation,
                        'duration': event.get('duration_minutes', 0)
                    }
        
        # Location anomaly detection
        if 'location_deviation_km' in event:
            deviation = event['location_deviation_km']
            if deviation > 50:  # More than 50km off route
                anomaly_type = 'location_deviation'
                severity = 'high' if deviation > 100 else 'medium'
                details = {'deviation_km': deviation}
        
        # Door open anomaly
        if event.get('door_open_duration_minutes', 0) > 15:
            anomaly_type = 'door_open_extended'
            severity = 'medium'
            details = {'duration_minutes': event['door_open_duration_minutes']}
        
        if anomaly_type:
            return {
                'type': anomaly_type,
                'severity': severity,
                'details': details,
                'timestamp': datetime.now().isoformat(),
                'shipment_id': event.get('shipment_id'),
                'product_type': event.get('product_type')
            }
        
        return None
    
    def generate_actions(self, anomaly: Dict[str, Any], sops: List[str]) -> List[Dict[str, str]]:
        """Generate recommended actions based on anomaly and SOPs."""
        actions = []
        
        if anomaly['type'] == 'temperature_breach':
            severity = anomaly['severity']
            duration = anomaly['details'].get('duration', 0)
            
            if severity == 'critical':
                actions = [
                    {'action': 'IMMEDIATE_INSPECTION', 'priority': 'urgent', 'description': 'Inspect shipment immediately for spoilage signs'},
                    {'action': 'NOTIFY_QUALITY', 'priority': 'urgent', 'description': 'Alert quality team for assessment'},
                    {'action': 'QUARANTINE', 'priority': 'high', 'description': 'Quarantine shipment pending quality approval'},
                    {'action': 'DOCUMENT_INCIDENT', 'priority': 'high', 'description': 'Generate compliance incident report'}
                ]
            elif severity == 'high':
                actions = [
                    {'action': 'INSPECT_SHIPMENT', 'priority': 'high', 'description': 'Schedule inspection within 1 hour'},
                    {'action': 'CHECK_REFRIGERATION', 'priority': 'high', 'description': 'Verify refrigeration unit functionality'},
                    {'action': 'NOTIFY_OPS', 'priority': 'medium', 'description': 'Alert operations manager'},
                    {'action': 'LOG_INCIDENT', 'priority': 'medium', 'description': 'Log incident for tracking'}
                ]
            else:
                actions = [
                    {'action': 'MONITOR_CLOSELY', 'priority': 'medium', 'description': 'Increase monitoring frequency to every 15 minutes'},
                    {'action': 'CHECK_SENSORS', 'priority': 'medium', 'description': 'Verify sensor calibration'},
                    {'action': 'LOG_EVENT', 'priority': 'low', 'description': 'Log event for analysis'}
                ]
        
        elif anomaly['type'] == 'location_deviation':
            actions = [
                {'action': 'CONTACT_DRIVER', 'priority': 'high', 'description': 'Contact driver to verify location and route'},
                {'action': 'REROUTE_ANALYSIS', 'priority': 'high', 'description': 'Analyze if rerouting is needed'},
                {'action': 'UPDATE_ETA', 'priority': 'medium', 'description': 'Recalculate and update ETA'},
                {'action': 'NOTIFY_CUSTOMER', 'priority': 'medium', 'description': 'Proactively notify customer of potential delay'}
            ]
        
        elif anomaly['type'] == 'door_open_extended':
            actions = [
                {'action': 'VERIFY_DOOR_STATUS', 'priority': 'high', 'description': 'Confirm door is now closed'},
                {'action': 'CHECK_TEMPERATURE', 'priority': 'high', 'description': 'Monitor temperature for next 30 minutes'},
                {'action': 'INVESTIGATE_CAUSE', 'priority': 'medium', 'description': 'Determine reason for extended door opening'}
            ]
        
        return actions
    
    def respond_to_anomaly(self, event: Dict[str, Any], vector_search_fn=None, llm_generate_fn=None) -> Dict[str, Any]:
        """Main entry point: detect anomaly and generate response."""
        logger.info(f"Processing event for shipment {event.get('shipment_id')}")
        
        # 1. Detect anomaly
        anomaly = self.detect_anomaly(event)
        if not anomaly:
            return {
                'status': 'no_anomaly',
                'shipment_id': event.get('shipment_id'),
                'timestamp': datetime.now().isoformat()
            }
        
        logger.warning(f"Anomaly detected: {anomaly['type']} (severity: {anomaly['severity']})")
        
        # 2. Retrieve relevant SOPs
        sops = []
        if vector_search_fn:
            try:
                sop_query = f"{anomaly['type']} for {event.get('product_type', 'general')} product"
                sop_results = vector_search_fn(sop_query, collection='lineage-sops', k=3)
                sops = [r.get('document', '') for r in sop_results]
            except Exception as e:
                logger.error(f"SOP retrieval failed: {e}")
                sops = ["Standard cold chain breach protocol: inspect, document, escalate if needed."]
        
        # 3. Generate actions
        actions = self.generate_actions(anomaly, sops)
        
        # 4. Generate detailed recommendation using LLM (if available)
        recommendation = None
        if llm_generate_fn and sops:
            try:
                prompt = f"""Temperature breach detected for Lineage Logistics shipment:
                
                Shipment ID: {event.get('shipment_id')}
                Product Type: {event.get('product_type')}
                Anomaly: {anomaly['type']}
                Severity: {anomaly['severity']}
                Details: {anomaly['details']}
                
                Relevant SOPs:
                {chr(10).join(sops)}
                
                Provide a concise 2-3 sentence recommendation for the operations team.
                """
                recommendation = llm_generate_fn(prompt)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
        
        # 5. Prepare response
        response = {
            'status': 'anomaly_detected',
            'shipment_id': event.get('shipment_id'),
            'anomaly': anomaly,
            'actions': actions,
            'sops_retrieved': len(sops),
            'recommendation': recommendation,
            'notification_channels': self.notification_channels,
            'response_time_target': f"{self.response_target} minutes",
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Response generated with {len(actions)} actions")
        return response


def respond_to_anomaly(event: dict, config: dict = None, vector_search_fn=None, llm_generate_fn=None) -> dict:
    """Convenience function for backward compatibility."""
    if config is None:
        config = {
            'anomaly_temperature_threshold_c': 2.0,
            'anomaly_temperature_critical_c': 5.0,
            'lineage': {
                'temperature_ranges': {
                    'Seafood': [-2, 2],
                    'Dairy': [0, 4],
                    'FrozenFoods': [-25, -18],
                    'Produce': [0, 10],
                    'Meat': [-2, 4]
                }
            }
        }
    
    responder = AnomalyResponder(config)
    return responder.respond_to_anomaly(event, vector_search_fn, llm_generate_fn)
