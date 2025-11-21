from fastapi import APIRouter

from routes.AEO_tracker.models import AEOAnalysisRequest
from routes.AEO_tracker.utils import AEO_Utils

aeo_router = APIRouter(prefix="/aeo", tags=["classify"])


@aeo_router.post("/home")
async def f(request: AEOAnalysisRequest):
    email = request.email
    brand_name = request.brand_name
    target_urls = request.target_urls
    queries = request.queries
    country = request.country
    competitors = request.competitors or [] 

    # store in dynamo db
    # use claude mcp to fetch the accurate data
    # claude web search to get the reuslts
    # evaluation

    utils = AEO_Utils(brand_name, target_urls, queries,country,competitors)
    # check if brand in DB
    is_present = await utils.brand_in_db()
    if not is_present:
        # save brand data to DB
        saved_brand_data = await utils.save_brand_details()
    ans = await utils.final_eval()

    # web search

    
    return {"data": ans}




