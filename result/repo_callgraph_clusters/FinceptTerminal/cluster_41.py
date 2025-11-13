# Cluster 41

class BusinessCycleAnalysis:
    """Business cycle effects on markets and policy"""
    CYCLE_CHARACTERISTICS = {BusinessCyclePhase.EXPANSION: {'gdp_growth': 'positive_accelerating', 'unemployment': 'declining', 'inflation': 'rising', 'policy_stance': 'neutral_to_tightening', 'yield_curve': 'steepening_then_flattening'}, BusinessCyclePhase.PEAK: {'gdp_growth': 'positive_slowing', 'unemployment': 'low', 'inflation': 'high', 'policy_stance': 'restrictive', 'yield_curve': 'flat_or_inverted'}, BusinessCyclePhase.CONTRACTION: {'gdp_growth': 'negative', 'unemployment': 'rising', 'inflation': 'falling', 'policy_stance': 'accommodative', 'yield_curve': 'steepening'}, BusinessCyclePhase.TROUGH: {'gdp_growth': 'negative_to_positive', 'unemployment': 'high_but_stabilizing', 'inflation': 'low', 'policy_stance': 'very_accommodative', 'yield_curve': 'steep'}}

    @staticmethod
    def analyze_cycle_effects(current_phase: BusinessCyclePhase) -> Dict:
        """Analyze business cycle effects on policy and markets"""
        characteristics = BusinessCycleAnalysis.CYCLE_CHARACTERISTICS[current_phase]
        return {'current_phase': current_phase.value, 'phase_characteristics': characteristics, 'policy_implications': BusinessCycleAnalysis._policy_implications(current_phase), 'market_implications': BusinessCycleAnalysis._market_implications(current_phase), 'yield_curve_effects': BusinessCycleAnalysis._yield_curve_effects(current_phase)}

    @staticmethod
    def _policy_implications(phase: BusinessCyclePhase) -> Dict:
        """Policy implications by cycle phase"""
        policy_map = {BusinessCyclePhase.EXPANSION: {'monetary_policy': 'Gradually tighten to prevent overheating', 'fiscal_policy': 'Reduce deficits, build fiscal space', 'regulatory_stance': 'May tighten financial regulations'}, BusinessCyclePhase.PEAK: {'monetary_policy': 'Restrictive to combat inflation', 'fiscal_policy': 'Counter-cyclical tightening', 'regulatory_stance': 'Monitor financial stability'}, BusinessCyclePhase.CONTRACTION: {'monetary_policy': 'Aggressive easing to support economy', 'fiscal_policy': 'Stimulus spending to cushion recession', 'regulatory_stance': 'May ease to support lending'}, BusinessCyclePhase.TROUGH: {'monetary_policy': 'Maintain accommodation for recovery', 'fiscal_policy': 'Continue support but plan exit strategy', 'regulatory_stance': 'Gradual normalization'}}
        return policy_map[phase]

    @staticmethod
    def _market_implications(phase: BusinessCyclePhase) -> Dict:
        """Market implications by cycle phase"""
        market_map = {BusinessCyclePhase.EXPANSION: {'equity_performance': 'Strong performance, cyclicals outperform', 'bond_performance': 'Rising yields hurt bond performance', 'credit_spreads': 'Tightening spreads', 'sector_rotation': 'Financials, industrials, materials favor'}, BusinessCyclePhase.PEAK: {'equity_performance': 'Volatile, defensive sectors outperform', 'bond_performance': 'Poor performance due to high yields', 'credit_spreads': 'Beginning to widen', 'sector_rotation': 'Utilities, consumer staples favor'}, BusinessCyclePhase.CONTRACTION: {'equity_performance': 'Poor performance, high volatility', 'bond_performance': 'Strong performance as yields fall', 'credit_spreads': 'Widening significantly', 'sector_rotation': 'Quality defensive names outperform'}, BusinessCyclePhase.TROUGH: {'equity_performance': 'Recovery begins, cyclicals lead', 'bond_performance': 'Moderate as yields stabilize', 'credit_spreads': 'Peak widening, beginning to stabilize', 'sector_rotation': 'Early cyclicals, technology, discretionary'}}
        return market_map[phase]

    @staticmethod
    def _yield_curve_effects(phase: BusinessCyclePhase) -> Dict:
        """Yield curve effects by cycle phase"""
        curve_map = {BusinessCyclePhase.EXPANSION: {'curve_shape': 'Steepening early, flattening late', 'short_rates': 'Rising gradually', 'long_rates': 'Rising but less than short rates', 'duration_performance': 'Negative for longer durations'}, BusinessCyclePhase.PEAK: {'curve_shape': 'Flat or inverted', 'short_rates': 'Peak levels', 'long_rates': 'Lower than short rates', 'duration_performance': 'Poor across all durations'}, BusinessCyclePhase.CONTRACTION: {'curve_shape': 'Steepening dramatically', 'short_rates': 'Falling rapidly', 'long_rates': 'Falling but less than short rates', 'duration_performance': 'Positive, especially long duration'}, BusinessCyclePhase.TROUGH: {'curve_shape': 'Steep', 'short_rates': 'Near zero', 'long_rates': 'Low but above short rates', 'duration_performance': 'Positive but moderating'}}
        return curve_map[phase]

@staticmethod
def analyze_cycle_effects(current_phase: BusinessCyclePhase) -> Dict:
    """Analyze business cycle effects on policy and markets"""
    characteristics = BusinessCycleAnalysis.CYCLE_CHARACTERISTICS[current_phase]
    return {'current_phase': current_phase.value, 'phase_characteristics': characteristics, 'policy_implications': BusinessCycleAnalysis._policy_implications(current_phase), 'market_implications': BusinessCycleAnalysis._market_implications(current_phase), 'yield_curve_effects': BusinessCycleAnalysis._yield_curve_effects(current_phase)}

