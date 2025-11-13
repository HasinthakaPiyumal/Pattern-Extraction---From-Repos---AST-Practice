# Cluster 183

class DataFeedManager:
    """Central manager for all data feeds"""

    def __init__(self):
        self.feeds = {'economic': EconomicDataFeed(), 'news': NewsDataFeed(), 'market': MarketDataFeed(), 'sentiment': SentimentDataFeed(), 'geopolitical': GeopoliticalDataFeed()}

    async def get_multi_source_data(self, data_requests: Dict[str, Dict]) -> Dict[str, List[DataPoint]]:
        """Get data from multiple sources concurrently"""
        results = {}

        async def fetch_data(feed_name: str, feed_obj: Any, request_params: Dict):
            async with feed_obj as feed:
                if feed_name == 'economic':
                    data = await feed.get_series(**request_params)
                elif feed_name == 'news':
                    data = await feed.get_headlines(**request_params)
                elif feed_name == 'market':
                    if request_params.get('data_type') == 'institutional':
                        data = await feed.get_institutional_trades(request_params['symbol'])
                    else:
                        data = await feed.get_insider_trades(**request_params)
                elif feed_name == 'sentiment':
                    data = await feed.get_reddit_sentiment(**request_params)
                elif feed_name == 'geopolitical':
                    data = await feed.get_conflict_data()
                else:
                    data = []
                results[feed_name] = data
        tasks = []
        for feed_name, request_params in data_requests.items():
            if feed_name in self.feeds:
                feed_obj = self.feeds[feed_name]
                tasks.append(fetch_data(feed_name, feed_obj, request_params))
        await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def get_latest_data_summary(self) -> Dict[str, Any]:
        """Get summary of latest data availability"""
        summary = {'timestamp': datetime.now().isoformat(), 'data_sources': list(self.feeds.keys()), 'cache_status': 'enabled' if CONFIG.agent.enable_caching else 'disabled', 'api_rate_limits': {'economic': f'{CONFIG.agent.max_api_calls_per_hour}/hour', 'news': f'{CONFIG.agent.max_api_calls_per_hour}/hour', 'market': f'{CONFIG.agent.max_api_calls_per_hour}/hour'}}
        return summary

def __init__(self):
    self.feeds = {'economic': EconomicDataFeed(), 'news': NewsDataFeed(), 'market': MarketDataFeed(), 'sentiment': SentimentDataFeed(), 'geopolitical': GeopoliticalDataFeed()}

