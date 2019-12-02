import argparse
import datetime
import os
import re
import sys
import time
from typing import List, Tuple, Dict, Sequence, Iterator, Iterable

# Usage example: python asm2mem.py test.asm > test.mem

# Argument parsing

ap = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
ap.add_argument("input", help="input ASM file path", type=str)
ap.add_argument(
    "-c", "--config", help="config file path", default="asm2mem.cfg", type=str)
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


# Config parsing

variables = {'ri', 'rj', 'rk', 'const4', 'const8'}


def get_instruction_regex(tokens: Iterable[str]):
    escape = lambda x: re.escape(x).replace(r'\{', '{').replace(r'\}', '}')
    format_expr = r'\s+'.join(map(escape, tokens))
    split_expr = re.split(r'{([^}]+)}', format_expr)  # split on '{' and '}'
    var_names = split_expr[1::2]  # extract captured variable names
    for v in var_names:     
        if v not in variables:
            raise RuntimeError(f"{v} is undefined. It should be one of {variables}")
    assert all(v in variables for v in var_names)
    signs = ['' if x.startswith('r') else '-?' for x in var_names]
    split_expr[1::2] = [f'(?P<{x}>{s}\\d+)' for x, s in zip(var_names, signs)]
    return re.compile(''.join(split_expr) + r'\s*#?[^$]*', re.IGNORECASE)


class InstructionMatcher:
    def __init__(self, opcode: int, tokens: Sequence[str]):
        self.opcode, self.name = opcode, tokens[0].upper()
        self.template = ' '.join(tokens)
        self._regex = get_instruction_regex(tokens)

    def match(self, asm_expression: str) -> Dict[str, int]:
        match = self._regex.match(asm_expression)
        if match is None:
            return None
        d = {k: int(v) for k, v in match.groupdict().items()}
        return {'opcode': self.opcode, **d}


def parse_config(config_file: str) -> List[InstructionMatcher]:

    def to_instruction_matcher(instr_pattern: str) -> Dict[str, str]:
        opcode, *tokens = instr_pattern.split()
        assert opcode[-1] == ':', "Invalid syntax."
        return InstructionMatcher(opcode=int(opcode[:-1]), tokens=tokens)

    lines = (strip_comments_and_whitespace(x) for x in read_lines(config_file))
    return [to_instruction_matcher(x) for x in lines if len(x) > 0]


# Assembler to mem translation


def get_instruction_code(opcode: int,
                         ri: int = None,
                         rj: int = None,
                         rk: int = None,
                         const4: int = None,
                         const8: int = None) -> Tuple[str, str]:
    """
    Given values for instruction parts, returns a pair of strings representing 
    two bytes of an instruction's code.
    """
    if const8 is not None and any(x is not None for x in (rj, rk, const4)):
        raise ValueError(
            "An instruction cannot have both const8 and any of rj, rk, const4.")
    get = lambda x: 0 if x is None else x
    first_byte = f"{opcode:06b} {get(ri):02b}"
    if const8 is None:
        return first_byte, f"{get(rj):02b} {get(rk):02b} {get(const4):04b}"
    else:
        return first_byte, f"{get(const8)}"


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


class Translator:
    def __init__(self, instruction_matchers: List[InstructionMatcher]):
        self._matchers = instruction_matchers

    def translate_instruction(self, line: str) -> Tuple[str, str]:
        line = strip_comments_and_whitespace(line)
        if len(line) == 0:
            return None
        for im in self._matchers:
            match = im.match(line)
            if match is not None:
                return get_instruction_code(**match)
        else:  # If nothing matches, write a helpful error message.
            msg = f'"{line}" does not match any instruction.'
            raise ValueError(
                next((f'{msg} Did you want to use "{im.template}"?'
                      for im in self._matchers
                      if line.upper().startswith(im.name)), msg))

    def translate(self, lines: Iterable[str]) -> Iterable[str]:
        lp = MemoryLocationProvider()

        def add_location(data: str) -> str:
            nonlocal lp
            return f"{lp.get_next():03d}: {data}"

        def fix_comment(l):  # to avoid a MythSim parsing bug
            return l.replace(':', '.')

        address_regex = re.compile(r"(\d+):")

        for l in lines:
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
            else:
                m = address_regex.match(strip_comments_and_whitespace(l))
                if m:  # new starting location label
                    yield f"// {fix_comment(l)}"  # copy the line in a comment
                    lp.set_start(int(m.group(1)))
                else:  # assembler command
                    yield f"// {l}"  # copy the line in a comment
                    instr_code = self.translate_instruction(l)
                    if instr_code is not None:
                        for c in instr_code:  # write a 2-byte-instruction
                            yield add_location(c)
        yield ''


# Main

output = args.output or f"{os.path.splitext(args.input)[0]}.mem"


def remove_non_ASCII(s: str) -> str:
    return ''.join(filter(lambda x: ord(x) < 128, s))


def translate():
    translator = Translator(instruction_matchers=parse_config(args.config))
    with open(output, mode='w', encoding='ascii') as f:
        for l in translator.translate(read_lines(args.input)):
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
