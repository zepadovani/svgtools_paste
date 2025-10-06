# combinar_svgs.py
import xml.etree.ElementTree as ET

def combinar_svgs(arquivo_destino, arquivo_fonte, arquivo_saida):
    """
    "Cola" os elementos de um SVG fonte dentro de um SVG de destino.

    Args:
        arquivo_destino (str): Caminho para o SVG base (ex: o azul).
        arquivo_fonte (str): Caminho para o SVG a ser colado (ex: o vermelho).
        arquivo_saida (str): Caminho para o arquivo combinado final.
    """
    # Registra o namespace para evitar tags como <ns0:svg>
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    
    try:
        # Carrega e parseia os dois arquivos XML
        tree_destino = ET.parse(arquivo_destino)
        root_destino = tree_destino.getroot()
        
        tree_fonte = ET.parse(arquivo_fonte)
        root_fonte = tree_fonte.getroot()
        
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e.filename}")
        print("Certifique-se de executar o script 'gerar_svgs.py' primeiro.")
        return

    # Itera sobre todos os elementos filhos do SVG fonte (no nosso caso, apenas a <line>)
    # e os adiciona ao SVG de destino.
    # Como a escala (unidade do viewBox -> mm) é a mesma, não precisamos de transformações.
    for elemento in root_fonte:
        # Opcional: Adicionar um deslocamento para que as linhas não se sobreponham
        # Aqui, vamos movê-la um pouco para baixo para melhor visualização.
        # Criamos um grupo <g> para aplicar a transformação.
        grupo = ET.Element('g', {'transform': 'translate(0, 0.5)'})
        grupo.append(elemento)
        root_destino.append(grupo)
        
        # Se não quisesse deslocar, a linha seria mais simples:
        # root_destino.append(elemento)
        
    # Atualiza a altura do SVG de destino para acomodar a nova linha
    viewbox_vals = root_destino.get('viewBox').split()
    viewbox_vals[3] = "2" # Nova altura do viewBox
    root_destino.set('viewBox', ' '.join(viewbox_vals))
    root_destino.set('height', '2mm')

    # Escreve a árvore modificada no novo arquivo
    tree_destino.write(arquivo_saida, encoding='utf-8', xml_declaration=True)
    print(f"Arquivo combinado '{arquivo_saida}' criado com sucesso.")

# --- Programa Principal ---
if __name__ == "__main__":
    print("\nCombinando os arquivos SVG...")
    
    combinar_svgs(
        arquivo_destino="figura_azul.svg",
        arquivo_fonte="figura_vermelha.svg",
        arquivo_saida="figura_combinada.svg"
    )