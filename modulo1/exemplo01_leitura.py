with open("arquivo.txt", "r") as file:
    linha = file.readline()
    while linha:
		# .strip() remove espaços em branco e 
        # quebras de linha extras
        print(linha.rstrip())
        linha = file.readline()
