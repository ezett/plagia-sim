#!/usr/bin/env python
# -*- coding: utf-8 -*-
# LAParams good defaults: -F -0.5 -M 4.0 -W 0.15 -L 2.63
import sys, re, traceback
import HTMLParser
from io import BytesIO
from cStringIO import StringIO
from urllib2 import urlopen, Request, URLError, unquote
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdftypes import PDFException
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from pdfminer.image import ImageWriter

# DOI
DOI_REGEX = r"""DOI:\s?([^\s,]+)"""

# URL
#URL_REGEX = (r'(?:https?://|www\.)(?:[^\s<>"\(\)]+(?:\([^\s<>"\(\)]+\)'
#    ')?)+[^\s<>"\(\)\.,;”“]')
URL_REGEX = (r'(?i)\b(?:https?:(?:/{1,3}|[a-z0-9%])|www\.)(?:(?:[a-z0-9.\-]+[.]'
    '(?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|muse'
    'um|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at'
    '|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|'
    'cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|d'
    'z|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm'
    '|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|'
    'it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|l'
    'u|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz'
    '|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|'
    'pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|s'
    'r|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz'
    '|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s'
    '()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]'
    '*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’])|(?:'
    '(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia'
    '|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|a'
    'd|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi'
    '|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|'
    'cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|f'
    'm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn'
    '|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|'
    'kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|m'
    'n|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz'
    '|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|'
    'sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|t'
    'h|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn'
    '|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))')



class HTML2Text(HTMLParser.HTMLParser):
    """
    extract text from HTML code
    """
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.output = StringIO()
    def get_text(self):
        """get the text output"""
        return self.output.getvalue()
    def handle_starttag(self, tag, attrs):
        """handle <br> tags"""
        if tag == 'br':
            # Need to put a new line in
            self.output.write('\n')
    def handle_data(self, data):
        """normal text"""
        self.output.write(data.encode('utf-8'))
    def handle_endtag(self, tag):
        if tag == 'p':
            # end of paragraph. Add newline.
            self.output.write('\n')


# WEB to string
class WEBstringifier:

    def web2txt(self, url):
        if not re.match(URL_REGEX, url): return ''

        if url.startswith('www.'): url = 'http://' + url
        try:
            self.request = Request(url, headers={
                'User-Agent': ('Mozilla/5.0 (X11;Linux x86_64) AppleWebKit/'
                    '537.11 (KHTML, like Gecko)Chrome/23.0.1271.64 Safari/537.11'),
                'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.'
                    '9,*/*;q=0.8'),
                'Accept-Charset': 'utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding': 'none', 'Accept-Language': 'de-DE,de;q=0.8',
                'Connection': 'keep-alive'})
            connection = urlopen(self.request)
            webstr = connection.read()

            if webstr.startswith('%PDF'):
                return webstr

            encoding = connection.headers.getparam('charset')
            if encoding is None:
                try:
                    from feedparser import _getCharacterEncoding as enc
                except ImportError:
                    enc = lambda x, y: ('utf-8', 1)
                encoding = enc(connection.headers, webstr)[0]
                if encoding == 'us-ascii':
                    encoding = 'utf-8'

        # either:
        #    webstr = webstr.decode(encoding).encode('utf-8')
        #    webstr = re.sub('<[^<]+?>', ' ', webstr)
        #    webstr = (webstr.replace('&#228;', 'ä').replace('&#246;',
        #            'ö').replace('&#252;', 'ü').replace('&#196;',
        #                    'Ä').replace('&#214;', 'Ö').replace('&#220;',
        #                            'Ü').replace('&#223;', 'ß'))

        # or:
        #    html2txt = HTML2Text()
        #    html2txt.feed(webstr.decode(encoding))
        #    webstr = html2txt.get_text()
        #    html2txt.close()

        # or:
        #    import html2text
        #    html2txt = html2text.HTML2Text()
        #    html2txt.ignore_images = True
        #    html2txt.ignore_links = True
        #    webstr = html2txt.handle(webstr.decode(encoding)).encode('utf-8')
        #    webstr = re.sub(r'(?:#+ | *\* |\*\*)', '', webstr)

        # or:
            from bs4 import BeautifulSoup, SoupStrainer, Comment
            soup = BeautifulSoup(webstr, "html.parser",
                    parse_only=SoupStrainer('body'), from_encoding=encoding)
            for script in soup(['script', 'style']):
                script.extract()
            for element in soup(text=lambda text: isinstance(text, Comment)):
                element.extract()
            webstr = soup.get_text().encode('utf-8')
            lines = (line.strip() for line in webstr.splitlines())
            webstr = '\n'.join(line for line in lines if line)


        #    # remove all the empty lines and leading/trailing white spaces from
        #    # the raw extracted text add back the newline character to each line
        #    raw_list = webstr.splitlines()
        #    new_list = []
        #    for line in raw_list:
        #        line = line.strip()
        #        if line != '':
        #            line = line + '\n'
        #            new_list.append(line)
        #    #print new_list  # test only
        #    webstr = "".join(new_list)

            return webstr
        except:
            print 'Exception in ' + url
            traceback.print_exc(file=sys.stdout)
            return ''


# PDF to string
class PDFstringifier:

    def __init__(self, opts):
        # debug option
        self.debug = 0
        # input option
        self.password = ''
        self.pagenos = set()
        self.maxpages = 0
        # output option
        self.outtype = None
        self.outfile = None
        self.imagewriter = None
        self.rotation = 0
        self.layoutmode = 'normal'
        self.codec = 'utf-8'
        self.pageno = 1
        self.scale = 1
        self.caching = True
        self.showpageno = True
        self.laparams = LAParams()
        self.webstringifier = WEBstringifier()

        # LAParams good defaults: -F -0.5 -M 4.0 -W 0.15 -L 2.63
        self.laparams.boxes_flow = float("-0.5")
        self.laparams.char_margin = float("4.0")
        self.laparams.word_margin = float("0.15")
        self.laparams.line_margin = float("2.63")

        for (k, v) in opts:
            if k == '-d': self.debug += 1
            elif k == '-p': self.pagenos.update( int(x)-1 for x in v.split(',') )
            elif k == '-m': self.maxpages = int(v)
            elif k == '-P': self.password = v
            elif k == '-C': self.caching = False
            elif k == '-t': self.outtype = v
            elif k == '-o': self.outfile = v
            elif k == '-n': self.laparams = None
            elif k == '-A': self.laparams.all_texts = True
            elif k == '-V': self.laparams.detect_vertical = True
            elif k == '-M': self.laparams.char_margin = float(v)
            elif k == '-L': self.laparams.line_margin = float(v)
            elif k == '-W': self.laparams.word_margin = float(v)
            elif k == '-F': self.laparams.boxes_flow = float(v)
            elif k == '-Y': self.layoutmode = v
            elif k == '-O': self.imagewriter = ImageWriter(v)
            elif k == '-R': self.rotation = int(v)
            elif k == '-c': self.codec = v
            elif k == '-s': self.scale = float(v)

        if not self.outtype:
            self.outtype = 'text'
            if self.outfile:
                if (self.outfile.lower().endswith('.htm') or
                        self.outfile.lower().endswith('.html')):
                    self.outtype = 'html'
                elif self.outfile.lower().endswith('.xml'):
                    self.outtype = 'xml'


    def resetLAParams(self):
        self.laparams = LAParams()


    def pdf2str(self, txttools, fname):
        if not fname.lower().endswith('.pdf'): return ''

        PDFDocument.debug = self.debug
        PDFParser.debug = self.debug
        CMapDB.debug = self.debug
        PDFResourceManager.debug = self.debug
        PDFPageInterpreter.debug = self.debug
        PDFDevice.debug = self.debug
        rsrcmgr = PDFResourceManager(caching=self.caching)
        retstr = BytesIO()

        if self.outtype == 'text':
            device = TextConverter(rsrcmgr, retstr, codec=self.codec,
                                   laparams=self.laparams,
                                   imagewriter=self.imagewriter)
        elif self.outtype == 'html':
            device = HTMLConverter(rsrcmgr, retstr, codec=self.codec,
                                   scale=self.scale, layoutmode=self.layoutmode,
                                   laparams=self.laparams,
                                   imagewriter=self.imagewriter)
        elif self.outtype == 'xml':
            device = XMLConverter(rsrcmgr, retstr, codec=self.codec,
                                  laparams=laparams, imagewriter=imagewriter)
        else:
            return usage()
        if txttools.is_http_url(fname):
            webstr = self.webstringifier.web2txt(fname)
            fp = BytesIO(webstr)
        else:
            fp = file(fname, 'rb')

        interpreter = PDFPageInterpreter(rsrcmgr, device)
        try:
            for page in PDFPage.get_pages(fp, self.pagenos,
                maxpages=self.maxpages, password=self.password,
                    caching=self.caching, check_extractable=True):
                page.rotate = (page.rotate+self.rotation) % 360
                interpreter.process_page(page)

                # Collect URL annotations
                try:
                    if page.annots and isinstance(page.annots, list):
                        for annot in page.annots:
                            a = annot.resolve()
                            if "A" in a and "URI" in a["A"]:
                                ref = a["A"]["URI"].decode("utf-8").encode("utf-8")
                                txttools.references.add(ref)
                except Exception as e:
                    retstr = BytesIO()
                    print "Annotation Exception with " + fname + " ..."

        except PDFException:
            retstr = BytesIO()
            print "PDFException with " + fname + " ..."

        fp.close()
        device.close()

        strg = retstr.getvalue()
        retstr.close()

        return strg


class TXTtools:

    def __init__(self, opts):
        self.ligatures = {0xFB00: u'ff', 0xFB01: u'fi', 0xFB02: u'fl', 0xFB03:
            u'ffi', 0xFB04: u'ffl', 0xFB05: u'ft', 0xFB06: u'st'}
        self.utf8oddity = {0x00A0: u' '}
        self.webstringifier = WEBstringifier()
        self.pdfstringifier = PDFstringifier(opts)
        self.references = set()
        self.metadata = {}


    def file2txt(self, fname):
        txt = ''

        if fname.lower().endswith('.pdf'):
            txt = self.pdfstringifier.pdf2str(self, fname)
            txt = txt.decode('utf-8')
            txt = txt.translate(self.ligatures)
            txt = txt.translate(self.utf8oddity)
            txt = (txt.replace(u'¨a', u'ä').replace(u'¨o', u'ö').replace(u'¨u',
                u'ü').replace(u'¨A', u'Ä').replace(u'¨O', u'Ö').replace(u'¨U',
                    u'Ü'))
            txt = txt.encode('utf-8')
        elif self.is_http_url(fname):
            txt = self.webstringifier.web2txt(fname)
        else:
            txt = file(fname, 'rb').read()
            txt = txt.decode('utf-8')
            txt = txt.translate(self.ligatures)
            txt = txt.translate(self.utf8oddity)
            txt = (txt.replace(u'¨a', u'ä').replace(u'¨o', u'ö').replace(u'¨u',
                u'ü').replace(u'¨A', u'Ä').replace(u'¨O', u'Ö').replace(u'¨U',
                    u'Ü'))
            txt = txt.encode('utf-8')

        txt = re.sub(r'\r\n?', r'\n', txt)
        txt = re.sub((r'(\s(?!http|www)\S+?[a-zäöü])-([\n\t])\s*(?!oder|und)('
            '[a-zäöü]\S*)\s'), '\\1\\3\\2', txt)
        txt = re.sub(r'(?:[0-9]{1,3}\n+)?\f+', '', txt)
        txt = re.sub(r'\n\s*\n\s*[\n\s]+', r'\n\n', txt)
        txt = re.sub(r'[ \t]*(\n+)[ \t]*', '\\1', txt)
        txt = re.sub(r' *\t+ *', '\t', txt)
        txt = re.sub('  +', ' ', txt)

        return txt

    def extract_urls(self, txt):
        text = re.sub(r'([,?!"])\n', r'\1 ', txt).replace('\n', '')
        urls = re.findall(URL_REGEX, text, re.IGNORECASE) + \
            ["http://dx.doi.org/" + url for url in re.findall(DOI_REGEX, text,
            re.IGNORECASE)]
        for i, url in enumerate(urls):
            urls[i] = url.strip(".")
            if url.startswith('www.'): urls[i] = 'http://' + url
            self.references.add(url)
        return self.references

    def is_http_url(self, urlstr):
        return re.match(URL_REGEX, urlstr)



# main
def main(argv):
    import getopt
    def usage():
        print ('usage: %s [-d] [-p pagenos] [-m maxpages] [-P password] [-o output]'
            ' [-C] [-n] [-A] [-V] [-M char_margin] [-L line_margin] [-W word_margin]'
            ' [-F boxes_flow] [-Y layout_mode] [-O output_dir] [-R rotation]'
            ' [-t text|html|xml] [-c codec] [-s scale] [-u]'
            ' file' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'dp:m:P:o:CnAVM:L:W:F:Y:O:R:t:c:s:u')
    except getopt.GetoptError:
        return usage()
    if not (args and len(args) == 1): return usage()
    txttools = TXTtools(opts)
    outfp = sys.stdout
    print_urls = False

    for (k, v) in opts:
        if k == '-o': outfp = file(v, 'wb')
        elif k == '-u': print_urls = True

    txt = txttools.file2txt(args.pop(0))
    if print_urls:
        txt = "\n".join(url for url in txttools.extract_urls(txt)) + "\n"

    outfp.write(txt)
    outfp.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
