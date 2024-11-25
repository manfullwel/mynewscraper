# Web Scraper Profissional

Um scraper profissional com interface gráfica para extrair informações de páginas web.

## Funcionalidades

- Interface gráfica amigável
- Múltiplos modos de busca:
  - Apenas URL
  - URL + Número do Contrato
  - Busca Livre
- Filtros avançados para:
  - Códigos/Bancos
  - Nomes
  - CPF
  - Acordos
  - Busca personalizada
- Rotação automática de User Agents
- Salvamento automático de resultados
- Suporte a Chrome, Firefox e Edge

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/mynewscraper.git
cd mynewscraper
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Instale os navegadores necessários:
```bash
playwright install
```

## Uso

1. Execute o programa:
```bash
python main_improved.py
```

2. Na interface:
   - Escolha o navegador
   - Selecione o modo de busca
   - Cole as URLs ou números
   - Configure os filtros
   - Clique em "Processar"

## Resultados

Os resultados são:
- Exibidos na interface
- Salvos em arquivos JSON com timestamp
- Registrados em log para debug

## Requisitos

- Python 3.8+
- Playwright
- BeautifulSoup4
- Tkinter (incluído com Python)
- Outros requisitos em requirements.txt

## Contribuição

Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Enviar pull requests

## Licença

MIT License
