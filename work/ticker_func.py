import yfinance as yf
import pandas as pd
import numpy as np
from pandasql import sqldf

import warnings
warnings.filterwarnings("ignore")

#from IPython.display import display
#pd.options.display.max_columns = None
#pd.options.display.max_rows = 30
#pd.get_option("display.max_rows")
#pd.set_option('display.max_rows', 100)



import plotly.express as px

import plotly.io as pio
pio.templates.default = "plotly_dark"

import plotly.graph_objects as go

#====== FUNCS =====


#========= closing prices =============

def dailyClosePricesbyPeriod(ticker,str_period='5y'):
    #['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y','5y', 'ytd', 'max']
    df = yf.download(ticker.upper(), period=str_period)
    df.reset_index(inplace=True)
    df.columns = ['Date','Close','High','Low','Open','Volume']
    #df['ticker']=ticker
    return df


def simpleMovingAveragesClosePrice(df):
    df['sma10'] = df['Close'].rolling(window=10).mean()
    df['sma20'] = df['Close'].rolling(window=20).mean()
    df['sma50'] = df['Close'].rolling(window=50).mean()
    return df.sort_values(by=['Date'],ascending=[False])


def exponentialMovingAveragesClosePrice(df):
    df['EMA10']= df['Close'].ewm(span=10).mean()
    df['EMA20']= df['Close'].ewm(span=20).mean()
    df['EMA50']= df['Close'].ewm(span=50).mean()
    df['EMA150']= df['Close'].ewm(span=150).mean()
    df['EMA200']= df['Close'].ewm(span=200).mean()
    return df.sort_values(by=['Date'],ascending=[False])



def findBreakOut(df,ticker):
    ticker = ticker[0]
    qry = """
                SELECT
                '{ticker}' AS ticker
                ,*
                ,CASE
                WHEN Close > EMA10 AND Close > EMA20 AND Close > EMA50 THEN 'Yes'
                ELSE 'No' END AS 'break_out'

                ,CASE
                WHEN Close < EMA10 AND Close < EMA20 AND Close < EMA50 THEN 'Yes'
                ELSE 'No' END AS 'break_down'



                ,CASE
                WHEN Close < EMA200 THEN 'Yes'
                ELSE 'No' END AS break_down_200ema



                ,CASE
                WHEN Close < EMA150 THEN 'Yes'
                ELSE 'No' END AS break_down_150ema



                FROM df
                """.format(ticker=ticker)
    return sqldf(qry,locals())

def breakOutSignals(df):
    qry="""
        SELECT *
        ,LAG ( break_out,1,0) OVER ( ORDER BY Date ) AS prev1
        ,LAG ( break_out,2,0) OVER ( ORDER BY Date ) AS prev2
        ,LAG ( break_out,3,0) OVER ( ORDER BY Date ) AS prev3
        FROM df
        ORDER BY Date DESC
        """

    qry2="""
        SELECT *

        ,CASE
        WHEN break_out = 'Yes' AND prev1 = 'Yes' AND prev2 = 'Yes' AND prev3 = 'No' THEN 'Buy'
        ELSE '' END AS Flag_Buy

        ,CASE
        WHEN prev1 = 'Yes'AND prev2 = 'Yes' AND prev3 = 'Yes' AND break_out = 'No' THEN 'Sell'
        ELSE '' END AS Flag_Sell
        FROM df
        """

    qry3 =  """
            SELECT *
            ,CASE
            WHEN Flag_Buy='Buy' THEN 'Yes Buy'
            WHEN Flag_Sell = 'Sell' THEN 'Sell'
            WHEN break_down_200ema = 'Yes' THEN 'below200ema'
            WHEN break_down_150ema = 'Yes' THEN 'below150ema'
            ELSE break_out END AS break_out_signal
            FROM df
            """


    df = sqldf(qry,locals())
    df = sqldf(qry2,locals())
    df = sqldf(qry3,locals())
    return df

#================= end of closing prices ===================





#=============== recent financials ------------

def financials_quarter(ticker_list):
    qtr_cols = list(set(['ticker','shortName','sector','industry','Total Assets','Total Liabilities Net Minority Interest'
            ,'Other Intangible Assets','Total Debt','Net Interest Income','Interest Income','Total Revenue'
            ,'Current Assets','Current Liabilities'
            ,'Gross Profit','Operating Income','Total Equity Gross Minority Interest'
            ,'EBIT','EBITDA','Interest Expense','Working Capital','Retained Earnings'
            ]))

    df = pd.DataFrame(columns=qtr_cols)
    for ticker in ticker_list:
        #print(ticker)
        # Get the ticker object
        stock = yf.Ticker(ticker.upper())
        if 'sector' not in stock.info.keys():
            sector = np.nan
        else:
            sector = stock.info['sector']

        if 'industry' not in stock.info.keys():
            industry = np.nan
        else:
            industry = stock.info['industry']

        if 'shortName' not in stock.info.keys():
            shortName = np.nan
        else:
            shortName = stock.info['shortName']
        #print(shortName,sector,industry)

        # Get the balance sheet
        balancesheet_df = stock.quarterly_balance_sheet.transpose()
        balancesheet_df.reset_index(inplace=True)
        balancesheet_df.rename(columns={"index": "date"}, inplace=True)

        # Get the income statement
        income_df = stock.quarterly_income_stmt.transpose()
        income_df.reset_index(inplace=True)
        income_df.rename(columns={"index": "date_b"}, inplace=True)
        income_df['Total Revenue'] = income_df['Total Revenue'].abs()

        # Get the cashflow statement
        cashflow_df = stock.quarterly_cashflow.transpose()
        cashflow_df.reset_index(inplace=True)
        cashflow_df.rename(columns={"index": "date_c"}, inplace=True)

        #COMBINE
        tmp_df = sqldf("""SELECT
                  '{ticker}' AS ticker
                  ,'{shortName}' AS shortName
                  ,'{sector}' AS sector
                  ,'{industry}' AS industry
                  ,(`Total Revenue`- LEAD(`Total Revenue`,1) OVER (ORDER BY date DESC))/`Total Revenue` AS qtr_chg_total_revenue



                  ,*
                  FROM balancesheet_df a
                  LEFT JOIN income_df b ON a.date = b.date_b
                  LEFT JOIN cashflow_df c ON a.date = c.date_c
                  """.format(ticker=ticker,shortName=shortName,sector=sector,industry=industry)
               ,locals())
        tmp_df.drop(columns=['date_b','date_c'])

        #print(tmp_df.shape)
        df =pd.concat([df,tmp_df]).reset_index(drop=True)

    df.dropna(subset=['Total Revenue'], inplace=True)



    # interest income ratio
    qry = """
          SELECT
            `Total Assets`- `Total Liabilities Net Minority Interest` - `Other Intangible Assets`
            AS tangible_net_worth

            --,`Total Debt`/market_cap AS debt_ratio

            ,`Interest Income`/`Total Revenue` AS interest_income_ratio

            ,`Net Interest Income`/`Total Revenue` AS net_interest_income_ratio

            ,`Current Assets`/`Current Liabilities` AS current_liquidity

            ,`Gross Profit`/`Total Revenue` AS gross_margin

            ,`Operating Income`/`Total Revenue` AS operating_profit_of_the_sales

            ,`Total Revenue`/`Total Assets` AS assets_turnover

            ,`Total Revenue`/`Current Assets` AS current_assets_turnover


            ,`Total Equity Gross Minority Interest`/`Total Liabilities Net Minority Interest`
            AS capital_ratio

            ,`Total Equity Gross Minority Interest`/`Current Liabilities`
            AS coverage_of_short_term_liabilities_by_equity

            ,`Net Income`/`Total Revenue` AS npat_margin

            ,EBIT/`Interest Expense` AS interest_cover

            ,`Total Liabilities Net Minority Interest` / (`Total Assets`- `Total Liabilities Net Minority Interest` - `Other Intangible Assets`)
            AS total_liabilities_to_tangible_networth

            ,`Total Debt`/ EBITDA AS debt_to_ebitda

            ,`Working Capital`/`Total Revenue` AS working_capital_to_sales

            ,`Working Capital`/`Total Assets`  AS A_LIQUIDITY
            ,`Retained Earnings`/`Total Assets` AS B_PROFITABILITY
            , EBIT/`Total Assets` AS C_OPERATING_EFFICIENCY
            --, market_cap/`Total Liabilities Net Minority Interest` AS D_INDEBTNESS

            -- ASSETS TURNOVER
            , `Total Revenue`/`Total Assets` AS E_PRODUCTIVITY
            ,* FROM df
            """
    #print(qry)
    df= sqldf(qry,locals())
    df['date'] = pd.to_datetime(df['date']).dt.date
    return df



def latestRatios(df):
    # for left join to yahoo stats
    interest_income_ratio_df = sqldf("""
                                    SELECT
                                    a.ticker AS ticker_b
                                    ,a.interest_income_ratio
                                    ,a.net_interest_income_ratio
                                    --,a.perc_chg_total_revenue
                                    --,a.Zone
                                    FROM df a
                                    INNER JOIN (
                                                SELECT
                                                ticker
                                                ,max(date) AS max_date
                                                FROM df
                                                GROUP BY 1
                                              ) b on a.ticker = b.ticker AND a.date = b.max_date
                                    """,locals())
    interest_income_ratio_df['interest_income_ratio']=interest_income_ratio_df['interest_income_ratio'].fillna(0)
    interest_income_ratio_df['net_interest_income_ratio']=interest_income_ratio_df['net_interest_income_ratio'].fillna(0)
    return interest_income_ratio_df


# In[4]:


recent_ls = ['shortName'
            ,'industry'
            ,'trailingPE','forwardPE'
            ,'currentPrice','fiftyTwoWeekLow','fiftyTwoWeekHigh'
            ,'targetMedianPrice','targetHighPrice'
            #,'fiftyDayAverage','twoHundredDayAverage'
            ,'trailingPegRatio','currentRatio'
            ,'shortRatio','revenuePerShare','totalCashPerShare'
            ,'returnOnEquity','returnOnAssets','operatingMargins','ebitdaMargins'
            ,'revenueGrowth','earningsGrowth'
            ,'totalDebt','marketCap','freeCashflow'
            ,'debtToEquity'
            ,'longBusinessSummary','sector'
            ,'financialCurrency'
            ]


def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res


def recentTickerFinance(ticker,recent_ls):
    fin_dict={'ticker':[ticker]}
    stock = yf.Ticker(ticker.upper())
    for r in recent_ls:
        if r not in stock.info.keys():
            tmp_dict = {r:[np.nan]}
        else:
            tmp_dict = {r:[stock.info[r]]}
        fin_dict = Merge(fin_dict,tmp_dict)
    return pd.DataFrame.from_dict(fin_dict)





def recentFinance(ticker_ls,recent_ls):
    df = pd.DataFrame()
    for ticker in ticker_ls:
        #print(ticker)
        tmp_df = recentTickerFinance(ticker,recent_ls)
        df = pd.concat([df,tmp_df])
    return df.fillna(0)




def marketTrend(df):
    qry="""
        SELECT

        CASE
        WHEN perc_Chg_52WkHigh > -10 AND perc_Chg_52WkHigh <= -5 THEN 'Dip'
        WHEN perc_Chg_52WkHigh > -20 AND perc_Chg_52WkHigh <= -10 THEN 'Correction'
        WHEN perc_Chg_52WkHigh <= -20 THEN 'Bearish'
        ELSE '-' END AS market_trend


        ,*
        FROM df
        """
    return sqldf(qry,locals())




#import streamlit as st
#@st.cache_data
def fetchRecent(ticker_list,recent_ls):
    df = recentFinance(ticker_list,recent_ls)




    qry_recent_ratios = """
                    SELECT
                    ROUND(  (currentPrice-fiftyTwoWeekHigh)/fiftyTwoWeekHigh  ,4)*100 AS perc_Chg_52WkHigh
                    ,ROUND((targetMedianPrice/currentPrice)-1,4)*100 AS upside_Perc_targetMedianPrice

                    ,CASE
                    WHEN financialCurrency = 'USD' THEN CAST(totalDebt AS FLOAT)/marketCap
                    WHEN financialCurrency = 'EUR' THEN (CAST(totalDebt AS FLOAT)*1.17)/marketCap
                    WHEN financialCurrency = 'TWD' THEN (CAST(totalDebt AS FLOAT)*0.033)/marketCap
                    WHEN financialCurrency = 'DKK' THEN (CAST(totalDebt AS FLOAT)*0.16)/marketCap
                    ELSE NULL END AS debt_ratio

                    ,*
                    FROM df
                    """
    df = sqldf(qry_recent_ratios,locals())
    return marketTrend(df)







def genAnalyseTicker(ticker,report=True):
    df = dailyClosePricesbyPeriod(ticker)
    df = exponentialMovingAveragesClosePrice(df)
    df = findBreakOut(df,ticker)
    df = breakOutSignals(df)

    recent_df = fetchRecent([ticker],recent_ls)
    qtr_df = financials_quarter([ticker])


    # fetch variables
    interest_income_ratio = qtr_df['interest_income_ratio'].values[0]
    net_interest_income_ratio = qtr_df['net_interest_income_ratio'].values[0]
    qtr_revenue_growth = qtr_df['qtr_chg_total_revenue'].values[0]
    qtr_npat_margin = qtr_df['npat_margin'].values[0]

    lastBreakOutSignal = df['break_out_signal'].values[0]
    break_down_150ema = df['break_down_150ema'].values[0]
    break_down = df['break_down'].values[0]

    longBusinessSummary = recent_df['longBusinessSummary'].values[0]
    forwardPE = round(recent_df['forwardPE'][0],2)
    trailingPE = round(recent_df['trailingPE'][0],2)
    trailingPegRatio = round(recent_df['trailingPegRatio'][0],2)
    #currentRatio = round(recent_df['currentRatio'][0],2)
    revenueGrowth = round(recent_df['revenueGrowth'][0],4)
    operatingMargins = round(recent_df['operatingMargins'][0],4)
    returnOnEquity = round(recent_df['returnOnEquity'][0],4)
    debt_ratio = round(recent_df['debt_ratio'][0],4)

    marketCap = recent_df['marketCap'].values[0]
    shortName = recent_df['shortName'].values[0]
    industry = recent_df['industry'].values[0]
    financialCurrency = recent_df['financialCurrency'].values[0]


    # tmp_df
    tmp_df = recent_df.loc[:,('ticker','revenueGrowth','operatingMargins','returnOnEquity','debt_ratio','forwardPE','trailingPegRatio')]

    if interest_income_ratio is not np.nan:
        tmp_df['interest_income_ratio'] = interest_income_ratio
    else:
        tmp_df['interest_income_ratio'] = net_interest_income_ratio

    tmp_df['MarketCap_Bil']=round(marketCap/1000000000,2)

    tmp_df['qtr_TotalRevenue_Bil'] =round(qtr_df['Total Revenue'].values[0]/1000000000,2)

    # Handle potential None values for 'Free Cash Flow'
    free_cash_flow = qtr_df['Free Cash Flow'].values[0] if 'Free Cash Flow' in qtr_df.columns and qtr_df['Free Cash Flow'].values[0] is not None else 0

    tmp_df['qtr_FreeCashFlow_Bil'] =round(free_cash_flow/1000000000,2)

    tmp_df['qtr_revenue_growth'] = qtr_revenue_growth
    # Handle potential division by zero
    tmp_df['qtr_fcf_margin'] = round(tmp_df['qtr_FreeCashFlow_Bil']/tmp_df['qtr_TotalRevenue_Bil'],2) if tmp_df['qtr_TotalRevenue_Bil'].values[0] != 0 else 0


    tmp_df['qtr_npat_margin'] = qtr_df['npat_margin'].values[0]
    #tmp_df['qtr_ebitda_margin'] = qtr_df['ebitdaMargins'].values[0]


    for c in ['revenueGrowth','operatingMargins','returnOnEquity','debt_ratio','forwardPE','trailingPegRatio'
              ,'interest_income_ratio','qtr_revenue_growth','qtr_npat_margin']:
        tmp_df[c] = round(tmp_df[c],3)

    tmp_df['Close'] = round(df['Close'].values[0],2)
    tmp_df['break_out_signal'] = lastBreakOutSignal
    if break_down_150ema == 'No':
      tmp_df['break_out_150ema'] ='Yes'
    else:
      tmp_df['break_out_150ema'] = 'No'
    tmp_df['break_down'] = break_down

    #tmp_df['longBusinessSummary'] = longBusinessSummary
    tmp_df['shortName'] = shortName
    tmp_df['industry'] = industry
    tmp_df['financialCurrency'] = financialCurrency

    qry_fx = """
          SELECT
          *
          ,CASE
          WHEN financialCurrency = 'USD' THEN qtr_TotalRevenue_Bil
          WHEN financialCurrency = 'EUR' THEN ROUND(qtr_TotalRevenue_Bil*1.17,2)
          WHEN financialCurrency = 'TWD' THEN ROUND(qtr_TotalRevenue_Bil*0.033,2)
          WHEN financialCurrency = 'DKK' THEN ROUND(qtr_TotalRevenue_Bil*0.16,2)
          ELSE NULL END AS qtr_TotalRevenue_Bil_USD

          ,CASE
          WHEN financialCurrency = 'USD' THEN qtr_FreeCashFlow_Bil
          WHEN financialCurrency = 'EUR' THEN ROUND(qtr_FreeCashFlow_Bil*1.17,2)
          WHEN financialCurrency = 'TWD' THEN ROUND(qtr_FreeCashFlow_Bil*0.033,2)
          WHEN financialCurrency = 'DKK' THEN ROUND(qtr_FreeCashFlow_Bil*0.16,2)
          ELSE NULL END AS qtr_FreeCashFlow_Bil_USD


          FROM tmp_df
          """
    tmp_df = sqldf(qry_fx,locals())


    if report:
      print(f'\n\n================== {shortName} ==================')
      print(f'\n\nCompany:  {shortName} ')
      print('Industry:  ',industry)
      print('MarketCap:  ',round(marketCap/1000000000,2),' billion' )
      print('ForwardPE:  ',forwardPE)
      print(f'Break Out Signal: {lastBreakOutSignal}',)

      print("\n\nRed Flags  (if exist):")
      #if forwardPE > trailingPE and trailingPE!=0: print('* __forwardPE:__ ', forwardPE, ' > trailingPE: ', trailingPE,' :x:')
      if debt_ratio >=0.33 :
          print('- debt_ratio:  ',round(debt_ratio*100,1),'%')
      if revenueGrowth < 0 :
          print('- revenueGrowth:  ',round(revenueGrowth*100,1),'%')
      if qtr_revenue_growth is not None and not np.isnan(qtr_revenue_growth) and qtr_revenue_growth < 0:
          print('- qtr_revenue_growth:  ',round(qtr_revenue_growth*100,1),'%')

      if returnOnEquity < 0.1 :
          print('- returnOnEquity:  ',round(returnOnEquity*100,1),'%')
      if operatingMargins < 0.1 :
          print('- operatingMargins:  ',round(operatingMargins*100,1),'%')
      if break_down == 'Yes':
          print('- Down Trend: Below 50,20,10 EMA!')
      if break_down_150ema == 'Yes':
          print('- Down Trend: Below 150EMA!')

      print("\n\nGreen Flags (if exist):")
      if revenueGrowth >= 0.1 :
          print('- revenueGrowth: ',round(revenueGrowth*100,1),'%')
      if qtr_revenue_growth is not None and not np.isnan(qtr_revenue_growth) and qtr_revenue_growth >= 0.1 :
          print('- qtr_revenue_growth: ',round(qtr_revenue_growth*100,1),'%')
      if returnOnEquity >= 0.2 :
          print('- returnOnEquity: ',round(returnOnEquity*100,1),'%')
      if operatingMargins >= 0.2 :
          print('- operatingMargins:',round(operatingMargins*100,1),'%')
      if break_down_150ema == 'No':
          print('- Up Trend:  Above 150 EMA!')

      if lastBreakOutSignal in ['Yes','Yes Buy']:
          print('- Up Trend:  Above 50,20,10 EMA!')



      #print('\n\n',tmp_df)
      print('\n\n',qtr_df[['date','Total Revenue','Free Cash Flow','Capital Expenditure']])
      print('\n\n',df[['Date','Close','EMA150','break_out_signal']].head(10),'\n')


      # Handle potential None or NaN values for qtr_revenue_growth
      debt_ratio_str = f' debt_ratio: {round(debt_ratio*100,1)}%,' if debt_ratio is not None and not np.isnan(debt_ratio) else ' debt_ratio: N/A,'
      qtr_revenue_growth_str = f' QtrRevenueGrowth: {round(qtr_revenue_growth*100,1)}%,' if qtr_revenue_growth is not None and not np.isnan(qtr_revenue_growth) else ' QtrRevenueGrowth: N/A,'
      qtr_npat_margin_str = f' QtrNPATMargin: {round(qtr_npat_margin*100,1)}%,' if qtr_npat_margin is not None and not np.isnan(qtr_npat_margin) else 'QtrNPATMargin: N/A'

      revenueGrowth_perc_str = f' RevenueGrowth: {round(revenueGrowth*100,1)}%,' if revenueGrowth is not None and not np.isnan(revenueGrowth) else ' RevenueGrowth: N/A,'
      operatingMargins_perc_str = f' OperatingMargins: {round(operatingMargins*100,1)}%,' if operatingMargins is not None and not np.isnan(operatingMargins) else ' OperatingMargins: N/A,'


      closeTitle = ticker + ' ClosePrice ' + debt_ratio_str + qtr_revenue_growth_str + qtr_npat_margin_str + ' Break Out Signal: ' + lastBreakOutSignal


      fig_close_prices = px.scatter(df, x="Date", y="Close"
                                    , color="break_out_signal"
                                    #, symbol = 'break_down_150ema'
                                    , color_discrete_map = {'Yes':'green'
                                                            ,'Yes Buy':'yellow'
                                                            ,'No':'grey'
                                                            ,'below150ema':'purple'
                                                            ,'Sell': 'red'
                                                            }
                                    #,color_discrete_sequence = ['red','blue']
                                    , title = closeTitle
                                    #,template="plotly_dark"
                                      )


      fig_revenue = px.bar(qtr_df, x="date", y="Total Revenue", color="shortName"
                                , title = f'{ticker}: TotalRevenue {debt_ratio_str} {qtr_revenue_growth_str} {qtr_npat_margin_str} Break Out Signal: {lastBreakOutSignal}'
                          )

      fig_fcf = px.bar(qtr_df, x="date", y="Free Cash Flow", color="shortName"
                             , title = f'{ticker}: FreeCashFlow {debt_ratio_str} {qtr_revenue_growth_str} {qtr_npat_margin_str} Break Out Signal: {lastBreakOutSignal}'
                            )

      fig_capex = px.bar(qtr_df, x="date", y="Capital Expenditure", color="shortName"
                               , title = f'{ticker}: CapEx {debt_ratio_str} {qtr_revenue_growth_str} {qtr_npat_margin_str} Break Out Signal: {lastBreakOutSignal}'
                               )

      fig_close_prices.show()
      fig_revenue.show()
      fig_fcf.show()
      fig_capex.show()

    return tmp_df



def genScatterCharts(df):

    min_qtr_TotalRevenue_Bil = df['qtr_TotalRevenue_Bil_USD'].min()
    max_qtr_TotalRevenue_Bil = df['qtr_TotalRevenue_Bil_USD'].max()

    txt = f'Quaterly: Revenue Growth VS NetIncome Margins,  QTR Revenue:  Min= {min_qtr_TotalRevenue_Bil} Billion to  Max= {max_qtr_TotalRevenue_Bil} Billion'

    fig_rev_margins = px.scatter(df
                            , x= 'qtr_npat_margin' #'operatingMargins'
                            , y= 'qtr_revenue_growth'
                            , color= 'break_out_signal'
                            , color_discrete_map = {'Yes':'green'
                                                    ,'Yes Buy':'yellow'
                                                    ,'No':'white'
                                                    ,'below150ema':'purple'
                                                    ,'Sell': 'red'
                                                    }
                            #, symbol = 'industry'
                            #, size= 'qtr_TotalRevenue_Bil'
                            , hover_data=['ticker','shortName','qtr_TotalRevenue_Bil_USD','trailingPegRatio','Close']#,'revenueGrowth','forwardPE']
                            , title = txt
                            , height = 550
                            )

    fig_rev_margins.update_traces(marker=dict(size=15))
    fig_rev_margins.show()


