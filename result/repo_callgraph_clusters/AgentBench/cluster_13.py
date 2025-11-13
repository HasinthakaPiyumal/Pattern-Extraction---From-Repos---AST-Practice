# Cluster 13

class DBResultProcessor:
    """
    处理数据库查询结果和比较的类
    只对外暴露compare_results和calculate_tables_hash接口
    """

    @staticmethod
    def compare_results(answer, ground_truth, query_type):
        """
        比较答案和标准答案
        
        参数:
        answer - 模型输出的答案
        ground_truth - 标准答案
        query_type - 查询类型 (SELECT/INSERT/UPDATE/DELETE)
        
        返回:
        bool - 答案是否匹配
        """
        try:
            processed_answer = DBResultProcessor._clean_answer(answer)
            processed_ground_truth = DBResultProcessor._clean_answer(ground_truth)
            if query_type in ('INSERT', 'DELETE', 'UPDATE'):
                return processed_answer == processed_ground_truth
            print('Processed answer:', processed_answer)
            print('Processed ground_truth:', processed_ground_truth)
            if len(processed_answer) == 1 and len(processed_ground_truth) == 1:
                ans_val = processed_answer[0]
                gt_val = processed_ground_truth[0]
                if ans_val == '0' and gt_val == '0':
                    return True
                if DBResultProcessor._is_float(ans_val) and DBResultProcessor._is_float(gt_val):
                    return DBResultProcessor._float_equal(ans_val, gt_val)
                return ans_val == gt_val
            else:
                if all((DBResultProcessor._is_float(x) for x in processed_answer)) and all((DBResultProcessor._is_float(x) for x in processed_ground_truth)):
                    if len(processed_answer) != len(processed_ground_truth):
                        return False
                    matched_gt = [False] * len(processed_ground_truth)
                    for ans in processed_answer:
                        matched = False
                        for i, gt in enumerate(processed_ground_truth):
                            if not matched_gt[i] and DBResultProcessor._float_equal(ans, gt):
                                matched_gt[i] = True
                                matched = True
                                break
                        if not matched:
                            return False
                    return all(matched_gt)
                return set(processed_answer) == set(processed_ground_truth)
        except Exception as e:
            print(f'Comparison error: {e}')
            return False

    @staticmethod
    async def calculate_tables_hash_async(database: Database, entry):
        """异步计算所有表的组合哈希值"""
        tables = entry['table'] if isinstance(entry['table'], list) else [entry['table']]
        table_hashes = []
        for table in tables:
            table_name = table['table_name']
            table_info = table['table_info']
            table_hash = await DBResultProcessor._get_table_hash_async(database, table_info, table_name)
            cleaned_hash = table_hash.strip('[]()')
            hash_value = cleaned_hash.split(',')[0].strip().strip("'")
            table_hashes.append(hash_value)
        combined_hash = '_'.join(sorted(table_hashes))
        return combined_hash

    @staticmethod
    async def _get_table_hash_async(database: Database, table_info, table_name):
        """异步获取单个表的MD5哈希值"""
        columns = ','.join([f'`{column['name']}`' for column in table_info['columns']])
        md5_query = f"select md5(group_concat(rowhash order by rowhash)) as hash from( SELECT substring(MD5(CONCAT_WS(',', {columns})), 1, 5) AS rowhash FROM `{table_name}`) as sub;"
        return await database.execute(md5_query)

    @staticmethod
    def _normalize_special_values(value):
        """处理特殊值、百分比和格式化数字"""
        if value is None:
            return '0'
        str_value = str(value).strip()
        if str_value.endswith('%'):
            try:
                return str_value[:-1].strip()
            except:
                pass
        if ',' in str_value and (not str_value.startswith('[')) and (not str_value.endswith(']')):
            try:
                str_value = str_value.replace(',', '')
            except:
                pass
        lower_value = str_value.lower()
        special_values_map = {'none': '0', 'null': '0', 'undefined': '0', 'nan': '0', 'inf': '0', 'infinity': '0', '-inf': '0', '-infinity': '0', '': '0'}
        return special_values_map.get(lower_value, str_value)

    @staticmethod
    def _clean_mysql_result(result):
        """处理MySQL执行结果的特殊格式 [(value,)] 或多元组情况 [(value1,), (value2,), ...]"""
        if isinstance(result, str) and result.startswith('[') and result.endswith(']'):
            try:
                parsed_result = eval(result)
                if isinstance(parsed_result, list) and all((isinstance(item, tuple) for item in parsed_result)):
                    cleaned_values = []
                    for item in parsed_result:
                        if len(item) == 1:
                            value = str(item[0]).strip().strip('\'"')
                            cleaned_values.append(value)
                    return cleaned_values
            except:
                pass
            try:
                result_stripped = result.strip('[]')
                if result_stripped.count('(') == 1 and result_stripped.startswith('(') and result_stripped.endswith(',)'):
                    value = result_stripped[1:-2]
                    value = value.strip().strip('\'"')
                    return [value]
            except:
                pass
        return None

    @staticmethod
    def _clean_answer(answer):
        """清理和标准化答案"""
        if answer is None:
            return ['0']
        mysql_result = DBResultProcessor._clean_mysql_result(answer)
        if mysql_result is not None:
            return [DBResultProcessor._normalize_special_values(x) for x in mysql_result]
        if isinstance(answer, str):
            answer = answer.strip()
            if answer.startswith('[') and answer.endswith(']'):
                try:
                    cleaned = eval(answer)
                    if isinstance(cleaned, list):
                        result = []
                        for item in cleaned:
                            if isinstance(item, tuple) and len(item) == 1:
                                value = str(item[0]).strip().strip('\'"')
                                result.append(DBResultProcessor._normalize_special_values(value))
                            else:
                                value = str(item).strip().strip('\'"')
                                result.append(DBResultProcessor._normalize_special_values(value))
                        return result
                except:
                    answer = answer[1:-1]
                    items = []
                    current = ''
                    in_quotes = False
                    for char in answer:
                        if char in '"\'':
                            in_quotes = not in_quotes
                        elif char == ',' and (not in_quotes):
                            if current:
                                items.append(DBResultProcessor._normalize_special_values(current.strip().strip('\'"')))
                                current = ''
                        else:
                            current += char
                    if current:
                        items.append(DBResultProcessor._normalize_special_values(current.strip().strip('\'"')))
                    return items
            else:
                return [DBResultProcessor._normalize_special_values(answer.strip().strip('\'"'))]
        elif isinstance(answer, (list, tuple)):
            result = []
            for item in answer:
                if isinstance(item, tuple) and len(item) == 1:
                    value = str(item[0]).strip().strip('\'"')
                    result.append(DBResultProcessor._normalize_special_values(value))
                else:
                    value = str(item).strip().strip('\'"')
                    result.append(DBResultProcessor._normalize_special_values(value))
            return result
        else:
            return [DBResultProcessor._normalize_special_values(str(answer).strip().strip('\'"'))]

    @staticmethod
    def _is_float(value):
        """检查是否可以转换为浮点数"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _float_equal(a, b, tol=0.01):
        """比较两个浮点数是否相等（考虑精度）"""
        try:
            return abs(float(a) - float(b)) <= tol
        except (ValueError, TypeError):
            return False

@staticmethod
def compare_results(answer, ground_truth, query_type):
    """
        比较答案和标准答案
        
        参数:
        answer - 模型输出的答案
        ground_truth - 标准答案
        query_type - 查询类型 (SELECT/INSERT/UPDATE/DELETE)
        
        返回:
        bool - 答案是否匹配
        """
    try:
        processed_answer = DBResultProcessor._clean_answer(answer)
        processed_ground_truth = DBResultProcessor._clean_answer(ground_truth)
        if query_type in ('INSERT', 'DELETE', 'UPDATE'):
            return processed_answer == processed_ground_truth
        print('Processed answer:', processed_answer)
        print('Processed ground_truth:', processed_ground_truth)
        if len(processed_answer) == 1 and len(processed_ground_truth) == 1:
            ans_val = processed_answer[0]
            gt_val = processed_ground_truth[0]
            if ans_val == '0' and gt_val == '0':
                return True
            if DBResultProcessor._is_float(ans_val) and DBResultProcessor._is_float(gt_val):
                return DBResultProcessor._float_equal(ans_val, gt_val)
            return ans_val == gt_val
        else:
            if all((DBResultProcessor._is_float(x) for x in processed_answer)) and all((DBResultProcessor._is_float(x) for x in processed_ground_truth)):
                if len(processed_answer) != len(processed_ground_truth):
                    return False
                matched_gt = [False] * len(processed_ground_truth)
                for ans in processed_answer:
                    matched = False
                    for i, gt in enumerate(processed_ground_truth):
                        if not matched_gt[i] and DBResultProcessor._float_equal(ans, gt):
                            matched_gt[i] = True
                            matched = True
                            break
                    if not matched:
                        return False
                return all(matched_gt)
            return set(processed_answer) == set(processed_ground_truth)
    except Exception as e:
        print(f'Comparison error: {e}')
        return False

class NotRule(RuleBase):

    def __init__(self, rule: RuleBase) -> None:
        self.rule = rule

    def check(self, obj) -> bool:
        return not self.rule.check(obj)

def check(self, obj) -> bool:
    return not self.rule.check(obj)

class AndRule(RuleBase):

    def __init__(self, rules: List[RuleBase]) -> None:
        self.rules = rules

    def check(self, obj) -> bool:
        return all((rule.check(obj) for rule in self.rules))

def check(self, obj) -> bool:
    return all((rule.check(obj) for rule in self.rules))

class OrRule(RuleBase):

    def __init__(self, rules: List[RuleBase]) -> None:
        self.rules = rules

    def check(self, obj) -> bool:
        return any((rule.check(obj) for rule in self.rules))

def check(self, obj) -> bool:
    return any((rule.check(obj) for rule in self.rules))

def check_context_limit(content: str):
    content = content.lower()
    and_words = [['prompt', 'context', 'tokens'], ['limit', 'exceed', 'max', 'long', 'much', 'many', 'reach', 'over', 'up', 'beyond']]
    rule = AndRule([OrRule([ContainRule(word) for word in and_words[i]]) for i in range(len(and_words))])
    return rule.check(content)

