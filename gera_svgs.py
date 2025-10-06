# gerar_svgs.py
import xml.etree.ElementTree as ET

def criar_svg_linha(nome_arquivo, largura_mm, cor):
    """
    Cria um arquivo SVG contendo uma única linha horizontal.

    Args:
        nome_arquivo (str): O nome do arquivo a ser salvo (ex: 'figura.svg').
        largura_mm (int): A largura da figura e da linha em milímetros.
        cor (str): A cor da linha (ex: 'blue', 'red').
    """
    # O namespace do SVG é necessário para o ElementTree
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    
    # Define os atributos da tag <svg>
    # A mágica está aqui: width e viewBox.width têm o mesmo valor numérico.
    svg_attrs = {
        "width": f"{largura_mm}mm",
        "height": "1mm", # Altura arbitrária para visualização
        "viewBox": f"0 0 {largura_mm} 1",
        "version": "1.1"
    }
    
    # Cria o elemento raiz <svg>
    svg_root = ET.Element("svg", svg_attrs)

    # Cria o elemento <line>
    # A linha vai de x=0 até x=largura_mm, no meio da altura (y=0.5)
    line_attrs = {
        "x1": "0",
        "y1": "0.5",
        "x2": str(largura_mm),
        "y2": "0.5",
        "stroke": cor,
        "stroke-width": "0.2" # Espessura da linha em unidades do viewBox (0.2mm)
    }
    linha = ET.Element("line", line_attrs)
    
    # Adiciona a linha ao SVG
    svg_root.append(linha)
    
    # Cria a árvore XML e a escreve no arquivo
    tree = ET.ElementTree(svg_root)
    # Escreve com a declaração XML e codificação UTF-8
    tree.write(nome_arquivo, encoding='utf-8', xml_declaration=True)
    
    print(f"Arquivo '{nome_arquivo}' criado com sucesso.")

# --- Programa Principal ---
if __name__ == "__main__":
    print("Gerando os arquivos SVG iniciais...")
    
    # Cria a figura azul de 4mm
    criar_svg_linha(
        nome_arquivo="figura_azul.svg",
        largura_mm=4,
        cor="blue"
    )
    
    # Cria a figura vermelha de 3mm
    criar_svg_linha(
        nome_arquivo="figura_vermelha.svg",
        largura_mm=3,
        cor="red"
    )
    
    print("\nArquivos gerados.")
    