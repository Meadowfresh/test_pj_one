import requests
from bs4 import BeautifulSoup
import csv
import os
import re
import smtplib
import random
import logging


# Logger settings
logging.basicConfig(filename='webscrap_log.log', level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s')


# Lists of all the auction details
auction_details = []
# List of recently scrapped auction M_Links
auction_links = []
# List of previously scrapped auction M_Links
file_links = []
# List of all the auction details for previously unrecorded auctions
new_listing = []


# Randomly select a URL to check
def get_url():
    url_list = [] # enter target url here

    url = random.choice(url_list)
    return url


# Randomly select a proxy to use
def get_proxy():
    proxy_list = [] # enter proxy list here in the format of {"https": 'http://XXXXX:XXXX'}

    proxy = random.choice(proxy_list)
    logging.info(proxy)
    return proxy


# Scrap the selected url
def make_soup():
    proxies = get_proxy()
    url = get_url()
    headers = {'User-Agent': 'Mozilla/5.0'}
    result = requests.get(url, headers=headers, proxies=proxies)
    if result.status_code == 200:
        logging.info(result.status_code)

        # create BS of the target url
        soup = BeautifulSoup(result.content.decode(), 'html.parser')
    else:
        logging.info(result.status_code)
        exit()
    # print(soup)
    return soup


# Check the listings on the selected url
def check_listing():
    soup = make_soup()

    # Checks the scraped data file and reads the M_Links into a list to be used for comparing to the newly parsed links
    make_new_file = False
    # CSV file containing previously scrapped listings
    bk_file = '.csv' # enter the csv file name here
    if os.path.isfile(bk_file):
        logging.info('Have bk file')

        with open(bk_file, 'r', encoding='UTF-8') as bk_csv:
            reader = csv.DictReader(bk_csv, delimiter=',')
            for row in reader:
                file_links.append(row['M_Link'])

    else:
        logging.info('New bk file made')
        make_new_file = True

    if make_new_file == True:
        # Making the auction history csv
        csv_file = open(bk_file, 'w', encoding='UTF-8', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Title', 'Link', 'M_Link', 'Price', 'Active/Sold', 'Thumbnail'])
    else:
        # print('Passed on making a new file')
        pass

    # Parse the scrapped HTML data for only the sections wanted
    for auction in soup.find_all('section', class_='items-box'):
        # Get the auction title
        try:
            title = auction.h3.text
        except Exception as e:
            title = None
            # logging.warning(e)
        # Get the auction link
        try:
            link = auction.a.get('href')
        except Exception as e:
            link = None
            # logging.warning(e)
        # Get the auction price
        try:
            price = auction.find('div', class_='items-box-price').text
        except Exception as e:
            price = None
            # logging.warning(e)
        # Gets the sold out icons text, otherwise will return 'Active'
        try:
            soldOut = auction.find('div', class_='item-sold-out-badge').text
        except Exception as e:
            soldOut = 'Active'
            # logging.warning(e)
        # Gets the thumbnail image link
        try:
            image = auction.img.get('data-src')
        except Exception as e:
            image = None
            # logging.warning(e)
        # Extracts the static listing link from the url to be used for checking if it has been previously parsed or not
        pattern = 'item.mercari.com/jp/([a-z\d]+)/'
        try:
            match_link = re.search(pattern, link, re.IGNORECASE)
            m_link = match_link.group(1)
        except Exception as e:
            # logging.warning(e)
            m_link = 'No match found'

        if make_new_file == True:
            # Writes the parsed information to the csv file
            csv_writer.writerow([title, link, m_link, price, soldOut, image])
        else:
            # print('Passed on writing to the bk file')
            pass

        # Adds the parsed information to its corresponding list
        auction_links.append(m_link)
        auction_details.append({
            'Title': title,
            'Link': link,
            'M_Link': m_link,
            'Price': price,
            'Active/Sold': soldOut,
            'Thumbnail': image})

    if make_new_file == True:
        csv_file.close()
    else:
        pass

    # Compares freshly parsed links with stored links to determine if any are new
    new_auction = set(auction_links).difference(file_links)
    # print(new_auction)
    # print('============================================')

    # Retrieves full listing details for new auctions
    for line in auction_details:
        if line['M_Link'] in new_auction:
            # print(line)
            new_listing.append(line)

    if len(new_listing) == 0:
        # print('No new listings')
        exit()

    elif make_new_file == True:
        pass
    else:
        # print(new_listing)
        with open(bk_file, 'a', encoding='UTF-8', newline='') as f:
            fieldnames = ['Title', 'Link', 'M_Link', 'Price', 'Active/Sold', 'Thumbnail']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            for x in new_listing:
                print(x)
                writer.writerow(x)


def send_email():
    email = os.environ.get('') # enter enviroment variable details
    email_pw = os.environ.get('') # enter enviroment variable details
    recipient_email = '' # enter recipient email here
    body_text = ''
    # body text
    for x in new_listing:
        body_text = body_text + ("\n\n"
                                 "New listing details:\n"
                                 "{Title}\n"
                                 "{Link}\n"
                                 "{M_Link}\n"
                                 "{Price}\n"
                                 "{Active/Sold}\n"
                                 "{Thumbnail}".format(**x))

    if len(body_text) == 0:
        exit()
    else:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            smtp.login(email, email_pw)

            subject = ''  # enter the email subject text here
            body = body_text

            msg = f'Subject: {subject}\n\n{body}'
            smtp.sendmail(email, recipient_email, msg.encode(encoding='UTF-8'))


def main():
    check_listing()
    send_email()


if __name__ == "__main__":
    main()

