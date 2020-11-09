from tradester.feeds.static import SecuritiesTS

from matplotlib.gridspec import GridSpec
from tqdm import tqdm

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import calendar



class Metrics():
    
    def __init__(
            self, 
            portfolio, 
            oms,
            trade_start_date, 
            start_date, 
            end_date, 
            ):
        self.portfolio = portfolio
        self.oms = oms
        self.trade_start_date = trade_start_date
        self.start_date = start_date
        self.end_date = end_date
        self.holdings = None
        self.values = None
        self.trading_log = None

        self.statistics = None
        self.monthly_returns_pct = None
        self.monthly_returns_usd = None
        self.yearly_returns = None
    

    def _calculate(self):
        self.holdings = self.portfolio.holdings_df
        self.values = self.portfolio.values_df.set_index('date').sort_index()
        self.trading_log = self.portfolio.trading_log_df

        if not self.trade_start_date is None:
            self.holdings = self.holdings.loc[self.holdings.date >= pd.to_datetime(self.trade_start_date)]
            self.values = self.values.loc[self.values.index >= pd.to_datetime(self.trade_start_date)]
            self.trading_log = self.trading_log.loc[self.trading_log.date >= pd.to_datetime(self.trade_start_date)]

        self.values['expanding_max'] = self.values['value'].expanding().max()
        self.values['dd_%'] = (self.values['value'] / self.values['expanding_max'] - 1).apply(lambda x: 0 if x > 0 else x)
        self.values['dd_$'] = (self.values['value'] - self.values['expanding_max']).apply(lambda x: 0 if x > 0 else x)
        self.values['lmv%'] = self.values['long_equity'] / self.values['value']
        self.values['smv%'] = self.values['short_equity'] / self.values['value']
        self.values['nmv%'] = self.values['lmv%'] + self.values['smv%'] 
        self.values['gmv%'] = self.values['lmv%'] - self.values['smv%'] 
        self.values['cash%'] = self.values['cash']/self.values['value'] - 1
        self.values['%'] = self.values['value'].pct_change().fillna(0)
        self.values['$'] = self.values['value'].diff().fillna(0)
        self.values['cumulative'] = (1+self.values['%']).cumprod().fillna(1)
        self.values['date'] = self.values.index
        self.values['date'] = self.values['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        self.values['year-month'] = self.values['date'].apply(lambda x: pd.to_datetime(f'{x.split("-")[0]}' +'-'+ f'{x.split("-")[1]}'+'-01'))
        self.values['year'] = self.values['date'].apply(lambda x: pd.to_datetime(f'{x.split("-")[0]}'+'-01-01'))

        self.monthly_returns_pct, self.monthly_returns_usd, self.yearly_returns = self.__group_returns()

        stats = {}
        
        stats['Cumulative Return (%)'] = (1+self.values['%']).prod() - 1
        stats['Cumulative Return ($)'] = self.values['value'].tail(1).values[0] - self.values['value'].head(1).values[0]
        stats['Annualized Return (%)'] = (1+stats['Cumulative Return (%)']) ** (252/len(self.values.index)) - 1 
        stats['Annualized Volatility (%)'] = self.values['%'].std() * np.sqrt(252)
        stats['Sharpe Ratio'] = stats['Annualized Return (%)'] / stats['Annualized Volatility (%)']
        stats['Sortino Ratio'] = stats['Annualized Return (%)'] / (self.values.loc[self.values['%'] < 0, '%'].std() * np.sqrt(252))
        stats['Max Drawdown (%)'] = self.values['dd_%'].min()
        stats['Max Drawdown ($)'] = self.values['dd_$'].min()
        stats['Calmar Ratio'] = stats['Annualized Return (%)'] / abs(stats['Max Drawdown (%)'])
        
        if not self.trading_log is None and not self.trading_log.empty:
            stats['Trade num'] = len(self.trading_log.index)
            stats['Trade Win Rate'] = self.trading_log['%c'].map(lambda x: 1 if x > 0 else 0).sum() / stats['Trade num']
            stats['Trade Loss Rate'] = self.trading_log['%c'].map(lambda x: 1 if x < 0 else 0).sum() / stats['Trade num']
            stats['Trade Pass Rate'] = self.trading_log['%c'].map(lambda x: 1 if x == 0 else 0).sum() / stats['Trade num']
            stats['Trade Win Avg (%c)'] = self.trading_log.loc[self.trading_log['%c'] > 0]['%c'].mean()
            stats['Trade Win Std (%c)'] = self.trading_log.loc[self.trading_log['%c'] > 0]['%c'].std()
            stats['Trade Loss Avg (%c)'] = self.trading_log.loc[self.trading_log['%c'] < 0]['%c'].mean()
            stats['Trade Loss Std (%c)'] = self.trading_log.loc[self.trading_log['%c'] < 0]['%c'].std()
            stats['Trade Win Expected'] = stats['Trade Win Rate'] * stats['Trade Win Avg (%c)']
            stats['Trade Loss Expected'] = stats['Trade Loss Rate'] * stats['Trade Loss Avg (%c)']
        else:
            stats['Trade num'] = 0
            stats['Trade Win Rate'] = 0
            stats['Trade Loss Rate'] = 0
            stats['Trade Pass Rate'] = 0
            stats['Trade Win Avg (%c)'] = 0
            stats['Trade Win Std (%c)'] = 0
            stats['Trade Loss Avg (%c)'] = 0
            stats['Trade Loss Std (%c)'] = 0
            stats['Trade Win Expected'] = stats['Trade Win Rate'] * stats['Trade Win Avg (%c)']
            stats['Trade Loss Expected'] = stats['Trade Loss Rate'] * stats['Trade Loss Avg (%c)']

        self.statistics = stats
   

    def __group_returns(self):

        grouped_m_returns_pct = self.values[['%', 'year-month']].groupby('year-month').apply(lambda x: (1+x).prod() -1)
        grouped_m_returns_pct['month_num'] = grouped_m_returns_pct.index.month
        grouped_m_returns_pct['year'] = grouped_m_returns_pct.index.year
        grouped_m_returns_pct = grouped_m_returns_pct.pivot_table(index = 'year', columns = 'month_num', values= '%')
        grouped_m_returns_pct.columns = [calendar.month_name[x] for x in grouped_m_returns_pct.columns]
        grouped_m_returns_pct.index.name = 'Year'
        grouped_m_returns_usd = self.values[['$', 'year-month']].groupby('year-month').apply(lambda x: x.sum())
        grouped_m_returns_usd['month_num'] = grouped_m_returns_usd.index.month
        grouped_m_returns_usd['year'] = grouped_m_returns_usd.index.year
        grouped_m_returns_usd = grouped_m_returns_usd.pivot_table(index = 'year', columns = 'month_num', values= '$')
        grouped_m_returns_usd.columns = [calendar.month_name[x] for x in grouped_m_returns_usd.columns]
        grouped_m_returns_usd.index.name = 'Year'

        grouped_y_returns = self.values[['%', 'year']].groupby('year').apply(lambda x: (1+x).prod() - 1)
        grouped_y_returns_vol = self.values[['%', 'year']].groupby('year').apply(lambda x: x.std() * np.sqrt(252))
        grouped_y_returns['volatility'] = grouped_y_returns_vol['%']
        grouped_y_returns['sharpe'] = grouped_y_returns['%'] / grouped_y_returns['volatility']
        grouped_y_returns.index = grouped_y_returns.index.year
        grouped_y_returns.columns = ['Return', 'Volatility', 'Sharpe']
        grouped_y_returns.index.name = 'Year' 

        grouped_y_returns_usd = self.values[['$', 'year']].groupby('year').apply(lambda x: x.sum()) 
        grouped_y_returns_usd.index = grouped_y_returns_usd.index.year
        grouped_y_returns['PnL'] = grouped_y_returns_usd['$']
        grouped_y_returns.loc['mean'] = grouped_y_returns.mean()

        return grouped_m_returns_pct, grouped_m_returns_usd, grouped_y_returns


    def print(self):
        print()
        print(f'----- Portfolio Statistics -----')
        print(f"Cumulative Return: ${self.statistics['Cumulative Return ($)']:,.0f} ({self.statistics['Cumulative Return (%)']*100:.2f}%)")
        print(f"Annualized Return: {self.statistics['Annualized Return (%)']*100:.2f}%")
        print(f"Annualized Volatility: {self.statistics['Annualized Volatility (%)']*100:.2f}%")
        print(f"Sharpe Ratio: {self.statistics['Sharpe Ratio']:.2f}")
        print(f"Sortino Ratio: {self.statistics['Sortino Ratio']:.2f}")
        print(f"Max Drawdown: ${self.statistics['Max Drawdown ($)']:,.0f} ({self.statistics['Max Drawdown (%)']*100:.2f}%)")
        print(f"Calmar Ratio: {self.statistics['Calmar Ratio']:.2f}")
        print()
        print('----- Trades -----')
        print(f"Total Trades: {self.statistics['Trade num']}")
        print(f"Win Rate: {self.statistics['Trade Win Rate']*100:.1f}% (avg: {self.statistics['Trade Win Avg (%c)']*100:,.1f}%, std: {self.statistics['Trade Win Std (%c)']*100:,.1f}%)")
        print(f"Loss Rate: {self.statistics['Trade Loss Rate']*100:.1f}% (avg: {self.statistics['Trade Loss Avg (%c)']*100:,.1f}%, std: {self.statistics['Trade Loss Std (%c)']*100:,.1f}%)")
        print(f"Pass Rate: {self.statistics['Trade Pass Rate']*100:.1f}%")
        print(f"E(Win): {self.statistics['Trade Win Expected']*100:,.1f}%")
        print(f"E(Loss): {self.statistics['Trade Loss Expected']*100:,.1f}%")
        #print() 
        #print('----- Monthly Returns -----')
        #print(self.monthly_returns_pct.applymap(lambda x: '' if np.isnan(x) else f'{round(x*100,1)}%'))
        printable_y = self.yearly_returns[['Return', 'Volatility']]
        printable_y = printable_y.applymap(lambda x: '' if np.isnan(x) else f'{round(x*100,1)}%')
        printable_y['Sharpe'] = self.yearly_returns['Sharpe'].apply(lambda x: '' if np.isnan(x) else f'{round(x,2)}')
        printable_y['P&L ($)'] = self.yearly_returns['PnL'].apply(lambda x: '' if np.isnan(x) else f'{x:,.0f}')
        print()
        print('----- Yearly Returns ------')
        print(printable_y)


    def plot(self, plot_type = '%'):
        fig = plt.figure()
        gs = GridSpec(2, 2, figure =fig)
        ax1 = fig.add_subplot(gs[0,:])
        ax1b = ax1.twinx()
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        
        ax1.set_title("Strategy Performance Characteristics")
        ax1.set_ylabel("Positioning (% of Capital)")
        ax1b.set_ylabel("Cumulative Return (%)")
        ax2.set_title("Distribution of Trade PnL")
        ax2.set_ylabel("PnL ($)")
        ax3.set_title("Cumlative Return YoY")

        self.values['lmv%'].plot(ax = ax1, color = 'green', alpha = 0.5)
        self.values['smv%'].plot(ax = ax1, color = 'red', alpha = 0.5)
        self.values['nmv%'].plot.area(ax = ax1, color = 'blue', alpha = 0.25, stacked = False)
        self.values['cumulative'].plot(ax = ax1b, color = 'black')

        self.trading_log.loc[self.trading_log['gross'] > 0, 'gross'].hist(ax = ax2, color = 'green', bins = 50)
        self.trading_log.loc[self.trading_log['gross'] < 0, 'gross'].hist(ax = ax2, color = 'red', bins = 50)

        fig.suptitle("Backtest Graphs")
        ax1.legend()
        
        plt.show()
