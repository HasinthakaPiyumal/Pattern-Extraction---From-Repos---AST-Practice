# Cluster 78

def assess_policy_impact(policy_data, policy_type='fiscal'):
    """Quick policy impact assessment"""
    if policy_type == 'fiscal':
        analyzer = FiscalPolicyAnalyzer()
    else:
        analyzer = MonetaryPolicyAnalyzer()
    return analyzer.assess_impact(policy_data)

