# Cluster 13

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

def _get_style(self):
    return get_halo_td_style()

