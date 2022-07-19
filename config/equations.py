
class mytalib():
    def SUPERTREND(self,srcHigh,srcLow,srcClose,length,multiplier):
        # common length and multiplier
        # length=5
        # multiplier=4
        trueRange=[0]
        ATR=[0]*length
        BasicUpperband=[0]*length
        BasicLowerband=[0]*length
        FinalUpperband=[0]*length
        FinalLowerband=[0]*length
        trend=[0]*length

        supertrend=[0]*length
        # base on typy of Supertrend comments/uncomments below lines
        
        #alph=2/(1+length) # for ATR(EMA)
        beta=1/length # for ATR(wilder)

        for x in range(1,length):
            trueRange.append(max(srcHigh[x]-srcLow[x],abs(srcHigh[x]-srcClose[x-1]),abs(srcLow[x]-srcClose[x-1])))
        for x in range(length,srcClose.size):
            trueRange.append(max(srcHigh[x]-srcLow[x],abs(srcHigh[x]-srcClose[x-1]),abs(srcLow[x]-srcClose[x-1])))


            #ATR.append(sum(trueRange[-length:])/length) SMA
            
            if x==length:
                ATR.append(sum(trueRange[-length:])/length)
            else:
                #ATR.append(trueRange[x]*alph+ATR[x-1]*(1-alph)) #ATR==EMA
                ATR.append(trueRange[x]*beta+ATR[x-1]*(1-beta))  #ATR(WILDER)    
            #CALCULATE ATR SL(CLOSE)
            #upperATRClose=srcClose[x]+ATR[x]*multiplier 
            #lowerATRClose=srcClose[x]-ATR[x]*multiplier

            #ATR SL(HIGH/LOW)
            #upperATRlow=srcLow[x]+ATR[x]*multiplier
            #lowerATRhigh=srcHigh[x]-ATR[x]*multiplier

            #ATR upperSupertrend
            upperSupertrend=(srcHigh[x]+srcLow[x])/2+ATR[x]*multiplier
            lowerSupertrend=(srcHigh[x]+srcLow[x])/2-ATR[x]*multiplier

            BasicUpperband.append(upperSupertrend) #upperATRlow or upperATRClose
            BasicLowerband.append(lowerSupertrend) #lowerATRhigh or lowerATRClose


            if(BasicUpperband[x]<FinalUpperband[x-1] or srcClose[x-1]>FinalUpperband[x-1]):
                FinalUpperband.append(BasicUpperband[x])
            else:
                FinalUpperband.append(FinalUpperband[x-1])

            if(BasicLowerband[x]>FinalLowerband[x-1] or srcClose[x-1]<FinalLowerband[x-1]):
                FinalLowerband.append(BasicLowerband[x])
            else:
                FinalLowerband.append(FinalLowerband[x-1])

            if (supertrend[x-1]==FinalUpperband[x-1] and srcClose[x]<=FinalUpperband[x]):
                supertrend.append(FinalUpperband[x])
            elif(supertrend[x-1]==FinalUpperband[x-1] and srcClose[x]>=FinalUpperband[x]):
                supertrend.append(FinalLowerband[x])
            elif(supertrend[x-1]==FinalLowerband[x-1] and srcClose[x]>=FinalLowerband[x]):
                supertrend.append(FinalLowerband[x])
            elif(supertrend[x-1]==FinalLowerband[x-1] and srcClose[x]<=FinalLowerband[x]):
                supertrend.append(FinalUpperband[x])  
            else:
                pass
            if srcClose[x]<supertrend[x]:
                trend.append(-1) #-1 sell
            else:
                trend.append(1) #1 buy
        return supertrend,trend

    def CMO(self,src,length):
        parray=[0]
        narray=[0]
        cmo=[0]*length
        for x in range(1,length):
            change=src[x]-src[x-1]
            if change>0:
                parray.append(change)
                narray.append(0)
            else:
                parray.append(0)
                narray.append(change*-1)
        for x in range(length,src.size):
            change=src[x]-src[x-1]
            if change>0:
                parray.append(change)
                narray.append(0)
            else:
                parray.append(0)
                narray.append(change*-1)
            cmo.append((sum(parray[-length:])-sum(narray[-length:]))/(sum(parray[-length:])+sum(narray[-length:]))*100)
        return cmo

    def rsi(self,srcClose,length):
        gain=[0]
        loss=[0]
        avgGain=0
        avgLoss=0
        strength=0
        rsi=[0]*(length)
        def assignGainAndLoss(src,y):
            change=src[y]-src[y-1]
            if change>0:
                gain.append(change)
                loss.append(0)
            elif change<0:
                loss.append(change*-1)
                gain.append(0)
            else:
                gain.append(change)
                loss.append(change)

        for x in range(1,length):
            assignGainAndLoss(srcClose,x)

        assignGainAndLoss(srcClose,length)
        avgGain=sum(gain)/length
        avgLoss=sum(loss)/length
        strength=avgGain/avgLoss
        if(avgLoss==0):
            rsi.append(100)
        else:
            rsi.append((100-(100/(1+strength))))
        for x in range(length+1,srcClose.size):
            assignGainAndLoss(srcClose,x)
            avgGain=(avgGain*13+gain[x])/length
            avgLoss=(avgLoss*13+loss[x])/length
            strength=avgGain/avgLoss

            if(avgLoss==0):
                rsi.append(100)
            else:
                rsi.append((100-(100/(1+strength))))

        return rsi

    def convert2HeikinAshi(self,data):
        haData=data.copy()
        index1=data.index[0]
        prvOpen=data.loc[index1,'open']
        prvClose=data.loc[index1,'close']
        for x in haData.index[1:]:
            haData.loc[x,'close']=(haData.loc[x,'open']+haData.loc[x,'close']+haData.loc[x,'high']+haData.loc[x,'low'])/4    
            haData.loc[x,'open']=(prvOpen+prvClose)/2
            haData.loc[x,'high']=max(haData.loc[x,'open'],haData.loc[x,'close'],haData.loc[x,'high'])
            haData.loc[x,'low']=min(haData.loc[x,'open'],haData.loc[x,'close'],haData.loc[x,'low'])
            prvOpen=haData.loc[x,'open']
            prvClose=haData.loc[x,'close']
        return haData


