import os
import gzip
import random
import string
import shutil
import base64
import zlib
import marshal
import subprocess
import io
import nest_asyncio
import asyncio
import codecs
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, CallbackContext, filters
from telegram.error import BadRequest

TOKEN = '8084091800:AAFZ8hZ_jGAyUsArcpQFWusBDnthWF0k1sE'

users_waiting_for_file = {}

ENC_TYPES = {
    'sayopy': '𝗦𝗮𝘆𝗼𝗽𝘆',
    'marshal': '𝗠𝗮𝗿𝘀𝗵𝗮𝗹',
    'zlib': '𝗭𝗹𝗶𝗯',
    'cython': '𝗖𝘆𝘁𝗵𝗼𝗻',
    'base64': '𝗕𝗮𝘀𝗲𝟲𝟰',
    'gzip': '𝗚𝘇𝗶𝗽',
    'base85': '𝗕𝗮𝘀𝗲𝟴𝟱',
    'obf': '𝗢𝗯𝗳',
    'marshal_zlib': '𝗠𝗮𝗿 + 𝗭𝗹𝗶𝗯',
    'hex': '𝗛𝗲𝘅',
    'base32': '𝗕𝗮𝘀𝗲𝟯𝟮',
    'lambda_marshal_zlib': '𝗹𝗮𝗺 + 𝗺𝗮 + 𝘇𝗹 + 𝗯𝟲𝟰'
}

def create_lowercase_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def create_alphanumeric_string(length):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def remove_comments(input_file, output_file):
    with open(input_file, 'r') as input_f:
        content = input_f.read()

    cleaned_content = ''
    in_comment = False
    index = 0

    while index < len(content):
        if content[index:index+2] == '/*':
            in_comment = True
            index += 2
            continue
        elif content[index:index+2] == '*/':
            in_comment = False
            index += 2
            continue

        if not in_comment:
            cleaned_content += content[index]

        index += 1

    with open(output_file, 'w') as output_f:
        output_f.write(cleaned_content)

if not os.path.exists("m/"):
    os.mkdir("m")

def marshal_zlib_encode(code):
    compiled = compile(code, "<string>", 'exec')
    marshaled = marshal.dumps(compiled)
    compressed = zlib.compress(marshaled)
    encoded = "import zlib\nimport base64\nimport marshal\nexec(marshal.loads(zlib.decompress(" + repr(compressed) + ")))"
    return encoded

def hex_encode(code):
    hex_representation = code.encode().hex()
    return "exec(bytes.fromhex('" + hex_representation + "'))"

def base32_encode(code):
    base32_representation = base64.b32encode(code.encode()).decode()
    return "import base64\nexec(base64.b32decode('" + base32_representation + "'))"

def lambda_marshal_zlib_encode(code):
    compressed = zlib.compress(marshal.dumps(compile(code, '<string>', 'exec')))
    encoded = base64.b64encode(compressed).decode()[::-1]
    return "_ = lambda __ : __import__('marshal').loads(__import__('zlib').decompress(__import__('base64').b64decode(__[::-1])));\nexec((_)(b'" + encoded + "'))"

async def create_encrypted_file(input_file, enc_type):
    input_file = str(input_file)
    output_script = None

    if enc_type == 'sayopy':
        filename = input_file.split("/")[-1]
        temp_filename = create_lowercase_string(10) + ".py"
        shutil.copyfile(input_file, f"m/{temp_filename}")
        encrypted_file = g(temp_filename)
        shutil.copyfile(encrypted_file, input_file.replace(".py", "_cythonized.py"))

        with open(input_file.replace(".py", "_cythonized.py"), 'rb') as file:
            file_content = file.read()

        compressed_content = zlib.compress(file_content, level=9)
        encoded_content = base64.b64encode(compressed_content).decode('utf-8')
        output_script = os.path.splitext(input_file)[0] + '_encrypted.py'

        script_template = f"""import os, sys, base64 as B, zlib, gzip, io
X = '.Sayopy'
Q = '{encoded_content}'

try:
    with open(X, 'wb') as D:
        with gzip.GzipFile(fileobj=D, mode='wb') as gzip_file:
            gzip_file.write(zlib.decompress(B.b64decode(Q)))

    with open(X, 'rb') as D:
        with gzip.GzipFile(fileobj=D, mode='rb') as gzip_file:
            R = gzip_file.read().decode('utf-8')

    exec(R, globals())
finally:
    if os.path.exists(X):
        os.remove(X)
"""

        with io.BytesIO() as bytes_io:
            with gzip.GzipFile(fileobj=bytes_io, mode='wb') as gzip_file:
                gzip_file.write(script_template.encode('utf-8'))
            compressed_script = bytes_io.getvalue()

        final_script = f"""
A = '.Sayopy'
import os, sys, base64 as B, gzip, io
C = '{base64.b64encode(compressed_script).decode()}'
try:
    with open(A, 'wb') as D:
        D.write(B.b64decode(C))
    with open(A, 'rb') as D:
        with gzip.GzipFile(fileobj=D, mode='rb') as gzip_file:
            R = gzip_file.read().decode('utf-8')
    exec(R, globals())
except Exception as E:
    print(E)
finally:
    if os.path.exists(A):
        os.remove(A)
"""

        with open(output_script, 'w') as output_file:
            output_file.write(final_script)

    elif enc_type == 'marshal':
        with open(input_file, 'r') as f:
            code = f.read()
        data = marshal.dumps(compile(code, '', 'exec'))
        output_script = os.path.splitext(input_file)[0] + '-𝗘𝗡𝗖.py'
        with open(output_script, 'w') as fileout:
            fileout.write(f'import marshal\nexec(marshal.loads({repr(data)}))')

    elif enc_type == 'zlib':
        with open(input_file, 'r') as f:
            code = f.read()
        compressed_code = zlib.compress(code.encode('utf-8'))
        output_script = os.path.splitext(input_file)[0] + '-𝗘𝗡𝗖.py'
        with open(output_script, 'w') as fileout:
            fileout.write(f'exec(__import__("zlib").decompress({compressed_code}))')

    elif enc_type == 'cython':
        filename = input_file.split("/")[-1]
        temp_filename = create_lowercase_string(10) + ".py"
        shutil.copyfile(input_file, f"m/{temp_filename}")
        encrypted_file = g(temp_filename)
        shutil.copyfile(encrypted_file, input_file.replace(".py", "_enc-saython.py"))
        output_script = input_file.replace(".py", "_enc-saython.py")

    elif enc_type == 'base64':
        with open(input_file, 'rb') as file:
            file_data = file.read()
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        output_script = os.path.splitext(input_file)[0] + '_enc.py'
        with open(output_script, 'w') as output_file:
            output_file.write(f"import base64\nexec(base64.b64decode('{encoded_data}'))")

    elif enc_type == 'gzip':
        with open(input_file, 'rb') as file:
            file_data = file.read()
        compressed_data = gzip.compress(file_data)
        output_script = os.path.splitext(input_file)[0] + '_enc.py'
        with open(output_script, 'w') as output_file:
            output_file.write(f"import gzip\nexec(gzip.decompress({compressed_data}))")

    elif enc_type == 'base85':
        with open(input_file, 'rb') as file:
            file_data = file.read()
        encoded_data = base64.b85encode(file_data).decode('utf-8')
        output_script = os.path.splitext(input_file)[0] + '_enc.py'
        with open(output_script, 'w') as output_file:
            output_file.write(f"import base64\nexec(base64.b85decode('{encoded_data}'))")

    elif enc_type == 'obf':
        output_script = os.path.splitext(input_file)[0] + '_enc.py'
        obfuscate_file(input_file, output_script)

    elif enc_type == 'marshal_zlib':
        with open(input_file, 'r', encoding='utf-8') as file:
            code = file.read()
        encrypted_code = marshal_zlib_encode(code)
        output_script = os.path.splitext(input_file)[0] + '_enc.py'
        with open(output_script, 'w', encoding='utf-8') as encrypted_file:
            encrypted_file.write(encrypted_code)

    elif enc_type == 'hex':
        with open(input_file, 'r', encoding='utf-8') as file:
            code = file.read()
        encrypted_code = hex_encode(code)
        output_script = os.path.splitext(input_file)[0] + '_enc.py'
        with open(output_script, 'w', encoding='utf-8') as encrypted_file:
            encrypted_file.write(encrypted_code)

    elif enc_type == 'base32':
        with open(input_file, 'r', encoding='utf-8') as file:
            code = file.read()
        encrypted_code = base32_encode(code)
        output_script = os.path.splitext(input_file)[0] + '_enc.py'
        with open(output_script, 'w', encoding='utf-8') as encrypted_file:
            encrypted_file.write(encrypted_code)

    elif enc_type == 'lambda_marshal_zlib':
        with open(input_file, 'r', encoding='utf-8') as file:
            code = file.read()
        encrypted_code = lambda_marshal_zlib_encode(code)
        output_script = os.path.splitext(input_file)[0] + '_enc.py'
        with open(output_script, 'w', encoding='utf-8') as encrypted_file:
            encrypted_file.write(encrypted_code)

    return output_script

def obfuscate_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        code = file.read()

    obfuscator = Obfuscator(code)
    with open(output_file, 'w', encoding='utf-8') as output_file:
        output_file.write(obfuscator.code)

class Obfuscator:
    def __init__(self, code):
        self.code = code
        self.__obfuscate()

    def __com__fer(self, text, key=None):
        newstring = ""
        if key is None:
            key = "".join(random.choices(string.digits + string.ascii_letters, k=random.randint(4, 8)))
        if not key[0] == " ":
            key = " " + key
        for i in range(len(text)):
            newstring += chr(ord(text[i]) ^ ord(key[(len(key) - 2) + 1]))
        return (newstring, key)

    def __encodestring(self, string):
        newstring = ""
        for i in string:
            if random.choice([True, False]):
                newstring += "\\x" + codecs.encode(i.encode(), "hex").decode()
            else:
                newstring += "\\" + oct(ord(i))[2:]
        return newstring

    def __obfuscate(self):
        compile_f = self.__com__fer(self.code)
        self.code = compile_f[0]
        encoded_code = base64.b64encode(codecs.encode(codecs.encode(self.code.encode(), "bz2"), "uu")).decode()
        encoded_code = [encoded_code[i: i + int(len(encoded_code) / 4)] for i in range(0, len(encoded_code), int(len(encoded_code) / 4))]
        new_encoded_code = []
        new_encoded_code.append(codecs.encode(encoded_code[0].encode(), "uu").decode() + "u")
        new_encoded_code.append(codecs.encode(encoded_code[1], "rot13") + "r")
        new_encoded_code.append(codecs.encode(encoded_code[2].encode(), "hex").decode() + "h")
        new_encoded_code.append(base64.b85encode(codecs.encode(encoded_code[3].encode(), "hex")).decode() + "x")
        self.code = f"""
_____=eval("{self.__encodestring('eval')}")
_______=_____("{self.__encodestring('compile')}")
______,____=_____(_______("{self.__encodestring("__import__('base64')")}","",_____.__name__)),_____(_______("{self.__encodestring("__import__('codecs')")}","",_____.__name__));____________________=_____("'{self.__encodestring(compile_f[True])}'");________,_________,__________,___________=_____(_______("{self.__encodestring('exec')}","",_____.__name__)),_____(_______("{self.__encodestring('str.encode')}","",_____.__name__)),_____(_______("{self.__encodestring('isinstance')}","",_____.__name__)),_____(_______("{self.__encodestring('bytes')}","",_____.__name__))
def decode_string(__________, ___________):
    __________=__________.decode()
    _________=""
    if not ___________[False]=="{self.__encodestring(' ')}":
        ___________="{self.__encodestring(' ')}"+___________
    for _ in range(_____("{self.__encodestring('len(__________)')}")):
        _________+=_____("{self.__encodestring('chr(ord(__________[_])^ord(___________[(len(___________) - True*2) + True]))')}")
    return (_________,___________)
def encode_string(_____________):
    if(_____________[-True]!=_____(_______("'{self.__encodestring('c________________6s5________________6ardv8')}'[-True*4]","",_____.__name__))):_____________ = _________(_____________)
    if not(__________(_____________, ___________)):_____________ = _____(_______("{self.__encodestring('____.decode(_____________[:-True]')},'{self.__encodestring('rot13')}')","",_____.__name__))
    else:
        if(_____________[-True]==_____(_______("b'{self.__encodestring('f5sfsdfauf85')}'[-True*4]","", _____.__name__))):
            _____________=_____(_______("{self.__encodestring('____.decode(_____________[:-True]')},'{self.__encodestring('uu')}')","",_____.__name__))
        elif (_____________[-True] ==_____(_______("b'{self.__encodestring('d5sfs1dffhsd8')}'[-True*4]","",_____.__name__))):_____________=_____(_______("{self.__encodestring('____.decode(_____________[:-True]')},'{self.__encodestring('hex')}')","",_____.__name__))
        else:_____________=_____(_______("{self.__encodestring('______.b85decode(_____________[:-True])')}","",_____.__name__));_____________=_____(_______("{self.__encodestring('____.decode(_____________')}, '{self.__encodestring('hex')}')","",_____.__name__))
        _____________=_____(_______("{self.__encodestring('___________.decode(_____________)')}","",_____.__name__))
    return _____________
_________________=_____(_______("{self.__encodestring('___________.decode')}({self.__encodestring(new_encoded_code[True*3]).encode()})","",_____.__name__));________________ = _____(_______("{self.__encodestring('___________.decode')}({self.__encodestring(new_encoded_code[1]).encode()})","",_____.__name__));__________________=_____(_______("{self.__encodestring('___________.decode')}({self.__encodestring(new_encoded_code[True*2]).encode()})","",_____.__name__));______________=_____(_______("{self.__encodestring('___________.decode')}({self.__encodestring(new_encoded_code[False]).encode()})","",_____.__name__));_______________=_____(_______("{self.__encodestring('str.join')}('', {self.__encodestring('[encode_string(x) for x in [______________,________________,__________________,_________________]]')})","", _____.__name__));________(decode_string(____.decode(____.decode(______.b64decode(_________(_______________)), "{self.__encodestring("uu")}"),"{self.__encodestring("bz2")}"),____________________)[_____("{self.__encodestring('False')}")])\n"""

def g(name):
    w = open(f"m/{name}", "r", encoding="utf-8")
    a = w.read()
    w.close()
    
    if a.count("\n") < 30:
        a = a + "#" + gw(1000)
        
    encoded_bytes = base64.b64encode(a.encode('utf-8'))
    a = encoded_bytes.decode('utf-8')
    
    lis2 = []
    lis = a.split("a")
    result = []
    
    for i in range(len(lis)):
        result.append(lis[i])
        if i < len(lis) - 1:
            result[-1] += "a"
            
    lis = result[::-1]
    a = ""
    t = 1
    nm = 0
    
    for x in lis:
        while True:
            if nm > 20:
                t += 1
            n = create_lowercase_string(t)
            n = "_" + n
            if n not in lis2:
                nm = 0
                break
            nm += 1
        lis2.append(n)
        a += f"{n}='{x}'\n"
        
    a = a.split("\n")    
    a.append(create_lowercase_string(1) + "='" + create_alphanumeric_string(10) + "a'")
    a.append(create_lowercase_string(1) + "='" + create_alphanumeric_string(20) + "a'")
    a.append(create_lowercase_string(1) + "='" + create_alphanumeric_string(30) + "a'")
    a.append(create_lowercase_string(1) + "='" + create_alphanumeric_string(40) + "a'")
    a.append(create_lowercase_string(1) + "='" + create_alphanumeric_string(50) + "a'")
    a.append(create_lowercase_string(1) + "='" + create_alphanumeric_string(80) + "a'")
    
    random.shuffle(a)
    a = "\n".join(a)
    aa = f'''import base64,os
os.system("rm requests.py")
os.system("rm -r requests")
os.system("clear")
{a}
lis2 = {lis2}
lis2 = lis2[::-1]
a = "+".join(lis2)
a = f"a={{a}}"
exec(a)
exec(base64.b64decode(a.encode('utf-8')).decode('utf-8'))
'''
    os.remove(f"m/{name}")
    os.system("cd")
    with open(f"m/{name}", 'w') as output_f:
        output_f.write(aa)
    os.system(f"cythonize m/{name}")
    name2 = name.replace(".py", ".c")
    remove_comments(f"m/{name2}", f"m/{name2}")
    name2 = name.replace(".py", "")
    c = '''
#ifdef __FreeBSD__
#include <floatingpoint.h>
#endif
#if PY_MAJOR_VERSION < 3
int main(int argc, char** argv) {
#elif defined(WIN32) || defined(MS_WINDOWS)
int wmain(int argc, wchar_t **argv) {
#else
static int __Pyx_main(int argc, wchar_t **argv) {
#endif
    /* 754 requires that FP exceptions run in "no stop" mode by default,
     * and until C vendors implement C99's ways to control FP exceptions,
     * Python requires non-stop mode.  Alas, some platforms enable FP
     * exceptions by default.  Here we disable them.
     */
#ifdef __FreeBSD__
    fp_except_t m;
    m = fpgetmask();
    fpsetmask(m & ~FP_X_OFL);
#endif
    if (argc && argv)
        Py_SetProgramName(argv[0]);
    Py_Initialize();
    if (argc && argv)
        PySys_SetArgv(argc, argv);
    {
      PyObject* m = NULL;
      __pyx_module_is_main_''' + name2 + ''' = 1;
      #if PY_MAJOR_VERSION < 3
          init''' + name2 + '''();
      #elif CYTHON_PEP489_MULTI_PHASE_INIT
          m = PyInit_''' + name2 + '''();
          if (!PyModule_Check(m)) {
              PyModuleDef *mdef = (PyModuleDef *) m;
              PyObject *modname = PyUnicode_FromString("__main__");
              m = NULL;
              if (modname) {
                  m = PyModule_NewObject(modname);
                  Py_DECREF(modname);
                  if (m) PyModule_ExecDef(m, mdef);
              }
          }
      #else
          m = PyInit_''' + name2 + '''();
      #endif
      if (PyErr_Occurred()) {
          PyErr_Print();
          #if PY_MAJOR_VERSION < 3
          if (Py_FlushLine()) PyErr_Clear();
          #endif
          return 1;
      }
      Py_XDECREF(m);
    }
#if PY_VERSION_HEX < 0x03060000
    Py_Finalize();
#else
    if (Py_FinalizeEx() < 0)
        return 2;
#endif
    return 0;
}
#if PY_MAJOR_VERSION >= 3 && !defined(WIN32) && !defined(MS_WINDOWS)
#include <locale.h>
static wchar_t*
__Pyx_char2wchar(char* arg)
{
    wchar_t *res;
#ifdef HAVE_BROKEN_MBSTOWCS
    /* Some platforms have a broken implementation of
     * mbstowcs which does not count the characters that
     * would result from conversion.  Use an upper bound.
     */
    size_t argsize = strlen(arg);
#else
    size_t argsize = mbstowcs(NULL, arg, 0);
#endif
    size_t count;
    unsigned char *in;
    wchar_t *out;
#ifdef HAVE_MBRTOWC
    mbstate_t mbs;
#endif
    if (argsize != (size_t)-1) {
        res = (wchar_t *)malloc((argsize+1)*sizeof(wchar_t));
        if (!res)
            goto oom;
        count = mbstowcs(res, arg, argsize+1);
        if (count != (size_t)-1) {
            wchar_t *tmp;
            /* Only use the result if it contains no
               surrogate characters. */
            for (tmp = res; *tmp != 0 &&
                     (*tmp < 0xd800 || *tmp > 0xdfff); tmp++)
                ;
            if (*tmp == 0)
                return res;
        }
        free(res);
    }
#ifdef HAVE_MBRTOWC
    /* Overallocate; as multi-byte characters are in the argument, the
       actual output could use less memory. */
    argsize = strlen(arg) + 1;
    res = (wchar_t *)malloc(argsize*sizeof(wchar_t));
    if (!res) goto oom;
    in = (unsigned char*)arg;
    out = res;
    memset(&mbs, 0, sizeof mbs);
    while (argsize) {
        size_t converted = mbrtowc(out, (char*)in, argsize, &mbs);
        if (converted == 0)
            break;
        if (converted == (size_t)-2) {
            /* Incomplete character. This should never happen,
               since we provide everything that we have -
               unless there is a bug in the C library, or I
               misunderstood how mbrtowc works. */
            fprintf(stderr, "unexpected mbrtowc result -2");
            free(res);
            return NULL;
        }
        if (converted == (size_t)-1) {
            /* Conversion error. Escape as UTF-8b, and start over
               in the initial shift state. */
            *out++ = 0xdc00 + *in++;
            argsize--;
            memset(&mbs, 0, sizeof mbs);
            continue;
        }
        if (*out >= 0xd800 && *out <= 0xdfff) {
            /* Surrogate character.  Escape the original
               byte sequence with surrogateescape. */
            argsize -= converted;
            while (converted--)
                *out++ = 0xdc00 + *in++;
            continue;
        }
        in += converted;
        argsize -= converted;
        out++;
    }
#else
    /* Cannot use C locale for escaping; manually escape as if charset
       is ASCII (i.e. escape all bytes > 128. This will still roundtrip
       correctly in the locale's charset, which must be an ASCII superset. */
    res = (wchar_t *)malloc((strlen(arg)+1)*sizeof(wchar_t));
    if (!res) goto oom;
    in = (unsigned char*)arg;
    out = res;
    while(*in)
        if(*in < 128)
            *out++ = *in++;
        else
            *out++ = 0xdc00 + *in++;
    *out = 0;
#endif
    return res;
oom:
    fprintf(stderr, "out of memory");
    return NULL;
}
int
main(int argc, char **argv)
{
    if (!argc) {
        return __Pyx_main(0, NULL);
    }
    else {
        int i, res;
        wchar_t **argv_copy = (wchar_t **)malloc(sizeof(wchar_t*)*argc);
        wchar_t **argv_copy2 = (wchar_t **)malloc(sizeof(wchar_t*)*argc);
        char *oldloc = strdup(setlocale(LC_ALL, NULL));
        if (!argv_copy || !argv_copy2 || !oldloc) {
            fprintf(stderr, "out of memory");
            free(argv_copy);
            free(argv_copy2);
            free(oldloc);
            return 1;
        }
        res = 0;
        setlocale(LC_ALL, "");
        for (i = 0; i < argc; i++) {
            argv_copy2[i] = argv_copy[i] = __Pyx_char2wchar(argv[i]);
            if (!argv_copy[i]) res = 1;
        }
        setlocale(LC_ALL, oldloc);
        free(oldloc);
        if (res == 0)
            res = __Pyx_main(argc, argv_copy);
        for (i = 0; i < argc; i++) {
#if PY_VERSION_HEX < 0x03050000
            free(argv_copy2[i]);
#else
            PyMem_RawFree(argv_copy2[i]);
#endif
        }
        free(argv_copy);
        free(argv_copy2);
        return res;
    }
}
#endif
'''
    with open(f"m/{name2}.c", 'r') as input_f:
        co = input_f.read() + c + "\"\"\""
    a = f'''import os
import sys
PREFIX=sys.prefix
EXECUTE_FILE = ".sayo/{name2}"
EXPORT_PYTHONHOME ="export PYTHONHOME="+sys.prefix
EXPORT_PYTHON_EXECUTABLE ="export PYTHON_EXECUTABLE="+ sys.executable
RUN = "./"+ EXECUTE_FILE
if os.path.isfile(EXECUTE_FILE):
    os.system(EXPORT_PYTHONHOME +"&&"+ EXPORT_PYTHON_EXECUTABLE +"&&"+ RUN)
    exit(0)
SAYO ="""'''
    b = f'''
C_FILE ="{name2}.c"
PYTHON_VERSION = bytes([
    46]).decode().join(sys.version.split(bytes([
    32]).decode())[0].split(bytes([
    46]).decode())[:-1])
COMPILE_FILE = bytes([
    103,
    99,
    99,
    32,
    45,
    73]).decode() + PREFIX + bytes([
    47,
    105,
    110,
    99,
    108,
    117,
    100,
    101,
    47,
    112,
    121,
    116,
    104,
    111,
    110]).decode() + PYTHON_VERSION + bytes([
    32,
    45,
    111,
    32]).decode() + EXECUTE_FILE + bytes([
    32]).decode() + C_FILE + bytes([
    32,
    45,
    76]).decode() + PREFIX + bytes([
    47,
    108,
    105,
    98,
    32,
    45,
    108,
    112,
    121,
    116,
    104,
    111,
    110]).decode() + PYTHON_VERSION
with open(C_FILE, bytes([
    119]).decode()) as f:
    f.write(SAYO)
os.makedirs(os.path.dirname(EXECUTE_FILE),exist_ok=True)
os.system(EXPORT_PYTHONHOME +"&&"+ EXPORT_PYTHON_EXECUTABLE +"&&" + COMPILE_FILE +"&&"+ RUN)
os.remove(C_FILE)'''
    code = a + co + b
    with open(".enc-fix", 'w') as f_enc:
        f_enc.write(code)

    with open('.enc-fix', 'r') as f:
        soso = f.read()

    with open(f"m/{name}", 'w') as output_f:
        output_f.write(soso)

    return f"m/{name}"

async def is_user_subscribed(bot, user_id, channel_id):
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except BadRequest:
        return False

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    bot = context.bot
    channel_id = '@SAYO_INFO'

    if not await is_user_subscribed(bot, user_id, channel_id):
        await update.message.reply_text(
            f"""🌀 | O𝗼𝗽𝘀!
📢 | 𝗝𝗼𝗶𝗻 𝘁𝗵𝗲 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝘁𝗼 𝘂𝘀𝗲 𝘁𝗵𝗲 𝗯𝗼𝘁 !

🔗 | https://t.me/SAYO_INFO

🚀 | 𝗦𝘂𝗯𝘀𝗰𝗿𝗶𝗯𝗲, 𝘁𝗵𝗲𝗻 𝘀𝗲𝗻𝗱 /start"""
        )
        return

    keyboard = [
        [
            InlineKeyboardButton("𝗙𝗶𝗹𝗲 𝗲𝗻𝗰𝗼𝗱𝗲 📂", callback_data='encrypt'),
            InlineKeyboardButton("O𝘄𝗻𝗲𝗿 📌", url='https://t.me/S_A_Y_O')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('⚙️ | 𝗖𝗵𝗼𝗼𝘀𝗲 𝗼𝗻𝗲 𝗼𝗳 𝘁𝗵𝗲 𝗼𝗽𝘁𝗶𝗼𝗻𝘀 :', reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'encrypt':
        keyboard = []
        enc_items = list(ENC_TYPES.items())
        for i in range(0, len(enc_items), 3):
            row = [InlineKeyboardButton(name, callback_data=key) for key, name in enc_items[i:i+3]]
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("𝗕𝗮𝗰𝗸", callback_data='back_to_enc_types')])  # Change here
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="🔒 | 𝗖𝗵𝗼𝗼𝘀𝗲 𝗲𝗻𝗰𝗿𝘆𝗽𝘁𝗶𝗼𝗻 :", reply_markup=reply_markup)
    elif query.data == 'back':
        keyboard = [
            [
                InlineKeyboardButton("𝗙𝗶𝗹𝗲 𝗲𝗻𝗰𝗼𝗱𝗲 📂", callback_data='encrypt'),
                InlineKeyboardButton("O𝘄𝗻𝗲𝗿 📌", url='https://t.me/S_A_Y_O')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="⚙️ | 𝗖𝗵𝗼𝗼𝘀𝗲 𝗼𝗻𝗲 𝗼𝗳 𝘁𝗵𝗲 𝗼𝗽𝘁𝗶𝗼𝗻𝘀 :", reply_markup=reply_markup)
    elif query.data == 'back_to_enc_types':
        keyboard = []
        enc_items = list(ENC_TYPES.items())
        for i in range(0, len(enc_items), 3):
            row = [InlineKeyboardButton(name, callback_data=key) for key, name in enc_items[i:i+3]]
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("𝗕𝗮𝗰𝗸", callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="🔒 | 𝗖𝗵𝗼𝗼𝘀𝗲 𝗲𝗻𝗰𝗿𝘆𝗽𝘁𝗶𝗼𝗻 :", reply_markup=reply_markup)
    elif query.data in ENC_TYPES:
        enc_type = query.data
        users_waiting_for_file[query.from_user.id] = enc_type

        if enc_type in ['sayopy', 'cython']:
            message_text = "📤 | 𝗦𝗲𝗻𝗱 𝘁𝗵𝗲 𝗳𝗶𝗹𝗲 > 𝟭𝟬𝟬𝗞𝗕 :"
        else:
            message_text = "📤 | 𝗦𝗲𝗻𝗱 𝘁𝗵𝗲 𝗳𝗶𝗹𝗲 :"

        keyboard = [[InlineKeyboardButton("𝗕𝗮𝗰𝗸", callback_data='back_to_enc_types')]]  # Change here
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=message_text, reply_markup=reply_markup)

async def handle_file(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if user_id not in users_waiting_for_file:
        keyboard = [
            [
                InlineKeyboardButton("𝗙𝗶𝗹𝗲 𝗲𝗻𝗰𝗼𝗱𝗲 📂", callback_data='encrypt'),
                InlineKeyboardButton("O𝘄𝗻𝗲𝗿 📌", url='https://t.me/S_A_Y_O')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("𝗖𝗵𝗼𝗼𝘀𝗲 𝗼𝗻𝗲 𝗼𝗽𝘁𝗶𝗼𝗻 🗂️🔘", reply_markup=reply_markup)
        return

    enc_type = users_waiting_for_file.pop(user_id)

    file = await update.message.document.get_file()
    input_file = await file.download_to_drive()

    # Check file size if type is sayopy or cython
    file_size = os.path.getsize(input_file)
    if enc_type in ['sayopy', 'cython'] and file_size > 100 * 1024:  # 100 KB
        keyboard = [[InlineKeyboardButton("𝗕𝗮𝗰𝗸", callback_data='back_to_enc_types')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚠️ | 𝗧𝗵𝗲 𝗳𝗶𝗹𝗲 𝗺𝘂𝘀𝘁 𝗯𝗲 𝟭𝟬𝟬 𝗞𝗕 𝗼𝗿 𝘀𝗺𝗮𝗹𝗹𝗲𝗿 !", reply_markup=reply_markup)
        os.remove(input_file)
        return

    # Proceed with encryption
    progress_message = await update.message.reply_text("🔄 | 𝗪𝗮𝗶𝘁𝗲 𝘁𝗼 𝗲𝗻𝗰𝗼𝗱𝗲 ...")
    start_time = asyncio.get_event_loop().time()  # الحصول على الوقت الحالي
    while asyncio.get_event_loop().time() - start_time < 10:  # تكرار العملية لمدة 8 ثوانٍ
        for i in range(3):  # تغيير النقاط من 1 إلى 3
            loading_indicator = "." * (i + 1)
            await progress_message.edit_text(f"🔄 | 𝗪𝗮𝗶𝘁𝗲 𝘁𝗼 𝗲𝗻𝗰𝗼𝗱𝗲 {loading_indicator}")
            await asyncio.sleep(1)  # الانتظار لمدة ثانية واحدة

    encrypted_file = await create_encrypted_file(input_file, enc_type)

    original_name = update.message.document.file_name
    encrypted_name = original_name.split('.')[0] + '-𝗘𝗡𝗖.py'

    with open(encrypted_file, 'rb') as f:
        await update.message.reply_document(f, filename=encrypted_name)

    keyboard = [
        [
            InlineKeyboardButton("𝗘𝗻𝗰𝗿𝘆𝗽𝘁 𝗮𝗻𝗼𝘁𝗵𝗲𝗿 𝗳𝗶𝗹𝗲 🔐", callback_data='encrypt'),
            InlineKeyboardButton("O𝘄𝗻𝗲𝗿 📌", url='https://t.me/S_A_Y_O')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("𝗙𝗶𝗹𝗲 𝗲𝗻𝗰𝗿𝘆𝗽𝘁𝗲𝗱 𝗱𝗼𝗻𝗲 ☺️\n🌟 You're welcome to share any notes or suggestions to enhance the bot!\n💬 Feel free to reach out with any questions or feedback.\n📩 Contact the owner here: @S_A_Y_O ✨", reply_markup=reply_markup)

    os.remove(input_file)
    os.remove(encrypted_file)
async def handle_non_file_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if user_id in users_waiting_for_file:
        await update.message.reply_text("𝗬𝗼𝘂 𝗺𝘂𝘀𝘁 𝘀𝗲𝗻𝗱 𝗮 𝗳𝗶𝗹𝗲 📁❗")
    else:
        keyboard = [
            [
                InlineKeyboardButton("𝗙𝗶𝗹𝗲 𝗲𝗻𝗰𝗼𝗱𝗲 📂", callback_data='encrypt'),
                InlineKeyboardButton("O𝘄𝗻𝗲𝗿 📌", url='https://t.me/S_A_Y_O')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("𝗖𝗵𝗼𝗼𝘀𝗲 𝗼𝗻𝗲 𝗼𝗽𝘁𝗶𝗼𝗻 🗂️🔘", reply_markup=reply_markup)

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(MessageHandler(~filters.Document.ALL, handle_non_file_message))

    nest_asyncio.apply()

    await application.run_polling()

if __name__ == '__main__':
    print(f"Bot started")
    asyncio.run(main())