import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import re
import asyncio
from playwright.async_api import async_playwright
import os

class CRMScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Scraper Profissional")
        
        # Configurar redimensionamento
        self.root.minsize(800, 600)  # Tamanho mínimo
        self.root.geometry("1024x768")  # Tamanho inicial
        
        # Configurar grid weights para permitir redimensionamento
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
        state = 'normal' if self.use_advanced_filter.get() else 'disabled'
        # Configure state only for widgets that support it (Checkbuttons, Entry, Text)
        for widget in self.advanced_frame.winfo_children():
            if isinstance(widget, (ttk.Checkbutton, ttk.Entry, tk.Text)):
                widget.configure(state=state)
            elif isinstance(widget, ttk.LabelFrame):
                for child in widget.winfo_children():
                    if isinstance(child, (ttk.Checkbutton, ttk.Entry, tk.Text)):
                        child.configure(state=state)
                
    def extract_info(self, text, label):
        """Extrai informação após os dois pontos para um determinado rótulo"""
        # Remove espaços extras e quebras de linha
        text = ' '.join(text.split())
        
        # Padrão mais flexível para encontrar texto após o rótulo
        patterns = [
            rf'{label}\s*:\s*([^:]+?)(?=\s*(?:[A-Z][a-z]+:|$))',  # Padrão normal
            rf'{label}\s*:\s*([^:]+?)(?=\s*(?:\d+/\d+/\d+|$))',   # Para datas
            rf'{label}\s*:\s*([^:]+?)(?=\s*(?:[A-Z]+|$))'         # Para outros casos
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(1).strip()
                if result:
                    return result
        return None

    async def find_text_in_page(self, page, pattern):
        # Buscar em todo o conteúdo da página
        content = await page.evaluate('document.body.innerText')
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        results = []
        
        for match in matches:
            text = match.group(0)
            # Se encontrou dois pontos, pega o texto depois
            if ':' in text:
                label = text[:text.find(':')].strip()
                after_colon = text[text.find(':') + 1:].strip()
                if after_colon:  # Se tem conteúdo após os dois pontos
                    results.append(f"{label}: {after_colon}")
            else:
                results.append(text)
        
        return results

    async def run_scraping(self, urls):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Iniciando processo de scraping...\n")
        
        try:
            async with async_playwright() as p:
                # Configurar o navegador selecionado
                browser_type = getattr(p, self.browser_var.get())
                browser = await browser_type.launch(
                    headless=not self.show_browser.get(),
                    args=['--start-maximized']
                )
                
                # Criar contexto com viewport maior
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    accept_downloads=True
                )
                
                page = await context.new_page()
                
                # Configurar timeouts mais longos
                page.set_default_timeout(30000)  # 30 segundos
                page.set_default_navigation_timeout(30000)

                for url in urls:
                    try:
                        # Adicionar delay entre requisições
                        await asyncio.sleep(1)
                        
                        # Processar URL baseado no modo de busca
                        mode = self.search_mode.get()
                        if mode == "url_contract":
                            full_url = f"{self.url_base.get().strip()}{url}"
                        else:
                            full_url = url
                            
                        results = await self.process_page(page, full_url)
                        
                        # Adicionar resultados à área de texto
                        if mode == "url_contract":
                            self.result_text.insert(tk.END, f"\nContrato {url}:\n")
                        else:
                            self.result_text.insert(tk.END, f"\nURL: {full_url}\n")
                            
                        if results:
                            for result in results:
                                self.result_text.insert(tk.END, f"- {result}\n")
                        else:
                            self.result_text.insert(tk.END, "- Nenhuma informação encontrada\n")
                        
                    except Exception as e:
                        self.result_text.insert(tk.END, f"Erro ao processar {url}: {str(e)}\n")
                
                if not self.keep_browser_open.get():
                    await browser.close()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro durante o scraping: {str(e)}")
            
    def process_input(self):
        mode = self.search_mode.get()
        urls_text = self.url_text.get(1.0, tk.END).strip()
        
        if not urls_text:
            messagebox.showwarning("Aviso", "Por favor, insira o texto para processar.")
            return
        
        # Separar as URLs/contratos (por vírgula ou quebra de linha)
        items = re.split(r'[,\n]', urls_text)
        items = [item.strip() for item in items if item.strip()]
        
        if mode == "url_contract":
            # Validar números de contrato
            valid_items = []
            for item in items:
                if self.validate_contract_number(item):
                    valid_items.append(item)
                else:
                    self.result_text.insert(tk.END, f"Aviso: Número de contrato inválido ignorado: {item}\n")
            
            if not valid_items:
                messagebox.showwarning("Aviso", "Nenhum número de contrato válido para processar.")
                return
                
            if not self.url_base.get().strip():
                messagebox.showerror("Erro", "Por favor, insira a URL base do sistema.")
                return
        else:
            valid_items = items
        
        # Executar o scraping
        if valid_items:
            asyncio.run(self.run_scraping(valid_items))
        else:
            messagebox.showwarning("Aviso", "Nenhum item válido para processar.")

    def clear_fields(self):
        self.url_text.delete(1.0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.url_base.set("")

    def load_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
                    current_tab = self.search_mode.get()
                    if current_tab == "url_contract":
                        self.url_text.delete(1.0, tk.END)
                        self.url_text.insert(tk.END, content)
                    else:  # url_only ou free_search
                        self.url_text.delete(1.0, tk.END)
                        self.url_text.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao ler o arquivo: {str(e)}")

    def validate_contract_number(self, contract):
        # Validar se o número do contrato tem entre 4 e 6 dígitos
        return bool(re.match(r'^\d{4,6}$', contract.strip()))

if __name__ == "__main__":
    root = tk.Tk()
    app = CRMScraperApp(root)
    root.mainloop()
