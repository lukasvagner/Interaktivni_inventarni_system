# Interaktivní inventární systém
## Anotace:
Bylo by to sledování krabiček. Systém by měl využívat vývojovou desku Raspberry Pi Zero, na které běží webserver. Tento webserver umožní vidět, které položky chybí a kdo si je vypůjčil. 
Každá krabička by měla své místo ve skříni a bude fungovat jako šuplík. U každého šuplíku by byl umístěn senzor, pravděpodobně infračervený (IR), který by sledoval, zda je krabička na svém místě. Dále by byla RGB LED pro zobrazování stavu a navigaci, kde danou položku vrátit.
Když uživatel vyjme krabičku, bude potřebovat se přihlásit tím, že přiloží svou identifikační kartu (RFID) k čtečce, kterou běžně používá ve škole. Tato informace spolu s číslem nebo názvem krabičky bude uložena do databáze spolu s datem a časem výpůjčky.

## Hardware
Budeme používat několik komponentů:
<ol>
  <li>Mozek všeho raspberry pi zeroWH - <a href="https://rpishop.cz/raspberry-pi-zero/685-raspberry-pi-zero-wh-4250236816296.html?gad_source=1&gclid=EAIaIQobChMIn8uG2eLtggMViIKDBx0NCALqEAQYASABEgIbhfD_BwE">RPIShop</a><ul>
  <li>W značí že obsahuje čip na bezdrátové rozhraní</li>
  <li>H značí předem instalovaný header</li>
  <img src="https://rpishop.cz/2519-large_default/raspberry-pi-zero-wh.jpg" width=500px;/>
  </ul></li>
  <li>Nfc/Rfid čtečka na karty</li>
  <li>Senzor světla <ul>
    <li>Budeme nejspíš používat TCRT5000 - <a href="https://pdf1.alldatasheet.com/datasheet-pdf/download/26406/VISHAY/TCRT5000.html">DATASHEET</a></li>
    <li>používá se jako senzor ke kontrole zda jsou krabičky uloženy či nikoliv</li>
  </ul>
  </li>
  <li>Individuálně adresovatelné diody WS2812B k navigaci kam vracet krabičky<a href="https://pdf1.alldatasheet.com/datasheet-pdf/download/1179113/WORLDSEMI/WS2812B.html">DATASHEET</a> </li>
</ol>

## Progress update:
<ul>
  <li>30.11.23- Objednáno RaspberryPi Zero W</li>
  <li>15.12.23- Objední zbytku</li>
  <li>26.12.23- Funkční systém se čtečkou nfc a jedním senzorem</li>
  <li>02.01.24- Funkční systém se základním výpisem na server a psaní data logu do .txt</li>
  <li>04.01.24- Všechno přišlo</li>
  
</ul>
