# Cluster 125

class PortersFiveForcesAnalyzer:
    """Porter's Five Forces analysis framework"""

    def analyze_five_forces(self, company_data: CompanyData) -> PortersFiveForcesAnalysis:
        """Perform comprehensive Porter's Five Forces analysis"""
        sector = company_data.sector
        threat_new_entrants = self.analyze_threat_of_new_entrants(sector)
        supplier_power = self.analyze_supplier_power(sector)
        buyer_power = self.analyze_buyer_power(sector)
        threat_substitutes = self.analyze_threat_of_substitutes(sector)
        competitive_rivalry = self.analyze_competitive_rivalry(sector)
        forces_scores = [threat_new_entrants['threat_level_score'], supplier_power['power_level_score'], buyer_power['power_level_score'], threat_substitutes['threat_level_score'], competitive_rivalry['intensity_score']]
        avg_score = np.mean(forces_scores)
        if avg_score <= 2:
            attractiveness = 'Highly Attractive'
        elif avg_score <= 3:
            attractiveness = 'Moderately Attractive'
        elif avg_score <= 4:
            attractiveness = 'Average Attractiveness'
        else:
            attractiveness = 'Unattractive'
        return PortersFiveForcesAnalysis(threat_of_new_entrants=threat_new_entrants, bargaining_power_suppliers=supplier_power, bargaining_power_buyers=buyer_power, threat_of_substitutes=threat_substitutes, competitive_rivalry=competitive_rivalry, overall_attractiveness=attractiveness)

    def analyze_threat_of_new_entrants(self, sector: str) -> Dict[str, Any]:
        """Analyze threat of new entrants"""
        entry_barriers = {'Information Technology': {'capital_requirements': 3, 'technology_complexity': 4, 'regulatory_requirements': 2, 'brand_loyalty': 3, 'network_effects': 4, 'access_to_distribution': 3}, 'Health Care': {'capital_requirements': 5, 'technology_complexity': 5, 'regulatory_requirements': 5, 'brand_loyalty': 4, 'network_effects': 2, 'access_to_distribution': 4}, 'Utilities': {'capital_requirements': 5, 'technology_complexity': 3, 'regulatory_requirements': 5, 'brand_loyalty': 2, 'network_effects': 5, 'access_to_distribution': 5}}
        barriers = entry_barriers.get(sector, {'capital_requirements': 3, 'technology_complexity': 3, 'regulatory_requirements': 3, 'brand_loyalty': 3, 'network_effects': 3, 'access_to_distribution': 3})
        avg_barrier_strength = np.mean(list(barriers.values()))
        threat_level_score = 6 - avg_barrier_strength
        if threat_level_score <= 2:
            threat_level = 'Low'
        elif threat_level_score <= 3:
            threat_level = 'Medium'
        else:
            threat_level = 'High'
        return {'entry_barriers': barriers, 'threat_level': threat_level, 'threat_level_score': threat_level_score, 'key_barriers': [k for k, v in barriers.items() if v >= 4], 'analysis': f'Entry barriers are {('strong' if avg_barrier_strength >= 4 else 'moderate' if avg_barrier_strength >= 3 else 'weak')}'}

    def analyze_supplier_power(self, sector: str) -> Dict[str, Any]:
        """Analyze bargaining power of suppliers"""
        supplier_power_factors = {'Information Technology': {'supplier_concentration': 3, 'switching_costs': 3, 'input_importance': 4, 'substitute_inputs': 3, 'forward_integration_threat': 2}, 'Health Care': {'supplier_concentration': 4, 'switching_costs': 4, 'input_importance': 5, 'substitute_inputs': 2, 'forward_integration_threat': 2}, 'Automotive': {'supplier_concentration': 4, 'switching_costs': 4, 'input_importance': 4, 'substitute_inputs': 3, 'forward_integration_threat': 3}}
        factors = supplier_power_factors.get(sector, {'supplier_concentration': 3, 'switching_costs': 3, 'input_importance': 3, 'substitute_inputs': 3, 'forward_integration_threat': 3})
        avg_power = np.mean(list(factors.values()))
        if avg_power >= 4:
            power_level = 'High'
        elif avg_power >= 3:
            power_level = 'Medium'
        else:
            power_level = 'Low'
        return {'power_factors': factors, 'power_level': power_level, 'power_level_score': avg_power, 'key_factors': [k for k, v in factors.items() if v >= 4], 'analysis': f'Supplier power is {power_level.lower()} due to {', '.join([k.replace('_', ' ') for k, v in factors.items() if v >= 4])}'}

    def analyze_buyer_power(self, sector: str) -> Dict[str, Any]:
        """Analyze bargaining power of buyers"""
        buyer_power_factors = {'Information Technology': {'buyer_concentration': 3, 'switching_costs': 2, 'product_importance': 4, 'substitute_products': 3, 'backward_integration_threat': 2, 'price_sensitivity': 3}, 'Health Care': {'buyer_concentration': 4, 'switching_costs': 4, 'product_importance': 5, 'substitute_products': 2, 'backward_integration_threat': 1, 'price_sensitivity': 4}, 'Retail': {'buyer_concentration': 2, 'switching_costs': 1, 'product_importance': 2, 'substitute_products': 4, 'backward_integration_threat': 2, 'price_sensitivity': 5}}
        factors = buyer_power_factors.get(sector, {'buyer_concentration': 3, 'switching_costs': 3, 'product_importance': 3, 'substitute_products': 3, 'backward_integration_threat': 3, 'price_sensitivity': 3})
        power_reducing_factors = ['switching_costs', 'product_importance']
        for factor in power_reducing_factors:
            if factor in factors:
                factors[factor] = 6 - factors[factor]
        avg_power = np.mean(list(factors.values()))
        if avg_power >= 4:
            power_level = 'High'
        elif avg_power >= 3:
            power_level = 'Medium'
        else:
            power_level = 'Low'
        return {'power_factors': buyer_power_factors.get(sector, factors), 'power_level': power_level, 'power_level_score': avg_power, 'key_factors': [k for k, v in factors.items() if v >= 4], 'analysis': f'Buyer power is {power_level.lower()}'}

    def analyze_threat_of_substitutes(self, sector: str) -> Dict[str, Any]:
        """Analyze threat of substitute products"""
        substitute_factors = {'Information Technology': {'substitute_availability': 4, 'switching_costs': 3, 'substitute_performance': 3, 'price_performance': 3}, 'Energy': {'substitute_availability': 4, 'switching_costs': 4, 'substitute_performance': 3, 'price_performance': 4}, 'Transportation': {'substitute_availability': 3, 'switching_costs': 3, 'substitute_performance': 3, 'price_performance': 3}}
        factors = substitute_factors.get(sector, {'substitute_availability': 3, 'switching_costs': 3, 'substitute_performance': 3, 'price_performance': 3})
        factors['switching_costs'] = 6 - factors['switching_costs']
        avg_threat = np.mean(list(factors.values()))
        if avg_threat >= 4:
            threat_level = 'High'
        elif avg_threat >= 3:
            threat_level = 'Medium'
        else:
            threat_level = 'Low'
        return {'substitute_factors': substitute_factors.get(sector, factors), 'threat_level': threat_level, 'threat_level_score': avg_threat, 'key_factors': [k for k, v in factors.items() if v >= 4], 'analysis': f'Substitute threat is {threat_level.lower()}'}

    def analyze_competitive_rivalry(self, sector: str) -> Dict[str, Any]:
        """Analyze intensity of competitive rivalry"""
        rivalry_factors = {'Information Technology': {'number_of_competitors': 5, 'industry_growth': 2, 'product_differentiation': 3, 'switching_costs': 2, 'exit_barriers': 3, 'fixed_costs': 3}, 'Airlines': {'number_of_competitors': 4, 'industry_growth': 3, 'product_differentiation': 2, 'switching_costs': 1, 'exit_barriers': 5, 'fixed_costs': 5}, 'Utilities': {'number_of_competitors': 2, 'industry_growth': 2, 'product_differentiation': 1, 'switching_costs': 4, 'exit_barriers': 5, 'fixed_costs': 5}}
        factors = rivalry_factors.get(sector, {'number_of_competitors': 4, 'industry_growth': 3, 'product_differentiation': 3, 'switching_costs': 3, 'exit_barriers': 3, 'fixed_costs': 3})
        rivalry_reducing = ['industry_growth', 'product_differentiation', 'switching_costs']
        for factor in rivalry_reducing:
            if factor in factors:
                factors[factor] = 6 - factors[factor]
        avg_intensity = np.mean(list(factors.values()))
        if avg_intensity >= 4:
            intensity = 'Very High'
        elif avg_intensity >= 3.5:
            intensity = 'High'
        elif avg_intensity >= 2.5:
            intensity = 'Medium'
        else:
            intensity = 'Low'
        return {'rivalry_factors': rivalry_factors.get(sector, factors), 'intensity': intensity, 'intensity_score': avg_intensity, 'key_factors': [k for k, v in factors.items() if v >= 4], 'analysis': f'Competitive rivalry is {intensity.lower()}'}

def analyze_five_forces(self, company_data: CompanyData) -> PortersFiveForcesAnalysis:
    """Perform comprehensive Porter's Five Forces analysis"""
    sector = company_data.sector
    threat_new_entrants = self.analyze_threat_of_new_entrants(sector)
    supplier_power = self.analyze_supplier_power(sector)
    buyer_power = self.analyze_buyer_power(sector)
    threat_substitutes = self.analyze_threat_of_substitutes(sector)
    competitive_rivalry = self.analyze_competitive_rivalry(sector)
    forces_scores = [threat_new_entrants['threat_level_score'], supplier_power['power_level_score'], buyer_power['power_level_score'], threat_substitutes['threat_level_score'], competitive_rivalry['intensity_score']]
    avg_score = np.mean(forces_scores)
    if avg_score <= 2:
        attractiveness = 'Highly Attractive'
    elif avg_score <= 3:
        attractiveness = 'Moderately Attractive'
    elif avg_score <= 4:
        attractiveness = 'Average Attractiveness'
    else:
        attractiveness = 'Unattractive'
    return PortersFiveForcesAnalysis(threat_of_new_entrants=threat_new_entrants, bargaining_power_suppliers=supplier_power, bargaining_power_buyers=buyer_power, threat_of_substitutes=threat_substitutes, competitive_rivalry=competitive_rivalry, overall_attractiveness=attractiveness)

