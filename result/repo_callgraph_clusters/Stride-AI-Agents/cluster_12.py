# Cluster 12

def main():
    cprint("🌟 [bold green]Welcome to the Crawl4ai Quickstart Guide! Let's dive into some web crawling fun! 🌐[/bold green]")
    cprint('⛳️ [bold cyan]First Step: Create an instance of WebCrawler and call the `warmup()` function.[/bold cyan]')
    cprint("If this is the first time you're running Crawl4ai, this might take a few seconds to load required model files.")
    crawler = create_crawler()
    crawler.always_by_pass_cache = True
    basic_usage(crawler)
    understanding_parameters(crawler)
    crawler.always_by_pass_cache = True
    screenshot_usage(crawler)
    add_chunking_strategy(crawler)
    add_extraction_strategy(crawler)
    add_llm_extraction_strategy(crawler)
    targeted_extraction(crawler)
    interactive_extraction(crawler)
    multiple_scrip(crawler)
    cprint("\n🎉 [bold green]Congratulations! You've made it through the Crawl4ai Quickstart Guide! Now go forth and crawl the web like a pro! 🕸️[/bold green]")

