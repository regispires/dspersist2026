import sys

# encoding interno do Python (utf-8)
print(sys.getdefaultencoding())

# encoding da entrada padrão (teclado)
print(sys.stdin.encoding)

# encoding do terminal/saída padrão
print(sys.stdout.encoding)

