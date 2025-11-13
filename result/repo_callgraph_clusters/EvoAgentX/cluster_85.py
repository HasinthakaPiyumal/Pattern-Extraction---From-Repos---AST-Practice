# Cluster 85

class StockDataFetcher:
    """股票数据抓取器 - 核心功能类"""

    def __init__(self, stock_code, auto_create_output_dir=True):
        """
        初始化数据抓取器
        
        Args:
            stock_code (str): 股票代码（如：300750、000001等）
            auto_create_output_dir (bool): 是否自动创建输出目录，默认True
        """
        self.stock_code = stock_code
        self.symbol_sz = f'sz{stock_code}' if stock_code.startswith('0') or stock_code.startswith('3') else f'sh{stock_code}'
        if auto_create_output_dir:
            self.output_dir = Path(f'output_{stock_code}')
        else:
            self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.stock_name = self._get_stock_name()

    def _get_stock_name(self):
        """获取股票名称"""
        try:
            stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
            if not stock_info.empty:
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    return name_row['value'].iloc[0]
            return f'股票{self.stock_code}'
        except:
            return f'股票{self.stock_code}'

    def get_timestamp(self):
        """获取当前日期用于文件命名"""
        return datetime.datetime.now().strftime('%Y%m%d')

    def save_data(self, data, filename_prefix, description=''):
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据（pandas DataFrame）
            filename_prefix (str): 文件名前缀
            description (str): 数据描述
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            timestamp = self.get_timestamp()
            filename = f'{filename_prefix}_{timestamp}_{self.stock_code}.csv'
            filepath = self.output_dir / filename
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath} (共{len(data)}条记录)')
            else:
                df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath}')
            return str(filepath)
        except Exception as e:
            self.logger.error(f'❌ 保存{description}失败: {str(e)}')
            return None

    def fetch_stock_daily(self, days=30):
        """
        抓取股票日线数据
        
        Args:
            days (int): 抓取最近多少天的数据，默认30天
            
        Returns:
            pandas.DataFrame: 股票日线数据
        """
        try:
            self.logger.info(f'📈 开始抓取{self.stock_code}日线数据...')
            stock_df = ak.stock_zh_a_daily(symbol=self.symbol_sz).reset_index()
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
            recent_data = stock_df[stock_df['date'] >= days_ago]
            self.save_data(recent_data, 'stock_daily_catl', f'{self.stock_code}日线数据')
            return recent_data
        except Exception as e:
            self.logger.error(f'❌ 抓取股票日线数据失败: {str(e)}')
            return None

    def fetch_china_cpi(self):
        """
        抓取中国CPI数据 (限制为过去2年)
        
        Returns:
            pandas.DataFrame: 中国CPI数据
        """
        try:
            self.logger.info('📊 开始抓取中国CPI数据...')
            cpi_df = ak.macro_china_cpi()
            if not cpi_df.empty:
                if '月份' in cpi_df.columns:

                    def convert_chinese_date(date_str):
                        try:
                            if '年' in date_str and '月' in date_str:
                                year = date_str.split('年')[0]
                                month = date_str.split('年')[1].split('月')[0]
                                return f'{year}-{month.zfill(2)}-01'
                            else:
                                return date_str
                        except:
                            return None
                    cpi_df['月份'] = cpi_df['月份'].apply(convert_chinese_date)
                    cpi_df['月份'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
                    cpi_df = cpi_df.dropna(subset=['月份'])
                    if not cpi_df.empty:
                        two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
                        cpi_df = cpi_df[cpi_df['月份'] >= two_years_ago]
                        self.logger.info(f'✅ CPI数据已限制为过去2年: {len(cpi_df)} 条记录')
            return cpi_df
        except Exception as e:
            self.logger.error(f'❌ 抓取CPI数据失败: {str(e)}')
            return None

    def fetch_china_gdp(self):
        """
        抓取中国GDP数据
        
        Returns:
            pandas.DataFrame: 中国GDP数据
        """
        try:
            self.logger.info('📊 开始抓取中国GDP数据...')
            gdp_df = ak.macro_china_gdp_yearly()
            return gdp_df
        except Exception as e:
            self.logger.error(f'❌ 抓取GDP数据失败: {str(e)}')
            return None

    def fetch_industry_fund_flow(self):
        """
        抓取行业资金流数据
        
        Returns:
            pandas.DataFrame: 行业资金流数据
        """
        try:
            self.logger.info('💰 开始抓取行业资金流数据...')
            industry_fund_df = ak.stock_fund_flow_industry()
            return industry_fund_df
        except Exception as e:
            self.logger.error(f'❌ 抓取行业资金流数据失败: {str(e)}')
            return None

    def fetch_stock_news(self):
        """
        抓取个股新闻数据
        
        Returns:
            pandas.DataFrame: 个股新闻数据
        """
        try:
            self.logger.info(f'📰 开始抓取{self.stock_name}({self.stock_code})新闻数据...')
            news_df = ak.stock_news_em(symbol=self.stock_code)
            return news_df
        except Exception as e:
            self.logger.error(f'❌ 抓取新闻数据失败: {str(e)}')
            return None

    def fetch_market_summary(self):
        """
        抓取上交所市场概况
        
        Returns:
            pandas.DataFrame: 市场概况数据
        """
        try:
            self.logger.info('🏛️ 开始抓取上交所市场概况...')
            sse_summary = ak.stock_sse_summary()
            return sse_summary
        except Exception as e:
            self.logger.error(f'❌ 抓取市场概况失败: {str(e)}')
            return None

    def fetch_market_indices(self):
        """
        抓取重要指数行情
        
        Returns:
            pandas.DataFrame: 重要指数数据
        """
        try:
            self.logger.info('📊 开始抓取重要指数行情...')
            market_indices = ak.stock_zh_index_spot_em(symbol='沪深重要指数')
            return market_indices
        except Exception as e:
            self.logger.error(f'❌ 抓取市场指数失败: {str(e)}')
            return None

    def fetch_option_volatility(self):
        """
        抓取50ETF期权波动率指数 (限制为过去1个月)
        
        Returns:
            pandas.DataFrame: 期权波动率数据
        """
        try:
            self.logger.info('📈 开始抓取50ETF波动率指数...')
            vol50 = ak.index_option_50etf_qvix()
            if not vol50.empty:
                if 'date' in vol50.columns:
                    vol50['date'] = pd.to_datetime(vol50['date'])
                    one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    vol50 = vol50[vol50['date'] >= one_month_ago]
                    self.logger.info(f'✅ 期权波动率数据已限制为过去1个月: {len(vol50)} 条记录')
            return vol50
        except Exception as e:
            self.logger.error(f'❌ 抓取期权波动率数据失败: {str(e)}')
            return None

    def fetch_institution_recommendation(self):
        """
        抓取机构评级数据 (限制为过去半年)
        
        Returns:
            pandas.DataFrame: 机构评级数据
        """
        try:
            self.logger.info(f'🏦 开始抓取{self.stock_name}({self.stock_code})机构评级...')
            inst_rec = ak.stock_institute_recommend_detail(symbol=self.stock_code)
            if not inst_rec.empty:
                date_columns = ['评级日期', 'date', '日期']
                date_col = None
                for col in date_columns:
                    if col in inst_rec.columns:
                        date_col = col
                        break
                if date_col:
                    inst_rec[date_col] = pd.to_datetime(inst_rec[date_col])
                    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                    inst_rec = inst_rec[inst_rec[date_col] >= six_months_ago]
                    self.logger.info(f'✅ 机构评级数据已限制为过去半年: {len(inst_rec)} 条记录')
            return inst_rec
        except Exception as e:
            self.logger.error(f'❌ 抓取机构评级数据失败: {str(e)}')
            return None

    def fetch_all_data(self):
        """
        抓取所有类型的数据
        
        Returns:
            dict: 包含所有数据的字典
        """
        self.logger.info('🚀 开始抓取全部数据...')
        results = {}
        tasks = [('stock_daily', lambda: self.fetch_stock_daily(), '股票日线数据'), ('china_cpi', lambda: self.fetch_china_cpi(), '中国CPI数据'), ('china_gdp', lambda: self.fetch_china_gdp(), '中国GDP数据'), ('industry_fund_flow', lambda: self.fetch_industry_fund_flow(), '行业资金流数据'), ('stock_news', lambda: self.fetch_stock_news(), '个股新闻数据'), ('market_summary', lambda: self.fetch_market_summary(), '市场整体概况'), ('market_indices', lambda: self.fetch_market_indices(), '重要指数行情'), ('option_volatility', lambda: self.fetch_option_volatility(), '期权波动率指数'), ('institution_recommendation', lambda: self.fetch_institution_recommendation(), '机构评级数据')]
        for task_name, task_func, description in tasks:
            try:
                self.logger.info(f'\n--- 开始执行: {description} ---')
                result = task_func()
                results[task_name] = result
                if result is not None:
                    filename_mapping = {'stock_daily': 'stock_daily_catl', 'china_cpi': 'china_cpi', 'china_gdp': 'china_gdp_yearly', 'industry_fund_flow': 'industry_fund_flow', 'stock_news': 'stock_news_catl', 'market_summary': 'market_summary_sse', 'market_indices': 'market_indices', 'option_volatility': 'option_volatility_50etf', 'institution_recommendation': 'institution_recommendation_catl'}
                    self.save_data(result, filename_mapping[task_name], description)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f'执行{description}时发生错误: {str(e)}')
                results[task_name] = None
        self.logger.info('🎉 全部数据抓取完成！')
        return results

    def create_data_documentation(self):
        """创建数据文件说明文档"""
        try:
            timestamp = self.get_timestamp()
            doc_content = f'# {self.stock_name}({self.stock_code})数据文件说明\n\n## 📋 文件命名规则\n\n所有数据文件按以下格式命名：\n```\n数据类型_日期_股票代码.csv\n```\n\n例如：`china_cpi_{timestamp}_{self.stock_code}.csv` 表示{timestamp[:4]}年{timestamp[4:6]}月{timestamp[6:8]}日抓取的中国CPI数据，与{self.stock_name}({self.stock_code})相关。\n\n---\n\n## 📊 数据文件详细说明\n\n### 1. 股票日线数据\n**文件名**: `stock_daily_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_a_daily()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘价（元）\n- **high** - 最高价（元）\n- **low** - 最低价（元）\n- **close** - 收盘价（元）\n- **volume** - 成交量（股）\n- **amount** - 成交额（元）\n- **outstanding_share** - 流通股数（股）\n- **turnover** - 换手率\n\n**用途**: 分析{self.stock_name}股价走势、成交情况，进行技术分析\n\n---\n\n### 2. 中国CPI数据\n**文件名**: `china_cpi_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_cpi()\n\n**中文指标说明**:\n- **月份** - 统计月份\n- **全国-当月** - 全国当月CPI指数\n- **全国-同比增长** - 全国CPI同比增长率(%)\n- **全国-环比增长** - 全国CPI环比增长率(%)\n- **全国-累计** - 全国累计CPI指数\n- **城市-当月** - 城市当月CPI指数\n- **城市-同比增长** - 城市CPI同比增长率(%)\n- **城市-环比增长** - 城市CPI环比增长率(%)\n- **城市-累计** - 城市累计CPI指数\n- **农村-当月** - 农村当月CPI指数\n- **农村-同比增长** - 农村CPI同比增长率(%)\n- **农村-环比增长** - 农村CPI环比增长率(%)\n- **农村-累计** - 农村累计CPI指数\n\n**用途**: 反映通胀水平，判断宏观经济环境对{self.stock_name}所在行业的影响\n\n---\n\n### 3. 中国GDP数据\n**文件名**: `china_gdp_yearly_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_gdp_yearly()\n\n**中文指标说明**:\n- **商品** - 数据类型（中国GDP年率报告）\n- **日期** - 发布日期\n- **今值** - 当期GDP增长率(%)\n- **预测值** - 市场预测GDP增长率(%)\n- **前值** - 前期GDP增长率(%)\n\n**用途**: 评估国家经济增长情况，判断宏观经济对{self.stock_name}所在行业需求的影响\n\n---\n\n### 4. 行业资金流数据\n**文件名**: `industry_fund_flow_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_fund_flow_industry()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **行业** - 行业名称\n- **行业指数** - 行业指数代码\n- **行业-涨跌幅** - 行业当日涨跌幅(%)\n- **流入资金** - 资金流入金额（万元）\n- **流出资金** - 资金流出金额（万元）\n- **净额** - 资金净流入金额（万元）\n- **公司家数** - 该行业公司数量\n- **领涨股** - 行业内领涨股票\n- **领涨股-涨跌幅** - 领涨股涨跌幅(%)\n- **当前价** - 领涨股当前价格（元）\n\n**用途**: 分析各行业资金流向，判断{self.stock_name}所在行业的资金关注度\n\n---\n\n### 5. 个股新闻数据\n**文件名**: `stock_news_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_news_em()\n\n**中文指标说明**:\n- **关键词** - 搜索关键词（股票代码）\n- **新闻标题** - 新闻标题\n- **新闻内容** - 新闻摘要/内容\n- **发布时间** - 新闻发布时间\n- **新闻来源** - 新闻来源媒体\n- **新闻链接** - 原文链接地址\n\n**用途**: 获取{self.stock_name}相关新闻资讯，进行舆情分析和基本面研究\n\n---\n\n### 6. 上交所市场概况\n**文件名**: `market_summary_sse_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_sse_summary()\n\n**中文指标说明**:\n- **项目** - 统计项目名称\n- **股票** - 股票相关数据\n- **主板** - 主板市场数据\n- **科创板** - 科创板市场数据\n\n**具体项目包括**:\n- **流通股本** - 流通股总数（亿股）\n- **总市值** - 总市值（亿元）\n- **平均市盈率** - 平均市盈率（倍）\n- **上市公司** - 上市公司数量（家）\n- **上市股票** - 上市股票数量（只）\n- **流通市值** - 流通市值（亿元）\n- **总股本** - 总股本（亿股）\n\n**用途**: 了解整体市场状况，判断市场环境对{self.stock_name}的影响\n\n---\n\n### 7. 重要指数行情\n**文件名**: `market_indices_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_index_spot_em()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **代码** - 指数代码\n- **名称** - 指数名称\n- **最新价** - 最新指数点位\n- **涨跌幅** - 当日涨跌幅(%)\n- **涨跌额** - 当日涨跌点数\n- **成交量** - 成交量（手）\n- **成交额** - 成交金额（万元）\n- **振幅** - 当日振幅(%)\n- **最高** - 当日最高点位\n- **最低** - 当日最低点位\n- **今开** - 今日开盘点位\n- **昨收** - 昨日收盘点位\n- **量比** - 量比\n\n**包含指数**:\n- 上证指数、深证成指、创业板指、科创综指、北证50等\n\n**用途**: 跟踪重要市场指数走势，判断整体市场方向\n\n---\n\n### 8. 50ETF期权波动率指数\n**文件名**: `option_volatility_50etf_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.index_option_50etf_qvix()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘波动率\n- **high** - 最高波动率\n- **low** - 最低波动率\n- **close** - 收盘波动率\n\n**用途**: 反映市场恐慌情绪和波动性预期，是重要的市场情绪指标\n\n---\n\n### 9. 机构评级数据\n**文件名**: `institution_recommendation_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_institute_recommend_detail()\n\n**中文指标说明**:\n- **股票代码** - 股票代码\n- **股票名称** - 股票名称\n- **目标价** - 机构给出的目标价格（元）\n- **最新评级** - 机构最新评级（买入/增持/中性/减持/卖出）\n- **评级机构** - 研究机构名称\n- **分析师** - 分析师姓名\n- **行业** - 所属行业\n- **评级日期** - 评级发布日期\n\n**评级含义**:\n- **买入** - 强烈推荐买入\n- **增持** - 推荐增加持仓\n- **中性** - 维持现有持仓\n- **减持** - 建议减少持仓\n- **卖出** - 建议卖出\n\n**用途**: 了解专业机构对{self.stock_name}的投资建议和价格预期\n\n---\n\n### 10. 数据收集报告\n**文件名**: `collection_report_{timestamp}_{self.stock_code}.csv`\n\n**自动生成的收集统计报告**\n\n**中文指标说明**:\n- **数据类型** - 数据收集任务名称\n- **收集状态** - 收集是否成功（成功/失败）\n- **记录数量** - 成功收集的数据条数\n- **时间戳** - 数据收集完成时间\n\n**用途**: 监控数据收集任务的执行情况，确保数据完整性\n\n---\n\n## 🔍 数据使用建议\n\n### 综合分析框架\n\n1. **宏观经济层面**\n   - 使用CPI、GDP数据判断宏观经济环境\n   - 分析对{self.stock_name}所在行业的影响\n\n2. **市场情绪层面**\n   - 使用期权波动率指数判断市场恐慌程度\n   - 使用重要指数走势判断市场整体方向\n\n3. **行业资金层面**\n   - 使用行业资金流数据判断资金偏好\n   - 关注{self.stock_name}所在行业的资金流向\n\n4. **个股基本面**\n   - 使用机构评级了解专业判断\n   - 使用新闻数据进行舆情分析\n\n5. **技术面分析**\n   - 使用股票日线数据进行技术分析\n   - 结合成交量判断趋势强度\n\n### 数据更新频率\n\n- **日更新**: 股票日线、新闻、指数行情、期权波动率\n- **月更新**: CPI数据\n- **季更新**: GDP数据\n- **实时更新**: 行业资金流、机构评级\n\n---\n\n## ⚠️ 使用注意事项\n\n1. **数据时效性**: 部分数据存在发布延迟，请注意数据的时效性\n2. **数据完整性**: 如遇到数据源问题，某些文件可能缺失，请查看收集报告\n3. **投资风险**: 数据仅供参考，不构成投资建议，投资需谨慎\n4. **版权声明**: 数据来源于公开渠道，请遵守相关使用条款\n\n---\n\n## 📞 技术支持\n\n如有数据解读疑问或技术问题，请参考：\n- akshare官方文档: https://akshare.readthedocs.io/\n- 数据抓取函数库: 本项目中的股票数据抓取函数\n\n**生成时间**: {datetime.datetime.now().strftime('%Y年%m月%d日')}\n**数据版本**: v2.0  \n**适用股票**: {self.stock_name}({self.stock_code})\n'
            doc_filepath = self.output_dir / '数据文件说明.md'
            with open(doc_filepath, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            self.logger.info(f'✅ 数据说明文档已生成: {doc_filepath}')
            return str(doc_filepath)
        except Exception as e:
            self.logger.error(f'❌ 生成数据说明文档失败: {str(e)}')
            return None

def _get_stock_name(self):
    """获取股票名称"""
    try:
        stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
        if not stock_info.empty:
            name_row = stock_info[stock_info['item'] == '股票简称']
            if not name_row.empty:
                return name_row['value'].iloc[0]
        return f'股票{self.stock_code}'
    except:
        return f'股票{self.stock_code}'

class StockDataFetcher:
    """股票数据抓取器 - 核心功能类"""

    def __init__(self, stock_code, auto_create_output_dir=True):
        """
        初始化数据抓取器
        
        Args:
            stock_code (str): 股票代码（如：300750、000001等）
            auto_create_output_dir (bool): 是否自动创建输出目录，默认True
        """
        self.stock_code = stock_code
        self.symbol_sz = f'sz{stock_code}' if stock_code.startswith('0') or stock_code.startswith('3') else f'sh{stock_code}'
        if auto_create_output_dir:
            self.output_dir = Path(f'output_{stock_code}')
        else:
            self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.stock_name = self._get_stock_name()

    def _get_stock_name(self):
        """获取股票名称"""
        try:
            stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
            if not stock_info.empty:
                name_row = stock_info[stock_info['item'] == '股票简称']
                if not name_row.empty:
                    return name_row['value'].iloc[0]
            return f'股票{self.stock_code}'
        except:
            return f'股票{self.stock_code}'

    def get_timestamp(self):
        """获取当前日期用于文件命名"""
        return datetime.datetime.now().strftime('%Y%m%d')

    def save_data(self, data, filename_prefix, description=''):
        """
        保存数据到CSV文件
        
        Args:
            data: 要保存的数据（pandas DataFrame）
            filename_prefix (str): 文件名前缀
            description (str): 数据描述
            
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            timestamp = self.get_timestamp()
            filename = f'{filename_prefix}_{timestamp}_{self.stock_code}.csv'
            filepath = self.output_dir / filename
            if isinstance(data, pd.DataFrame):
                data.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath} (共{len(data)}条记录)')
            else:
                df = pd.DataFrame([data] if isinstance(data, dict) else data)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                self.logger.info(f'✅ {description} 已保存: {filepath}')
            return str(filepath)
        except Exception as e:
            self.logger.error(f'❌ 保存{description}失败: {str(e)}')
            return None

    def fetch_stock_daily(self, days=30):
        """
        抓取股票日线数据
        
        Args:
            days (int): 抓取最近多少天的数据，默认30天
            
        Returns:
            pandas.DataFrame: 股票日线数据
        """
        try:
            self.logger.info(f'📈 开始抓取{self.stock_code}日线数据...')
            stock_df = ak.stock_zh_a_daily(symbol=self.symbol_sz).reset_index()
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
            recent_data = stock_df[stock_df['date'] >= days_ago]
            self.save_data(recent_data, 'stock_daily_catl', f'{self.stock_code}日线数据')
            return recent_data
        except Exception as e:
            self.logger.error(f'❌ 抓取股票日线数据失败: {str(e)}')
            return None

    def fetch_china_cpi(self):
        """
        抓取中国CPI数据 (限制为过去2年)
        
        Returns:
            pandas.DataFrame: 中国CPI数据
        """
        try:
            self.logger.info('📊 开始抓取中国CPI数据...')
            cpi_df = ak.macro_china_cpi()
            if not cpi_df.empty:
                if '月份' in cpi_df.columns:

                    def convert_chinese_date(date_str):
                        try:
                            if '年' in date_str and '月' in date_str:
                                year = date_str.split('年')[0]
                                month = date_str.split('年')[1].split('月')[0]
                                return f'{year}-{month.zfill(2)}-01'
                            else:
                                return date_str
                        except:
                            return None
                    cpi_df['月份'] = cpi_df['月份'].apply(convert_chinese_date)
                    cpi_df['月份'] = pd.to_datetime(cpi_df['月份'], errors='coerce')
                    cpi_df = cpi_df.dropna(subset=['月份'])
                    if not cpi_df.empty:
                        two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2 * 365)
                        cpi_df = cpi_df[cpi_df['月份'] >= two_years_ago]
                        self.logger.info(f'✅ CPI数据已限制为过去2年: {len(cpi_df)} 条记录')
            return cpi_df
        except Exception as e:
            self.logger.error(f'❌ 抓取CPI数据失败: {str(e)}')
            return None

    def fetch_china_gdp(self):
        """
        抓取中国GDP数据
        
        Returns:
            pandas.DataFrame: 中国GDP数据
        """
        try:
            self.logger.info('📊 开始抓取中国GDP数据...')
            gdp_df = ak.macro_china_gdp_yearly()
            return gdp_df
        except Exception as e:
            self.logger.error(f'❌ 抓取GDP数据失败: {str(e)}')
            return None

    def fetch_industry_fund_flow(self):
        """
        抓取行业资金流数据
        
        Returns:
            pandas.DataFrame: 行业资金流数据
        """
        try:
            self.logger.info('💰 开始抓取行业资金流数据...')
            industry_fund_df = ak.stock_fund_flow_industry()
            return industry_fund_df
        except Exception as e:
            self.logger.error(f'❌ 抓取行业资金流数据失败: {str(e)}')
            return None

    def fetch_stock_news(self):
        """
        抓取个股新闻数据
        
        Returns:
            pandas.DataFrame: 个股新闻数据
        """
        try:
            self.logger.info(f'📰 开始抓取{self.stock_name}({self.stock_code})新闻数据...')
            news_df = ak.stock_news_em(symbol=self.stock_code)
            return news_df
        except Exception as e:
            self.logger.error(f'❌ 抓取新闻数据失败: {str(e)}')
            return None

    def fetch_market_summary(self):
        """
        抓取上交所市场概况
        
        Returns:
            pandas.DataFrame: 市场概况数据
        """
        try:
            self.logger.info('🏛️ 开始抓取上交所市场概况...')
            sse_summary = ak.stock_sse_summary()
            return sse_summary
        except Exception as e:
            self.logger.error(f'❌ 抓取市场概况失败: {str(e)}')
            return None

    def fetch_market_indices(self):
        """
        抓取重要指数行情
        
        Returns:
            pandas.DataFrame: 重要指数数据
        """
        try:
            self.logger.info('📊 开始抓取重要指数行情...')
            market_indices = ak.stock_zh_index_spot_em(symbol='沪深重要指数')
            return market_indices
        except Exception as e:
            self.logger.error(f'❌ 抓取市场指数失败: {str(e)}')
            return None

    def fetch_option_volatility(self):
        """
        抓取50ETF期权波动率指数 (限制为过去1个月)
        
        Returns:
            pandas.DataFrame: 期权波动率数据
        """
        try:
            self.logger.info('📈 开始抓取50ETF波动率指数...')
            vol50 = ak.index_option_50etf_qvix()
            if not vol50.empty:
                if 'date' in vol50.columns:
                    vol50['date'] = pd.to_datetime(vol50['date'])
                    one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                    vol50 = vol50[vol50['date'] >= one_month_ago]
                    self.logger.info(f'✅ 期权波动率数据已限制为过去1个月: {len(vol50)} 条记录')
            return vol50
        except Exception as e:
            self.logger.error(f'❌ 抓取期权波动率数据失败: {str(e)}')
            return None

    def fetch_institution_recommendation(self):
        """
        抓取机构评级数据 (限制为过去半年)
        
        Returns:
            pandas.DataFrame: 机构评级数据
        """
        try:
            self.logger.info(f'🏦 开始抓取{self.stock_name}({self.stock_code})机构评级...')
            inst_rec = ak.stock_institute_recommend_detail(symbol=self.stock_code)
            if not inst_rec.empty:
                date_columns = ['评级日期', 'date', '日期']
                date_col = None
                for col in date_columns:
                    if col in inst_rec.columns:
                        date_col = col
                        break
                if date_col:
                    inst_rec[date_col] = pd.to_datetime(inst_rec[date_col])
                    six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
                    inst_rec = inst_rec[inst_rec[date_col] >= six_months_ago]
                    self.logger.info(f'✅ 机构评级数据已限制为过去半年: {len(inst_rec)} 条记录')
            return inst_rec
        except Exception as e:
            self.logger.error(f'❌ 抓取机构评级数据失败: {str(e)}')
            return None

    def fetch_all_data(self):
        """
        抓取所有类型的数据
        
        Returns:
            dict: 包含所有数据的字典
        """
        self.logger.info('🚀 开始抓取全部数据...')
        results = {}
        tasks = [('stock_daily', lambda: self.fetch_stock_daily(), '股票日线数据'), ('china_cpi', lambda: self.fetch_china_cpi(), '中国CPI数据'), ('china_gdp', lambda: self.fetch_china_gdp(), '中国GDP数据'), ('industry_fund_flow', lambda: self.fetch_industry_fund_flow(), '行业资金流数据'), ('stock_news', lambda: self.fetch_stock_news(), '个股新闻数据'), ('market_summary', lambda: self.fetch_market_summary(), '市场整体概况'), ('market_indices', lambda: self.fetch_market_indices(), '重要指数行情'), ('option_volatility', lambda: self.fetch_option_volatility(), '期权波动率指数'), ('institution_recommendation', lambda: self.fetch_institution_recommendation(), '机构评级数据')]
        for task_name, task_func, description in tasks:
            try:
                self.logger.info(f'\n--- 开始执行: {description} ---')
                result = task_func()
                results[task_name] = result
                if result is not None:
                    filename_mapping = {'stock_daily': 'stock_daily_catl', 'china_cpi': 'china_cpi', 'china_gdp': 'china_gdp_yearly', 'industry_fund_flow': 'industry_fund_flow', 'stock_news': 'stock_news_catl', 'market_summary': 'market_summary_sse', 'market_indices': 'market_indices', 'option_volatility': 'option_volatility_50etf', 'institution_recommendation': 'institution_recommendation_catl'}
                    self.save_data(result, filename_mapping[task_name], description)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f'执行{description}时发生错误: {str(e)}')
                results[task_name] = None
        self.logger.info('🎉 全部数据抓取完成！')
        return results

    def create_data_documentation(self):
        """创建数据文件说明文档"""
        try:
            timestamp = self.get_timestamp()
            doc_content = f'# {self.stock_name}({self.stock_code})数据文件说明\n\n## 📋 文件命名规则\n\n所有数据文件按以下格式命名：\n```\n数据类型_日期_股票代码.csv\n```\n\n例如：`china_cpi_{timestamp}_{self.stock_code}.csv` 表示{timestamp[:4]}年{timestamp[4:6]}月{timestamp[6:8]}日抓取的中国CPI数据，与{self.stock_name}({self.stock_code})相关。\n\n---\n\n## 📊 数据文件详细说明\n\n### 1. 股票日线数据\n**文件名**: `stock_daily_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_a_daily()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘价（元）\n- **high** - 最高价（元）\n- **low** - 最低价（元）\n- **close** - 收盘价（元）\n- **volume** - 成交量（股）\n- **amount** - 成交额（元）\n- **outstanding_share** - 流通股数（股）\n- **turnover** - 换手率\n\n**用途**: 分析{self.stock_name}股价走势、成交情况，进行技术分析\n\n---\n\n### 2. 中国CPI数据\n**文件名**: `china_cpi_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_cpi()\n\n**中文指标说明**:\n- **月份** - 统计月份\n- **全国-当月** - 全国当月CPI指数\n- **全国-同比增长** - 全国CPI同比增长率(%)\n- **全国-环比增长** - 全国CPI环比增长率(%)\n- **全国-累计** - 全国累计CPI指数\n- **城市-当月** - 城市当月CPI指数\n- **城市-同比增长** - 城市CPI同比增长率(%)\n- **城市-环比增长** - 城市CPI环比增长率(%)\n- **城市-累计** - 城市累计CPI指数\n- **农村-当月** - 农村当月CPI指数\n- **农村-同比增长** - 农村CPI同比增长率(%)\n- **农村-环比增长** - 农村CPI环比增长率(%)\n- **农村-累计** - 农村累计CPI指数\n\n**用途**: 反映通胀水平，判断宏观经济环境对{self.stock_name}所在行业的影响\n\n---\n\n### 3. 中国GDP数据\n**文件名**: `china_gdp_yearly_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.macro_china_gdp_yearly()\n\n**中文指标说明**:\n- **商品** - 数据类型（中国GDP年率报告）\n- **日期** - 发布日期\n- **今值** - 当期GDP增长率(%)\n- **预测值** - 市场预测GDP增长率(%)\n- **前值** - 前期GDP增长率(%)\n\n**用途**: 评估国家经济增长情况，判断宏观经济对{self.stock_name}所在行业需求的影响\n\n---\n\n### 4. 行业资金流数据\n**文件名**: `industry_fund_flow_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_fund_flow_industry()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **行业** - 行业名称\n- **行业指数** - 行业指数代码\n- **行业-涨跌幅** - 行业当日涨跌幅(%)\n- **流入资金** - 资金流入金额（万元）\n- **流出资金** - 资金流出金额（万元）\n- **净额** - 资金净流入金额（万元）\n- **公司家数** - 该行业公司数量\n- **领涨股** - 行业内领涨股票\n- **领涨股-涨跌幅** - 领涨股涨跌幅(%)\n- **当前价** - 领涨股当前价格（元）\n\n**用途**: 分析各行业资金流向，判断{self.stock_name}所在行业的资金关注度\n\n---\n\n### 5. 个股新闻数据\n**文件名**: `stock_news_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_news_em()\n\n**中文指标说明**:\n- **关键词** - 搜索关键词（股票代码）\n- **新闻标题** - 新闻标题\n- **新闻内容** - 新闻摘要/内容\n- **发布时间** - 新闻发布时间\n- **新闻来源** - 新闻来源媒体\n- **新闻链接** - 原文链接地址\n\n**用途**: 获取{self.stock_name}相关新闻资讯，进行舆情分析和基本面研究\n\n---\n\n### 6. 上交所市场概况\n**文件名**: `market_summary_sse_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_sse_summary()\n\n**中文指标说明**:\n- **项目** - 统计项目名称\n- **股票** - 股票相关数据\n- **主板** - 主板市场数据\n- **科创板** - 科创板市场数据\n\n**具体项目包括**:\n- **流通股本** - 流通股总数（亿股）\n- **总市值** - 总市值（亿元）\n- **平均市盈率** - 平均市盈率（倍）\n- **上市公司** - 上市公司数量（家）\n- **上市股票** - 上市股票数量（只）\n- **流通市值** - 流通市值（亿元）\n- **总股本** - 总股本（亿股）\n\n**用途**: 了解整体市场状况，判断市场环境对{self.stock_name}的影响\n\n---\n\n### 7. 重要指数行情\n**文件名**: `market_indices_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_zh_index_spot_em()\n\n**中文指标说明**:\n- **序号** - 排序编号\n- **代码** - 指数代码\n- **名称** - 指数名称\n- **最新价** - 最新指数点位\n- **涨跌幅** - 当日涨跌幅(%)\n- **涨跌额** - 当日涨跌点数\n- **成交量** - 成交量（手）\n- **成交额** - 成交金额（万元）\n- **振幅** - 当日振幅(%)\n- **最高** - 当日最高点位\n- **最低** - 当日最低点位\n- **今开** - 今日开盘点位\n- **昨收** - 昨日收盘点位\n- **量比** - 量比\n\n**包含指数**:\n- 上证指数、深证成指、创业板指、科创综指、北证50等\n\n**用途**: 跟踪重要市场指数走势，判断整体市场方向\n\n---\n\n### 8. 50ETF期权波动率指数\n**文件名**: `option_volatility_50etf_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.index_option_50etf_qvix()\n\n**中文指标说明**:\n- **date** - 交易日期\n- **open** - 开盘波动率\n- **high** - 最高波动率\n- **low** - 最低波动率\n- **close** - 收盘波动率\n\n**用途**: 反映市场恐慌情绪和波动性预期，是重要的市场情绪指标\n\n---\n\n### 9. 机构评级数据\n**文件名**: `institution_recommendation_catl_{timestamp}_{self.stock_code}.csv`\n\n**数据来源**: akshare.stock_institute_recommend_detail()\n\n**中文指标说明**:\n- **股票代码** - 股票代码\n- **股票名称** - 股票名称\n- **目标价** - 机构给出的目标价格（元）\n- **最新评级** - 机构最新评级（买入/增持/中性/减持/卖出）\n- **评级机构** - 研究机构名称\n- **分析师** - 分析师姓名\n- **行业** - 所属行业\n- **评级日期** - 评级发布日期\n\n**评级含义**:\n- **买入** - 强烈推荐买入\n- **增持** - 推荐增加持仓\n- **中性** - 维持现有持仓\n- **减持** - 建议减少持仓\n- **卖出** - 建议卖出\n\n**用途**: 了解专业机构对{self.stock_name}的投资建议和价格预期\n\n---\n\n### 10. 数据收集报告\n**文件名**: `collection_report_{timestamp}_{self.stock_code}.csv`\n\n**自动生成的收集统计报告**\n\n**中文指标说明**:\n- **数据类型** - 数据收集任务名称\n- **收集状态** - 收集是否成功（成功/失败）\n- **记录数量** - 成功收集的数据条数\n- **时间戳** - 数据收集完成时间\n\n**用途**: 监控数据收集任务的执行情况，确保数据完整性\n\n---\n\n## 🔍 数据使用建议\n\n### 综合分析框架\n\n1. **宏观经济层面**\n   - 使用CPI、GDP数据判断宏观经济环境\n   - 分析对{self.stock_name}所在行业的影响\n\n2. **市场情绪层面**\n   - 使用期权波动率指数判断市场恐慌程度\n   - 使用重要指数走势判断市场整体方向\n\n3. **行业资金层面**\n   - 使用行业资金流数据判断资金偏好\n   - 关注{self.stock_name}所在行业的资金流向\n\n4. **个股基本面**\n   - 使用机构评级了解专业判断\n   - 使用新闻数据进行舆情分析\n\n5. **技术面分析**\n   - 使用股票日线数据进行技术分析\n   - 结合成交量判断趋势强度\n\n### 数据更新频率\n\n- **日更新**: 股票日线、新闻、指数行情、期权波动率\n- **月更新**: CPI数据\n- **季更新**: GDP数据\n- **实时更新**: 行业资金流、机构评级\n\n---\n\n## ⚠️ 使用注意事项\n\n1. **数据时效性**: 部分数据存在发布延迟，请注意数据的时效性\n2. **数据完整性**: 如遇到数据源问题，某些文件可能缺失，请查看收集报告\n3. **投资风险**: 数据仅供参考，不构成投资建议，投资需谨慎\n4. **版权声明**: 数据来源于公开渠道，请遵守相关使用条款\n\n---\n\n## 📞 技术支持\n\n如有数据解读疑问或技术问题，请参考：\n- akshare官方文档: https://akshare.readthedocs.io/\n- 数据抓取函数库: 本项目中的股票数据抓取函数\n\n**生成时间**: {datetime.datetime.now().strftime('%Y年%m月%d日')}\n**数据版本**: v2.0  \n**适用股票**: {self.stock_name}({self.stock_code})\n'
            doc_filepath = self.output_dir / '数据文件说明.md'
            with open(doc_filepath, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            self.logger.info(f'✅ 数据说明文档已生成: {doc_filepath}')
            return str(doc_filepath)
        except Exception as e:
            self.logger.error(f'❌ 生成数据说明文档失败: {str(e)}')
            return None

def _get_stock_name(self):
    """获取股票名称"""
    try:
        stock_info = ak.stock_individual_info_em(symbol=self.stock_code)
        if not stock_info.empty:
            name_row = stock_info[stock_info['item'] == '股票简称']
            if not name_row.empty:
                return name_row['value'].iloc[0]
        return f'股票{self.stock_code}'
    except:
        return f'股票{self.stock_code}'

