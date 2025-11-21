from routes.claude_web_search.claude import ClaudeWebSearchService

async def claude_web_search(query, target_url, brand_name):
    # Initialize service
    service = ClaudeWebSearchService(
        api_key=""
    )
    
    # Execute search and analysis
    result = service.search_and_analyze(query, target_url, brand_name)
        # query="best project management software for teams",
        # target_url="asana.com",
        # brand_name="Asana"
    # )
    
    # # Display results
    # print("=" * 60)
    # print("CLAUDE WEB SEARCH RESULT")
    # print("=" * 60)
    # print()
    
    # print("📝 ANSWER:")
    # print(result.answer)
    # print()
    
    # print("=" * 60)
    # print("📊 CITATION ANALYSIS")
    # print("=" * 60)
    # print()
    
    # print(f"Total Citations: {result.total_citations}")
    # print(f"Cited Indices: {result.cited_indices}")
    # print()
    
    # if result.target_cited:
    #     print(f"✅ TARGET CITED: YES")
    #     print(f"📍 Citation Position: #{result.target_citation_position}")
    # else:
    #     print(f"❌ TARGET CITED: NO")
    # print()
    
    # print("=" * 60)
    # print("🔗 ALL SOURCES")
    # print("=" * 60)
    
    # # for citation in result.citations:
    # #     print(f"[{citation.index}] {citation.title or 'Unknown'}")
    # #     print(f"    {citation.url}")
    # #     print()


    competitors = [
        {
            "name": c.name,
            "mention_count": c.mention_count,
            "cited": c.cited,
            "citation_position": c.citation_position,
            "url": c.url
        }
        for c in result.competitors_mentioned
    ]

    
    return result.answer,result.total_citations,result.cited_indices,result.target_cited,result.target_citation_position,result.cited_urls,competitors,result.competitor_urls_cited
    


# if __name__ == "__main__":
#     main()