import logging
import os
from datetime import datetime
from decimal import Decimal

import requests

from Money import Money

import xml.etree.ElementTree as ET


class NoCacheFound(BaseException):
    pass


class CurrencyConverter:

    PATTERN = 'http://www.hmrc.gov.uk/softwaredevelopers/rates/exrates-monthly-{suffix}.XML'

    cache = {}

    def __init__(self, money: Money) -> None:
        self.money = money

    def convert_to_gbp(self, transaction_date: datetime) -> Money:
        rate = self.get_rate_to_gbp(transaction_date)
        new_amount = self.money.amount / rate
        return Money(new_amount, 'GBP')

    def get_rate_to_gbp(self, transaction_date: datetime) -> Decimal:
        currency = self.money.currency
        if currency == 'GBP':
            return Decimal(1)
        if currency == 'GBX':
            return Decimal(100)

        if not self.__is_rate_cached(transaction_date):
            self.__fetch_and_cache_xml_rate(transaction_date)

        return self.__get_cached_rate(transaction_date)

    def __is_rate_cached(self, date: datetime) -> bool:
        try:
            self.__get_cached_rate(date)
        except NoCacheFound as error:
            logging.warning(error)
            return False

        return True

    def __get_rate_from_cache(self) -> Decimal:
        pass

    def __fetch_and_cache_xml_rate(self, date: datetime):
        self.__fetch_xml_file(date)
        self.__parse_rate_file(date)

    def __fetch_xml_file(self, date):
        response = requests.get(self.PATTERN.format(suffix=self.__get_month_year_suffix(date)), stream=True)
        cache_file_path = self.__get_cache_tile_path(date)
        with open(cache_file_path, 'wb') as file:
            file.write(response.content)

    def __get_cached_rate(self, date: datetime) -> Decimal:
        cache_file_path = self.__get_cache_tile_path(date)
        if not os.path.exists(cache_file_path):
            raise NoCacheFound('Cache file for {amount} is not found: {file}'.format(amount=self.money, file=cache_file_path))

        return self.__parse_rate_file(date)

    def __parse_rate_file(self, date):
        cache_file_path = self.__get_cache_tile_path(date)
        tree = ET.parse(cache_file_path)

        root = tree.getroot()
        for item in root.findall("./exchangeRate[currencyCode='{currency}']".format(currency=self.money.currency)):
            return Decimal(item.find('rateNew').text)

    def __get_cache_tile_path(self, date: datetime) -> str:
        return './converters/currency/data/{suffix}.xml'.format(suffix=self.__get_month_year_suffix(date))

    def __get_month_year_suffix(self, date: datetime) -> str:
        month = date.strftime('%m')
        year = date.strftime('%y')
        return '{}{}'.format(month, year)




