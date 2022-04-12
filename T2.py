# InputData.xlsx, worksheet Fround contains a list of 50 articles dealing with the founding round. In the
# worksheet, the candidate will find the name of the organization, the website, the link to news covering
# the funding round of the company and the company unique identifier (client_id).
# The candidate shall create a Python script to to extract the below information for each of the news_url
# listed:
# 1. The amount of the round as float (preferably denominated in original currency - in the case
# above SEK);
# 2. The date of the round as Timestamp - the article publication date;
# 3. The investors taking part in the round.
# Please note that point 3 is OPTIONAL.
#
import re
import pandas as pd
import logging
import Utils
from bs4 import BeautifulSoup as bs
import csv
from dateutil import parser
import datetime

def get_date_pt():
    """ Get the regex pattern to locate a date in the text"""
    month_letters = "(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)([a-z])*"
    dd_mm_numbers = "(\d{1,2})"
    day_ordinal = "(\d{1,2})(st|nd|rd|th)"
    year = "(\d{2,4})"

    date_pt = re.compile("(" + dd_mm_numbers+"[/\-]" + dd_mm_numbers + "[/\-]"+ year +
                         ")|(" + year + " [/\-]" + dd_mm_numbers + "[/\-]" + dd_mm_numbers +
                         ")|(" + month_letters + "(((\s)the)?\s)?" + "("+day_ordinal+"|"+dd_mm_numbers+")" + "[(\s),]+" + year +
                         ")|(" + day_ordinal + "( of )*" + month_letters + "\s" + year + ")")

    return date_pt


def get_money_pt():
    """The regex for amounts of money, with currency. One for URLs, one for text"""
    all_currency_symbols = "(CHF|DKK|SEK|NOK|kr|EUR|€|GBP|£|PLN|zł|TRY|UAH|ILS|CAD|CLP|USD|\$|AUD|CNY|¥|HK$|INR|₹|SGD|JPY|" \
                           "BTC|XBT|₿|ETH|Ξ)"
    numbers = "("+ "([0-9,.])+" + ")|(" + "(one|two|three|four|five|six|seven|eight|nine|ten)(\s)?" + ")"
    numbers_and_currency = "(" + numbers + all_currency_symbols + "|" + all_currency_symbols + numbers + ")"
    text_money_pt = re.compile(numbers_and_currency + '( digit )?'
                                '([mM]|(\s(million(s)?|Million(s)?|thousand(s)?)))')

    # url_money_pt = re.compile("(\d){1,2}(-(\d){1,2})?(-)?([mM](illion)?)")

    return text_money_pt



def exe():
    Utils.init_logging("FundingRounds.log")
    rounds_df = pd.read_excel("InputData.xlsx", sheet_name=1)
    rounds_df = rounds_df[0:20]

    f = open('FundingRounds.csv', 'w', newline='')
    writer = csv.writer(f)
    writer.writerow(["client_id","news_url","funding", "date"])  # add the date next

    driver = Utils.get_webdriver()

    for i, row in rounds_df.iterrows():
        news_url = row["news_url"]
        try:
            driver.get(news_url)
        except Exception as e:
            logging.warning(e)
            continue

        soup = bs(driver.page_source, features="lxml")
        visible_text = soup.getText(separator=" ")
        # logging.info(visible_text + "***\n")
        text_money_pt = get_money_pt()

        all_mentions_of_money = list(set([mtc.group(0).lower() for mtc in re.finditer(text_money_pt, visible_text)]))
        if len(all_mentions_of_money) > 0:
            funding = all_mentions_of_money[0]  # get the first. The next ones may be total funding, investor etc.
            logging.info(all_mentions_of_money)
        else:
            funding = []

        date_pt = get_date_pt()
        time_elem = soup.find("time")
        if time_elem is not None:
            time_txt = time_elem.string
            date_str = str(parser.parse(time_txt, fuzzy=True))
        else:
            time_txt = visible_text
            all_dates = list(set([mtc.group(0) for mtc in re.finditer(date_pt, time_txt)]))
            if len(all_dates) > 1:
                date_str = all_dates[0]  # pick the first
            else:  # we did not find it in the text. Maybe the URL has it
                date_str = "not found"
                logging.info(time_txt)

        if i % (len(rounds_df) // 5) == 0:
            logging.info(str(i) + "/" + str(len(rounds_df))+ "...")
        writer.writerow([row["client_id"], row["news_url"], funding, date_str])




