import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import re
import asyncio
import random
import time
from datetime import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from playwright.async_api import async_playwright
import aiohttp
from tqdm import tqdm
import os
import json
from typing import List, Dict, Any, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class WebScraper:
    def __init__(self):
        self.user_agent = UserAgent()
        self.session = None
        self.browser = None
        self.context = None
        self.page = None
        self.results = []
        
    async def initialize(self, browser_type: str, headless: bool = True):
        """Inicializa o browser com configurações profissionais"""
        try:
            playwright = await async_playwright().start()
            browser_options = {
                'chrome': playwright.chromium,
                'firefox': playwright.firefox,
                'msedge': playwright.chromium
            }
            
            self.browser = await browser_options[browser_type].launch(
                headless=headless,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu'
                ]
            )
            
            # Configurar contexto com user agent aleatório
            self.context = await self.browser.new_context(
                user_agent=self.user_agent.random,
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True
            )
            
            # Configurar interceptação de requests
            await self.context.route("**/*", self.route_interceptor)
            
            self.page = await self.context.new_page()
            await self.setup_page_handlers()
            
        except Exception as e:
            logging.error(f"Erro ao inicializar o browser: {str(e)}")
            raise
            
    async def route_interceptor(self, route):
        """Intercepta e modifica requests para evitar detecção"""
        if route.request.resource_type in ['image', 'media', 'font']:
            await route.abort()
        else:
            headers = {
                'User-Agent': self.user_agent.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            await route.continue_(headers=headers)
            
    async def setup_page_handlers(self):
        """Configura handlers para eventos da página"""
        await self.page.set_viewport_size({'width': 1920, 'height': 1080})
        await self.page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1'
        })
        
    async def extract_text_with_context(self, element, custom_terms=None) -> Dict[str, Any]:
        """Extrai texto com contexto melhorado"""
        try:
            text = await element.inner_text()
            html = await element.inner_html()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Processar texto após os dois pontos
            if ':' in text:
                label, value = text.split(':', 1)
                return {
                    'label': label.strip(),
                    'value': value.strip(),
                    'full_text': text.strip(),
                    'html': html
                }
            
            return {
                'full_text': text.strip(),
                'html': html
            }
            
        except Exception as e:
            logging.error(f"Erro ao extrair texto: {str(e)}")
            return {'error': str(e)}
            
    async def smart_wait(self, min_time: float = 2.0, max_time: float = 5.0):
        """Espera inteligente entre requests"""
        wait_time = random.uniform(min_time, max_time)
        await asyncio.sleep(wait_time)
        
    async def search_page(self, url: str, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Realiza busca avançada na página"""
        try:
            await self.smart_wait()
            await self.page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Esperar carregamento dinâmico
            await self.page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)  # Espera adicional para conteúdo dinâmico
            
            results = []
            
            # Pegar todo o conteúdo da página primeiro
            page_content = await self.page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Função auxiliar para buscar texto
            async def search_text(selector: str, text_type: str, search_term: str = None):
                try:
                    # Busca por seletor CSS primeiro
                    elements = await self.page.query_selector_all(selector)
                    
                    # Se não encontrar, busca por texto em toda a página
                    if not elements:
                        # Usar BeautifulSoup para busca mais flexível
                        for tag in soup.find_all(text=True):
                            if search_term:
                                if search_term.lower() in tag.lower():
                                    results.append({
                                        'type': text_type,
                                        'text': tag.strip(),
                                        'url': url
                                    })
                            else:
                                results.append({
                                    'type': text_type,
                                    'text': tag.strip(),
                                    'url': url
                                })
                    else:
                        for el in elements:
                            text = await el.inner_text()
                            html = await el.inner_html()
                            
                            # Extrair texto após os dois pontos se existir
                            if ':' in text:
                                label, value = text.split(':', 1)
                                results.append({
                                    'type': text_type,
                                    'label': label.strip(),
                                    'value': value.strip(),
                                    'full_text': text.strip(),
                                    'html': html,
                                    'url': url
                                })
                            else:
                                results.append({
                                    'type': text_type,
                                    'text': text.strip(),
                                    'html': html,
                                    'url': url
                                })
                            
                except Exception as e:
                    logging.error(f"Erro ao buscar {text_type}: {str(e)}")
            
            # Busca por tipo de conteúdo
            if search_params.get('cod', False):
                await search_text('text="COD" i, text="CÓD" i, text="BANCO" i, [id*="cod" i], [class*="cod" i]', 'cod')
            
            if search_params.get('nome', False):
                await search_text('text="NOME" i, text="CLIENTE" i, [id*="nome" i], [class*="nome" i]', 'nome')
            
            if search_params.get('cpf', False):
                await search_text('text="CPF" i, text="DOCUMENTO" i, [id*="cpf" i], [class*="cpf" i]', 'cpf')
            
            if search_params.get('acordo', False):
                await search_text('text="ACORDO" i, text="CONTRATO" i, [id*="acordo" i], [class*="acordo" i]', 'acordo')
            
            # Busca personalizada
            if search_params.get('custom', False) and search_params.get('custom_terms'):
                for term in search_params['custom_terms']:
                    term = term.strip()
                    if term:
                        # Busca mais flexível para termos personalizados
                        await search_text(f'*', 'custom', term)
            
            # Busca livre - busca em todo o conteúdo da página
            if search_params.get('free_search', False):
                # Pegar todo o texto visível da página
                page_text = await self.page.evaluate('() => document.body.innerText')
                
                # Dividir em linhas e processar cada uma
                lines = page_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        results.append({
                            'type': 'free_search',
                            'text': line,
                            'url': url
                        })
            
            # Remover duplicatas mantendo a ordem
            seen = set()
            unique_results = []
            for r in results:
                # Criar uma chave única baseada no tipo e texto
                key = (r.get('type'), r.get('text', ''), r.get('full_text', ''))
                if key not in seen:
                    seen.add(key)
                    unique_results.append(r)
            
            return unique_results
            
        except Exception as e:
            logging.error(f"Erro ao buscar página {url}: {str(e)}")
            return [{'error': str(e), 'url': url}]
            
    async def close(self):
        """Fecha recursos do scraper"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

class CRMScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper Profissional")
        self.scraper = WebScraper()
        
        # Configurar redimensionamento
        self.root.minsize(800, 600)
        self.root.geometry("1024x768")
        
        # Configurar grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Frame principal com scroll
        self.main_canvas = tk.Canvas(root)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Layout dos componentes principais
        self.main_canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Frame principal com padding
        main_frame = ttk.Frame(self.scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Frame para configurações do navegador
        browser_frame = ttk.LabelFrame(main_frame, text="Configurações do Navegador", padding="5")
        browser_frame.grid(row=0, column=0, sticky="ew", pady=5)
        browser_frame.grid_columnconfigure(1, weight=1)
        
        # Seleção do navegador
        ttk.Label(browser_frame, text="Navegador:").grid(row=0, column=0, sticky="w", padx=5)
        self.browser_var = tk.StringVar(value="chrome")
        ttk.Radiobutton(browser_frame, text="Google Chrome", variable=self.browser_var, value="chrome").grid(row=0, column=1, padx=5)
        ttk.Radiobutton(browser_frame, text="Firefox", variable=self.browser_var, value="firefox").grid(row=0, column=2, padx=5)
        ttk.Radiobutton(browser_frame, text="Microsoft Edge", variable=self.browser_var, value="msedge").grid(row=0, column=3, padx=5)
        
        # Opções do navegador
        self.show_browser = tk.BooleanVar(value=True)
        ttk.Checkbutton(browser_frame, text="Mostrar navegador", variable=self.show_browser).grid(row=1, column=0, columnspan=2, sticky="w", padx=5)
        self.keep_browser_open = tk.BooleanVar(value=False)
        ttk.Checkbutton(browser_frame, text="Manter navegador aberto", variable=self.keep_browser_open).grid(row=1, column=2, columnspan=2, sticky="w", padx=5)
        
        # Frame para modo de busca
        search_mode_frame = ttk.LabelFrame(main_frame, text="Modo de Busca", padding="5")
        search_mode_frame.grid(row=1, column=0, sticky="ew", pady=5)
        search_mode_frame.grid_columnconfigure(1, weight=1)
        
        # Seleção do modo de busca
        self.search_mode = tk.StringVar(value="url_only")
        ttk.Radiobutton(search_mode_frame, text="Apenas URL", variable=self.search_mode, 
                       value="url_only", command=self.toggle_search_mode).grid(row=0, column=0, padx=5)
        ttk.Radiobutton(search_mode_frame, text="URL + Número do Contrato", variable=self.search_mode, 
                       value="url_contract", command=self.toggle_search_mode).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(search_mode_frame, text="Busca Livre", variable=self.search_mode, 
                       value="free_search", command=self.toggle_search_mode).grid(row=0, column=2, padx=5)
        
        # Frame para entrada de URLs
        self.url_frame = ttk.LabelFrame(main_frame, text="URLs para Busca", padding="5")
        self.url_frame.grid(row=2, column=0, sticky="ew", pady=5)
        self.url_frame.grid_columnconfigure(0, weight=1)
        
        # URL Base (para modo contrato)
        self.url_base_frame = ttk.Frame(self.url_frame)
        self.url_base_frame.grid(row=0, column=0, sticky="ew")
        self.url_base_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(self.url_base_frame, text="URL Base:").grid(row=0, column=0, sticky="w", padx=5)
        self.url_base = tk.StringVar()
        ttk.Entry(self.url_base_frame, textvariable=self.url_base).grid(row=0, column=1, sticky="ew", padx=5)
        
        # Área de texto para URLs/contratos
        self.url_text = scrolledtext.ScrolledText(self.url_frame, height=8)
        self.url_text.grid(row=1, column=0, sticky="ew", pady=5)
        ttk.Label(self.url_frame, text="Cole as URLs (uma por linha) ou números de contrato").grid(row=2, column=0, sticky="w")
        
        # Frame para filtros de busca
        filter_frame = ttk.LabelFrame(main_frame, text="Filtros de Busca", padding="5")
        filter_frame.grid(row=3, column=0, sticky="ew", pady=5)
        filter_frame.grid_columnconfigure(0, weight=1)
        
        # Checkbutton para ativar filtro avançado
        self.use_advanced_filter = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="Usar Filtro Avançado", 
                       variable=self.use_advanced_filter,
                       command=self.toggle_advanced_filters).grid(row=0, column=0, sticky="w")
        
        # Frame para opções de filtro
        self.advanced_frame = ttk.Frame(filter_frame)
        self.advanced_frame.grid(row=1, column=0, sticky="ew", pady=5)
        self.advanced_frame.grid_columnconfigure((0,1), weight=1)
        
        # Checkboxes para cada tipo de busca
        self.filter_vars = {
            'cod': tk.BooleanVar(value=True),
            'nome': tk.BooleanVar(value=False),
            'cpf': tk.BooleanVar(value=False),
            'acordo': tk.BooleanVar(value=False),
            'custom': tk.BooleanVar(value=False)
        }
        
        ttk.Checkbutton(self.advanced_frame, text="Buscar COD/CÓD/BANCO", 
                       variable=self.filter_vars['cod']).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(self.advanced_frame, text="Buscar Nome Completo", 
                       variable=self.filter_vars['nome']).grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(self.advanced_frame, text="Buscar CPF", 
                       variable=self.filter_vars['cpf']).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(self.advanced_frame, text="Buscar Acordo", 
                       variable=self.filter_vars['acordo']).grid(row=1, column=1, sticky="w")
        
        # Frame para busca personalizada
        custom_search_frame = ttk.LabelFrame(self.advanced_frame, text="Busca Personalizada", padding="5")
        custom_search_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        custom_search_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Checkbutton(custom_search_frame, text="Ativar Busca Personalizada", 
                       variable=self.filter_vars['custom']).grid(row=0, column=0, sticky="w")
        
        ttk.Label(custom_search_frame, text="Palavras ou frases (separadas por vírgula):").grid(row=1, column=0, sticky="w", pady=2)
        self.custom_search_text = tk.Text(custom_search_frame, height=3)
        self.custom_search_text.grid(row=2, column=0, sticky="ew", pady=2)
        
        self.custom_after_colon = tk.BooleanVar(value=False)
        ttk.Checkbutton(custom_search_frame, text="Buscar apenas texto após os dois pontos (:)", 
                       variable=self.custom_after_colon).grid(row=3, column=0, sticky="w")
        
        # Frame para botões
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky="ew", pady=10)
        button_frame.grid_columnconfigure((0,1,2), weight=1)
        
        ttk.Button(button_frame, text="Carregar arquivo .txt", command=self.load_file).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Processar", command=self.process_input).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Limpar", command=self.clear_fields).grid(row=0, column=2, padx=5)
        
        # Frame para resultados
        result_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="5")
        result_frame.grid(row=5, column=0, sticky="ew", pady=5)
        result_frame.grid_columnconfigure(0, weight=1)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=15)
        self.result_text.grid(row=0, column=0, sticky="ew", pady=5)
        
        # Inicializar estados
        self.toggle_search_mode()
        self.toggle_advanced_filters()

    def toggle_search_mode(self):
        """Alterna o modo de busca"""
        mode = self.search_mode.get()
        if mode == "url_only":
            self.url_base_frame.grid_remove()
            self.url_text.configure(height=8)
            self.url_text.delete(1.0, tk.END)
            self.url_text.insert(tk.END, "Cole as URLs completas aqui (uma por linha)")
        elif mode == "url_contract":
            self.url_base_frame.grid()
            self.url_text.configure(height=6)
            self.url_text.delete(1.0, tk.END)
            self.url_text.insert(tk.END, "Cole os números dos contratos aqui (um por linha)")
        else:  # free_search
            self.url_base_frame.grid_remove()
            self.url_text.configure(height=8)
            self.url_text.delete(1.0, tk.END)
            self.url_text.insert(tk.END, "Cole qualquer texto para buscar (URL, número, frase)")

    def toggle_advanced_filters(self):
        """Alterna a visibilidade dos filtros avançados"""
        if self.use_advanced_filter.get():
            self.advanced_frame.grid(row=1, column=0, sticky="ew", pady=5)
        else:
            self.advanced_frame.grid_remove()

    def clear_fields(self):
        """Limpa todos os campos"""
        self.url_text.delete(1.0, tk.END)
        self.url_base.set("")
        self.custom_search_text.delete(1.0, tk.END)
        self.result_text.delete(1.0, tk.END)

    def load_file(self):
        """Carrega URLs de um arquivo"""
        filename = filedialog.askopenfilename(
            title="Selecione o arquivo de URLs",
            filetypes=(("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*"))
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.url_text.delete(1.0, tk.END)
                    self.url_text.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar arquivo: {str(e)}")
                
    async def process_urls(self, urls: List[str], search_params: Dict[str, Any]):
        """Processa URLs com progress bar"""
        results = []
        
        # Inicializar scraper
        browser_type = self.browser_var.get()
        show_browser = self.show_browser.get()
        await self.scraper.initialize(browser_type, not show_browser)
        
        try:
            for url in tqdm(urls, desc="Processando URLs"):
                # Verificar se URL é válida
                if not url.startswith(('http://', 'https://')):
                    url = f'https://{url}'
                    
                page_results = await self.scraper.search_page(url, search_params)
                results.extend(page_results)
                
                # Salvar resultados parciais
                self.save_results(results)
                
            return results
            
        finally:
            await self.scraper.close()
            
    def save_results(self, results: List[Dict[str, Any]]):
        """Salva resultados em arquivo JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'resultados_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
    def process_input(self):
        """Processa entrada do usuário"""
        try:
            # Obter URLs
            urls = self.get_urls()
            if not urls:
                messagebox.showerror("Erro", "Por favor, insira pelo menos uma URL válida")
                return
                
            # Construir parâmetros de busca
            search_params = {
                'cod': self.filter_vars['cod'].get(),
                'nome': self.filter_vars['nome'].get(),
                'cpf': self.filter_vars['cpf'].get(),
                'acordo': self.filter_vars['acordo'].get(),
                'custom': self.filter_vars['custom'].get(),
                'custom_terms': self.get_custom_terms() if self.filter_vars['custom'].get() else [],
                'free_search': self.search_mode.get() == 'free_search'
            }
            
            # Limpar área de resultados
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "Iniciando busca...\n\n")
            self.root.update()
            
            # Executar busca de forma assíncrona
            results = asyncio.run(self.process_urls(urls, search_params))
            
            # Mostrar resultados na interface
            self.result_text.delete(1.0, tk.END)
            if results:
                for result in results:
                    if 'error' in result:
                        self.result_text.insert(tk.END, f"Erro na URL {result['url']}: {result['error']}\n\n")
                    else:
                        self.result_text.insert(tk.END, f"Tipo: {result['type']}\n")
                        if 'label' in result and 'value' in result:
                            self.result_text.insert(tk.END, f"Campo: {result['label']}\n")
                            self.result_text.insert(tk.END, f"Valor: {result['value']}\n")
                        elif 'text' in result:
                            self.result_text.insert(tk.END, f"Texto: {result['text']}\n")
                        self.result_text.insert(tk.END, f"URL: {result['url']}\n\n")
            else:
                self.result_text.insert(tk.END, "Nenhum resultado encontrado.\n")
            
        except Exception as e:
            logging.error(f"Erro ao processar entrada: {str(e)}")
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            
    def get_urls(self) -> List[str]:
        """Obtém lista de URLs do input"""
        text = self.url_text.get(1.0, tk.END).strip()
        if not text:
            return []
            
        urls = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                if self.search_mode.get() == 'url_contract':
                    base_url = self.url_base.get().strip()
                    if base_url:
                        urls.append(f"{base_url}{line}")
                else:
                    urls.append(line)
                    
        return urls
        
    def get_custom_terms(self) -> List[str]:
        """Obtém termos de busca personalizados"""
        text = self.custom_search_text.get(1.0, tk.END).strip()
        if not text:
            return []
        return [term.strip() for term in text.split(',') if term.strip()]

if __name__ == "__main__":
    root = tk.Tk()
    app = CRMScraperApp(root)
    root.mainloop()
