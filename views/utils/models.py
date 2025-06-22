from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from enum import Enum

# --- Enums for valid value constraints ---
# You can expand these Enums with the full list of values from your knowledge graphs.

class VenueType(str, Enum):
    mansion = "Mansion"
    ballroom = "Ballroom"
    garden = "Garden"
    loft = "Loft"
    urban_winery = "Urban Winery"
    historic_estate = "Historic Estate"
    hotel = "Hotel"
    inn = "Inn"
    resort = "Resort"
    banquet_hall = "Banquet Hall"
    industrial_space = "Industrial Space"
    vineyard = "Vineyard"
    winery = "Winery"
    farm = "Farm"
    barn = "Barn"
    ranch = "Ranch"
    park = "Park"
    lodge = "Lodge"
    retreat = "Retreat"
    event_venue = "Event Venue"
    restaurant = "Restaurant"
    brewery = "Brewery"
    urban = "Urban"
    beach = "Beach"
    golf_and_country_club = "Golf and Country Club"
    urban_location = "Urban Location"

class Atmosphere(str, Enum):
    indoor = "Indoor"
    outdoor = "Outdoor"
    rustic_chic = "Rustic Chic"

class VenueService(str, Enum):
    bar_services = "Bar services"
    catering_services = "Catering services"
    clean_up = "Clean up"
    dance_floor = "Dance floor"
    event_planning = "Event planning"
    florals = "Florals"
    decor = "Decor"
    spa = "Spa"
    bridal_studio = "Bridal studio"
    group_lodging_specialist = "Group lodging specialist"
    culinary_and_confection_professionals = "Culinary and confection professionals"
    dressing_room_bridal_suite = "Dressing room / Bridal Suite"
    event_coordinator = "Event coordinator"
    event_rentals = "Event rentals"
    event_staff = "Event staff"
    liability_insurance = "Liability insurance"
    lighting_sound = "Lighting/Sound"
    pet_friendly = "Pet friendly"
    on_site_accommodations = "On-site accommodations"
    service_staff = "Service staff"
    set_up = "Set up"
    wedding_cake_services = "Wedding cake services"
    wifi = "Wifi"
    wheelchair_accessible = "Wheelchair accessible"
    transportation_access = "Transportation & access"
    self_parking_free = "Self parking - free"
    catering = "Catering"
    photography = "Photography"
    dj = "DJ"
    cake = "Cake"
    personal_florals = "Personal Florals"
    event_management_day_of_coordination = "Event Management & Day of Coordination"

class CateringService(str, Enum):
    bartenders = "Bartenders"
    cleanup_breakdown = "Cleanup and breakdown"
    tastings = "Consultations and tastings"
    complimentary_tastings = "Consultations and tastings - complimentary"
    delivery_setup = "Delivery and setup"
    event_planner = "Event planner"
    rental_coordination = "Rental coordination - directly invoice couple"
    serving_staff = "Serving staff"
    full_service_event_planning = "Full service event planning"
    chef_services = "Chef services"
    logistical_services = "Logistical services"
    day_of_coordination = "Day/of coordination"
    securing_rentals = "Securing rentals"
    catering = "Catering"

class Cuisine(str, Enum):
    pan_asian = "Pan-Asian"
    pan_european = "Pan-European"
    southern = "Southern"
    latin_american = "Latin American"
    american = "American"
    bbq = "BBQ"
    italian = "Italian"

class DietaryOption(str, Enum):
    dairy_free = "Dairy-free"
    gluten_free = "Gluten-free"
    nut_free = "Nut-free"
    vegan = "Vegan"
    vegetarian = "Vegetarian"

class MealType(str, Enum):
    buffet = "Buffet"
    dessert_service = "Dessert service"
    family_style_meal = "Family-style meal"
    plated = "Plated"
    food_stations = "Food stations"
    passed_appetizers = "Passed appetizers"
    seated_meal = "Seated meal"
    stationary_appetizers = "Stationary appetizers"
    wedding_cake_service = "Wedding cake service"

class DecorServiceLevel(str, Enum):
    a_la_carte = "A La Carte"
    full_service = "Full-Service Floral Design"

class FloralArrangement(str, Enum):
    bouquets = "Bouquets"
    centerpieces = "Centerpieces"
    ceremony_decor = "Ceremony decor"

# --- Pydantic Models ---

class VenuePrice(BaseModel):
    space_rental: Optional[int] = None
    per_person: Optional[int] = None
    other: List[Any] = []

class Venue(BaseModel):
    obligatorios_venue: Optional[List[str]] = Field(None, exclude=True) # Exclude from schema/output
    budget: Optional[str] = Field(None, alias="venue_budget", description="Part of the general budget destined to the venue")
    type: Optional[VenueType] = Field(None, alias="venue_type", description="Type of venue")
    location: Optional[str] = None
    price: Optional[VenuePrice] = Field(None, alias="venue_price")
    atmosphere: Optional[List[Atmosphere]] = None
    services: Optional[List[VenueService]] = Field(None, alias="venue_services")
    restrictions: Optional[Union[str, List[str]]] = Field(None, alias="venue_restrictions")
    supported_events: Optional[List[str]] = None
    other: Optional[Dict[str, Any]] = Field(None, alias="other_venue")

class CateringPrice(BaseModel):
    food: Optional[str] = None
    bar_services: Optional[str] = None

class Catering(BaseModel):
    obligatorios_catering: Optional[List[str]] = Field(None, exclude=True)
    budget: Optional[str] = Field(None, alias="catering_budget")
    services: Optional[List[CateringService]] = Field(None, alias="catering_services")
    ubication: Optional[str] = Field(None, alias="catering_ubication")
    price: Optional[CateringPrice] = Field(None, alias="catering_price")
    cuisines: Optional[List[Cuisine]] = None
    dietary_options: Optional[List[DietaryOption]] = None
    meal_types: Optional[List[MealType]] = None
    beverage_services: Optional[List[str]] = None
    drink_types: Optional[List[str]] = None
    restrictions: Optional[List[str]] = Field(None, alias="catering_restrictions")
    other: Optional[Dict[str, Any]] = Field(None, alias="other_catering")

class DecorPrice(BaseModel):
    bouquets: Optional[str] = None
    centerpieces: Optional[str] = None
    minimum_spend: Optional[str] = None

class Decor(BaseModel):
    obligatorios_decor: Optional[List[str]] = Field(None, exclude=True)
    budget: Optional[str] = Field(None, alias="decor_budget")
    service_levels: Optional[List[DecorServiceLevel]] = Field(None, alias="decor_service_levels")
    pre_wedding_services: Optional[List[str]] = None
    post_wedding_services: Optional[List[str]] = None
    day_of_services: Optional[List[str]] = None
    arrangement_styles: Optional[List[str]] = None
    floral_arrangements: Optional[List[FloralArrangement]] = None
    restrictions: Optional[Union[str, List[str]]] = Field(None, alias="restrictions_decor")
    price: Optional[Union[DecorPrice, str]] = Field(None, alias="decor_price")
    ubication: Optional[str] = Field(None, alias="decor_ubication")
    other: Optional[Dict[str, Any]] = Field(None, alias="other_decor")

class Criterios(BaseModel):
    presupuesto: Optional[int] = Field(None, alias="presupuesto_total", description="Total budget for the event")
    guest_count: Optional[int] = Field(None, alias="guest_count_general", description="Number of guests")
    style: Optional[str] = Field(None, alias="general_style", description="Event style (e.g., luxury, classic, etc.)")
    venue: Optional[Venue] = None
    catering: Optional[Catering] = None
    decor: Optional[Decor] = None

class ResponseModel(BaseModel):
    criterios: Criterios

    class Config:
        populate_by_name = True 