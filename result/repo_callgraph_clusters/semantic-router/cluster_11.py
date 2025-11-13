# Cluster 11

class UtteranceDiff(BaseModel):
    """A list of Utterance objects that represent the differences between local and
    remote utterances.
    """
    diff: List[Utterance]

    @classmethod
    def from_utterances(cls, local_utterances: List[Utterance], remote_utterances: List[Utterance]):
        """Create a UtteranceDiff object from two lists of Utterance objects.

        :param local_utterances: A list of Utterance objects.
        :type local_utterances: List[Utterance]
        :param remote_utterances: A list of Utterance objects.
        :type remote_utterances: List[Utterance]
        """
        local_utterances_map = {x.to_str(include_metadata=True): x for x in local_utterances}
        remote_utterances_map = {x.to_str(include_metadata=True): x for x in remote_utterances}
        local_utterances_str = list(local_utterances_map.keys())
        local_utterances_str.sort()
        remote_utterances_str = list(remote_utterances_map.keys())
        remote_utterances_str.sort()
        differ = Differ()
        diff_obj = list(differ.compare(local_utterances_str, remote_utterances_str))
        utterance_diffs = []
        for line in diff_obj:
            utterance_str = line[2:]
            utterance_diff_tag = line[0]
            if utterance_diff_tag == '?':
                continue
            utterance = remote_utterances_map[utterance_str] if utterance_diff_tag == '+' else local_utterances_map[utterance_str]
            utterance.diff_tag = utterance_diff_tag
            utterance_diffs.append(utterance)
        return UtteranceDiff(diff=utterance_diffs)

    def to_utterance_str(self, include_metadata: bool=False) -> List[str]:
        """Outputs the utterance diff as a list of diff strings. Returns a list
        of strings showing what is different in the remote when compared to the
        local. For example:

        ["  route1: utterance1",
         "  route1: utterance2",
         "- route2: utterance3",
         "- route2: utterance4"]

        Tells us that the remote is missing "route2: utterance3" and "route2:
        utterance4", which do exist locally. If we see:

        ["  route1: utterance1",
         "  route1: utterance2",
         "+ route2: utterance3",
         "+ route2: utterance4"]

        This diff tells us that the remote has "route2: utterance3" and
        "route2: utterance4", which do not exist locally.

        :param include_metadata: Whether to include metadata in the string.
        :type include_metadata: bool
        :return: A list of diff strings.
        :rtype: List[str]
        """
        return [x.to_diff_str(include_metadata=include_metadata) for x in self.diff]

    def get_tag(self, diff_tag: str) -> List[Utterance]:
        """Get all utterances with a given diff tag.

        :param diff_tag: The diff tag to filter by. Must be one of "+", "-", or " ".
        :type diff_tag: str
        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
        if diff_tag not in ['+', '-', ' ']:
            raise ValueError("diff_tag must be one of '+', '-', or ' '")
        return [x for x in self.diff if x.diff_tag == diff_tag]

    def get_sync_strategy(self, sync_mode: str) -> dict:
        """Generates the optimal synchronization plan for local and remote instances.

        :param sync_mode: The mode to sync the routes with the remote index.
        :type sync_mode: str
        :return: A dictionary describing the synchronization strategy.
        :rtype: dict
        """
        if sync_mode not in SYNC_MODES:
            raise ValueError(f'sync_mode must be one of {SYNC_MODES}')
        local_only = self.get_tag('-')
        local_only_mapper = {utt.route: (utt.function_schemas, utt.metadata) for utt in local_only}
        remote_only = self.get_tag('+')
        remote_only_mapper = {utt.route: (utt.function_schemas, utt.metadata) for utt in remote_only}
        local_and_remote = self.get_tag(' ')
        if sync_mode == 'error':
            if len(local_only) > 0 or len(remote_only) > 0:
                raise ValueError('There are utterances that exist in the local or remote instance that do not exist in the other instance. Please sync the routes before running this command.')
            else:
                return {'remote': {'upsert': [], 'delete': []}, 'local': {'upsert': [], 'delete': []}}
        elif sync_mode == 'local':
            return {'remote': {'upsert': local_only, 'delete': remote_only}, 'local': {'upsert': [], 'delete': []}}
        elif sync_mode == 'remote':
            return {'remote': {'upsert': [], 'delete': []}, 'local': {'upsert': remote_only, 'delete': local_only}}
        elif sync_mode == 'merge-force-local':
            local_route_names = set([utt.route for utt in local_only])
            local_route_utt_strs = set([utt.to_str() for utt in local_only])
            remote_to_keep = [utt for utt in remote_only if utt.route in local_route_names and utt.to_str() not in local_route_utt_strs]
            logger.info(f'local_only_mapper: {local_only_mapper}')
            remote_to_update = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) for utt in remote_only if utt.route in local_only_mapper and (utt.metadata != local_only_mapper[utt.route][1] or utt.function_schemas != local_only_mapper[utt.route][0])]
            remote_to_keep = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) for utt in remote_to_keep if utt.to_str() not in [x.to_str() for x in remote_to_update]]
            remote_to_delete = [utt for utt in remote_only if utt.route not in local_route_names]
            return {'remote': {'upsert': local_only + remote_to_update, 'delete': remote_to_delete}, 'local': {'upsert': remote_to_keep, 'delete': []}}
        elif sync_mode == 'merge-force-remote':
            remote_route_names = set([utt.route for utt in remote_only])
            remote_route_utt_strs = set([utt.to_str() for utt in remote_only])
            local_to_keep = [utt for utt in local_only if utt.route in remote_route_names and utt.to_str() not in remote_route_utt_strs]
            local_to_keep = [Utterance(route=utt.route, utterance=utt.utterance, metadata=remote_only_mapper[utt.route][1], function_schemas=remote_only_mapper[utt.route][0]) for utt in local_to_keep]
            local_to_delete = [utt for utt in local_only if utt.route not in remote_route_names]
            return {'remote': {'upsert': local_to_keep, 'delete': []}, 'local': {'upsert': remote_only, 'delete': local_to_delete}}
        elif sync_mode == 'merge':
            remote_only_updated = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) if utt.route in local_only_mapper else utt for utt in remote_only]
            shared_updated = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) for utt in local_and_remote if utt.route in local_only_mapper and (utt.metadata != local_only_mapper[utt.route][1] or utt.function_schemas != local_only_mapper[utt.route][0])]
            return {'remote': {'upsert': local_only + shared_updated + remote_only_updated, 'delete': []}, 'local': {'upsert': remote_only_updated + shared_updated, 'delete': []}}
        else:
            raise ValueError(f'sync_mode must be one of {SYNC_MODES}')

def to_utterance_str(self, include_metadata: bool=False) -> List[str]:
    """Outputs the utterance diff as a list of diff strings. Returns a list
        of strings showing what is different in the remote when compared to the
        local. For example:

        ["  route1: utterance1",
         "  route1: utterance2",
         "- route2: utterance3",
         "- route2: utterance4"]

        Tells us that the remote is missing "route2: utterance3" and "route2:
        utterance4", which do exist locally. If we see:

        ["  route1: utterance1",
         "  route1: utterance2",
         "+ route2: utterance3",
         "+ route2: utterance4"]

        This diff tells us that the remote has "route2: utterance3" and
        "route2: utterance4", which do not exist locally.

        :param include_metadata: Whether to include metadata in the string.
        :type include_metadata: bool
        :return: A list of diff strings.
        :rtype: List[str]
        """
    return [x.to_diff_str(include_metadata=include_metadata) for x in self.diff]

