# Cluster 37

class CostModel:
    """
    Basic cost model. Change it as we add more cost based rules
    """

    def __init__(self):
        pass

    def calculate_cost(self, gexpr: GroupExpression):
        """
        Return the cost of the group expression.
        """

        @singledispatch
        def cost(opr: AbstractPlan):
            return 1.0

        @cost.register(NestedLoopJoinPlan)
        def cost_nested_loop_join_build_plan(opr: NestedLoopJoinPlan):
            return 1.0

        @cost.register(HashJoinBuildPlan)
        def cost_hash_join_build_plan(opr: HashJoinBuildPlan):
            return 1.0

        @cost.register(HashJoinProbePlan)
        def cost_hash_join_probe_plan(opr: HashJoinProbePlan):
            return 1.0

        @cost.register(SeqScanPlan)
        def cost_seq_scan(opr: SeqScanPlan):
            return 1.0

        @cost.register(ApplyAndMergePlan)
        def cost_apply_and_merge(opr: ApplyAndMergePlan):
            if opr.func_expr.has_cache():
                return 0
            return 1
        return cost(gexpr.opr)

def calculate_cost(self, gexpr: GroupExpression):
    """
        Return the cost of the group expression.
        """

    @singledispatch
    def cost(opr: AbstractPlan):
        return 1.0

    @cost.register(NestedLoopJoinPlan)
    def cost_nested_loop_join_build_plan(opr: NestedLoopJoinPlan):
        return 1.0

    @cost.register(HashJoinBuildPlan)
    def cost_hash_join_build_plan(opr: HashJoinBuildPlan):
        return 1.0

    @cost.register(HashJoinProbePlan)
    def cost_hash_join_probe_plan(opr: HashJoinProbePlan):
        return 1.0

    @cost.register(SeqScanPlan)
    def cost_seq_scan(opr: SeqScanPlan):
        return 1.0

    @cost.register(ApplyAndMergePlan)
    def cost_apply_and_merge(opr: ApplyAndMergePlan):
        if opr.func_expr.has_cache():
            return 0
        return 1
    return cost(gexpr.opr)

