# Plano: Site "Figurinhas da Prof Giu"

Site estático responsivo (mobile + desktop) deployado via GitHub Pages mostrando
estatísticas da coleção de figurinhas da Copa do Mundo 2026 (EUA · MEX · CAN).

---

## Contexto técnico

| Item | Detalhe |
|---|---|
| Total de figurinhas | **994** |
| Grupos de times | A–L (12 grupos × 4 times = 48 times) |
| Seções especiais | FWC (19), CC Coca-Cola (14), nº 00 (1) |
| Dados brutos | `results.json` (por figurinha: coletada/faltando + cor RGB) |
| Deploy | GitHub Pages → pasta `/docs` na branch `main` |

---

## Stack

- **Dados** → Python (`generate_site_data.py`) gera `docs/data.js`
- **Front-end** → HTML + CSS + JS vanilla (zero dependências externas pagas)
- **Fontes** → Google Fonts (Oswald + Roboto), carregadas via CDN
- **Ícones** → Emojis Unicode de bandeiras (sem API externa)

---

## Passos

### ✅ Passo 0 — Pré-requisitos
- [x] PDF analisado com PyMuPDF (`extractor.py`, `color_analyzer.py`, `main.py`)
- [x] Mapeamento grupo A–L extraído do layout espacial do PDF
- [x] `results.json` gerado com 994 figurinhas classificadas
- [x] Dependências instaladas: `fitz`, `Pillow`, `numpy`

---

### 🔲 Passo 1 — Gerar dados do site

**Script:** `generate_site_data.py`

O script lê `results.json` e produz `docs/data.js` com a variável `ALBUM_DATA`
embutida (sem CORS issues no GitHub Pages).

Estatísticas calculadas:
- Completude global: `coletadas / 994`
- Por time: coletadas, total, porcentagem, lista de faltantes
- Ranking "times mais críticos" (menor % coletado)
- Ranking "times mais completos" (maior % coletado)
- Progresso por seção: FWC, CC, grupos A–L
- Data da última atualização

Saída: **`docs/data.js`**

---

### 🔲 Passo 2 — Criar estrutura do site

```
docs/
├── index.html      # HTML principal
├── style.css       # Design Copa 2026 (responsivo)
├── app.js          # Lógica de UI (filtros, cards, ordenação)
├── data.js         # Gerado pelo Passo 1
└── .nojekyll       # Desativa processamento Jekyll no GH Pages
```

---

### 🔲 Passo 3 — Seções do site

#### 3.1 Hero / Header
- Fundo degradê Copa 2026 (azul escuro → vermelho)
- Título "Figurinhas da Prof Giu" + subtítulo "Copa do Mundo 2026"
- Barra de progresso animada com o % geral
- Contador: "**347** de **994** figurinhas coletadas"

#### 3.2 Cards de estatísticas globais (4 cards)
| Card | Valor |
|---|---|
| Figurinhas coletadas | 347 |
| Faltando | 647 |
| Progresso | 34.9% |
| Times 100% completos | N |

#### 3.3 Destaques: Times críticos × mais completos
- Top 5 mais críticos (barra vermelha)
- Top 5 mais completos (barra verde)

#### 3.4 Grade de times (seção principal)
- Filtro por grupo (pills A–L + "Todos" + "Especiais")
- Ordenação: por grupo / % crescente / % decrescente / alfabético
- Card por time: bandeira emoji, nome, grupo badge, X/20, barra de progresso
- Cores da barra: 🔴 < 30% · 🟡 30–70% · 🟢 > 70%
- Clique no card expande lista de figurinhas faltantes
- Badge 🏠 para anfitriões (MEX, CAN, USA)

#### 3.5 Seções especiais
- FWC (FIFA World Cup History) — 19 figurinhas
- Coca-Cola — 14 figurinhas
- Figurinha nº 00

#### 3.6 Footer
- Data da última atualização
- Link para o repositório

---

### 🔲 Passo 4 — Design

**Paleta:**
```css
--blue-dark:  #002868;   /* Azul FIFA */
--blue-mid:   #003f9e;
--red:        #CC0000;
--gold:       #E8B84B;
--bg:         #F0F4F8;
--card:       #FFFFFF;
--text:       #1A1A2E;
```

**Tipografia:** Oswald (títulos bold) + Roboto (corpo)

**Responsividade:**
- Mobile (< 640px): 1 coluna
- Tablet (640–1024px): 2 colunas
- Desktop (> 1024px): 3–4 colunas

---

### 🔲 Passo 5 — Configurar GitHub Pages

1. Criar repositório público `figurinhas-prof-giu` (ou usar o atual)
2. Fazer push da pasta `docs/` na branch `main`
3. Em *Settings → Pages*: Source = `main`, folder = `/docs`
4. Site disponível em `https://<usuario>.github.io/figurinhas-prof-giu/`

**Para atualizar** após escanear novo PDF:
```bash
python main.py                  # roda o leitor de cor
python generate_site_data.py    # regenera docs/data.js
git add docs/data.js && git commit -m "update: nova leitura" && git push
```

---

### 🔲 Passo 6 — Validação

- [ ] `docs/data.js`: total = 994, coletadas + faltando = 994
- [ ] Abrir `docs/index.html` localmente no browser
- [ ] Responsividade: testar em 375px (mobile) e 1280px (desktop)
- [ ] Filtros de grupo funcionando
- [ ] Cards expandem corretamente

---

## Mapeamento de grupos (Copa 2026)

| Grupo | Times |
|---|---|
| A | 🇲🇽 México · 🇿🇦 África do Sul · 🇰🇷 Coreia do Sul · 🇨🇿 Rep. Tcheca |
| B | 🇨🇦 Canadá · 🇧🇦 Bósnia · 🇶🇦 Catar · 🇨🇭 Suíça |
| C | 🇧🇷 Brasil · 🇲🇦 Marrocos · 🇭🇹 Haiti · 🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escócia |
| D | 🇺🇸 Estados Unidos · 🇵🇾 Paraguai · 🇦🇺 Austrália · 🇹🇷 Turquia |
| E | 🇩🇪 Alemanha · 🇨🇼 Curaçao · 🇨🇮 Costa do Marfim · 🇪🇨 Equador |
| F | 🇳🇱 Holanda · 🇯🇵 Japão · 🇸🇪 Suécia · 🇹🇳 Tunísia |
| G | 🇧🇪 Bélgica · 🇪🇬 Egito · 🇮🇷 Irã · 🇳🇿 Nova Zelândia |
| H | 🇪🇸 Espanha · 🇨🇻 Cabo Verde · 🇸🇦 Arábia Saudita · 🇺🇾 Uruguai |
| I | 🇫🇷 França · 🇸🇳 Senegal · 🇮🇶 Iraque · 🇳🇴 Noruega |
| J | 🇦🇷 Argentina · 🇩🇿 Argélia · 🇦🇹 Áustria · 🇯🇴 Jordânia |
| K | 🇵🇹 Portugal · 🇨🇩 Congo · 🇺🇿 Uzbequistão · 🇨🇴 Colômbia |
| L | 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra · 🇭🇷 Croácia · 🇬🇭 Gana · 🇵🇦 Panamá |
| — | 🏆 FIFA World Cup History · 🥤 Coca-Cola · ⭐ Especial (nº 00) |

Anfitriões: **🇲🇽 México (A)** · **🇨🇦 Canadá (B)** · **🇺🇸 Estados Unidos (D)**
