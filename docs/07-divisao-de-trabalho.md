# 07 — Divisão de trabalho entre as duas frentes

> 30/10/2026. Duas frentes passaram a escrever no mesmo código ao mesmo tempo:
>
> - **Frente Plano** — este repositório (`azul-gestao`): backlog por fase
>   (`docs/03`), agentes transversais, operação/rotas, controladoria, comercial
>   e governança.
> - **Frente Veículos** — `gestao-motoristas/docs/handoff-veiculos.md`: o
>   módulo de veículos do blueprint de frotas (3 ondas, substituir Sofit, LW e
>   as planilhas da frota).
>
> Este documento diz quem é dono de quê, o que cada frente lê da outra e o que
> ainda precisa de decisão. Antes de começar qualquer item, conferir aqui; se
> o item não estiver na tabela, combinar antes de escrever.

## Regra geral

1. **Um dono por assunto.** O dono decide o modelo de dados e a regra; a outra
   frente só lê (ou pede).
2. **Arquivos compartilhados** (`prisma/schema.prisma`, `vercel.json`,
   `src/lib/cronRun.ts`, `src/lib/pendencias/*`, `Sidebar.tsx`): trazer o
   `main` antes de cada PR e manter a mudança mínima. Migração nova sempre com
   timestamp do momento, nunca reaproveitando o de outra.
3. **Agente que já existe não ganha gêmeo.** Quem precisar mudar um agente da
   outra frente estende o agente (como a régua 90/60/30/15/7/0 estendeu o de
   vencimentos), não cria outro.
4. **ADR-001 vale para as duas:** gestão e controladoria em bancos separados;
   a controladoria lê a gestão só por `leitura.ts`; nenhuma escreve na outra.

## Quem é dono de quê

| Assunto | Dono | Onde | Observação |
|---|---|---|---|
| Cadastro do veículo (chassi, placa com histórico, status e transições, valores contábil/fiscal/FIPE, ciclo de vida) | **Veículos** | gestão | ADR-010 continua valendo |
| Documentos e licenças do veículo (régua, responsável, apto a operar, matriz por operação, anexos) | **Veículos** | gestão | agente `vencimentos` e os anexos nasceram na frente Plano; a evolução agora é da Veículos |
| Conciliação diária com a Ituran (frota × cadastro, `ituranId`, hodômetro) | **Veículos** | gestão | cron `conciliacao-ituran` |
| Odômetro oficial, km/dia, manutenção por km (planos por modelo, OS, checklist, VMRS) | **Veículos** | gestão | agentes `preventiva` e plano por tipo (`/manutencao/plano`) passam a ser da Veículos; o "odômetro diário" do backlog sai da frente Plano |
| Combustível (importação, desvio de consumo) | **Veículos** | gestão | agente `combustivel-desvio` passa a ser da Veículos (onda 2) |
| Multas (LW, prazos, tratativa, desconto em folha) | **Veículos** | gestão | agente `multas-prazos` passa a ser da Veículos |
| Estacionamentos, lavagens, pneus, sinistros, desmobilização | **Veículos** | gestão | |
| Financiamentos e consórcios (cadastro, importação, posição) | **Veículos** | gestão | a controladoria lê para o custo de propriedade |
| Motoristas: ponto, jornada, folga, horas extras, disponibilidade | **Plano** | gestão | `837059b` (EAR/toxicológico/curso na escala) foi da Veículos e fica como está |
| Escalas e SIAT, voucher | **Plano** | gestão | |
| Contrato operacional e linha, vigência e reajuste, importação da Omie | **Plano** | gestão + controladoria | |
| Telemetria de rota: trajeto (`TrajetoViagem`), desvios de rota e de ponto, pontualidade, paradas (Easy Course) | **Plano** | gestão | cron `ituran-trajetos` |
| Espelho da Omie, DRE, custos, rentabilidade por contrato, custo de propriedade por veículo, conciliação | **Plano** | controladoria | |
| Comercial: radar de licitações, simulador, pipeline | **Plano** | controladoria | |
| Governança: pendências, trilha, relatório semanal, backups, separação dos bancos | **Plano** | gestão + controladoria | pendências é infraestrutura comum: mudança combinada |

## O que cada frente lê da outra

- **Plano lê da Veículos:** `Vehicle` (placa, status, `valorContabilCents`,
  `vidaUtilMeses`, `valorResidualCents`, compra e venda), odômetro oficial
  (`odoTelemetriaKm + odoOffsetKm`), financiamentos. Uso: depreciação por
  veículo na controladoria, custo por km, impedimento na escala.
- **Veículos lê do Plano:** escalas e viagens (`Escala`, `VehicleTrip`,
  `TrajetoViagem`) para condutor da multa, utilização e km; contratos
  (`Contrato`) para a exigência de idade e documento por operação; pendências.

## Decisões em aberto (para o Leandro)

1. **"Integração Omie" e "TCO/margem por contrato" (onda 2 da Veículos).** A
   Omie já é espelhada na controladoria, e a margem por contrato e o custo de
   propriedade já existem lá (PR lezillig/controladoria#3). Proposta: a
   Veículos **não** integra a Omie na gestão (ADR-001); o TCO da ficha do
   veículo mostra o que a gestão mede (combustível, manutenção, multas,
   depreciação pelos valores do cadastro), e a margem por contrato fica na
   controladoria. O que a gestão precisar da Omie chega por arquivo exportado
   pela controladoria, como os contratos.
2. **Despesas com 3 chaves + XML NF-e (onda 2 da Veículos).** Cruza com o
   agente `contas_pagar_inbox` da Fase 5 do plano. Proposta: a leitura do
   XML e a chave veículo/contrato/categoria ficam na Veículos (é a OS e o
   abastecimento); o lançamento na Omie, quando houver, sai pela
   controladoria, atrás de pendência do financeiro.
3. **Depreciação.** A controladoria usa hoje a premissa geral do simulador (8
   anos, 20%). Com `vidaUtilMeses` e `valorResidualCents` no cadastro, passa a
   usar o valor do veículo quando preenchido (frente Plano, próximo PR).

## Itens do backlog que mudaram de dono

- Fase 3 "Odômetro diário por veículo" → Veículos (km/dia do handoff).
- Fase 4 inteira (manutenção, combustível, multas, pneus) → Veículos.
- Fase 1 "Documentos a vencer" → Veículos (régua e matriz por operação).
