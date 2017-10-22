from cement.core.controller import CementBaseController, expose
import requests
import xml.etree.ElementTree as etree
import re
from datetime import datetime, timedelta


class AlobgController(CementBaseController):
    source_url = 'https://www.alo.bg/obiavi/imoti-naemi/apartamenti/?region_id=16&location_ids=3333&price=500_700_BGN&after_date=%s&order_by=time-desc&page=%s'
    # after_date = dd.mm.yyyy, page = d

    class Meta:
        label = 'alobg'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'Loader from alo.bg'

    def load_html(self, url):
        r = requests.get(url)
        r.encoding = "utf-8"
        return r.content.decode('utf-8', "ignore")

    def process_prop_info(self, info):
        # print('load prop page, url=%s' % info['url'])
        html_content = self.load_html(info['url'])
        # print(len(html_content))

        # find first <div class=contacts", remove all html tags and check for agency keywords
        # имоти, агенц, оод, брокер, imot, agenc
        contacts = re.search('<div\s+class=".*?contacts">(?P<name>.*?)'
                             '(?P<wrapper><div class="contacts_wrapper">.*?)<!--BEGIN more user ads-->',
                             html_content, re.I | re.DOTALL)
        # print('after contacts search')
        # print(contacts.groupdict())
        contact_str = re.sub(r'<.*?>', ' ', contacts.group('name'), re.DOTALL).strip()
        test = re.search(r'(имоти|агенц|оод|брокер|imot|agenc|broker)', contact_str, re.I | re.DOTALL)
        if test:
            # print('found agency keyword in name "%s"' % contact_str)
            # print(test.group())
            return None

        # check div class=cotacts_wrapper, if there is a link to website - it is an agency
        if re.search(r'<div class="contacts_wrapper">.*?contact_row'
                     r'.*?<img src=".*?(website).*?\.svg".*icon-contacts">',
                     contacts.group('wrapper'), re.I | re.DOTALL):
            # print('found website icon')
            return None

        p = re.search(r'<div class="contacts_wrapper">.*?contact_row'
                      r'.*?<a href="tel:(?P<phone>\d+)">',
                      contacts.group('wrapper'), re.I | re.DOTALL)
        if not p:
            None
        info['phone'] = p.group('phone')
        return info

    def parse(self):
        page = 0
        found = []
        meet_end = False
        date = (datetime.today() - timedelta(days=7)).strftime('%d.%m.%Y')

        p = re.compile('<tr\s+id="adrows_\d+".*?</tr><tr\s+class="adrows_\d+.*?</tr>', re.I | re.DOTALL)
        tp = re.compile('<tr\s+id="adrows_(?P<id>\d+)"'
                        '.*?<a\s+title="(?P<title>.*?)".*?href="(?P<url>/\d+)">'
                        '.*?<div\s+id="price_\d+".*?<span\s+class="price_listing">'
                        '<span class="nowrap">(?P<price>\d+\s*\w+).*</div>'
                        # '(?P<have_img><img\s+title=".*?/>)?'
                        ,
                        re.I | re.DOTALL)
        while page < 10 and not meet_end:
            page += 1
            self.app.log.debug('alobg. loading page #%s' % page)
            html_content = self.load_html(self.source_url % (date, page))
            # print(html_content)
            tables = p.finditer(html_content)
            for table in tables:
                # print(table.group())
                info = tp.search(table.group()).groupdict()
                if re.search(r'<tr\s+id="adrows_\d+"\s+class=".*?viptr.*?"', table.group()) or \
                        re.search(r'<div\s+id="price_\d+".*?</div><img\s+title=".*?/>', table.group()):
                    # print('has viptr in class or image after price')
                    continue
                info['url'] = "https://www.alo.bg%s" % info['url']
                info['source'] = 'alobg'
                prop = self.app.db.get_property(info['source'], info['id'])
                if prop:
                    meet_end = True
                    break

                info = self.process_prop_info(info)
                if info:
                    found.append(info)
                    self.app.db.insert_property(info)
                    self.app.telegram_send_property(info)
                    self.app.log.debug("alobg. found new private property")

        if meet_end:
            self.app.log.debug("alobg. met the end at page #%s" % page)
        return found

    @expose(hide=True)
    def default(self):
        self.app.log.info("start Alo.bg parser")
        from time import sleep
        self.app.daemonize()

        count = 0
        while True:
            count += 1
            found = self.parse()
            self.app.log.info("alobg found %s private properties" % len(found))
            interval = self.app.config.get('loader', 'load_interval')
            sleep(int(interval))

