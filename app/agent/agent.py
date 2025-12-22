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
from app.agent.tools import clean_markdown, summarize_article, summarize_article_with_web_search, rank_article
from app.agent.language_config import get_language_config, get_header
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
        graph.add_node("rank", self._rank_node)
        graph.add_node("process", self._process_node)
        graph.set_entry_point("rank")
        graph.add_edge("rank", "process")
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
    
    def _rank_node(self, state: AgentState) -> AgentState:
        """Rank all articles and select top 10 based on ranking score."""
        extraction_data = state.get("extraction_data", {})
        collections = extraction_data.get("scraping", [])
        
        if not collections:
            return {
                "extraction_data": extraction_data,
                "collection_index": 0,
                "article_index": 0
            }
        
        # Collect all articles with their collection info
        all_articles_with_context = []
        for collection_idx, collection in enumerate(collections):
            articles = collection.get("articles", [])
            for article_idx, article in enumerate(articles):
                all_articles_with_context.append({
                    "article": article,
                    "collection_idx": collection_idx,
                    "article_idx": article_idx,
                    "source": collection.get("source", "Unknown")
                })
        
        total_articles = len(all_articles_with_context)
        if total_articles == 0:
            return {
                "extraction_data": extraction_data,
                "collection_index": 0,
                "article_index": 0
            }
        
        print(f"\n{'='*60}")
        print(f"Ranking {total_articles} articles...")
        print(f"{'='*60}\n")
        
        # Rank each article
        for idx, item in enumerate(all_articles_with_context):
            article = item["article"]
            title = article.get("title", "")
            content = article.get("content", "")
            link = article.get("link", "")
            published = article.get("published", "")
            source = item["source"]
            
            print(f"[{source}] Ranking {idx + 1}/{total_articles}: {title[:50]}...")
            
            try:
                score = rank_article(title, content, link, published, self.llm)
                article["rank_score"] = score
                print(f"  Score: {score:.2f}")
            except Exception as e:
                print(f"  Error ranking article: {e}")
                article["rank_score"] = 0.0
        
        # Sort all articles by rank_score (descending)
        all_articles_with_context.sort(key=lambda x: x["article"].get("rank_score", 0.0), reverse=True)
        
        # Select top 10 articles
        top_10 = all_articles_with_context[:int(os.getenv("TOP_RANK"))]
        
        print(f"\n{'='*60}")
        print(f"Selected top {len(top_10)} articles:")
        for idx, item in enumerate(top_10):
            article = item["article"]
            score = article.get("rank_score", 0.0)
            print(f"  {idx + 1}. [{item['source']}] {article.get('title', '')[:50]}... (Score: {score:.2f})")
        print(f"{'='*60}\n")
        
        # Rebuild collections structure with only top 10 articles
        # Group articles by their original collection
        collections_map = {}
        for item in top_10:
            collection_idx = item["collection_idx"]
            article = item["article"]
            
            if collection_idx not in collections_map:
                original_collection = collections[collection_idx]
                collections_map[collection_idx] = {
                    "source": original_collection.get("source", "Unknown"),
                    "articles": []
                }
            
            collections_map[collection_idx]["articles"].append(article)
        
        # Create new extraction_data with top 10 articles
        ranked_collections = [collections_map[idx] for idx in sorted(collections_map.keys())]
        ranked_extraction_data = {
            "scraping": ranked_collections
        }
        
        return {
            "extraction_data": ranked_extraction_data,
            "collection_index": 0,
            "article_index": 0
        }
        
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
            
            # Use existing content if available, otherwise fetch with web search
            existing_content = article.get("content", "")
            if existing_content and existing_content.strip():
                original_content = existing_content
            else:
                original_content = summarize_article_with_web_search(title, article.get("link", ""),date, self.openai)
            article["content"] = original_content
            
            # Step 2: Generate structured summary
            summary_obj = summarize_article(title, article["content"], self.llm)
            
            # Format summary as string with consistent structure using current language
            lang_config = get_language_config()
            summary_text = f"""{lang_config["headers"]["overview"]}:
{summary_obj.overview}

{lang_config["headers"]["key_points"]}:
{chr(10).join(f"• {point}" for point in summary_obj.key_points)}

{lang_config["headers"]["why_it_matters"]}:
{summary_obj.why_it_matters}

{lang_config["headers"]["simple_explanation"]}:
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
