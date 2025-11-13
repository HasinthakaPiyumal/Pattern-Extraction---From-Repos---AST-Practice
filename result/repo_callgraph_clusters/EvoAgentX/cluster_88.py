# Cluster 88

def f1_graph(prediction: str, label: str) -> float:

    def parse_graph_improved(text):
        """Improved graph parsing function for accurate node and edge extraction"""
        import re
        nodes = []
        edges = []
        text = text.strip()
        lines = text.splitlines()
        node_section = False
        edge_section = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith('node:'):
                node_section = True
                edge_section = False
                continue
            if line.lower().startswith('edge:'):
                edge_section = True
                node_section = False
                continue
            if node_section:
                node_match = re.match('^(\\d+):\\s*(.+)$', line)
                if node_match:
                    node_num = node_match.group(1)
                    node_content = node_match.group(2).strip()
                    nodes.append(f'{node_num}: {node_content}')
            if edge_section:
                edge_matches = re.findall('\\(([^)]+)\\)', line)
                for edge_match in edge_matches:
                    edge = edge_match.strip()
                    if edge and ',' in edge:
                        edges.append(f'({edge})')
        return (set(nodes), set(edges))

    def normalize_text(text):
        """Normalize text for better matching accuracy"""
        import re
        text = re.sub('\\s+', ' ', text)
        text = text.replace(',', ',').replace('.', '.').replace(':', ':')
        return text.strip().lower()

    def semantic_similarity(text1, text2):
        """Calculate semantic similarity"""
        text1_norm = normalize_text(text1)
        text2_norm = normalize_text(text2)
        words1 = set(text1_norm.split())
        words2 = set(text2_norm.split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0

    def build_graph_structure(nodes, edges):
        """Build graph structure and calculate topological features"""
        import re
        from collections import defaultdict, deque
        node_ids = set()
        node_content_map = {}
        for node in nodes:
            match = re.match('^(\\d+):\\s*(.+)$', node)
            if match:
                node_id = match.group(1)
                content = match.group(2)
                node_ids.add(node_id)
                node_content_map[node_id] = content
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        for edge in edges:
            match = re.match('\\(([^,]+),\\s*([^)]+)\\)', edge)
            if match:
                from_node = match.group(1).strip()
                to_node = match.group(2).strip()
                if from_node == 'START':
                    from_node = '0'
                if to_node == 'END':
                    to_node = str(max((int(n) for n in node_ids)) + 1 if node_ids else 1)
                if from_node in node_ids and to_node in node_ids:
                    graph[from_node].append(to_node)
                    in_degree[to_node] += 1

        def get_topological_features():
            """Calculate topological sorting and features"""
            queue = deque([node for node in node_ids if in_degree[node] == 0])
            topo_order = []
            visited = set()
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                topo_order.append(node)
                for neighbor in graph[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            features = {'node_count': len(node_ids), 'edge_count': len(edges), 'max_depth': len(topo_order), 'avg_branching': sum((len(graph[node]) for node in node_ids)) / len(node_ids) if node_ids else 0, 'parallel_paths': sum((1 for node in node_ids if len(graph[node]) > 1)), 'sequential_paths': sum((1 for node in node_ids if len(graph[node]) == 1))}
            return (features, topo_order)
        return get_topological_features()

    def structural_similarity(pred_nodes, pred_edges, label_nodes, label_edges):
        """Calculate graph structure similarity"""
        try:
            pred_features, pred_topo = build_graph_structure(pred_nodes, pred_edges)
            label_features, label_topo = build_graph_structure(label_nodes, label_edges)
            feature_similarity = 0
            total_features = 0
            for key in pred_features:
                if key in label_features:
                    pred_val = pred_features[key]
                    label_val = label_features[key]
                    if pred_val == 0 and label_val == 0:
                        similarity = 1.0
                    elif pred_val == 0 or label_val == 0:
                        similarity = 0.0
                    else:
                        similarity = min(pred_val, label_val) / max(pred_val, label_val)
                    feature_similarity += similarity
                    total_features += 1
            avg_feature_similarity = feature_similarity / total_features if total_features > 0 else 0.0
            topo_similarity = 0
            if pred_topo and label_topo:
                common_nodes = set(pred_topo) & set(label_topo)
                if common_nodes:
                    pred_positions = {node: i for i, node in enumerate(pred_topo)}
                    label_positions = {node: i for i, node in enumerate(label_topo)}
                    position_diffs = []
                    for node in common_nodes:
                        diff = abs(pred_positions[node] - label_positions[node])
                        position_diffs.append(diff)
                    if position_diffs:
                        avg_diff = sum(position_diffs) / len(position_diffs)
                        max_possible_diff = max(len(pred_topo), len(label_topo))
                        topo_similarity = 1.0 - avg_diff / max_possible_diff
            return 0.6 * avg_feature_similarity + 0.4 * topo_similarity
        except Exception as e:
            print(f'Error calculating structural similarity: {e}')
            return 0.0

    def improved_f1(set_pred, set_label, similarity_threshold=0.7):
        """Improved F1 calculation considering semantic similarity"""
        if not set_pred or not set_label:
            return 0.0
        exact_matches = len(set_pred & set_label)
        semantic_matches = 0
        for pred_item in set_pred:
            if pred_item in set_label:
                continue
            for label_item in set_label:
                if label_item in set_pred:
                    continue
                if semantic_similarity(pred_item, label_item) >= similarity_threshold:
                    semantic_matches += 1
                    break
        total_matches = exact_matches + semantic_matches
        precision = total_matches / len(set_pred) if set_pred else 0.0
        recall = total_matches / len(set_label) if set_label else 0.0
        return 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    pred_nodes, pred_edges = parse_graph_improved(prediction)
    label_nodes, label_edges = parse_graph_improved(label)
    node_f1 = improved_f1(pred_nodes, label_nodes)
    edge_f1 = improved_f1(pred_edges, label_edges)
    structural_sim = structural_similarity(pred_nodes, pred_edges, label_nodes, label_edges)
    semantic_score = 0.6 * node_f1 + 0.4 * edge_f1
    final_score = 0.7 * semantic_score + 0.3 * structural_sim
    return final_score

