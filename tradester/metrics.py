from tradester.feeds.static import SecuritiesTS

from matplotlib.gridspec import GridSpec
from tqdm import tqdm

import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import numpy as np
import calendar



class Metrics():
    
    def __init__(
            self, 
            portfolio, 
            oms,
            start_date, 
            end_date, 
            ):
        self.portfolio = portfolio
        self.oms = oms
        self.start_date = start_date
        self.end_date = end_date
        self.holdings = None
        self.values = None
        self.trading_log = None

        self.statistics = None
        self.monthly_returns_pct = None
        self.monthly_returns_usd = None
        self.yearly_returns = None
        self.ts_yearly_returns_usd = None
        self.ts_yearly_returns_pct = None
    

    def _calculate(self):
        self.holdings = self.portfolio.holdings_df
        self.values = self.portfolio.values_df.set_index('date').sort_index()
        self.trading_log = self.portfolio.trading_log_df

        #if not self.start_date is None:
        #    self.holdings = self.holdings.loc[self.holdings.date >= pd.to_datetime(self.trade_start_date)]
        #    self.values = self.values.loc[self.values.index >= pd.to_datetime(self.trade_start_date)]
        #    self.trading_log = self.trading_log.loc[self.trading_log.date >= pd.to_datetime(self.trade_start_date)]

        self.values['expanding_max'] = self.values['value'].expanding().max()
        self.values['dd_%'] = (self.values['value'] / self.values['expanding_max'] - 1).apply(lambda x: 0 if x > 0 else x)
        self.values['dd_$'] = (self.values['value'] - self.values['expanding_max']).apply(lambda x: 0 if x > 0 else x)
        self.values['Long Market Value'] = self.values['long_equity'] / self.values['value']
        self.values['Short Market Value'] = self.values['short_equity'] / self.values['value']
        self.values['Net Market Value'] = self.values['Long Market Value'] + self.values['Short Market Value'] 
        self.values['Gross Market Value'] = self.values['Long Market Value'] - self.values['Short Market Value'] 
        self.values['cash%'] = self.values['cash']/self.values['value'] - 1
        self.values['%'] = self.values['value'].pct_change().fillna(0)
        self.values['$'] = self.values['value'].diff().fillna(0)
        self.values['cumulative'] = (1+self.values['%']).cumprod().fillna(1)
        self.values['date'] = self.values.index
        self.values['date'] = self.values['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        self.values['year-month'] = self.values['date'].apply(lambda x: pd.to_datetime(f'{x.split("-")[0]}' +'-'+ f'{x.split("-")[1]}'+'-01'))
        self.values['year'] = self.values['date'].apply(lambda x: pd.to_datetime(f'{x.split("-")[0]}'+'-01-01'))
        self.values['day_of_year'] = self.values['date'].apply(lambda x: pd.to_datetime(x).timetuple().tm_yday)

        self.monthly_returns_pct, self.monthly_returns_usd, self.yearly_returns, self.ts_yearly_returns_usd, self.ts_yearly_returns_pct = self.__group_returns()

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

        grouped_y_ts_returns_usd = self.values.pivot_table(index = 'day_of_year', columns = 'year', values='$').fillna(0)
        grouped_y_ts_returns_pct = self.values.pivot_table(index = 'day_of_year', columns = 'year', values='%').fillna(0)
        grouped_y_ts_returns_usd.columns = [x.year for x in grouped_y_ts_returns_usd.columns]
        grouped_y_ts_returns_pct.columns = [x.year for x in grouped_y_ts_returns_pct.columns]
        grouped_y_ts_returns_usd = grouped_y_ts_returns_usd.cumsum()
        grouped_y_ts_returns_pct = (1+grouped_y_ts_returns_pct).cumprod()-1

        return grouped_m_returns_pct, grouped_m_returns_usd, grouped_y_returns, grouped_y_ts_returns_usd, grouped_y_ts_returns_pct


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

    def save(self, path, sheet_name = None):
        pass

    def plot(self, plot_type = '$', start_year = None):
        fig = plt.figure()
        gs = GridSpec(2, 2, figure =fig)
        ax1 = fig.add_subplot(gs[0,:])
        ax1b = ax1.twinx()
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        
        ax1.set_title("Strategy Performance Characteristics")
        ax1b.set_ylabel("Cumulative Performance ($1 invested)")
        ax1.set_ylabel("Portfolio Positioning (%)")
        ax2.set_title("Distribution of Trade PnL")
        ax2.set_xlabel("PnL ($1,000s)")
        ax2.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, pos: f'{x:,.0f}'))
        ax3.set_title("Cumlative Return YoY")
        ax3.set_xlabel("Days in Year")

        # Graph 1: Performance and positioning
        ax1.plot(self.values.index.values, self.values['Long Market Value'].values, color = 'green', alpha = 0.5, label = 'Long Market Value')
        ax1.plot(self.values.index.values, self.values['Short Market Value'].values, color = 'red', alpha = 0.5, label = 'Short Market Value')
        ax1.fill_between(self.values.index.values, self.values['Net Market Value'].values, color = 'blue', alpha = 0.25, label = 'Net Market Value')
        ax1b.plot(self.values.index.values, self.values.cumulative.values, color = 'black')

        # Graph 2: Distribution of Trade PnL
        (self.trading_log.loc[self.trading_log['gross'] > 0, 'gross'] / 1000).hist(ax = ax2, color = 'green', bins = 50)
        (self.trading_log.loc[self.trading_log['gross'] < 0, 'gross'] / 1000).hist(ax = ax2, color = 'red', bins = 50)

        # Graph 3: Yearly Returns by either % or $
        years = self.ts_yearly_returns_usd.columns
        if start_year is not None:
            years = [x for x in years if x >= start_year]
        norm = mpl.colors.Normalize(vmin = min(years), vmax = max(years))
        c_m = mpl.cm.hsv

        s_m = mpl.cm.ScalarMappable(cmap = c_m, norm = norm)
        s_m.set_array([])

        if plot_type == '$':
            ax3.set_ylabel("PnL ($1,000s)")
            ax3.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, pos: f'{x:,.0f}'))
            for year in years:
                ax3.plot(self.ts_yearly_returns_usd[year] / 1000, color = s_m.to_rgba(year))
        elif plot_type == '%':
            ax3.set_ylabel("PnL (%)")
            ax3.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, pos: f'{x:.1f}%'))
            for year in years:
                ax3.plot(self.ts_yearly_returns_pct[year]*100, color = s_m.to_rgba(year))
        temp = pd.DataFrame(index = self.ts_yearly_returns_usd.index)
        temp['0'] = 0
        ax3.plot(temp['0'], color = 'black')

        fig.suptitle("Backtest Graphs")
        ax1.legend()
        plt.colorbar(s_m, ax = ax3)
        plt.show()
