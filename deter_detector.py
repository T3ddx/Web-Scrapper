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
from RequestGenerator import RequestGenerator as rq
import json
import math, traceback

##############################################################################
#GLOBAL VARIABLES
##############################################################################
#ETHERSCAN.IO urls needed
ETHERSCAN_ALL_TXNS = 'https://etherscan.io/txs?block='
ETHERSCAN_TX = 'https://etherscan.io/tx/'


#response from the endpoint from quicknode
#will never change
RESPONSE = AsyncWeb3(AsyncHTTPProvider('https://solemn-wandering-borough.discover.quiknode.pro/73c4314a25c0c4d07d664fa5d610af480d02cd24/'))

##############################################################################
#BLOCK FUNCTIONS
##############################################################################

#returns the % of gas used for the blocks 
def get_gas_used(block_num):
    #gets all information from the api
    block_info = RESPONSE.eth.get_block(str(hex(block_num)))
    
    return float(block_info['gasUsed'])/float(block_info['gasLimit']) * 100

#formats and adds all the information to the file
def write_to_file(blocks, f):
    for i in range(len(blocks)):
        f.write(f'{blocks[i]}\n')

#checks 
async def check_blocks(start_block, num_blocks, gas_threshold):
    #first for loop is for all the block #s we are trying to parse
    for n in range(start_block, start_block + num_blocks, 10):
        file = open(f'deter_attacks_{gas_threshold}.txt', 'a')
        tracker = []
        start_time = time.time()
        #calling for asyncio.as_completed which goes in the for loop as soon as any one
        #element in the parameter is ready
        #must increment by 25 so there are no 429 responses
        for result in asyncio.as_completed(
            #list comprehension of every web3 call needed
            [RESPONSE.eth._get_block(str(hex(i))) for i in range(n, n+10)]
        ):
            #waits for any web3 call to be completed
            block = await result
            #calculates gas percent used
            gas_percent = float(block['gasUsed'])/float(block['gasLimit']) * 100
            #checks and appends the block number to the tracker if 
            #gas used is less than the threshold 
            if gas_percent < gas_threshold:
                tracker.append(f'{block["number"]}|{gas_percent}')
            
        write_to_file(tracker, file)
        file.close()

        #checks total time spent on 25 blocks
        total_time = time.time() - start_time
        if total_time < 1:
            #sleeps for the amount of time needed so no 429 request comes
            #1.2 was found by testing
            sleep(1.5-total_time)


##############################################################################
#GETTING TRANSACTION FUNCTIONS
##############################################################################


#checks the transactions for the surrounding blocks of the given block
#if a range of blocks is given, it will check around the first and last block
async def get_transaction_urls(session, fir_block, las_block=None):
    ###OLD WAY

    #coros = []

    # coros = [asyncio.create_task(get_num_transaction_hashes(session, block, fir_block)) for block in range(fir_block-1, fir_block-3, -1)]

    # if las_block:
    #     coros = coros + [asyncio.create_task(get_num_transaction_hashes(session, block, las_block)) for block in range(las_block+1, las_block+3)]
    # else:
    #     coros = coros + [asyncio.create_task(get_num_transaction_hashes(session, block, fir_block)) for block in range(fir_block+1, fir_block+3)]
    
    #return coros

    ###NEW WAY: 
    #I check every transaction so I do not need to check the blocks around
    return [asyncio.create_task(get_num_transaction_hashes(session, fir_block, fir_block))]

async def get_rest_transaction_hashes(session, page_num, block_num, og_block):
    resp_content = await manager.get_resp_data(session, f'{ETHERSCAN_ALL_TXNS}{block_num}&p={page_num}')
    
    hashes = BeautifulSoup(resp_content, 'html.parser').select('tbody tr div.d-flex a.myFnExpandBox_searchVal')

    print('rest of data')
    print(manager.proxies)
    print(f'block:{block_num} page:{page_num} new hashes: {len(hashes)}')

    return [(hash.text, block_num, og_block) for hash in hashes]

#returns all the transaction hashes associated with a block
async def get_num_transaction_hashes(session, block_num, og_block):
    #gets the website html and parses it into a list of all of the html around the hashes
    resp_content = await manager.get_resp_data(session, f'{ETHERSCAN_ALL_TXNS}{block_num}&p=1')
    
    hashes = BeautifulSoup(resp_content, 'html.parser').select('tbody tr div.d-flex a.myFnExpandBox_searchVal')

    if len(hashes) == 0:
        return [], 0, block_num, og_block

    num_hashes = BeautifulSoup(resp_content, 'html.parser').select('span.text-dark.content-center.gap-1')[0].text

    num_hashes = int(''.join([x for x in num_hashes if x.isdigit()]))
    print(num_hashes)
    print(manager.proxies)
    print(f'block:{block_num} page:{1} new hashes: {len(hashes)}')

    num_pages = math.ceil(num_hashes/50)
    print(f'num of pages: {num_pages}')

    #sleeps to stop too many requests
    #await asyncio.sleep(random.randint(10,20)/10)

    #changes every element to only be the text
    return [(hash.text, block_num, og_block) for hash in hashes], num_pages, block_num, og_block

async def async_manager(blocks):
    async with aiohttp.ClientSession(trust_env=True, connector=aiohttp.TCPConnector()) as session:
        tasks = []
        #iterates through the list of every line in the file
        for block in blocks:
            #splits up the line to see if there is more than one consecutive block
    
            temp = block.split(', ')
    
            #checks if last element is the same as first element
            if len(temp) > 1:
                first = int(temp[0])
                last = int(temp[-1])
                
                tasks.append(asyncio.create_task(get_transaction_urls(session, first, last)))
            else:
                block_num = int(temp[0])
                tasks.append(asyncio.create_task(get_transaction_urls(session, block_num)))

        response = await asyncio.gather(*tasks)

        tasks = [item for list in response for item in list]

        txs_n_tasks = await asyncio.gather(*tasks)


        print(f'finished getting num of pages')
        total_txs = []
        new_tasks = []
        for txs, pages, block, og_block in txs_n_tasks:
            total_txs = total_txs + txs
            for i in range(2, pages+1):
                new_tasks = new_tasks + [asyncio.create_task(get_rest_transaction_hashes(session, i, block, og_block))]

        new_txs = await asyncio.gather(*new_tasks)
        print('total pages done')

        for lst in new_txs:
            total_txs = total_txs + lst

    return total_txs

###################################################################
# CHECKING TRANSACTIONS
###################################################################
#adds information to file
#formats all the data
def add_to_file(f, og_block, new_block, transaction, attacks):
    f.write(f'Transaction: {transaction} in block {new_block}-around block{og_block}-has a these MEV attacks: {attacks}\n')

#Takes in a string and turns it into an integer
#used to remove commas in numbers
#ex: 1,000,000 -> 1000000
def stof(string):
    total = string.split(',')
    ret_val = ''
    for part in total:
        ret_val += part
    return float(ret_val)

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
    tx_actions = BeautifulSoup(content, 'html.parser').select('div.d-flex.align-items-baseline div.d-flex.flex-wrap.align-items-center')
    #for action in tx_actions:
    #    print(action)
    #list comprehension going through transactions
    #filters the bs_4 using the classes found using Inspect on the etherscan.io website
    try:
        return [(action.find('span', {'class' : ['text-muted', 'me-1']}).text,(action.find_all(bs4_filter)[0].text, action.find_all(bs4_filter)[-1].text)) for action in tx_actions]
    except:
        return []

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
            if not first_token:
                first_token = action[1][0]
                cur_token = action[1][1]
            else:
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

def check_suspicious(actions):
    swap_count = 0
    for action in actions:
        if action[0] == 'Swap':
            swap_count += 1

    if swap_count >= 2:
        return True
    return False

def find_attack(decoded_content):
    if 'eigenphi-ethereum-tx' in decoded_content:
        return None

    data = json.loads(decoded_content)
    attacks = data['summary']['types']
    attack_string = ''

    for attack in attacks:
        attack_string = attack_string + attack + ' '
    
    return attack_string

#checks transactions for all attacks
#only arbitrage for now
async def check_transaction(session, url, curr_block, og_block, tx):
    content = await manager.get_resp_data(session, url)
    
    percent_tracker = [None, None, None, None, None, None]
    
    type_of_attack = find_attack(content.decode('utf-8'))

    print(f'number of proxies: {len(manager.proxies)}')
    print(f'at {tx}, found this attack: {type_of_attack}')


    ######################################
    # WRITE CODE UNDER HERE
    # check if block is around an empty block write that
    # if not write something else
    ######################################

    if not type_of_attack:
        #if no attack, returns None
        return None
    
    #holds the minimum gas block in these ranges
    min_gas = 100
    min_gas_block = 0
    
    #checker for 5 percent
    for block in range(int(curr_block)-2, int(curr_block)+2):
        #checker for 5 percent
        if block in empty_blocks_5:
            percent_tracker[0] = f'DETER|{type_of_attack}|{tx}|{curr_block}|{block}'
        #checker for 10 percent
        if block in empty_blocks_10:
            percent_tracker[1] = f'DETER|{type_of_attack}|{tx}|{curr_block}|{block}'
        #checker for 15 percent
        if block in empty_blocks_15:
            percent_tracker[2] = f'DETER|{type_of_attack}|{tx}|{curr_block}|{block}'
        #checker for 20 percent
        if block in empty_blocks_20:
            percent_tracker[3] = f'DETER|{type_of_attack}|{tx}|{curr_block}|{block}'
        #checker for 25 percent
        if block in empty_blocks_25:
            percent_tracker[4] = f'DETER|{type_of_attack}|{tx}|{curr_block}|{block}'

        #find minimum algorithm
        #finds the block with the lowest gas used
        if block in empty_blocks_100 and empty_blocks_100[block] <= min_gas:
            min_gas = empty_blocks_100[block]
            min_gas_block = block
        

    if not percent_tracker[0]:
        percent_tracker[0] = f'N/A|{type_of_attack}|{tx}|{curr_block}|N/A'

    if not percent_tracker[1]:
        percent_tracker[1] = f'N/A|{type_of_attack}|{tx}|{curr_block}|N/A'

    if not percent_tracker[2]:
        percent_tracker[2] = f'N/A|{type_of_attack}|{tx}|{curr_block}|N/A'

    if not percent_tracker[3]:
        percent_tracker[3] = f'N/A|{type_of_attack}|{tx}|{curr_block}|N/A'
    
    if not percent_tracker[4]:
        percent_tracker[4] = f'N/A|{type_of_attack}|{tx}|{curr_block}|N/A'
    
    percent_tracker[5] = f'{min_gas}|{min_gas_block}|{type_of_attack}|{tx}|{curr_block}'

    return percent_tracker

async def async_manager2(data):
    async with aiohttp.ClientSession(trust_env=True) as session:
        tasks = []

        for piece in data:
            tx, curr_block, og_block = piece.split('|')
            og_block = og_block[:-1]

            url = f'https://storage.googleapis.com/eigenphi-ethereum-tx/{tx}'
            tasks.append(asyncio.create_task(check_transaction(session, url, curr_block, og_block, tx)))

        results = await asyncio.gather(*tasks)
        tup = ([], [], [], [], [], [])
        for attack in results:
            if attack:
                for i in range(len(tup)):
                    tup[i].append(attack[i])

    return tup

##############################################################################
#MAIN FUNCTIONS
##############################################################################

def get_deter_attacks(first_block, num_blocks):
    asyncio.run(check_blocks(first_block, num_blocks, 100))


# checks all the blocks asyncronously
def get_potential_MEV(start_value=0, file_name='transactions.txt', increment_val=50):
    file1 = open('deter_attacks_v2.txt', 'r')

    #reads all the lines of the files and puts them in a list
    #gets all blocks now
    blocks = [f'{block}' for block in range(19161569, 19161569 + 25000)]#file1.readlines()

    for i in range(start_value, len(blocks), increment_val):
        block_time = time.time()

        file2 = open(file_name, 'a')
        try:
    
            if i + increment_val >= len(blocks):
                txs = asyncio.run(async_manager(blocks[i:]))
            else:
                txs = asyncio.run(async_manager(blocks[i:i+increment_val]))

            print(f'time for one set: {time.time() - block_time}')
            print('adding to file')
            for tx, block, og_block in txs:
                file2.write(f'{tx}|{block}|{og_block}\n')

            time.sleep(random.randint(5,10))
        except Exception as e:
            file2.write(f'ended at: {i}')
            break
        file2.close()
    file1.close()

def get_MEV(start_val=0, file_name='arbitrage', increment_val=200):
    #readjusting for truncation of file
    start_val = start_val - 100
    reading_file = open('transactions_v3.txt')

    #this is the data I want to parse
    #the data that I the info of the surrounding blocks
    urls = reading_file.readlines()[100:3870789]

    for i in range(start_val, len(urls), increment_val):
        check_time = time.time()
        writing_file_list = [open(f'{file_name}_5.txt', 'a'),
                            open(f'{file_name}_10.txt', 'a'),
                            open(f'{file_name}_15.txt', 'a'),
                            open(f'{file_name}_20.txt', 'a'),
                            open(f'{file_name}_25.txt', 'a'),
                            open(f'{file_name}_100.txt', 'a')]

        try:
            if i + increment_val < len(urls):
                attacks = asyncio.run(async_manager2(urls[i:i+increment_val]))
            else:
                attacks = asyncio.run(async_manager2(urls[i:]))
        

            print(f'time taken: {time.time() - check_time}')
            print('adding to file')
            
            for i in range(len(attacks)):
                for attack in attacks[i]:
                    writing_file_list[i].write(attack + '\n')

            time.sleep(random.randint(5,10))
        except Exception as e:
            print(e)
            for j in range(len(writing_file_list)):
                writing_file_list[j].write(f'ended at: {i}')
            break

        for j in range(len(writing_file_list)):
            writing_file_list[j].close()

    reading_file.close()

#What we are currently running
start_time_total = time.time()
#manager to handle proxies and headers
manager = rq()

print(f'time to get proxy list: {time.time() - start_time_total}')
print(manager.proxies)

#5 percent file
empty_block_file_5 = open('deter_attacks_5.txt', 'r')
empty_blocks_5 = {int(block[:-1]) for block in empty_block_file_5.readlines()}

#10 percent file
empty_block_file_10 = open('deter_attacks_10.txt', 'r')
empty_blocks_10 = {int(block[:-1]) for block in empty_block_file_10.readlines()}

#15 percent file
empty_block_file_15 = open('deter_attacks_15.txt', 'r')
empty_blocks_15 = {int(block[:-1]) for block in empty_block_file_15.readlines()}

#20 percent file
empty_block_file_20 = open('deter_attacks_20.txt', 'r')
empty_blocks_20 = {int(block[:-1]) for block in empty_block_file_20.readlines()}

#25 percent file
empty_block_file_25 = open('deter_attacks_25.txt', 'r')
empty_blocks_25 = {int(block[:-1]) for block in empty_block_file_25.readlines()}

#100 percent file
empty_block_file_100 = open('deter_attacks_100.txt', 'r')
empty_blocks_100 = {int(line.split('|')[0]) : float(line.split('|')[1][:-1]) for line in empty_block_file_100.readlines()}


get_MEV(start_val=1342864, file_name='arbitrage', increment_val=2500)
#get_potential_MEV(start_value=0, file_name='transactions_v3.txt', increment_val=100)
#get_deter_attacks(19161569, 25000)
print('total time: %s' %(time.time()-start_time_total))