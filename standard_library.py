import errno
import os
import re
from datetime import date, datetime

from advpl_date import AdvPLDate


def build_utilities(runtime):
    from interpreter import (
        AdvPLBlock, AdvPLObject, AdvPLRuntimeError, VariableReference,
        is_number, truthy, to_display,
    )
    from parser import ParseError, parse_source
    from lexer import LexError

    def count(name, args, minimum, maximum=None):
        maximum = minimum if maximum is None else maximum
        if not minimum <= len(args) <= maximum:
            raise AdvPLRuntimeError(f"{name}: quantidade de argumentos invalida")

    def text(name, value):
        if not isinstance(value, str):
            raise AdvPLRuntimeError(f"{name} espera texto")
        return value

    def integer(name, value):
        if not is_number(value) or not float(value).is_integer():
            raise AdvPLRuntimeError(f"{name} espera numero inteiro")
        return int(value)

    def array(name, value):
        if not isinstance(value, list):
            raise AdvPLRuntimeError(f"{name} espera array")
        return value

    def day_value(name, value):
        if not isinstance(value, AdvPLDate):
            raise AdvPLRuntimeError(f"{name} espera data")
        return value

    def b_date(args):
        count("Date", args, 0)
        return AdvPLDate.from_date(date.today())

    def b_time(args):
        count("Time", args, 0)
        return datetime.now().strftime("%H:%M:%S")

    def b_ctod(args):
        count("CToD", args, 1)
        value = text("CToD", args[0]).strip()
        if not value:
            return AdvPLDate()
        try:
            return AdvPLDate.from_date(datetime.strptime(value, runtime.date_format).date())
        except ValueError:
            return AdvPLDate()

    def b_dtoc(args):
        count("DToC", args, 1)
        value = day_value("DToC", args[0])
        return value.value.strftime(runtime.date_format) if value.ordinal else ""

    def b_strtran(args):
        count("StrTran", args, 2, 5)
        source = text("StrTran", args[0])
        search = text("StrTran", args[1])
        replacement = text("StrTran", args[2]) if len(args) > 2 and args[2] is not None else ""
        start = integer("StrTran", args[3]) if len(args) > 3 and args[3] is not None else 1
        limit = integer("StrTran", args[4]) if len(args) > 4 and args[4] is not None else -1
        if not search or start < 1 or limit == 0:
            return source
        position = 0
        for _ in range(start - 1):
            found = source.find(search, position)
            if found < 0:
                return source
            position = found + len(search)
        return source[:position] + source[position:].replace(search, replacement, limit)

    def b_chr(args):
        count("Chr", args, 1)
        value = integer("Chr", args[0])
        if not 0 <= value <= 255:
            raise AdvPLRuntimeError("Chr espera codigo entre 0 e 255")
        try:
            return bytes([value]).decode("cp1252")
        except UnicodeDecodeError:
            return chr(value)

    def b_at(args):
        count("At", args, 2)
        return text("At", args[1]).find(text("At", args[0])) + 1

    def b_left(args):
        count("Left", args, 2)
        return text("Left", args[0])[:max(0, integer("Left", args[1]))]

    def b_type(args):
        count("Type", args, 1)
        expression = text("Type", args[0])
        previous = runtime._handling_error
        runtime._handling_error = True
        try:
            program = parse_source("Function __TypeExpr()\nReturn " + expression + "\n")
            if len(program.functions) != 1 or len(program.functions[0].body) != 1:
                return "U"
            return runtime.builtins["VALTYPE"]([runtime.eval(program.functions[0].body[0].expr)])
        except (AdvPLRuntimeError, ParseError, LexError):
            return "U"
        finally:
            runtime._handling_error = previous

    def b_aclone(args):
        count("AClone", args, 1)
        memo = {}
        def clone(value):
            if not isinstance(value, list):
                return value
            if id(value) not in memo:
                result = []
                memo[id(value)] = result
                result.extend(clone(item) for item in value)
            return memo[id(value)]
        return clone(array("AClone", args[0]))

    def b_ascan(args):
        count("AScan", args, 2, 4)
        values = array("AScan", args[0])
        start, end = array_range("AScan", values, args, 2)
        for index in range(start, end):
            matched = (truthy(runtime.invoke_block(args[1], [values[index]]))
                       if isinstance(args[1], AdvPLBlock) else values[index] == args[1])
            if matched:
                return index + 1
        return 0

    def b_errorblock(args):
        count("ErrorBlock", args, 0, 1)
        previous = runtime._error_block
        if args:
            if args[0] is not None and not isinstance(args[0], AdvPLBlock):
                raise AdvPLRuntimeError("ErrorBlock espera bloco ou NIL")
            runtime._error_block = args[0]
        return previous

    def b_break(args):
        count("Break", args, 0, 1)
        return runtime.builtins["THROW"](args)

    def b_encode_utf8(args):
        count("EncodeUTF8", args, 1, 2)
        if len(args) == 2:
            text("EncodeUTF8", args[1])
        return text("EncodeUTF8", args[0])

    def b_freeobj(args):
        count("FreeObj", args, 1)
        value = args[0].get() if isinstance(args[0], VariableReference) else args[0]
        if value is not None and not isinstance(value, AdvPLObject):
            raise AdvPLRuntimeError("FreeObj espera objeto ou NIL")
        if isinstance(args[0], VariableReference):
            args[0].set(None)
        return None

    def b_transform(args):
        count("Transform", args, 2)
        picture = text("Transform", args[1])
        value = args[0]
        if isinstance(value, AdvPLDate):
            return b_dtoc([value])
        if isinstance(value, str):
            return value.upper() if "@!" in picture else value
        if is_number(value):
            european = "@E" in picture.upper()
            mask = re.sub(r"^@\S+\s*", "", picture)
            decimals = len(mask.rsplit(".", 1)[1]) if "." in mask else 0
            result = format(value, ("," if "," in mask else "") + f".{decimals}f")
            if european:
                result = result.translate(str.maketrans({",": ".", ".": ","}))
            return result
        return to_display(value)

    def b_conout(args):
        if len(args) != 1:
            raise AdvPLRuntimeError("ConOut espera uma mensagem")
        print(to_display(args[0]))
        return None

    def b_alert(args):
        count("Alert", args, 1, 2)
        print("[ALERTA] " + text("Alert", args[0]))
        return None

    def file_error(exc):
        runtime._file_error = exc.errno or errno.EIO

    def b_fcreate(args):
        count("FCreate", args, 1, 2)
        path = text("FCreate", args[0])
        if len(args) > 1:
            integer("FCreate", args[1])
        try:
            handle = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_RDWR | getattr(os, "O_BINARY", 0), 0o666)
            runtime._open_files.add(handle)
            runtime._file_error = 0
            return handle
        except OSError as exc:
            file_error(exc)
            return -1

    def b_fwrite(args):
        count("FWrite", args, 2, 3)
        handle = integer("FWrite", args[0])
        try:
            payload = text("FWrite", args[1]).encode("cp1252")
        except UnicodeEncodeError as exc:
            raise AdvPLRuntimeError("FWrite exige texto representavel em CP1252") from exc
        if len(args) > 2:
            payload = payload[:max(0, integer("FWrite", args[2]))]
        try:
            if handle not in runtime._open_files:
                raise OSError(errno.EBADF, "Handle invalido")
            result = os.write(handle, payload)
            runtime._file_error = 0
            return result
        except OSError as exc:
            file_error(exc)
            return 0

    def b_fclose(args):
        count("FClose", args, 1)
        handle = integer("FClose", args[0])
        try:
            if handle not in runtime._open_files:
                raise OSError(errno.EBADF, "Handle invalido")
            os.close(handle)
            runtime._open_files.remove(handle)
            runtime._file_error = 0
            return True
        except OSError as exc:
            file_error(exc)
            return False

    def b_stod(args):
        count("SToD", args, 1)
        value = text("SToD", args[0])
        if not re.fullmatch(r"\d{8}", value):
            return AdvPLDate()
        try:
            return AdvPLDate.from_iso(f"{value[:4]}-{value[4:6]}-{value[6:]}")
        except ValueError:
            return AdvPLDate()

    def b_dtos(args):
        count("DToS", args, 1)
        value = day_value("DToS", args[0])
        return f"{value.value.year:04d}{value.value.month:02d}{value.value.day:02d}" if value.ordinal else " " * 8

    def date_part(name, part, args):
        count(name, args, 1)
        value = day_value(name, args[0])
        return getattr(value.value, part) if value.ordinal else 0

    def b_right(args):
        count("Right", args, 2)
        value = text("Right", args[0])
        size = max(0, integer("Right", args[1]))
        return value[-size:] if size else ""

    def b_replicate(args):
        count("Replicate", args, 2)
        return text("Replicate", args[0]) * max(0, integer("Replicate", args[1]))

    def b_rat(args):
        count("RAt", args, 2)
        return text("RAt", args[1]).rfind(text("RAt", args[0])) + 1

    def trim(name, side, args):
        count(name, args, 1)
        value = text(name, args[0])
        return value.lstrip(" ") if side == "left" else value.rstrip(" ")

    def b_asc(args):
        count("Asc", args, 1)
        value = text("Asc", args[0])
        if not value:
            return 0
        try:
            return value[0].encode("cp1252")[0]
        except UnicodeEncodeError as exc:
            if ord(value[0]) <= 255:
                return ord(value[0])
            raise AdvPLRuntimeError("Asc exige caractere representavel em CP1252") from exc

    def b_strzero(args):
        count("StrZero", args, 2, 3)
        if not is_number(args[0]):
            raise AdvPLRuntimeError("StrZero espera numero")
        size = integer("StrZero", args[1])
        decimals = integer("StrZero", args[2]) if len(args) > 2 else 0
        if size < 0 or decimals < 0:
            raise AdvPLRuntimeError("StrZero exige tamanho e decimais nao negativos")
        result = f"{args[0]:.{decimals}f}"
        return "*" * size if len(result) > size else result.zfill(size)

    def b_padc(args):
        count("PadC", args, 2, 3)
        value = runtime.builtins["CVALTOCHAR"]([args[0]])
        size = max(0, integer("PadC", args[1]))
        fill = text("PadC", args[2]) if len(args) > 2 else " "
        if not fill:
            raise AdvPLRuntimeError("PadC exige preenchimento nao vazio")
        value = value[:size]
        padding = size - len(value)
        left = padding // 2
        return (fill * left)[:left] + value + (fill * (padding - left))[:padding - left]

    def b_array(args):
        count("Array", args, 1, 16)
        dimensions = [integer("Array", value) for value in args]
        if any(value < 0 for value in dimensions):
            raise AdvPLRuntimeError("Array exige dimensoes nao negativas")
        def create(level):
            return [None if level == len(dimensions) - 1 else create(level + 1)
                    for _ in range(dimensions[level])]
        return create(0)

    def array_range(name, values, args, offset):
        start = integer(name, args[offset]) if len(args) > offset and args[offset] is not None else 1
        length = integer(name, args[offset + 1]) if len(args) > offset + 1 and args[offset + 1] is not None else len(values) - start + 1
        if start < 1 or length < 0:
            raise AdvPLRuntimeError(f"{name} exige inicio positivo e quantidade nao negativa")
        return start - 1, min(len(values), start - 1 + length)

    def b_afill(args):
        count("AFill", args, 2, 4)
        values = array("AFill", args[0])
        start, end = array_range("AFill", values, args, 2)
        for index in range(start, end):
            values[index] = args[1]
        return values

    def b_acopy(args):
        count("ACopy", args, 2, 5)
        source = array("ACopy", args[0])
        target = array("ACopy", args[1])
        start, end = array_range("ACopy", source, args, 2)
        position = integer("ACopy", args[4]) if len(args) > 4 and args[4] is not None else 1
        if position < 1:
            raise AdvPLRuntimeError("ACopy exige posicao positiva")
        for index, value in enumerate(source[start:end], position - 1):
            if index >= len(target):
                break
            target[index] = value
        return target

    def b_adel(args):
        count("ADel", args, 2)
        values = array("ADel", args[0])
        index = integer("ADel", args[1]) - 1
        if 0 <= index < len(values):
            del values[index]
            values.append(None)
        return values

    def b_ains(args):
        count("AIns", args, 2)
        values = array("AIns", args[0])
        index = integer("AIns", args[1]) - 1
        if 0 <= index < len(values):
            values.insert(index, None)
            values.pop()
        return values

    def b_atail(args):
        count("ATail", args, 1)
        values = array("ATail", args[0])
        return values[-1] if values else None

    def b_aeval(args):
        count("AEval", args, 2, 4)
        values = array("AEval", args[0])
        if not isinstance(args[1], AdvPLBlock):
            raise AdvPLRuntimeError("AEval espera bloco")
        start, end = array_range("AEval", values, args, 2)
        for index in range(start, end):
            runtime.invoke_block(args[1], [values[index], index + 1])
        return values

    def b_ferror(args):
        count("FError", args, 0)
        return runtime._file_error

    def b_seconds(args):
        count("Seconds", args, 0)
        hours, minutes, seconds = map(int, runtime.builtins["TIME"]([]).split(":"))
        return hours * 3600 + minutes * 60 + seconds

    return {
        "DATE": b_date, "TIME": b_time, "CTOD": b_ctod, "DTOC": b_dtoc,
        "STRTRAN": b_strtran, "CHR": b_chr, "AT": b_at, "LEFT": b_left,
        "TYPE": b_type, "ACLONE": b_aclone, "ASCAN": b_ascan,
        "ERRORBLOCK": b_errorblock, "BREAK": b_break,
        "ENCODEUTF8": b_encode_utf8, "FREEOBJ": b_freeobj, "TRANSFORM": b_transform,
        "CONOUT": b_conout, "ALERT": b_alert,
        "FCREATE": b_fcreate, "FWRITE": b_fwrite, "FCLOSE": b_fclose,
        "STOD": b_stod, "DTOS": b_dtos,
        "DAY": lambda args: date_part("Day", "day", args),
        "MONTH": lambda args: date_part("Month", "month", args),
        "YEAR": lambda args: date_part("Year", "year", args),
        "RIGHT": b_right, "REPLICATE": b_replicate, "RAT": b_rat,
        "LTRIM": lambda args: trim("LTrim", "left", args),
        "RTRIM": lambda args: trim("RTrim", "right", args),
        "TRIM": lambda args: trim("Trim", "right", args),
        "ASC": b_asc, "STRZERO": b_strzero, "PADC": b_padc,
        "ARRAY": b_array, "AFILL": b_afill, "ACOPY": b_acopy,
        "ADEL": b_adel, "AINS": b_ains, "ATAIL": b_atail, "AEVAL": b_aeval,
        "FERROR": b_ferror, "SECONDS": b_seconds,
    }
