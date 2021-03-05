# Tradester
Tradester is a python-based backtesting framework to test trading strategies using futures and equities. The current implementation is meant to interface with the data infrastructure I currently have set up.


## Setup

```
py setup.py install
```

Please note that I run out of WSL 2 (Ubuntu 20.something), there may need to be some modifications for other operating systems. By default the system handles MySQL, you may need to include psycopg2 (or psycopg2-binary for linux) or pyodbc for PostgreSQL or SQL Server support.

## Running a Strategy (SMA Strategy)
Please see the completed SMA Strategy example in examples/sma.py.


## User Control

The systems is designed with bias limitations in mind. If your strategy has a buy signal Monday, it won't be executed until Tuesday. Additionally, there are rules defined in the Engine() constructor such as _adv_participation_, _adv_period_, and _adv_oi_ which limit the percentage of average daily volume (_adv_particiation_ over _adv_period_ periods) or percentage of open interest (_adv_oi_).

## Sample Output

The output from the example portfolio is as follows:
![sample_output](https://user-images.githubusercontent.com/61852120/110053973-2265a400-7d0f-11eb-8cd7-2f0a3cea7fec.PNG)
