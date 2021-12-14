
import os
from typing import List
import requests
from bs4 import BeautifulSoup
from time import sleep, time, localtime, strftime
import json

from datetime import date, datetime
from pytz import timezone

saoPauloTimezone = timezone('America/Sao_Paulo')

websites = {
   'nova': 'https://cdn2.uso.com.br/sites/logos/47735.png',
   'natureza': 'https://img.buscaimoveis.com/fotos/logo/png/210.png',
   'novapetropolis': 'https://imgs.kenlo.io/VWRCUkQ2Tnp3d1BJRDBJVe1s0xgxSbBGOsBT9+RO1zjks-ynciLnlXpdKzsuCVZKPvMZhGt-GI0v+QFtypVh7xY3icsFUfjn5XDehcKoyvKw6mCx17Tqnov84vjeYOqZkIsy2KSjTwL9vvU4H40sYkt1auMjGxCzAd3ebCQK-WnJrEHKRfECCXMfjV5qhQ==.png'
}

IMMOBILE_FILE = "./immobiles.json"

def jsonToImmobile(obj: dict):
   im = Immobile()
   im.images        = obj['images']
   im.title         = obj['title']
   im.localization  = obj['localization']
   im.description   = obj['description'] if 'description' in obj else ""
   im.link          = obj['link']
   im.details       = obj['details']
   im.prices        = obj['prices']
   im.website       = obj['website']
   im.inclusionDate = obj['inclusionDate']
   return im

class Immobile:
   images        = []
   title         = ""
   localization  = ""
   description   = ""
   link          = ""
   details       = ""
   prices        = ""
   website       = ""
   inclusionDate = 0
   
   def toJSON(self):
      return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=3)

Immobile.fromJSON = staticmethod(jsonToImmobile)

immobiles = []

def loadFromNovaPetropolis(immobiles: List[Immobile]):
   
   headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
   data = requests.get("https://www.imobiliarianovapetropolis.com.br/imoveis/para-alugar/apartamento/nova-petropolis", headers=headers)
   
   soup = BeautifulSoup(data.text, 'html.parser')

   results = soup.find('div', class_="listing-results")
   
   for result in results:
      
      images  = result.find_all("div", class_="card-img-top")
      prices  = ""
      
      left = result.find("div", class_='info-left')
      if left:
         prices = list(left.children)[-1].text
      
      right = result.find("div", class_='info-right')
      if right:
         prices += " | " + right.getText(separator=" ")
      
      immobile = Immobile()
      immobile.title = result.find("h3", class_="card-text").text
      immobile.localization = result.find("h2", class_="card-title").text
      immobile.description = result.find("p", class_="description").text
      immobile.details = " | ".join([ ( val.p.span.text + " " + val.p.find(text=True, recursive=False) ) for val in result.find("div", class_="values") ])
      immobile.prices = prices
      immobile.images = [ img['data-src'] for img in images ]
      immobile.link = "https://www.imobiliarianovapetropolis.com.br" + result.find('a')['href']
      immobile.website = "novapetropolis"
      
      immobiles.append(immobile)
   

def loadFromNaturezaimoveis(immobiles: List[Immobile]):
   
   data = requests.get("https://www.naturezaimoveis.com.br/busca?estado=2&cidade=18&bairro=&valor-min=&valor-max=&operacao=locacao&tipo-imovel=6&dormitorios=&area-min=&area-max=&page=1")
   
   soup = BeautifulSoup(data.text, 'html.parser')
   
   immobilesDivs = soup.find_all("a", {"class": "imovel"})	

   for immobileDiv in immobilesDivs:
      
      details = ""
      for index, obj in enumerate(immobileDiv.find_all("div", {"class": "objeto"})):
         
         if details != "":
            details += " | "

         if index == 0:
            details += obj.text + " dormitorios"
         elif index == 1:
            details += obj.text + " banheiros"
         elif index == 2:
            details += obj.text + " vagas"
      
      immobile = Immobile()
      immobile.title = immobileDiv.find("h3").text
      immobile.localization = immobileDiv.find("div", class_="info").text.strip()
      # immobile.description = description
      immobile.details = details
      immobile.prices = immobileDiv.find("div", class_="objeto-valor").text
      immobile.images = [ immobileDiv.find("img")["src"] ]
      immobile.link = immobileDiv['href']
      immobile.website = "natureza"

      immobiles.append(immobile)
   

def loadFromNovaImoveis(immobiles: List[Immobile]):
   
   data = requests.get("https://www.imoveisnova.com.br/alugar/rs/nova-petropolis/apartamento/ordem-valor/resultado-decrescente/quantidade-48/")
   
   soup = BeautifulSoup(data.text, 'html.parser')
   
   res = soup.find_all('div', class_='resultado')

   for item in res:
      
      title = item.find('h3', class_='tipo').text
      localization = ""
      details = ""
      prices = ""
      images = []
      description = ""
      
      divDesc = item.find('div', class_='descricao')
      if divDesc:
         description = divDesc.text
      
      h4Local = item.find('h4', class_='localizacao')
      if h4Local:
         localization = h4Local.find('span').text
      
      for val in item.find_all('div', class_='valor'):
         if prices != "":
            prices += " | "
         prices += val.small.text + ' ' + val.h5.text
      
      detailDiv = item.find_all('div', class_='detalhe')
      
      if len(detailDiv) == 4:
         
         dorms = detailDiv[0].text
         suites = detailDiv[1].text
         parkingSpaces = detailDiv[2].text
         tamanho = detailDiv[3].text + (" m²" if not "m²" in detailDiv[3].text else "")
         
         if len(dorms) == 1:
            dorms = dorms + " dormitorios"

         if len(suites) == 1:
            suites = suites + " suites"

         if len(parkingSpaces) == 1:
            parkingSpaces = parkingSpaces + " vagas"
         
         details = dorms + " | " + suites + " | " + parkingSpaces + " | " + tamanho
      
      fotoramaDiv = item.find('div', class_="fotorama")
      
      if fotoramaDiv:
         for div in item.find('div', class_="fotorama"):
            images.append(div['data-img'])
      else:
         img = item.find('img')
         if img:
            images.append(img['src'])
         
      link = "https://www.imoveisnova.com.br" + item.find("a")['href']
      
      immobile = Immobile()
      immobile.title = title
      immobile.localization = localization
      immobile.description = description
      immobile.details = details
      immobile.prices = prices
      immobile.images = images
      immobile.link = link
      immobile.website = "nova"

      immobiles.append(immobile)


def generateHTML(immobiles: List[Immobile], fileName: str):
   
   immobiles.sort(key=lambda i: i.inclusionDate, reverse=True)
   
   itensHTML = ""

   for immobile in immobiles:
      
      # formatedDate = strftime('%d/%m/%Y %H:%M', localtime(immobile.inclusionDate) - timedelta(hours=0, minutes=50))
      
      formatedDate = datetime.fromtimestamp(immobile.inclusionDate).strftime('%d/%m/%Y %H:%M')
      
      imagesHTML = ""
      
      for img in immobile.images:
         
         active = "active" if imagesHTML == "" else ""
         
         imagesHTML += """
            <div class="carousel-item """ + active + """">
               <img class="d-block w-100" src=" """ + img + """ ">
            </div>
         """
      
      idItem = "item" + str(immobiles.index(immobile))
      
      itensHTML += """
         <div class="col-md-4 col-xl-3">
            <div class="card m-1">
               
               <div class="card-img-top">
               
                  <div id=\"""" + idItem + """\" class="carousel slide" data-ride="carousel" data-interval="false">
                     <div class="carousel-inner">
                        """ + imagesHTML + """
                     </div>""" + ("""<a class="carousel-control-prev" href="#""" + idItem + """\" role="button" data-slide="prev">
                        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                        <span class="sr-only">Previous</span>
                     </a>
                     <a class="carousel-control-next" href="#""" + idItem + """\" role="button" data-slide="next">
                        <span class="carousel-control-next-icon" aria-hidden="true"></span>
                        <span class="sr-only">Next</span>
                     </a>""" if len(immobile.images) > 1 else "") + """
                  </div>
                  
               </div>
               
               <div class="card-body">
                  <h5 class="card-title">""" + immobile.title + """</h5>
                  <p class="card-text">
                     """ + ((immobile.description + "<hr>") if immobile.description else "") + """
                     """ + ((immobile.details + "<hr>") if immobile.details else "") + """
                     """ + (("<b>Localização:</b> " + immobile.localization + "<hr>") if immobile.localization else "") + """
                     """ + immobile.prices + """
                  </p>
                  <a href=\"""" + immobile.link + """\" target="_blank" class="btn btn-primary">Abrir no site</a>
                  <div style="float: right">
                     <img style="height: 35px;" src=\"""" + websites[immobile.website] + """\">
                  </div>
                  <p class="mb-0">
                     <small>Inclusão: """ + formatedDate + """</small>
                  </p>
               </div>
            </div> 
         </div>
      """.strip()
   
   htmlString = """
   <!DOCTYPE html>
   <html lang="pt">
   <head>
      <meta charset="UTF-8">
      <meta http-equiv="X-UA-Compatible" content="IE=edge">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Imóveis para alugar em Nova Petrópolis</title>
      
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
      <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
      <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>

   </head>
   <body>
      
      <div class="container-fluid mb-3">
         <div class="row">
            <div class="col py-3">
               <h1 class="h2">
                  Imóveis para alugar em Nova Petrópolis
               </h1>
               <div>
                  Atualizado em """ + datetime.fromtimestamp(time()).strftime('%d/%m/%Y %H:%M') + """
               </div>
            </div>
         </div>
         <div class="row">
            """ + itensHTML + """
         </div>
      </div>
      
   </body>
   </html>""".strip()

   with open(fileName, 'w', encoding='utf-8') as f:
      f.write(htmlString)


def loadImmobiles() -> List[Immobile]:
   
   if not os.path.isfile(IMMOBILE_FILE):
      return []
   
   with open(IMMOBILE_FILE, "r") as f:
      return [ Immobile.fromJSON(obj) for obj in json.loads("".join(f.readlines())) ]


def saveImmobiles(immobiles: List[Immobile]):
   
   with open(IMMOBILE_FILE, "w") as f:
      f.write("[\n" + ",".join([ imob.toJSON() for imob in immobiles ]) + "\n]")


def processNewImmobiles(immobiles: List[Immobile], lastGenImobbiles: List[Immobile]):
   
   for currentImob in immobiles:
      
      lastGen = [i for i in lastGenImobbiles if i.link == currentImob.link]
      
      if len(lastGen) > 0:
         currentImob.inclusionDate = lastGen[0].inclusionDate
      else:
         currentImob.inclusionDate = int(time())
   

if __name__ == "__main__":
   
   lastGenImobbiles = loadImmobiles()
   
   loadFromNovaImoveis(immobiles)
   sleep(2)
   
   loadFromNaturezaimoveis(immobiles)
   sleep(2)

   loadFromNovaPetropolis(immobiles)
   sleep(2)

   # TODO:  Usar selenium
   # https://www.alpinaimoveis.com.br/busca_imoveis.php?modalidade=2&tipo=1&cidade=1&bairro=&codigo=
   
   # TODO: Usar selenium
   # https://www.dedicareimoveis.com.br/?pesquisar/1

   processNewImmobiles(immobiles, lastGenImobbiles)

   if len(immobiles) > 1:
      generateHTML(immobiles, "index.html")
      saveImmobiles(immobiles)
   
