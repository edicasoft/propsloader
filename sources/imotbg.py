from cement.core.controller import CementBaseController, expose
import requests
import xml.etree.ElementTree as etree
import re


class ImotbgController(CementBaseController):
    source_url = 'https://www.imot.bg/pcgi/imot.cgi?act=3&slink=35mi7t&f1=%s'  # page

    class Meta:
        label = 'imotbg'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'Loader from imot.bg'

    def load_html(self, url):
        r = requests.get(url)
        r.encoding = "windows-1251"
        return r.content.decode('windows-1251', "ignore")

    def process_prop_info(self, info):
        html_content = self.load_html(info['url'])
        if not re.search(r'<div style=".*?<b>(Частно лице|Строителна)', html_content, re.I | re.DOTALL):
            return None

        p = re.compile('<img src=".*?phone-ico.gif".*?<span.*?>.*?(?P<phone>\d+).*?</span>',
                       re.I | re.DOTALL)
        info['phone'] = p.search(html_content).group('phone')
        return info

    def parse(self):
        page = 0
        found = []
        meet_end = False
        while page < 10 and not meet_end:
            page += 1
            self.app.log.debug('imotbg. loading page #%s' % page)
            html_content = self.load_html(self.source_url % page)
            p = re.compile('<table width=660.*?<div class="price".*?</table>', re.I | re.DOTALL)
            tp = re.compile('<a href="//www\.imot\.bg/pcgi/imot\.cgi\?act=5&adv=(?P<id>\w+)&.*?class="photoLink"'
                            '.*?<div class="price">\s*(?P<price>\d+\s*\w+)'
                            '.*?<a href="//(?P<url>.*?)" class="lnk1">(?P<title>.*?)</a>'
                            '.*?<td align="right".*?>(?P<is_vip>.*?)</td>'
                            '.*?<td align="right".*?>(?P<is_agency>.*?)</td>',
                            re.I | re.DOTALL)
            tables = p.finditer(html_content)
            for table in tables:
                info = tp.search(table.group()).groupdict()
                info['url'] = "https://%s" % info['url']
                if re.search(r'(vip_sm\.gif|top_sm\.gif)', info["is_vip"]) or \
                        re.search(r'<a href', info["is_agency"]):
                    continue

                prop = self.app.db.get_property(info['id'])
                if prop:
                    meet_end = True
                    break

                info = self.process_prop_info(info)
                if info:
                    info['source'] = 'imotbg'
                    found.append(info)
                    self.app.db.insert_property(info)
                    self.app.telegram_send_property(info)
                    self.app.log.debug("imotbg. found new private property")

        if meet_end:
            self.app.log.debug("imotbg. met the end at page #%s" % page)
        return found

    @expose(hide=True)
    def default(self):
        self.app.log.info("start Imot.bg parser")
        from time import sleep
        self.app.daemonize()

        count = 0
        while True:
            count += 1
            found = self.parse()
            self.app.log.info("found %s private properties" % len(found))
            interval = self.app.config.get('loader', 'load_interval')
            sleep(int(interval))

