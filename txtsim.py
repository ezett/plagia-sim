#!/usr/bin/env python
# -*- coding: utf-8 -*-
#good default results so far: -F -0.5 -M 4.0 -L 2.63 -b 8
import sys, re, time
from multiprocessing import Process, Queue, Pool, cpu_count
from difflib import SequenceMatcher
from TXTtools import TXTtools


class color:
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    FG_RED = '\033[91m'
    FG_DARKRED = '\033[31m'
    FG_GREEN = '\033[92m'
    FG_DARKGREEN = '\033[32m'
    FG_YELLOW = '\033[93m'
    FG_DARKYELLOW = '\033[33m'
    FG_BLUE = '\033[94m'
    FG_DARKBLUE = '\033[34m'
    FG_MAGENTA = '\033[95m'
    FG_DARGMAGENTA = '\033[35m'
    FG_CYAN = '\033[96m'
    FG_DARKCYAN = '\033[36m'
    BG_RED = '\033[101m'
    BG_DARKRED = '\033[41m'
    BG_GREEN = '\033[102m'
    BG_DARKGREEN = '\033[42m'
    BG_YELLOW = '\033[103m'
    BG_DARKYELLOW = '\033[43m'
    BG_BLUE = '\033[104m'
    BG_DARKBLUE = '\033[44m'
    BG_MAGENTA = '\033[105m'
    BG_DARKMAGENTA = '\033[45m'
    BG_CYAN = '\033[106m'
    BG_DARKCYAN = '\033[46m'
    END = '\033[0m'


# percentage of string similarity
def stringsimilarity(s_str, s_cmp, s_ret, cb):
    m = SequenceMatcher(None, s_cmp, s_str, autojunk=False)
    mbs = m.get_matching_blocks()
    count = 0
    slen = len(s_str)
    for mb in reversed(mbs):
        if mb[2] >= cb:
            #seq = s1[mb[1]:mb[1]+mb[2]]
            #if len(re.findall(r'\w+', seq)) >= 0:
                s_ret = s_ret[:mb[1]+mb[2]] + color.END + s_ret[mb[1]+mb[2]:]
                for index in reversed([i.start() for i in re.finditer(r'[\n\f]',
                    s_ret[mb[1]:mb[1]+mb[2]])]):
                    s_ret = (s_ret[:mb[1] + index+1] + color.BG_DARKYELLOW +
                        s_ret[mb[1] + index+1:])
                    s_ret = (s_ret[:mb[1] + index] + color.END + s_ret[mb[1] +
                        index:])
                s_ret = s_ret[:mb[1]] + color.BG_DARKYELLOW + s_ret[mb[1]:]
                count += mb[2]
    ret = {'s_ret': s_ret, 'string_sim': m.ratio() * 100.0, 'cpy_txt':
            count*100.0/slen}
    return ret


def worker(fname, cmp_fname, s_str, s_cmp, s_ret, cb):
    """thread worker function"""
    print "[CHILD] " + cmp_fname + " started..."

    ret_str = 'Comparing "' + fname + '" with "' + cmp_fname + '"\n\n'
    ret_obj = stringsimilarity(s_str, s_cmp, s_ret, cb)
    ret_str += ('Percentage of string similarity: ' + str(ret_obj['string_sim'])
        + '\n')
    ret_str += 'Percentage of copied text: ' + str(ret_obj['cpy_txt'])  + '\n\n'
    ret_str += ret_obj['s_ret'].replace('\f', '\n\n')
    ret_str += '\n\n\n\n'
    print "[CHILD] " + cmp_fname + " finished..."
    return ret_str


class TXTsimilarity:

    def __init__(self, opts):
        self.check_urls = False
        self.cb = 8
        self.txttools = TXTtools(opts)
        self.processes = []
        self.queue = Queue()
        self.pool = Pool()

        for (k, v) in opts:
            if k == '-b': self.cb = int(v)
            elif k == '-u': self.check_urls = True

    def txtcompare(self, fname, flist):
        stud_str = self.txttools.file2txt(fname)
        stud_str1 = re.sub(r'\n+', ' ', stud_str)
        stud_str2 = re.sub(r'\n\n+', r'\f', stud_str)

        urlset = self.txttools.extract_urls(stud_str)
        for u in urlset:
            print u

        print '\n'
        if not self.check_urls:
            urlset.clear()


        results = [self.pool.apply_async(worker, args=(fname, cmp_fname,
            stud_str1, re.sub(r'\s+', ' ', self.txttools.file2txt(cmp_fname)),
            stud_str2, self.cb,)) for cmp_fname in flist + list(urlset)]
        return [p.get() for p in results]



# main
def main(argv):
    import getopt

    runtime = time.time()

    def usage():
        print ('usage: %s [-d] [-p pagenos] [-m maxpages] [-P password] [-o output]'
            ' [-C] [-n] [-A] [-V] [-M char_margin] [-L line_margin] [-W word_margin]'
            ' [-F boxes_flow] [-Y layout_mode] [-O output_dir] [-R rotation]'
            ' [-t text|html|xml] [-c codec] [-s scale] [-b copy_block_length]'
            ' [-u] file ...' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'dp:m:P:o:CnAVM:L:W:F:Y:O:R:t:c:s:b:u')
    except getopt.GetoptError:
        return usage()
    if not args: return usage()

    txtsimilarity = TXTsimilarity(opts)
    outfp = sys.stdout

    for (k, v) in opts:
        if k == '-o':
            outfp = file(v, 'wb')

    output = txtsimilarity.txtcompare(args.pop(0), args)
    for o in output:
        outfp.write(o)

    print 'Running time: ' + str(time.time() - runtime) + 's'
    outfp.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
