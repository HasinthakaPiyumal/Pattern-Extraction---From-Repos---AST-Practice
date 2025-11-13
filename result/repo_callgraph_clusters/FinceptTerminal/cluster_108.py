# Cluster 108

class PrivateCompanyValuator:
    """Comprehensive private company valuation framework"""

    def __init__(self):
        self.normalizer = PrivateCompanyNormalizer()
        self.income_valuator = IncomeApproachValuator()
        self.market_valuator = MarketApproachValuator()
        self.asset_valuator = AssetApproachValuator()
        self.discount_analyzer = DiscountPremiumAnalyzer()

    def comprehensive_valuation(self, private_company: PrivateCompanyData, valuation_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive private company valuation"""
        earnings_adjustments = valuation_inputs.get('earnings_adjustments', {})
        normalized_earnings = self.normalizer.normalize_earnings(private_company.net_income, earnings_adjustments)
        income_valuations = self.perform_income_approach_valuations(private_company, normalized_earnings, valuation_inputs)
        market_valuations = self.perform_market_approach_valuations(private_company, valuation_inputs)
        asset_valuations = self.perform_asset_approach_valuations(private_company, valuation_inputs)
        discounts_premiums = self.calculate_discounts_premiums(private_company, valuation_inputs)
        final_valuation = self.synthesize_valuation_results(income_valuations, market_valuations, asset_valuations, discounts_premiums)
        return {'normalized_earnings': normalized_earnings, 'income_approach': income_valuations, 'market_approach': market_valuations, 'asset_approach': asset_valuations, 'discounts_premiums': discounts_premiums, 'final_valuation': final_valuation, 'valuation_summary': self.generate_valuation_summary(final_valuation)}

    def perform_income_approach_valuations(self, company: PrivateCompanyData, normalized_earnings: Dict[str, float], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform all income approach valuations"""
        income_valuations = {}
        cap_rate = inputs.get('capitalization_rate', 0.2)
        growth_rate = inputs.get('growth_rate', 0.03)
        try:
            cap_earnings_value = self.income_valuator.calculate_capitalized_earnings_value(normalized_earnings['normalized_earnings'], cap_rate, growth_rate)
            income_valuations['capitalized_earnings'] = {'value': cap_earnings_value, 'method': 'Capitalized Earnings', 'cap_rate': cap_rate, 'growth_rate': growth_rate}
        except Exception as e:
            income_valuations['capitalized_earnings'] = {'error': str(e)}
        if 'projected_cash_flows' in inputs:
            discount_rate = inputs.get('discount_rate', 0.15)
            terminal_growth = inputs.get('terminal_growth', 0.03)
            try:
                dcf_value = self.income_valuator.calculate_dcf_value(inputs['projected_cash_flows'], discount_rate, None, terminal_growth)
                income_valuations['dcf'] = {**dcf_value, 'method': 'Discounted Cash Flow', 'discount_rate': discount_rate, 'terminal_growth': terminal_growth}
            except Exception as e:
                income_valuations['dcf'] = {'error': str(e)}
        if 'tangible_assets' in inputs:
            tangible_assets = inputs['tangible_assets']
            asset_return_rate = inputs.get('asset_return_rate', 0.08)
            intangible_return_rate = inputs.get('intangible_return_rate', 0.15)
            try:
                excess_earnings_value = self.income_valuator.calculate_excess_earnings_value(normalized_earnings['normalized_earnings'], tangible_assets, asset_return_rate, intangible_return_rate)
                income_valuations['excess_earnings'] = {**excess_earnings_value, 'method': 'Excess Earnings'}
            except Exception as e:
                income_valuations['excess_earnings'] = {'error': str(e)}
        return income_valuations

    def perform_market_approach_valuations(self, company: PrivateCompanyData, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform market approach valuations"""
        market_valuations = {}
        company_metrics = {'revenue': company.annual_revenue, 'ebitda': company.ebitda, 'net_income': company.net_income}
        if 'public_comparables' in inputs:
            control_premium = inputs.get('control_premium', 0)
            try:
                gpc_value = self.market_valuator.calculate_guideline_public_company_value(company_metrics, inputs['public_comparables'], control_premium)
                market_valuations['guideline_public_companies'] = {**gpc_value, 'method': 'Guideline Public Companies'}
            except Exception as e:
                market_valuations['guideline_public_companies'] = {'error': str(e)}
        if 'transaction_comparables' in inputs:
            try:
                transaction_value = self.market_valuator.calculate_guideline_transaction_value(company_metrics, inputs['transaction_comparables'])
                market_valuations['guideline_transactions'] = {**transaction_value, 'method': 'Guideline Transactions'}
            except Exception as e:
                market_valuations['guideline_transactions'] = {'error': str(e)}
        return market_valuations

    def perform_asset_approach_valuations(self, company: PrivateCompanyData, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform asset approach valuations"""
        asset_valuations = {}
        if 'asset_fair_values' in inputs:
            book_values = {'current_assets': company.total_assets * 0.4, 'fixed_assets': company.total_assets * 0.6}
            try:
                adjusted_bv = self.asset_valuator.calculate_adjusted_book_value(book_values, inputs['asset_fair_values'])
                asset_valuations['adjusted_book_value'] = {**adjusted_bv, 'method': 'Adjusted Book Value'}
            except Exception as e:
                asset_valuations['adjusted_book_value'] = {'error': str(e)}
        if 'asset_categories' in inputs:
            try:
                replacement_cost = self.asset_valuator.calculate_replacement_cost_value(inputs['asset_categories'])
                asset_valuations['replacement_cost'] = {**replacement_cost, 'method': 'Replacement Cost'}
            except Exception as e:
                asset_valuations['replacement_cost'] = {'error': str(e)}
        if 'liquidation_assumptions' in inputs:
            assets = {'total_assets': company.total_assets}
            liquidation_discounts = inputs['liquidation_assumptions'].get('discounts', {})
            liquidation_costs = inputs['liquidation_assumptions'].get('costs', 0)
            try:
                liquidation_value = self.asset_valuator.calculate_liquidation_value(assets, liquidation_discounts, liquidation_costs)
                asset_valuations['liquidation_value'] = {**liquidation_value, 'method': 'Liquidation Value'}
            except Exception as e:
                asset_valuations['liquidation_value'] = {'error': str(e)}
        return asset_valuations

    def calculate_discounts_premiums(self, company: PrivateCompanyData, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all applicable discounts and premiums"""
        discounts_premiums = {}
        characteristics = {'revenue': company.annual_revenue, 'profitability': self.assess_profitability_level(company), 'financial_reporting_quality': company.financial_reporting_quality, 'growth_prospects': inputs.get('growth_prospects', 'Average'), 'management_quality': company.management_quality}
        marketability_discount = self.discount_analyzer.calculate_marketability_discount(characteristics)
        discounts_premiums['marketability'] = marketability_discount
        ownership_percentage = inputs.get('ownership_percentage', 1.0)
        control_characteristics = inputs.get('control_characteristics', {})
        control_analysis = self.discount_analyzer.calculate_control_premium(ownership_percentage, control_characteristics)
        discounts_premiums['control'] = control_analysis
        key_person_chars = {'dependency_level': company.key_person_dependency, 'age': inputs.get('key_person_age', 50), 'succession_plan': inputs.get('succession_plan', False), 'employment_contract': inputs.get('employment_contract', False), 'non_compete': inputs.get('non_compete', False)}
        key_person_discount = self.discount_analyzer.calculate_key_person_discount(key_person_chars)
        discounts_premiums['key_person'] = key_person_discount
        size_metrics = {'revenue': company.annual_revenue, 'total_assets': company.total_assets, 'employee_count': company.employee_count}
        size_discount = self.discount_analyzer.calculate_size_discount(size_metrics)
        discounts_premiums['size'] = size_discount
        return discounts_premiums

    def assess_profitability_level(self, company: PrivateCompanyData) -> str:
        """Assess company profitability level"""
        if company.annual_revenue == 0:
            return 'Weak'
        ebitda_margin = company.ebitda / company.annual_revenue
        net_margin = company.net_income / company.annual_revenue
        if ebitda_margin > 0.2 and net_margin > 0.1:
            return 'Strong'
        elif ebitda_margin > 0.1 and net_margin > 0.05:
            return 'Average'
        else:
            return 'Weak'

    def synthesize_valuation_results(self, income_results: Dict, market_results: Dict, asset_results: Dict, discounts_premiums: Dict) -> Dict[str, Any]:
        """Synthesize results from all valuation approaches"""
        valuation_indications = []
        method_weights = {}
        for method, result in income_results.items():
            if 'error' not in result:
                if method == 'capitalized_earnings':
                    value = result['value']
                    weight = 0.4
                elif method == 'dcf':
                    value = result['enterprise_value']
                    weight = 0.4
                elif method == 'excess_earnings':
                    value = result['total_business_value']
                    weight = 0.3
                else:
                    continue
                valuation_indications.append(value)
                method_weights[f'income_{method}'] = weight
        for method, result in market_results.items():
            if 'error' not in result and 'indicated_values' in result:
                indicated_values = list(result['indicated_values'].values())
                if indicated_values:
                    value = np.median(indicated_values)
                    weight = 0.5
                    valuation_indications.append(value)
                    method_weights[f'market_{method}'] = weight
        for method, result in asset_results.items():
            if 'error' not in result:
                if method == 'adjusted_book_value':
                    value = result['adjusted_book_value']
                    weight = 0.2
                elif method == 'replacement_cost':
                    value = result['total_replacement_cost']
                    weight = 0.2
                elif method == 'liquidation_value':
                    value = result['net_liquidation_value']
                    weight = 0.1
                else:
                    continue
                valuation_indications.append(value)
                method_weights[f'asset_{method}'] = weight
        if len(valuation_indications) > 1:
            weights = list(method_weights.values())
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            weighted_value = sum((v * w for v, w in zip(valuation_indications, normalized_weights)))
            simple_average = np.mean(valuation_indications)
            median_value = np.median(valuation_indications)
        else:
            weighted_value = valuation_indications[0] if valuation_indications else 0
            simple_average = weighted_value
            median_value = weighted_value
        base_value = weighted_value
        dp_factors = {}
        if 'control' in discounts_premiums:
            control_result = discounts_premiums['control']
            if 'control_premium' in control_result:
                dp_factors['control_premium'] = control_result['control_premium']
            elif 'minority_discount' in control_result:
                dp_factors['minority_discount'] = control_result['minority_discount']
        if 'marketability' in discounts_premiums:
            dp_factors['marketability_discount'] = discounts_premiums['marketability']['final_marketability_discount']
        if 'key_person' in discounts_premiums:
            dp_factors['key_person_discount'] = discounts_premiums['key_person']['final_key_person_discount']
        if 'size' in discounts_premiums:
            dp_factors['size_discount'] = discounts_premiums['size']['size_discount']
        final_adjustment = self.discount_analyzer.apply_all_discounts_premiums(base_value, dp_factors)
        return {'valuation_indications': valuation_indications, 'method_weights': method_weights, 'base_valuation': {'weighted_average': weighted_value, 'simple_average': simple_average, 'median': median_value}, 'discount_premium_analysis': final_adjustment, 'final_valuation_range': {'low': final_adjustment['adjusted_value'] * 0.85, 'mid': final_adjustment['adjusted_value'], 'high': final_adjustment['adjusted_value'] * 1.15}, 'valuation_methods_used': len(valuation_indications)}

    def generate_valuation_summary(self, final_valuation: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of valuation"""
        final_value = final_valuation['final_valuation_range']['mid']
        base_value = final_valuation['base_valuation']['weighted_average']
        total_adjustment = final_valuation['discount_premium_analysis']['total_adjustment_percentage']
        summary = {'final_value': final_value, 'valuation_range': final_valuation['final_valuation_range'], 'base_value_before_adjustments': base_value, 'total_discount_premium_adjustment': total_adjustment, 'number_of_methods_used': final_valuation['valuation_methods_used'], 'primary_valuation_driver': self.identify_primary_driver(final_valuation), 'confidence_level': self.assess_confidence_level(final_valuation), 'key_assumptions': self.extract_key_assumptions(final_valuation)}
        return summary

    def identify_primary_driver(self, final_valuation: Dict[str, Any]) -> str:
        """Identify primary valuation driver"""
        method_weights = final_valuation['method_weights']
        if not method_weights:
            return 'No clear driver'
        max_weight_method = max(method_weights.items(), key=lambda x: x[1])[0]
        if 'income' in max_weight_method:
            return 'Income/Earnings Generation'
        elif 'market' in max_weight_method:
            return 'Market Comparables'
        elif 'asset' in max_weight_method:
            return 'Asset Values'
        else:
            return 'Multiple Factors'

    def assess_confidence_level(self, final_valuation: Dict[str, Any]) -> str:
        """Assess confidence level in valuation"""
        num_methods = final_valuation['valuation_methods_used']
        if num_methods >= 3:
            return 'High'
        elif num_methods == 2:
            return 'Medium'
        else:
            return 'Low'

    def extract_key_assumptions(self, final_valuation: Dict[str, Any]) -> List[str]:
        """Extract key valuation assumptions"""
        assumptions = ['Normalized earnings reflect sustainable performance', 'Market multiples are representative of subject company', 'Discount rates reflect appropriate risk levels']
        dp_analysis = final_valuation['discount_premium_analysis']
        individual_adjustments = dp_analysis['individual_adjustments']
        if 'marketability_discount' in individual_adjustments:
            assumptions.append('Marketability discount reflects lack of ready market')
        if 'control_premium' in individual_adjustments:
            assumptions.append('Control premium reflects strategic value')
        elif 'minority_discount' in individual_adjustments:
            assumptions.append('Minority discount reflects lack of control')
        if 'key_person_discount' in individual_adjustments:
            assumptions.append('Key person discount reflects dependency risk')
        return assumptions

def generate_valuation_summary(self, final_valuation: Dict[str, Any]) -> Dict[str, Any]:
    """Generate executive summary of valuation"""
    final_value = final_valuation['final_valuation_range']['mid']
    base_value = final_valuation['base_valuation']['weighted_average']
    total_adjustment = final_valuation['discount_premium_analysis']['total_adjustment_percentage']
    summary = {'final_value': final_value, 'valuation_range': final_valuation['final_valuation_range'], 'base_value_before_adjustments': base_value, 'total_discount_premium_adjustment': total_adjustment, 'number_of_methods_used': final_valuation['valuation_methods_used'], 'primary_valuation_driver': self.identify_primary_driver(final_valuation), 'confidence_level': self.assess_confidence_level(final_valuation), 'key_assumptions': self.extract_key_assumptions(final_valuation)}
    return summary

