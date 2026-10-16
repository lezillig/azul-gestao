# 01 — Arquitetura

## Visão geral

```
┌──────────────────────────────────────────────────────────────┐
│                        FONTES EXTERNAS                       │
│   Omie (ERP)      Ituran (rastreamento)     Ponto (jornada)  │
│   PNCP (licitações)   E-mail contasapagar@   Planilhas legadas│
└───────┬──────────────────┬──────────────────────┬────────────┘
        │ MCP omie         │ MCP ituran           │ MCP ponto
        ▼                  ▼                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    CAMADA DE INTEGRAÇÃO (mcp/)               │
│  Servidores MCP expõem tools; usados pela API, pelos agentes  │
│  e pelo Claude em conversa. Só leitura por padrão; escrita   │
│  explícita e logada.                                          │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                  POSTGRES ÚNICO (schemas por domínio)         │
│ cadastro │ compliance │ pessoas │ operacao │ frota │          │
│ financeiro │ comercial │ auditoria                            │
└───────┬───────────────────────┬──────────────────────┬───────┘
        ▼                       ▼                      ▼
┌───────────────┐   ┌───────────────────┐   ┌───────────────────┐
│ API (app/)    │   │ AGENTES (agents/) │   │ RELATÓRIOS        │
│ FastAPI, CRUD │   │ jobs agendados,   │   │ (reports/) SQL +  │
│ por módulo    │   │ regras + LLM só   │   │ dashboards HTML   │
│               │   │ para exceções     │   │                   │
└───────────────┘   └─────────┬─────────┘   └───────────────────┘
                              ▼
                    ┌───────────────────┐
                    │ PENDÊNCIAS        │  ← humano aprova/rejeita
                    │ + ALERTAS (e-mail)│
                    └───────────────────┘
```

## Componentes

| Componente | Responsabilidade | Onde |
|---|---|---|
| Banco | Fonte única da verdade; histórico; auditoria | `db/` |
| API | CRUD, validações, regras de negócio síncronas | `app/` |
| MCP | Adaptadores para sistemas externos, com contrato estável de tools | `mcp/` |
| Agentes | Rotinas periódicas: coletar → comparar → apontar exceção → pendência/alerta | `agents/` |
| Relatórios | KPIs e dashboards lidos do banco | `reports/` |
| Pendências | Fila única de decisões humanas (aprovação, correção, ciência) | `auditoria.pendencia` |

## Decisões de arquitetura (ADRs)

### ADR-001 — Um banco por sistema, nunca um banco por módulo · **revisto em 15/10/2026**
**Contexto**: a proposta original era um PostgreSQL único com schema por domínio. Na prática a gestão (`public`) e a controladoria (`controladoria`) dividem o mesmo banco no Neon, e a credencial de um sistema alcança o schema do outro. A controladoria já tem um plano para ir a um banco próprio (`controladoria/docs/separar-bancos.md`).
**Decisão**: **dois bancos**, um por sistema: o da gestão (operação, cadastro mestre, frota, pessoas) e o da controladoria (financeiro, comercial). Dentro de cada sistema, os módulos novos continuam no banco dele — nada de banco por módulo.
**Como os dois se cruzam**: a controladoria lê a gestão por uma conexão própria, com papel **somente leitura** e consultas explícitas num arquivo só (`src/lib/gestao/leitura.ts`). Nenhum JOIN entre bancos; nenhuma escrita de um sistema no banco do outro. O que um relatório precisar dos dois lados (ex.: margem por contrato = contrato da gestão × lançamentos da controladoria) é montado na controladoria a partir dessas leituras.
**Consequência**: o cadastro mestre (veículo, pessoa, cliente, contrato) tem dono único — a gestão — e a controladoria referencia por id/chave natural, sem duplicar. Toda tabela nova que a controladoria precise ler entra também em `leitura.ts` e no GRANT do papel somente leitura.

### ADR-002 — Herdar a stack da gestão e da controladoria (Next.js + Prisma) · **decidido em 15/10/2026**
**Contexto**: a proposta original era Python (FastAPI + SQLAlchemy + Alembic), "salvo se a controladoria existente impuser outra". A verificação (ver `docs/06-mapa-do-existente.md`) mostrou que a controladoria **e** a gestão de motoristas já rodam em produção em Next.js 16 + Prisma 6 + PostgreSQL (Neon) na Vercel, compartilham o login, e já têm boa parte do cadastro mestre (veículo, motorista, cliente, escala, ponto, abastecimento) e todas as integrações (Omie, Ituran, TiqueTaque, SIAT, Sofit, Ticket Log, LW, Prodesp).
**Decisão**: não criar um terceiro sistema. O código novo entra nos dois repositórios que já existem:
- `lezillig/gestao-motoristas` — cadastro mestre, compliance, pessoas/ponto, operação e frota;
- `lezillig/controladoria` — financeiro, custos, comercial e simulador.

Este repositório (`azul-gestao`) guarda o **plano**: specs, docs, backlog e decisões. `db/schema.sql` e `agents/_template.py` ficam como referência de modelo, não como código a executar; o que faltar vira migração Prisma no repositório dono da tabela.
**Consequência**: uma linguagem, um login, um deploy por sistema. Python só entra se um caso concreto exigir (ex.: biblioteca sem equivalente em TypeScript), como exceção registrada aqui.

### ADR-003 — Integrações sempre via MCP · **em revisão (15/10/2026)**
**Decisão**: nenhum módulo chama API externa diretamente; chama a tool do servidor MCP correspondente. O servidor encapsula autenticação, paginação, rate limit e normalização.
**Consequência**: o mesmo conector serve a API, os agentes e o Claude em conversa; trocar fornecedor (ex.: outro rastreador) muda um lugar só.
**Revisão**: os clientes TypeScript que já existem (`src/lib/ituran/`, `src/lib/tiquetaque/`, `src/lib/omie/` etc.) já encapsulam autenticação, paginação e normalização, e são o "um lugar só". Proposta: o código continua chamando esses clientes; servidor MCP só onde o Claude precisar consultar o sistema em conversa, e como casca fina sobre o mesmo cliente.

### ADR-004 — Regras são código; LLM só para exceção e redação
**Decisão**: comparar odômetro, detectar vencimento, validar NF contra OS, conferir jornada: tudo em SQL/Python determinístico e testável. O LLM entra para (a) interpretar documentos não estruturados (PDF de NF, e-mail), (b) classificar e priorizar exceções, (c) redigir mensagens e relatórios.
**Consequência**: resultados reproduzíveis, auditáveis e baratos.

### ADR-005 — Agentes nunca executam ação financeira ou trabalhista sem aprovação
**Decisão**: pagamento, lançamento na Omie, desconto em folha, indicação de condutor em multa, bloqueio de motorista → o agente cria `pendencia` com proposta e evidências; um humano aprova na interface; só então a ação executa (e é logada).
**Consequência**: a fila de pendências é a tela mais importante do sistema.

### ADR-006 — Chaves naturais e sem exclusão física
**Decisão**: placa, CPF, CNPJ e número de contrato são únicos e imutáveis; registros são desativados, nunca apagados.

### ADR-008 — A Ituran é a base oficial da frota · **decidido em 15/10/2026**
**Contexto**: o código da gestão hoje trata o cadastro do SIAT como correto e corrige as placas que a Ituran reporta erradas (`src/lib/ituran/plateAliases.ts`).
**Decisão**: a relação de veículos da Ituran define **quais veículos a empresa tem**. Veículo ativo no SIAT, na Sofit, no Ticket Log ou na planilha e ausente da Ituran é divergência a resolver, não veículo válido. A placa é sempre a chave; a correção de grafia de placa (`plateAliases.ts`) continua existindo, mas cada entrada precisa de data e motivo e é revista a cada renovação de frota.
**Consequência**: o relatório de divergências da Fase 0 usa a Ituran como referência e lista, de cada outra fonte, o que sobra e o que falta.

### ADR-010 — Cadastro único do veículo, com ficha por área · **decidido em 16/10/2026**
**Decisão**: um só registro do veículo, dividido em seções com área dona: Aquisição (Financeiro: nota fiscal, anos, chassi, compra, venda, financiamento, adaptações), Frota (placa, renavam, lugares, tipo, prefixo) e Documentação (tipo de operação, licenças, apólice, CRLV). Cada área edita a sua seção e vê o resto; valores só para Financeiro, Gestor e Administrador. O veículo nasce na compra, pelo chassi; **a chave natural passa a ser o chassi** e a placa é opcional até o emplacamento.
**Consequência**: perfis `FINANCEIRO`, `FROTA` e `DOCUMENTACAO` na gestão; integrações que só conhecem placa ignoram veículo sem placa; "apto a operar" é calculado da ficha. O mesmo desenho vale para as próximas fichas (motorista).

### ADR-009 — O contrato operacional mora na gestão · **decidido em 15/10/2026**
**Decisão**: `contrato` e `linha` (SLA, reajuste, horários, veículo e motorista padrão) são tabelas da gestão, ao lado de veículo, escala e viagem. O contrato guarda a ligação com o `OmieContrato` (código da Omie) e com o cliente por CNPJ; a controladoria lê o contrato da gestão para faturamento e margem.
**Consequência**: a rota deixa de ser só texto em `Escala.routeName`; a escala do SIAT passa a casar com uma linha cadastrada.

### ADR-007 — Telemetria bruta separada de eventos de negócio
**Decisão**: posições da Ituran entram em `operacao.posicao` (particionada por mês, retenção 13 meses). Agentes derivam **eventos** (`operacao.evento_viagem`: início, fim, atraso, desvio) que são o que relatórios e SLA usam.

## Segurança e acesso

- Perfis: `admin`, `gestor`, `operacao`, `financeiro`, `rh`, `leitura`.
- Cada pendência tem perfil aprovador obrigatório (ex.: pagamento → `financeiro`).
- Segredos em `.env`; servidores MCP ligados a `127.0.0.1` por padrão.
- Toda escrita passa pelo helper de auditoria (`app/core/audit.py`).

## Ambientes

- `dev` (local), `prod` na Vercel com Postgres no Neon — o arranjo que a gestão e a controladoria já usam. Backups diários do Postgres com retenção 30 dias; teste de restauração mensal (isto também é um controle).
