import config
from config import SYMBOLS
from pybit.unified_trading import HTTP
import telegramBot as tlg
import pandas as pd
from time import sleep
from binance.error import ClientError
import ta
from ta.volatility import BollingerBands
import datetime
from pybit.unified_trading import HTTP

# Conexção com a conta da Bybit
session = HTTP(
    api_key=config.API_KEY,
    api_secret=config.API_SECRET
)

# Inicializando o contador
contador = 0

#Define data e hora atuais
data_e_hora_atuais = datetime.datetime.now()
data_e_hora_em_texto = data_e_hora_atuais.strftime('%d/%m/%Y - %Hh:%Mm') 


timeframe = 60 # 15 minutes # Tempo gráfico para negociações
tp = 0.1  # Take Profit +10%
sl = 0.03  # Stop Loss -3%
volume = 10  # volume para uma ordem (se for 10 e a alavancagem for 10, então você coloca 1 usdt em uma posição)
leverage = 10
mode = 1  # 1 - Isolated, 0 - Cross
qty = 15  # Quantidade de USDT por ordem


# Configuração do telegram
telegramBot = tlg.BotTelegram(config.TOKEN,config.CHAT_ID)



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
   except ClientError as error:
      print(
         "Erro encontrado. status: {}, código do erro: {}, mensagem do erro: {}".format(
               error.status_code, error.error_code, error.error_message
         )
      )
   # except Exception as err:
      # print(err)
      # print("Erro encontrado na função get_positions: {}".format(err))

# Getting last 50 PnL. I used it to check strategies performance
def get_pnl():
   try:
      resp = session.get_closed_pnl(category="linear", limit=50)['result']['list']
      pnl = 0
      for elem in resp:
         pnl += float(elem['closedPnl'])
      return pnl
   except ClientError as error:
      print(
         "Erro encontrado. status: {}, código do erro: {}, mensagem do erro: {}".format(
               error.status_code, error.error_code, error.error_message
         )
      )
   # except Exception as err:
   #    print(err)

# Alterando modo e alavancagem:
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
   except ClientError as error:
      print(
         "Erro encontrado. status: {}, código do erro: {}, mensagem do erro: {}".format(
               error.status_code, error.error_code, error.error_message
         )
      )

# Definir as variáveis globalmente ou em um escopo superior
global_order_data = {}
# Fazer pedido com preço de mercado. Colocando TP e SL também
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
         +"\n🟢 *Mínima ABAIXO da banda inferior*"
         +"\n"                
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
      print("lateral= "+str(symbol))
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
   sma_14_low = ta.trend.sma_indicator(low_series, window=14, fillna=False)
   sma_7_close = ta.trend.sma_indicator(close_series, window=7, fillna=False)

   # Verificando a inclinação da média de 34 períodos
   if sma_34_close.iloc[-1] > sma_34_close.iloc[-2] > sma_34_close.iloc[-3] > sma_34_close.iloc[-4]:
      inclinacao_34 = 'up'
   elif sma_34_close.iloc[-1] < sma_34_close.iloc[-2] < sma_34_close.iloc[-3] < sma_34_close.iloc[-4]:
      inclinacao_34 = 'down'
   else:
      inclinacao_34 = 'none'

   # Verificando as condições para os cruzamentos das médias
   if sma_7_close.iloc[-3] < sma_14_low.iloc[-3] and sma_7_close.iloc[-1] > sma_14_low.iloc[-1]:
      # Cruzamento de alta
      if inclinacao_34 == 'up':
         telegramBot.send_msg("🟢 === *COMPRAR {}* ===".format(symbol) +
                              "\n💹 Cruzamento de alta 💹")
         return 'up'
   elif sma_7_close.iloc[-3] > sma_14_low.iloc[-3] and sma_7_close.iloc[-1] < sma_14_low.iloc[-1]:
      # Cruzamento de baixa
      if inclinacao_34 == 'down':
         telegramBot.send_msg("🔴 === *VENDER {}* ===".format(symbol) +
                              "\n♨️ Cruzamento de baixa ♨️")
         return 'down'
      
   else:
      # telegramBot.send_msg("🟡 Sem cruzamento 🟡 {}".format(symbol))
      return 'none'

# Função para verificar se volume é 3x maior que os últimos 20
def average_volume(data):
   # Calcula a média dos volumes dos últimos 20 candles
   last_20_volumes = data['Volume'].iloc[-20:]
   average = last_20_volumes.mean()
   return average



def is_volume_3x_higher(symbol):
   try:
      # Obter os dados do candle
      candle_data = klines(symbol)
      
      # Obter o volume do candle atual
      current_volume = candle_data.iloc[-1]['Volume']
      
      # Obter a média dos volumes dos últimos 20 candles
      avg_volume = average_volume(candle_data)
      
      # Verificar se o volume atual é 3x maior que a média
      if current_volume >= 3 * avg_volume:
         return True
      else:
         return False
   except Exception as e:
      print("Erro ao verificar o volume:", e)
      return False



#configurações da primeira mensagem
balance = get_balance_usdt()
sleep(1)      
telegramBot.send_msg("=== 𝐈𝐍𝐈𝐂𝐈𝐎 𝐃𝐎 𝐁𝐎𝐓 ==="
                     +"\n𝐏𝐲𝐓𝐫𝐚𝐝𝐞𝐆𝐞𝐧𝐢𝐮𝐬 🅱🆈🅱🅸🆃"
                     +"\n\n"
                     +"\nTIME:  " + data_e_hora_em_texto 
                     +"\n𝗦𝗔𝗟𝗗𝗢 𝗗𝗔 𝗖𝗢𝗡𝗧𝗔: $"+str(format(float(balance),'.2f')) +" USDT"
                     +"\n*Tempo Gráfico: {}*".format(timeframe))

max_pos = 15    # Max current orders
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
      # telegramBot.send_msg("Saldo Conta de Futuros: $"+str(balance) +" USDT")
      
      positions = get_positions()
      print(f'Você tem '+str(len(positions)), "posições abertas")
      for coin in positions:
         print(f'Você tem posição aberta em: {coin}')
         
         response_data = session.get_positions(category="inverse",symbol=coin,)
         # print(response_data)
         # Dados da primeira posição da lista
         position_data = response_data['result']['list'][0]
         
         # Atribuir os valores às variáveis
         CoinName = position_data['symbol']
         HorarioDeEnvio = position_data['createdTime']  # Timestamp em milissegundos
         Lado = position_data['side']
         TamanhoEmDolar = position_data['positionValue']
         QtyMoedas = position_data['size']
         precoEntrada = position_data['avgPrice']
         PrecoAtual = position_data['markPrice']
         TakeProfit = position_data['takeProfit']
         StopLoss = position_data['stopLoss']
         PrecoLiquidacao = position_data['liqPrice']
         PositionMargin = position_data['positionBalance']
         Lucro = position_data['unrealisedPnl']
         HorarioAtual = position_data['updatedTime']  # Timestamp em milissegundos
         
         # Convertendo os timestamps para valores legíveis
         created_timestamp = int(HorarioDeEnvio) / 1000  # Dividindo por 1000 para converter para segundos
         updated_timestamp = int(HorarioAtual) / 1000
         
         created_time = datetime.datetime.fromtimestamp(created_timestamp).strftime('%d/%m/%Y - %Hh:%Mm')
         updated_time = datetime.datetime.fromtimestamp(updated_timestamp).strftime('%d/%m/%Y - %Hh:%Mm')
         
         # Exibir os valores das variáveis
         # print("Coin Name:", CoinName)
         # print("Lado:", Lado)
         # print("Tamanho em Dólar:", TamanhoEmDolar)
         # print("Quantidade de Moedas:", QtyMoedas)
         # print("Preço de Entrada:", precoEntrada)
         # print("Preço Atual:", PrecoAtual)
         # print("Preço de Liquidação:", PrecoLiquidacao)
         # print("Margem da Posição:", PositionMargin)
         # print("Lucro:", Lucro)
         telegramBot.send_msg("🅿🅞🆂🅸🆃🅸🅞🅽 🅸🅽🅵🅞🆁🅼🅐🆃🅸🅞🅽"
                              +"\n"
                              +"\n𝗖𝗼𝗶𝗻 𝗡𝗮𝗺𝗲: "+ str(CoinName) # Nome da moeda
                              +"\n𝗜𝗻𝗶𝗰𝗶𝗼𝘂: " + created_time # O momento exato que a função foi chamada e que não se repete
                              +"\n𝗤𝘂𝗮𝗻𝘁𝗶𝗱𝗮𝗱𝗲 𝗱𝗲 𝗺𝗼𝗲𝗱𝗮𝘀: "+str(QtyMoedas)
                              +"\n𝗧𝗮𝗺𝗮𝗻𝗵𝗼 𝗱𝗮 𝗽𝗼𝘀𝗶𝗰̧𝗮̃𝗼: $"+str(format(float(TamanhoEmDolar),'.2f'))
                              +"\n𝗟𝗮𝗱𝗼: "+ Lado 
                              +"\n𝗩𝗟𝗥 𝗲𝗻𝘁𝗿𝗮𝗱𝗮:."+str(precoEntrada) # O preço de entrada, o valor da compra
                              +"\n𝗣𝗿𝗲𝗰̧𝗼 𝗮𝘁𝘂𝗮𝗹:.."+str(format(float(PrecoAtual),'.4f'))
                              +"\n𝗧𝗮𝗸𝗲 𝗣𝗿𝗼𝗳𝗶𝘁:.."+str(format(float(TakeProfit),'.4f')) # Take profit, o valor da ordem de lucro
                              +"\n𝗦𝘁𝗼𝗽 𝗹𝗼𝘀𝘀:....."+str(format(float(StopLoss),'.4f'))  # Stop loss, o valor da ordem de prejuízo máximo 
                              +"\n𝗣𝗿𝗲𝗰̧𝗼 𝗱𝗲 𝗟𝗶𝗾𝘂𝗶𝗱𝗮𝗰̧𝗮̃𝗼: "+str(PrecoLiquidacao)  # Stop loss, o valor da ordem de prejuízo máximo 
                              +"\n𝗠𝗮𝗿𝗴𝗲𝗺 𝗱𝗮 𝗣𝗼𝘀𝗶𝗰̧𝗮̃𝗼: "+str(format(float(PositionMargin),'.2f'))  # Stop loss, o valor da ordem de prejuízo máximo 
                              +"\n𝗣&𝗟 (%): "+str(format(float(Lucro),'.2f'))) 
         
      if len(positions) < max_pos:
            # Checking every symbol from the symbols list:
            for elem in symbols:
               positions = get_positions()
               if len(positions) >= max_pos:
                  break
               
               
               # Obter os dados do candle
               candle_data = klines(elem)
               # Obter o volume do candle atual
               current_volume = candle_data.iloc[-1]['Volume']
               # Obter a média dos volumes dos últimos 20 candles
               avg_volume = average_volume(candle_data)
               
               # Exemplo de uso
               if is_volume_3x_higher(elem):
                  print("O volume do candle atual é 3x maior que a média dos últimos 20 candles.")
                  telegramBot.send_msg("🟢 𝗩𝗢𝗟𝗨𝗠𝗘 𝗚𝗥𝗔𝗡𝗗𝗘 🟢"
                                       +"\nO volume do candle atual é 3x maior que a média dos últimos 20 candles."
                                       +"\n𝗠𝗼𝗲𝗱𝗮: "+str(elem)
                                       +"\nVolume da barra........: "+str(format(float(current_volume),'.0f'))
                                       +"\nMédia de 20 volumes: "+str(format(float(avg_volume),'0f')))
               
               # Volume acima da média
               if current_volume > avg_volume:
                  print("O volume do candle atual é 3x maior que a média dos últimos 20 candles.")
                  telegramBot.send_msg("🥎 *Volume acima da média* 🥎"
                                       +"\n𝗠𝗼𝗲𝗱𝗮: "+str(elem)
                                       +"\nVolume da barra........: "+str(format(float(current_volume),'.0f'))
                                       +"\nMédia de 20 volumes: "+str(format(float(avg_volume),'0f')))   
               
               
               # Verificando se já existe uma posição aberta para o símbolo atual
               if elem not in positions:
                  
                  # Obtendo as séries de close e low para o símbolo atual
                  close_series, low_series = get_close_low_series(elem)
                  
                  # Sinal para comprar ou vender com base nos indicadores
                  signal1 = bollinger_signal(elem)
                  # print("Sinal1: ",signal1)
                  signal2 = cruzandoMedias(close_series, low_series, elem)
                  # print("Sinal2: ",signal2)
                 
                  # Se houver um sinal válido em signal2, envie uma ordem com base nele
                  if signal2 != 'none':
                     if signal2 == 'up':
                           print('Enviando ordem de COMPRA para', elem, 'com base em cruzandoMedias')
                           # telegramBot.send_msg("Enviando ordem de COMPRA com base em cruzandoMedias para " + str(elem))
                           set_mode(elem)
                           telegramBot.send_msg("COMPRA enviada Status= OK"
                                                +"\n-----------------------------------")
                           sleep(2)
                           place_order_market(elem, 'buy')
                           sleep(5)
                     elif signal2 == 'down':
                           print('Enviando ordem de VENDA para ', elem, 'com base em cruzandoMedias')
                           # telegramBot.send_msg("Enviando ordem de VENDA com base em cruzandoMedias para " + str(elem))
                           set_mode(elem)
                           telegramBot.send_msg("Ordem de VENDA envida Status= OK"
                                                +"\n-----------------------------------")
                           sleep(2)
                           place_order_market(elem, 'sell')
                           sleep(5)
                  # Se não houver sinal válido em signal2, verifique signal1
                  else:
                     if signal1 != 'none':
                           if signal1 == 'up':
                              print('Enviando ordem de COMPRA para ', elem, 'com base em bollinger_signal')
                              # telegramBot.send_msg("Enviando ordem de COMPRA com base em bollinger_signal para " + str(elem))
                              set_mode(elem)
                              telegramBot.send_msg("COMPRA envida Status= OK"
                                                   +"\n-----------------------------------")
                              sleep(2)
                              place_order_market(elem, 'buy')
                              sleep(5)
                           elif signal1 == 'down':
                              print('Enviando ordem de VENDA para ', elem, 'com base em bollinger_signal')
                              # telegramBot.send_msg("Enviando ordem de VENDA com base em bollinger_signal para " + str(elem))
                              set_mode(elem)
                              telegramBot.send_msg("Ordem de VENDA envida Status= OK"
                                                   +"\n-----------------------------------")
                              sleep(2)
                              place_order_market(elem, 'sell')
                              sleep(5)
   
   print('Esperar 15 minutos')
   sleep(900)