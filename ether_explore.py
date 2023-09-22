import requests
from time import sleep
from bs4 import BeautifulSoup

def scrape_block(blocknumber, page):
    # the URL of the web page that we want to get transaction data
    api_url = "https://etherscan.io/txs?block=" + str(blocknumber) + "&p="+str(page)
    # HTTP headers used to send a HTTP request
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0'}
    # Pauses for 0.5 seconds before sending the next request
    sleep(0.5)
    # send the request to get data in the webpage
    response = requests.get(api_url, headers=headers)
    # get the transaction table from the response data we get

    count = 0

    for row in BeautifulSoup(response.content, 'html.parser').select('table.table-hover tbody tr'):
        # each row in the table is a transaction
        attributes = map(lambda x: x.text, row.findAll('td'))
        # extract transaction attributes
        _begin, hash, method, block, timestamp1, age, x, from1, _arr, to1, value1, txnfee, burnfee = attributes
        ######################## modify code below for each exercise #######################
        if method == 'Transfer':
            count += 1
        #print("transaction of ID:", hash, "block:", block, "from address", from1, "toaddress", to1, "transaction fee",txnfee)
    return count

if __name__ == "__main__":  # entrance to the main function
    transfer = 0
    for i in range(1,4):
        transfer += scrape_block(15479087, i)
    print(transfer)

