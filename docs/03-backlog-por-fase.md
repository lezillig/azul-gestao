# 03 — Backlog por fase

Ordem definida por valor ÷ esforço e por dependência de dados. Marcar `[x]` ao concluir. Cada item aponta a spec; os critérios de pronto detalhados estão lá.

## Fase 0 — Fundação (2–3 semanas) · `specs/01-cadastro-mestre.md`

> Revisada em 15/10/2026: boa parte desta fase já existe na gestão e na controladoria. Situação item a item em `docs/06-mapa-do-existente.md`.
>
> 16/10/2026: PR lezillig/gestao-motoristas#5 em produção (trilha, pendências, veículo com ficha por área — ADR-010 —, planilhas de controle e de financiamentos, cliente por CNPJ, contrato e linha).
> 17/10/2026: PR lezillig/gestao-motoristas#6 em produção (baixa da venda por área; agentes de vencimentos, escala com veículo impedido, prazos de multa, ponto/jornada, desvio de combustível e preventiva; horas extras e pontualidade por cliente). Primeira rodada dos agentes: 18/10, entre 06:15 e 06:55.
> 21/10/2026: PR lezillig/gestao-motoristas#9 em produção (agentes de vigência e reajuste de contratos).
> 23/10/2026: PRs lezillig/gestao-motoristas#10 e lezillig/controladoria#1 em produção (contratos da Omie: a controladoria exporta o CSV, a gestão importa em Cadastros › Contratos › Importar da Omie).
> 24/10/2026: PR lezillig/gestao-motoristas#11 em produção (diagnóstico do histórico de posições da Ituran em /telemetria/ituran-historico; aguarda o resultado para a Fase 3).
> 24/10/2026: PR lezillig/gestao-motoristas#12 em produção (trajeto ponto a ponto da Ituran; desvio de rota aprendido por rota do SIAT; batida do TiqueTaque longe do veículo escalado).
> 29/10/2026: PR lezillig/gestao-motoristas#13 em produção (veículo trocado sem atualizar a escala; parada fora da rota). PR lezillig/controladoria#2 aberto (radar de licitações do PNCP).
> 18/10/2026: PR lezillig/gestao-motoristas#8 em produção (folga semanal no agente de jornada; vencimentos por segmento).
> 17/10/2026: PR lezillig/gestao-motoristas#7 em produção (preventiva com a conta da tela de Manutenção; plano por tipo de veículo para freios, pneus e correia).

- [x] Decidir stack definitiva (ADR-002): herdar Next.js + Prisma da gestão e da controladoria.
- [x] Banco, migrações e deploy: já existem (Neon, Prisma, Vercel).
- [x] Trilha de auditoria genérica (antes/depois por tabela) na gestão.
- [x] Fila única de pendências com perfil aprovador (quem cria ≠ quem aprova); multas e folha passam a gerar entradas nela.
- [x] `Vehicle` completo (renavam, chassi, categoria de uso, compra/venda, status `VENDIDO`); importar "CONTROLE INFORMAÇÕES GERAIS" (FROTA ATIVA + VENDIDOS); relatório de divergências com a Ituran como referência (ADR-008).
- [x] Financiamento por veículo, importado de "Consórcios e Financiamentos".
- [ ] Cliente e fornecedor por CNPJ (cliente feito em 16/10/2026; falta fornecedor e o casamento com o `OmieParceiro` na controladoria), ligando `Cliente` (gestão) ao `OmieParceiro` (controladoria).
- [x] Contrato operacional e linha na gestão (ADR-009): SLA, reajuste, horário, veículo e motorista padrão, ligados ao `OmieContrato` e às rotas do SIAT.
- [x] Carga dos contratos a partir da Omie: CSV exportado pela controladoria e importado na gestão (simular → aplicar), sem escrita entre bancos (ADR-001).
- [ ] Separar os bancos (ADR-001): executar `controladoria/docs/separar-bancos.md`, com papel somente leitura da controladoria no banco da gestão.
- [ ] Cadastro de pessoa além do motorista (monitor, mecânico, administrativo).
- [ ] Centro de custo por veículo e contrato, alinhado ao `CentroCusto` que a controladoria já mantém.
- [x] Clientes de Omie, Ituran e ponto (TiqueTaque): já existem em TypeScript. MCP em revisão (ADR-003).

**Pronto quando**: toda placa ativa da Ituran existe em `Vehicle`, e o que sobra no SIAT, Sofit ou planilha está listado como divergência; toda alteração de cadastro aparece na trilha com antes/depois; uma pendência pode ser criada, aprovada por outra pessoa e aparece na trilha.

## Fase 1 — Compliance e vencimentos (1 semana) · `specs/02-compliance-vencimentos.md`

- [x] Catálogo de antecedências do **veículo** (licenças 90d, apólice e tacógrafo 45d, vistoria escolar 30d) — `src/lib/vencimentos.ts` na gestão. CNH e documentos do motorista entram com a ficha do motorista.
- [x] Carga inicial dos documentos do veículo pela planilha CONTROLE INFORMAÇÕES GERAIS (Fase 0). Apólices Sombrero/ESSOR por PDF: pendente.
- [x] **Agente `vencimentos`** (diário, `/api/cron/vencimentos`, 06:30 em São Paulo) para o veículo: e-mail à Documentação nos degraus (antecedência do tipo, 60, 30, 7; um aviso por degrau) e pendência para a Documentação no vencimento (apólice = crítica). Escala de veículo com documento vencido: justificativa escrita no formulário e pendência para o gestor nas escalas do SIAT (hoje e amanhã). Falta: os documentos do motorista (CNH já bloqueia a escala desde antes).
- [~] Relatório "Documentos a vencer": `/cadastros/veiculos/vencimentos` (vencidos, a vencer em 90 dias, ativos sem apólice vigente, filtro por tipo). Recorte por segmento (tipo de operação da ficha): PR lezillig/gestao-motoristas#8.

## Fase 2 — Ponto e jornada (1–2 semanas) · `specs/03-ponto-jornada.md`

- [x] Sincronização diária de marcações: cliente TiqueTaque da gestão (cron `tiquetaque-import`), não MCP.
- [x] **Agente `ponto_erros`** (`/api/cron/jornada`, 06:40): escalado sem batida, turno sem saída, batidas que não fecham → e-mail ao gestor; 3 dias com erro em 30 → pendência para a Folha. Falta: aviso ao próprio motorista (WhatsApp exige template novo aprovado na Meta).
- [x] Cálculo da jornada com a Lei 13.103 e a convenção: já existia em `src/lib/pontoCompliance.ts` e `convencao.ts` (relatório `/ponto/analise`); o agente reaproveita dia a dia.
- [x] **Agente `jornada_limites`**: hora extra acima de 2h, sem intervalo, interjornada → pendência para a Folha (perfil FOLHA), alta se repete na semana. Descanso semanal no agente diário: PR lezillig/gestao-motoristas#8. Falta: cruzamento com ignição Ituran.
- [x] Relatório: horas extras por motorista/mês (`/ponto/mensal`, já existia) e por cliente (`/ponto/mensal/clientes`, pela escala do dia, com custo da convenção); reincidência de erros vira pendência. Falta: taxa de erro de marcação por equipe.

## Fase 3 — Operação: rota planejada × realizada (2–3 semanas) · `specs/04-operacao-rotas.md`

- [~] Posições Ituran: trajeto ponto a ponto de cada viagem (`GET /api/v2/trips/{id}/points`) em `TrajetoViagem`, buscado diariamente pelo cron `ituran-trajetos` (PR lezillig/gestao-motoristas#12). Falta: tempo quase real (hoje D-1).
- [ ] Geração de `viagem` planejada a partir de `linha` + `escala`.
- [~] **Agente `monitor_rotas`** (D-1 em `/telemetria/desvios`: desvio de rota, veículo trocado, parada fora da rota; falta tempo quase real e virar pendência): início/fim de viagem, atraso > X min, desvio > Y m, veículo diferente do escalado, parada não prevista → `evento_viagem` + alerta em tempo quase real.
- [ ] Odômetro diário por veículo (para manutenção e custo/km).
- [~] Relatório de pontualidade por cliente (`/telemetria/pontualidade`): saída da viagem da Ituran × horário de saída da escala, tolerância 10 min. Falta: chegada no ponto, que pede `ponto_parada` (paradas do Easy Course — aguardando acesso ou exportação).
- [x] Desvio de rota sem cadastro: caminho habitual aprendido por rota e cliente do SIAT (30 dias, mínimo 5 viagens), trecho fora com ≥ 1 km ou 5 min (`/telemetria/desvios`, PR lezillig/gestao-motoristas#12). Falta: calibrar com casos reais e virar pendência.
- [x] Batida de ponto (TiqueTaque, local do app) longe do veículo escalado naquele horário, ≥ 1 km (`/telemetria/desvios`).

## Fase 4 — Frota: manutenção, combustível, multas (2–3 semanas) · `specs/05-frota-manutencao.md`

- [x] **Agente `preventiva`** (`/api/cron/preventiva`): km da Ituran/Sofit × última revisão da Sofit, contra o intervalo do veículo → pendência para a Frota abrir a OS (pula quem já tem OS de revisão aberta). Usa a mesma conta da tela `/manutencao` (km ou dias contra o plano da Sofit). `plano_manutencao` por tipo de veículo para freios, pneus e correia em `/manutencao/plano` (PR lezillig/gestao-motoristas#7): intervalo da Frota, última troca pelas OS da Sofit. Tacógrafo e extintor já vêm como vencimento da Sofit e da planilha.
- [x] Importação de abastecimentos (Sofit, Ticket Log e extrato — já existia); **agente `combustivel`** (`/api/cron/combustivel-desvio`): km/l de 30 dias contra a mediana do mesmo modelo e combustível, desvio > 15% → pendência para a Frota, com litros por motorista. Falta: ranking por motorista (hoje vai na evidência).
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
- [x] Reajustes contratuais: **agente `reajustes`** (`/api/cron/contratos`) abre pendência para o Financeiro 60 dias antes da data-base (PR lezillig/gestao-motoristas#9).
- [x] Vigências: contratos a vencer em 180/90/30 dias, ou vigentes com o fim passado → pendência para o gestor (PR lezillig/gestao-motoristas#9).
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
