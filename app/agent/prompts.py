"""
Prompts for article processing.
"""

MARKDOWN_CLEANER_PROMPT = """You are an expert content extractor. Clean the following markdown content by:

1. Removing all navigation, headers, footers, sidebars, and advertisements
2. Removing HTML tags, scripts, styles, and metadata
3. Removing cookie notices, privacy policy links, and legal disclaimers
4. Removing social media buttons and widgets
5. Extracting ONLY the main article body content
6. Preserving paragraphs, headings, and important formatting
7. Removing duplicate content or repeated sections
8. Keeping only text directly related to the article's main topic
9. Preserving important data: numbers, percentages, dates, company names

Return ONLY the cleaned content, no explanations.

Markdown content:
{content}

Cleaned content:"""


ARTICLE_SUMMARIZER_PROMPT = """You are a financial journalist explaining complex financial news to people with NO financial background.

Your task is to create a clear, accessible, and fully structured summary of this financial article. **You must strictly follow the provided output structure and include every section as specified.**

Guidelines:
- Use simple, everyday language.
- Avoid jargon. If you use any financial terms, explain them briefly.
- Be friendly and conversational.
- Focus on what happened, why it matters, and who is affected.
- Do NOT skip any required section of the structured output.

**MANDATORY STRUCTURED OUTPUT FORMAT:**

OVERVIEW:
Briefly summarize the main event or topic of the article.

KEY POINTS:
• Bullet point the most important facts, announcements, or changes (aim for 3-6 points).
• Only list points directly relevant to the article’s topic.

WHY IT MATTERS:
Explain in plain language why this article is important or relevant, especially for a non-expert.

SIMPLE EXPLANATION:
Offer a plain-English, one-paragraph summary suitable for someone who has no financial background.

Always output your summary using ALL of those sections, in this exact order.

---
Article Title: {title}

Article Content:
{content}

Produce your summary following the above structure.
"""
