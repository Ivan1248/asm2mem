import argparse
import datetime
import os
import re
import sys
import time
from typing import List, Tuple, Dict, Sequence, Iterator, Iterable

# Usage example: python automem.py test.asm > test.mem

# Argument parsing

ap = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("input", help="input PREMEM file path", type=str)
ap.add_argument(
    "-o", "--output", help="output MEM file path", default=None, type=str)
ap.add_argument(
    "-p", "--print", help="print output to the console", action="store_true")
watch_arg_help = "watch the input file for changes and translate it whenever it is changed"
ap.add_argument("-w", "--watch", help=watch_arg_help, action="store_true")
args = ap.parse_args()

# Common


def read_lines(file_path: str) -> Iterator[str]:
    with open(file_path, "r") as f:
        for l in f.readlines():
            yield l


def strip_comments_and_whitespace(line: str) -> str:
    return (line[:line.index('#')] if '#' in line else line).strip()


# Assembler to mem translation


class MemoryLocationProvider:

    def __init__(self):
        self.idx, self.populated = -1, set()

    def get_next(self) -> int:
        self.idx += 1
        if self.idx in self.populated:
            raise ValueError("Memory regions overlap.")
        self.populated.add(self.idx)
        return self.idx

    def set_start(self, idx: int):
        self.idx = idx - 1


def translate_lines(lines: Iterable[str]) -> Iterable[str]:
    lp = MemoryLocationProvider()

    def add_location(data: str) -> str:
        nonlocal lp
        return f"{lp.get_next():03d}: {data}"

    def fix_comment(l):  # to avoid a MythSim parsing bug
        return l.replace(':', '.')

    address_regex = re.compile(r"(\d+):")

    for i, l in enumerate(lines):
        l = l.strip()
        if len(l) == 0:  # empty line
            yield l
        elif l.startswith(':'):  # lines starting with ":" represent data
            l = l[1:].strip()
            if '#' in l:
                l = l.replace('#', '//', 1)
            yield add_location(l)
        elif l.startswith('#'):  # komentar
            yield f"// {fix_comment(l[1:])}"
        else:  # new starting location label
            m = address_regex.match(strip_comments_and_whitespace(l))
            if m:
                yield f"// {fix_comment(l)}"  # copy the line in a comment
                lp.set_start(int(m.group(1)))
            else:
                raise ValueError(f'Cannot parse line {i}: "{l}"".')
    yield ''


# Main

output = args.output or f"{os.path.splitext(args.input)[0]}.mem"


def remove_non_ASCII(s: str) -> str:
    return ''.join(filter(lambda x: ord(x) < 128, s))


def translate():
    with open(output, mode='w', encoding='ascii') as f:
        for l in translate_lines(read_lines(args.input)):
            l = remove_non_ASCII(l)
            f.write(l + '\n')
            if args.print:
                print(l)


if args.watch:  # Watch for changes and translate whenever the input changes.
    prev_time = 0
    while True:
        try:
            curr_time = os.stat(args.input).st_mtime
            if curr_time != prev_time:
                prev_time = curr_time
                translate()
                dt_now_string = datetime.datetime.now().strftime("%H:%M:%S")
                print(f'[{dt_now_string}] Output "{output}" updated.')
            time.sleep(0.2)
        except KeyboardInterrupt:
            break
        except:
            print(f'Unhandled error: {sys.exc_info()[0]}')
else:  # Translate once end exit
    translate()
