# Cluster 11

class SeparableCostFunction(StrategicCostFunction):
    """Separable cost function of the form c(x,y) = max{0, c2(y) - c1(x)}."""

    def __init__(self, c1_coefficients: Union[Dict[str, float], torch.Tensor], c2_coefficients: Union[Dict[str, float], torch.Tensor], feature_names: Optional[List[str]]=None):
        """Initialize separable cost function.
        
        Args:
            c1_coefficients: Coefficients for c1 function (original state value)
            c2_coefficients: Coefficients for c2 function (target state value)
            feature_names: Optional list of feature names for dict-based coefficients
        """
        if isinstance(c1_coefficients, dict) and isinstance(c2_coefficients, dict):
            if feature_names is None:
                raise ValueError('feature_names required when using dict coefficients')
            self.c1 = torch.tensor([c1_coefficients.get(name, 0.0) for name in feature_names])
            self.c2 = torch.tensor([c2_coefficients.get(name, 0.0) for name in feature_names])
            self.feature_names = feature_names
        else:
            self.c1 = c1_coefficients if isinstance(c1_coefficients, torch.Tensor) else torch.tensor(c1_coefficients)
            self.c2 = c2_coefficients if isinstance(c2_coefficients, torch.Tensor) else torch.tensor(c2_coefficients)
            self.feature_names = feature_names

    def compute_cost(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Compute separable cost c(x,y) = max{0, c2(y) - c1(x)}."""
        c1_x = torch.dot(self.c1, x)
        c2_y = torch.dot(self.c2, y)
        return torch.relu(c2_y - c1_x)

    def compute_best_response(self, x: torch.Tensor, f: callable) -> torch.Tensor:
        """Compute best response for separable cost function.
        
        This implements Algorithm 1 from the strategic classification paper.
        """
        candidates = self._generate_candidates(x)
        best_utility = float('-inf')
        best_response = x.clone()
        for candidate in candidates:
            with torch.no_grad():
                f_candidate = f(candidate.unsqueeze(0)).squeeze()
                if len(f_candidate.shape) > 0:
                    f_candidate = torch.max(f_candidate)
            cost = self.compute_cost(x, candidate)
            utility = f_candidate - cost
            if utility > best_utility:
                best_utility = utility
                best_response = candidate
        return best_response

    def _generate_candidates(self, x: torch.Tensor, num_candidates: int=50) -> List[torch.Tensor]:
        """Generate candidate points for optimization."""
        candidates = [x]
        for i in range(len(x)):
            for delta in torch.linspace(-2.0, 2.0, 10):
                if delta == 0:
                    continue
                candidate = x.clone()
                candidate[i] += delta
                candidates.append(candidate)
        for _ in range(num_candidates - len(candidates)):
            noise = torch.randn_like(x) * 0.5
            candidate = x + noise
            candidates.append(candidate)
        return candidates[:num_candidates]

def compute_cost(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Compute separable cost c(x,y) = max{0, c2(y) - c1(x)}."""
    c1_x = torch.dot(self.c1, x)
    c2_y = torch.dot(self.c2, y)
    return torch.relu(c2_y - c1_x)

class LinearCostFunction(SeparableCostFunction):
    """Linear cost function c(x,y) = <alpha, y-x>_+."""

    def __init__(self, alpha: Union[Dict[str, float], torch.Tensor], feature_names: Optional[List[str]]=None):
        """Initialize linear cost function.
        
        Args:
            alpha: Cost coefficients for each feature
            feature_names: Optional list of feature names for dict-based coefficients
        """
        if isinstance(alpha, dict):
            if feature_names is None:
                raise ValueError('feature_names required when using dict coefficients')
            alpha_tensor = torch.tensor([alpha.get(name, 0.0) for name in feature_names])
        else:
            alpha_tensor = alpha if isinstance(alpha, torch.Tensor) else torch.tensor(alpha)
        super().__init__(alpha_tensor, alpha_tensor, feature_names)
        self.alpha = alpha_tensor

    def compute_cost(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Compute linear cost c(x,y) = <alpha, y-x>_+."""
        diff = y - x
        cost = torch.dot(self.alpha, diff)
        return torch.relu(cost)

def compute_cost(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Compute linear cost c(x,y) = <alpha, y-x>_+."""
    diff = y - x
    cost = torch.dot(self.alpha, diff)
    return torch.relu(cost)

