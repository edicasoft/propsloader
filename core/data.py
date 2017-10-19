import MySQLdb
import MySQLdb.cursors


class Database:
    def __init__(self, config):
        self.config = {
            "port": 3306,
            "host": "localhost"
        }
        self.config.update(config)
        self._db = MySQLdb.connect(host=self.config["host"],
                                   user=self.config["user"],
                                   port=self.config["port"],
                                   passwd=self.config["password"],
                                   db=self.config["database"],
                                   charset='utf8', init_command='SET NAMES UTF8; SET time_zone = "+00:00";',
                                   cursorclass=MySQLdb.cursors.DictCursor)

    def save_log(self, level, msg):
        """
        save log message
        :param level:
        :param msg:
        :return:
        """
        c = self._db.cursor()
        c.execute("""insert into parser_logs (level, msg)
                                      values (%s, %s)""",
                  (level, msg,))
        new_id = c.connection.insert_id()
        self._db.commit()
        return new_id

    def get_property(self, id):
        """
        simple select property by id
        :param code: property ID
        :return: row as dictionary or None
        """
        # print(id)
        c = self._db.cursor()
        c.execute("""select id, source, created, title, phone, url FROM properties
                 WHERE id = %s""", (id,))
        row = c.fetchone()
        return row

    def insert_property(self, data):
        """
        insert property
        :param data: dict
        :return: inserted ID
        """
        c = self._db.cursor()
        c.execute("""insert into properties (id, source, title, phone, url)
                              values (%s, %s, %s, %s, %s)""",
                  (data["id"], data["source"], data["title"].encode("cp1251").decode('cp1251').encode('utf8'), data["phone"], data["url"]))
        new_id = self._db.insert_id()
        self._db.commit()
        return new_id

    def get_event(self, eid):
        """
        simple select event by id
        :param eid: event ID
        :return: row as dictionary or None
        """
        c = self._db.cursor()
        c.execute("""select id, name, start_at FROM events
                 WHERE id = %s""", (eid,))
        row = c.fetchone()
        return row

    def find_event(self, event_data):
        """
        find event
        :param event_data: dict with event data it has to contain keys:
            "start_at" - date and time in MyuSQL datetime format '%Y-%m-%d m:i:s'
            "home" - team name playing home (team1)
            "away" - team name playing away (team2)
        :return dict:
        """
        # get events by datetime
        self._db.query("""select id, name, home, away FROM events
                 WHERE start_at = '%s'""" % event_data['start_at'])
        r = self._db.store_result()
        result = None
        for row in r.fetch_row(maxrows=0, how=1):
            # match a game with event using at least 1 team name
            if row['home'] == event_data['home'] or row['home'] == event_data['away'] \
                    or row['away'] == event_data['home'] or row['away'] == event_data['away']:
                result = row
                break
        return result

    def insert_event_article(self, event):
        """
        insert new article related to the event
        :param event:
        :return: article_id
        """
        a = prepare_event_article(event)
        c = self._db.cursor()
        c.execute("""insert into article (event_id, slug, title, body, category_id,
                      status, created_at, published_at,
                      meta_title, meta_description, meta_keywords, created_by)
                              values (%s, %s, %s, %s, %s,
                              %s, %s, %s,
                              %s, %s, %s, %s)""",
                  (a['event_id'], a['slug'], a['title'], a['body'], a['category_id'],
                a['status'], a['created_at'], a['published_at'],
                a['meta_title'], a['meta_description'], a['meta_keywords'], a['created_by']))
        # print(c._last_executed)
        new_id = c.connection.insert_id()
        self._db.commit()
        return new_id

    def insert_tournament_article(self, tournament):
        """
        insert new article related to the event
        :param event:
        :return: article_id
        """
        a = prepare_tournament_article(tournament)
        c = self._db.cursor()
        c.execute("""insert into article (tournament_id, slug, title, body, category_id,
                      status, created_at, published_at,
                      meta_title, meta_description, meta_keywords, created_by)
                              values (%s, %s, %s, %s, %s,
                              %s, %s, %s,
                              %s, %s, %s, %s)""",
                  (a['tournament_id'], a['slug'], a['title'], a['body'], a['category_id'],
                   a['status'], a['created_at'], a['published_at'],
                   a['meta_title'], a['meta_description'], a['meta_keywords'], a['created_by']))
        new_id = c.connection.insert_id()
        self._db.commit()
        return new_id

    def insert_event(self, e):
        """
        insert new event
        :param event_data: dict with event data
        :return: inserted row
        """
        # print("insert event")
        c = self._db.cursor()
        c.execute("""insert into events (tournament_id, name, start_at, home, away)
                      values (%s, %s, %s, %s, %s)""",
                  (e["tournament_id"], e["name"], e["start_at"], e["home"], e["away"]))
        new_id = c.connection.insert_id()
        self._db.commit()
        e = self.get_event(new_id)
        self.insert_event_article(e)
        return e

    def get_koeff(self, bookmaker_id, event_id, bet_type):
        self._db.query("""select ek.* FROM event_koeffs ek, bet_types bt
                         WHERE ek.bookmaker_id = %d and ek.event_id = %d
                         and ek.bet_type_id = bt.id and bt.code='%s'""" %
                       (bookmaker_id, event_id, bet_type))
        r = self._db.store_result()
        row = r.fetch_row(how=1)
        return row[0] if len(row) == 1 else None

    def insert_koeff(self, bookmaker_id, event_id, bet_type, bm_event_id, value):
        """
        insert koeff for particular bookmaker, event, bet code
        :param bookmaker_id:
        :param event_id:
        :param bet_type:
        :param bm_event_id:
        :param value:
        :return: inserted ID
        """
        # print("insert koeff", [bet_type, value])
        self._db.query("""select id FROM bet_types
                          WHERE code='%s'""" % bet_type)
        r = self._db.store_result()
        bet_type_id = r.fetch_row(how=1)[0]["id"]
        c = self._db.cursor()
        c.execute("""insert into event_koeffs (bookmaker_id, event_id, bet_type_id, bm_event_id, value)
                     values (%s, %s, %s, %s, %s)""",
                  (bookmaker_id, event_id, bet_type_id, bm_event_id, value))
        new_id = c.connection.insert_id()
        self._db.commit()
        return new_id

    def update_koeff(self, koeff_id, value):
        """
        update koeff with value by id
        :param koeff_id:
        :param value:
        :return:
        """
        # print("update koeff", koeff_id, value)
        c = self._db.cursor()
        res = c.execute("""update event_koeffs set value=%s
                     where id = %s""",
                        (value, koeff_id))
        self._db.commit()
        return res

    def save_event_koeffs(self, bookmaker_id, event_id, bm_event_id, koeffs):
        """
        update event koeffs for bookmaker
        :param bookmaker_id: int
        :param event_id: int
        :param koeffs: dict, ex: {"bet_type":"1", "value":2.3, "bm_event_id": 1212121212}
        :return:
        """
        for k in koeffs:
            kr = self.get_koeff(bookmaker_id, event_id, k["bet_type"])
            if kr is None:
                self.insert_koeff(bookmaker_id, event_id, k["bet_type"], bm_event_id, k["value"])
            elif float(kr["value"]) != float(k["value"]):
                self.update_koeff(kr["id"], k["value"])

        return True
