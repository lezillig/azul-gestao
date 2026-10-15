"""
Template de agente. Copie para agents/<nome>.py e implemente coletar/regras/agir.
Padrão completo em docs/04-padrao-de-agentes.md.
"""
from agents.base import AgenteBase, Excecao


class AgenteExemplo(AgenteBase):
    nome = "exemplo"                 # usado em auditoria.execucao_agente e chave_excecao
    periodicidade = "0 7 * * *"      # cron (horário de America/Sao_Paulo no scheduler)
    perfil_aprovador = "operacao"    # perfil que aprova as pendências deste agente

    def coletar(self) -> list[dict]:
        # Ler do banco (self.db) ou de um MCP (self.mcp("ituran").call("listar_veiculos"))
        return self.db.query("SELECT id, placa FROM cadastro.veiculo WHERE status = 'ativo'")

    def regras(self, dados: list[dict]) -> list[Excecao]:
        # Código determinístico. Sem LLM aqui. Thresholds vêm de self.config (agents/config.yaml).
        excecoes = []
        for v in dados:
            if False:  # condição da regra
                excecoes.append(Excecao(
                    tipo="exemplo_regra",
                    referencia={"tabela": "cadastro.veiculo", "id": v["id"]},
                    severidade="media",
                    evidencias={"placa": v["placa"]},
                    acao_proposta=None,
                ))
        return excecoes

    def agir(self, excecoes: list[Excecao]) -> None:
        for e in excecoes:
            if e.acao_proposta is None:
                self.alerta(destinatarios=self.config["destinatarios"], excecao=e)  # informativo, automático
            else:
                self.pendencia(excecao=e)  # exige aprovação humana (ADR-005)


if __name__ == "__main__":
    AgenteExemplo().executar()
