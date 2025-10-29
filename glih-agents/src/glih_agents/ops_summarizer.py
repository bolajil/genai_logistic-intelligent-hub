from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class OpsSummarizer:
    """Generate shift handoff reports, performance digests, and incident summaries for Lineage Logistics."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.summary_window_hours = config.get('ops_summary_window_hours', 24)
        self.summary_schedule = config.get('ops_summary_schedule', 'shift_end')
        self.export_format = config.get('ops_export_format', 'pdf')
    
    def get_events(self, time_window: str) -> List[Dict[str, Any]]:
        """Retrieve events for the specified time window."""
        # Simulated events (in production, would query event database)
        now = datetime.now()
        
        if time_window == '8h':
            hours = 8
        elif time_window == '24h':
            hours = 24
        elif time_window == '7d':
            hours = 168
        else:
            hours = 24
        
        # Simulated event data
        events = [
            {
                'event_id': 'EVT-001',
                'timestamp': (now - timedelta(hours=2)).isoformat(),
                'type': 'shipment_arrival',
                'shipment_id': 'CHI-ATL-2025-089',
                'facility': 'Chicago',
                'status': 'completed'
            },
            {
                'event_id': 'EVT-002',
                'timestamp': (now - timedelta(hours=4)).isoformat(),
                'type': 'temperature_breach',
                'shipment_id': 'TX-CHI-2025-001',
                'facility': 'Chicago',
                'status': 'resolved',
                'severity': 'high'
            },
            {
                'event_id': 'EVT-003',
                'timestamp': (now - timedelta(hours=6)).isoformat(),
                'type': 'shipment_departure',
                'shipment_id': 'CHI-LA-2025-445',
                'facility': 'Chicago',
                'status': 'in_transit'
            },
            {
                'event_id': 'EVT-004',
                'timestamp': (now - timedelta(hours=7)).isoformat(),
                'type': 'delay',
                'shipment_id': 'BOS-CHI-2025-332',
                'facility': 'Chicago',
                'status': 'delayed',
                'delay_minutes': 45
            }
        ]
        
        return events
    
    def get_incidents(self, time_window: str) -> List[Dict[str, Any]]:
        """Retrieve incidents for the specified time window."""
        # Simulated incidents
        now = datetime.now()
        
        incidents = [
            {
                'incident_id': 'INC-001',
                'timestamp': (now - timedelta(hours=4)).isoformat(),
                'type': 'temperature_breach',
                'severity': 'high',
                'shipment_id': 'TX-CHI-2025-001',
                'product_type': 'Seafood',
                'description': 'Temperature exceeded 8.5°C for 45 minutes',
                'resolution': 'Shipment inspected and quarantined',
                'resolved': True,
                'resolution_time_minutes': 12
            },
            {
                'incident_id': 'INC-002',
                'timestamp': (now - timedelta(hours=7)).isoformat(),
                'type': 'equipment_failure',
                'severity': 'medium',
                'facility': 'Chicago',
                'description': 'Refrigeration unit #3 malfunction',
                'resolution': 'Unit repaired, backup activated',
                'resolved': True,
                'resolution_time_minutes': 90
            }
        ]
        
        return incidents
    
    def calculate_metrics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics from events."""
        total_shipments = len([e for e in events if e['type'] in ['shipment_arrival', 'shipment_departure']])
        
        # On-time performance
        on_time = len([e for e in events if e.get('status') != 'delayed'])
        on_time_pct = (on_time / len(events) * 100) if events else 100
        
        # Temperature compliance
        temp_breaches = len([e for e in events if e['type'] == 'temperature_breach'])
        temp_compliance_pct = ((total_shipments - temp_breaches) / total_shipments * 100) if total_shipments else 100
        
        # Average delay
        delays = [e.get('delay_minutes', 0) for e in events if e.get('status') == 'delayed']
        avg_delay = sum(delays) / len(delays) if delays else 0
        
        return {
            'total_shipments': total_shipments,
            'total_events': len(events),
            'on_time_pct': round(on_time_pct, 1),
            'temp_compliance_pct': round(temp_compliance_pct, 1),
            'avg_delay_minutes': round(avg_delay, 1),
            'incidents': len([e for e in events if e.get('severity') in ['high', 'critical']])
        }
    
    def generate_charts(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart data for visualization."""
        # Simulated chart data (in production, would generate actual charts)
        return {
            'on_time_performance': {
                'type': 'gauge',
                'value': metrics['on_time_pct'],
                'target': 95.0
            },
            'temperature_compliance': {
                'type': 'gauge',
                'value': metrics['temp_compliance_pct'],
                'target': 99.0
            },
            'shipment_volume': {
                'type': 'bar',
                'data': [45, 52, 48, 50, 47, 51, 49]  # Last 7 days
            }
        }
    
    def export_report(self, report: Dict[str, Any], format: str = 'pdf') -> Dict[str, str]:
        """Export report in specified format."""
        # Simulated export (in production, would generate actual PDF/Excel)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ops_summary_{timestamp}.{format}"
        
        logger.info(f"Exporting report to {filename}")
        
        return {
            'filename': filename,
            'format': format,
            'size_kb': 245,
            'download_url': f"/reports/{filename}"
        }
    
    def summarize_ops(self, time_window: str = '24h', vector_search_fn=None, llm_generate_fn=None) -> Dict[str, Any]:
        """Main entry point: generate operations summary."""
        logger.info(f"Generating ops summary for {time_window}")
        
        # 1. Aggregate events
        events = self.get_events(time_window)
        incidents = self.get_incidents(time_window)
        
        # 2. Calculate metrics
        metrics = self.calculate_metrics(events)
        
        # 3. Query for historical context
        context = []
        if vector_search_fn:
            try:
                context_query = f"Operational performance trends {time_window}"
                context_results = vector_search_fn(context_query, collection='lineage-ops-history', k=3)
                context = [r.get('document', '') for r in context_results]
            except Exception as e:
                logger.error(f"Context retrieval failed: {e}")
        
        # 4. Generate executive summary using LLM
        executive_summary = None
        key_highlights = []
        issues_requiring_attention = []
        recommendations = []
        
        if llm_generate_fn:
            try:
                prompt = f"""Generate an executive operations summary for Lineage Logistics:
                
                Time period: {time_window}
                Total shipments: {metrics['total_shipments']}
                Total events: {metrics['total_events']}
                Incidents: {len(incidents)}
                
                Key metrics:
                - On-time delivery: {metrics['on_time_pct']}%
                - Temperature compliance: {metrics['temp_compliance_pct']}%
                - Average delay: {metrics['avg_delay_minutes']} minutes
                
                Incidents:
                {chr(10).join([f"- {i['type']}: {i['description']} (Severity: {i['severity']}, Resolved: {i['resolved']})" for i in incidents])}
                
                Historical context:
                {chr(10).join(context) if context else 'No historical data available'}
                
                Provide:
                1. Executive summary (2-3 sentences)
                2. Key highlights (3-5 bullet points)
                3. Issues requiring attention (if any)
                4. Recommendations for next shift (2-3 bullet points)
                """
                
                summary_text = llm_generate_fn(prompt)
                
                # Parse LLM response (simplified)
                executive_summary = summary_text
                key_highlights = [
                    f"Processed {metrics['total_shipments']} shipments with {metrics['on_time_pct']}% on-time performance",
                    f"Temperature compliance at {metrics['temp_compliance_pct']}%",
                    f"{len(incidents)} incidents reported, all resolved"
                ]
                
                if metrics['on_time_pct'] < 95:
                    issues_requiring_attention.append(f"On-time performance below target (95%): {metrics['on_time_pct']}%")
                
                if metrics['temp_compliance_pct'] < 99:
                    issues_requiring_attention.append(f"Temperature compliance below target (99%): {metrics['temp_compliance_pct']}%")
                
                recommendations = [
                    "Continue monitoring temperature-sensitive shipments closely",
                    "Review equipment maintenance schedule for refrigeration units",
                    "Maintain current staffing levels for optimal performance"
                ]
                
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                executive_summary = f"Operations summary for {time_window}: {metrics['total_shipments']} shipments processed with {metrics['on_time_pct']}% on-time performance."
        else:
            executive_summary = f"Operations summary for {time_window}: {metrics['total_shipments']} shipments processed."
            key_highlights = [f"{metrics['total_events']} events recorded", f"{len(incidents)} incidents"]
        
        # 5. Generate visualizations
        charts = self.generate_charts(metrics)
        
        # 6. Prepare report
        report = {
            'time_window': time_window,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'executive': executive_summary,
                'highlights': key_highlights,
                'issues': issues_requiring_attention,
                'recommendations': recommendations
            },
            'metrics': metrics,
            'events': {
                'total': len(events),
                'by_type': self._group_by_type(events)
            },
            'incidents': {
                'total': len(incidents),
                'by_severity': self._group_by_severity(incidents),
                'details': incidents
            },
            'charts': charts
        }
        
        # 7. Export report
        export_info = self.export_report(report, self.export_format)
        report['export'] = export_info
        
        logger.info(f"Ops summary generated: {metrics['total_shipments']} shipments, {len(incidents)} incidents")
        return report
    
    def _group_by_type(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group events by type."""
        grouped = {}
        for event in events:
            event_type = event.get('type', 'unknown')
            grouped[event_type] = grouped.get(event_type, 0) + 1
        return grouped
    
    def _group_by_severity(self, incidents: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group incidents by severity."""
        grouped = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for incident in incidents:
            severity = incident.get('severity', 'low')
            grouped[severity] = grouped.get(severity, 0) + 1
        return grouped


def summarize_ops(time_window: str = '24h', config: dict = None, vector_search_fn=None, llm_generate_fn=None) -> dict:
    """Convenience function for backward compatibility."""
    if config is None:
        config = {
            'ops_summary_window_hours': 24,
            'ops_summary_schedule': 'shift_end',
            'ops_export_format': 'pdf'
        }
    
    summarizer = OpsSummarizer(config)
    return summarizer.summarize_ops(time_window, vector_search_fn, llm_generate_fn)
