##############################################################################
#IMPORTS
##############################################################################
import time
from time import sleep
import requests
from bs4 import BeautifulSoup
from web3 import AsyncWeb3, AsyncHTTPProvider
import asyncio
import aiohttp
import random

##############################################################################
#GLOBAL VARIABLES
##############################################################################
#ETHERSCAN.IO urls needed
ETHERSCAN_ALL_TXNS = 'https://etherscan.io/txs?block='
ETHERSCAN_TX = 'https://etherscan.io/tx/'

#gas limit for a deter attack to be detected
GAS_THRESHOLD = 2
#response from the endpoint from quicknode
#will never change
RESPONSE = AsyncWeb3(AsyncHTTPProvider('https://solemn-wandering-borough.discover.quiknode.pro/73c4314a25c0c4d07d664fa5d610af480d02cd24/'))

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

    #constructor
    def __init__(self) -> None:
        #creates a class variable
        #it is a list of working proxies
        self.proxies = []

        #calls a request to two proxy lists
        resp1 = requests.get('https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt')
        resp2 = requests.get('https://free-proxy-list.net')

        #gets the proxies form the website
        html_list = BeautifulSoup(resp2.content, 'html.parser').select('table.table.table-striped.table-bordered tbody tr')
        proxy_list = resp1.text.split('\n') + [html.find('td').text for html in html_list]

        #print([html.select('td span')[0].text for html in html_list2])
        #checks all the working proxies asyncronously
        asyncio.run(self.check_proxies(proxy_list))

        #filters all the None out of the proxy list
        self.proxies = [proxy for proxy in self.proxies if proxy]

    #checks the proxy
    async def check_page(self, session, proxy):
        try:
            #waits for the result of session.get
            #either error or site information
            temp = await session.get('http://ident.me', proxy=f'http://{proxy}', ssl=False, timeout=50)

            #if it doesn't error, the proxy is returned
            return proxy
        except:
            #if errors, None is returned
            return None

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
    async def check_proxies(self, proxies):
        #opens and closes the ClientSession
        #trust_env must be used to use the proxies
        async with aiohttp.ClientSession(trust_env=True, headers=self.create_headers()) as session: 
            #waits for a list of proxies to come back
            responses = await self.get_tasks(session, proxies)
            self.proxies = responses

    def create_headers(self):
        #returns standard template w/ a random user agent from the class variable
        return {'User-Agent' : self.user_agents[random.randint(0,len(self.user_agents)-1)],
                'Referer' : 'no-referer',
                'Sec-Ch-Ua' : '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
                'Sec-Ch-Ua-Platform': 'Windows', 
                'Sec-Fetch-Dest' : 'document',
                'Sec-Fetch-Mode' : 'navigate',
                'Sec-Fetch-Site' : 'none',
                'Sec-Fetch-User' : '?1',
                'Connection' : 'keep-alive',
                'Upgrader-Insecure-Requests' : '1',
                'scheme' : 'https',
                'method' : 'GET',
                'Cache-Control': 'max-age=0',
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language' : 'en-US,en;q=0.9',
                'Accept-Encoding' : 'gzip, deflate'
                }

    def get_proxy(self):
        #returns random proxy from list
        return self.proxies[random.randint(0,len(self.proxies)-1)]

##############################################################################
#BLOCK FUNCTIONS
##############################################################################

#returns the % of gas used for the blocks 
def get_gas_used(block_num):
    #gets all information from the api
    block_info = RESPONSE.eth.get_block(str(hex(block_num)))
    
    return float(block_info['gasUsed'])/float(block_info['gasLimit']) * 100

#formats and adds all the information to the file
def add_to_file(blocks, f):
    for i in range(len(blocks)):
        if i > 0:
            if blocks[i-1] + 1 == blocks[i]:
                #if the blocks are consecutive then keep it on the same line
                #adds a comma so we can split it up
                f.write(f', {blocks[i]}')
            else:
                #if it's not consecutive, add it to the next line
                f.write(f'\n{blocks[i]}')
        else:
            #if it is the first block, append it regularly to the file
            f.write(f'{blocks[i]}')

#checks 
async def check_blocks(start_block, num_blocks, arr):
    #first for loop is for all the block #s we are trying to parse
    for n in range(start_block, start_block + num_blocks, 25):
        start_time = time.time()
        #calling for asyncio.as_completed which goes in the for loop as soon as any one
        #element in the parameter is ready
        #must increment by 25 so there are no 429 responses
        for result in asyncio.as_completed(
            #list comprehension of every web3 call needed
            [RESPONSE.eth._get_block(str(hex(i))) for i in range(n, n+25)]
        ):
            #waits for any web3 call to be completed
            block = await result
            #calculates gas percent used
            gas_percent = float(block['gasUsed'])/float(block['gasLimit']) * 100
            #checks and appends the block number to the tracker if 
            #gas used is less than the threshold 
            if gas_percent < GAS_THRESHOLD:
                arr.append(block['number'])
        #checks total time spent on 25 blocks
        total_time = time.time() - start_time
        if total_time < 1:
            #sleeps for the amount of time needed so no 429 request comes
            #1.2 was found by testing
            sleep(1.2-total_time)
    return arr

##############################################################################
#TRANSACTION FUNCTIONS
##############################################################################

#adds information to file
#formats all the data
def add_to_file(f, og_block, new_block, transaction, attacks):
    f.write(f'Transaction: {transaction} in block {new_block}-around block{og_block}- has a these EVM attacks: {attacks}\n')

#Takes in a string and turns it into an integer
#used to remove commas in numbers
#ex: 1,000,000 -> 1000000
def stof(string):
    total = string.split(',')
    ret_val = ''
    for part in total:
        ret_val += part
    return float(ret_val)

##########################
# MAKE ASYNC
#Check surrounding blocks async

#checks the transactions for the surrounding blocks of the given block
#if a range of blocks is given, it will check around the first and last block
def check_EVM_attack(fir_block, las_block=None):
    for block in range(fir_block-1, fir_block-3, -1):
        transactions = get_transaction_hashes(block)

        check_all_transactions(transactions, fir_block, block)

    #if there is a last block, it will check around the last block and
    #skip all blocks with 0 gas
    if las_block:
        for block in range(las_block+1, las_block+3):
            transactions = get_transaction_hashes(block)

            check_all_transactions(transactions, las_block, block)
    else:
        #otherwise it will keep checking from the first block
        for block in range(fir_block+1, fir_block+3):
            transactions = get_transaction_hashes(block)

            check_all_transactions(transactions, fir_block, block)


################################################
# MAKE ASYNC
# poss not

#returns all the transaction hashes associated with a block
def get_transaction_hashes(block_num):
    #used to track the pages that 
    i = 1
    hashes = []

    while True:
        #gets the website html and parses it into a list of all of the html around the hashes
        resp = requests.get(f'{ETHERSCAN_ALL_TXNS}{block_num}&p={i}', '''headers=create_headers()''')
        new_hashes = BeautifulSoup(resp.content, 'html.parser').select('tbody tr div.d-flex a.myFnExpandBox_searchVal')

        #if there are no hashes on a page stop
        if len(new_hashes) == 0:
            break

        hashes = hashes + new_hashes
        i+=1

        #sleeps to stop too many requests
        sleep(random.randint(10,40)/100)

    #changes every element to only be the text
    return [hash.text for hash in hashes]

#custom filter to use with beautiful soup
def bs4_filter(tag):
    try:
        #if the tag only has one class and it is 'me-1' while not having the tag 'data-bs-toggle'
        if len(tag.get('class')) == 1 and tag.get('class')[0] == 'me-1' and not tag.get('data-bs-toggle'):
            return True
    except Exception:
        pass
    return False

#gets all the actions for an associated transaction
#returns a list of a tuple in a tuple: [(action, (x,y))]
def get_actions(content):
    tx_actions = BeautifulSoup(content, 'html.parser').select('div.d-flex.flex-column.gap-2 div.d-flex.align-items-baseline div.d-flex.flex-wrap.align-items-center')
    #list comprehension going through transactions
    #filters the bs_4 using the classes found using Inspect on the etherscan.io website
    return [(action.find('span', {'class' : ['text-muted', 'me-1']}).text,(action.find_all(bs4_filter)[0].text, action.find_all(bs4_filter)[-1].text)) for action in tx_actions]

#adds the EVM attacks to a file
def check_all_transactions(txs, original_block, new_block):
    file = open('EVM_attacks.txt', 'a')

    #iterates through the transactions
    for transaction in txs:
        #checks for attack
        type_of_attack = check_transaction(transaction)
        #adds transaction to file if attack exists
        if type_of_attack:
            add_to_file(file, original_block, new_block, transaction, type_of_attack)
    file.close()

#returns True or false depending on if there is an arbitrage attack or not
def check_arbitrage(actions):
    initial_amt = '-1'
    final_amt = '-1'
    #sets these to be different in case one of these doesn't change
    first_token = 'temp1'
    cur_token = 'temp2'

    for action in actions:
        if action[0] == 'Borrow':
            #sets initial_amt to the amount borrowed and the current token and first token
            #to the token it was borrowed on
            initial_amt = action[1][0]
            cur_token = first_token = action[1][1]
        elif action[0] == 'Withdraw':
            #sets final amount to the total amount they were able to withdraw
            final_amt = action[1][0]
        elif action[0] == 'Swap':
            #updates the current token if the current token is the same
            #as the current being swapped
            if cur_token == action[1][0]:
                cur_token = action[1][1]
        
    #to be an arbitrage attack:
    #token must have made it's way all the way to the first token
    #you must have withdrew more than you borrowed
    if cur_token == first_token and stof(initial_amt) < stof(final_amt):
        return True
    return False

###################################
# MAKE ASYNC

#checks transactions for all attacks
#only arbitrage for now
def check_transaction(tx):
    ####CHANGE SOMETHING IF STATUS_CODE IS 403
    resp = requests.get(f'{ETHERSCAN_TX}{tx}', '''headers=create_headers()''')
    print(resp.status_code)
    
    #checks for arbitrage and if there is it returns a string
    if check_arbitrage(get_actions(resp.content)):
        return 'arbitrage'
    
    #if there is no attack, returns None
    return None

        

##############################################################################
#MAIN FUNCTIONS
##############################################################################

def get_deter_attacks(first_block, num_blocks):
    #file to store potential deter attacks
    file = open('deter_attacks.txt', 'a')
    #list to keep track if the low gas used are back to back or not
    tracker = []
    #Using asyncronous method to parse faster
    asyncio.run(check_blocks(first_block, num_blocks, tracker))

    #adds all low gas blocks to a file to store data
    add_to_file(tracker,file)

    file.close()

################################
# MAKE THIS ASYNC
# checks all the blocks asyncronously

def get_EVM_attacks():
    file = open('deter_attacks.txt', 'r')
    #reads all the lines of the files and puts them in a list
    blocks = file.readlines()
    #iterates through the list of every line in the file
    for block in blocks:
        #splits up the line to see if there is more than one consecutive block
        temp = block.split(', ')
        #checks if last element is the same as first element
        if temp[0] != temp[-1]:
            first = int(temp[0])
            last = int(temp[-1])
            
            check_EVM_attack(first, last)

        else:
            block_num = int(temp[0])
            check_EVM_attack(block_num)

    file.close()


#What we are currently running

start_time_total = time.time()

#check_EVM_attack(10633646)
#check_transaction('0x01afae47b0c98731b5d20c776e58bd8ce5c2c89ed4bd3f8727fad3ebf32e9481')
req = RequestGenerator()
print(len(req.proxies))


print('total time: %s' %(time.time()-start_time_total))