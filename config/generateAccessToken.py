from kiteconnect import KiteConnect
from configLogin import api_key,api_secret

kite = KiteConnect(api_key = api_key)
print('click on below link and login into your Zerodha account to creat request_token')
print(kite.login_url())
#after login copy the request_token from url and paste it 
request_token = input('request_token :')
data = kite.generate_session(request_token,api_secret=api_secret)

with open('access_token.txt','w') as ak:
  ak.write(data['access_token'])
  
# access_token is valid for 24hrs only, you have to generate access_token again after that.