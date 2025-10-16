# restaurant_agent.py - Gets restaurants from user's EXACT browser location
import requests
import urllib.parse
from typing import Dict, List, Optional

SWIGGY_API_BASE = "https://www.swiggy.com/dapi"

def get_nearby_restaurants(
    lat: float, 
    lng: float, 
    cuisines: Optional[List[str]] = None, 
    radius_m: int = 3000, 
    limit: int = 7  # Changed from 30 to 7
) -> Dict:
    """
    Get nearby restaurants from Swiggy's LIVE API
    Uses exact coordinates from browser geolocation
    Returns ALL restaurants, then ranks by user preferences
    """
    try:
        swiggy_url = f"{SWIGGY_API_BASE}/restaurants/list/v5"
        
        params = {
            'lat': lat,
            'lng': lng,
            'is-seo-homepage-enabled': 'true',
            'page_type': 'DESKTOP_WEB_LISTING'
        }
        
        print(f"🔍 Searching restaurants at exact location ({lat}, {lng})...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.swiggy.com/',
            'Origin': 'https://www.swiggy.com',
        }
        
        response = requests.get(swiggy_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        all_restaurants = []
        cards = data.get('data', {}).get('cards', [])
        
        for card in cards:
            card_data = card.get('card', {}).get('card', {})
            card_type = card_data.get('@type', '')
            
            if 'GridWidget' in card_type or 'Restaurant' in card_type:
                grid_elements = card_data.get('gridElements', {}).get('infoWithStyle', {})
                restaurant_list = grid_elements.get('restaurants', [])
                
                if not restaurant_list:
                    restaurant_list = grid_elements.get('info', [])
                
                for restaurant_data in restaurant_list:
                    info = restaurant_data.get('info', {})
                    
                    if not info or not info.get('name'):
                        continue
                    
                    restaurant_id = str(info.get('id', ''))
                    name = info.get('name', '')
                    cuisines_list = info.get('cuisines', [])
                    area = info.get('areaName', '')
                    locality = info.get('locality', '')
                    city = info.get('city', 'bangalore').lower()
                    rating = info.get('avgRating', 0)
                    cost_for_two = info.get('costForTwo', 'N/A')
                    
                    sla_info = info.get('sla', {})
                    delivery_time = sla_info.get('deliveryTime', 0)
                    
                    rest_lat = info.get('lat') or lat
                    rest_lng = info.get('lng') or lng
                    
                    cta = restaurant_data.get('cta', {})
                    swiggy_url = cta.get('link', '')
                    
                    if not swiggy_url or not swiggy_url.startswith('http'):
                        city_slug = city.replace(' ', '-')
                        name_slug = name.lower().replace(' ', '-').replace("'", '').replace(',', '').replace('&', 'and').replace('.', '')
                        area_slug = (locality or area).lower().replace(' ', '-').replace(',', '').replace('.', '')
                        swiggy_url = f"https://www.swiggy.com/city/{city_slug}/{name_slug}-{area_slug}-rest{restaurant_id}"
                    
                    encoded_name = urllib.parse.quote_plus(name)
                    
                    restaurant = {
                        "id": restaurant_id,
                        "name": name,
                        "cuisines": cuisines_list[:4],
                        "area": area or locality,
                        "address": f"{locality}, {area}" if locality and area else (locality or area),
                        "city": city.title(),
                        "lat": rest_lat,
                        "lng": rest_lng,
                        "rating": rating,
                        "cost_for_two": cost_for_two,
                        "delivery_time": f"{delivery_time} mins" if delivery_time else "N/A",
                        "swiggy_url": swiggy_url,
                        "swiggy_search_url": f"https://www.swiggy.com/search?query={encoded_name}",
                        "zomato_search_url": f"https://www.zomato.com/search?q={encoded_name}",
                        "types": cuisines_list[:3],
                        "source": "swiggy_live_api",
                        "link_confidence": "high"
                    }
                    
                    # Calculate preference match score
                    if cuisines:
                        cuisine_text = ' '.join(cuisines_list).lower()
                        exact_matches = sum(1 for pref in cuisines if pref.lower() in cuisine_text)
                        partial_matches = sum(1 for pref in cuisines 
                                            for cuisine in cuisines_list 
                                            if pref.lower() in cuisine.lower())
                        preference_score = (exact_matches * 3) + partial_matches + (rating * 0.5)
                        restaurant['preference_score'] = preference_score
                        restaurant['exact_matches'] = exact_matches
                    else:
                        restaurant['preference_score'] = rating
                        restaurant['exact_matches'] = 0
                    
                    all_restaurants.append(restaurant)
                    
                    if len(all_restaurants) >= 100:
                        break
            
            if len(all_restaurants) >= 100:
                break
        
        # Sort by preference score (high to low), then by rating
        all_restaurants.sort(key=lambda x: (x['preference_score'], x['rating']), reverse=True)
        
        # Return top restaurants
        top_restaurants = all_restaurants[:limit]
        
        print(f"✅ Found {len(all_restaurants)} total restaurants")
        print(f"🎯 Returning top {len(top_restaurants)} by preference match")
        
        return {
            "restaurants": top_restaurants,
            "success": True,
            "user_location": {"lat": lat, "lng": lng},
            "total_found": len(all_restaurants)
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            "restaurants": [], 
            "error": str(e), 
            "success": False
        }
