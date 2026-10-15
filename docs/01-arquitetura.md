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

### ADR-001 — Um banco, vários schemas (não um banco por módulo)
**Contexto**: módulos atuais têm bancos separados; preocupação com performance ao unificar.
**Decisão**: um PostgreSQL com schema por domínio. Para ~200 veículos, ~300 pessoas e dezenas de contratos, o volume é pequeno (milhões de linhas só em telemetria, e essa fica em tabela própria particionada por mês). O custo real de bancos separados é não conseguir cruzar frota × pessoas × financeiro, que é exatamente o que gera gestão.
**Consequência**: módulos novos nascem no banco único; módulos existentes migram na Fase 0 (ou ficam como fonte externa via MCP até migrarem).
**Em revisão (15/10/2026)**: a controladoria tem um plano para ir a um banco próprio (`controladoria/docs/separar-bancos.md`), motivado pela credencial de um sistema alcançar o schema do outro. Alternativa que mantém este ADR: um banco, um papel Postgres por sistema, escrita só no próprio schema e leitura concedida tabela a tabela. Decisão pendente.

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

### ADR-007 — Telemetria bruta separada de eventos de negócio
**Decisão**: posições da Ituran entram em `operacao.posicao` (particionada por mês, retenção 13 meses). Agentes derivam **eventos** (`operacao.evento_viagem`: início, fim, atraso, desvio) que são o que relatórios e SLA usam.

## Segurança e acesso

- Perfis: `admin`, `gestor`, `operacao`, `financeiro`, `rh`, `leitura`.
- Cada pendência tem perfil aprovador obrigatório (ex.: pagamento → `financeiro`).
- Segredos em `.env`; servidores MCP ligados a `127.0.0.1` por padrão.
- Toda escrita passa pelo helper de auditoria (`app/core/audit.py`).

## Ambientes

- `dev` (local), `prod` na Vercel com Postgres no Neon — o arranjo que a gestão e a controladoria já usam. Backups diários do Postgres com retenção 30 dias; teste de restauração mensal (isto também é um controle).
