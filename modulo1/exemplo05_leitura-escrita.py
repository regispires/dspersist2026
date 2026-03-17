with open("arquivo.txt", "w", encoding="utf-8") as file:
    while True:
        linha = input()
        if linha == "":
            break
        file.write(linha + "\n")