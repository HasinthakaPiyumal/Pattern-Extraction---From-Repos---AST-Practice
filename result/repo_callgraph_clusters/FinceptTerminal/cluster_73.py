# Cluster 73

class CorrelationEffectsAnalysis:
    """Analysis of correlation effects on portfolio risk"""

    @staticmethod
    def correlation_impact(weights: np.ndarray, individual_stds: np.ndarray, correlation_matrix: np.ndarray) -> Dict:
        """Analyze impact of correlations on portfolio risk"""
        cov_matrix = np.outer(individual_stds, individual_stds) * correlation_matrix
        actual_portfolio_std = PortfolioMath.calculate_portfolio_std(weights, cov_matrix)
        perfect_corr_matrix = np.ones_like(correlation_matrix)
        perfect_cov_matrix = np.outer(individual_stds, individual_stds) * perfect_corr_matrix
        perfect_corr_std = PortfolioMath.calculate_portfolio_std(weights, perfect_cov_matrix)
        zero_corr_matrix = np.eye(len(correlation_matrix))
        zero_cov_matrix = np.outer(individual_stds, individual_stds) * zero_corr_matrix
        zero_corr_std = PortfolioMath.calculate_portfolio_std(weights, zero_cov_matrix)
        weighted_avg_std = np.dot(weights, individual_stds)
        diversification_ratio = PortfolioMath.calculate_diversification_ratio(weights, individual_stds, actual_portfolio_std)
        return {'actual_portfolio_std': actual_portfolio_std, 'perfect_correlation_std': perfect_corr_std, 'zero_correlation_std': zero_corr_std, 'weighted_average_std': weighted_avg_std, 'diversification_ratio': diversification_ratio, 'risk_reduction_vs_perfect_corr': (perfect_corr_std - actual_portfolio_std) / perfect_corr_std, 'risk_reduction_vs_weighted_avg': (weighted_avg_std - actual_portfolio_std) / weighted_avg_std, 'average_correlation': np.mean(correlation_matrix[correlation_matrix != 1.0])}

    @staticmethod
    def optimal_correlation_for_risk_target(weights: np.ndarray, individual_stds: np.ndarray, target_portfolio_std: float) -> float:
        """Find correlation needed to achieve target portfolio standard deviation"""

        def objective(avg_correlation):
            n = len(weights)
            corr_matrix = np.full((n, n), avg_correlation)
            np.fill_diagonal(corr_matrix, 1.0)
            cov_matrix = np.outer(individual_stds, individual_stds) * corr_matrix
            portfolio_std = PortfolioMath.calculate_portfolio_std(weights, cov_matrix)
            return (portfolio_std - target_portfolio_std) ** 2
        from scipy import optimize
        result = optimize.minimize_scalar(objective, bounds=(-1, 1), method='bounded')
        return result.x if result.success else None

@staticmethod
def optimal_correlation_for_risk_target(weights: np.ndarray, individual_stds: np.ndarray, target_portfolio_std: float) -> float:
    """Find correlation needed to achieve target portfolio standard deviation"""

    def objective(avg_correlation):
        n = len(weights)
        corr_matrix = np.full((n, n), avg_correlation)
        np.fill_diagonal(corr_matrix, 1.0)
        cov_matrix = np.outer(individual_stds, individual_stds) * corr_matrix
        portfolio_std = PortfolioMath.calculate_portfolio_std(weights, cov_matrix)
        return (portfolio_std - target_portfolio_std) ** 2
    from scipy import optimize
    result = optimize.minimize_scalar(objective, bounds=(-1, 1), method='bounded')
    return result.x if result.success else None

