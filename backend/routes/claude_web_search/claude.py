# import anthropic
# import re
# from typing import Dict, List, Optional
# from pydantic import BaseModel

# # ============================================
# # Response Models
# # ============================================

# class Citation(BaseModel):
#     index: int
#     url: str
#     title: Optional[str] = None
#     snippet: Optional[str] = None

# class ClaudeWebSearchResult(BaseModel):
#     answer: str
#     citations: List[Citation]
#     cited_indices: List[int]
#     target_cited: bool
#     target_citation_position: Optional[int] = None
#     total_citations: int
#     raw_response: dict

# # ============================================
# # Claude Web Search Service
# # ============================================

# class ClaudeWebSearchService:
#     def __init__(self, api_key: str):
#         self.client = anthropic.Anthropic(api_key=api_key)
#         self.model = "claude-haiku-4-5-20251001"
    
#     def search_and_analyze(
#         self, 
#         query: str, 
#         target_url: str,
#         brand_name: str
#     ) -> ClaudeWebSearchResult:
#         # System prompt to ensure citations
#         system_prompt = """You are a research assistant that provides comprehensive answers with citations.

# CRITICAL REQUIREMENTS:
# 1. Use the web_search tool to find current information
# 2. ALWAYS cite sources using [1], [2], [3] format immediately after claims
# 3. If multiple sources support a claim, cite all: [1][2]
# 4. Create a 200-300 word comprehensive answer
# 5. At the end, list all sources you used with URLs

# Format:
# - Answer with inline citations
# - Then: "Sources:\n[1] Title - URL\n[2] Title - URL"
# """

#         user_prompt = f"""Research this query and provide a comprehensive answer with citations:

# Query: {query}

# Requirements:
# - Use web_search to find the most relevant sources
# - Cite each claim with [1], [2], etc.
# - Include diverse perspectives from multiple sources
# - Provide a balanced, informative answer"""

#         # Make API call with web_search tool
#         response = self.client.messages.create(
#             model=self.model,
#             max_tokens=4000,
#             system=system_prompt,
#             messages=[
#                 {
#                     "role": "user",
#                     "content": user_prompt
#                 }
#             ],
#             tools=[
#                 {
#                     "type": "web_search_20250305",
#                     "name": "web_search"
#                 }
#             ]
#         )
        
#         # Extract answer and citations
#         result = self._parse_response(
#             response=response,
#             target_url=target_url,
#             brand_name=brand_name
#         )
        
#         return result
    
#     def _parse_response(
#         self,
#         response,
#         target_url: str,
#         brand_name: str
#     ) -> ClaudeWebSearchResult:
#         """Parse Claude's response to extract citations and sources"""
        
#         # Extract text content
#         answer_text = ""
#         sources_list = []
        
#         for block in response.content:
#             if block.type == "text":
#                 answer_text += block.text
        
#         # Extract citation numbers from answer
#         citation_pattern = r'\[(\d+)\]'
#         citation_matches = re.findall(citation_pattern, answer_text)
#         cited_indices = sorted(list(set(int(c) for c in citation_matches)))
        
#         # Extract sources from "Sources:" section
#         sources_section = self._extract_sources_section(answer_text)
#         citations = self._parse_sources(sources_section)
        
#         # If sources not in text, try to extract from tool results
#         if not citations:
#             citations = self._extract_from_tool_results(response)
        
#         # Check if target URL is cited
#         target_cited = False
#         target_position = None
        
#         # Normalize target URL for matching
#         normalized_target = self._normalize_url(target_url)
        
#         for idx in cited_indices:
#             # Find corresponding citation
#             citation = next((c for c in citations if c.index == idx), None)
#             if citation:
#                 normalized_citation_url = self._normalize_url(citation.url)
                
#                 # Check if target URL matches
#                 if normalized_target in normalized_citation_url or \
#                    normalized_citation_url in normalized_target:
#                     target_cited = True
#                     # Position is the order in cited_indices
#                     target_position = cited_indices.index(idx) + 1
#                     break
        
#         return ClaudeWebSearchResult(
#             answer=answer_text,
#             citations=citations,
#             cited_indices=cited_indices,
#             target_cited=target_cited,
#             target_citation_position=target_position,
#             total_citations=len(cited_indices),
#             raw_response=response.model_dump()
#         )
    
#     def _extract_sources_section(self, text: str) -> str:
#         """Extract the 'Sources:' section from answer"""
        
#         # Look for common patterns
#         patterns = [
#             r'Sources?:\s*\n(.*?)(?:\n\n|\Z)',
#             r'References?:\s*\n(.*?)(?:\n\n|\Z)',
#             r'Citations?:\s*\n(.*?)(?:\n\n|\Z)',
#         ]
        
#         for pattern in patterns:
#             match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
#             if match:
#                 return match.group(1)
        
#         return ""
    
#     def _parse_sources(self, sources_text: str) -> List[Citation]:
#         """Parse sources from text format"""
        
#         citations = []
        
#         # Pattern: [1] Title - URL or [1] URL
#         pattern = r'\[(\d+)\]\s*(.+?)\s*-\s*(https?://[^\s\]]+)|' \
#                   r'\[(\d+)\]\s*(https?://[^\s\]]+)'
        
#         matches = re.finditer(pattern, sources_text)
        
#         for match in matches:
#             if match.group(1):  # Format: [1] Title - URL
#                 index = int(match.group(1))
#                 title = match.group(2).strip()
#                 url = match.group(3).strip()
#             elif match.group(4):  # Format: [1] URL
#                 index = int(match.group(4))
#                 title = None
#                 url = match.group(5).strip()
#             else:
#                 continue
            
#             citations.append(Citation(
#                 index=index,
#                 url=url,
#                 title=title
#             ))
        
#         return citations
    
#     def _extract_from_tool_results(self, response) -> List[Citation]:
#         """
#         Extract sources from tool use results in response
#         (When Claude uses web_search, results may be in tool blocks)
#         """
        
#         citations = []
#         index = 1
        
#         for block in response.content:
#             if hasattr(block, 'type') and block.type == "tool_result":
#                 # Tool result contains search results
#                 if hasattr(block, 'content'):
#                     # Parse tool result content
#                     # This structure varies, adapt as needed
#                     citations.append(Citation(
#                         index=index,
#                         url="unknown",  # Extract from block
#                         title="Source from tool"
#                     ))
#                     index += 1
        
#         return citations
    
#     def _normalize_url(self, url: str) -> str:
#         """Normalize URL for comparison"""
        
#         # Remove protocol
#         url = re.sub(r'^https?://', '', url)
#         # Remove www
#         url = re.sub(r'^www\.', '', url)
#         # Remove trailing slash
#         url = url.rstrip('/')
#         # Lowercase
#         url = url.lower()
        
#         return url





import anthropic
import re
from typing import Dict, List, Optional
from pydantic import BaseModel

# ============================================
# Response Models
# ============================================

class Citation(BaseModel):
    index: int
    url: str
    title: Optional[str] = None
    snippet: Optional[str] = None

class CompetitorMention(BaseModel):
    name: str
    mention_count: int
    cited: bool  # Whether they were cited (in [1], [2], etc.)
    citation_position: Optional[int] = None  # Their position in citations
    url: Optional[str] = None  # Their URL if cited

class ClaudeWebSearchResult(BaseModel):
    # Core answer
    answer: str
    
    # Citation data
    citations: List[Citation]  # All citations with URLs
    cited_indices: List[int]  # [1, 3, 5, 7]
    total_citations: int
    
    # Target brand tracking
    target_cited: bool
    target_citation_position: Optional[int] = None
    
    # NEW: URL tracking
    cited_urls: List[str]  # All URLs that were cited
    
    # NEW: Competitor tracking
    competitors_mentioned: List[CompetitorMention]  # All competitors in answer
    competitor_urls_cited: List[str]  # Competitor URLs that were cited
    
    # Raw data
    raw_response: dict

# ============================================
# Claude Web Search Service
# ============================================

class ClaudeWebSearchService:
    def __init__(self, api_key: str, competitor_brands: Optional[List[str]] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-haiku-4-5-20251001"
        
        # Default competitors if none provided
        self.competitor_brands = competitor_brands or [
            "Monday.com", "ClickUp", "Notion", "Trello", 
            "Jira", "Asana", "Smartsheet", "Wrike"
        ]
    
    def search_and_analyze(
        self, 
        query: str, 
        target_url: str,
        brand_name: str
    ) -> ClaudeWebSearchResult:
        # System prompt to ensure citations
        system_prompt = """You are a research assistant that provides comprehensive answers with citations.

CRITICAL REQUIREMENTS:
1. Use the web_search tool to find current information
2. ALWAYS cite sources using [1], [2], [3] format immediately after claims
3. If multiple sources support a claim, cite all: [1][2]
4. Create a 200-300 word comprehensive answer
5. At the end, list all sources you used with URLs

Format:
- Answer with inline citations
- Then: "Sources:\n[1] Title - URL\n[2] Title - URL"
"""

        user_prompt = f"""Research this query and provide a comprehensive answer with citations:

Query: {query}

Requirements:
- Use web_search to find the most relevant sources
- Cite each claim with [1], [2], etc.
- for each citation give the source with URL at the end.
- Include diverse perspectives from multiple sources
- Provide a balanced, informative answer
- the cited sources must be mentioned with url.
"""

        # Make API call with web_search tool
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            tools=[
                {
                    "type": "web_search_20250305",
                    "name": "web_search"
                }
            ]
        )
        
        # Extract answer and all metrics
        result = self._parse_response(
            response=response,
            target_url=target_url,
            brand_name=brand_name
        )
        
        return result
    
    def _parse_response(
        self,
        response,
        target_url: str,
        brand_name: str
    ) -> ClaudeWebSearchResult:
        """Parse Claude's response to extract all metrics"""
        
        # Extract text content
        answer_text = ""
        for block in response.content:
            if block.type == "text":
                answer_text += block.text
        
        # Extract citation numbers from answer [1], [2], [3]
        citation_pattern = r'\[(\d+)\]'
        citation_matches = re.findall(citation_pattern, answer_text)
        cited_indices = sorted(list(set(int(c) for c in citation_matches)))
        
        # Extract sources from "Sources:" section
        sources_section = self._extract_sources_section(answer_text)
        citations = self._parse_sources(sources_section)
        
        # If sources not in text, try to extract from tool results
        if not citations:
            citations = self._extract_from_tool_results(response)
        
        # === NEW: Extract all cited URLs ===
        cited_urls = [c.url for c in citations if c.index in cited_indices]
        
        # === Check if target URL is cited ===
        target_cited = False
        target_position = None
        normalized_target = self._normalize_url(target_url)
        
        for idx in cited_indices:
            citation = next((c for c in citations if c.index == idx), None)
            if citation:
                normalized_citation_url = self._normalize_url(citation.url)
                if normalized_target in normalized_citation_url or \
                   normalized_citation_url in normalized_target:
                    target_cited = True
                    target_position = cited_indices.index(idx) + 1
                    break
        
        # === NEW: Analyze competitor mentions and citations ===
        competitors_mentioned = self._analyze_competitors(
            answer_text=answer_text,
            citations=citations,
            cited_indices=cited_indices,
            brand_name=brand_name
        )
        
        # === NEW: Extract competitor URLs that were cited ===
        competitor_urls_cited = [
            comp.url for comp in competitors_mentioned 
            if comp.cited and comp.url
        ]
        
        return ClaudeWebSearchResult(
            answer=answer_text,
            citations=citations,
            cited_indices=cited_indices,
            total_citations=len(cited_indices),
            
            # Target tracking
            target_cited=target_cited,
            target_citation_position=target_position,
            
            # NEW: URL tracking
            cited_urls=cited_urls,
            
            # NEW: Competitor tracking
            competitors_mentioned=competitors_mentioned,
            competitor_urls_cited=competitor_urls_cited,
            
            raw_response=response.model_dump()
        )
    
    def _analyze_competitors(
        self,
        answer_text: str,
        citations: List[Citation],
        cited_indices: List[int],
        brand_name: str
    ) -> List[CompetitorMention]:
        """
        Analyze which competitors are mentioned and cited
        
        Returns:
            List of CompetitorMention with counts, citation status, and URLs
        """
        
        competitors_data = []
        answer_lower = answer_text.lower()
        
        for competitor in self.competitor_brands:
            # Skip if this is the target brand
            if competitor.lower() == brand_name.lower():
                continue
            
            # Count mentions in answer
            mention_count = answer_lower.count(competitor.lower())
            
            if mention_count == 0:
                continue  # Skip competitors not mentioned
            
            # Check if competitor was cited (has a URL in citations)
            cited = False
            citation_position = None
            competitor_url = None
            
            # Try to find competitor's URL in cited sources
            for idx in cited_indices:
                citation = next((c for c in citations if c.index == idx), None)
                if citation:
                    # Check if URL or title contains competitor name
                    url_lower = citation.url.lower()
                    title_lower = (citation.title or "").lower()
                    comp_lower = competitor.lower().replace(".com", "").replace(" ", "")
                    
                    if comp_lower in url_lower or comp_lower in title_lower:
                        cited = True
                        citation_position = cited_indices.index(idx) + 1
                        competitor_url = citation.url
                        break
            
            competitors_data.append(CompetitorMention(
                name=competitor,
                mention_count=mention_count,
                cited=cited,
                citation_position=citation_position,
                url=competitor_url
            ))
        
        # Sort by mention count (most mentioned first)
        competitors_data.sort(key=lambda x: x.mention_count, reverse=True)
        
        return competitors_data
    
    def _extract_sources_section(self, text: str) -> str:
        """Extract the 'Sources:' section from answer"""
        
        patterns = [
            r'Sources?:\s*\n(.*?)(?:\n\n|\Z)',
            r'References?:\s*\n(.*?)(?:\n\n|\Z)',
            r'Citations?:\s*\n(.*?)(?:\n\n|\Z)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _parse_sources(self, sources_text: str) -> List[Citation]:
        """Parse sources from text format"""
        
        citations = []
        
        # Pattern: [1] Title - URL or [1] URL
        pattern = r'\[(\d+)\]\s*(.+?)\s*-\s*(https?://[^\s\]]+)|' \
                  r'\[(\d+)\]\s*(https?://[^\s\]]+)'
        
        matches = re.finditer(pattern, sources_text)
        
        for match in matches:
            if match.group(1):  # Format: [1] Title - URL
                index = int(match.group(1))
                title = match.group(2).strip()
                url = match.group(3).strip()
            elif match.group(4):  # Format: [1] URL
                index = int(match.group(4))
                title = None
                url = match.group(5).strip()
            else:
                continue
            
            citations.append(Citation(
                index=index,
                url=url,
                title=title
            ))
        
        return citations
    
    def _extract_from_tool_results(self, response) -> List[Citation]:
        """Extract sources from tool use results in response"""
        
        citations = []
        index = 1
        
        for block in response.content:
            if hasattr(block, 'type') and block.type == "tool_result":
                if hasattr(block, 'content'):
                    citations.append(Citation(
                        index=index,
                        url="unknown",
                        title="Source from tool"
                    ))
                    index += 1
        
        return citations
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        url = url.rstrip('/')
        url = url.lower()
        
        return url

