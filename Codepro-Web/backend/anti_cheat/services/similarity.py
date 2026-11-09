"""Language aware token fingerprints. This produces review signals, not a verdict."""
import hashlib
import re

ALGORITHM_VERSION = 'token-winnow-1'
MAX_SOURCE_LENGTH = 200_000
KEYWORDS = set('''and as assert async await break case catch class const continue def delete do else
except false False final finally for from if import in instanceof interface is lambda let new
None null or package pass private protected public raise return static struct switch this
throw throws true True try typedef using var virtual void while yield auto bool char double
float int long short signed unsigned string String vector map set include namespace std'''.split())
TOKEN_RE = re.compile(
    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/|'
    r'#[^\n]*|[A-Za-z_]\w*|\d+(?:\.\d+)?|==|!=|<=|>=|&&|\|\||->|::|[^\s]',
    re.MULTILINE,
)


def normalize_tokens(source, language=''):
    if len(source) > MAX_SOURCE_LENGTH:
        raise ValueError('Source exceeds anti-cheat scan limit')
    language = language.lower()
    python = 'python' in language or language.startswith('py')
    normalized = []
    for match in TOKEN_RE.finditer(source):
        token = match.group(0)
        if token.startswith(('//', '/*')):
            continue
        if token.startswith('#') and (python or token.lower().startswith(('#include', '#define', '#pragma'))):
            continue
        if token.startswith(('"', "'")):
            normalized.append('STR')
        elif token[0].isdigit():
            normalized.append('NUM')
        elif token[0].isalpha() or token[0] == '_':
            normalized.append(token if token in KEYWORDS else 'ID')
        else:
            normalized.append(token)
    return normalized


def fingerprint(tokens, ngram_size=7, window_size=4):
    if len(tokens) < ngram_size:
        return set()
    hashes = [int.from_bytes(hashlib.blake2b(
        '\x1f'.join(tokens[i:i + ngram_size]).encode(), digest_size=8
    ).digest(), 'big') for i in range(len(tokens) - ngram_size + 1)]
    if len(hashes) <= window_size:
        return set(hashes)
    return {min(hashes[i:i + window_size]) for i in range(len(hashes) - window_size + 1)}


def similarity_score(first, second):
    if not first or not second:
        return 0.0
    return round(100.0 * len(first & second) / len(first | second), 2)


def source_digest(source):
    return hashlib.sha256(source.encode('utf-8')).hexdigest()
