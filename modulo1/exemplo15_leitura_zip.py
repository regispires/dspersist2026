import zipfile
# Caminho para o arquivo .zip
caminho_zip = 'modulo1.zip'
# Abre o arquivo .zip e exibe o conteúdo de todos os arquivos .txt internos
with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
	# Itera sobre cada arquivo dentro do zip
	for nome_arquivo in zip_ref.namelist():
		# Verifica se o arquivo termina com .txt
		if nome_arquivo.endswith('.txt'):
			with zip_ref.open(nome_arquivo) as file:
				conteudo = file.read().decode('utf-8')
				print(f'Conteúdo de {nome_arquivo}:')
				print(conteudo)
				print('-' * 40) # Linha separadora para cada arquivo
