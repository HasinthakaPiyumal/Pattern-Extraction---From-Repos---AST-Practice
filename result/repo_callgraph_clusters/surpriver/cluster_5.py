# Cluster 5

class Surpriver:

    def __init__(self):
        print('Surpriver has been initialized...')
        self.TOP_PREDICTIONS_TO_PRINT = top_n
        self.HISTORY_TO_USE = history_to_use
        self.MINIMUM_VOLUME = min_volume
        self.IS_LOAD_FROM_DICTIONARY = is_load_from_dictionary
        self.DATA_DICTIONARY_PATH = data_dictionary_path
        self.IS_SAVE_DICTIONARY = is_save_dictionary
        self.DATA_GRANULARITY_MINUTES = data_granularity_minutes
        self.IS_TEST = is_test
        self.FUTURE_BARS_FOR_TESTING = future_bars
        self.VOLATILITY_FILTER = volatility_filter
        self.OUTPUT_FORMAT = output_format
        self.STOCK_LIST = stock_list
        self.DATA_SOURCE = data_source
        self.dataEngine = DataEngine(self.HISTORY_TO_USE, self.DATA_GRANULARITY_MINUTES, self.IS_SAVE_DICTIONARY, self.IS_LOAD_FROM_DICTIONARY, self.DATA_DICTIONARY_PATH, self.MINIMUM_VOLUME, self.IS_TEST, self.FUTURE_BARS_FOR_TESTING, self.VOLATILITY_FILTER, self.STOCK_LIST, self.DATA_SOURCE)

    def is_nan(self, object):
        """
		Checks if a value is null. 
		"""
        return object != object

    def calculate_percentage_change(self, old, new):
        return (new - old) * 100 / old

    def calculate_return(self, old, new):
        return new / old

    def parse_large_values(self, value):
        if value < 1000:
            value = str(value)
        elif value >= 1000 and value < 1000000:
            value = round(value / 1000, 2)
            value = str(value) + 'K'
        else:
            value = round(value / 1000000, 1)
            value = str(value) + 'M'
        return value

    def calculate_volume_changes(self, historical_price):
        volume = list(historical_price['Volume'])
        dates = list(historical_price['Datetime'])
        dates = [str(date) for date in dates]
        volume_by_date_dictionary = collections.defaultdict(list)
        for j in range(0, len(volume)):
            date = dates[j].split(' ')[0]
            volume_by_date_dictionary[date].append(volume[j])
        for key in volume_by_date_dictionary:
            volume_by_date_dictionary[key] = np.sum(volume_by_date_dictionary[key])
        all_dates = list(reversed(sorted(volume_by_date_dictionary.keys())))
        latest_date = all_dates[0]
        latest_data_point = list(reversed(sorted(dates)))[0]
        today_volume = volume_by_date_dictionary[latest_date]
        average_vol_last_five_days = np.mean([volume_by_date_dictionary[date] for date in all_dates[1:6]])
        average_vol_last_twenty_days = np.mean([volume_by_date_dictionary[date] for date in all_dates[1:20]])
        return (latest_data_point, self.parse_large_values(today_volume), self.parse_large_values(average_vol_last_five_days), self.parse_large_values(average_vol_last_twenty_days))

    def calculate_recent_volatility(self, historical_price):
        close_price = list(historical_price['Close'])
        volatility_five_bars = np.std(close_price[-5:])
        volatility_twenty_bars = np.std(close_price[-20:])
        volatility_all = np.std(close_price)
        return (volatility_five_bars, volatility_twenty_bars, volatility_all)

    def calculate_future_performance(self, future_data):
        CLOSE_PRICE_INDEX = 4
        price_at_alert = future_data[0][CLOSE_PRICE_INDEX]
        prices_in_future = [item[CLOSE_PRICE_INDEX] for item in future_data[1:]]
        prices_in_future = [item for item in prices_in_future if item != 0]
        total_sum_percentage_change = abs(sum([self.calculate_percentage_change(price_at_alert, next_price) for next_price in prices_in_future]))
        future_volatility = np.std(prices_in_future)
        return (total_sum_percentage_change, future_volatility)

    def find_anomalies(self):
        """
		Main function that does everything
		"""
        if self.IS_LOAD_FROM_DICTIONARY == 0:
            features, historical_price_info, future_prices, symbol_names = self.dataEngine.collect_data_for_all_tickers()
        else:
            features, historical_price_info, future_prices, symbol_names = self.dataEngine.load_data_from_dictionary()
        detector = IsolationForest(n_estimators=100, random_state=0)
        detector.fit(features)
        predictions = detector.decision_function(features)
        predictions_with_output_data = [[predictions[i], symbol_names[i], historical_price_info[i], future_prices[i]] for i in range(0, len(predictions))]
        predictions_with_output_data = list(sorted(predictions_with_output_data))
        results = []
        for item in predictions_with_output_data[:self.TOP_PREDICTIONS_TO_PRINT]:
            prediction, symbol, historical_price, future_price = item
            if self.IS_TEST == 1 and len(future_price) < 5:
                print('No future data is present. Please make sure that you ran the prior command with is_test enabled or disable that command now. Exiting now...')
                exit()
            latest_date, today_volume, average_vol_last_five_days, average_vol_last_twenty_days = self.calculate_volume_changes(historical_price)
            volatility_vol_last_five_days, volatility_vol_last_twenty_days, _ = self.calculate_recent_volatility(historical_price)
            if average_vol_last_five_days == None or volatility_vol_last_five_days == None:
                continue
            if self.IS_TEST == 0:
                if self.OUTPUT_FORMAT == 'CLI':
                    print('Last Bar Time: %s\nSymbol: %s\nAnomaly Score: %.3f\nToday Volume: %s\nAverage Volume 5d: %s\nAverage Volume 20d: %s\nVolatility 5bars: %.3f\nVolatility 20bars: %.3f\n----------------------' % (latest_date, symbol, prediction, today_volume, average_vol_last_five_days, average_vol_last_twenty_days, volatility_vol_last_five_days, volatility_vol_last_twenty_days))
                results.append({'latest_date': latest_date, 'Symbol': symbol, 'Anomaly Score': prediction, 'Today Volume': today_volume, 'Average Volume 5d': average_vol_last_five_days, 'Average Volume 20d': average_vol_last_twenty_days, 'Volatility 5bars': volatility_vol_last_five_days, 'Volatility 20bars': volatility_vol_last_twenty_days})
            else:
                future_abs_sum_percentage_change, _ = self.calculate_future_performance(future_price)
                if self.OUTPUT_FORMAT == 'CLI':
                    print('Last Bar Time: %s\nSymbol: %s\nAnomaly Score: %.3f\nToday Volume: %s\nAverage Volume 5d: %s\nAverage Volume 20d: %s\nVolatility 5bars: %.3f\nVolatility 20bars: %.3f\nFuture Absolute Sum Price Changes: %.2f\n----------------------' % (latest_date, symbol, prediction, today_volume, average_vol_last_five_days, average_vol_last_twenty_days, volatility_vol_last_five_days, volatility_vol_last_twenty_days, future_abs_sum_percentage_change))
                results.append({'latest_date': latest_date, 'Symbol': symbol, 'Anomaly Score': prediction, 'Today Volume': today_volume, 'Average Volume 5d': average_vol_last_five_days, 'Average Volume 20d': average_vol_last_twenty_days, 'Volatility 5bars': volatility_vol_last_five_days, 'Volatility 20bars': volatility_vol_last_twenty_days, 'Future Absolute Sum Price Changes': future_abs_sum_percentage_change})
        if self.OUTPUT_FORMAT == 'JSON':
            self.store_results(results)
        if self.IS_TEST == 1:
            self.calculate_future_stats(predictions_with_output_data)

    def store_results(self, results):
        """
		Function for storing results in a file
		"""
        today = dt.datetime.today().strftime('%Y-%m-%d')
        prefix = 'results'
        if self.IS_TEST != 0:
            prefix = 'results_future'
        file_name = '%s_%s.json' % (prefix, str(today))
        with open(file_name, 'w+') as result_file:
            json.dump(results, result_file)
        print('Results stored successfully in', file_name)

    def calculate_future_stats(self, predictions_with_output_data):
        """
		Calculate different stats for future data to show whether the anomalous stocks found were actually better than non-anomalous ones
		"""
        future_change = []
        anomalous_score = []
        historical_volatilities = []
        future_volatilities = []
        for item in predictions_with_output_data:
            prediction, symbol, historical_price, future_price = item
            future_sum_percentage_change, future_volatility = self.calculate_future_performance(future_price)
            _, _, historical_volatility = self.calculate_recent_volatility(historical_price)
            if abs(future_sum_percentage_change) > 250 or self.is_nan(future_sum_percentage_change) == True or self.is_nan(prediction) == True:
                continue
            future_change.append(future_sum_percentage_change)
            anomalous_score.append(prediction)
            future_volatilities.append(future_volatility)
            historical_volatilities.append(historical_volatility)
        correlation = np.corrcoef(anomalous_score, future_change)[0, 1]
        anomalous_future_changes = np.mean([future_change[x] for x in range(0, len(future_change)) if anomalous_score[x] < 0])
        normal_future_changes = np.mean([future_change[x] for x in range(0, len(future_change)) if anomalous_score[x] >= 0])
        anomalous_future_volatilities = np.mean([future_volatilities[x] for x in range(0, len(future_volatilities)) if anomalous_score[x] < 0])
        normal_future_volatilities = np.mean([future_volatilities[x] for x in range(0, len(future_volatilities)) if anomalous_score[x] >= 0])
        anomalous_historical_volatilities = np.mean([historical_volatilities[x] for x in range(0, len(historical_volatilities)) if anomalous_score[x] < 0])
        normal_historical_volatilities = np.mean([historical_volatilities[x] for x in range(0, len(historical_volatilities)) if anomalous_score[x] >= 0])
        print('\n*************** Future Performance ***************')
        print('Correlation between future absolute change vs anomalous score (lower is better, range = (-1, 1)): **%.2f**\nTotal absolute change in future for Anomalous Stocks: **%.3f**\nTotal absolute change in future for Normal Stocks: **%.3f**\nAverage future volatility of Anomalous Stocks: **%.3f**\nAverage future volatility of Normal Stocks: **%.3f**\nHistorical volatility for Anomalous Stocks: **%.3f**\nHistorical volatility for Normal Stocks: **%.3f**\n' % (correlation, anomalous_future_changes, normal_future_changes, anomalous_future_volatilities, normal_future_volatilities, anomalous_historical_volatilities, normal_historical_volatilities))
        FONT_SIZE = 14
        colors = ['#c91414' if anomalous_score[x] < 0 else '#035AA6' for x in range(0, len(anomalous_score))]
        anomalous_vs_normal = np.array([1 if anomalous_score[x] < 0 else 0 for x in range(0, len(anomalous_score))])
        plt.scatter(np.array(anomalous_score)[anomalous_vs_normal == 1], np.array(future_change)[anomalous_vs_normal == 1], marker='v', color='#c91414')
        plt.scatter(np.array(anomalous_score)[anomalous_vs_normal == 0], np.array(future_change)[anomalous_vs_normal == 0], marker='P', color='#035AA6')
        plt.axvline(x=0, linestyle='--', color='#848484')
        plt.xlabel('Anomaly Score', fontsize=FONT_SIZE)
        plt.ylabel('Absolute Future Change', fontsize=FONT_SIZE)
        plt.xticks(fontsize=FONT_SIZE)
        plt.yticks(fontsize=FONT_SIZE)
        plt.legend(['Anomalous', 'Normal'], fontsize=FONT_SIZE)
        plt.title('Absolute Future Change', fontsize=FONT_SIZE)
        plt.tight_layout()
        plt.grid()
        plt.show()

def calculate_recent_volatility(self, historical_price):
    close_price = list(historical_price['Close'])
    volatility_five_bars = np.std(close_price[-5:])
    volatility_twenty_bars = np.std(close_price[-20:])
    volatility_all = np.std(close_price)
    return (volatility_five_bars, volatility_twenty_bars, volatility_all)

def calculate_future_performance(self, future_data):
    CLOSE_PRICE_INDEX = 4
    price_at_alert = future_data[0][CLOSE_PRICE_INDEX]
    prices_in_future = [item[CLOSE_PRICE_INDEX] for item in future_data[1:]]
    prices_in_future = [item for item in prices_in_future if item != 0]
    total_sum_percentage_change = abs(sum([self.calculate_percentage_change(price_at_alert, next_price) for next_price in prices_in_future]))
    future_volatility = np.std(prices_in_future)
    return (total_sum_percentage_change, future_volatility)

class DataEngine:

    def __init__(self, history_to_use, data_granularity_minutes, is_save_dict, is_load_dict, dict_path, min_volume_filter, is_test, future_bars_for_testing, volatility_filter, stocks_list, data_source):
        print('Data engine has been initialized...')
        self.DATA_GRANULARITY_MINUTES = data_granularity_minutes
        self.IS_SAVE_DICT = is_save_dict
        self.IS_LOAD_DICT = is_load_dict
        self.DICT_PATH = dict_path
        self.VOLUME_FILTER = min_volume_filter
        self.FUTURE_FOR_TESTING = future_bars_for_testing
        self.IS_TEST = is_test
        self.VOLATILITY_THRESHOLD = volatility_filter
        self.DATA_SOURCE = data_source
        self.directory_path = str(os.path.dirname(os.path.abspath(__file__)))
        self.stocks_file_path = self.directory_path + f'/stocks/{stocks_list}'
        self.stocks_list = []
        self.load_stocks_from_file()
        self.taEngine = TAEngine(history_to_use=history_to_use)
        self.features_dictionary_for_all_symbols = {}
        self.stock_data_length = []
        self.binance_client = Client('', '')

    def load_stocks_from_file(self):
        """
		Load stock names from the file
		"""
        print('Loading all stocks from file...')
        stocks_list = open(self.stocks_file_path, 'r').readlines()
        stocks_list = [str(item).strip('\n') for item in stocks_list]
        stocks_list = list(sorted(set(stocks_list)))
        print('Total number of stocks: %d' % len(stocks_list))
        self.stocks_list = stocks_list

    def get_most_frequent_key(self, input_list):
        counter = collections.Counter(input_list)
        counter_keys = list(counter.keys())
        frequent_key = counter_keys[0]
        return frequent_key

    def get_data(self, symbol):
        """
		Get stock data.
		"""
        if self.DATA_GRANULARITY_MINUTES == 1:
            period = '7d'
        else:
            period = '30d'
        try:
            if self.DATA_SOURCE == 'binance':
                if self.DATA_GRANULARITY_MINUTES == 60:
                    interval = '1h'
                else:
                    interval = str(self.DATA_GRANULARITY_MINUTES) + 'm'
                stock_prices = self.binance_client.get_klines(symbol=symbol, interval=interval)
                if len(stock_prices) == 0:
                    return ([], [], True)
                stock_prices = pd.DataFrame(stock_prices, columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
                stock_prices['Datetime'] = stock_prices['Datetime'].astype(float)
                stock_prices['Open'] = stock_prices['Open'].astype(float)
                stock_prices['High'] = stock_prices['High'].astype(float)
                stock_prices['Low'] = stock_prices['Low'].astype(float)
                stock_prices['Close'] = stock_prices['Close'].astype(float)
                stock_prices['Volume'] = stock_prices['Volume'].astype(float)
            else:
                stock_prices = yf.download(tickers=symbol, period=period, interval=str(self.DATA_GRANULARITY_MINUTES) + 'm', auto_adjust=False, progress=False)
            stock_prices = stock_prices.reset_index()
            stock_prices = stock_prices[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
            data_length = len(stock_prices.values.tolist())
            self.stock_data_length.append(data_length)
            if len(self.stock_data_length) > 5:
                most_frequent_key = self.get_most_frequent_key(self.stock_data_length)
                if data_length != most_frequent_key:
                    return ([], [], True)
            if self.IS_TEST == 1:
                stock_prices_list = stock_prices.values.tolist()
                stock_prices_list = stock_prices_list[1:]
                future_prices_list = stock_prices_list[-(self.FUTURE_FOR_TESTING + 1):]
                historical_prices = stock_prices_list[:-self.FUTURE_FOR_TESTING]
                historical_prices = pd.DataFrame(historical_prices)
                historical_prices.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
            else:
                stock_prices_list = stock_prices.values.tolist()
                stock_prices_list = stock_prices_list[1:]
                historical_prices = pd.DataFrame(stock_prices_list)
                historical_prices.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
                future_prices_list = []
            if len(stock_prices.values.tolist()) == 0:
                return ([], [], True)
        except:
            return ([], [], True)
        return (historical_prices, future_prices_list, False)

    def calculate_volatility(self, stock_price_data):
        CLOSE_PRICE_INDEX = 4
        stock_price_data_list = stock_price_data.values.tolist()
        close_prices = [float(item[CLOSE_PRICE_INDEX]) for item in stock_price_data_list]
        close_prices = [item for item in close_prices if item != 0]
        volatility = np.std(close_prices)
        return volatility

    def collect_data_for_all_tickers(self):
        """
		Iterates over all symbols and collects their data
		"""
        print('Loading data for all stocks...')
        features = []
        symbol_names = []
        historical_price_info = []
        future_price_info = []
        for i in tqdm(range(len(self.stocks_list))):
            symbol = self.stocks_list[i]
            try:
                stock_price_data, future_prices, not_found = self.get_data(symbol)
                if not not_found:
                    volatility = self.calculate_volatility(stock_price_data)
                    if volatility < self.VOLATILITY_THRESHOLD:
                        continue
                    features_dictionary = self.taEngine.get_technical_indicators(stock_price_data)
                    feature_list = self.taEngine.get_features(features_dictionary)
                    self.features_dictionary_for_all_symbols[symbol] = {'features': features_dictionary, 'current_prices': stock_price_data, 'future_prices': future_prices}
                    if len(self.features_dictionary_for_all_symbols) % 100 == 0 and self.IS_SAVE_DICT == 1:
                        np.save(self.DICT_PATH, self.features_dictionary_for_all_symbols)
                    if np.isnan(feature_list).any() == True:
                        continue
                    average_volume_last_30_tickers = np.mean(list(stock_price_data['Volume'])[-30:])
                    if average_volume_last_30_tickers < self.VOLUME_FILTER:
                        continue
                    features.append(feature_list)
                    symbol_names.append(symbol)
                    historical_price_info.append(stock_price_data)
                    future_price_info.append(future_prices)
            except Exception as e:
                print('Exception', e)
                continue
        features, historical_price_info, future_price_info, symbol_names = self.remove_bad_data(features, historical_price_info, future_price_info, symbol_names)
        return (features, historical_price_info, future_price_info, symbol_names)

    def load_data_from_dictionary(self):
        print('Loading data from dictionary')
        dictionary_data = np.load(self.DICT_PATH, allow_pickle=True).item()
        features = []
        symbol_names = []
        historical_price_info = []
        future_price_info = []
        for symbol in dictionary_data:
            feature_list = self.taEngine.get_features(dictionary_data[symbol]['features'])
            current_prices = dictionary_data[symbol]['current_prices']
            future_prices = dictionary_data[symbol]['future_prices']
            if np.isnan(feature_list).any() == True:
                continue
            features.append(feature_list)
            symbol_names.append(symbol)
            historical_price_info.append(current_prices)
            future_price_info.append(future_prices)
        features, historical_price_info, future_price_info, symbol_names = self.remove_bad_data(features, historical_price_info, future_price_info, symbol_names)
        return (features, historical_price_info, future_price_info, symbol_names)

    def remove_bad_data(self, features, historical_price_info, future_price_info, symbol_names):
        """
		Remove bad data i.e data that had some errors while scraping or feature generation
		"""
        length_dictionary = collections.Counter([len(feature) for feature in features])
        length_dictionary = list(length_dictionary.keys())
        most_common_length = length_dictionary[0]
        filtered_features, filtered_historical_price, filtered_future_prices, filtered_symbols = ([], [], [], [])
        for i in range(0, len(features)):
            if len(features[i]) == most_common_length:
                filtered_features.append(features[i])
                filtered_symbols.append(symbol_names[i])
                filtered_historical_price.append(historical_price_info[i])
                filtered_future_prices.append(future_price_info[i])
        return (filtered_features, filtered_historical_price, filtered_future_prices, filtered_symbols)

def calculate_volatility(self, stock_price_data):
    CLOSE_PRICE_INDEX = 4
    stock_price_data_list = stock_price_data.values.tolist()
    close_prices = [float(item[CLOSE_PRICE_INDEX]) for item in stock_price_data_list]
    close_prices = [item for item in close_prices if item != 0]
    volatility = np.std(close_prices)
    return volatility

