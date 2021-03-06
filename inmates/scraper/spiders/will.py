import ipdb

from pprint import pprint
from scrapy import Request
from scrapy import Spider
from urllib.parse import urlparse


class WillSpider(Spider):
    """
    NOTE: court information is available though not being scraped
    """

    name = "will"

    def __init__(self, *args, **kwargs):
        self.domain = kwargs.get("domain")
        self.start_urls = ["https://www.willcosheriff.org/,http://66.158.72.230/NewWorld.InmateInquiry/Public"]
        self.parsed_urls = [urlparse(url) for url in self.start_urls]

    def parse(self, response):
        table_body = response.xpath('//*[@id="Inmate_Index"]/div[2]/div[2]/table/tbody')[0]
        rows = table_body.xpath("tr")
        parsed_url = self.parsed_urls[0]
        for row in rows:
            profile_url = self.extract_profile_url(row)
            yield Request(url=profile_url, callback=self.parse_profile)

        next_page_path = response.xpath('//*[@id="Inmate_Index"]/div[2]/div[3]/a[3]/@href').get()
        if next_page_url is not None:
            yield response.follow(response.urljoin(next_page_path), callback=self.parse)

    def parse_profile(self, response):
        demography = response.xpath('//div[@id="DemographicInformation"]/ul/li')
        demographic_info = self.parse_demographic_data(demography)
        bookings = response.xpath('//div[@id="BookingHistory"]/div[@class="Booking"]')
        booking_data = [self.parse_booking_data(booking) for booking in bookings]
        demographic_info["Bookings"] = booking_data
        yield demographic_info

    def parse_demographic_data(self, demography):
        demographic_info = {}
        for element in demography:
            key = element.xpath("label/text()").get()
            value = element.xpath("span/text()").get()
            demographic_info.update({key: value})
        return demographic_info

    def parse_booking_data(self, booking):
        booking_data = booking.xpath('./div[@class="BookingData"]')
        booking_info = self.parse_booking_info(booking_data)
        bond_info = self.parse_bond_info(booking_data)
        booking_info["Bonds"] = bond_info
        charge_info = self.parse_charge_info(booking_data)
        booking_info["Charges"] = charge_info
        return booking_info

    def parse_bond_info(self, booking_data):
        bond_info = []
        keys = booking_data.xpath('./div[@class="BookingBonds"]//table/thead//th/text()').getall()
        vals = booking_data.xpath('./div[@class="BookingBonds"]//table/tbody//td/text()').getall()
        for row in booking_data.xpath('./div[@class="BookingBonds"]//table/tbody/tr'):
            vals = row.xpath("./td/text()").getall()
            bond_info.append(dict(zip(keys, vals)))
        return bond_info

    def parse_booking_info(self, booking_data):
        booking_info = {}
        for element in booking_data.xpath('./ul[@class="FieldList"]/li'):
            key = element.xpath("label/text()").get()
            value = element.xpath("span/text()").get()
            booking_info.update({key: value})
        return booking_info

    def parse_charge_info(self, booking_data):
        charge_info = []
        keys = booking_data[0].xpath('./div[@class="BookingCharges"]//table/thead//th/text()').getall()
        for row in booking_data.xpath('./div[@class="BookingCharges"]//table/tbody/tr'):
            vals = row.xpath("./td/text()").getall()
            charge_info.append(dict(zip(keys, vals)))
        return charge_info

    def extract_profile_url(self, row):
        path = row.xpath('./td[@class="Name"]/a/@href').get()
        return self.gen_url(path)

    def gen_url(self, path):
        parsed_url = self.parsed_urls[0]
        url_root = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return f"{url_root}{path}"
