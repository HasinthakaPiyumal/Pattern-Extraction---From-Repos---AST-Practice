# Cluster 27

def optimize_portfolio(self, method: str=None, objective: str=None) -> pd.Series:
    """
    Main portfolio optimization method

    Parameters:
    -----------
    method : str
        Optimization method to use
    objective : str
        Optimization objective

    Returns:
    --------
    Optimal portfolio weights
    """
    method = method or self.config.optimization_method
    objective = objective or self.config.objective
    self.config.objective = objective
    if method == 'efficient_frontier':
        return self._efficient_frontier_optimization()
    elif method == 'hrp':
        return self.hrp_optimization()
    elif method == 'cla':
        return self.cla_optimization()
    elif method == 'black_litterman':
        return self.black_litterman_optimization()
    elif method == 'efficient_semivariance':
        return self.efficient_semivariance_optimization()
    elif method == 'efficient_cvar':
        return self.efficient_cvar_optimization()
    elif method == 'efficient_cdar':
        return self.efficient_cdar_optimization()
    else:
        raise ValueError(f'Unknown optimization method: {method}')

