# Robô de trader Bybit com envio de ordens - e com o sistema de envio de mensagens no telegram

O robô de sinais **PyTradeGenius_Bybit_Bot** realiza o monitoramento dos **Múltiplos** pares de criptomoedas e envia mensagens de alertas via **Telegram**. Com diversos indicadores e tempos gráficos customizavéis, é uma excelente opção para quem quer ficar por dentro das oportunidades e regiões de preços importantes.

## Referências

### Imagem do grupo do telegram
<div align="center">
<img src ="https://raw.githubusercontent.com/HeberSilverio/PyTradeGenius_Bybit_Bot/main/img/imageTelegram.JPG" alt="Image" style="max-width: 40%;">
</div>

## ⌨️ Como executar o projeto
```* Clonando o repositório
git clone https://github.com/HeberSilverio/PyTradeGenius_Bybit_Bot.git


# Execute o arquivo python com o comando
`python main.py`
```

## Autor
Desenvolvido por **Héber Silvério** </br>
<a href="https://www.linkedin.com/in/hebersilverio/" rel="nofollow" target="_blank"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="Linkedin Badge" data-canonical-src="https://img.shields.io/badge/linkedin-%230077B5.svg?&amp;style=for-the-badge&amp;logo=linkedin&amp;logoColor=white&amp;link=https://www.linkedin.com/in/hebersilverio/" style="max-width:100%;"></a></br>
👋 Fique a vontade para se conectar

</br></br>

# 📋 Índice

*  <a href="https://github.com/HeberSilverio/PyTradeGenius_Bin_Bot?tab=readme-ov-file#manual-de-utiliza%C3%A7%C3%A3o" rel="nofollow" target="_blank">Manual de utilização</a>
*  <a href="https://github.com/HeberSilverio/PyTradeGenius_Bin_Bot?tab=readme-ov-file#links-%C3%BAteis" rel="nofollow" target="_blank">Links úteis</a>
*  <a href="https://github.com/HeberSilverio/PyTradeGenius_Bin_Bot?tab=readme-ov-file#manual-de-desenvolvimento" rel="nofollow" target="_blank">Manual de Desenvolvimento</a>


## **MANUAL DE UTILIZAÇÃO**

No arquivo **"config.py"** deverá ser inserida a **API_KEY** da sua conta Bybit juntamente de sua senha **API_ SECRET**. Ambos podem ser obtidos nas configurações da sua conta Bybit, adentrando na opção **API Management**.
<div align="center">
<img src = "https://raw.githubusercontent.com/HeberSilverio/PyHbSinais/main/img/secrets.png">
</div>

</br>
Ainda no arquivo **"config.py"**, para inserir o **TOKEN** é necessário criar um bot no Telegram utilizando o canal **BotFather**:
<div align="center">
<img src = "https://raw.githubusercontent.com/HeberSilverio/PyHbSinais/main/img/botfather.png" alt="Image" height="350" width="300">
</div>
  
Para capturar o **CHAT_ID**, basta enviar uma mensagem através do telegram ou realizar qualquer alteração no grupo.
Em seguida, utilize esta url https://api.telegram.org/botTOKEN/getUpdates e substitua o **TOKEN**. 
O número do Chat_Id aparece na string: {"message_id":xxx,"from":{"id":**Número ID**.

</br></br>

## Links úteis 

### Vídeo Tutorial do projeto no youtube
<a target="_blank" rel="noopener noreferrer" href="gif do vídeo">
    <img src="https://raw.githubusercontent.com/HeberSilverio/PyTradeGenius_Bin_Bot/main/img/print_video.JPG" alt="Print Video" style="max-width: 40%;">
</a> </br>

* <a href="https://youtu.be/YVnu7aSMaCM?si=mwc2suq6GYSAH8R0" rel="nofollow" target="_blank">Link do video tutorial</a> 

</br></br>

### Repositório GitHub - Bybit
<a target="_blank" rel="noopener noreferrer" href="gif do vídeo">
    <img src="" alt="Repositorio Bybit" style="max-width: 40%;">
</a> </br>

*  <a href="" target="_blank">Api da Bybit</a> 

</br></br>



## **MANUAL DE DESENVOLVIMENTO**
Inicie seu projeto instalando as bibliotecas necessárias
É necessário instalar a biblioteca da Pybit. Digite no terminal: 

`pip install pybit`

Instale a biblioteca Pandas
`pip install pandas`

Instale a biblioteca de indicadores TA
`pip install ta`


### Foi sugerido utilizar esta biblioteca de indicadores - Biblioteca de análise técnica em python 

<a target="_blank" rel="noopener noreferrer" href="gif do vídeo">
    <img src="https://raw.githubusercontent.com/HeberSilverio/PyTradeGenius_Bin_Bot/main/img/biblioteca%20de%20indicadores%20python.JPG" alt="Biblioteca de indicadores" style="max-width: 20%;">
</a> </br>

*  <a href="https://github.com/binance/binance-futures-connector-python/tree/main/examples/um_futures/trade" rel="nofollow" target="_blank">Biblioteca de análise técnica em python</a> 


**Esta enviando ordens corretamente**
CORREÇÕES
* Não está colocando ordens cruzadas
* Está aumentando a posição se o candle ainda não fechou
* Enviar no telegram as os lucros das posições em aberto