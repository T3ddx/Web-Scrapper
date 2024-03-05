import asyncio
import aiohttp
import random
import requests
from bs4 import BeautifulSoup
from time import sleep
import math, traceback
#Class to help make requests look more human
#It will rotate proxies and create random headers
class RequestGenerator:
    #list of user agents
    user_agents = ['Mozilla/5.0 (iPhone14,3; U; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/19A346 Safari/602.1',
               'Mozilla/5.0 (Linux; Android 7.0; Pixel C Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
               'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9',
               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
               'Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
               'Mozilla/5.0 (Linux; Android 12; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
               'Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
               'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
               ]
    
    eigen_api = lambda x : 'resultId' not in x.decode('utf-8') and 'eigenphi-ethereum-tx' not in x.decode('utf-8')
    eigen_web = lambda x : BeautifulSoup(x, 'html.parser').select('noscript')[1].text != 'You need to enable JavaScript to run this app.'
    ether = lambda x : BeautifulSoup(x, 'html.parser').select('h1.h5.mb-0')[0].text != "\nTransactions\n"

    #constructor
    def __init__(self, timeout=30) -> None:
        #creates a class variable
        #it is a list of working proxies
        self.proxies = {}
        self.timeout = timeout

        self.refreshing = False

        asyncio.run(self.refresh_proxy_list())

    #checks the proxy
    async def check_page(self, session, proxy): 
        i = 0

        if proxy in self.proxies:
            return None
        
        while(True):
            try:
                #waits for the result of session.get
                #either error or site information
                await asyncio.sleep(0)
                temp = await session.get('https://eigenphi.io/', proxy=f'http://{proxy}', ssl=False, timeout=self.timeout, headers=self.create_headers())
                
                content = await temp.content.read()
                
                if RequestGenerator.eigen_web(content):
                    raise Exception

                #if it doesn't error, the proxy is returned
                return proxy
            except Exception as e:
                #print(e)
                await asyncio.sleep(0.5)
                if i > 2:
                    return None
                i+=1

    #returns a list that includes None for non working proxies
    #or the proxy itself if it is working
    async def get_tasks(self, session, proxies):
        #lists of all async tasks to run
        tasks = []
        for proxy in proxies:
            #adds all the coroutines  to the lists
            #The tasks are the function that checks the proxy
            #Do not have to wait for the future objects here
            tasks.append(asyncio.create_task(self.check_page(session, proxy)))
        #waits for all the future objects of all coroutines
        proxy_list = await asyncio.gather(*tasks)
        return proxy_list

    #checks 
    async def add_proxies(self, session, proxies):
        #waits for a list of proxies to come back
        responses = await self.get_tasks(session, proxies)
        responses_set = {proxy : 0 for proxy in responses if proxy}
        self.proxies.update(responses_set)

    async def refresh_proxy_list(self):
        #opens and closes the ClientSession
        #trust_env must be used to use the proxies
        async with aiohttp.ClientSession(trust_env=True) as session:
            #calls a request to two proxy lists
            resp1 = await session.get('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt')
            resp2 = await session.get('https://free-proxy-list.net')

            #gets the proxies form the website
            html_list = BeautifulSoup(await resp2.content.read(), 'html.parser').select('table.table.table-striped.table-bordered tbody tr')
            proxy_list = (await resp1.text()).split('\n') + [html.find('td').text + ':' + html.select('td')[1].text for html in html_list]

            #checks all the working proxies asyncronously
            await self.add_proxies(session, proxy_list)
            
        if len(self.proxies) == 0:
            print('refreshing list but fr')
            await asyncio.sleep(60*3)
            await self.refresh_proxy_list()
            print('finished refreshing but fr')

    def create_headers(self):
        #returns standard template w/ a random user agent from the class variable
        return {'User-Agent' : self.user_agents[random.randint(0,len(self.user_agents)-1)],
                'Referer' : 'no-referer',
                'Sec-Ch-Ua' : '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
                'Sec-Ch-Ua-Platform': 'Windows', 
                'Connection' : 'keep-alive',
                'Upgrader-Insecure-Requests' : '1',
                'scheme' : 'https',
                'method' : 'GET',
                'Cache-Control': 'max-age=0',
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language' : 'en-US,en;q=0.9',
                'Accept-Encoding' : 'gzip, deflate'
                }

    def ban_proxy(self, proxy):
        if not proxy in self.proxies:
            return
        
        if self.proxies[proxy] >= 3:
            del self.proxies[proxy]
            return

        self.proxies[proxy] += 1

    async def get_proxy(self):
        while self.refreshing and len(self.proxies) == 0:
            await asyncio.sleep(10)

        if not self.refreshing and len(self.proxies) <= 40:
            print(f'refreshing list of: {len(self.proxies)}')
            self.refreshing = True
            await self.refresh_proxy_list()
            self.refreshing = False
            print('finished refreshing')

        #returns random proxy from list    
        return list(self.proxies.keys())[random.randint(0,len(self.proxies)-1)]
    

    async def get_resp_data(self, session, url): 
        proxy = await self.get_proxy()
        headers = self.create_headers()

        while(True):
            for _ in range(5):
                try:
                    await asyncio.sleep(0)
                    resp = await session.get(url, ssl=False, headers=headers, proxy=f'http://{proxy}', timeout=self.timeout)
                    
                    content = await resp.content.read()

                    #Change this when switching sites
                    if RequestGenerator.eigen_api(content):
                        raise Exception
                    return content
                except:
                    pass
                    
            
            self.ban_proxy(proxy)

            try:
                await asyncio.sleep(0)
                resp = await session.get(url, ssl=False, headers=headers, timeout=self.timeout)
                
                content = await resp.content.read()

                #Change this when switching sites
                if RequestGenerator.eigen_api(content):
                    raise Exception
                
                return content
            except Exception as e:
                print(e)
                await asyncio.sleep(1)
            
            proxy = await self.get_proxy()
