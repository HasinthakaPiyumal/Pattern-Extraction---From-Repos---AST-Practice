# Cluster 41

class RulesManager:

    def __init__(self, configs: dict={}):
        self._logical_rules = [LogicalInnerJoinCommutativity(), CacheFunctionExpressionInApply(), CacheFunctionExpressionInFilter(), CacheFunctionExpressionInProject()]
        self._stage_one_rewrite_rules = [XformLateralJoinToLinearFlow(), XformExtractObjectToLinearFlow()]
        self._stage_two_rewrite_rules = [EmbedFilterIntoGet(), EmbedSampleIntoGet(), PushDownFilterThroughJoin(), PushDownFilterThroughApplyAndMerge(), CombineSimilarityOrderByAndLimitToVectorIndexScan(), ReorderPredicates()]
        self._implementation_rules = [LogicalCreateToPhysical(), LogicalCreateFromSelectToPhysical(), LogicalRenameToPhysical(), LogicalCreateFunctionToPhysical(), LogicalCreateFunctionFromSelectToPhysical(), LogicalDropObjectToPhysical(), LogicalInsertToPhysical(), LogicalDeleteToPhysical(), LogicalLoadToPhysical(), LogicalGetToSeqScan(), LogicalDerivedGetToPhysical(), LogicalUnionToPhysical(), LogicalGroupByToPhysical(), LogicalOrderByToPhysical(), LogicalLimitToPhysical(), LogicalJoinToPhysicalNestedLoopJoin(), LogicalLateralJoinToPhysical(), LogicalJoinToPhysicalHashJoin(), LogicalFunctionScanToPhysical(), LogicalFilterToPhysical(), LogicalShowToPhysical(), LogicalExplainToPhysical(), LogicalCreateIndexToVectorIndex(), LogicalVectorIndexScanToPhysical(), LogicalProjectNoTableToPhysical()]
        ray_enabled = configs.get('ray', False)
        if is_ray_enabled_and_installed(ray_enabled):
            self._implementation_rules.extend([LogicalExchangeToPhysical(), LogicalApplyAndMergeToRayPhysical(), LogicalProjectToRayPhysical()])
        else:
            self._implementation_rules.extend([LogicalApplyAndMergeToPhysical(), LogicalProjectToPhysical()])
        self._all_rules = self._stage_one_rewrite_rules + self._stage_two_rewrite_rules + self._logical_rules + self._implementation_rules

    @property
    def stage_one_rewrite_rules(self):
        return self._stage_one_rewrite_rules

    @property
    def stage_two_rewrite_rules(self):
        return self._stage_two_rewrite_rules

    @property
    def implementation_rules(self):
        return self._implementation_rules

    @property
    def logical_rules(self):
        return self._logical_rules

    def disable_rules(self, rules: List[Rule]):

        def _remove_from_list(rule_list, rule_to_remove):
            for rule in rule_list:
                if rule.rule_type == rule_to_remove.rule_type:
                    rule_list.remove(rule)
        for rule in rules:
            assert rule.is_implementation_rule() or rule.is_stage_one_rewrite_rules() or rule.is_stage_two_rewrite_rules() or rule.is_logical_rule(), f'Provided Invalid rule {rule}'
            if rule.is_implementation_rule():
                _remove_from_list(self.implementation_rules, rule)
            elif rule.is_stage_one_rewrite_rules():
                _remove_from_list(self.stage_one_rewrite_rules, rule)
            elif rule.is_stage_two_rewrite_rules():
                _remove_from_list(self.stage_two_rewrite_rules, rule)
            elif rule.is_logical_rule():
                _remove_from_list(self.logical_rules, rule)

    def add_rules(self, rules: List[Rule]):

        def _add_to_list(rule_list, rule_to_remove):
            if any([rule.rule_type != rule_to_remove.rule_type for rule in rule_list]):
                rule_list.append(rule)
        for rule in rules:
            assert rule.is_implementation_rule() or rule.is_stage_one_rewrite_rules() or rule.is_stage_two_rewrite_rules() or rule.is_logical_rule(), f'Provided Invalid rule {rule}'
            if rule.is_implementation_rule():
                _add_to_list(self.implementation_rules, rule)
            elif rule.is_stage_one_rewrite_rules():
                _add_to_list(self.stage_one_rewrite_rules, rule)
            elif rule.is_stage_two_rewrite_rules():
                _add_to_list(self.stage_two_rewrite_rules, rule)
            elif rule.is_logical_rule():
                _add_to_list(self.logical_rules, rule)

def disable_rules(self, rules: List[Rule]):

    def _remove_from_list(rule_list, rule_to_remove):
        for rule in rule_list:
            if rule.rule_type == rule_to_remove.rule_type:
                rule_list.remove(rule)
    for rule in rules:
        assert rule.is_implementation_rule() or rule.is_stage_one_rewrite_rules() or rule.is_stage_two_rewrite_rules() or rule.is_logical_rule(), f'Provided Invalid rule {rule}'
        if rule.is_implementation_rule():
            _remove_from_list(self.implementation_rules, rule)
        elif rule.is_stage_one_rewrite_rules():
            _remove_from_list(self.stage_one_rewrite_rules, rule)
        elif rule.is_stage_two_rewrite_rules():
            _remove_from_list(self.stage_two_rewrite_rules, rule)
        elif rule.is_logical_rule():
            _remove_from_list(self.logical_rules, rule)

def add_rules(self, rules: List[Rule]):

    def _add_to_list(rule_list, rule_to_remove):
        if any([rule.rule_type != rule_to_remove.rule_type for rule in rule_list]):
            rule_list.append(rule)
    for rule in rules:
        assert rule.is_implementation_rule() or rule.is_stage_one_rewrite_rules() or rule.is_stage_two_rewrite_rules() or rule.is_logical_rule(), f'Provided Invalid rule {rule}'
        if rule.is_implementation_rule():
            _add_to_list(self.implementation_rules, rule)
        elif rule.is_stage_one_rewrite_rules():
            _add_to_list(self.stage_one_rewrite_rules, rule)
        elif rule.is_stage_two_rewrite_rules():
            _add_to_list(self.stage_two_rewrite_rules, rule)
        elif rule.is_logical_rule():
            _add_to_list(self.logical_rules, rule)

