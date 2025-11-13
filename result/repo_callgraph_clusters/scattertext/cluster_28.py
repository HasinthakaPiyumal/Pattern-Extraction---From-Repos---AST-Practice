# Cluster 28

def get_trend_scatterplot_structure(corpus: TermDocMatrix, trend_plot_settings: TrendPlotSettings, d3_url_struct: Optional[D3URLs]=None, non_text: bool=False, plot_height: int=500, plot_width: int=600, show_chart: bool=True, show_category_headings: bool=False, category_order: Optional[List[str]]=None, kwargs: Optional[Dict]=None):
    if kwargs is None:
        kwargs = {}
    add_to_plot_df = {}
    line_df = None
    if isinstance(trend_plot_settings, DispersionPlotSettings):
        dispersion = Dispersion(corpus, use_categories_as_documents=True, non_text=non_text, regressor=trend_plot_settings.regressor, term_ranker=trend_plot_settings.term_ranker)
        dispersion_metric = trend_plot_settings.metric
        terms = dispersion.get_names()
        if trend_plot_settings.use_residual:
            dispersion_df = dispersion.get_adjusted_metric_df(metric=dispersion_metric)
            Y = dispersion_df['Residual']
            YPos = trend_plot_settings.dispersion_scaler(Y)
            line_y = 0.5
        else:
            dispersion_df = dispersion.get_adjusted_metric_df(metric=dispersion_metric)
            Y = dispersion_df['Metric']
            all_scale = trend_plot_settings.dispersion_scaler(np.concatenate([dispersion_df['Metric'].values, dispersion_df['Estimate'].values]))
            YPos = all_scale[:len(dispersion_df)]
            line_y = all_scale[len(dispersion_df):]
        x_axis = trend_plot_settings.get_x_axis(corpus=corpus, non_text=non_text)
        XPos = x_axis.scaled
        X = x_axis.orig
        line_df = pd.DataFrame({'x': x_axis.scaled, 'y': line_y}).sort_values(by='x')
    elif isinstance(trend_plot_settings, CorrelationPlotSettings):
        correlations = Correlations(use_non_text=non_text).set_correlation_type(correlation_type=trend_plot_settings.correlation_type)
        correlation_df = correlations.get_correlation_df(corpus=corpus, document_scores=trend_plot_settings.get_category_ranks(corpus=corpus))
        x_axis = trend_plot_settings.get_x_axis(corpus=corpus, non_text=non_text)
        XPos = x_axis.scaled
        X = x_axis.orig
        line_df = pd.DataFrame({'x': x_axis.scaled, 'y': 0.5}).sort_values(by='x')
        Y = correlation_df[Correlations.get_notation_name(correlation_type=trend_plot_settings.correlation_type)]
        YPos = Scalers.scale_neg_1_to_1_with_zero_mean_abs_max(Y)
        terms = list(correlation_df.index)
    elif isinstance(trend_plot_settings, TimePlotSettings):
        position_df = TimePlotPositioner(corpus=corpus, category_order=trend_plot_settings.category_order, non_text=non_text, dispersion_metric=trend_plot_settings.y_axis_metric, use_residual=trend_plot_settings.use_residual).get_position_df()
        X = position_df.Mean
        XPos = X / corpus.get_num_categories()
        terms = list(position_df.index)
        add_to_plot_df = position_df
        Y = position_df.Dispersion
        YPos = trend_plot_settings.dispersion_scaler(Y)
    else:
        raise Exception('Invalid trend_plot_settings type: ' + str(type(trend_plot_settings)))
    plot_params = trend_plot_settings.get_plot_params()
    plot_df = pd.DataFrame().assign(X=X, Frequency=lambda df: df.X, Xpos=XPos, Y=Y, Ypos=YPos, Color='#ffbf00', term=terms).set_index('term')
    for k, v in add_to_plot_df.items():
        plot_df[k] = v
    kwargs.setdefault('top_terms_left_buffer', 10)
    kwargs.setdefault('ignore_categories', False)
    kwargs.setdefault('unified_context', True)
    kwargs['category_order'] = category_order
    if d3_url_struct is None:
        d3_url_struct = D3URLs()
    scatterplot_structure = dataframe_scattertext(corpus, plot_df=plot_df, x_label=plot_params.x_label, y_label=plot_params.y_label, y_axis_labels=plot_params.y_axis_labels, x_axis_labels=plot_params.x_axis_labels, color_column='Color', tooltip_columns=plot_params.tooltip_columns, tooltip_column_names=plot_params.tooltip_column_names, header_names=plot_params.header_names, left_list_column=plot_params.left_list_column, line_coordinates=line_df.to_dict('records') if line_df is not None else None, use_non_text_features=non_text, return_scatterplot_structure=True, width_in_pixels=plot_width, height_in_pixels=plot_height, d3_url=d3_url_struct.get_d3_url(), d3_scale_chromatic_url=d3_url_struct.get_d3_scale_chromatic_url(), show_chart=show_chart, show_category_headings=show_category_headings, **kwargs)
    return scatterplot_structure

def get_p_vals(df, positive_category, term_significance):
    """
	Parameters
	----------
	df : A data frame from, e.g., get_term_freq_df : pd.DataFrame
	positive_category : str
		The positive category name.
	term_significance : TermSignificance
		A TermSignificance instance from which to extract p-values.
	"""
    df_pos = df[[positive_category]]
    df_pos.columns = ['pos']
    df_neg = pd.DataFrame(df[[c for c in df.columns if c != positive_category and c.endswith(' freq')]].sum(axis=1))
    df_neg.columns = ['neg']
    X = df_pos.join(df_neg)[['pos', 'neg']].values
    return term_significance.get_p_vals(X)

class GraphStructure(object):

    def __init__(self, scatterplot_structure, graph_renderer, scatterplot_width=500, scatterplot_height=700, d3_url_struct=None, protocol='http', template_file_name=None):
        """,
        Parameters
        ----------
        scatterplot_structure: ScatterplotStructure
        graph_renderer: GraphRenderer
        scatterplot_width: int
        scatterplot_height: int
        d3_url_struct: D3URLs
        protocol: str
            http or https
        template_file_name: file name to use as template
        """
        self.graph_renderer = graph_renderer
        self.scatterplot_structure = scatterplot_structure
        self.d3_url_struct = d3_url_struct if d3_url_struct else D3URLs()
        ExternalJSUtilts.ensure_valid_protocol(protocol)
        self.protocol = protocol
        self.scatterplot_width = scatterplot_width
        self.scatterplot_height = scatterplot_height
        self.template_file_name = GRAPH_VIZ_FILE_NAME if template_file_name is None else template_file_name

    def to_html(self):
        """
        Returns
        -------
        str, the html file representation

        """
        javascript_to_insert = self._get_javascript_to_insert()
        autocomplete_css = PackedDataUtils.full_content_of_default_autocomplete_css()
        html_template = self._get_html_template()
        html_content = self._replace_html_template(autocomplete_css, html_template, javascript_to_insert)
        return html_content

    def _get_javascript_to_insert(self):
        return '\n'.join([PackedDataUtils.full_content_of_javascript_files(), self.scatterplot_structure._visualization_data.to_javascript(), self.scatterplot_structure.get_js_to_call_build_scatterplot_with_a_function('termPlotInterface'), PackedDataUtils.javascript_post_build_viz('termSearch', 'plotInterface'), self.graph_renderer.get_javascript()])

    def _replace_html_template(self, autocomplete_css, html_template, javascript_to_insert):
        return HELLO + html_template.replace('/***AUTOCOMPLETE CSS***/', autocomplete_css, 1).replace('<!-- INSERT SCRIPT -->', javascript_to_insert, 1).replace('<!--D3URL-->', self.d3_url_struct.get_d3_url(), 1).replace('<!-- INSERT GRAPH -->', self.graph_renderer.get_graph()).replace('<!--D3SCALECHROMATIC-->', self.d3_url_struct.get_d3_scale_chromatic_url()).replace('<!--USEZOOM-->', self.get_zoom_script_import()).replace('<!--FONTIMPORT-->', self.get_font_import()).replace('http://', self.protocol + '://').replace('{width}', str(self.scatterplot_width)).replace('{height}', str(self.scatterplot_height)).replace('{cellheight}', str(int(self.scatterplot_height * (6 / 12))))

    def get_font_import(self):
        return '<link href="https://fonts.googleapis.com/css?family=IBM+Plex+Sans&display=swap" rel="stylesheet">'

    def get_zoom_script_import(self):
        return '<script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.0/dist/svg-pan-zoom.min.js"></script>'

    def _get_html_template(self):
        return PackedDataUtils.get_packaged_html_template_content(self.template_file_name)

def __init__(self, scatterplot_structure, graph_renderer, scatterplot_width=500, scatterplot_height=700, d3_url_struct=None, protocol='http', template_file_name=None):
    """,
        Parameters
        ----------
        scatterplot_structure: ScatterplotStructure
        graph_renderer: GraphRenderer
        scatterplot_width: int
        scatterplot_height: int
        d3_url_struct: D3URLs
        protocol: str
            http or https
        template_file_name: file name to use as template
        """
    self.graph_renderer = graph_renderer
    self.scatterplot_structure = scatterplot_structure
    self.d3_url_struct = d3_url_struct if d3_url_struct else D3URLs()
    ExternalJSUtilts.ensure_valid_protocol(protocol)
    self.protocol = protocol
    self.scatterplot_width = scatterplot_width
    self.scatterplot_height = scatterplot_height
    self.template_file_name = GRAPH_VIZ_FILE_NAME if template_file_name is None else template_file_name

def to_html(self):
    """
        Returns
        -------
        str, the html file representation

        """
    javascript_to_insert = self._get_javascript_to_insert()
    autocomplete_css = PackedDataUtils.full_content_of_default_autocomplete_css()
    html_template = self._get_html_template()
    html_content = self._replace_html_template(autocomplete_css, html_template, javascript_to_insert)
    return html_content

def _get_javascript_to_insert(self):
    return '\n'.join([PackedDataUtils.full_content_of_javascript_files(), self.scatterplot_structure._visualization_data.to_javascript(), self.scatterplot_structure.get_js_to_call_build_scatterplot_with_a_function('termPlotInterface'), PackedDataUtils.javascript_post_build_viz('termSearch', 'plotInterface'), self.graph_renderer.get_javascript()])

def _replace_html_template(self, autocomplete_css, html_template, javascript_to_insert):
    return HELLO + html_template.replace('/***AUTOCOMPLETE CSS***/', autocomplete_css, 1).replace('<!-- INSERT SCRIPT -->', javascript_to_insert, 1).replace('<!--D3URL-->', self.d3_url_struct.get_d3_url(), 1).replace('<!-- INSERT GRAPH -->', self.graph_renderer.get_graph()).replace('<!--D3SCALECHROMATIC-->', self.d3_url_struct.get_d3_scale_chromatic_url()).replace('<!--USEZOOM-->', self.get_zoom_script_import()).replace('<!--FONTIMPORT-->', self.get_font_import()).replace('http://', self.protocol + '://').replace('{width}', str(self.scatterplot_width)).replace('{height}', str(self.scatterplot_height)).replace('{cellheight}', str(int(self.scatterplot_height * (6 / 12))))

def _get_html_template(self):
    return PackedDataUtils.get_packaged_html_template_content(self.template_file_name)

class ComponentDiGraphHTMLRenderer(GraphRenderer):

    def __init__(self, component_graph, width=1000, height=1000, enable_pan_and_zoom=True, engine='dot'):
        self.component_graph = component_graph
        self.width = width
        self.height = height
        self.enable_pan_and_zoom = enable_pan_and_zoom
        self.engine = engine

    def get_graph(self):
        selected_components = self.component_graph.get_components_at_least_size(0)
        all_svg = ''
        for i, component in enumerate(selected_components):
            dot_str = self.component_graph.get_dot(component)
            raw_svg = self.get_svg(dot_str)
            lines = raw_svg.split('\n')
            lines[9] = lines[9].replace('graph0', 'graph%s' % component)
            lines[6] = ('<svg easypz width="{width}pt" height="{height}pt" id="svg{component}"' + ' style="display: none" class="dotgraph"').format(width=self.width, height=self.height, component=component)
            for line in lines[6:]:
                if line.startswith('<!--') or line.endswith('-->'):
                    continue
                all_svg += line + '\n'
        return all_svg

    def get_svg(self, dot_str):
        import graphviz as gv
        return gv.Source(dot_str, format='svg', engine=self.engine).pipe().decode('utf-8')

    def get_javascript(self):
        return '\n        name_to_component = %s;\n        \n        name_to_coord = {}; // term -> {x, y, svg} \n        origViewBox = {}; // svgid -> viewbox\n        \n        Array.prototype.forEach.call(\n            document.querySelectorAll(".dotgraph"),\n            function(svg) {\n                origViewBox[svg.id] = svg.getAttribute(\'viewBox\');\n                \n                Array.prototype.forEach.call(\n                    svg.getElementsByTagName(\'text\'), \n                    function(text) {\n                        name_to_coord[text.textContent] = {\n                            "x": text.getAttribute("x"), \n                            "y": text.getAttribute("y"), \n                            "svg": svg.id\n                        };\n                    }\n                )\n            }\n        ) \n        \n        panZoomInstance = null;\n        \n        \n        function zoomToName(name) {\n        \n            //panZoomInstance.reset();\n                        \n                        \n            console.log("ZOOMING TO "); console.log(name);\n            panZoomInstance.fit();\n            panZoomInstance.center(); \n            \n            var pzSizes = panZoomInstance.getSizes();\n            var centerX = name_to_coord[name].x;\n            var centerY = -name_to_coord[name].y;\n            var newX = centerX*pzSizes["width"]/pzSizes["viewBox"]["width"];\n            var newY = centerY*pzSizes["height"]/pzSizes["viewBox"]["height"];\n            \n            //var zoomRatio = 1/(pzSizes["width"]/pzSizes["viewBox"]["width"]);\n            console.log(\'zr \'.concat(name, \' \', pzSizes, \' \', centerX, \' \', centerY, \' \', newX, \' \', newY));       \n            panZoomInstance.zoomAtPointBy(5, {\'x\':newX, \'y\':newY});\n        }\n        \n        function panToName(name) {\n            var x = name_to_coord[name].x; \n            var y = panZoomInstance.getSizes().viewBox.height + Number.parseInt(name_to_coord[name].y); \n            panZoomInstance.reset() \n            panZoomInstance.zoom(1/panZoomInstance.getSizes().realZoom, true)\n            panZoomInstance.pan({x:0,y:0});\n            var realZoom = panZoomInstance.getSizes().realZoom; \n            var destX = -((x * realZoom) - (panZoomInstance.getSizes().width/2));\n            var destY = -((y * realZoom) - (panZoomInstance.getSizes().height/2));\n            panZoomInstance.pan({\'x\':0,\'y\':0}); \n            panZoomInstance.pan({\'x\': destX, \'y\': destY})\n        }\n            \n        \n        function showTermGraph(term) {\n            var nodeName = \'svg\' + name_to_component[term];\n            document.getElementById(nodeName).style.display=\'block\'; \n            %s\n            panToName(term);\n        }\n\n        Array.from(document.querySelectorAll(\'.node\')).map(\n            function (node) {\n                node.addEventListener(\'mouseenter\', mouseEnterNode);\n                node.addEventListener(\'mouseleave\', mouseLeaveNode);\n                node.addEventListener(\'click\', clickNode);\n            }\n        )\n        \n        function clickNode() {\n            document.querySelectorAll(".dotgraph")\n                .forEach(node => node.style.display = \'none\');\n\n            var term = Array.prototype.filter\n                .call(this.children, (x => x.tagName === "text"))[0].textContent;\n\n            plotInterface.handleSearchTerm(term, true);\n        }\n\n        function mouseEnterNode(event) {\n            var term = Array.prototype.filter.call(this.children, (x => x.tagName === "text"))[0].textContent;\n            plotInterface.showTooltipSimple(term);\n            this.style.fill="red";\n        }\n\n        function mouseLeaveNode() {\n            plotInterface.tooltip.transition().style(\'opacity\', 0)\n            this.style.fill="black";\n        }' % (json.dumps(self.component_graph.get_node_to_component_dict()), self._get_pan_and_zoom_js())

    def _get_pan_and_zoom_js(self):
        if self.enable_pan_and_zoom:
            return "\n                panZoomInstance = svgPanZoom('#' + nodeName, {\n                    zoomEnabled: true,\n                    controlIconsEnabled: true,\n                    fit: true,\n                    center: true,\n                    maxZoom: 100000,\n                    minZoom: 0.1\n                  });\n            "
        else:
            return ''

def get_graph(self):
    selected_components = self.component_graph.get_components_at_least_size(0)
    all_svg = ''
    for i, component in enumerate(selected_components):
        dot_str = self.component_graph.get_dot(component)
        raw_svg = self.get_svg(dot_str)
        lines = raw_svg.split('\n')
        lines[9] = lines[9].replace('graph0', 'graph%s' % component)
        lines[6] = ('<svg easypz width="{width}pt" height="{height}pt" id="svg{component}"' + ' style="display: none" class="dotgraph"').format(width=self.width, height=self.height, component=component)
        for line in lines[6:]:
            if line.startswith('<!--') or line.endswith('-->'):
                continue
            all_svg += line + '\n'
    return all_svg

class Correlations(CoefficientBase):

    def __init__(self, use_non_text=False):
        self.set_correlation_type('pearsonr')
        CoefficientBase.__init__(self, use_non_text=use_non_text)

    def set_correlation_type(self, correlation_type: str='pearsonr') -> 'Correlations':
        assert correlation_type in ['pearsonr', 'spearmanr', 'kendalltau']
        self.correlation_type_ = correlation_type
        self.cols_ = [Correlations.get_notation_name(correlation_type=correlation_type), 'p']
        return self

    @classmethod
    def get_notation_name(cls, correlation_type):
        if correlation_type == 'pearsonr':
            return 'r'
        if correlation_type == 'spearmanr':
            return 'r'
        if correlation_type == 'kendalltau':
            return 'p'

    def __get_correlation_funct(self):
        if self.correlation_type_ == 'pearsonr':
            return pearsonr
        if self.correlation_type_ == 'spearmanr':
            return spearmanr
        if self.correlation_type_ == 'kendalltau':
            return kendalltau

    def get_correlation_df(self, corpus: TermDocMatrix, document_scores: np.array) -> pd.DataFrame:
        """

        :param corpus: TermDocMatrix, should just have unigrams
        :param document_scores: np.array, continuous value for each document score
        :return: pd.DataFrame
        """
        assert document_scores.shape == (corpus.get_num_docs(),)
        tdm = self._get_tdm(corpus)
        return pd.DataFrame([self.__get_correlation_funct()(tdm.T[i].todense().A1, document_scores) for i in range(tdm.shape[1])], columns=self.cols_).assign(Term=self._get_terms(corpus), Frequency=(tdm > 0).sum(axis=0).A1).set_index('Term').reindex(self._get_terms(corpus))

def set_correlation_type(self, correlation_type: str='pearsonr') -> 'Correlations':
    assert correlation_type in ['pearsonr', 'spearmanr', 'kendalltau']
    self.correlation_type_ = correlation_type
    self.cols_ = [Correlations.get_notation_name(correlation_type=correlation_type), 'p']
    return self

def _get_term_plot_change_js_func(wordfish_style, category_focused, initial_category):
    if wordfish_style:
        return '(function (termInfo) {termPlotInterface.yAxisLogCounts(termInfo); return false;})'
    if category_focused:
        return '(function (termInfo) {termPlotInterface.drawCategoryAssociation("%s", termInfo.term); return false;})' % initial_category.replace('"', '\\"')
    return '(function (termInfo) {termPlotInterface.drawCategoryAssociation(termInfo.term); return false;})'

class TimeStructure(GraphStructure):

    def __init__(self, scatterplot_structure, graph_renderer, scatterplot_width=500, scatterplot_height=700, d3_url_struct=None, protocol='http', template_file_name='time_plot.html'):
        GraphStructure.__init__(self, scatterplot_structure, graph_renderer, scatterplot_width, scatterplot_height, d3_url_struct, protocol, template_file_name)

    def _replace_html_template(self, autocomplete_css, html_template, javascript_to_insert):
        html_template = html_template.replace('<!-- EXTRA LIBS -->', "<script src='../scattertext/scattertext/data/viz/scripts/timelines-chart.js'></script>\n<!--D3URL-->")
        return GraphStructure._replace_html_template(self, autocomplete_css, html_template, javascript_to_insert)

def _replace_html_template(self, autocomplete_css, html_template, javascript_to_insert):
    html_template = html_template.replace('<!-- EXTRA LIBS -->', "<script src='../scattertext/scattertext/data/viz/scripts/timelines-chart.js'></script>\n<!--D3URL-->")
    return GraphStructure._replace_html_template(self, autocomplete_css, html_template, javascript_to_insert)

class FeatsFromSpacyDoc(object):

    def __init__(self, use_lemmas=False, entity_types_to_censor=set(), tag_types_to_censor=set(), strip_final_period=False):
        """
		Parameters
		----------
		use_lemmas : bool, optional
			False by default
		entity_types_to_censor : set, optional
			empty by default
		tag_types_to_censor : set, optional
			empty by default
		strip_final_period : bool, optional
			if you know that spacy is going to mess up parsing, strip final period.  default no.
		"""
        self._use_lemmas = use_lemmas
        assert type(entity_types_to_censor) == set
        assert type(tag_types_to_censor) == set
        self._entity_types_to_censor = entity_types_to_censor
        self._pos_types_to_censor = {}
        self._tag_types_to_censor = tag_types_to_censor
        self._strip_final_period = strip_final_period
        self._ignore_censored_types = False

    def _post_process_term(self, term):
        if self._strip_final_period and (term.strip().endswith('.') or term.strip().endswith(',')):
            term = term.strip()[:-1]
        return term

    def get_doc_metadata(self, doc):
        return Counter()

    def get_row_metadata(self, doc, row: pd.Series):
        return Counter()

    def ignore_censored_types(self):
        self._ignore_censored_types = True
        return self

    def censor_pos_types(self, pos_types):
        assert type(pos_types) == set
        self._pos_types_to_censor = pos_types
        return self

    def censor_entity_types(self, entity_types):
        assert type(entity_types) == set
        self._entity_types_to_censor = entity_types
        return self

    def censor_tag_types(self, tag_types):
        assert type(tag_types) == set
        self._tag_types_to_censor = tag_types
        return self

    def get_feats(self, doc):
        """
		Parameters
		----------
		doc, Spacy Docs

		Returns
		-------
		Counter (unigram, bigram) -> count
		"""
        ngram_counter = Counter()
        for sent in doc.sents:
            unigrams = self._get_unigram_feats(sent)
            bigrams = self._get_bigram_feats(unigrams)
            ngram_counter += Counter(chain(unigrams, bigrams))
        return ngram_counter

    def _get_bigram_feats(self, unigrams):
        if len(unigrams) > 1:
            bigrams = map(' '.join, zip(unigrams[:-1], unigrams[1:]))
        else:
            bigrams = []
        return bigrams

    def _get_unigram_feats(self, sent):
        unigrams = []
        for tok in sent:
            if tok.pos_ not in ('PUNCT', 'SPACE', 'X'):
                if tok.ent_type_ in self._entity_types_to_censor:
                    if not self._ignore_censored_types:
                        unigrams.append('_' + tok.ent_type_)
                elif tok.tag_ in self._tag_types_to_censor:
                    if not self._ignore_censored_types:
                        unigrams.append(tok.tag_)
                elif tok.pos_ in self._pos_types_to_censor:
                    if not self._ignore_censored_types:
                        unigrams.append(tok.pos_)
                elif self._use_lemmas and tok.lemma_.strip():
                    unigrams.append(self._post_process_term(tok.lemma_.strip().lower()))
                elif tok.lower_.strip():
                    unigrams.append(self._post_process_term(tok.lower_.strip()))
        return unigrams

    def has_metadata_term_list(self):
        """
		Returns True if there is a meta data term list associated with object, False if not.

		Returns
		-------
		bool
		"""
        return False

    def get_top_model_term_lists(self):
        raise Exception('No topic models associated with these features.')

def _post_process_term(self, term):
    if self._strip_final_period and (term.strip().endswith('.') or term.strip().endswith(',')):
        term = term.strip()[:-1]
    return term

def get_tooltip_js_function(plot_df, tooltip_column_names, tooltip_columns):
    if len(tooltip_columns) > 2:
        raise Exception('You can have at most two columns in a tooltip.')
    tooltip_content = ''
    tooltip_column_names = {} if tooltip_column_names is None else tooltip_column_names
    for col in tooltip_columns:
        if col not in plot_df:
            raise Exception(f'Column {col} not in plot_df')
        formatting = ''
        if pd.api.types.is_float(plot_df[col].iloc[0]):
            formatting = '.toFixed(6)'
        tooltip_content += '+ "<br />%s: " + d.etc["%s"]%s' % (html.escape(tooltip_column_names.get(col, col)), col.replace('"', '\\"').replace("'", "\\'"), formatting)
    tooltip_content_js_function = '(function(d) {return d.term %s;})' % tooltip_content
    return tooltip_content_js_function

def get_custom_term_info_js_function(plot_df, term_description_column_names, term_description_columns, term_word_in_term_description):
    custom_term_html = ''
    term_description_column_names = {} if term_description_column_names is None else term_description_column_names
    for col in term_description_columns:
        if col not in plot_df:
            raise Exception(f'Column {col} not in plot_df')
        formatting = '.toFixed(6)' if pd.api.types.is_float(plot_df[col].iloc[0]) else ''
        custom_term_html += '+ "<b>%s:</b> " + d.etc["%s"]%s + "<br />"' % (html.escape(term_description_column_names.get(col, col)), col.replace('"', '\\"').replace("'", "\\'"), formatting)
    if custom_term_html != '':
        custom_term_html += '+'
    custom_term_info_js_function = '(d => "%s: "+d.term+"<div class=topic_preview>"%s"</div>")' % (term_word_in_term_description, custom_term_html)
    return custom_term_info_js_function

class ClickableTerms:

    @staticmethod
    def get_clickable_lexicon(lexicon, plot_interface='plotInterface'):
        out = []
        for term in lexicon:
            clickable_term = ClickableTerms.get_clickable_term(term, plot_interface)
            out.append(clickable_term)
        return ',\n'.join(out)

    @staticmethod
    def get_clickable_term(term, plot_interface='plotInterface', other_plot_interface=None, style=None):
        onclick_js = ClickableTerms._get_onclick_js(term.replace("'", "\\'"), plot_interface, other_plot_interface)
        onmouseover_js = "{plot_interface}.showToolTipForTerm({plot_interface}.data, {plot_interface}.svg, '%s'," % term.replace("'", "\\'") + "{plot_interface}.termDict['%s'])" % term.replace("'", "\\'")
        onmouseout_js = "{plot_interface}.tooltip.transition().style('opacity', 0)"
        template = '<span onclick="' + onclick_js + '" onmouseover="' + onmouseover_js + '" onmouseout="' + onmouseout_js + '" ' + ('' if style is None else 'style="' + style + '"') + '>{term}</span>'
        clickable_term = template.format(term=term, plot_interface=plot_interface)
        return clickable_term

    @staticmethod
    def _get_onclick_js(term, plot_interface, other_plot_interface=None):
        if other_plot_interface:
            return "{other_plot_interface}.drawCategoryAssociation({plot_interface}.termDict['{term}'].ci); return false;".format(other_plot_interface=other_plot_interface, plot_interface=plot_interface, term=term.replace("'", "\\'"))
        return "{plot_interface}.displayTermContexts({plot_interface}.data, {plot_interface}.gatherTermContexts({plot_interface}.termDict['%s']));" % term.replace("'", "'")

@staticmethod
def get_clickable_term(term, plot_interface='plotInterface', other_plot_interface=None, style=None):
    onclick_js = ClickableTerms._get_onclick_js(term.replace("'", "\\'"), plot_interface, other_plot_interface)
    onmouseover_js = "{plot_interface}.showToolTipForTerm({plot_interface}.data, {plot_interface}.svg, '%s'," % term.replace("'", "\\'") + "{plot_interface}.termDict['%s'])" % term.replace("'", "\\'")
    onmouseout_js = "{plot_interface}.tooltip.transition().style('opacity', 0)"
    template = '<span onclick="' + onclick_js + '" onmouseover="' + onmouseover_js + '" onmouseout="' + onmouseout_js + '" ' + ('' if style is None else 'style="' + style + '"') + '>{term}</span>'
    clickable_term = template.format(term=term, plot_interface=plot_interface)
    return clickable_term

@staticmethod
def _get_onclick_js(term, plot_interface, other_plot_interface=None):
    if other_plot_interface:
        return "{other_plot_interface}.drawCategoryAssociation({plot_interface}.termDict['{term}'].ci); return false;".format(other_plot_interface=other_plot_interface, plot_interface=plot_interface, term=term.replace("'", "\\'"))
    return "{plot_interface}.displayTermContexts({plot_interface}.data, {plot_interface}.gatherTermContexts({plot_interface}.termDict['%s']));" % term.replace("'", "'")

class HTMLSemioticSquareViz(object):

    def __init__(self, semiotic_square):
        """
		Parameters
		----------
		semiotic_square : SemioticSquare
		"""
        self.semiotic_square_ = semiotic_square

    def get_html(self, num_terms=10):
        return self._get_style() + self._get_table(num_terms)

    def _get_style(self):
        return get_halo_td_style()

    def _get_table(self, num_terms):
        lexicons = self.semiotic_square_.get_lexicons(num_terms=num_terms)
        template = self._get_template()
        formatters = {category: self._lexicon_to_html(lexicon) for category, lexicon in lexicons.items()}
        formatters.update(self.semiotic_square_.get_labels())
        for k, v in formatters.items():
            template = template.replace('{' + k + '}', v)
        return template

    def _lexicon_to_html(self, lexicon):
        return ClickableTerms.get_clickable_lexicon(lexicon)

    def _get_template(self):
        return pkgutil.get_data('scattertext', SEMIOTIC_SQUARE_HTML_PATH).decode('utf-8')

def _get_table(self, num_terms):
    lexicons = self.semiotic_square_.get_lexicons(num_terms=num_terms)
    template = self._get_template()
    formatters = {category: self._lexicon_to_html(lexicon) for category, lexicon in lexicons.items()}
    formatters.update(self.semiotic_square_.get_labels())
    for k, v in formatters.items():
        template = template.replace('{' + k + '}', v)
    return template

class PairPlotFromScatterplotStructure(object):

    def __init__(self, category_scatterplot_structure, term_scatterplot_structure, category_projection, category_width, category_height, include_category_labels=True, show_halo=True, num_terms=5, d3_url_struct=None, x_dim=0, y_dim=1, protocol='http', term_plot_interface='termPlotInterface', category_plot_interface='categoryPlotInterface'):
        """,
        Parameters
        ----------
        category_scatterplot_structure: ScatterplotStructure
        term_scatterplot_structure: ScatterplotStructure,
        category_projection: CategoryProjection
        category_height: int
        category_width: int
        show_halo: bool
        num_terms: int, default 5
        include_category_labels: bool, default True
        d3_url_struct: D3URLs
        x_dim: int, 0
        y_dim: int, 1
        protocol: str
            http or https
        term_plot_interface : str
        category_plot_interface : str
        """
        self.category_scatterplot_structure = category_scatterplot_structure
        self.term_scatterplot_structure = term_scatterplot_structure
        self.category_projection = category_projection
        self.d3_url_struct = d3_url_struct if d3_url_struct else D3URLs()
        ExternalJSUtilts.ensure_valid_protocol(protocol)
        self.protocol = protocol
        self.category_width = category_width
        self.category_height = category_height
        self.num_terms = num_terms
        self.show_halo = show_halo
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.include_category_labels = include_category_labels
        self.term_plot_interface = term_plot_interface
        self.category_plot_interface = category_plot_interface

    def to_html(self):
        """
        Returns
        -------
        str, the html file representation

        """
        javascript_to_insert = '\n'.join([PackedDataUtils.full_content_of_javascript_files(), self.category_scatterplot_structure._visualization_data.to_javascript('getCategoryDataAndInfo'), self.category_scatterplot_structure.get_js_to_call_build_scatterplot_with_a_function(self.category_plot_interface), self.term_scatterplot_structure._visualization_data.to_javascript('getTermDataAndInfo'), self.term_scatterplot_structure.get_js_to_call_build_scatterplot_with_a_function(self.term_plot_interface), self.term_scatterplot_structure.get_js_reset_function(values_to_set=[self.category_plot_interface, self.term_plot_interface], functions_to_reset=['build' + self.category_plot_interface, 'build' + self.term_plot_interface]), PackedDataUtils.javascript_post_build_viz('categorySearch', self.category_plot_interface), PackedDataUtils.javascript_post_build_viz('termSearch', self.term_plot_interface)])
        autocomplete_css = PackedDataUtils.full_content_of_default_autocomplete_css()
        html_template = self._get_html_template()
        html_content = HELLO + html_template.replace('/***AUTOCOMPLETE CSS***/', autocomplete_css, 1).replace('<!-- INSERT SCRIPT -->', javascript_to_insert, 1).replace('<!--D3URL-->', self.d3_url_struct.get_d3_url(), 1).replace('<!--D3SCALECHROMATIC-->', self.d3_url_struct.get_d3_scale_chromatic_url())
        html_content = html_content.replace('http://', self.protocol + '://')
        if self.show_halo:
            axes_labels = self.category_projection.get_nearest_terms(num_terms=self.num_terms)
            for position, terms in axes_labels.items():
                html_content = html_content.replace('{%s}' % position, self._get_lexicon_html(terms))
        cellheight, cellheightshort = cell_height_and_cell_height_short_from_height(self.category_height)
        return html_content.replace('{width}', str(self.category_width)).replace('{height}', str(self.category_height)).replace('{cellheight}', str(cellheight)).replace('{cellheightshort}', str(cellheightshort))

    def _get_html_template(self):
        if self.show_halo:
            return PackedDataUtils.get_packaged_html_template_content(PAIR_PLOT_HTML_VIZ_FILE_NAME)
        return PackedDataUtils.get_packaged_html_template_content(PAIR_PLOT_WITHOUT_HALO_HTML_VIZ_FILE_NAME)

    def _get_lexicon_html(self, terms):
        lexicon_html = ''
        for i, term in enumerate(terms):
            lexicon_html += '<b>' + ClickableTerms.get_clickable_term(term, self.term_plot_interface) + '</b>'
            if self.include_category_labels:
                category = self.category_projection.category_counts.loc[term].idxmax()
                lexicon_html += ' (<i>%s</i>)' % ClickableTerms.get_clickable_term(category, self.category_plot_interface, self.term_plot_interface)
            if i != len(terms) - 1:
                lexicon_html += ',\n'
        return lexicon_html

def __init__(self, category_scatterplot_structure, term_scatterplot_structure, category_projection, category_width, category_height, include_category_labels=True, show_halo=True, num_terms=5, d3_url_struct=None, x_dim=0, y_dim=1, protocol='http', term_plot_interface='termPlotInterface', category_plot_interface='categoryPlotInterface'):
    """,
        Parameters
        ----------
        category_scatterplot_structure: ScatterplotStructure
        term_scatterplot_structure: ScatterplotStructure,
        category_projection: CategoryProjection
        category_height: int
        category_width: int
        show_halo: bool
        num_terms: int, default 5
        include_category_labels: bool, default True
        d3_url_struct: D3URLs
        x_dim: int, 0
        y_dim: int, 1
        protocol: str
            http or https
        term_plot_interface : str
        category_plot_interface : str
        """
    self.category_scatterplot_structure = category_scatterplot_structure
    self.term_scatterplot_structure = term_scatterplot_structure
    self.category_projection = category_projection
    self.d3_url_struct = d3_url_struct if d3_url_struct else D3URLs()
    ExternalJSUtilts.ensure_valid_protocol(protocol)
    self.protocol = protocol
    self.category_width = category_width
    self.category_height = category_height
    self.num_terms = num_terms
    self.show_halo = show_halo
    self.x_dim = x_dim
    self.y_dim = y_dim
    self.include_category_labels = include_category_labels
    self.term_plot_interface = term_plot_interface
    self.category_plot_interface = category_plot_interface

def to_html(self):
    """
        Returns
        -------
        str, the html file representation

        """
    javascript_to_insert = '\n'.join([PackedDataUtils.full_content_of_javascript_files(), self.category_scatterplot_structure._visualization_data.to_javascript('getCategoryDataAndInfo'), self.category_scatterplot_structure.get_js_to_call_build_scatterplot_with_a_function(self.category_plot_interface), self.term_scatterplot_structure._visualization_data.to_javascript('getTermDataAndInfo'), self.term_scatterplot_structure.get_js_to_call_build_scatterplot_with_a_function(self.term_plot_interface), self.term_scatterplot_structure.get_js_reset_function(values_to_set=[self.category_plot_interface, self.term_plot_interface], functions_to_reset=['build' + self.category_plot_interface, 'build' + self.term_plot_interface]), PackedDataUtils.javascript_post_build_viz('categorySearch', self.category_plot_interface), PackedDataUtils.javascript_post_build_viz('termSearch', self.term_plot_interface)])
    autocomplete_css = PackedDataUtils.full_content_of_default_autocomplete_css()
    html_template = self._get_html_template()
    html_content = HELLO + html_template.replace('/***AUTOCOMPLETE CSS***/', autocomplete_css, 1).replace('<!-- INSERT SCRIPT -->', javascript_to_insert, 1).replace('<!--D3URL-->', self.d3_url_struct.get_d3_url(), 1).replace('<!--D3SCALECHROMATIC-->', self.d3_url_struct.get_d3_scale_chromatic_url())
    html_content = html_content.replace('http://', self.protocol + '://')
    if self.show_halo:
        axes_labels = self.category_projection.get_nearest_terms(num_terms=self.num_terms)
        for position, terms in axes_labels.items():
            html_content = html_content.replace('{%s}' % position, self._get_lexicon_html(terms))
    cellheight, cellheightshort = cell_height_and_cell_height_short_from_height(self.category_height)
    return html_content.replace('{width}', str(self.category_width)).replace('{height}', str(self.category_height)).replace('{cellheight}', str(cellheight)).replace('{cellheightshort}', str(cellheightshort))

def _get_html_template(self):
    if self.show_halo:
        return PackedDataUtils.get_packaged_html_template_content(PAIR_PLOT_HTML_VIZ_FILE_NAME)
    return PackedDataUtils.get_packaged_html_template_content(PAIR_PLOT_WITHOUT_HALO_HTML_VIZ_FILE_NAME)

class PackedDataUtils:

    @staticmethod
    def full_content_of_default_html_template():
        return PackedDataUtils.get_packaged_html_template_content(DEFAULT_HTML_VIZ_FILE_NAME)

    @staticmethod
    def full_content_of_default_autocomplete_css():
        return PackedDataUtils.get_packaged_html_template_content(AUTOCOMPLETE_CSS_FILE_NAME)

    @staticmethod
    def full_content_of_default_search_form(input_id):
        return PackedDataUtils.get_packaged_html_template_content(SEARCH_FORM_FILE_NAME).replace('{{id}}', input_id)

    @staticmethod
    def full_content_of_javascript_files():
        return PackedDataUtils._load_script_file_names(['rectangle-holder.js', 'main.js', 'autocomplete_definition.js'])

    @staticmethod
    def _load_script_file_names(script_names):
        return '; \n \n '.join([PackedDataUtils.get_packaged_script_content(script_name) for script_name in script_names])

    @staticmethod
    def javascript_post_build_viz(input_id, plot_interface_name):
        return PackedDataUtils._load_script_file_names(['autocomplete_call.js']).replace('{{id}}', input_id).replace('__plotInterface__', plot_interface_name)

    @staticmethod
    def get_packaged_script_content(file_name):
        return pkgutil.get_data('scattertext', 'data/viz/scripts/' + file_name).decode('utf-8')

    @staticmethod
    def get_packaged_html_template_content(file_name):
        return pkgutil.get_data('scattertext', 'data/viz/' + file_name).decode('utf-8')

@staticmethod
def full_content_of_default_html_template():
    return PackedDataUtils.get_packaged_html_template_content(DEFAULT_HTML_VIZ_FILE_NAME)

@staticmethod
def full_content_of_default_autocomplete_css():
    return PackedDataUtils.get_packaged_html_template_content(AUTOCOMPLETE_CSS_FILE_NAME)

@staticmethod
def full_content_of_default_search_form(input_id):
    return PackedDataUtils.get_packaged_html_template_content(SEARCH_FORM_FILE_NAME).replace('{{id}}', input_id)

@staticmethod
def full_content_of_javascript_files():
    return PackedDataUtils._load_script_file_names(['rectangle-holder.js', 'main.js', 'autocomplete_definition.js'])

@staticmethod
def javascript_post_build_viz(input_id, plot_interface_name):
    return PackedDataUtils._load_script_file_names(['autocomplete_call.js']).replace('{{id}}', input_id).replace('__plotInterface__', plot_interface_name)

class BasicHTMLFromScatterplotStructure(object):

    def __init__(self, scatterplot_structure):
        """
        :param scatterplot_structure: ScatterplotStructure
        """
        self.scatterplot_structure = scatterplot_structure

    def to_html(self, protocol='http', d3_url=None, d3_scale_chromatic_url=None, html_base=None, search_input_id='searchInput', halo_colors: Optional[dict]=None):
        """
        Parameters
        ----------
        protocol : str
         'http' or 'https' for including external urls
        d3_url, str
          None by default.  The url (or path) of
          d3, to be inserted into <script src="..."/>
          By default, this is `DEFAULT_D3_URL` declared in `ScatterplotStructure`.
        d3_scale_chromatic_url : str
          None by default.
          URL of d3_scale_chromatic_url, to be inserted into <script src="..."/>
          By default, this is `DEFAULT_D3_SCALE_CHROMATIC` declared in `ScatterplotStructure`.
        html_base : str
            None by default.  HTML of semiotic square to be inserted above plot.
        search_input_id : str
            Id of search input. Default is 'searchInput'.
        halo_colors : Optional[Dict[str, str]]
            If None, defaults to HALO_COLORS. Maps halo position to background color
        Returns
        -------
        str, the html file representation

        """
        halo_colors = HALO_COLORS if halo_colors is None else halo_colors
        d3_url_struct = D3URLs(d3_url, d3_scale_chromatic_url)
        ExternalJSUtilts.ensure_valid_protocol(protocol)
        javascript_to_insert = '\n'.join([PackedDataUtils.full_content_of_javascript_files(), self.scatterplot_structure._visualization_data.to_javascript(), self.scatterplot_structure.get_js_to_call_build_scatterplot(), PackedDataUtils.javascript_post_build_viz(search_input_id, 'plotInterface')])
        html_template = PackedDataUtils.full_content_of_default_html_template() if html_base is None else self._format_html_base(html_base, halo_colors)
        html_content = HELLO + html_template.replace('<!-- INSERT SCRIPT -->', javascript_to_insert, 1).replace('<!-- INSERT SEARCH FORM -->', PackedDataUtils.full_content_of_default_search_form(search_input_id), 1).replace('<!--D3URL-->', d3_url_struct.get_d3_url(), 1).replace('<!--D3SCALECHROMATIC-->', d3_url_struct.get_d3_scale_chromatic_url())
        "\n        if html_base is not None:\n            html_file = html_file.replace('<!-- INSERT SEMIOTIC SQUARE -->',\n                                          html_base)\n        "
        extra_libs = ''
        if self.scatterplot_structure._save_svg_button:
            extra_libs = ''
        autocomplete_css = PackedDataUtils.full_content_of_default_autocomplete_css()
        html_content = html_content.replace('/***AUTOCOMPLETE CSS***/', autocomplete_css, 1).replace('<!-- EXTRA LIBS -->', extra_libs, 1).replace('http://', protocol + '://')
        return html_content

    def _format_html_base(self, html_base, halo_colors):
        height = self.scatterplot_structure._height_in_pixels
        cellheight, cellheightshort = cell_height_and_cell_height_short_from_height(height)
        html = html_base.replace('{width}', str(self.scatterplot_structure._width_in_pixels)).replace('{height}', str(height)).replace('{cellheight}', str(cellheight)).replace('{cellheightshort}', str(cellheightshort))
        for position, color in halo_colors.items():
            html = html.replace('{' + f'{position}_halo_color' + '}', color)
        return html

def to_html(self, protocol='http', d3_url=None, d3_scale_chromatic_url=None, html_base=None, search_input_id='searchInput', halo_colors: Optional[dict]=None):
    """
        Parameters
        ----------
        protocol : str
         'http' or 'https' for including external urls
        d3_url, str
          None by default.  The url (or path) of
          d3, to be inserted into <script src="..."/>
          By default, this is `DEFAULT_D3_URL` declared in `ScatterplotStructure`.
        d3_scale_chromatic_url : str
          None by default.
          URL of d3_scale_chromatic_url, to be inserted into <script src="..."/>
          By default, this is `DEFAULT_D3_SCALE_CHROMATIC` declared in `ScatterplotStructure`.
        html_base : str
            None by default.  HTML of semiotic square to be inserted above plot.
        search_input_id : str
            Id of search input. Default is 'searchInput'.
        halo_colors : Optional[Dict[str, str]]
            If None, defaults to HALO_COLORS. Maps halo position to background color
        Returns
        -------
        str, the html file representation

        """
    halo_colors = HALO_COLORS if halo_colors is None else halo_colors
    d3_url_struct = D3URLs(d3_url, d3_scale_chromatic_url)
    ExternalJSUtilts.ensure_valid_protocol(protocol)
    javascript_to_insert = '\n'.join([PackedDataUtils.full_content_of_javascript_files(), self.scatterplot_structure._visualization_data.to_javascript(), self.scatterplot_structure.get_js_to_call_build_scatterplot(), PackedDataUtils.javascript_post_build_viz(search_input_id, 'plotInterface')])
    html_template = PackedDataUtils.full_content_of_default_html_template() if html_base is None else self._format_html_base(html_base, halo_colors)
    html_content = HELLO + html_template.replace('<!-- INSERT SCRIPT -->', javascript_to_insert, 1).replace('<!-- INSERT SEARCH FORM -->', PackedDataUtils.full_content_of_default_search_form(search_input_id), 1).replace('<!--D3URL-->', d3_url_struct.get_d3_url(), 1).replace('<!--D3SCALECHROMATIC-->', d3_url_struct.get_d3_scale_chromatic_url())
    "\n        if html_base is not None:\n            html_file = html_file.replace('<!-- INSERT SEMIOTIC SQUARE -->',\n                                          html_base)\n        "
    extra_libs = ''
    if self.scatterplot_structure._save_svg_button:
        extra_libs = ''
    autocomplete_css = PackedDataUtils.full_content_of_default_autocomplete_css()
    html_content = html_content.replace('/***AUTOCOMPLETE CSS***/', autocomplete_css, 1).replace('<!-- EXTRA LIBS -->', extra_libs, 1).replace('http://', protocol + '://')
    return html_content

