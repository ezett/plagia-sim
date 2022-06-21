#!/usr/bin/env python
# -*- coding: utf-8 -*-
#best default results so far: -F -0.5 -M 4.0 -L 2.63
import sys, re
import subprocess
from tempfile import NamedTemporaryFile
from TXTtools import TXTtools


# main
def main(argv):
    import getopt
    def usage():
        print ('usage: %s [-d] [-p pagenos] [-m maxpages] [-P password] [-o output]'
            ' [-C] [-n] [-A] [-V] [-M char_margin] [-L line_margin] [-W word_margin]'
            ' [-F boxes_flow] [-Y layout_mode] [-O output_dir] [-R rotation]'
            ' [-t text|html] [-c codec] [-s scale]'
            ' file1 file2 ...' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'dp:m:P:o:CnAVM:L:W:F:Y:O:R:t:c:s:')
    except getopt.GetoptError:
        return usage()
    if not (args and len(args) >= 2): return usage()

    txttools = TXTtools(opts)
    outfp = sys.stdout

    for (k, v) in opts:
        if k == '-o':
            outfp = file(v, 'wb')

    stud_str = txttools.file2txt(args.pop(0))
    tmpfp_stud_str = NamedTemporaryFile(mode='w+b', delete=False)
    tmpfp_stud_str.write(stud_str)
    tmpfp_stud_str.close()

    for fname in args:
        txt = txttools.file2txt(fname)
        tmpfp = NamedTemporaryFile(mode='w+b', delete=False)
        tmpfp.write(txt)
        tmpfp.close()

        subprocess.call(['git', 'diff', '--text', '--color-words', tmpfp_stud_str.name,
            tmpfp.name], stdout=outfp, stderr=sys.stderr)

    outfp.close()
    return

if __name__ == '__main__': sys.exit(main(sys.argv))
