from kiteconnect import KiteConnect
import pandas as pd
import logging
from configLogin import api_key
from datetime import datetime

outputFileName = "instruments.csv"
# change date as per next weekly expriry data for option stock.
expiry_date = '2022-07-21'

logging.basicConfig(filename='./chalicelib/instrumentListUpdate.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.error("Logged to instrumentListUpdate.log")
#connect to Kite API service
kite = KiteConnect(api_key=api_key)
try:
    # read access token from file which was saved manually by user (you) by login into your trading account with zerodha
    acess_token = open('access_token.txt','r').read()
    kite.set_access_token(acess_token)
    profileObj=kite.profile()
except Exception as e: 
    logging.error("Exception occurred", exc_info=True)

    
# hit API which gives list of BANKNIFTY instruments for given expriry date.    
def setInstrumentsdf(expirydatestr):
    try:
        expirydate=datetime.strptime(expirydatestr,'%Y-%m-%d').date()
        instrumentsList=kite.instruments(exchange=kite.EXCHANGE_NFO)
        df = pd.DataFrame(instrumentsList)
        df.drop(df.loc[(df['name']!='BANKNIFTY')].index,inplace=True)
        df.drop(df.loc[df['expiry']!=expirydate].index,inplace=True)
        return df
    except Exception as e:
        logging.error("Exception-setInstrument", exc_info=True)
        print("Exception-setInstrument:{0}".format(e))
        #htmlReqGETBot("Exception-setInstrument:{0}".format(e))
    return None

datframe=setInstrumentsdf(expiry_date)
#save it in csv file format.
datframe.to_csv(outputFileName,index=False)








    
    


