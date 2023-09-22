import requests
import time
from time import sleep
from bs4 import BeautifulSoup
from web3 import Web3, HTTPProvider

#gas limit for a deter attack to be detected
GAS_THRESHOLD = 2.00
#response from the endpoint from quicknode
#will never change
RESPONSE = Web3(HTTPProvider('https://solemn-wandering-borough.discover.quiknode.pro/73c4314a25c0c4d07d664fa5d610af480d02cd24/'))

def get_gas_used(block_num):
    block_info = RESPONSE.eth.get_block(str(hex(block_num)))
    return float(block_info['gasUsed'])/float(block_info['gasLimit']) * 100

def parse_data(starting_block, num_blocks):
    #list to keep track if the low gas used are back to back or not
    consecutive_tracker = []
    #list to record all deter attacks detected (records like: block1 - block2)
    deter_attacks = []
    #goes backwards from the starting block to starting_block - num_blocks
    count = 0
    for block in range(starting_block,starting_block-num_blocks, -1):
        #checks if gas percent is less than the gas threshold
        if(get_gas_used(block) <= GAS_THRESHOLD):
            #adds block number to the consecutive tracker if it is less
            consecutive_tracker.append(block)
        else:
            if(len(consecutive_tracker) > 2):
                #adds the set of blocks to the deter attack tracker 
                #if the consecutive tracker is long enough
                deter_attacks.append(f'{consecutive_tracker[-1]}-{consecutive_tracker[0]}')
            #resets the consecutive trakcer since there was a break
            consecutive_tracker = []
        count+=1
    print(deter_attacks)


start_time = time.time()
parse_data(16000000, 25)
print('total time: %s' %(time.time()-start_time))