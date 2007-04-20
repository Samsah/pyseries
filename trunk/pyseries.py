from BeautifulSoup import BeautifulSoup
import time
import datetime
import urllib
import urllib2
import urlparse
import re
import sqlite
import os
import shutil
import google
import optparse
import sys

try:
    import yaml
except ImportError:
    print "PyYAML not found, please install from http://pyyaml.org/wiki/PyYAML"
    sys.exit(1)

class PySeries(object):

    CREATETABLE = "CREATE TABLE series (id INTEGER PRIMARY KEY, uid TEXT UNIQUE ON CONFLICT REPLACE, serie TEXT, season INTEGER, episode INTEGER, title TEXT, airdate DATE);"

    config = None
    db = None
    epRe=re.compile("(?P<no>[\d]+)\.[\s]+(?P<season>[\d]+)-[ ]?(?P<episode>[\d]+)[\s]+(?P<prodno>[\w-]+)?[\s]+(?P<date>[\d]{1,2} [\w]{3} [\d]{2})[\s]+<[^>]+>(?P<name>.*)</a>")
    
    def __init__(self, config, db):
        self.config = config;
        self.db = db

    def _get_seriedata(self, url):
        """Get serie name and all episodes from the given url
        
        @return serie name, episode data, last update day"""
        
        epdata = []

        f = urllib2.urlopen(url)
        bs = BeautifulSoup(f)

        # this will fail if the serie page has been redirected
        # epguides uses a dimwitted meta refresh instead of a proper one...
        try:
            seriename = bs.fetch("h1")[0].renderContents()
            seriename = re.sub("<.*?>", "", seriename) # remove HTML
        except IndexError:
            return

        # parse just the relevant parts with regexes
        filedata = bs.fetch("pre")[0].renderContents().split("\n")

        # regex-match the relevant parts
        for line in filedata:
            m = self.epRe.search(line)
            if m:
                # convert datestring to gmtime format
                t = time.strptime(m.group('date'), '%d %b %y')
            
                # put episode data into a nifty dict
                data = {'epno'    : m.group('no'),
                        'season'  : int(m.group('season')),
                        'episode' : int(m.group('episode')),
                        'prodno'  : m.group('prodno'),
                        'airdate' : m.group('date'),
                        'airdate2': datetime.date(t[0], t[1], t[2]),
                        'epname'  : m.group('name')}
                
                epdata.append(data)

        # name of serie, episode data and date of last check
        return seriename, epdata, datetime.date.today()
        
    def _search_serie(self, searchterms):
        """Pick a way to search for the serie"""
        
        try:
            return self._search_serie_api(searchterms) # the nice way
        except NoLicenseKey:
            return self._search_serie_http(searchterms) # The get-banned-on-your-first-cronjob way

    def _search_serie_api(self, searchterms):
        """Search for a serie using the Google SOAP API"""
        
        d = google.doGoogleSearch("site:epguides.com %s" % searchterms)
        return d.results[0].URL
            
    def _search_serie_http(self, searchterms):
        """Search for a serie and return its episode list page URL"""

        # google power!
        url = "http://www.google.com/search?hl=en&q=site:epguides.com%%20%s"
        search = "%s %s"
        search = urllib.quote(search % (searchterms, '"(a Titles and Air Dates Guide)"'))

        f = urllib.urlopen(url % search)
        bs = BeautifulSoup(f)
        print bs
        if not bs: return False

        results = []
    
        # tidy up the search results
        for url in bs.fetch("a", {"href":re.compile("http://epguides.com/")}):
            url = url['href']
        
            # only add serie summary pages (don't end with .html)
            if url.endswith("/"):
                results.append(url)

        if not results: return False

        # The first result is (usually) the correct one
        return results[0]

    def _cache_serie(self, serie, epdata, updatedate):
        """Parse the seriedata from the internets into sqlite"""
    
        con = sqlite.connect(self.db);
    
        for episode in epdata:
            cur = con.cursor()
            uid = "%s%d%d" % (serie, episode['season'], episode['episode'])
            cur.execute("INSERT INTO series (uid, serie, season, episode, title, airdate) VALUES (%s, %s, %d, %d, %s, date(%s));", (uid, serie, episode['season'], episode['episode'], episode['epname'], episode['airdate2'].strftime("%Y-%m-%d")))
            cur.close()

        # Commit & close
        con.commit()
        con.close()

        return serie

    def _save_serie_url(self, seriename, url):
        """Save the serie URL for reliable updates"""
        if os.path.exists(self.config):
            f = file(self.config, 'r')
            urls = yaml.load(f)
            f.close()
        else:
            urls = {}

        urls[seriename] = url

        # download to temp file to prevent file corruption
        f = file(self.config+'.tmp', 'w')
        yaml.dump(urls, f)
        f.close()
        
        shutil.move(self.config+'.tmp', self.config)

    def _delete_serie_url(self, seriename):
        if os.path.exists(self.config):
            f = file(self.config, 'r')
            urls = yaml.load(f)
            f.close()
        else:
            urls = {}

        if urls.has_key(seriename):
            del urls[seriename]

            # download to temp file to prevent file corruption
            f = file(self.config+'.tmp', 'w')
            yaml.dump(urls, f)
            f.close()
        
            shutil.move(self.config+'.tmp', self.config)
        
    def add_serie_by_name(self, seriename):
        """Try to find the serie homepage with a google search"""
        
        url = self._search_serie(seriename)
        if not url:
            print "No URL found for serie %s" % seriename
            return
        (serie, data, date) = self._get_seriedata(url)
        self._save_serie_url(serie, url)
        return self._cache_serie(serie, data, date)

    def add_serie_by_url(self, url):
        """Add serie directly via URL"""
        
        #if not url.startswith("http://epguides.com/"): return False
        
        (serie, data, date) = self._get_seriedata(url)
        self._save_serie_url(serie, url)
        return self._cache_serie(serie, data, date)

    def delete_serie_by_name(self, seriename):
        """Delete all data about a serie"""

        con = sqlite.connect(self.db)
        cur = con.cursor()
        cur.execute("DELETE FROM series WHERE serie='%s';" % seriename)
        cur.close()
        con.commit()
        con.close()
        
        self._delete_serie_url(seriename)
        return cur.rowcount

    def get_all_series(self):
        """Return a list of all cached series"""
        
        con = sqlite.connect(self.db)
        cur = con.cursor()
        cur.execute("select distinct serie from series;")

        serielist = []
        for i in cur:
            serielist.append(i[0])

        return serielist

    def update_all(self):
        """Update all series specified in the config file"""
        if os.path.exists(self.config):
            f = file(self.config, 'r')
            urls = yaml.load(f)
            f.close()

            for serie, url in urls.items():
                self.add_serie_by_url(url)
                print "recached %s from %s" % (serie, url)


def main():
    from optparse import OptionParser

    parser = OptionParser()

    parser.add_option("-u", "--update", action="store_true", help="Update all serie airdates")
    parser.add_option("-a", "--add", help="Add serie by name")
    parser.add_option("-d", "--delete", help="Remove serie by name")
    parser.add_option("-l", "--list", action="store_true", help="List series in DB")
    parser.add_option("--url", help="Add serie by URL")
    parser.add_option("--db", help="Path to the sqlite database")
    parser.add_option("--conf", help="Path to the url config")
    
    (options, args) = parser.parse_args()

    # default db & urlconf locations
    if not options.db:
        options.db = os.path.join(sys.path[0], "series.db")
    if not options.conf:
        options.conf = os.path.join(sys.path[0], "series.urls")

    ps = PySeries(options.conf, options.db)

    if options.update:
        ps.update_all()
    elif options.list:
        print " | ".join(ps.get_all_series())
    elif options.add:
        print "Added %s" % ps.add_serie_by_name(options.add)
    elif options.delete:
        print "Deleted %d row(s)" % ps.delete_serie_by_name(options.delete)
    elif options.url:
        print "Added %s" % ps.add_serie_by_url(options.url)
    else:
        print "gief options."
    
if __name__ == "__main__":
    main()
