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

def parse_data(ending_block, num_blocks):
    #list to keep track if the low gas used are back to back or not
    tracker = []
    #goes from ending_block-num_blocks to ending_block
    #only checks every 3 since the low gas has to be consecutive
    #if it hits a low gas used, it will track it for later
    #method is ONLY faster if gas threshold is low
    for block in range(ending_block-num_blocks, ending_block, 3):
        #checks if gas percent is less than the gas threshold
        if(get_gas_used(block) <= GAS_THRESHOLD):
            #adds block number to the consecutive tracker if it is less
            tracker.append(block)
    #checks all the blocks around the blocks that it has hit
    for block in tracker:
        #tracks the lowest and highest # blocks  
        lower_block = block
        upper_block = block
        #counter
        i = 1
        #keeps going until the streak of low gas used blocks BELOW the block in the tracker is done
        while(get_gas_used(block - i) <= GAS_THRESHOLD):
            #updates the lowest block in the group
            lower_block = block - i
            #updates counter
            i+=1
            #if block-i in tracker:
                #removes redundant blocks
                #tracker.remove(block+i)
            #note: doesn't check wether block-1 is in tracker since tracker goes from lowest to highest
            #and if a block is redundant in the list it will get it when checking the blocks above the
            #current block
        #resets counter
        i = 1
        #keeps going until the streak of low gas used blocks ABOVE the block in the tracker is done
        while(get_gas_used(block+i) <= GAS_THRESHOLD):
            #updates highest block in the group
            upper_block = block+i
            #checks if any of the blocks above are counted in the tracker 
            if block+i in tracker:
                #removes redundant blocks
                tracker.remove(block+i)
            #updates counter
            i+=1
        #prints deter attack as a range of blocks
        if lower_block != upper_block and upper_block - lower_block > 2:
            print(f'Potential deter attack at {lower_block}-{upper_block}')

        #method I tried first
        #regular for loop checking every block
        #faster if gas threshold is higher
        """else:
            if(len(consecutive_tracker) > 2):
                #adds the set of blocks to the deter attack tracker 
                #if the consecutive tracker is long enough
                deter_attacks.append(f'{consecutive_tracker[0]}-{consecutive_tracker[-1]}')
            #resets the consecutive trakcer since there was a break
            consecutive_tracker = []

    #checks if the last set of blocks were added to consecutive tracker
    if consecutive_tracker:
        deter_attacks.append(f'{consecutive_tracker[0]}-{consecutive_tracker[-1]}')"""

start_time = time.time()
parse_data(10000000, 500000)
print('total time: %s' %(time.time()-start_time))