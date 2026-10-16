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
| `auditoria.log` genérico | 🟡 | **Implementado em 15/10/2026 no PR lezillig/gestao-motoristas#5, aguardando merge.** Gatilho no Postgres grava antes/depois em `RegistroAuditoria` (somente-inclusão) para veículo, motorista, cliente, sindicato, usuário, empresa e convenção; telas informam o autor por `comAutor`; consulta em `/auditoria`. Falta: os syncs (SIAT, Sofit, Prodesp, TiqueTaque) se identificarem com `autorDeProcesso`, e estender o gatilho às tabelas novas da Fase 0. |
| `cadastro.veiculo` | 🟡 | `Vehicle` com `plate` única e normalizada sem hífen (`src/lib/plate.ts`, já trata Mercosul × antiga). **Campos patrimoniais (renavam, chassi, ano do modelo, categoria de uso, compra e venda) implementados em 15/10/2026 no PR lezillig/gestao-motoristas#5, aguardando merge.** Vendido = `INATIVO` + `dataVenda` (sem status `VENDIDO`, que furaria os filtros de escala). Falta: fornecedor da compra (depende do cadastro de fornecedor por CNPJ). |
| Divergência planilha × Ituran | 🟡 | **Relatório Ituran × cadastro × cartões Ticket Log e importador da planilha "CONTROLE INFORMAÇÕES GERAIS" implementados no PR lezillig/gestao-motoristas#5, aguardando merge.** O importador só preenche campo vazio, não repete renavam/chassi, e manda baixa de veículo ativo para a fila de pendências. Conferido com a planilha de agosto/2026 (215 ativos, 86 vendidos). Falta: rodar em produção com a planilha atualizada e resolver os achados dela (ver abaixo). |
| `frota.financiamento` | 🟡 | **`Financiamento` (contrato de CDC ou cota de consórcio) e `FinanciamentoVeiculo` (rateio por placa) com importador da planilha "Consórcios e Financiamentos" implementados em 16/10/2026 no PR lezillig/gestao-motoristas#5, aguardando merge.** Conferido com a posição de 31/08/2026: 496 contratos e cotas (284 em aberto, R$ 955.890,08/mês de parcela, R$ 22,55 mi de saldo), 8 de 12 bancos batendo com o Controle Geral. Falta: a controladoria ler por `leitura.ts` (hoje tem financiamentos só no `BalancoPatrimonial`) e o capital de giro, que não é por veículo. |
| `cadastro.pessoa` | 🟡 | `Driver` com `cpf` único e validado (`src/lib/cpf.ts`), alimentado pelo TiqueTaque, SIAT e Sofit. Só cobre motoristas: **monitor, mecânico e administrativo não têm cadastro**. |
| `cadastro.cliente` | 🟡 | **CNPJ (com validação do formato alfanumérico de jul/2026), razão social e tipo privado/público implementados no PR lezillig/gestao-motoristas#5, aguardando merge.** Falta: a controladoria casar `Cliente` com `OmieParceiro` pelo CNPJ (em `leitura.ts`) e preencher o CNPJ dos clientes existentes. |
| `cadastro.fornecedor` | 🟡 | Só como `OmieParceiro` (controladoria). Não há cadastro na gestão. |
| `cadastro.contrato` | 🟡 | `OmieContrato` (controladoria) espelha o contrato de venda da Omie. **Contrato operacional (`Contrato`: número, cliente, tipo, vigência, valor mensal, índice e data-base de reajuste, SLA de pontualidade, código na Omie) implementado em 16/10/2026 no PR lezillig/gestao-motoristas#5, aguardando merge**, com tela de situação (a vencer em 60 dias, vencido com status vigente) e próximo reajuste. Falta: cadastrar os contratos ativos e a controladoria ler `Contrato` em `leitura.ts`, casando com `OmieContrato` pelo código. |
| `cadastro.linha` / `ponto_parada` | 🟡 | **`Linha` (código, horário, km, veículo e motorista padrão, rota no SIAT e na Ituran) implementada no PR lezillig/gestao-motoristas#5, aguardando merge.** A escala do SIAT casa com a linha pela rota (chave sem acento e maiúsculas); a tela `/cadastros/contratos/rotas-siat` lista o que roda sem linha. Falta: `Escala.linhaId` (entra com a geração de viagens, Fase 3) e `ponto_parada`. |
| `centro_custo` | 🟡 | `CentroCusto` + `CentroCustoVinculo` + `OmieVinculoCentroCusto` na controladoria, já com `vehicleId`, `clienteId` e `driverId` apontando para a gestão. O padrão é por departamento/projeto da Omie, não `V-<placa>` e `C-<contrato>`. |
| MCP `omie` | 🟡 | Cliente Omie em TypeScript na controladoria. Não é servidor MCP. |
| MCP `ituran` | 🟡 | Cliente Ituran em TypeScript na gestão. Não é servidor MCP. |
| MCP `ponto` | 🟡 | Cliente TiqueTaque em TypeScript na gestão. Não é servidor MCP. |
| Fila de pendências | 🟡 | **Implementada em 15/10/2026 no PR lezillig/gestao-motoristas#5, aguardando merge.** `Pendencia` + `src/lib/pendencias` (idempotência por chave, quem cria ≠ quem aprova, motivo obrigatório, prazo por severidade com escalada ao GESTOR, executor por tipo fora da transação) e tela `/pendencias`. Falta: `IndicacaoCondutor` e `FechamentoFolha` passarem a gerar pendências. |
| `agents/base` | 🟡 | `CronExecucao` faz o papel de `execucao_agente`. Os agentes da controladoria (`src/lib/controladoria/agents/`) já seguem coletar → regras → achado com chave determinística. Falta o passo "agir → pendência". |

## Lacunas que a Fase 0 precisa fechar

Em ordem de dependência:

1. **Trilha de auditoria genérica** (antes/depois por tabela) na gestão. Vem
   primeiro porque todo o resto grava dados.
2. **Fila única de pendências**, com perfil aprovador e regra de quem cria ≠
   quem aprova. Os fluxos de multa e folha passam a gerar entradas nela.
3. **Veículo completo**: campos de compra/venda e documento, status
   `VENDIDO`, importador da planilha e relatório de divergências com a
   Ituran como referência (ADR-008).
4. **Financiamento por veículo**, importado da planilha.
5. **Cliente e fornecedor por CNPJ**, ligando `Cliente` ao `OmieParceiro`.
6. **Contrato operacional e linha**, na gestão (ADR-009): SLA, reajuste,
   linhas com horário e veículo/motorista padrão, ligados ao `OmieContrato`
   e às rotas do SIAT, e expostos à controladoria em `leitura.ts`.
7. **Pessoa além do motorista** (monitor, mecânico, administrativo).
8. **Centro de custo**: decidir se o padrão `V-<placa>` / `C-<contrato>` do
   `docs/02` substitui ou complementa o vínculo por departamento da Omie.

## Achados da planilha de controle (agosto/2026)

Da primeira leitura de "CONTROLE INFORMAÇÕES GERAIS" pelo importador:

- **Renavam e chassi repetidos em duas placas**: GAM3671 (FROTA ATIVA, contrato
  "CARRO A VENDA") e BAM2H50 (VENDIDOS, vendido em 19/02/2026) têm o mesmo
  renavam 01167718736 e o mesmo chassi. É o mesmo veículo físico; uma das
  linhas está errada ou houve troca de placa.
- **EEJ1210** está ao mesmo tempo na FROTA ATIVA e em VENDIDOS.
- **EZO1110** aparece duas vezes em VENDIDOS.
- **4 chassis com 16 caracteres** (falta um): EEJ1210, FMU4J83, FQX0H73
  (FROTA ATIVA) e GKH2607 (VENDIDOS).
- **29 vendas sem data** e 64 sem valor na aba VENDIDOS.
- **18 veículos com categoria "UNIDADE MÓVEL"**, que não é fretamento,
  escolar nem cargas: decidir se vira categoria própria.
- Todos os 215 renavams da FROTA ATIVA passaram na verificação do dígito.

### Planilha atualizada (outubro/2026), comparada com a de agosto

- **Corrigido**: os 3 chassis curtos da FROTA ATIVA (EEJ1210, FMU4J83,
  FQX0H73) e as 29 vendas sem data em VENDIDOS.
- **Entraram** na FROTA ATIVA: UPK0G59 e UQQ5E77.
- **Novo problema — renavam repetido**: GBT9I12 passou a ter o renavam
  01350943948, que é o da FJO0F81 (em agosto era 01349893193). As duas são
  Ford Transit da mesma compra, com notas fiscais seguidas; parece cópia de
  linha. O importador não grava o renavam repetido.
- **Novo problema**: EFV4194 está na FROTA ATIVA e também em VENDIDOS, e o
  chassi difere em um dígito entre as duas abas (…E2133335 × …E2123335).
- **Linha sem placa** (FROTA ATIVA, linha 217): Sprinter comprada em
  24/06/2026, ainda sem placa na planilha; ignorada até ter placa.
- **Continuam**: GAM3671 × BAM2H50 com o mesmo renavam e chassi; EEJ1210
  ativa e vendida; EZO1110 duas vezes em VENDIDOS; chassi curto de GKH2607;
  18 "UNIDADE MÓVEL" sem categoria.

## Decisões tomadas em 15/10/2026

- **Stack**: herdar Next.js + Prisma (ADR-002).
- **Banco**: dois bancos, um por sistema; a controladoria lê a gestão em
  somente leitura (ADR-001 revisto). Executar
  `controladoria/docs/separar-bancos.md` deixa de ser opcional.
- **Fonte oficial da frota**: Ituran (ADR-008). O relatório de divergências
  usa a Ituran como referência; SIAT, Sofit, Ticket Log e planilha são
  comparados contra ela.
- **Contrato operacional**: na gestão, ligado ao `OmieContrato` (ADR-009).

## Decisões em aberto

- **MCP (ADR-003)**: os clientes TypeScript já encapsulam autenticação e
  paginação. MCP passa a ser só para uso do Claude em conversa?
- **Centro de custo**: o padrão `V-<placa>` / `C-<contrato>` substitui ou
  complementa o vínculo por departamento da Omie que a controladoria usa?
- **Situação de `gestao-embarques` e `gestao-multas`**: as multas parecem
  absorvidas pela gestão (integração LW).

## Achados da planilha "Consórcios e Financiamentos" (posição de 31/08/2026)

Encontrados na primeira importação; nenhum deles é corrigido pelo sistema.

- **O resumo (Controle Geral) não bate com as abas em 4 casos**: CDC Moneo
  (10 contratos em aberto na aba contra 8 no resumo — os dois a mais,
  745090 e 745081, têm data final em 17/11/2025 e ainda 4 parcelas);
  consórcio Banco do Brasil (14 contra 11: um segundo bloco de 3 cotas sem
  título); consórcio Bradesco (15 contra 13); consórcio Mercabenco (parcela
  de R$ 9.714,03 na aba contra R$ 12.286,08 no resumo).
- **Tabelas dinâmicas desatualizadas** no meio das abas (no Bradesco, R$
  197.036,40 de saldo por placa contra R$ 188.977,24 nas linhas). O
  importador não lê nenhuma.
- **Rateio que não fecha** em dois CDC Moneo (848239 e 855120): o saldo por
  placa soma mais que o saldo do contrato — a placa de garantia (EXV1773,
  em três contratos) entra com a mesma parte das outras.
- **15 cotas contempladas com o bem sem placa** (9 na CNP, 6 no Santander) e
  **3 CDC sem placa** (os 2 da RCI, de agosto, e um Stellantis com a placa
  `V44EAAB`, fora do formato).
- **Chassi digitado errado**: GHV1G72 aparece na CNP com
  `9V8VBYHERA001475` (falta um V).
- O título "QUITADOS" da CNP diz **"solicitar crédito 60 dias após a
  quitação da cota"** e o do Itaú, **"gravame - baixa automática"**: duas
  rotinas que hoje dependem de alguém lembrar.

## Cadastro único do veículo por área (16/10/2026)

Implementado no PR lezillig/gestao-motoristas#5 (ADR-010), aguardando merge.
Primeira leitura com a planilha de controle real (222 veículos ativos): **152
aptos a operar**; o que mais falta, por área:

- Documentação: 48 tacógrafos "preliminar", 42 sem tipo de operação (as 19
  UNIDADE MÓVEL e as linhas com "-"), 19 sem apólice, 6 EMTU vencidas, 4 CVS
  vencidos, 3 vistorias semestrais e 3 ATE vencidas.
- Financeiro: 38 sem nota fiscal de compra, 22 sem data de compra.
- Frota: 5 sem lugares, 3 sem renavam.

Em aberto: o que "LETRA G / R / E / A" da coluna ADAPTAÇÃO significa (está
guardado como texto, na Documentação) e a venda como checklist por área.

