# 03 — Backlog por fase

Ordem definida por valor ÷ esforço e por dependência de dados. Marcar `[x]` ao concluir. Cada item aponta a spec; os critérios de pronto detalhados estão lá.

## Fase 0 — Fundação (2–3 semanas) · `specs/01-cadastro-mestre.md`

> Revisada em 15/10/2026: boa parte desta fase já existe na gestão e na controladoria. Situação item a item em `docs/06-mapa-do-existente.md`.
>
> 16/10/2026: PR lezillig/gestao-motoristas#5 em produção (trilha, pendências, veículo com ficha por área — ADR-010 —, planilhas de controle e de financiamentos, cliente por CNPJ, contrato e linha).

- [x] Decidir stack definitiva (ADR-002): herdar Next.js + Prisma da gestão e da controladoria.
- [x] Banco, migrações e deploy: já existem (Neon, Prisma, Vercel).
- [x] Trilha de auditoria genérica (antes/depois por tabela) na gestão.
- [x] Fila única de pendências com perfil aprovador (quem cria ≠ quem aprova); multas e folha passam a gerar entradas nela.
- [x] `Vehicle` completo (renavam, chassi, categoria de uso, compra/venda, status `VENDIDO`); importar "CONTROLE INFORMAÇÕES GERAIS" (FROTA ATIVA + VENDIDOS); relatório de divergências com a Ituran como referência (ADR-008).
- [x] Financiamento por veículo, importado de "Consórcios e Financiamentos".
- [ ] Cliente e fornecedor por CNPJ (cliente feito em 16/10/2026; falta fornecedor e o casamento com o `OmieParceiro` na controladoria), ligando `Cliente` (gestão) ao `OmieParceiro` (controladoria).
- [x] Contrato operacional e linha na gestão (ADR-009): SLA, reajuste, horário, veículo e motorista padrão, ligados ao `OmieContrato` e às rotas do SIAT.
- [ ] Separar os bancos (ADR-001): executar `controladoria/docs/separar-bancos.md`, com papel somente leitura da controladoria no banco da gestão.
- [ ] Cadastro de pessoa além do motorista (monitor, mecânico, administrativo).
- [ ] Centro de custo por veículo e contrato, alinhado ao `CentroCusto` que a controladoria já mantém.
- [x] Clientes de Omie, Ituran e ponto (TiqueTaque): já existem em TypeScript. MCP em revisão (ADR-003).

**Pronto quando**: toda placa ativa da Ituran existe em `Vehicle`, e o que sobra no SIAT, Sofit ou planilha está listado como divergência; toda alteração de cadastro aparece na trilha com antes/depois; uma pendência pode ser criada, aprovada por outra pessoa e aparece na trilha.

## Fase 1 — Compliance e vencimentos (1 semana) · `specs/02-compliance-vencimentos.md`

- [x] Catálogo de antecedências do **veículo** (licenças 90d, apólice e tacógrafo 45d, vistoria escolar 30d) — `src/lib/vencimentos.ts` na gestão. CNH e documentos do motorista entram com a ficha do motorista.
- [x] Carga inicial dos documentos do veículo pela planilha CONTROLE INFORMAÇÕES GERAIS (Fase 0). Apólices Sombrero/ESSOR por PDF: pendente.
- [x] **Agente `vencimentos`** (diário, `/api/cron/vencimentos`, 06:30 em São Paulo) para o veículo: e-mail à Documentação nos degraus (antecedência do tipo, 60, 30, 7; um aviso por degrau) e pendência para a Documentação no vencimento (apólice = crítica). Falta: o motorista, e o aviso na escala de veículo com documento vencido.
- [~] Relatório "Documentos a vencer": `/cadastros/veiculos/vencimentos` (vencidos, a vencer em 90 dias, ativos sem apólice vigente, filtro por tipo). Falta o recorte por segmento.

## Fase 2 — Ponto e jornada (1–2 semanas) · `specs/03-ponto-jornada.md`

- [ ] Sincronização diária de marcações via MCP `ponto`.
- [ ] **Agente `ponto_erros`**: marcações inválidas/ausentes do dia anterior → e-mail ao gestor/motorista.
- [ ] Cálculo de `jornada_dia` com regras da Lei 13.103 (limite diário, intervalo, interjornada).
- [ ] **Agente `jornada_limites`**: excedentes → pendência para RH.
- [ ] Relatório: horas extras por motorista/mês, reincidência de erros.

## Fase 3 — Operação: rota planejada × realizada (2–3 semanas) · `specs/04-operacao-rotas.md`

- [ ] Ingestão de posições Ituran (a cada 5 min) → `operacao.posicao`.
- [ ] Geração de `viagem` planejada a partir de `linha` + `escala`.
- [ ] **Agente `monitor_rotas`**: início/fim de viagem, atraso > X min, desvio > Y m, veículo diferente do escalado, parada não prevista → `evento_viagem` + alerta em tempo quase real.
- [ ] Odômetro diário por veículo (para manutenção e custo/km).
- [ ] Relatório de pontualidade por linha/contrato (base do SLA).

## Fase 4 — Frota: manutenção, combustível, multas (2–3 semanas) · `specs/05-frota-manutencao.md`

- [ ] `plano_manutencao` por tipo de veículo; **agente `preventiva`** (km da Ituran × último serviço) → OS sugerida.
- [ ] Importação de abastecimentos (cartão/planilha); **agente `combustivel`**: consumo km/l por veículo e motorista, desvio > 15% da média → pendência.
- [x] Multas: cadastro e indicação de condutor já vinham da LW; **agente `multas_prazos`** (diário, `/api/cron/multas-prazos`): pendência para o gestor a 7/3/1 dias do prazo de indicação, fechada por quem envia a indicação. Falta: prazo de recurso (a LW não traz em coluna) e desconto em folha → RH.
- [ ] Pneus (fase 4b, opcional no início).

## Fase 5 — Financeiro e controladoria (3 semanas) · `specs/06-custos-controladoria.md`

- [ ] Sincronização diária Omie → `financeiro.lancamento` (com centro de custo).
- [ ] Views `custo_veiculo_mes` e `margem_contrato_mes`.
- [ ] Depreciação e financiamento alocados por veículo.
- [ ] **Agente `contas_pagar_inbox`** (contasapagar@): lê e-mail/NF, extrai dados, valida contra OS/abastecimento/contrato, propõe lançamento na Omie → pendência para financeiro.
- [ ] **Agente `conciliacao`** (semanal): Omie × extrato; combustível × km; horas × escala.
- [ ] Dashboard gerencial: custo/km, margem por contrato, DRE gerencial.
- [ ] Integrar simulador de custos: `comercial.proposta.composicao_custos` alimentada pelos custos reais.

## Fase 6 — Comercial e licitações (2 semanas) · `specs/07-comercial-licitacoes.md`

- [ ] **Agente `radar_pncp`**: busca diária por objeto/UF, grava em `comercial.licitacao`, alerta prazos de proposta e recurso.
- [ ] Reajustes contratuais: **agente `reajustes`** avisa 60 dias antes da data-base.
- [ ] Vigências: contratos a vencer em 180/90/30 dias.
- [ ] Pipeline comercial simples (status por licitação/proposta).

## Fase 7 — Auditoria e governança contínua · `specs/08-auditoria-governanca.md`

- [ ] **Agente `relatorio_semanal`**: resumo em texto + números para a diretoria (segunda-feira, 7h).
- [ ] Trilha de auditoria consultável (quem alterou o quê, por período).
- [ ] Segregação de funções nas pendências (quem cria ≠ quem aprova).
- [ ] Backups testados; rotina mensal de restauração.
- [ ] Revisão trimestral de regras dos agentes (thresholds) com base em falsos positivos.

## Depois (ideias registradas, sem compromisso)

- Videotelemetria / câmera com IA de fadiga e distração (ver `docs/05-benchmarking-segmentos.md`).
- App do motorista: checklist pré-viagem digital, jornada, ocorrências.
- Portal do cliente/escola: pontualidade, frequência de alunos, ocorrências.
- Calculadora de CO2 por contrato (veículo elétrico × combustão).
- Manutenção preditiva (probabilidade de falha por idade × histórico × uso).
