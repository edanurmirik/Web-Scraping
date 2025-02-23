from django.shortcuts import render
from django.http import HttpResponse
import requests, pymongo, os
from urllib.parse import urlparse
from pymongo import MongoClient
from bs4 import BeautifulSoup

def database():
    client = MongoClient("mongodb+srv://edanrmirik:755502Eda@cluster0.nz8jxm9.mongodb.net/test?retryWrites=true&w=majority")
    db = client['makalebilgi']
    collection = db['makaleler']
    return collection

def index(request):
    collection = database()
    makaleler = collection.find({})
    return render(request, "index.html", {"makaleler": makaleler})

def liste(request):
    collection = database()
    article_details = []

    if request.method == "POST":
        search = request.POST.get('text')

        query = {"AratilanKelimeler": search} 
        results = list(collection.find(query))
        #print(results[0].get("YayinAdi")

        if len(results) > 0: 
            print("aaaaaaaaaa")
            for result in results:
                print(result.get("YayinAdi"))

                article_details.append({
                    "YayinAdi": result.get("YayinAdi"),
                    "YazarlarinIsimleri": result.get("YazarlarinIsimleri"),
                    "YayinTürü": result.get("YayinTürü"),
                    "YayimlanmaTarihi": result.get("YayimlanmaTarihi"),
                    "YayinciAdi": result.get("YayinciAdi"),
                    "AratilanKelimeler": result.get("AratilanKelimeler"),
                    "AnahtarKelimeler": result.get("AnahtarKelimeler"),
                    "Ozet": result.get("Ozet"),
                    "Referanslar": result.get("Referanslar"),
                    "AlintiSayisi": result.get("AlintiSayisi"),
                    "DoiNumarasi": result.get("DoiNumarasi"),
                    "URLAdresi": result.get("URLAdresi"),
                    "PDFLink": result.get("PDFLink")
                })
            
            return render(request, "liste.html", {"article_details": article_details})

        else:
            url = "https://dergipark.org.tr/en/search?q=" + search
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            }
            response = requests.get(url, headers=headers)

            print(response.status_code)

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('div', {'class': 'card article-card dp-card-outline'})

            for i, article in enumerate(articles):
                if(i > 10):
                    break
                title = article.find('h5', {'class': 'card-title'}).text.strip()
                article_url = article.find('a')['href']
                article = makale_detaylari(article_url, collection, search)
                if article:
                    article_details.append(article)
                    print(article_url)

            return render(request, "liste.html", {"article_details": article_details})
    else:
        sort_by = request.GET.get('sort', 'date_eski')
        if sort_by == 'date_yeni':
            articles = collection.find().sort("YayimlanmaTarihi", -1)
        else:
            articles = collection.find().sort("YayimlanmaTarihi", 1)
        
        return render(request, "liste.html", {"article_details": articles})


def makale_detaylari(article_url, collection, search):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    response = requests.get(article_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.find('meta', attrs={'name': 'citation_title'})['content']

        authors = [author['content'] for author in soup.find_all('meta', attrs={'name': 'citation_author'})]

        publication_type = soup.find('meta', attrs={'name': 'citation_article_type'})
        if publication_type is not None:
            publication_type_content = publication_type.get('content', '0')
        else:
            publication_type_content = 'none'

        publication_date = soup.find('meta', attrs={'name': 'citation_publication_date'})
        if publication_date is not None:
            publication_date_content = publication_date.get('content', '0')
        else:
            publication_date_content = 'none'

        publisher_name = soup.find('meta', attrs={'name': 'citation_publisher'})
        if publisher_name is not None:
            publisher_name_content = publisher_name.get('content', '0')
        else:
            publisher_name_content = 'none'

        keywords_search = search.lower()

        keywords_article = [keyword['content'] for keyword in
                            soup.find_all('meta', attrs={'name': 'citation_keywords'})]

        abstract = soup.find('meta', attrs={'name': 'citation_abstract'})['content']

        references = [reference['content'] for reference in
                      soup.find_all('meta', attrs={'name': 'citation_reference'})]

        citation_count = soup.find('meta', attrs={'name': 'stats_trdizin_citation_count'})
        if citation_count is not None:
            citation_count_content = citation_count.get('content', '0')
        else:
            citation_count_content = 'none'


        doi_tag = soup.find('meta', attrs={'name': 'citation_doi'})
        if doi_tag is not None:
            doi_content = doi_tag.get('content', '0')
        else:
            doi_content = 'none'

        url = article_url

        pdf_linki = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if pdf_linki:
            pdf_linki_content = pdf_linki.get('content', '')
        else:
            pdf_linki_content = None


        article_details = {
            "YayinAdi": title,
            "YazarlarinIsimleri": authors,
            "YayinTürü": publication_type_content,
            "YayimlanmaTarihi": publication_date_content,
            "YayinciAdi": publisher_name_content,
            "AratilanKelimeler": keywords_search,
            "AnahtarKelimeler": keywords_article,
            "Ozet": abstract,
            "Referanslar": references,
            "AlintiSayisi": citation_count_content,
            "DoiNumarasi": doi_content,
            "URLAdresi": url,
            "PDFLink": pdf_linki_content
        }

        collection.insert_one(article_details)
        
        return article_details
    else:
        print("Hata: Makale sayfası yüklenemedi.")
        return None


def detay(request, yayinAdi):
    collection = database()
    
    result = collection.find_one({"YayinAdi": yayinAdi})

    article_details = {
        "YayinAdi": result.get("YayinAdi"),
        "YazarlarinIsimleri": result.get("YazarlarinIsimleri"),
        "YayinTürü": result.get("YayinTürü"),
        "YayimlanmaTarihi": result.get("YayimlanmaTarihi"),
        "YayinciAdi": result.get("YayinciAdi"),
        "AratilanKelimeler": result.get("AratilanKelimeler"),
        "AnahtarKelimeler": result.get("AnahtarKelimeler"),
        "Ozet": result.get("Ozet"),
        "Referanslar": result.get("Referanslar"),
        "AlintiSayisi": result.get("AlintiSayisi"),
        "DoiNumarasi": result.get("DoiNumarasi"),
        "URLAdresi": result.get("URLAdresi"),
        "PDFLink": result.get("PDFLink"),
    }

    return render(request, "detay.html", {"article": article_details})

