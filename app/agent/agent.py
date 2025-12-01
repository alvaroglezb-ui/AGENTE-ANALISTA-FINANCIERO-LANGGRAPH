"""
Simple LangGraph agent to process articles: clean markdown and generate structured summaries.
"""
import os
import io
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from openai import OpenAI
from app.scrapers.rss_scraper import extraction
from app.agent.tools import clean_markdown, summarize_article, summarize_article_with_web_search
from IPython.display import Image, display
from dotenv import load_dotenv
load_dotenv()

class AgentState(TypedDict):
    """State for article processing."""
    extraction_data: extraction
    collection_index: int
    article_index: int


class ArticleSummarizerAgent:
    """Simple agent that processes articles sequentially."""
    
    def __init__(self, model: str = os.getenv("AGENT_MODEL"), temperature: float = 0.3):
        self.model = model
        self.temperature = temperature
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self.openai = OpenAI()
        self.app = self._build_graph()
        self._graph_to_png()
    
    def _build_graph(self):
        """Build simple LangGraph workflow."""
        graph = StateGraph(AgentState)
        graph.add_node("process", self._process_node)
        graph.set_entry_point("process")
        graph.add_conditional_edges(
            "process",
            self._should_continue,
            {"continue": "process", "end": END}
        )
        return graph.compile()

    def _graph_to_png(self, path="app/agent"):
        """Save graph schema as PNG image."""
        try:
            from pathlib import Path
            
            # Get PNG bytes from LangGraph
            png_bytes = self.app.get_graph().draw_mermaid_png()
            
            # Save PNG bytes directly to file
            output_path = Path(path) / "graph_schema.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(png_bytes)
            
            print(f"✓ Graph schema saved to: {output_path}")
            
            # Display using IPython if available
            try:
                from IPython.display import Image, display
                display(Image(str(output_path)))
            except:
                pass  # Not in IPython environment
                
        except Exception as e:
            print(f"⚠️  Warning: Could not save graph schema: {e}")
        
    def _process_node(self, state: AgentState) -> AgentState:
        """Process one article: clean markdown and generate summary."""
        extraction_data = state.get("extraction_data", {})
        collection_index = state.get("collection_index", 0)
        article_index = state.get("article_index", 0)
        
        collections = extraction_data.get("scraping", [])
        
        # Check if done
        if collection_index >= len(collections):
            return state
        
        collection = collections[collection_index]
        articles = collection.get("articles", [])
        
        # Move to next collection if done with current
        if article_index >= len(articles):
            return {
                "collection_index": collection_index + 1,
                "article_index": 0
            }
        
        # Get article and update in-place
        article = articles[article_index]
        title = article.get("title", "")
        date = article.get("published", "")
        source = collection.get("source", "Unknown")
        
        print(f"[{source}] Processing {article_index + 1}/{len(articles)}: {title[:50]}...")
        
        try:
            # Step 1: Clean markdown
            original_content = summarize_article_with_web_search(title, article.get("link", ""),date, self.openai)
            article["content"] = original_content
            
            # Step 2: Generate structured summary
            summary_obj = summarize_article(title, article["content"], self.llm)
            
            # Format summary as string with consistent structure
            summary_text = f"""OVERVIEW:
{summary_obj.overview}

KEY POINTS:
{chr(10).join(f"• {point}" for point in summary_obj.key_points)}

WHY IT MATTERS:
{summary_obj.why_it_matters}

SIMPLE EXPLANATION:
{summary_obj.simple_explanation}"""
            
            article["summary"] = summary_text
            
        except Exception as e:
            print(f"Error processing article: {e}")
            article["summary"] = f"Error: {str(e)}"
        
        # Move to next article
        return {"article_index": article_index + 1}
    
    def _should_continue(self, state: AgentState) -> str:
        """Check if processing should continue."""
        extraction_data = state.get("extraction_data", {})
        collection_index = state.get("collection_index", 0)
        article_index = state.get("article_index", 0)
        
        collections = extraction_data.get("scraping", [])
        
        if collection_index >= len(collections):
            total = sum(len(c.get("articles", [])) for c in collections)
            print(f"\n✓ Processed {total} articles")
            return "end"
        
        collection = collections[collection_index]
        articles = collection.get("articles", [])
        
        if article_index >= len(articles):
            return "continue"  # Move to next collection
        
        return "continue"  # Process next article
    
    def process_extraction(self, extraction_data: extraction) -> extraction:
        """
        Process all articles: clean markdown and generate structured summaries.
        Updates articles in-place to maintain order.
        """
        collections = extraction_data.get("scraping", [])
        
        if not collections:
            return extraction_data
        
        total = sum(len(c.get("articles", [])) for c in collections)
        if total == 0:
            return extraction_data
        
        print(f"\n{'='*60}")
        print(f"Processing {total} articles across {len(collections)} collections")
        print(f"{'='*60}\n")
        
        initial_state: AgentState = {
            "extraction_data": extraction_data,
            "collection_index": 0,
            "article_index": 0
        }
        
        final_state = self.app.invoke(initial_state)
        
        print(f"\n{'='*60}")
        print(f"✓ Completed processing")
        print(f"{'='*60}\n")
        
        return final_state["extraction_data"]
