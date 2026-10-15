# 06 — Mapa do que já existe (Fase 0)

Levantamento feito em 15/10/2026, lendo o código de produção dos dois
sistemas em uso. Serve para a Fase 0 **completar** o que falta em vez de
reconstruir o que já roda. Atualizar este arquivo quando uma lacuna fechar.

## Os dois sistemas

| | `lezillig/gestao-motoristas` (a "gestão") | `lezillig/controladoria` |
|---|---|---|
| Papel | Operação: cadastro, escala, ponto, frota, multas, folha | Financeiro: espelho da Omie, auditoria, DRE, simulador de custos |
| Stack | Next.js 16 + Prisma 6 + Tailwind v4 | Next.js 16 + Prisma 6 + Tailwind v4 |
| Banco | Neon, schema `public` (33 modelos) | Neon, mesmo banco, schema `controladoria`; lê `public` só por `src/lib/gestao/leitura.ts` |
| Deploy | Vercel, `prisma migrate deploy` no build | Vercel, idem |
| Login | `User` + `Role` (ADMIN, GESTOR, FOLHA, MOTORISTA) | Usa o login da gestão; perfis próprios em `PerfilAcesso`/`UsuarioPerfil` |
| Agendamento | 12 crons da Vercel (`vercel.json`), registro em `CronExecucao` | 1 cron da Vercel + GitHub Actions como condutor do ciclo |

Convenções reais que diferem dos docs 01–04 (os docs passam a seguir o código):
- Modelos em inglês na gestão (`Vehicle`, `Driver`) e em português na
  controladoria; ids `cuid()` em texto, não `bigserial`.
- Dinheiro em **centavos inteiros** (`valorCents`, `*Cents`), não `numeric(14,2)`.
- Multiempresa por `companyId` em toda tabela.

## Integrações que já existem

| Sistema | Para quê | Onde |
|---|---|---|
| **TiqueTaque** | Ponto: funcionários, marcações, espelho mensal, afastamentos | gestão, `src/lib/tiquetaque/` |
| **SIAT** | Despacho: escalas, rotas, cadastro de veículo e motorista | gestão, `src/lib/sync/siat.ts` |
| **Ituran** | Viagens e telemetria por veículo | gestão, `src/lib/ituran/`, `src/lib/telemetry/` |
| **Sofit** | Manutenção: OS, vencimentos de veículo, odômetro, CNH, afastamento | gestão, `src/lib/sofit/` |
| **Ticket Log** | Cartão combustível: transações e situação do cartão | gestão, `src/lib/ticketlog/`, `src/lib/sync/ticketlogCards.ts` |
| **LW Tecnologia** | Multas e indicação de condutor | gestão, `src/lib/lw/` |
| **Prodesp (DETRAN-SP)** | Situação oficial da CNH | gestão, `src/lib/prodesp/` |
| **ANP** | Preço de referência do combustível | gestão, `src/lib/anp/` |
| **Omie** (2 empresas) | Títulos, baixas, movimentos, notas, contratos, CT-e, parceiros | controladoria, `src/lib/omie/` |
| **BrasilAPI** | Cadastro de CNPJ na Receita | controladoria, `src/lib/receita/` |

O "sistema de ponto" do `CLAUDE.md` é o **TiqueTaque**.

## Fase 0 item por item

Legenda: ✅ existe · 🟡 existe em parte · ❌ falta

| Item da Fase 0 (`docs/03`) | Situação | Onde está / o que falta |
|---|---|---|
| Decidir stack (ADR-002) | ✅ | Decidido em 15/10/2026: herdar Next.js + Prisma. Ver ADR-002. |
| Schema, migrações, `app/core` | ✅ | Migrações Prisma escritas à mão nos dois repositórios. Não há Alembic nem FastAPI. |
| `auditoria.log` genérico | ❌ | Há trilhas pontuais: `TimeClockCorrection` (antes/depois do ponto), `FechamentoEvento` (folha), `ControladoriaEventLog`. Não há log de antes/depois para todo cadastro. |
| `cadastro.veiculo` | 🟡 | `Vehicle` com `plate` única e normalizada sem hífen (`src/lib/plate.ts`, já trata Mercosul × antiga). **Faltam** renavam, chassi, ano do modelo, categoria de uso (fretamento/escolar/cargas), compra e venda (data, valor, fornecedor). `VehicleStatus` não tem `VENDIDO` (só ATIVO, MANUTENCAO, INATIVO). |
| Divergência planilha × Ituran | 🟡 | O cliente da Ituran já lista veículos e corrige placas erradas (`plateAliases.ts`). Falta o importador da planilha "CONTROLE INFORMAÇÕES GERAIS" e o relatório de divergências. |
| `frota.financiamento` | 🟡 | Controladoria tem financiamentos no `BalancoPatrimonial`, sem vínculo por veículo. Falta o importador de "Consórcios e Financiamentos" por placa. |
| `cadastro.pessoa` | 🟡 | `Driver` com `cpf` único e validado (`src/lib/cpf.ts`), alimentado pelo TiqueTaque, SIAT e Sofit. Só cobre motoristas: **monitor, mecânico e administrativo não têm cadastro**. |
| `cadastro.cliente` | 🟡 | `Cliente` na gestão é chaveado por **nome**, sem CNPJ. Os clientes com CNPJ estão em `OmieParceiro` na controladoria. Falta casar os dois pelo CNPJ. |
| `cadastro.fornecedor` | 🟡 | Só como `OmieParceiro` (controladoria). Não há cadastro na gestão. |
| `cadastro.contrato` | 🟡 | `OmieContrato` (controladoria) espelha o contrato de venda da Omie. **Não há contrato operacional** com SLA, linhas e reajuste. |
| `cadastro.linha` / `ponto_parada` | ❌ | A rota existe só como texto em `Escala.routeName` e `Escala.clientName`, vindos do SIAT. |
| `centro_custo` | 🟡 | `CentroCusto` + `CentroCustoVinculo` + `OmieVinculoCentroCusto` na controladoria, já com `vehicleId`, `clienteId` e `driverId` apontando para a gestão. O padrão é por departamento/projeto da Omie, não `V-<placa>` e `C-<contrato>`. |
| MCP `omie` | 🟡 | Cliente Omie em TypeScript na controladoria. Não é servidor MCP. |
| MCP `ituran` | 🟡 | Cliente Ituran em TypeScript na gestão. Não é servidor MCP. |
| MCP `ponto` | 🟡 | Cliente TiqueTaque em TypeScript na gestão. Não é servidor MCP. |
| Fila de pendências | 🟡 | Fluxos de aprovação isolados: `IndicacaoCondutor` (SUGERIDA → confirmação humana → ENVIADA), `FechamentoFolha` (aprovação com hash do dossiê), `AuditFinding` com tratativa. **Falta a fila única** com perfil aprovador. |
| `agents/base` | 🟡 | `CronExecucao` faz o papel de `execucao_agente`. Os agentes da controladoria (`src/lib/controladoria/agents/`) já seguem coletar → regras → achado com chave determinística. Falta o passo "agir → pendência". |

## Lacunas que a Fase 0 precisa fechar

Em ordem de dependência:

1. **Trilha de auditoria genérica** (antes/depois por tabela) na gestão. Vem
   primeiro porque todo o resto grava dados.
2. **Fila única de pendências**, com perfil aprovador e regra de quem cria ≠
   quem aprova. Os fluxos de multa e folha passam a gerar entradas nela.
3. **Veículo completo**: campos de compra/venda e documento, status
   `VENDIDO`, importador da planilha e relatório de divergências contra a
   Ituran e o SIAT.
4. **Financiamento por veículo**, importado da planilha.
5. **Cliente e fornecedor por CNPJ**, ligando `Cliente` ao `OmieParceiro`.
6. **Contrato operacional e linha**: SLA, reajuste, linhas com horário e
   veículo/motorista padrão, ligados ao `OmieContrato` e às rotas do SIAT.
7. **Pessoa além do motorista** (monitor, mecânico, administrativo).
8. **Centro de custo**: decidir se o padrão `V-<placa>` / `C-<contrato>` do
   `docs/02` substitui ou complementa o vínculo por departamento da Omie.

## Decisões em aberto

- **Banco**: um só com papéis separados (ADR-001) ou dois, como planeja
  `controladoria/docs/separar-bancos.md`.
- **Fonte oficial da frota**: o `CLAUDE.md` diz Ituran; o código da gestão
  trata o **SIAT** como cadastro correto e corrige a Ituran contra ele.
- **MCP (ADR-003)**: os clientes TypeScript já encapsulam autenticação e
  paginação. MCP passa a ser só para uso do Claude em conversa?
- **Onde mora o contrato operacional**: gestão (operação) ou controladoria
  (já tem `OmieContrato`)?
- **Situação de `gestao-embarques` e `gestao-multas`**: as multas parecem
  absorvidas pela gestão (integração LW).
