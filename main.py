from kiteconnect import KiteConnect
import pandas as pd
import numpy as np
from config.configLogin import api_key
from config.equations import mytalib as tl
from config.telegram_bot import htmlReqGETBot
from datetime import datetime, timedelta
import logging
import pytz
import time

logging.basicConfig(
    filename='./config/app.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.error("Logged to app.log")


#use currentDateTime fun instead of datetime.now()
# it is important if you are runing script in server.
def currentDateTime():
    return datetime.now().astimezone(pytz.timezone("Asia/Kolkata"))


#normaly previousTradingDay
previousTradingDay = currentDateTime()
# maxlength=300
# maxintervel=3
if previousTradingDay.weekday() == 0 or previousTradingDay.weekday() == 1:
    dayDelta = 4
else:
    dayDelta = 2

#we are doing trading on BankNifty weekly option here
# instruments are change every Thursday for weekly option
# so it need to update on every Friday befor trading start
instrumentsdf = pd.read_csv('./config/instruments.csv')

slm_order_id = 0
order_id = 0
exit_order_id = 0
orders = []
haveCall = False
havePut = False
orderType = None  #SELL or BUY
optionType = None  #CE or PE
placeOrder = False
positionOnBuy = False  # after placing order.
selectedtradingsymbol = None
quantity = 25


def writeCurrentStatus(date, message):
    try:
        global slm_order_id, order_id, exit_order_id, orders, haveCall, havePut, orderType, optionType, placeOrder, positionOnBuy, selectedtradingsymbol, quantity
        writeDown = "DateTime-{0}, {1} \n\n".format(date, message)
        writeDown += "slm_order_id={0}\norder_id={1}\nexit_order_id={2}\norders={3}\nhaveCall={4}\nhavePut={5}\norderType={6}\noptionType={7}\nplaceOrder={8}\npositionOnBuy={9}\nselectedtradingsymbol={10}\nquantity={11}\n\n".format(
            slm_order_id, order_id, exit_order_id, orders, haveCall, havePut,
            orderType, optionType, placeOrder, positionOnBuy,
            selectedtradingsymbol, quantity)
        with open('currentStatus.txt', 'a') as ak:
            ak.write(writeDown)
            ak.close()
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        htmlReqGETBot('Error in write.\n{0}'.format(e))
    return None


kite = KiteConnect(api_key=api_key)

myTalibObj = tl()

#set acess_token from file
try:
    acess_token = open('./config/access_token.txt', 'r').read()
    kite.set_access_token(acess_token)
    profileObj = kite.profile()
    htmlReqGETBot('{0}, you are logged in main.py.'.format(
        profileObj.get('user_shortname')))
except Exception as e:
    logging.error("Exception occurred", exc_info=True)
    htmlReqGETBot('It seem token is expired.Need to login again\n{0}'.format(
        kite.login_url()))


def selectTradingsymbol(strike, optionType, df):
    global kite
    try:
        strike = int(strike)
        buyTradingsymbol = ''
        buyDF = df.loc[df['strike'].between(
            strike - 500,
            strike + 900)].loc[df['instrument_type'] == optionType]
        if optionType == 'PE':
            array = np.flipud(buyDF['tradingsymbol'].values)
        else:
            array = buyDF['tradingsymbol']
        for x in array:
            ltpobj = kite.ltp("NFO:" + x)
            if (ltpobj["NFO:" + x]['last_price'] <
                    500):  #ltpobj["NFO:"+x]['last_price']>450 and
                buyTradingsymbol = x
                print("selectedTradingsymbol:{0},ltp:{1}".format(
                    x, ltpobj["NFO:" + x]['last_price']))
                htmlReqGETBot("selectedTradingsymbol:{0},ltp:{1}".format(
                    x, ltpobj["NFO:" + x]['last_price']))
                return buyTradingsymbol
    except Exception as e:
        logging.error("Exception-selectTradingsymbol", exc_info=True)
        print("Exception-selectTradingsymbol:{0}".format(e))
        htmlReqGETBot("Exception-selectTradingsymbol:{0}".format(e))
    return None


def strategyChecking(BNHeikinAshi3min, x):
    global orders, orderType, optionType, haveCall, havePut, placeOrder, positionOnBuy, order_id, slm_order_id, exit_order_id, selectedtradingsymbol
    try:
        cmo = BNHeikinAshi3min['cmo5'][x]
        trand0 = BNHeikinAshi3min['trend'][x - 1]
        trand1 = BNHeikinAshi3min['trend'][x]
        rsi = BNHeikinAshi3min['rsi14'][x]
        date = BNHeikinAshi3min['date'][x]
        if cmo >= 80 and trand1 != trand0 and rsi < 75:
            orders.append(date)
            orderType = "BUY"
            optionType = "CE"
            haveCall = True
            placeOrder = True  #buy CE
            #print("{0} Buy call CMO :{1}, RSI:{2}.".format(date,cmo,rsi))
            htmlReqGETBot("{0} Buy call CMO :{1}, RSI:{2}.".format(
                date, cmo, rsi))
            if havePut and positionOnBuy:
                order_id, slm_order_id, exit_order_id = placeOrderfn(
                    trnsactiontype="SELL",
                    tradingsymbol=selectedtradingsymbol,
                    quantity=quantity,
                    order_id=order_id,
                    slm_order_id=slm_order_id,
                    exit_order_id=exit_order_id,
                    exchangetype='NFO',
                    ordertype='MARKET',
                    producttype='MIS')
                positionOnBuy = False
                havePut = False
                selectedtradingsymbol = None
        elif cmo <= -80 and trand1 != trand0 and rsi > 25:
            orders.append(date)
            orderType = "BUY"
            optionType = "PE"
            havePut = True
            placeOrder = True  #buy PE
            #print("{0} Buy put CMO :{1}, RSI:{2}.".format(date,cmo,rsi))
            htmlReqGETBot("{0} Buy put CMO :{1}, RSI:{2}.".format(
                date, cmo, rsi))
            if haveCall and positionOnBuy:
                order_id, slm_order_id, exit_order_id = placeOrderfn(
                    trnsactiontype="SELL",
                    tradingsymbol=selectedtradingsymbol,
                    quantity=quantity,
                    order_id=order_id,
                    slm_order_id=slm_order_id,
                    exit_order_id=exit_order_id,
                    exchangetype='NFO',
                    ordertype='MARKET',
                    producttype='MIS')
                positionOnBuy = False
                haveCall = False
                selectedtradingsymbol = None
        elif haveCall and rsi >= 75:
            orders.append(date)
            orderType = "SELL"
            optionType = "CE"
            haveCall = False
            placeOrder = True  #place sell CE
            #print("{0} sell call CMO :{1}, RSI:{2}.".format(date,cmo,rsi))
            htmlReqGETBot("{0} sell call CMO :{1}, RSI:{2}.".format(
                date, cmo, rsi))
        elif havePut and rsi <= 25:
            orders.append(date)
            orderType = "SELL"
            optionType = "PE"
            havePut = False
            placeOrder = True  #place sell PE
            #print("{0} sell put CMO :{1}, RSI:{2}.".format(date,cmo,rsi))
            htmlReqGETBot("{0} sell put CMO :{1}, RSI:{2}.".format(
                date, cmo, rsi))
        else:
            placeOrder = False  #don't place order
            #htmlReqGETBot("waiting...")
    except Exception as e:
        placeOrder = False
        logging.error("Exception-strategyChecking", exc_info=True)
        #print("Exception-strategyChecking:{0}".format(e))
        htmlReqGETBot("Exception-strategyChecking:{0}".format(e))
    return placeOrder


def placeOrderfn(trnsactiontype,
                 tradingsymbol,
                 quantity=1,
                 order_id=0,
                 slm_order_id=0,
                 exit_order_id=0,
                 exchangetype='NFO',
                 ordertype='MARKET',
                 producttype='MIS'):
    global kite
    try:
        if trnsactiontype == 'SELL' or slm_order_id != 0:
            for x in kite.orders():
                if x['status'] == 'TRIGGER PENDING' and x[
                        'order_id'] == slm_order_id:
                    exit_order_id = kite.modify_order(
                        variety=kite.VARIETY_REGULAR,
                        order_id=slm_order_id,
                        quantity=quantity,
                        order_type='MARKET')
                    logging.error(
                        "Exit from open SM-L order.Exit_ID is: {0}".format(
                            exit_order_id))
                    #print("Exit from open order SM-L.Exit_ID is: {0}".format(exit_order_id))
                    htmlReqGETBot(
                        "Exit from open order SM-L.Exit_ID is: {}".format(
                            exit_order_id))
            slm_order_id = 0
            order_id = 0
        if trnsactiontype == 'BUY':
            order_id = kite.place_order(tradingsymbol=tradingsymbol,
                                        exchange=exchangetype,
                                        transaction_type='BUY',
                                        variety=kite.VARIETY_REGULAR,
                                        quantity=quantity,
                                        order_type=ordertype,
                                        product=producttype)  #producttype
            logging.error("Order is placed. ID is: {0}".format(order_id))
            #print("Order is placed. ID is: {0}".format(order_id))
            htmlReqGETBot("Order is placed. ID is: {0}".format(order_id))
            #place stoploss at 20% buy value, market price
            stoploss = round(
                kite.ltp(exchangetype + ":" +
                         tradingsymbol)[exchangetype + ":" +
                                        tradingsymbol]['last_price'] * 0.70, 1)
            #stoploss=round(kite.ltp('NSE:IRFC')['NSE:IRFC']['last_price']*0.80,1)
            slm_order_id = kite.place_order(
                tradingsymbol=tradingsymbol,
                exchange=exchangetype,
                transaction_type='SELL',
                variety=kite.VARIETY_REGULAR,
                quantity=quantity,
                order_type='SL-M',
                product=producttype,
                trigger_price=stoploss  #need to see response of order_id
            )
            logging.error(
                "SL-M Order is placed. ID is: {}".format(slm_order_id))
            #print("SL-M Order is placed. ID is: {}".format(slm_order_id))
            htmlReqGETBot(
                "SL-M Order is placed. ID is: {}".format(slm_order_id))
            exit_order_id = 0
            selectedtradingsymbol = tradingsymbol
    except Exception as e:
        logging.error("Exception-placeOrder", exc_info=True)
        #print("Order placement failed: {0}".format(e))
        htmlReqGETBot("Order placement failed: {0}".format(e))
    return order_id, slm_order_id, exit_order_id


endtime = currentDateTime().replace(hour=15,
                                    minute=24,
                                    second=0,
                                    microsecond=0)

while True:
    currenttime = currentDateTime()

    if currenttime > endtime:
        htmlReqGETBot("script end {0}".format(currenttime))
        break
    elif (currenttime.minute % 3 == 0 and currenttime.second == 5):  #

        to_date = datetime.strftime(currenttime, '%Y-%m-%d %H:%M:%S')

        from_dateGstr = datetime.strftime(
            currenttime - timedelta(days=dayDelta), '%Y-%m-%d %H:%M:%S')
        try:
            records = kite.historical_data(15665922,
                                           from_date=from_dateGstr,
                                           to_date=to_date,
                                           interval='3minute',
                                           oi=False)
            recorddf = pd.DataFrame(records)
            BNHeikinAshi3min = myTalibObj.convert2HeikinAshi(data=recorddf)

            BNHeikinAshi3min.drop(BNHeikinAshi3min.tail(1).index.item(),
                                  axis=0,
                                  inplace=True)

            BNHeikinAshi3min["rsi14"] = myTalibObj.rsi(
                srcClose=BNHeikinAshi3min['close'], length=14)

            BNHeikinAshi3min["cmo5"] = myTalibObj.CMO(
                src=BNHeikinAshi3min['close'], length=5)

            BNHeikinAshi3min["supertrend54"], BNHeikinAshi3min[
                "trend"] = myTalibObj.SUPERTREND(
                    srcHigh=BNHeikinAshi3min['high'],
                    srcLow=BNHeikinAshi3min['low'],
                    srcClose=BNHeikinAshi3min['close'],
                    length=5,
                    multiplier=4)
            logging.error(BNHeikinAshi3min.tail(1))
            print(BNHeikinAshi3min.tail(1))

            #strategyChecking()==True placeOrder
            if strategyChecking(BNHeikinAshi3min,
                                BNHeikinAshi3min.tail(1).index.item()):
                if positionOnBuy and orderType == 'SELL':
                    order_id, slm_order_id, exit_order_id = placeOrderfn(
                        trnsactiontype=orderType,
                        tradingsymbol=selectedtradingsymbol,
                        quantity=quantity,
                        order_id=order_id,
                        slm_order_id=slm_order_id,
                        exit_order_id=exit_order_id,
                        exchangetype='NFO',
                        ordertype='MARKET',
                        producttype='MIS')
                    positionOnBuy = False
                    selectedtradingsymbol = None
                    #print('Sell:-\norder_ID:{0}\nslm_order_id:{1}\nexit_order_id:{2}'.format(order_id,slm_order_id,exit_order_id))
                    #htmlReqGETBot('Sell:-\order_ID:{0}\nslm_order_id:{1}\nexit_order_id:{2}'.format(order_id,slm_order_id,exit_order_id))

                    writeCurrentStatus(
                        datetime.strftime(currenttime, '%Y-%m-%d %H:%M:%S'),
                        "After selling at exit conditin.")

                elif positionOnBuy != True and orderType == 'BUY':
                    selectedtradingsymbol = selectTradingsymbol(
                        recorddf['close'].values[-1], optionType,
                        instrumentsdf)
                    print('selectedtradingsymbol:-{0}'.format(
                        selectedtradingsymbol)
                          )  #,kite.ltp("NFO:"+selectedtradingsymbol)))
                    htmlReqGETBot('selectedtradingsymbol:-{0}'.format(
                        selectedtradingsymbol)
                                  )  #,kite.ltp("NFO:"+selectedtradingsymbol)))
                    if selectedtradingsymbol != None:
                        order_id, slm_order_id, exit_order_id = placeOrderfn(
                            trnsactiontype=orderType,
                            tradingsymbol=selectedtradingsymbol,
                            quantity=quantity,
                            order_id=order_id,
                            slm_order_id=slm_order_id,
                            exit_order_id=exit_order_id,
                            exchangetype='NFO',
                            ordertype='MARKET',
                            producttype='MIS')
                        positionOnBuy = True
                        orderobj = kite.orders()
                        logging.error("order :-{0}".format(orderobj),
                                      exc_info=True)
                        htmlReqGETBot("order :-{0}".format(orderobj))

                        writeCurrentStatus(
                            datetime.strftime(currentDateTime(),
                                              '%Y-%m-%d %H:%M:%S'),
                            "After buying.")

                htmlReqGETBot("Start at -{0}".format(currenttime))
                htmlReqGETBot(
                    "SLM:-{0}\n Order:-{1}\n ExitID:-{2}\n haveCall:-{3}\n havePut:-{4}\n orderType:-{5}\n optionType:-{6}\n positionOnBuy:-{7}\n placeOrder:-{8}\n tradingsymbol:-{9}"
                    .format(slm_order_id, order_id, exit_order_id, haveCall,
                            havePut, orderType, optionType, positionOnBuy,
                            placeOrder, selectedtradingsymbol))
            else:
                pass
        except Exception as e:
            writeCurrentStatus(
                datetime.strftime(currenttime, '%Y-%m-%d %H:%M:%S'),
                "Exception in while loop")
            logging.error("Exception occurred in continous loop",
                          exc_info=True)
            #print("Exception occurred in continous loop:{0}".format(e))
            htmlReqGETBot("Exception occurred in continous loop:{0}".format(e))
            break
        time.sleep(140)
