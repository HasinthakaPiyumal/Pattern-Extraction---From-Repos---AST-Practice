# Cluster 18

class RAG:

    def __init__(self, llm, retriever, parser, prompt_template, format_func) -> None:
        self.rag_chain = {'examples': retriever | format_func, 'prompt': RunnablePassthrough()} | prompt_template | llm | parser

    def gen(self, prompt):
        return self.rag_chain.invoke(prompt)

def __init__(self, llm, retriever, parser, prompt_template, format_func) -> None:
    self.rag_chain = {'examples': retriever | format_func, 'prompt': RunnablePassthrough()} | prompt_template | llm | parser

