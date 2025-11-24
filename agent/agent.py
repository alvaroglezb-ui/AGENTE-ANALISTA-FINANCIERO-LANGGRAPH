import argparse
import json
import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from scrapers.rss_scraper import Article, RSSScraper


class AgentState(TypedDict, total=False):
    articles: List[Article]
    summary: str
    insights: str
    email_body: str


@dataclass
class Settings:
    rss_urls: Dict[str, str]
    limit: int
    language: str
    model: str
    temperature: float
    email_sender: str
    email_recipients: List[str]
    subject_prefix: str
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    dry_run: bool


def load_rss_urls(config_path: Path) -> Dict[str, str]:
    with config_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload.get("RSS_URLS", {})


class MSCIWorldAgent:
    """Encapsulates the LangGraph workflow for the MSCI report."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.scraper = RSSScraper(settings.rss_urls, settings.limit)
        self.chain = self._build_chain()
        self.app = self._build_graph()

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Eres un analista financiero. Resume noticias sobre MSCI World en un lenguaje "
                    "for dummies y destaca conclusiones accionables. Responde siempre en JSON con "
                    "las claves 'summary_for_dummies' y 'conclusiones'.",
                ),
                (
                    "human",
                    "Fecha: {date}\nIdioma objetivo: {language}\nEntradas:\n{articles}",
                ),
            ]
        )
        llm = ChatOpenAI(model=self.settings.model, temperature=self.settings.temperature)
        return prompt | llm

    def _build_graph(self):
        graph = StateGraph(AgentState)

        def node_fetch(_: AgentState) -> AgentState:
            return {"articles": self.scraper.fetch()}

        def node_summarize(state: AgentState) -> AgentState:
            articles = state.get("articles", [])
            if not articles:
                return {
                    "summary": "No hay artículos disponibles.",
                    "insights": "Sin datos nuevos, revisar más tarde.",
                }
            response = self.chain.invoke(
                {
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "language": self.settings.language,
                    "articles": self._format_articles_for_prompt(articles),
                }
            )
            parsed = self._extract_json_block(response.content)
            return {
                "summary": parsed.get("summary_for_dummies", ""),
                "insights": parsed.get("conclusiones", ""),
            }

        def node_compose(state: AgentState) -> AgentState:
            today = datetime.now().strftime("%d/%m/%Y")
            lines = [
                f"{self.settings.subject_prefix} - {today}",
                "",
                "Resumen for dummies:",
                state.get("summary", ""),
                "",
                "Conclusiones MSCI World:",
                state.get("insights", ""),
                "",
                "Titulares revisados:",
            ]
            for art in state.get("articles", []):
                lines.append(f"- {art['title']} ({art['source']}) -> {art['link']}")
            return {"email_body": "\n".join(lines)}

        def node_send(state: AgentState) -> AgentState:
            if self.settings.dry_run:
                print("Modo DRY_RUN activo. Email no enviado.")
                print(state.get("email_body", ""))
                return {}
            if not (self.settings.email_recipients and self.settings.email_sender):
                print("Faltan emails de remitente/destinatarios. No se envía.")
                return {}
            if not self.settings.smtp_host or not self.settings.smtp_username or not self.settings.smtp_password:
                print("Configuración SMTP incompleta. No se envía.")
                return {}
            message = MIMEText(state.get("email_body", ""), _charset="utf-8")
            message["Subject"] = f"{self.settings.subject_prefix} - {datetime.now().strftime('%d/%m/%Y')}"
            message["From"] = self.settings.email_sender
            message["To"] = ", ".join(self.settings.email_recipients)
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                smtp.sendmail(
                    self.settings.email_sender, self.settings.email_recipients, message.as_string()
                )
            return {}

        graph.add_node("fetch", node_fetch)
        graph.add_node("summarize", node_summarize)
        graph.add_node("compose", node_compose)
        graph.add_node("send", node_send)

        graph.set_entry_point("fetch")
        graph.add_edge("fetch", "summarize")
        graph.add_edge("summarize", "compose")
        graph.add_edge("compose", "send")
        graph.add_edge("send", END)
        return graph.compile()

    @staticmethod
    def _format_articles_for_prompt(articles: List[Article]) -> str:
        rows = []
        for art in articles:
            rows.append(
                f"- Fuente: {art['source']}\n  Título: {art['title']}\n"
                f"  Publicado: {art['published']}\n  Link: {art['link']}\n"
                f"  Resumen: {art['summary']}"
            )
        return "\n".join(rows)

    @staticmethod
    def _extract_json_block(text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.strip("` \n")
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Respuesta del modelo no es JSON válido: {cleaned}") from exc

    def run(self):
        self.app.invoke({})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agente diario MSCI World para RSS + email.")
    parser.add_argument("--limit", type=int, default=3, help="Número de artículos por RSS.")
    parser.add_argument("--language", default="es", help="Idioma del resumen.")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    parser.add_argument(
        "--temperature", type=float, default=0.2, help="Creatividad del modelo."
    )
    parser.add_argument("--subject-prefix", default="Reporte MSCI World")
    parser.add_argument("--dry-run", action="store_true", help="Evita enviar email real.")
    return parser.parse_args()


def build_settings(args: argparse.Namespace) -> Settings:
    config_path = Path(__file__).with_name("config.json")
    urls = load_rss_urls(config_path)
    recipients = [
        email.strip()
        for email in os.getenv("REPORT_RECIPIENTS", "").split(",")
        if email.strip()
    ]
    return Settings(
        rss_urls=urls,
        limit=args.limit,
        language=args.language,
        model=args.model,
        temperature=args.temperature,
        email_sender=os.getenv("REPORT_SENDER", ""),
        email_recipients=recipients,
        subject_prefix=args.subject_prefix,
        smtp_host=os.getenv("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        dry_run=args.dry_run or os.getenv("DRY_RUN", "false").lower() == "true",
    )


def main():
    args = parse_args()
    settings = build_settings(args)
    agent = MSCIWorldAgent(settings)
    agent.run()


if __name__ == "__main__":
    main()
