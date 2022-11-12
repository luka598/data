from bz2 import compress
from collections import defaultdict
import bytes as by
from typing import Sized

NULLB = b"\x00"


def remove(s, begin, length):
    return s[0:begin] + s[begin + length :]


def insert(s1, s2, begin):
    return s1[0:begin] + s2 + s1[begin:]


def find(s1, s2, start):
    return s1.find(s2, start)


compressStruct = by.Struct([by.Sequence, by.Sequence])


class Compress:
    KEY_SIZE = 1
    VALUE_SIZE = 3
    BUFFER_SIZE = 1000

    def __init__(self) -> None:
        self.buffer = b""
        self.generateTable()

    def createTable(self, b):
        occurrences = defaultdict(lambda: 0)
        for i in range(0, len(b) - self.VALUE_SIZE + 1):
            occurrences[b[i : i + self.VALUE_SIZE]] += 1
        occurrences = list(occurrences.items())
        occurrences.sort(key=lambda x: x[1], reverse=True)
        occurrences = occurrences[:255]
        t = {NULLB: NULLB}
        for i in range(1, len(occurrences)):
            t[i.to_bytes(1, byteorder="big", signed=False)] = occurrences[i - 1][0]
        return t

    def generateTable(self):
        self.table = self.createTable(self.buffer)
        self.tableInverted = {v: k for k, v in self.table.items()}
        return self.table, self.tableInverted

    def addToBuffer(self, b):
        self.buffer += b
        self.buffer = self.buffer[: self.BUFFER_SIZE]

    def compress(self, b):
        self.addToBuffer(b)
        compressed = []
        i = 0
        while i + self.VALUE_SIZE < len(b):
            bytes = b[i : i + self.VALUE_SIZE]
            byte = b[i : i + 1]
            # print(b, bytes, byte, len(b), i)
            if bytes in self.tableInverted:
                b = remove(b, i, self.VALUE_SIZE)
                b = insert(b, NULLB, i)
                compressed.append(self.tableInverted[bytes])
            elif byte == NULLB:
                compressed.append(self.tableInverted[byte])
            i += self.KEY_SIZE
        # return b, b"".join(compressed)
        return compressStruct.toBytes([b, b"".join(compressed)])

    def decompress(self, bStruct):
        b, compressed = compressStruct.fromBytes(bStruct)
        # print("DEC", b, compressed)
        compressed = [
            compressed[i : i + self.KEY_SIZE]
            for i in range(0, len(compressed), self.KEY_SIZE)
        ]
        i = 0
        while len(compressed) > 0:
            val = self.table[compressed.pop(0)]
            i = find(b, NULLB, i)
            b = remove(b, i, 1)
            b = insert(b, val, i)
            i += len(val)
            # print(i)
        self.addToBuffer(b)
        return b


def benchmark_table(b_decomp: Sized, b_comp) -> float:
    decomp_size = len(b_decomp)
    comp_size = len(b_comp[0])
    table_size = len(b_comp[1])
    total_comp_size = comp_size + table_size
    ratio = 1 - total_comp_size / decomp_size
    print("Compression results:")
    print(
        f"\t{decomp_size}b -> {total_comp_size}b (Comp: {comp_size}b - Table: {table_size})"
    )
    print(f"\tRatio: {round(ratio*100, 2)} compressed")
    return ratio


def benchmark_packet(b_decomp: Sized, b_comp: Sized) -> float:
    decomp_size = len(b_decomp)
    comp_size = len(b_comp)
    ratio = 1 - comp_size / decomp_size
    print("Compression results:")
    print(f"\t{decomp_size}b -> {comp_size}b")
    print(f"\tRatio: {round(ratio*100, 2)} compressed")
    return ratio


if __name__ == "__main__":
    # b = b"A\x00BCDEFG"
    b = b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer volutpat nunc at dictum vestibulum. Sed nunc nisi, ultrices nec metus quis, semper auctor lectus. Nam bibendum justo non gravida maximus. Nunc ullamcorper leo imperdiet sagittis gravida. Quisque ultrices dolor pulvinar odio gravida feugiat. Maecenas elementum ultricies lectus vitae venenatis. Morbi sed tortor lectus. Fusce ullamcorper, mi quis gravida pulvinar, lorem tortor cursus augue, vestibulum gravida urna mi sit amet est. Pellentesque rhoncus lacus augue, non posuere nunc pretium dignissim. In dapibus at lectus et convallis. Donec sed metus nulla. Pellentesque posuere sollicitudin risus sed volutpat."

    c = Compress()
    c.compress(b)
    c.generateTable()
    comp = c.compress(b)
    assert c.decompress(comp) == b, "Not equal"
    print(b, comp)
    benchmark_packet(b, comp)
