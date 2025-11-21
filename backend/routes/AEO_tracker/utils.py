from typing_extensions import evaluate_forward_ref
from client.ai import AIClient, AIClientError
import asyncio
import boto3
from botocore.exceptions import ClientError
from collections import defaultdict
from typing import Any, Dict, List

# from client.ai import AIClient
from routes.claude_web_search.app import claude_web_search

class AEO_Utils:
    def __init__(self, brand_name, brand_url, queries,country,competitors):
        self.table_name = "aeo_brand_details"

        self.dynamodb = boto3.resource(
            "dynamodb",
            aws_access_key_id="",
            aws_secret_access_key="",
            region_name="us-west-2"
        )

        # ensure table exists before using it
        self._ensure_table_exists()
        self.table = self.dynamodb.Table(self.table_name)

        self.country = country
        self.competitors = competitors
        self.brand = brand_name
        self.url = brand_url
        self.queries = [q.strip() for q in queries.split(",")] if isinstance(queries, str) else queries


    def _ensure_table_exists(self):
        client = self.dynamodb.meta.client
        tables = client.list_tables()["TableNames"]

        if self.table_name in tables:
            print(f"✔ Table '{self.table_name}' already exists.")
            return

        print(f"⚠ Table '{self.table_name}' not found. Creating now...")

        table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {"AttributeName": "brand_name", "KeyType": "HASH"},  # PRIMARY KEY
            ],
            AttributeDefinitions=[
                {"AttributeName": "brand_name", "AttributeType": "S"},  # ONLY KEYS GO HERE
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        print("⏳ Waiting for table creation to complete...")
        table.meta.client.get_waiter("table_exists").wait(TableName=self.table_name)
        print(f"✔ Table '{self.table_name}' is ready!")


    async def brand_in_db(self) -> bool:
        try:
            response = self.table.get_item(Key={"brand_name": self.brand})
        except ClientError as e:
            print("❌ DynamoDB Error:", e)
            return False

        return "Item" in response

    
    async def save_brand_details(self):
        try:
            self.table.put_item(
                Item={
                    "brand_name": self.brand,   # PK
                    "brand_url": self.url,
                    "queries": self.queries,
                    "country": self.country,
                    "competitors": self.competitors       # DynamoDB supports list attributes
                }
            )
            print(f"✔ Saved brand '{self.brand}' to DynamoDB")
            return True

        except ClientError as e:
            print(f"❌ Error saving brand '{self.brand}':", e)
            return False

    async def get_brand_details(self):
        try:
            response = self.table.get_item(Key={"brand_name": self.brand})
            return response.get("Item", None)
        except ClientError as e:
            print("❌ Error fetching brand details:", e)
            return None

    

    # async def get_queries(self):
        
    #     return 

    
    async def web_search(self,query):   
        answer,total_citations,cited_indices,target_cited,target_citation_position,cited_urls,competitors,competitor_urls_cited = await claude_web_search(query, self.url, self.brand)     
        return {
            "answer": answer,
            "total_citations": total_citations,
            "cited_indices": cited_indices,
            "target_cited": target_cited,
            "target_citation_position": target_citation_position,
            "cited_urls": cited_urls,
            "competitors": competitors,
            "competitor_urls_cited": competitor_urls_cited
        }
    
    async def check_brand_name(self, answer: str):
        
        # Brand visibility indicator
        brand_mentions = answer.lower().count(self.brand.lower())
        
        # Brand prominence measurement
        total_words = len(answer.split())
        brand_density = (brand_mentions / total_words) * 100 if total_words > 0 else 0
        
        # Brand prominence score (0-30 points)
        prominence_score = min((brand_mentions * 5), 30)
        
        return {
            "brand_mentions": brand_mentions,
            "brand_density": brand_density,
            "prominence_score": prominence_score
        }
    
    async def analyze_competitors(self, answer: str, competitors_data: list):
        # Total words for density calculation
        total_words = len(answer.split())
        
        # Count total competitor mentions
        total_competitor_mentions = sum(
            comp["mention_count"] for comp in competitors_data
        )
        
        # Competitor density
        competitor_density = (total_competitor_mentions / total_words) * 100 if total_words > 0 else 0
        
        # Count how many competitors were cited (not just mentioned)
        competitors_cited_count = sum(1 for comp in competitors_data if comp["cited"])
        
        # Get competitor citation positions
        competitor_positions = [
            {
                "name": comp["name"],
                "position": comp["citation_position"],
                "mentions": comp["mention_count"]
            }
            for comp in competitors_data if comp["cited"]
        ]
        
        # Sort by citation position
        competitor_positions.sort(key=lambda x: x["position"] if x["position"] else 999)
        
        return {
            "total_competitor_mentions": total_competitor_mentions,
            "competitor_density": competitor_density,
            "competitors_cited_count": competitors_cited_count,
            "competitor_positions": competitor_positions,
            "competitors_detailed": competitors_data  # Full competitor data
        }
    
    async def calculate_competitive_score(
        self, 
        target_cited: bool,
        target_position: int,
        competitors_cited_count: int,
        competitor_positions: list
    ):
        if not target_cited:
            # Not cited at all - check how many competitors were cited
            return max(20 - (competitors_cited_count * 4), 0)
        
        # You're cited - calculate based on relative position
        competitors_before_you = sum(
            1 for comp in competitor_positions 
            if comp["position"] and comp["position"] < target_position
        )
        
        competitors_after_you = sum(
            1 for comp in competitor_positions 
            if comp["position"] and comp["position"] > target_position
        )
        
        # Score based on competitive position
        if competitors_before_you == 0:
            # You're cited first - maximum points
            competitive_score = 20
        elif competitors_before_you == 1:
            # One competitor before you
            competitive_score = 16
        elif competitors_before_you == 2:
            # Two competitors before you
            competitive_score = 12
        else:
            # Three or more competitors before you
            competitive_score = max(20 - (competitors_cited_count * 2), 0)
        
        return competitive_score


    # async def calculate_competitive_score(
    #     self,
    #     target_cited: bool,
    #     competitors_cited_count: int,
    # ) -> float:
 
    #     if not target_cited:
    #         return 0.0

    #     competitors = max(0, int(competitors_cited_count or 0))

    #     if competitors == 0:
    #         # We're the only one cited => strongest competitive position
    #         return 30.0
    #     elif competitors <= 2:
    #         # A few competitors, but still strong
    #         return 22.0
    #     elif competitors <= 5:
    #         # Many competitors
    #         return 12.0
    #     else:
    #         # Very crowded answer
    #         return 5.0

    async def calculate_aeo_score(self, metrics: dict) -> dict:
        """
        More conservative AEO score:
        - URL-related data only uses target_cited (bool).
        - No longer uses citation positions or per-URL position info.
        """

        target_cited = bool(metrics.get("target_cited", False))

        # --- 1) Citation score (0–30) ---
        citation_score = 30.0 if target_cited else 0.0

        # --- 2) Brand visibility score (0–40) ---
        raw_prominence = metrics.get("prominence_score", 0.0) or 0.0
        try:
            raw_prominence = float(raw_prominence)
        except (TypeError, ValueError):
            raw_prominence = 0.0

        # Normalize: support both 0–1 and 0–100 inputs
        if raw_prominence <= 1.0:
            norm_prominence = max(0.0, min(raw_prominence, 1.0))
        else:
            norm_prominence = max(0.0, min(raw_prominence, 100.0)) / 100.0

        brand_visibility_score = norm_prominence * 40.0  # 0–40

        # --- 3) Competitive score (0–30) ---
        competitive_score = await self.calculate_competitive_score(
            target_cited=target_cited,
            competitors_cited_count=metrics.get("competitors_cited_count", 0),
        )

        # --- 4) Total score & grade ---
        total_score = citation_score + brand_visibility_score + competitive_score
        total_score = min(total_score, 100.0)
        total_score = round(total_score, 1)  # optional: nicer number

        if total_score >= 92:
            grade = "A"
        elif total_score >= 80:
            grade = "B"
        elif total_score >= 65:
            grade = "C"
        elif total_score >= 50:
            grade = "D"
        else:
            grade = "F"

        return {
            "aeo_score": total_score,
            "grade": grade,
            "score_breakdown": {
                "citation": citation_score,
                "brand_visibility": brand_visibility_score,
                "competitive": competitive_score,
            },
        }

    # async def calculate_aeo_score(self, metrics: dict):
    #     # Citation score (0-60)
    #     citation_score = 0
    #     if metrics["target_cited"]:
    #         citation_score = 50
    #         if metrics["target_citation_position"] and metrics["target_citation_position"] <= 3:
    #             citation_score += 10
        
    #     # Brand visibility score (0-30)
    #     brand_visibility_score = metrics["prominence_score"]
        
    #     # Competitive score (0-20)
    #     competitive_score = await self.calculate_competitive_score(
    #         target_cited=metrics["target_cited"],
    #         target_position=metrics["target_citation_position"],
    #         competitors_cited_count=metrics["competitors_cited_count"],
    #         competitor_positions=metrics["competitor_positions"]
    #     )
        
    #     # Total score
    #     total_score = citation_score + brand_visibility_score + competitive_score
    #     total_score = min(total_score, 100)  # Cap at 100
        
    #     # Assign grade
    #     if total_score >= 90:
    #         grade = 'A'
    #     elif total_score >= 75:
    #         grade = 'B'
    #     elif total_score >= 60:
    #         grade = 'C'
    #     elif total_score >= 45:
    #         grade = 'D'
    #     else:
    #         grade = 'F'
        
    #     return {
    #         "aeo_score": total_score,
    #         "grade": grade,
    #         "score_breakdown": {
    #             "citation": citation_score,
    #             "brand_visibility": brand_visibility_score,
    #             "competitive": competitive_score
    #         }
    #     }
    
    async def evaluate(self,query):
        # Step 1: Execute web search
        web_search_data = await self.web_search(query)
        
        # Step 2: Analyze brand mentions
        brand_data = await self.check_brand_name(web_search_data["answer"])
        
        # Step 3: Analyze competitors
        competitor_data = await self.analyze_competitors(
            answer=web_search_data["answer"],
            competitors_data=web_search_data["competitors"]
        )
        
        # Step 4: Combine metrics for scoring
        combined_metrics = {
            **web_search_data,
            **brand_data,
            **competitor_data
        }
        
        # Step 5: Calculate AEO score
        scoring_data = await self.calculate_aeo_score(combined_metrics)
        
        # Step 6: Build final report
        return {
            # Core answer
            "answer": web_search_data["answer"],
            "query": query,
            
            # Citation metrics
            "total_citations": web_search_data["total_citations"],
            "cited_indices": web_search_data["cited_indices"],
            "target_cited": web_search_data["target_cited"],
            "target_citation_position": web_search_data["target_citation_position"],
            "cited_urls": web_search_data["cited_urls"],
            
            # Brand visibility metrics
            "brand_mentions": brand_data["brand_mentions"],
            "brand_density": brand_data["brand_density"],
            "prominence_score": brand_data["prominence_score"],
            
            # Competitor metrics
            "competitor_density": competitor_data["competitor_density"],
            "competitors_cited_count": competitor_data["competitors_cited_count"],
            "competitor_positions": competitor_data["competitor_positions"],
            "competitors_detailed": competitor_data["competitors_detailed"],
            "competitor_urls_cited": web_search_data["competitor_urls_cited"],
            
            # Scoring
            "aeo_score": scoring_data["aeo_score"],
            "grade": scoring_data["grade"],
            "score_breakdown": scoring_data["score_breakdown"],
            
            # Metadata
            "brand": self.brand,
            "target_url": self.url
        }







    async def aggregate_aeo_results(self,query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate per-query AEO results to a brand-level summary.

        query_results: list of dicts
        """

        if not query_results:
            return {
                "brand": None,
                "total_queries": 0,
                "overall_aeo_score": 0.0,
                "overall_grade": "F",
                "scores": {},
                "citations": {},
                "mentions": {},
                "grade_distribution": {},
            }

        # Normalize to inner "data" dict
        rows = []
        for item in query_results:
            if "data" in item and isinstance(item["data"], dict):
                rows.append(item["data"])
            else:
                rows.append(item)

        total_queries = len(rows)
        brand_name = rows[0].get("brand")

        # --- accumulators ---
        sum_aeo = 0.0
        sum_citation_score = 0.0
        sum_brand_visibility_score = 0.0
        sum_competitive_score = 0.0

        sum_total_citations = 0
        sum_competitors_cited = 0

        sum_brand_mentions = 0
        sum_competitor_mentions = 0

        sum_brand_density = 0.0
        sum_competitor_density = 0.0

        target_cited_count = 0
        brand_mentioned_query_count = 0
        competitor_mentioned_query_count = 0

        grade_counts = defaultdict(int)
        competitor_mention_totals = defaultdict(int)

        for row in rows:
            aeo_score = float(row.get("aeo_score", 0.0) or 0.0)
            sum_aeo += aeo_score

            # score_breakdown might be missing or partial
            bd = row.get("score_breakdown", {}) or {}
            citation_score = float(bd.get("citation", 0.0) or 0.0)
            brand_vis_score = float(bd.get("brand_visibility", 0.0) or 0.0)
            competitive_score = float(bd.get("competitive", 0.0) or 0.0)

            sum_citation_score += citation_score
            sum_brand_visibility_score += brand_vis_score
            sum_competitive_score += competitive_score

            # citations
            total_citations = int(row.get("total_citations", 0) or 0)
            sum_total_citations += total_citations

            competitors_cited_count = int(row.get("competitors_cited_count", 0) or 0)
            sum_competitors_cited += competitors_cited_count

            if row.get("target_cited"):
                target_cited_count += 1

            # mentions
            brand_mentions = int(row.get("brand_mentions", 0) or 0)
            sum_brand_mentions += brand_mentions
            if brand_mentions > 0:
                brand_mentioned_query_count += 1

            competitor_density = float(row.get("competitor_density", 0.0) or 0.0)
            brand_density = float(row.get("brand_density", 0.0) or 0.0)
            sum_brand_density += brand_density
            sum_competitor_density += competitor_density

            # competitors_detailed
            competitors_detailed = row.get("competitors_detailed") or []
            any_competitor_mentioned = False
            for c in competitors_detailed:
                name = c.get("name")
                mention_count = int(c.get("mention_count", 0) or 0)
                if name and mention_count > 0:
                    competitor_mention_totals[name] += mention_count
                    sum_competitor_mentions += mention_count
                    any_competitor_mentioned = True

            if any_competitor_mentioned:
                competitor_mentioned_query_count += 1

            # grade distribution
            grade = (row.get("grade") or "F").upper()
            grade_counts[grade] += 1

        # --- averages ---
        def safe_avg(total, n):
            return total / n if n > 0 else 0.0

        avg_aeo = safe_avg(sum_aeo, total_queries)
        avg_citation_score = safe_avg(sum_citation_score, total_queries)
        avg_brand_visibility_score = safe_avg(sum_brand_visibility_score, total_queries)
        avg_competitive_score = safe_avg(sum_competitive_score, total_queries)

        avg_total_citations = safe_avg(sum_total_citations, total_queries)
        avg_competitors_cited = safe_avg(sum_competitors_cited, total_queries)

        avg_brand_density = safe_avg(sum_brand_density, total_queries)
        avg_competitor_density = safe_avg(sum_competitor_density, total_queries)

        # --- rates & shares ---
        citation_rate = target_cited_count / total_queries
        brand_mentioned_rate = brand_mentioned_query_count / total_queries
        competitor_mentioned_rate = competitor_mentioned_query_count / total_queries

        total_mentions = sum_brand_mentions + sum_competitor_mentions
        if total_mentions > 0:
            brand_mention_share = sum_brand_mentions / total_mentions
            competitor_mention_share = sum_competitor_mentions / total_mentions
        else:
            brand_mention_share = 0.0
            competitor_mention_share = 0.0

        # top competitors
        top_competitors = []
        for name, mcount in sorted(
            competitor_mention_totals.items(),
            key=lambda kv: kv[1],
            reverse=True,
        ):
            share = mcount / sum_competitor_mentions if sum_competitor_mentions > 0 else 0.0
            top_competitors.append(
                {
                    "name": name,
                    "total_mentions": mcount,
                    "share_of_competitor_mentions": share,
                }
            )

        # overall grade
        if avg_aeo >= 92:
            overall_grade = "A"
        elif avg_aeo >= 80:
            overall_grade = "B"
        elif avg_aeo >= 65:
            overall_grade = "C"
        elif avg_aeo >= 50:
            overall_grade = "D"
        else:
            overall_grade = "F"

        # RETURN RESULT
        return {
            "brand": brand_name,
            "total_queries": total_queries,
            "overall_aeo_score": round(avg_aeo, 1),
            "overall_grade": overall_grade,
            "scores": {
                "aeo": {
                    "avg": round(avg_aeo, 1),
                    "min": min(r.get("aeo_score", 0.0) or 0.0 for r in rows),
                    "max": max(r.get("aeo_score", 0.0) or 0.0 for r in rows),
                },
                "citation": {"avg": round(avg_citation_score, 1)},
                "brand_visibility": {"avg": round(avg_brand_visibility_score, 1)},
                "competitive": {"avg": round(avg_competitive_score, 1)},
            },
            "citations": {
                "target_citation_rate": citation_rate,
                "avg_total_citations_per_query": avg_total_citations,
                "avg_competitors_cited_per_query": avg_competitors_cited,
            },
            "mentions": {
                "total_brand_mentions": sum_brand_mentions,
                "total_competitor_mentions": sum_competitor_mentions,
                "brand_mention_share": brand_mention_share,
                "competitor_mention_share": competitor_mention_share,
                "brand_mentioned_query_rate": brand_mentioned_rate,
                "competitor_mentioned_query_rate": competitor_mentioned_rate,
                "avg_brand_density": avg_brand_density,
                "avg_competitor_density": avg_competitor_density,
                "top_competitors_by_mentions": top_competitors,
            },
            "grade_distribution": dict(grade_counts),
        }


    async def final_eval(self):
        query_results = []
        for q in self.queries:
            data = await self.evaluate(q)
            query_results.append(data)
        report = self.aggregate_aeo_results(query_results)
        return report

  
#     async def web_search(self):
#         answer, total_citations, cited_indices, target_cited, target_citation_position = await claude_web_search(self.brand, self.url, self.queries)
#         return answer, total_citations, cited_indices, target_cited, target_citation_position

    
    
#     async def check_brand_name(self,answer):
#         # Brand visibility indicator
#         brand_mentions = answer.lower().count(self.brand.lower())
#         # Brand prominence measurement
#         total_words = len(answer.split())
#         brand_density = (brand_mentions / total_words) * 100
#         prominence_score = min((brand_mentions*5), 30) 
#         # competitor
#         competitors = ["Monday.com", "ClickUp", "Notion"]
#         competitor_counts = {
#             comp: answer.lower().count(comp.lower())
#             for comp in competitors
#         }
#         total_competitor_mentions = sum(competitor_counts.values())
#         competitor_density = (total_competitor_mentions / total_words) * 100

             
#         return brand_mentions, brand_density, competitor_density, prominence_score

#     # async def checck_brand_name(self, )
#     # brand name mention count, 

#     # evaluate
#     async def evaluate(self):
#         answer, total_citations, cited_indices, target_cited, target_citation_position = await self.web_search()
#         brand_mentions, brand_density, competitor_dencity, prominence_score = await self.check_brand_name(answer)
        
#         return {
#         "answer": answer,
#         "total_citations": total_citations,
#         "cited_indices": cited_indices,
#         "target_cited": target_cited,
#         "target_citation_position": target_citation_position,
#         "brand_mentions": brand_mentions,
#         "brand_density": brand_density,
#         "competitor_density": competitor_dencity,
#         "prominence_score": prominence_score
#     }






