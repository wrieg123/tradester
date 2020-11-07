from tradester.feeds.static import SecuritiesTS

from tqdm import tqdm

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import calendar



class Metrics():
    
    def __init__(
            self, 
            portfolio, 
            trade_start_date, 
            start_date, 
            end_date, 
            management_fee, 
            performance_fee, 
            index = 'SPY'
            ):
        self.portfolio = portfolio
        self.trade_start_date = trade_start_date
        self.start_date = start_date
        self.end_date = end_date
        self.management_fee = management_fee
        self.performance_fee = performance_fee
        self.index_series = SecuritiesTS(index, fields='close', start_date = start_date, end_date = end_date).data
        self.holdings = None
        self.values = None
        self.statistics = None
        self.trading_log = None
        self.monthly_returns = None
        self.yearly_returns = None
    
    def _calculate(self):
        self.holdings = self.portfolio.holdings_df
        self.values = self.portfolio.values_df.set_index('date')
        self.trading_log = self.portfolio.trading_log_df

        if not self.trade_start_date is None:
            self.holdings = self.holdings.loc[self.holdings.date >= self.trade_start_date]
            self.values = self.values.loc[self.values.index >= self.trade_start_date]
            self.trading_log = self.trading_log.loc[self.trading_log.date >= self.trade_start_date]
            self.index_series = self.index_series.loc[self.index_series.index >= pd.to_datetime(self.trade_start_date)]
        self.index_series['%'] = self.index_series['close'].pct_change().fillna(method='ffill')
        self.values['index_returns'] = (1+self.index_series['%']).cumprod()
        self.values['index_returns'] = self.values['index_returns'].fillna(method='ffill').fillna(1)

        self.values['expanding_max'] = self.values['value'].expanding().max()
        self.values['dd'] = (self.values['value'] / self.values['expanding_max'] - 1).apply(lambda x: 0 if x > 0 else x)
        self.values['lmv%'] = self.values['long_equity'] / self.values['value']
        self.values['smv%'] = self.values['short_equity'] / self.values['value']
        self.values['nmv%'] = self.values['lmv%'] + self.values['smv%'] 
        self.values['gmv%'] = self.values['lmv%'] - self.values['smv%'] 
        self.values['cash%'] = self.values['cash']/self.values['value'] - 1
        self.values['%'] = self.values['value'].pct_change().fillna(0)
        self.values['cumulative'] = (1+self.values['%']).cumprod().fillna(1)
        self.values['date'] = self.values.index
        self.values['date'] = self.values['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        self.values['year-month'] = self.values['date'].apply(lambda x: pd.to_datetime(f'{x.split("-")[0]}' +'-'+ f'{x.split("-")[1]}'+'-01'))
        self.values['year'] = self.values['date'].apply(lambda x: pd.to_datetime(f'{x.split("-")[0]}'+'-01-01'))

        self.monthly_returns, self.yearly_returns = self.__group_returns()


        stats = {
            'portfolio': {},
            'portfolio_net': {},
            'index' : {},
        }

        stats['portfolio']['Cumulative Return'] = (1+self.values['%']).prod() - 1
        stats['portfolio']['Annualized Return'] = (1+stats['portfolio']['Cumulative Return']) ** (252/len(self.values.index)) - 1
        stats['portfolio']['Annualized Volatility'] = self.values['%'].std() * np.sqrt(252)
        stats['portfolio']['Sharpe Ratio'] = stats['portfolio']['Annualized Return'] / stats['portfolio']['Annualized Volatility']
        stats['portfolio']['Sortino Ratio'] = stats['portfolio']['Annualized Return'] / (self.values.loc[self.values['%'] < 0, '%'].std() * np.sqrt(252))
        stats['portfolio']['Max Drawdown'] = self.values['dd'].min()
        stats['portfolio']['Calmar Ratio'] = stats['portfolio']['Annualized Return'] / abs(stats['portfolio']['Max Drawdown'])
        stats['portfolio']['Win Rate'] = self.values['%'].map(lambda x: 1 if x > 0 else 0).sum() / len(self.values.index)
        stats['portfolio']['Loss Rate'] = self.values['%'].map(lambda x: 1 if x < 0 else 0).sum() / len(self.values.index)
        stats['portfolio']['Pass Rate'] = self.values['%'].map(lambda x: 1 if x == 0 else 0).sum() / len(self.values.index)
        stats['portfolio']['Win Rate Mean'] = self.values['%'].map(lambda x: x if x > 0 else 0).mean() 
        stats['portfolio']['Loss Rate Mean'] = self.values['%'].map(lambda x: x if x < 0 else 0).mean() 
        stats['portfolio']['Win Rate Std'] = self.values['%'].map(lambda x: x if x > 0 else 0).std() 
        stats['portfolio']['Loss Rate Std'] = self.values['%'].map(lambda x: x if x < 0 else 0).std() 
        


        if not self.trading_log is None and not self.trading_log.empty:
            stats['portfolio']['Trade num'] = len(self.trading_log.index)
            stats['portfolio']['Trade Win Rate'] = self.trading_log['pnl%'].map(lambda x: 1 if x > 0 else 0).sum() / len(self.trading_log.index)
            stats['portfolio']['Trade Loss Rate'] = self.trading_log['pnl%'].map(lambda x: 1 if x < 0 else 0).sum() / len(self.trading_log.index)
            stats['portfolio']['Trade Pass Rate'] = self.trading_log['pnl%'].map(lambda x: 1 if x == 0 else 0).sum() / len(self.trading_log.index)
            stats['portfolio']['Trade Win Avg'] = self.trading_log['pnl%'].loc[self.trading_log['pnl%'] > 0].mean() 
            stats['portfolio']['Trade Win Std'] = self.trading_log['pnl%'].loc[self.trading_log['pnl%'] > 0].std() 
            stats['portfolio']['Trade Loss Avg'] = self.trading_log['pnl%'].loc[self.trading_log['pnl%'] < 0].mean() 
            stats['portfolio']['Trade Loss Std'] = self.trading_log['pnl%'].loc[self.trading_log['pnl%'] < 0].std() 
            stats['portfolio']['IR'] = stats['portfolio']['Trade Win Rate'] * np.sqrt(stats['portfolio']['Trade num'])
        else:
            stats['portfolio']['Trade num'] = 0
            stats['portfolio']['Trade Win Rate'] = 0
            stats['portfolio']['Trade Loss Rate'] = 0
            stats['portfolio']['Trade Pass Rate'] = 0
            stats['portfolio']['Trade Win Avg'] = 0
            stats['portfolio']['Trade Win Std'] = 0
            stats['portfolio']['Trade Loss Avg'] = 0
            stats['portfolio']['Trade Loss Std'] = 0
            stats['portfolio']['IR'] = 0

        self.statistics = stats
   

    def __group_returns(self):

        grouped_m_returns = self.values[['%', 'year-month']].groupby('year-month').apply(lambda x: (1+x).prod() -1)
        grouped_m_returns['month_num'] = grouped_m_returns.index.month
        grouped_m_returns['year'] = grouped_m_returns.index.year
        grouped_m_returns = grouped_m_returns.pivot_table(index = 'year', columns = 'month_num', values= '%')
        grouped_m_returns.columns = [calendar.month_name[x] for x in grouped_m_returns.columns]
        grouped_m_returns.index.name = 'Year'
        grouped_y_returns = self.values[['%', 'year']].groupby('year').apply(lambda x: (1+x).prod() - 1)
        grouped_y_returns_vol = self.values[['%', 'year']].groupby('year').apply(lambda x: x.std() * np.sqrt(252))
        grouped_y_returns['volatility'] = grouped_y_returns_vol['%']
        grouped_y_returns['sharpe'] = grouped_y_returns['%'] / grouped_y_returns['volatility']
        grouped_y_returns.index = grouped_y_returns.index.year
        grouped_y_returns.columns = ['Return', 'Volatility', 'Sharpe']
        grouped_y_returns.index.name = 'Year' 

        return grouped_m_returns, grouped_y_returns


    def _print(self):
        print()
        print(f'----- Portfolio Statistics -----')
        print(f"Cumulative Return: {self.statistics['portfolio']['Cumulative Return']*100:.2f}%")
        print(f"Annualized Return: {self.statistics['portfolio']['Annualized Return']*100:.2f}%")
        print(f"Annualized Volatility: {self.statistics['portfolio']['Annualized Volatility']*100:.2f}%")
        print(f"Sharpe Ratio: {self.statistics['portfolio']['Sharpe Ratio']:.2f}")
        print(f"Sortino Ratio: {self.statistics['portfolio']['Sortino Ratio']:.2f}")
        print(f"Max Drawdown: {self.statistics['portfolio']['Max Drawdown']*100:.2f}%")
        print(f"Calmar Ratio: {self.statistics['portfolio']['Calmar Ratio']:.2f}")
        print()
        print('----- Trades -----')
        print(f"Win Rate: {self.statistics['portfolio']['Trade Win Rate']*100:.1f}% (avg: {self.statistics['portfolio']['Trade Win Avg']*100:.1f}%, std: {self.statistics['portfolio']['Trade Win Std']*100:.1f}%)")
        print(f"Loss Rate: {self.statistics['portfolio']['Trade Loss Rate']*100:.1f}% (avg: {self.statistics['portfolio']['Trade Loss Avg']*100:.1f}%, std: {self.statistics['portfolio']['Trade Loss Std']*100:.1f}%)")
        print(f"Pass Rate: {self.statistics['portfolio']['Trade Pass Rate']*100:.1f}%")
        print(f"Number of Trades: {self.statistics['portfolio']['Trade num']:,}")
        print(f"Information Ratio: {self.statistics['portfolio']['IR']:.2f}")
        print() 
        print('----- Daily Returns -----')
        print(f"Win Rate: {self.statistics['portfolio']['Win Rate']*100:.1f}% (avg: {self.statistics['portfolio']['Win Rate Mean']*100:.1f}%, {self.statistics['portfolio']['Win Rate Std']*100:.1f}%)")
        print(f"Loss Rate: {self.statistics['portfolio']['Loss Rate']*100:.1f}% (avg: {self.statistics['portfolio']['Loss Rate Mean']*100:.1f}%, {self.statistics['portfolio']['Loss Rate Std']*100:.1f}%)")
        print(f"Pass Rate: {self.statistics['portfolio']['Pass Rate']*100:.1f}%")
        print()
        print('----- Monthly Returns -----')
        print(self.monthly_returns.applymap(lambda x: '' if np.isnan(x) else f'{round(x*100,1)}%'))
        printable_y = self.yearly_returns[['Return', 'Volatility']]
        printable_y = printable_y.applymap(lambda x: '' if np.isnan(x) else f'{round(x*100,1)}%')
        printable_y['Sharpe'] = self.yearly_returns['Sharpe'].apply(lambda x: '' if np.isnan(x) else f'{round(x,2)}')
        print()
        print('----- Yearly Returns ------')
        print(printable_y)


    def plot(self, index = True):
        #fig , axs = plt.subplots((2, 2))
        #axs[0, 0].set_title('Cumulative Return (%) against Maximum Drawdown (%)')
        #axs[1].set_title('Distribution of Trade Returns (%)')
        #axs[1].set_xlim(xmin= -0.015, xmax=0.015)
        #axs[2].set_title('Portfolio Positioning')
        self.values['cumulative'].plot(color = 'blue', secondary_y = True)
        #self.values['returns_net_cum'].plot(color = 'navy', secondary_y = True)
        if index:
            self.values['index_returns'].plot(color = 'grey',secondary_y = True) 
        self.values['dd'].plot.area(stacked=False, color = 'red', alpha = 0.5)
        #self.trading_log.loc[self.trading_log['pnl%'] > 0, 'pnl%'].hist(ax = axs[1], color = 'green', bins = 100)
        #self.trading_log.loc[self.trading_log['pnl%'] < 0, 'pnl%'].hist(ax = axs[1], color = 'red', bins = 100)
        ##self.values.loc[self.values['%'] > 0, '%'].hist(ax = axs[1], color = 'green', bins = 50)
        ##self.values.loc[self.values['%'] < 0, '%'].hist(ax = axs[1], color = 'red', bins = 50)
        #self.values['lmv%'].plot(color = 'green', ax = axs[2])
        #self.values['smv%'].plot(color = 'red', ax = axs[2])
        #self.values['gmv%'].plot(color = 'black', ax = axs[2])
        #self.values['nmv%'].plot.area(stacked=False, color = 'blue', alpha = .75, ax = axs[2])
        #axs[2].legend()
        plt.legend()
        plt.show() 
