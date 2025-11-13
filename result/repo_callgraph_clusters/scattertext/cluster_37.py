# Cluster 37

class CategoryProjectionBase(ABC):
    """

    """

    def _pseduo_init(self, category_corpus, category_counts, projection, x_dim=0, y_dim=1, term_projection=None):
        self.category_corpus = category_corpus
        self.category_counts = category_counts
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.projection = projection
        self.term_projection = term_projection

    def project_with_alternative_dimensions(self, x_dim, y_dim):
        return CategoryProjection(self.category_corpus, self.category_counts, self.projection, x_dim, y_dim)

    def project_with_alternate_axes(self, x_axis=None, y_axis=None):
        if x_axis is None:
            x_axis = self._get_x_axis()
        if y_axis is None:
            y_axis = self._get_y_axis()
        return CategoryProjectionAlternateAxes(self.category_corpus, self.category_counts, self.projection, self.get_category_embeddings(), self.x_dim, self.y_dim, x_axis=x_axis, y_axis=y_axis)

    def get_pandas_projection(self):
        """

        :param x_dim: int
        :param y_dim: int
        :return: pd.DataFrame
        """
        to_ret = pd.DataFrame({'term': self.category_corpus.get_metadata(), 'x': self._get_x_axis(), 'y': self._get_y_axis()}).set_index('term')
        return to_ret

    def _get_x_axis(self):
        try:
            return self.projection.T[self.x_dim]
        except:
            return self.projection.T.loc[self.x_dim]

    def _get_y_axis(self):
        try:
            return self.projection.T[self.y_dim]
        except:
            try:
                return self.projection.T.loc[self.y_dim]
            except:
                import pdb
                pdb.set_trace()
                raise e

    def get_axes_labels(self, num_terms=5):
        df = self.get_term_projection()
        return {'right': list(df.sort_values(by='x', ascending=False).index[:num_terms]), 'left': list(df.sort_values(by='x', ascending=True).index[:num_terms]), 'top': list(df.sort_values(by='y', ascending=False).index[:num_terms]), 'bottom': list(df.sort_values(by='y', ascending=True).index[:num_terms])}

    def get_nearest_terms(self, num_terms: int=5) -> dict:
        return term_coordinates_to_halo(term_coordinates_df=self.get_term_projection(), num_terms=num_terms)

    def get_term_projection(self):
        if self.term_projection is None:
            dim_term = np.matmul(self.category_counts.values, self._get_x_y_projection())
        else:
            dim_term = self.term_projection
        df = pd.DataFrame(dim_term, index=self.category_corpus.get_terms(), columns=['x', 'y'])
        return df

    def _get_x_y_projection(self):
        return np.array([self._get_x_axis(), self._get_y_axis()]).T

    def get_projection(self):
        return self.projection

    @abstractmethod
    def use_alternate_projection(self, projection):
        pass

    @abstractmethod
    def get_category_embeddings(self):
        pass

    def get_corpus(self):
        return self.category_corpus

def _get_y_axis(self):
    try:
        return self.projection.T[self.y_dim]
    except:
        try:
            return self.projection.T.loc[self.y_dim]
        except:
            import pdb
            pdb.set_trace()
            raise e

def last_hidden_state_embeddings(model, inputs) -> np.array:
    full_output = model(input_ids=inputs['input_ids'], token_type_ids=inputs['token_type_ids'], attention_mask=inputs['attention_mask'])
    outputs = full_output.last_hidden_state.detach().numpy()
    return outputs[0][1:-1]

def middle_hidden_state_embeddings(model, inputs) -> np.array:
    full_output = model(input_ids=inputs['input_ids'], token_type_ids=inputs['token_type_ids'], attention_mask=inputs['attention_mask'], output_hidden_states=True)
    hidden_outputs = full_output.hidden_states
    outputs = hidden_outputs[len(hidden_outputs) // 2].detach().numpy()
    return outputs[0][1:-1]

class CorpusRunningStatsFactory:

    def __init__(self, corpus: Union[ParsedCorpus, OffsetCorpus], model: PreTrainedModel, tokenizer: PreTrainedTokenizerFast, feats_from_spacy_doc: Optional[FeatsFromSpacyDoc]=None, doc_segmenter: Optional[Callable[[spacy.tokens.doc.Doc], Iterable[spacy.tokens.span.Span]]]=None, token_normalizer: Optional[Callable[[spacy.tokens.Token], str]]=None, use_all_tokens_for_category_embeddings: bool=True, weights_to_embeddings: Callable=last_hidden_state_embeddings):
        """

        :param corpus:
        :param model:
        :param tokenizer:
        :param feats_from_spacy_doc: if none, use offsets
        :param doc_segmenter:
        :param token_normalizer: Function which takes spacy token and returns a string.
          Not used for embedding calculation, just feature representation. Lowercases all by default.
        :param use_all_tokens_for_category_embeddings: bool, Use all tokens in segment for category embeddings?
        """
        self.corpus = corpus
        self.model = model
        self.tokenizer = tokenizer
        self.feats_from_spacy_doc = feats_from_spacy_doc
        if not isinstance(corpus, OffsetCorpus):
            raise Exception('Since the corpus object is not an offset corpus, feats_from_spacy_doc needs to be passed.')
        self.doc_segmenter = doc_sentence_splitter if doc_segmenter is None else doc_segmenter
        self.token_normalizer = lambda x: x.lower_ if token_normalizer is None else token_normalizer
        self.weights_to_embeddings = weights_to_embeddings
        self.use_all_tokens_for_category_embeddings = use_all_tokens_for_category_embeddings

    def build(self, verbose: bool=True) -> CorpusRunningStats:
        running_stats = self.initialize_running_stats()
        offset_df = self.__build_offset_df()
        for i, row in self.__iter_docs_and_cats(verbose=verbose):
            if isinstance(self.corpus, OffsetCorpus):
                self._add_offsets_to_running_stats(doc_idx=i, doc=row.Doc, cat=row.Cat, running_stats=running_stats, offset_df=offset_df)
            else:
                raise Exception('Only implemented for OffsetCorpus. ParsedCorpus implementation will happen at some point in the future.')
        return running_stats

    def __build_offset_df(self):
        offset_data = []
        for term, values in self.corpus.get_offsets().items():
            term_idx = self.corpus.get_metadata_index(term)
            for doc_idx, offsets in values.items():
                for start, end in offsets:
                    offset_data.append([doc_idx, term_idx, start, end])
        offset_df = pd.DataFrame(offset_data, columns=['DocIdx', 'TermIdx', 'Start', 'End']).sort_values(by=['DocIdx', 'Start', 'End']).set_index('DocIdx')
        return offset_df

    def _add_offsets_to_running_stats(self, doc_idx, doc, cat, running_stats, offset_df) -> None:
        doc_offset_df = self.__query_for_doc_offset_df(offset_df, doc_idx)
        if len(doc_offset_df):
            for segment in self.doc_segmenter(doc):
                seg_start = segment[0].idx
                seg_end = seg_start + len(str(segment))
                try:
                    annots = doc_offset_df[lambda df: (df.Start >= seg_start) & (df.End <= seg_end)]
                except:
                    print('!!!')
                    print(doc_offset_df)
                    print(seg_start, seg_end)
                    print((doc_offset_df.Start >= seg_start) & (doc_offset_df.End <= seg_end))
                    mask = (doc_offset_df.Start >= seg_start) & (doc_offset_df.End <= seg_end)
                    import pdb
                    pdb.set_trace()
                embeddings = None
                if len(annots):
                    embeddings, subtoken_offsets = self.__embed_segment(segment, seg_start)
                    annots.apply(lambda r: self.__add_term_to_stats(term=self.corpus.get_metadata_from_index(r.TermIdx), kw_start=r.Start, kw_end=r.End, embeddings=embeddings, running_stats=running_stats, subtoken_offsets=subtoken_offsets, cat=cat, add_to_category_embeddings=not self.use_all_tokens_for_category_embeddings, segment=segment, seg_start=seg_start), axis=1)
                if self.use_all_tokens_for_category_embeddings:
                    if embeddings is None:
                        embeddings, _ = self.__embed_segment(segment, seg_start, adjust_offsets=False)
                    running_stats.add_embeddings_to_category(embeddings=embeddings, cat=cat)

    def __embed_segment(self, segment, seg_start, adjust_offsets=True):
        str_segment = str(segment)
        inputs = self.tokenizer(str_segment, return_tensors='pt', return_offsets_mapping=True)
        subtoken_offsets = inputs['offset_mapping'].cpu().detach().numpy()[0][1:-1]
        try:
            embeddings = self.__inputs_to_embeddings(inputs=inputs)
        except Exception as e:
            import pdb
            pdb.set_trace()
            raise e
        if adjust_offsets:
            subtoken_offsets_whitespace_stripped = []
            for s, e in subtoken_offsets:
                subtoken = str_segment[s:e]
                s += len(subtoken) - len(subtoken.lstrip())
                e -= len(subtoken) - len(subtoken.rstrip())
                if s != e:
                    subtoken_offsets_whitespace_stripped.append([s, e])
            subtoken_offsets = np.array(subtoken_offsets_whitespace_stripped)
        return (embeddings, subtoken_offsets.T + seg_start)

    def __query_for_doc_offset_df(self, offset_df: pd.DataFrame, doc_idx: int) -> pd.DataFrame:
        try:
            doc_offset_df = offset_df.loc[doc_idx]
        except KeyError:
            return pd.DataFrame([])
        if type(doc_offset_df) == pd.Series:
            return pd.DataFrame([dict(doc_offset_df)])
        return doc_offset_df

    def __add_term_to_stats(self, term: str, kw_start: int, kw_end: int, embeddings: np.array, running_stats: CorpusRunningStats, subtoken_offsets: np.array, cat: str, add_to_category_embeddings: bool, segment: str, seg_start: int):
        subtoken_start = np.searchsorted(subtoken_offsets[0], kw_start)
        subtoken_end = np.searchsorted(subtoken_offsets[1], kw_end, side='right')
        if subtoken_start == subtoken_end:
            if subtoken_start > 0:
                subtoken_start -= 1
            elif subtoken_end < subtoken_offsets.shape[1] - 1:
                subtoken_end += 1
            else:
                print([f'|{t}|' for t in segment])
                print(kw_start, kw_end)
                print('part', str(segment)[kw_start - seg_start:kw_end - seg_start])
                print('term', term)
                print('subtoken start end', subtoken_start, subtoken_end)
                print(seg_start)
                print(subtoken_offsets)
                for s, e in subtoken_offsets.T:
                    print(s, e, str(segment)[s - seg_start:e - seg_start])
                import pdb
                pdb.set_trace()
        kw_embedding = embeddings[subtoken_start:subtoken_end].mean(axis=0)
        if not np.isnan(kw_embedding).any():
            running_stats.add(term=term, cat=cat, embedding=kw_embedding, add_to_category_embeddings=add_to_category_embeddings)

    def __inputs_to_embeddings(self, inputs):
        return self.weights_to_embeddings(model=self.model, inputs=inputs)

    def __iter_docs_and_cats(self, verbose: bool):
        it = self.corpus.get_df()[[self.corpus.get_category_column(), self.corpus.get_parsed_column()]].rename(columns={self.corpus.get_category_column(): 'Cat', self.corpus.get_parsed_column(): 'Doc'}).itertuples()
        if verbose:
            it = tqdm(it, total=self.corpus.get_num_docs())
        return enumerate(it)

    def initialize_running_stats(self):
        running_stats = CorpusRunningStats(corpus=self.corpus, embedding_width=None)
        return running_stats

    def _get_segment_token_embeddings(self, segment: spacy.tokens.span.Span) -> np.array:
        inputs = self.tokenizer(str(segment), return_tensors='pt')
        return self.model(**inputs).last_hidden_state.detach().numpy()

def _add_offsets_to_running_stats(self, doc_idx, doc, cat, running_stats, offset_df) -> None:
    doc_offset_df = self.__query_for_doc_offset_df(offset_df, doc_idx)
    if len(doc_offset_df):
        for segment in self.doc_segmenter(doc):
            seg_start = segment[0].idx
            seg_end = seg_start + len(str(segment))
            try:
                annots = doc_offset_df[lambda df: (df.Start >= seg_start) & (df.End <= seg_end)]
            except:
                print('!!!')
                print(doc_offset_df)
                print(seg_start, seg_end)
                print((doc_offset_df.Start >= seg_start) & (doc_offset_df.End <= seg_end))
                mask = (doc_offset_df.Start >= seg_start) & (doc_offset_df.End <= seg_end)
                import pdb
                pdb.set_trace()
            embeddings = None
            if len(annots):
                embeddings, subtoken_offsets = self.__embed_segment(segment, seg_start)
                annots.apply(lambda r: self.__add_term_to_stats(term=self.corpus.get_metadata_from_index(r.TermIdx), kw_start=r.Start, kw_end=r.End, embeddings=embeddings, running_stats=running_stats, subtoken_offsets=subtoken_offsets, cat=cat, add_to_category_embeddings=not self.use_all_tokens_for_category_embeddings, segment=segment, seg_start=seg_start), axis=1)
            if self.use_all_tokens_for_category_embeddings:
                if embeddings is None:
                    embeddings, _ = self.__embed_segment(segment, seg_start, adjust_offsets=False)
                running_stats.add_embeddings_to_category(embeddings=embeddings, cat=cat)

def __embed_segment(self, segment, seg_start, adjust_offsets=True):
    str_segment = str(segment)
    inputs = self.tokenizer(str_segment, return_tensors='pt', return_offsets_mapping=True)
    subtoken_offsets = inputs['offset_mapping'].cpu().detach().numpy()[0][1:-1]
    try:
        embeddings = self.__inputs_to_embeddings(inputs=inputs)
    except Exception as e:
        import pdb
        pdb.set_trace()
        raise e
    if adjust_offsets:
        subtoken_offsets_whitespace_stripped = []
        for s, e in subtoken_offsets:
            subtoken = str_segment[s:e]
            s += len(subtoken) - len(subtoken.lstrip())
            e -= len(subtoken) - len(subtoken.rstrip())
            if s != e:
                subtoken_offsets_whitespace_stripped.append([s, e])
        subtoken_offsets = np.array(subtoken_offsets_whitespace_stripped)
    return (embeddings, subtoken_offsets.T + seg_start)

def _get_segment_token_embeddings(self, segment: spacy.tokens.span.Span) -> np.array:
    inputs = self.tokenizer(str(segment), return_tensors='pt')
    return self.model(**inputs).last_hidden_state.detach().numpy()

class RunningStatsArray:

    def __init__(self, width: int, n: int=0):
        self.width = width
        self.n = 0
        self.old_m = np.zeros(width)
        self.new_m = np.zeros(width)
        self.old_s = np.zeros(width)
        self.new_s = np.zeros(width)

    def clear(self) -> None:
        self.n = 0

    def push(self, x: np.array) -> 'RunningStatsArray':
        self.n += 1
        if self.n == 1:
            self.old_m = self.new_m = x
            self.old_s = np.zeros(self.width)
        else:
            self.new_m = self.old_m + (x - self.old_m) / self.n
            self.new_s = self.old_s + (x - self.old_m) * (x - self.new_m)
            self.old_m = self.new_m
            self.old_s = self.new_s
        if np.any(np.isnan(self.new_m)):
            import pdb
            pdb.set_trace()
        return self

    def mean(self) -> np.array:
        return self.new_m if self.n else np.zeros(self.width)

    def variance(self) -> np.array:
        return self.new_s / (self.n - 1) if self.n > 1 else np.zeros(self.width)

    def standard_deviation(self) -> np.array:
        return np.sqrt(self.variance())

    def pooled_variance(self, other: 'RunningStatsArray') -> np.array:
        return (self.variance() * self.n + other.variance() * other.n) / (self.n + other.n)

def push(self, x: np.array) -> 'RunningStatsArray':
    self.n += 1
    if self.n == 1:
        self.old_m = self.new_m = x
        self.old_s = np.zeros(self.width)
    else:
        self.new_m = self.old_m + (x - self.old_m) / self.n
        self.new_s = self.old_s + (x - self.old_m) * (x - self.new_m)
        self.old_m = self.new_m
        self.old_s = self.new_s
    if np.any(np.isnan(self.new_m)):
        import pdb
        pdb.set_trace()
    return self

