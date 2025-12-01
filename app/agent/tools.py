"""
Tools for article processing: markdown cleaning and summarization.
"""
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import OpenAI
from app.agent.schemas import ArticleSummary
from app.agent.prompts import MARKDOWN_CLEANER_PROMPT, ARTICLE_SUMMARIZER_PROMPT, ARTICLE_SUMMARIZER_PROMPT_WITH_WEB_SEARCH
from dotenv import load_dotenv
load_dotenv()

def clean_markdown(content: str, llm: ChatOpenAI) -> str:
    """
    Clean markdown content by removing navigation, ads, and keeping only article body.
    
    Args:
        content: Raw markdown content to clean
        llm: ChatOpenAI instance to use for cleaning
        
    Returns:
        Cleaned markdown content
    """
    if not content:
        return ""
    
    prompt = ChatPromptTemplate.from_template(MARKDOWN_CLEANER_PROMPT)
    chain = prompt | llm
    
    try:
        response = chain.invoke({"content": content})
        return response.content.strip()
    except Exception as e:
        print(f"Error cleaning markdown: {e}")
        return content


def summarize_article(title: str, content: str, llm: ChatOpenAI) -> ArticleSummary:
    """
    Generate structured summary of an article for non-expert readers.
    
    Args:
        title: Article title
        content: Article content (should be cleaned markdown)
        llm: ChatOpenAI instance to use for summarization
        
    Returns:
        ArticleSummary object with structured summary
    """
    if not content:
        return ArticleSummary(
            overview="No content available",
            key_points=[],
            why_it_matters="Unable to summarize",
            simple_explanation="No content available to summarize."
        )
    
    prompt = ChatPromptTemplate.from_template(ARTICLE_SUMMARIZER_PROMPT)
    
    # Use structured output with Pydantic
    structured_llm = llm.with_structured_output(ArticleSummary)
    chain = prompt | structured_llm
    
    try:
        summary = chain.invoke({"title": title, "content": content})
        return summary
    except Exception as e:
        print(f"Error summarizing: {e}")
        return ArticleSummary(
            overview="Summary generation failed",
            key_points=["Error occurred during summarization"],
            why_it_matters="Unable to determine",
            simple_explanation=f"Error: {str(e)}"
        )

def summarize_article_with_web_search(title: str, url: str, date: str,llm: OpenAI) -> ArticleSummary:
    """
    Generate structured summary of an article for non-expert readers.
    
    Args:
        title: Article title
        URL: Article URL
        llm: ChatOpenAI instance to use for summarization
        
    Returns:
        ArticleSummary object with structured summary
    """
    title = f"Article Title: {title}"
    url = f"Article URL: {url}"

    response = llm.responses.create(
        model=os.getenv("WEB_SEARCH_MODEL"),
        tools=[
            {
                "type": "web_search",
            }
        ],
        instructions=ARTICLE_SUMMARIZER_PROMPT_WITH_WEB_SEARCH.format(title=title, url=url, date=date),
        input=title,
        tool_choice="required",
        include=["web_search_call.action.sources"]
    )
    return response.output_text