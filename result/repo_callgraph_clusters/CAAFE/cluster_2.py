# Cluster 2

def generate_features(ds, df, model='gpt-3.5-turbo', just_print_prompt=False, iterative=1, metric_used=None, iterative_method='logistic', display_method='markdown', n_splits=10, n_repeats=2):

    def format_for_display(code):
        code = code.replace('```python', '').replace('```', '').replace('<end>', '')
        return code
    if display_method == 'markdown':
        from IPython.display import display, Markdown
        display_method = lambda x: display(Markdown(x))
    else:
        display_method = print
    assert iterative == 1 or metric_used is not None, 'metric_used must be set if iterative'
    prompt = build_prompt_from_df(ds, df, iterative=iterative)
    if just_print_prompt:
        code, prompt = (None, prompt)
        return (code, prompt, None)

    def generate_code(messages):
        if model == 'skip':
            return ''
        client = openai.OpenAI()
        completion = client.chat.completions.create(model=model, messages=messages, stop=['```end'], temperature=0.5, max_completion_tokens=500)
        completion = response.model_dump()
        code = completion['choices'][0]['message']['content']
        code = code.replace('```python', '').replace('```', '').replace('<end>', '')
        return code

    def execute_and_evaluate_code_block(full_code, code):
        old_accs, old_rocs, accs, rocs = ([], [], [], [])
        ss = RepeatedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=0)
        for train_idx, valid_idx in ss.split(df):
            df_train, df_valid = (df.iloc[train_idx], df.iloc[valid_idx])
            target_train = df_train[ds[4][-1]]
            target_valid = df_valid[ds[4][-1]]
            df_train = df_train.drop(columns=[ds[4][-1]])
            df_valid = df_valid.drop(columns=[ds[4][-1]])
            df_train_extended = copy.deepcopy(df_train)
            df_valid_extended = copy.deepcopy(df_valid)
            try:
                df_train = run_llm_code(full_code, df_train, convert_categorical_to_integer=not ds[0].startswith('kaggle'))
                df_valid = run_llm_code(full_code, df_valid, convert_categorical_to_integer=not ds[0].startswith('kaggle'))
                df_train_extended = run_llm_code(full_code + '\n' + code, df_train_extended, convert_categorical_to_integer=not ds[0].startswith('kaggle'))
                df_valid_extended = run_llm_code(full_code + '\n' + code, df_valid_extended, convert_categorical_to_integer=not ds[0].startswith('kaggle'))
            except Exception as e:
                display_method(f'Error in code execution. {type(e)} {e}')
                display_method(f'```python\n{format_for_display(code)}\n```\n')
                return (e, None, None, None, None)
            df_train[ds[4][-1]] = target_train
            df_valid[ds[4][-1]] = target_valid
            df_train_extended[ds[4][-1]] = target_train
            df_valid_extended[ds[4][-1]] = target_valid
            from contextlib import contextmanager
            import sys, os
            with open(os.devnull, 'w') as devnull:
                old_stdout = sys.stdout
                sys.stdout = devnull
                try:
                    result_old = evaluate_dataset(df_train=df_train, df_test=df_valid, prompt_id='XX', name=ds[0], method=iterative_method, metric_used=metric_used, seed=0, target_name=ds[4][-1])
                    result_extended = evaluate_dataset(df_train=df_train_extended, df_test=df_valid_extended, prompt_id='XX', name=ds[0], method=iterative_method, metric_used=metric_used, seed=0, target_name=ds[4][-1])
                finally:
                    sys.stdout = old_stdout
            old_accs += [result_old['roc']]
            old_rocs += [result_old['acc']]
            accs += [result_extended['roc']]
            rocs += [result_extended['acc']]
        return (None, rocs, accs, old_rocs, old_accs)
    messages = [{'role': 'system', 'content': 'You are an expert datascientist assistant solving Kaggle problems. You answer only by generating code. Answer as concisely as possible.'}, {'role': 'user', 'content': prompt}]
    display_method(f'*Dataset description:*\n {ds[-1]}')
    n_iter = iterative
    full_code = ''
    i = 0
    while i < n_iter:
        try:
            code = generate_code(messages)
        except Exception as e:
            display_method('Error in LLM API.' + str(e))
            continue
        i = i + 1
        e, rocs, accs, old_rocs, old_accs = execute_and_evaluate_code_block(full_code, code)
        if e is not None:
            messages += [{'role': 'assistant', 'content': code}, {'role': 'user', 'content': f'Code execution failed with error: {type(e)} {e}.\n Code: ```python{code}```\n Generate next feature (fixing error?):\n                                ```python\n                                '}]
            continue
        improvement_roc = np.nanmean(rocs) - np.nanmean(old_rocs)
        improvement_acc = np.nanmean(accs) - np.nanmean(old_accs)
        add_feature = True
        add_feature_sentence = 'The code was executed and changes to ´df´ were kept.'
        if improvement_roc + improvement_acc <= 0:
            add_feature = False
            add_feature_sentence = f'The last code changes to ´df´ were discarded. (Improvement: {improvement_roc + improvement_acc})'
        display_method('\n' + f'*Iteration {i}*\n' + f'```python\n{format_for_display(code)}\n```\n' + f'Performance before adding features ROC {np.nanmean(old_rocs):.3f}, ACC {np.nanmean(old_accs):.3f}.\n' + f'Performance after adding features ROC {np.nanmean(rocs):.3f}, ACC {np.nanmean(accs):.3f}.\n' + f'Improvement ROC {improvement_roc:.3f}, ACC {improvement_acc:.3f}.\n' + f'{add_feature_sentence}\n' + f'\n')
        if len(code) > 10:
            messages += [{'role': 'assistant', 'content': code}, {'role': 'user', 'content': f'Performance after adding feature ROC {np.nanmean(rocs):.3f}, ACC {np.nanmean(accs):.3f}. {add_feature_sentence}\nNext codeblock:\n'}]
        if add_feature:
            full_code += code
    return (full_code, prompt, messages)

def execute_and_evaluate_code_block(full_code, code):
    old_accs, old_rocs, accs, rocs = ([], [], [], [])
    ss = RepeatedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=0)
    for train_idx, valid_idx in ss.split(df):
        df_train, df_valid = (df.iloc[train_idx], df.iloc[valid_idx])
        target_train = df_train[ds[4][-1]]
        target_valid = df_valid[ds[4][-1]]
        df_train = df_train.drop(columns=[ds[4][-1]])
        df_valid = df_valid.drop(columns=[ds[4][-1]])
        df_train_extended = copy.deepcopy(df_train)
        df_valid_extended = copy.deepcopy(df_valid)
        try:
            df_train = run_llm_code(full_code, df_train, convert_categorical_to_integer=not ds[0].startswith('kaggle'))
            df_valid = run_llm_code(full_code, df_valid, convert_categorical_to_integer=not ds[0].startswith('kaggle'))
            df_train_extended = run_llm_code(full_code + '\n' + code, df_train_extended, convert_categorical_to_integer=not ds[0].startswith('kaggle'))
            df_valid_extended = run_llm_code(full_code + '\n' + code, df_valid_extended, convert_categorical_to_integer=not ds[0].startswith('kaggle'))
        except Exception as e:
            display_method(f'Error in code execution. {type(e)} {e}')
            display_method(f'```python\n{format_for_display(code)}\n```\n')
            return (e, None, None, None, None)
        df_train[ds[4][-1]] = target_train
        df_valid[ds[4][-1]] = target_valid
        df_train_extended[ds[4][-1]] = target_train
        df_valid_extended[ds[4][-1]] = target_valid
        from contextlib import contextmanager
        import sys, os
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            sys.stdout = devnull
            try:
                result_old = evaluate_dataset(df_train=df_train, df_test=df_valid, prompt_id='XX', name=ds[0], method=iterative_method, metric_used=metric_used, seed=0, target_name=ds[4][-1])
                result_extended = evaluate_dataset(df_train=df_train_extended, df_test=df_valid_extended, prompt_id='XX', name=ds[0], method=iterative_method, metric_used=metric_used, seed=0, target_name=ds[4][-1])
            finally:
                sys.stdout = old_stdout
        old_accs += [result_old['roc']]
        old_rocs += [result_old['acc']]
        accs += [result_extended['roc']]
        rocs += [result_extended['acc']]
    return (None, rocs, accs, old_rocs, old_accs)

def check_ast(node: ast.AST) -> None:
    """
    Checks if the given AST node is allowed.

    Parameters:
    node (ast.AST): The AST node to check.

    Raises:
    ValueError: If the AST node is not allowed.
    """
    allowed_nodes = {ast.Module, ast.Expr, ast.Load, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.Num, ast.Str, ast.Bytes, ast.List, ast.Tuple, ast.Dict, ast.Name, ast.Call, ast.Attribute, ast.keyword, ast.Subscript, ast.Index, ast.Slice, ast.ExtSlice, ast.Assign, ast.AugAssign, ast.NameConstant, ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn, ast.And, ast.Or, ast.BitOr, ast.BitAnd, ast.BitXor, ast.Invert, ast.Not, ast.Constant, ast.Store, ast.If, ast.IfExp, ast.For, ast.While, ast.Break, ast.Continue, ast.Pass, ast.Assert, ast.Return, ast.FunctionDef, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.Await, ast.Yield, ast.YieldFrom, ast.Lambda, ast.BoolOp, ast.FormattedValue, ast.JoinedStr, ast.Set, ast.Ellipsis, ast.expr, ast.stmt, ast.expr_context, ast.boolop, ast.operator, ast.unaryop, ast.cmpop, ast.comprehension, ast.arguments, ast.arg, ast.Import, ast.ImportFrom, ast.alias}
    allowed_packages = {'numpy', 'pandas', 'sklearn'}
    allowed_funcs = {'sum': sum, 'min': min, 'max': max, 'abs': abs, 'round': round, 'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool, 'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 'enumerate': enumerate, 'zip': zip, 'range': range, 'sorted': sorted, 'reversed': reversed}
    allowed_attrs = {'array', 'arange', 'values', 'linspace', 'mean', 'sum', 'contains', 'where', 'min', 'max', 'median', 'std', 'sqrt', 'pow', 'iloc', 'cut', 'qcut', 'inf', 'nan', 'isna', 'map', 'reshape', 'shape', 'split', 'var', 'codes', 'abs', 'cumsum', 'cumprod', 'cummax', 'cummin', 'diff', 'repeat', 'index', 'log', 'log10', 'log1p', 'slice', 'exp', 'expm1', 'pow', 'pct_change', 'corr', 'cov', 'round', 'clip', 'dot', 'transpose', 'T', 'astype', 'copy', 'drop', 'dropna', 'fillna', 'replace', 'merge', 'append', 'join', 'groupby', 'resample', 'rolling', 'expanding', 'ewm', 'agg', 'aggregate', 'filter', 'transform', 'apply', 'pivot', 'melt', 'sort_values', 'sort_index', 'reset_index', 'set_index', 'reindex', 'shift', 'extract', 'rename', 'tail', 'head', 'describe', 'count', 'value_counts', 'unique', 'nunique', 'idxmin', 'idxmax', 'isin', 'between', 'duplicated', 'rank', 'to_numpy', 'to_dict', 'to_list', 'to_frame', 'squeeze', 'add', 'sub', 'mul', 'div', 'mod', 'columns', 'loc', 'lt', 'le', 'eq', 'ne', 'ge', 'gt', 'all', 'any', 'clip', 'conj', 'conjugate', 'round', 'trace', 'cumprod', 'cumsum', 'prod', 'dot', 'flatten', 'ravel', 'T', 'transpose', 'swapaxes', 'clip', 'item', 'tolist', 'argmax', 'argmin', 'argsort', 'max', 'mean', 'min', 'nonzero', 'ptp', 'sort', 'std', 'var', 'str', 'dt', 'cat', 'sparse', 'plot'}
    if type(node) not in allowed_nodes:
        raise ValueError(f'Disallowed code: {ast.unparse(node)} is {type(node)}')
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id not in allowed_funcs:
            raise ValueError(f'Disallowed function: {node.func.id}')
    if isinstance(node, ast.Attribute) and node.attr not in allowed_attrs:
        raise ValueError(f'Disallowed attribute: {node.attr}')
    if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
        for alias in node.names:
            if alias.name not in allowed_packages:
                raise ValueError(f'Disallowed package import: {alias.name}')
    for child in ast.iter_child_nodes(node):
        check_ast(child)

