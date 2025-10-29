from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import math

logger = logging.getLogger(__name__)


class RouteAdvisor:
    """Optimize routing to prevent delays, reduce costs, and minimize spoilage for Lineage Logistics."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_delay_minutes = config.get('route_max_delay_minutes', 30)
        self.spoilage_risk_threshold = config.get('route_spoilage_risk_threshold', 0.7)
        self.optimization_enabled = config.get('route_optimization_enabled', True)
        self.weather_integration = config.get('route_weather_integration', False)
        
        # Product shelf life (hours)
        self.shelf_life = {
            'Seafood': 48,
            'Dairy': 72,
            'FrozenFoods': 720,  # 30 days
            'Produce': 120,
            'Meat': 96
        }
    
    def calculate_eta(self, route: Dict[str, Any]) -> datetime:
        """Calculate estimated time of arrival based on route."""
        # Simplified ETA calculation
        distance_km = route.get('distance_km', 0)
        avg_speed_kmh = route.get('avg_speed_kmh', 80)
        current_time = datetime.now()
        
        travel_hours = distance_km / avg_speed_kmh
        eta = current_time + timedelta(hours=travel_hours)
        
        return eta
    
    def assess_spoilage_risk(self, shipment: Dict[str, Any], eta: datetime) -> float:
        """Assess probability of spoilage based on ETA and product type."""
        product_type = shipment.get('product_type')
        shelf_life_hours = self.shelf_life.get(product_type, 72)
        
        # Time since shipment started
        start_time = datetime.fromisoformat(shipment.get('start_time', datetime.now().isoformat()))
        elapsed_hours = (datetime.now() - start_time).total_seconds() / 3600
        
        # Time until delivery
        remaining_hours = (eta - datetime.now()).total_seconds() / 3600
        total_transit_hours = elapsed_hours + remaining_hours
        
        # Risk calculation
        risk_score = total_transit_hours / shelf_life_hours
        
        # Adjust for temperature issues
        if shipment.get('temperature_issues', False):
            risk_score *= 1.5
        
        # Adjust for delays
        if shipment.get('delayed', False):
            risk_score *= 1.3
        
        return min(risk_score, 1.0)
    
    def find_alternative_routes(self, origin: str, destination: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find alternative routes based on constraints."""
        # Simulated alternative routes (in production, would call routing API)
        alternatives = []
        
        # Route 1: Direct (fastest)
        alternatives.append({
            'name': 'Direct Route',
            'distance_km': 1200,
            'avg_speed_kmh': 85,
            'estimated_hours': 14.1,
            'cost_estimate': 850,
            'risk_factors': ['Highway construction near Des Moines'],
            'recommended': False
        })
        
        # Route 2: Via Hub (safer)
        alternatives.append({
            'name': 'Via Distribution Hub',
            'distance_km': 1350,
            'avg_speed_kmh': 80,
            'estimated_hours': 16.9,
            'cost_estimate': 920,
            'risk_factors': [],
            'recommended': True
        })
        
        # Route 3: Expedited (fastest but expensive)
        alternatives.append({
            'name': 'Expedited Direct',
            'distance_km': 1180,
            'avg_speed_kmh': 95,
            'estimated_hours': 12.4,
            'cost_estimate': 1200,
            'risk_factors': ['Premium carrier required'],
            'recommended': False
        })
        
        return alternatives
    
    def calculate_savings(self, alternatives: List[Dict[str, Any]], current_route: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate potential savings from route optimization."""
        recommended = next((r for r in alternatives if r.get('recommended')), alternatives[0])
        
        current_cost = current_route.get('cost_estimate', 1000)
        recommended_cost = recommended.get('cost_estimate', 900)
        
        cost_savings = current_cost - recommended_cost
        time_savings_hours = current_route.get('estimated_hours', 16) - recommended.get('estimated_hours', 15)
        
        # Estimate spoilage prevention savings
        spoilage_prevention = 0
        if current_route.get('risk_score', 0) > 0.7:
            spoilage_prevention = 5000  # Average value of prevented spoilage
        
        return {
            'cost_savings': cost_savings,
            'time_savings_hours': time_savings_hours,
            'spoilage_prevention': spoilage_prevention,
            'total_savings': cost_savings + spoilage_prevention
        }
    
    def advise_route(self, shipment: Dict[str, Any], vector_search_fn=None, llm_generate_fn=None) -> Dict[str, Any]:
        """Main entry point: analyze route and provide recommendations."""
        logger.info(f"Analyzing route for shipment {shipment.get('shipment_id')}")
        
        # 1. Calculate current ETA
        current_route = shipment.get('route', {})
        current_eta = self.calculate_eta(current_route)
        
        # 2. Assess spoilage risk
        risk_score = self.assess_spoilage_risk(shipment, current_eta)
        
        # 3. Determine if optimization needed
        if risk_score < self.spoilage_risk_threshold and not shipment.get('delayed', False):
            return {
                'status': 'optimal',
                'shipment_id': shipment.get('shipment_id'),
                'risk_score': risk_score,
                'current_eta': current_eta.isoformat(),
                'recommendation': 'Continue on current route',
                'timestamp': datetime.now().isoformat()
            }
        
        logger.warning(f"High risk detected (score: {risk_score}), finding alternatives")
        
        # 4. Find alternative routes
        alternatives = self.find_alternative_routes(
            origin=shipment.get('origin'),
            destination=shipment.get('destination'),
            constraints=shipment.get('constraints', {})
        )
        
        # 5. Retrieve historical route performance
        route_history = []
        if vector_search_fn:
            try:
                route_query = f"Route performance {shipment.get('origin')} to {shipment.get('destination')}"
                history_results = vector_search_fn(route_query, collection='lineage-routes', k=3)
                route_history = [r.get('document', '') for r in history_results]
            except Exception as e:
                logger.error(f"Route history retrieval failed: {e}")
        
        # 6. Generate detailed recommendation using LLM
        recommendation = None
        if llm_generate_fn and route_history:
            try:
                prompt = f"""Route optimization needed for Lineage Logistics shipment:
                
                Shipment ID: {shipment.get('shipment_id')}
                Product Type: {shipment.get('product_type')}
                Origin: {shipment.get('origin')}
                Destination: {shipment.get('destination')}
                Current ETA: {current_eta.isoformat()}
                Spoilage Risk: {risk_score:.2%}
                
                Alternative Routes:
                {chr(10).join([f"- {r['name']}: {r['estimated_hours']}h, ${r['cost_estimate']}, Risk: {', '.join(r['risk_factors']) or 'None'}" for r in alternatives])}
                
                Historical Performance:
                {chr(10).join(route_history)}
                
                Provide a concise 2-3 sentence recommendation for the operations team, including:
                1. Which route to take and why
                2. Expected impact on delivery time and cost
                3. Any precautions or monitoring needed
                """
                recommendation = llm_generate_fn(prompt)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
        
        # 7. Calculate savings
        savings = self.calculate_savings(alternatives, current_route)
        
        # 8. Prepare response
        recommended_route = next((r for r in alternatives if r.get('recommended')), alternatives[0])
        
        response = {
            'status': 'optimization_recommended',
            'shipment_id': shipment.get('shipment_id'),
            'risk_score': risk_score,
            'current_eta': current_eta.isoformat(),
            'current_route': current_route,
            'recommended_route': recommended_route,
            'alternatives': alternatives,
            'savings': savings,
            'recommendation': recommendation or f"Recommend {recommended_route['name']} to reduce risk and optimize delivery",
            'action_required': risk_score > 0.8,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Route optimization recommended: {recommended_route['name']} (savings: ${savings['total_savings']})")
        return response


def advise_route(shipment: dict, config: dict = None, vector_search_fn=None, llm_generate_fn=None) -> dict:
    """Convenience function for backward compatibility."""
    if config is None:
        config = {
            'route_max_delay_minutes': 30,
            'route_spoilage_risk_threshold': 0.7,
            'route_optimization_enabled': True,
            'route_weather_integration': False
        }
    
    advisor = RouteAdvisor(config)
    return advisor.advise_route(shipment, vector_search_fn, llm_generate_fn)
