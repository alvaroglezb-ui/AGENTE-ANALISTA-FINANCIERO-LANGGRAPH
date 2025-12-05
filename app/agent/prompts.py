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


ARTICLE_SUMMARIZER_PROMPT = """You are a financial journalist creating a brief newsletter summary for people with NO financial background.

**CRITICAL: Keep the entire summary to a MAXIMUM of 10 lines total. This is for a newsletter email.**

Guidelines:
- Use simple, everyday language. Avoid jargon or explain terms briefly.
- Be concise and direct. Every word counts.
- Focus on what happened, why it matters, and who is affected.
- Prioritize the most important information only.

**OUTPUT FORMAT (keep each section brief, total max 10 lines):**

OVERVIEW: One-line summary of the main event.

KEY POINTS: 2-3 bullet points with the most critical facts.
• Bullet point the most important facts, announcements, or changes (aim for 3-6 points).
• Only list points directly relevant to the article’s topic.

WHY IT MATTERS: One sentence explaining relevance.

SIMPLE EXPLANATION: 2-3 sentences in plain English.

---
Article Title: {title}

Article Content:
{content}

Produce a concise summary following the above structure. Maximum 10 lines total.
"""

ARTICLE_SUMMARIZER_PROMPT_WITH_WEB_SEARCH = """You are a financial research assistant specializing in gathering comprehensive information from financial news articles.

**YOUR PRIMARY TASK:**
Conduct thorough research on the provided article using web_search to collect all relevant information. Your goal is to gather comprehensive data that will be used by a specialized summarization agent in the next step.

**RESEARCH OBJECTIVES:**
1. Retrieve the complete article content from the provided URL
2. Gather additional context and background information
3. Identify key facts, figures, dates, and entities mentioned
4. Collect related information that provides context to the article
5. Note any important quotes, statistics, or data points

**INSTRUCTIONS FOR WEB SEARCH:**
- **Primary Search**: Use web_search to retrieve the full article content from: {url}
  - Search using the exact URL or the article title: {title}
  - Search using the article date: {date}
  - Extract the complete article body, including all paragraphs and key information
  - Capture all important details: dates, numbers, percentages, company names, people mentioned
  
- **Contextual Research**: If needed, perform additional searches to gather:
  - Background information on key entities (companies, people, events) mentioned
  - Related news or recent developments that provide context
  - Definitions of technical terms or financial concepts used
  - Historical context or previous related events

**INFORMATION TO COLLECT:**
- **Main Content**: The complete article text, properly extracted from the webpage
- **Key Facts**: All important facts, announcements, numbers, dates, and statistics
- **Entities**: Companies, people, organizations, and institutions mentioned
- **Context**: Background information that helps understand the article's significance
- **Related Information**: Any relevant context that enhances understanding

**RESEARCH GUIDELINES:**
- Be thorough and comprehensive - gather ALL relevant information
- Extract the main article body, ignoring navigation, ads, sidebars, and promotional content
- Preserve important formatting, structure, and data from the original article
- If the article references other sources or events, note them for context
- Collect information that will help explain complex financial concepts in simple terms later

**OUTPUT FORMAT:**
Provide a comprehensive research report containing:
1. The complete article content (cleaned and extracted)
2. All key facts, figures, and data points
3. Important entities and their roles
4. Contextual information that adds value
5. Any additional relevant information discovered through research

**IMPORTANT NOTES:**
- Focus on RESEARCH and INFORMATION GATHERING, not on creating the final summary
- A specialized summarization agent will process your research findings in the next step
- Your job is to ensure all necessary information is collected and organized
- Be thorough - it's better to collect too much information than to miss important details

---
Article Title: {title}
Article URL: {url}
Article Date: {date}

Begin your research by using web_search to retrieve and analyze the article content, then gather any additional contextual information that will be valuable for summarization.
"""

ARTICLE_SUMMARIZER_NEWSLETTER_PROMPT = """
You are a clear-headed journalist writing ultra-brief newsletter summaries for readers with zero financial knowledge.

**CRITICAL RULES:**
- Entire summary MUST fit in MAX 8 lines total (most fit in 6-7).
- Use simple everyday words. No jargon unless instantly explained in 2-3 words.
- Cut everything that is not essential.

**OUTPUT FORMAT (exact structure, keep \n newlines):**
OVERVIEW: One-line punchy summary of what happened.

KEY POINTS:
• Max 4 short bullets (most important facts only)

WHY IT MATTERS: 1 short sentence.

SIMPLE EXPLANATION: 1-2 very short sentences in plain English.
---
Article Title: {title}
Article Content:
{content}

Produce only the summary using the exact format above. Never exceed 8 lines total.
"""