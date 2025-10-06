# combinar_svgs.py
import xml.etree.ElementTree as ET

def combinar_svgs(arquivo_destino, arquivo_fonte, arquivo_saida, x_offset=0, y_offset=0.5):
    """
    "Cola" os elementos de um SVG fonte dentro de um SVG de destino, preservando exatamente
    as dimensões originais em mm.

    Args:
        arquivo_destino (str): Caminho para o SVG base (ex: container.svg).
        arquivo_fonte (str): Caminho para o SVG a ser colado (ex: topaste.svg).
        arquivo_saida (str): Caminho para o arquivo combinado final.
        x_offset (float): Deslocamento horizontal em mm.
        y_offset (float): Deslocamento vertical em mm.
    """
    # Registra os namespaces necessários
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")
    
    try:
        # Carrega e parseia os dois arquivos XML
        tree_destino = ET.parse(arquivo_destino)
        root_destino = tree_destino.getroot()
        
        tree_fonte = ET.parse(arquivo_fonte)
        root_fonte = tree_fonte.getroot()
        
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e.filename}")
        print("Certifique-se de que os arquivos SVG existem.")
        return
    
    # Extrai as dimensões originais do SVG fonte
    fonte_width = root_fonte.get('width')
    fonte_height = root_fonte.get('height')
    fonte_viewbox = root_fonte.get('viewBox')
    
    # Extrai os valores numéricos das dimensões
    fonte_width_value = None
    if fonte_width:
        if fonte_width.endswith('mm'):
            fonte_width_value = float(fonte_width[:-2])
        else:
            fonte_width_value = float(fonte_width)
    
    fonte_height_value = None
    if fonte_height:
        if fonte_height.endswith('mm'):
            fonte_height_value = float(fonte_height[:-2])
        else:
            fonte_height_value = float(fonte_height)
    
    # Se temos viewBox, podemos extrair as dimensões dele também
    fonte_viewbox_width = None
    fonte_viewbox_height = None
    if fonte_viewbox:
        parts = fonte_viewbox.split()
        if len(parts) == 4:
            fonte_viewbox_width = float(parts[2])
            fonte_viewbox_height = float(parts[3])
    
    # Determina as dimensões finais - usa viewBox se width/height não estão definidos
    if fonte_width_value is None and fonte_viewbox_width is not None:
        fonte_width_value = fonte_viewbox_width
    
    if fonte_height_value is None and fonte_viewbox_height is not None:
        fonte_height_value = fonte_viewbox_height
    
    print(f"Dimensões originais do SVG fonte: {fonte_width_value}mm x {fonte_height_value}mm")
    
    # Primeiro, adicione um elemento defs se ele não existir
    defs = None
    for child in root_destino:
        if child.tag.endswith('defs'):
            defs = child
            break
            
    if defs is None:
        defs = ET.SubElement(root_destino, 'defs')

    # Cria um symbol que contém o conteúdo do SVG fonte e mantém suas dimensões exatas
    symbol_id = "svg_fonte_symbol"
    symbol = ET.SubElement(defs, 'symbol')
    symbol.set('id', symbol_id)
    
    # Define as dimensões exatas do símbolo
    if fonte_viewbox:
        symbol.set('viewBox', fonte_viewbox)
    
    if fonte_width:
        symbol.set('width', fonte_width)
    
    if fonte_height:
        symbol.set('height', fonte_height)
    
    # Adiciona todos os elementos do SVG fonte ao símbolo
    for elemento in root_fonte:
        symbol.append(elemento)
    
    # Usa o elemento <use> para referenciar o símbolo, garantindo que mantenha
    # suas dimensões originais exatas
    use_element = ET.SubElement(root_destino, 'use')
    use_element.set('{http://www.w3.org/1999/xlink}href', f'#{symbol_id}')
    use_element.set('x', str(x_offset))
    use_element.set('y', str(y_offset))
    
    # Define explicitamente as dimensões em mm para garantir que serão mantidas
    if fonte_width:
        use_element.set('width', fonte_width)
    elif fonte_width_value is not None:
        use_element.set('width', f'{fonte_width_value}mm')
    
    if fonte_height:
        use_element.set('height', fonte_height)
    elif fonte_height_value is not None:
        use_element.set('height', f'{fonte_height_value}mm')
    
    # Assegura que o elemento use não será escalado
    use_element.set('preserveAspectRatio', 'xMinYMin meet')
    
    # Atualiza as dimensões do SVG de destino se necessário
    destino_viewbox = root_destino.get('viewBox')
    if destino_viewbox:
        viewbox_vals = destino_viewbox.split()
        
        # Assegura que o viewBox é grande o suficiente para conter o elemento colado
        # Só ajusta se for necessário aumentar
        min_width = x_offset + fonte_width_value
        if float(viewbox_vals[2]) < min_width:
            viewbox_vals[2] = str(min_width)
            root_destino.set('width', f"{min_width}mm")
            
        min_height = y_offset + fonte_height_value
        if float(viewbox_vals[3]) < min_height:
            viewbox_vals[3] = str(min_height) 
            root_destino.set('height', f"{min_height}mm")
            
        root_destino.set('viewBox', ' '.join(viewbox_vals))

    # Escreve a árvore modificada no novo arquivo
    tree_destino.write(arquivo_saida, encoding='utf-8', xml_declaration=True)
    print(f"Arquivo combinado '{arquivo_saida}' criado com sucesso.")

# --- Programa Principal ---
if __name__ == "__main__":
    print("\nCombinando os arquivos SVG...")
    
    combinar_svgs(
        arquivo_destino="container.svg",
        arquivo_fonte="topaste.svg",
        arquivo_saida="container_plus_paste.svg",
        x_offset=10,  # Posição X em mm onde o SVG fonte será colado
        y_offset=5    # Posição Y em mm onde o SVG fonte será colado
    )