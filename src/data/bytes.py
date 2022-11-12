from typing import Type, Union

UNDEFINED = None
PY_INT = int
# del int
int = UNDEFINED  # type: ignore
PY_STR = str
# del str
str = UNDEFINED
PY_BYTES = bytes
# del bytes
bytes = UNDEFINED


class Buffer:
    def __init__(self, value) -> None:
        self.buffer = value

    def read(self, n):
        v = self.buffer[:n]
        self.buffer = self.buffer[n:]
        return v

    def peek(self, n):
        return self.buffer[:n]

    def write(self, v):
        self.buffer += v

    def get_empty(self):
        return len(self.buffer) == 0

    empty = property(get_empty, lambda x, y: None, lambda x: None)

    def get_length(self):
        return len(self.buffer)

    length = property(get_length, lambda x, y: None, lambda x: None)


class DataType:
    @classmethod
    def validateValue(cls, x):
        raise NotImplementedError()

    @classmethod
    def validateBytes(cls, x):
        raise NotImplementedError()

    @classmethod
    def toBytes(cls, x):
        raise NotImplementedError()

    @classmethod
    def fromBytes(cls, x):
        raise NotImplementedError()


class int(DataType):
    BITS: PY_INT = 0
    SIGNED: bool = False

    @classmethod
    def validateValue(cls, x):
        if cls.SIGNED:
            assert x < cls.max() or x > cls.min(), "Signed integer overflow"
        else:

            assert x >= cls.min(), "Got signed value, but this is unsigned datatype"
            assert x < cls.max(), "Integer overflow"
        return True

    @classmethod
    def validateBytes(cls, x):
        assert isinstance(x, (PY_BYTES, Buffer))

    @classmethod
    def toBytes(cls, x):
        cls.validateValue(x)
        return x.to_bytes(cls.BITS // 8, byteorder="big", signed=cls.SIGNED)

    @classmethod
    def fromBytes(cls, x):
        cls.validateBytes(x)
        if not isinstance(x, Buffer):
            x = Buffer(x)
        return PY_INT.from_bytes(
            x.read(cls.BITS // 8), byteorder="big", signed=cls.SIGNED
        )

    @classmethod
    def max(cls):
        if cls.SIGNED:
            return 2**cls.BITS / 2
        else:
            return 2**cls.BITS

    @classmethod
    def min(cls):
        if cls.SIGNED:
            return 2**cls.BITS / -2
        else:
            return 0


class uint8(int):
    BITS = 8


class uint16(int):
    BITS = 16


class uint32(int):
    BITS = 32


class Sequence(DataType):
    LENGTH_DT = uint32

    @classmethod
    def validateValue(cls, x):
        assert isinstance(x, PY_BYTES)

    @classmethod
    def validateBytes(cls, x):
        assert isinstance(x, (PY_BYTES, Buffer))

    @classmethod
    def toBytes(cls, x):
        cls.validateValue(x)
        return cls.LENGTH_DT.toBytes(len(x)) + x

    @classmethod
    def fromBytes(cls, x):
        cls.validateBytes(x)
        if not isinstance(x, Buffer):
            x = Buffer(x)
        length = cls.LENGTH_DT.fromBytes(x)
        return x.read(length)


class Struct:
    def __init__(self, dataTypes):
        self.validateDataTypes(dataTypes)
        self.dataTypes = dataTypes

    @staticmethod
    def validateDataTypes(dataTypes):
        assert isinstance(dataTypes, list), "dataTypes must be a list"
        for dt in dataTypes:
            assert isinstance(dt, type), "Datatype must be a class"
            assert issubclass(
                dt, DataType
            ), f"Invalid datatype provided, {dt.__name__} is not a subclass of DataType"

    def validateValue(self, x):
        assert len(x) == len(
            self.dataTypes
        ), "Length of values and length of datatypes is not same"

    def toBytes(self, x):
        self.validateValue(x)
        b = b""
        for dt, val in zip(self.dataTypes, x):
            b += dt.toBytes(val)
        return b

    def fromBytes(self, x):
        x = Buffer(x)
        r = []
        for dt in self.dataTypes:
            r.append(dt.fromBytes(x))
        return tuple(r)


if __name__ == "__main__":
    x = [uint32, uint16, uint8, Sequence]
    s = Struct(x)
    print(s.toBytes([16, 16, 16, b"123"]))
    print(s.fromBytes(s.toBytes([8, 8, 8, b"123"])))
