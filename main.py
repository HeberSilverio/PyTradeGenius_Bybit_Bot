import config
from config import SYMBOLS
from pybit.unified_trading import HTTP
import telegramBot as tlg
import pandas as pd
from time import sleep
from binance.error import ClientError
import ta
from ta.volatility import BollingerBands


# Conexção com a conta da Bybit
session = HTTP(
    api_key=config.API_KEY,
    api_secret=config.API_SECRET
)

# Inicializando o contador
contador = 0

# Tempo gráfico para negociações
timeframe = 15 # 15 minutes

# 0.012 means +1.2%, 0.009 is -0.9%
tp = 0.03  # Take Profit +3%
sl = 0.012  # Stop Loss -1,2%
volume = 10  # volume para uma ordem (se for 10 e a alavancagem for 10, então você coloca 1 usdt em uma posição)
leverage = 10
mode = 1  # 1 - Isolated, 0 - Cross
qty = 10  # Quantidade de USDT por ordem


# Configuração do telegram
telegramBot = tlg.BotTelegram(config.TOKEN,config.CHAT_ID)
telegramBot.send_msg("=== Inicio do bot PyTradeGenius BYBIT ===")

# OBTER DADOS DA CONTA DA Bybit
def get_balance_usdt():
   try:
      resp = session.get_wallet_balance(accountType="CONTRACT", coin="USDT")['result']['list'][0]['coin'][0]['walletBalance']
      resp = float(resp)
      return resp
   except ClientError as error:
      print(
         "Erro encontrado. status: {}, código do erro: {}, mensagem do erro: {}".format(
               error.status_code, error.error_code, error.error_message
         )
      )
      telegramBot.send_msg(
         "Erro encontrado. status: código do erro: {}, mensagem do erro: {}".format(
               error.status_code, error.error_code, error.error_message
         )
      )
   

# OBTER TODOS OS PARES USDT - usdⓈ-M do arquivo config
def get_tickers():
   try:
        relevant = SYMBOLS
        symbols = []
        for symbol in relevant:
            symbols.append(symbol)
        return symbols
   except ClientError as error:
      print(
         "Erro encontrado. status: {}, código do erro: {}, mensagem do erro: {}".format(
               error.status_code, error.error_code, error.error_message
         )
      )
      telegramBot.send_msg(
         "Erro encontrado. status: código do erro: {}, mensagem do erro: {}".format(
               error.status_code, error.error_code, error.error_message
         )
      )   


# # Informe o symbol como parametros e terá as últimas 500 velas para intervalo informado
# # Função que retorna os dados do candle - é um dataframe com 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'
def klines(symbol):
   try:
      resp = session.get_kline(
         category = 'linear',
         symbol = symbol,
         interval = timeframe,
         limit = 500
      )['result']['list']
      resp = pd.DataFrame(resp)
      resp.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
      resp = resp.set_index('Time')
      resp = resp.astype(float)
      resp = resp[::-1]
      return resp
   except ClientError as error:
      print(
         "Erro encontrado. status: {}, código do erro: {}, mensagem do erro: {}".format(
               error.status_code, error.error_code, error.error_message
         )
      )
      telegramBot.send_msg(
         "Erro encontrado. status: código do erro: {}, mensagem do erro: {}".format(
               error.status_code, error.error_code, error.error_message
         )
      )

# Obtendo suas posições atuais. Retorna lista de símbolos com posições abertas
def get_positions():
   try:
      resp = session.get_positions(
         category='linear',
         settleCoin='USDT'
      )['result']['list']
      pos = []
      for elem in resp:
         pos.append(elem['symbol'])
      return pos
   except Exception as err:
      print(err)

# Getting last 50 PnL. I used it to check strategies performance
def get_pnl():
   try:
      resp = session.get_closed_pnl(category="linear", limit=50)['result']['list']
      pnl = 0
      for elem in resp:
         pnl += float(elem['closedPnl'])
      return pnl
   except Exception as err:
      print(err)

# Changing mode and leverage: 
def set_mode(symbol):
   try:
      resp = session.switch_margin_mode(
         category='linear',
         symbol=symbol,
         tradeMode=mode,
         buyLeverage=leverage,
         sellLeverage=leverage
      )
      print(resp)
   except Exception as err:
      print(err)

print('Modo isolated? :',set_mode('ADAUSDT')) # ver o modo se isolado ou cruzado

# # Funções que define a precisa de preço e quantidade
# # Função 06 - Retorna o número de dígitos decimal para preço. BTC tem 1 casa decimal, XRP tem 4 casas decimais
# Getting number of decimal digits for price and qty
def get_precisions(symbol):
   try:
      resp = session.get_instruments_info(
         category='linear',
         symbol=symbol
      )['result']['list'][0]
      price = resp['priceFilter']['tickSize']
      if '.' in price:
         price = len(price.split('.')[1])
      else:
         price = 0
      qty = resp['lotSizeFilter']['qtyStep']
      if '.' in qty:
         qty = len(qty.split('.')[1])
      else:
         qty = 0

      return price, qty
   except Exception as err:
        print(err)


# Placing order with Market price. Placing TP and SL as well
def place_order_market(symbol, side):
   price_precision = get_precisions(symbol)[0]
   qty_precision = get_precisions(symbol)[1]
   mark_price = session.get_tickers(
      category='linear',
      symbol=symbol
   )['result']['list'][0]['markPrice']
   mark_price = float(mark_price)
   print(f'Placing {side} order for {symbol}. Mark price: {mark_price}')
   order_qty = round(qty/mark_price, qty_precision)
   sleep(2)
   if side == 'buy':
      try:
         tp_price = round(mark_price + mark_price * tp, price_precision)
         sl_price = round(mark_price - mark_price * sl, price_precision)
         resp = session.place_order(
               category='linear',
               symbol=symbol,
               side='Buy',
               orderType='Market',
               qty=order_qty,
               takeProfit=tp_price,
               stopLoss=sl_price,
               tpTriggerBy='Market',
               slTriggerBy='Market'
         )
         print(resp)
      except Exception as err:
         print(err)

   if side == 'sell':
      try:
         tp_price = round(mark_price - mark_price * tp, price_precision)
         sl_price = round(mark_price + mark_price * sl, price_precision)
         resp = session.place_order(
               category='linear',
               symbol=symbol,
               side='Sell',
               orderType='Market',
               qty=order_qty,
               takeProfit=tp_price,
               stopLoss=sl_price,
               tpTriggerBy='Market',
               slTriggerBy='Market'
         )
         print(resp)
      except Exception as err:
         print(err)


def bollinger_signal(symbol):
   
   # Obtendo os dados das velas para o símbolo fornecido
   kl = klines(symbol)
   
   # Calculando as bandas de Bollinger com período 21 e desvio padrão 3
   bb = ta.volatility.BollingerBands(close=kl.Close, window=21, window_dev=3)
   
   # Obtendo os valores das bandas superior e inferior
   upper_band = bb.bollinger_hband()
   lower_band = bb.bollinger_lband()
   
   # Verificando se a mínima do candle está abaixo da banda inferior
   if kl.Low.iloc[-1] < lower_band.iloc[-1]:
      telegramBot.send_msg("=== *COMPRAR {}* ===".format(symbol)
         +"\n🛤️ *Mínima *ABAIXO* da banda inferior* 🛤️"
         +"\nFechou ABAIXO da Bollinger"                
         +"\nBollinger Inferior..........."+str(format(float(lower_band.iloc[-1]),'.6f'))
         +"\n*Mínima*........................"+str(format(float(kl.Low.iloc[-1]),'.6f')))
      return 'up'
   
   # Verificando se a máxima do candle está acima da banda superior
   elif kl.High.iloc[-1] > upper_band.iloc[-1]:
      telegramBot.send_msg("=== *VENDER {}* ===".format(symbol)
         +"\n♨️Máxima *ACIMA* da Bollinger ♨️"
         +"\nBollinger Superior......."+str(format(float(upper_band.iloc[-1]),'.5f'))
         +"\n*Máxima*....................."+str(format(float(kl.High.iloc[-1]),'.5f')))
      return 'down'
      
   
   # Se não ultrapassar as bandas
   else:
      return 'none'
   
 
# Obter séries de fechamentos de candle
def get_close_low_series(symbol):
   # Obtendo os dados históricos dos candles
   kl = klines(symbol)
   # Obtendo as séries de close e low
   close_series = kl['Close']
   low_series = kl['Low']
   return close_series, low_series
   
# Cruzamento de médias
def cruzandoMedias(close_series, low_series, symbol):
   # Calculando as médias móveis simples para os três períodos diferentes e sources diferentes
   sma_34_close = ta.trend.sma_indicator(close_series, window=34, fillna=False)
   sma_12_low = ta.trend.sma_indicator(low_series, window=12, fillna=False)
   sma_7_close = ta.trend.sma_indicator(close_series, window=7, fillna=False)

   # Verificando a inclinação da média de 34 períodos
   if sma_34_close.iloc[-1] > sma_34_close.iloc[-2] > sma_34_close.iloc[-3] > sma_34_close.iloc[-4]:
      inclinacao_34 = 'up'
   elif sma_34_close.iloc[-1] < sma_34_close.iloc[-2] < sma_34_close.iloc[-3] < sma_34_close.iloc[-4]:
      inclinacao_34 = 'down'
   else:
      inclinacao_34 = 'none'

   # Verificando as condições para os cruzamentos das médias
   if sma_7_close.iloc[-3] < sma_12_low.iloc[-3] and sma_7_close.iloc[-1] > sma_12_low.iloc[-1]:
      # Cruzamento de alta
      if inclinacao_34 == 'up':
         telegramBot.send_msg("🟢 === *COMPRAR {}* ===".format(symbol) +
                              "\n💹 Cruzamento de alta 💹")
         return 'up'
   elif sma_7_close.iloc[-3] > sma_12_low.iloc[-3] and sma_7_close.iloc[-1] < sma_12_low.iloc[-1]:
      # Cruzamento de baixa
      if inclinacao_34 == 'down':
         telegramBot.send_msg("🔴 === *VENDER {}* ===".format(symbol) +
                              "\n♨️ Cruzamento de baixa ♨️")
         return 'down'
      
   else:
      # telegramBot.send_msg("🟡 Sem cruzamento 🟡 {}".format(symbol))
      return 'none'



max_pos = 5    # Max current orders
symbols = get_tickers()     # getting all symbols from the Bybit Derivatives
while True:
   # precisamos obter equilíbrio para verificar se a conexão está boa ou se você tem todas as permissões necessárias
   balance = get_balance_usdt()
   sleep(1)
   if balance == None:
      print('Não consigo conectar à API. Verifique IP, restrições ou espere algum tempo')
      telegramBot.send_msg("Não foi possível conectar à API. Verifique IP, restrições ou espere algum tempo")
   if balance != None:
      print("Meu saldo é: ", balance, " USDT")
      telegramBot.send_msg("Saldo Conta de Futuros: $"+str(balance) +" USDT")
      
      positions = get_positions()
      print(f'Você tem {positions} posições abertas')
      telegramBot.send_msg("Você tem {} posições abertas".format(positions))
      
      if len(positions) < max_pos:
            # Checking every symbol from the symbols list:
            for elem in symbols:
               positions = get_positions()
               if len(positions) >= max_pos:
                  break
               
               # Verificando se já existe uma posição aberta para o símbolo atual
               if elem not in positions:
                  
                  # Obtendo as séries de close e low para o símbolo atual
                  close_series, low_series = get_close_low_series(elem)
                  
                  # Sinal para comprar ou vender com base nos indicadores
                  signal1 = bollinger_signal(elem)
                  # print("Sinal1: ",signal1)
                  signal2 = cruzandoMedias(close_series, low_series, elem)
                  #print("Sinal2: ",signal2)
                 
                  # Se houver um sinal válido em signal2, envie uma ordem com base nele
                  if signal2 != 'none':
                     if signal2 == 'up':
                           print('Enviando ordem de COMPRA para ', elem, 'com base em cruzandoMedias')
                           telegramBot.send_msg("Enviando ordem de COMPRA com base em cruzandoMedias para " + str(elem))
                           set_mode(elem)
                           sleep(2)
                           place_order_market(elem, 'buy')
                           sleep(5)
                     elif signal2 == 'down':
                           print('Enviando ordem de VENDA para ', elem, 'com base em cruzandoMedias')
                           telegramBot.send_msg("Enviando ordem de VENDA com base em cruzandoMedias para " + str(elem))
                           set_mode(elem)
                           sleep(2)
                           place_order_market(elem, 'sell')
                           sleep(5)
                  # Se não houver sinal válido em signal2, verifique signal1
                  else:
                     if signal1 != 'none':
                           if signal1 == 'up':
                              print('Enviando ordem de COMPRA para ', elem, 'com base em bollinger_signal')
                              telegramBot.send_msg("Enviando ordem de COMPRA com base em bollinger_signal para " + str(elem))
                              set_mode(elem)
                              sleep(2)
                              place_order_market(elem, 'buy')
                              sleep(5)
                           elif signal1 == 'down':
                              print('Enviando ordem de VENDA para ', elem, 'com base em bollinger_signal')
                              telegramBot.send_msg("Enviando ordem de VENDA com base em bollinger_signal para " + str(elem))
                              set_mode(elem)
                              sleep(2)
                              place_order_market(elem, 'sell')
                              sleep(5)
   
   print('Esperar 60 segundos')
   sleep(60)