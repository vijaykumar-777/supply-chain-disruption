"""
ATLAS AI — Realistic Supply Chain Graph Seeder
Populates Neo4j with 100+ nodes and 150+ routes across a global supply chain network.
Covers: Suppliers, Factories, Warehouses, Distribution Centers, Ports, Locations.

Run: python3 scripts/seed_graph.py
"""
import sys
import os
import uuid
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.graph.neo4j_client import Neo4jClient

# ─── Node Data: 100+ realistic global supply chain nodes ─────────────────────

SUPPLIERS = [
    {"id": "SUP_TSMC", "name": "TSMC", "country": "Taiwan", "lat": 24.7736, "lon": 120.9820, "category": "Semiconductor"},
    {"id": "SUP_SAMSUNG_SEMI", "name": "Samsung Semiconductor", "country": "South Korea", "lat": 37.2636, "lon": 127.0286, "category": "Semiconductor"},
    {"id": "SUP_INTEL_CHANDLER", "name": "Intel Chandler Fab", "country": "USA", "lat": 33.3062, "lon": -111.8413, "category": "Semiconductor"},
    {"id": "SUP_SK_HYNIX", "name": "SK Hynix", "country": "South Korea", "lat": 37.4049, "lon": 127.1120, "category": "Memory"},
    {"id": "SUP_MICRON", "name": "Micron Technology", "country": "USA", "lat": 43.6150, "lon": -116.2023, "category": "Memory"},
    {"id": "SUP_BOSCH_STUTT", "name": "Bosch Stuttgart", "country": "Germany", "lat": 48.7758, "lon": 9.1829, "category": "Automotive Parts"},
    {"id": "SUP_DENSO", "name": "Denso Corporation", "country": "Japan", "lat": 34.8833, "lon": 137.1500, "category": "Automotive Parts"},
    {"id": "SUP_CONTINENTAL", "name": "Continental AG", "country": "Germany", "lat": 52.3759, "lon": 9.7320, "category": "Automotive Parts"},
    {"id": "SUP_CATL", "name": "CATL Battery", "country": "China", "lat": 26.6539, "lon": 119.3038, "category": "EV Batteries"},
    {"id": "SUP_LG_ENERGY", "name": "LG Energy Solution", "country": "South Korea", "lat": 36.3504, "lon": 127.3845, "category": "EV Batteries"},
    {"id": "SUP_PANASONIC_BAT", "name": "Panasonic Energy", "country": "Japan", "lat": 34.6937, "lon": 135.5023, "category": "EV Batteries"},
    {"id": "SUP_BHP", "name": "BHP Mining", "country": "Australia", "lat": -31.9505, "lon": 115.8605, "category": "Raw Materials"},
    {"id": "SUP_VALE", "name": "Vale S.A.", "country": "Brazil", "lat": -20.2976, "lon": -40.2958, "category": "Raw Materials"},
    {"id": "SUP_RIO_TINTO", "name": "Rio Tinto", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "category": "Raw Materials"},
    {"id": "SUP_BASF", "name": "BASF Ludwigshafen", "country": "Germany", "lat": 49.4774, "lon": 8.4452, "category": "Chemicals"},
    {"id": "SUP_DOW", "name": "Dow Chemical Midland", "country": "USA", "lat": 43.6156, "lon": -84.2472, "category": "Chemicals"},
    {"id": "SUP_CORNING", "name": "Corning Glass", "country": "USA", "lat": 42.1428, "lon": -77.0547, "category": "Display Glass"},
    {"id": "SUP_MURATA", "name": "Murata Manufacturing", "country": "Japan", "lat": 35.0116, "lon": 135.7681, "category": "Passive Components"},
    {"id": "SUP_TDK", "name": "TDK Corporation", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "category": "Passive Components"},
    {"id": "SUP_FOXCONN_MAT", "name": "Foxconn Materials", "country": "Taiwan", "lat": 25.0330, "lon": 121.5654, "category": "PCB Assembly"},
]

FACTORIES = [
    {"id": "FAC_FOXCONN_SZ", "name": "Foxconn Shenzhen", "country": "China", "lat": 22.5431, "lon": 114.0579, "category": "Electronics Assembly"},
    {"id": "FAC_FOXCONN_ZZ", "name": "Foxconn Zhengzhou", "country": "China", "lat": 34.7466, "lon": 113.6253, "category": "Electronics Assembly"},
    {"id": "FAC_PEGATRON", "name": "Pegatron Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737, "category": "Electronics Assembly"},
    {"id": "FAC_FLEX_ZH", "name": "Flex Zhuhai", "country": "China", "lat": 22.2710, "lon": 113.5767, "category": "Electronics Assembly"},
    {"id": "FAC_SAMSUNG_VN", "name": "Samsung Vietnam Factory", "country": "Vietnam", "lat": 21.1833, "lon": 106.0667, "category": "Electronics Assembly"},
    {"id": "FAC_TESLA_SHANG", "name": "Tesla Gigafactory Shanghai", "country": "China", "lat": 31.0975, "lon": 121.7782, "category": "EV Manufacturing"},
    {"id": "FAC_TESLA_BERLIN", "name": "Tesla Gigafactory Berlin", "country": "Germany", "lat": 52.3939, "lon": 13.7886, "category": "EV Manufacturing"},
    {"id": "FAC_TESLA_AUSTIN", "name": "Tesla Gigafactory Austin", "country": "USA", "lat": 30.2212, "lon": -97.6208, "category": "EV Manufacturing"},
    {"id": "FAC_TOYOTA_AICHI", "name": "Toyota Motomachi Plant", "country": "Japan", "lat": 35.0851, "lon": 137.1443, "category": "Automotive"},
    {"id": "FAC_BMW_MUNICH", "name": "BMW Munich Plant", "country": "Germany", "lat": 48.1771, "lon": 11.5564, "category": "Automotive"},
    {"id": "FAC_VW_WOLFSBURG", "name": "Volkswagen Wolfsburg", "country": "Germany", "lat": 52.4227, "lon": 10.7865, "category": "Automotive"},
    {"id": "FAC_HYUNDAI_ULSAN", "name": "Hyundai Ulsan Plant", "country": "South Korea", "lat": 35.5384, "lon": 129.3114, "category": "Automotive"},
    {"id": "FAC_APPLE_CORK", "name": "Apple Cork Campus", "country": "Ireland", "lat": 51.8985, "lon": -8.4756, "category": "Tech Operations"},
    {"id": "FAC_NVIDIA_TW", "name": "NVIDIA Taiwan Design Center", "country": "Taiwan", "lat": 24.9914, "lon": 121.5419, "category": "GPU Design"},
    {"id": "FAC_JABIL_PENANG", "name": "Jabil Penang", "country": "Malaysia", "lat": 5.4141, "lon": 100.3288, "category": "Contract Manufacturing"},
    {"id": "FAC_WISTRON_BANG", "name": "Wistron Bangalore", "country": "India", "lat": 12.9716, "lon": 77.5946, "category": "Electronics Assembly"},
]

PORTS = [
    {"id": "PORT_SHANGHAI", "name": "Port of Shanghai", "country": "China", "lat": 31.3552, "lon": 121.5048, "capacity_teu": 47000000},
    {"id": "PORT_SINGAPORE", "name": "Port of Singapore", "country": "Singapore", "lat": 1.2644, "lon": 103.8200, "capacity_teu": 37200000},
    {"id": "PORT_SHENZHEN", "name": "Port of Shenzhen", "country": "China", "lat": 22.4810, "lon": 114.0300, "capacity_teu": 28800000},
    {"id": "PORT_NINGBO", "name": "Port of Ningbo-Zhoushan", "country": "China", "lat": 29.8683, "lon": 121.5440, "capacity_teu": 31100000},
    {"id": "PORT_BUSAN", "name": "Port of Busan", "country": "South Korea", "lat": 35.1028, "lon": 129.0300, "capacity_teu": 22700000},
    {"id": "PORT_HONG_KONG", "name": "Port of Hong Kong", "country": "China", "lat": 22.2988, "lon": 114.1694, "capacity_teu": 17900000},
    {"id": "PORT_ROTTERDAM", "name": "Port of Rotterdam", "country": "Netherlands", "lat": 51.9036, "lon": 4.3901, "capacity_teu": 14500000},
    {"id": "PORT_HAMBURG", "name": "Port of Hamburg", "country": "Germany", "lat": 53.5333, "lon": 9.9833, "capacity_teu": 8700000},
    {"id": "PORT_ANTWERP", "name": "Port of Antwerp-Bruges", "country": "Belgium", "lat": 51.2324, "lon": 4.3990, "capacity_teu": 13500000},
    {"id": "PORT_LA", "name": "Port of Los Angeles", "country": "USA", "lat": 33.7405, "lon": -118.2700, "capacity_teu": 9600000},
    {"id": "PORT_LONG_BEACH", "name": "Port of Long Beach", "country": "USA", "lat": 33.7546, "lon": -118.2149, "capacity_teu": 9100000},
    {"id": "PORT_DUBAI", "name": "Jebel Ali Port", "country": "UAE", "lat": 25.0054, "lon": 55.0607, "capacity_teu": 15400000},
    {"id": "PORT_MUMBAI", "name": "Jawaharlal Nehru Port", "country": "India", "lat": 18.9490, "lon": 72.9510, "capacity_teu": 5700000},
    {"id": "PORT_SAVANNAH", "name": "Port of Savannah", "country": "USA", "lat": 32.0809, "lon": -81.0678, "capacity_teu": 5800000},
    {"id": "PORT_FELIXSTOWE", "name": "Port of Felixstowe", "country": "UK", "lat": 51.9559, "lon": 1.3307, "capacity_teu": 3800000},
    {"id": "PORT_TANJUNG", "name": "Port Klang", "country": "Malaysia", "lat": 3.0038, "lon": 101.3928, "capacity_teu": 14100000},
    {"id": "PORT_LAEM_CHAB", "name": "Laem Chabang Port", "country": "Thailand", "lat": 13.0778, "lon": 100.8851, "capacity_teu": 8900000},
    {"id": "PORT_YOKOHAMA", "name": "Port of Yokohama", "country": "Japan", "lat": 35.4437, "lon": 139.6380, "capacity_teu": 2900000},
    {"id": "PORT_SANTOS", "name": "Port of Santos", "country": "Brazil", "lat": -23.9544, "lon": -46.3088, "capacity_teu": 4300000},
    {"id": "PORT_PIRAEUS", "name": "Port of Piraeus", "country": "Greece", "lat": 37.9430, "lon": 23.6469, "capacity_teu": 5400000},
]

WAREHOUSES = [
    {"id": "WH_AMAZON_KY", "name": "Amazon CVG Hub", "country": "USA", "lat": 38.8943, "lon": -84.6001, "capacity_sqft": 3800000},
    {"id": "WH_AMAZON_UK", "name": "Amazon Tilbury FC", "country": "UK", "lat": 51.4610, "lon": 0.3600, "capacity_sqft": 2200000},
    {"id": "WH_DHL_LEIP", "name": "DHL Leipzig Hub", "country": "Germany", "lat": 51.4236, "lon": 12.2245, "capacity_sqft": 1500000},
    {"id": "WH_FEDEX_MEMPHIS", "name": "FedEx Super Hub Memphis", "country": "USA", "lat": 35.0424, "lon": -89.9767, "capacity_sqft": 4200000},
    {"id": "WH_UPS_LOUISVILLE", "name": "UPS Worldport Louisville", "country": "USA", "lat": 38.1781, "lon": -85.7272, "capacity_sqft": 5200000},
    {"id": "WH_MAERSK_ROTT", "name": "Maersk Rotterdam DC", "country": "Netherlands", "lat": 51.9144, "lon": 4.4120, "capacity_sqft": 1800000},
    {"id": "WH_COSCO_SHANG", "name": "COSCO Shanghai Logistics", "country": "China", "lat": 31.2784, "lon": 121.4879, "capacity_sqft": 2100000},
    {"id": "WH_CMA_MARSEILLE", "name": "CMA CGM Marseille DC", "country": "France", "lat": 43.3528, "lon": 5.4300, "capacity_sqft": 900000},
    {"id": "WH_CEVA_SING", "name": "CEVA Singapore Hub", "country": "Singapore", "lat": 1.3340, "lon": 103.7115, "capacity_sqft": 1100000},
    {"id": "WH_DB_SCHENKER_MUC", "name": "DB Schenker Munich", "country": "Germany", "lat": 48.3537, "lon": 11.7861, "capacity_sqft": 750000},
]

DISTRIBUTION_CENTERS = [
    {"id": "DC_APPLE_SHENZ", "name": "Apple Shenzhen Dist.", "country": "China", "lat": 22.5800, "lon": 114.0700, "category": "Consumer Electronics"},
    {"id": "DC_WALMART_BENTON", "name": "Walmart Bentonville DC", "country": "USA", "lat": 36.3729, "lon": -94.2088, "category": "Retail"},
    {"id": "DC_ZARA_ARTEIJO", "name": "Zara Arteixo DC", "country": "Spain", "lat": 43.3040, "lon": -8.5100, "category": "Fast Fashion"},
    {"id": "DC_TOYOTA_NAGOYA", "name": "Toyota Nagoya Parts DC", "country": "Japan", "lat": 35.1815, "lon": 136.9066, "category": "Automotive Parts"},
    {"id": "DC_BOSCH_BAMBERG", "name": "Bosch Bamberg DC", "country": "Germany", "lat": 49.8988, "lon": 10.9028, "category": "Industrial"},
    {"id": "DC_SAMSUNG_SUWON", "name": "Samsung Suwon DC", "country": "South Korea", "lat": 37.2636, "lon": 127.0286, "category": "Consumer Electronics"},
    {"id": "DC_NIKE_LAAKDAL", "name": "Nike European DC", "country": "Belgium", "lat": 51.0850, "lon": 5.0000, "category": "Apparel"},
    {"id": "DC_ALIBABA_HANGZ", "name": "Cainiao Hangzhou Hub", "country": "China", "lat": 30.2741, "lon": 120.1551, "category": "E-Commerce"},
    {"id": "DC_COSTCO_TRACY", "name": "Costco Tracy DC", "country": "USA", "lat": 37.7397, "lon": -121.4252, "category": "Retail"},
    {"id": "DC_IKEA_ALMHULT", "name": "IKEA Almhult DC", "country": "Sweden", "lat": 56.5512, "lon": 14.1359, "category": "Furniture"},
]

LOCATIONS = [
    {"id": "LOC_SUEZ_CANAL", "name": "Suez Canal", "country": "Egypt", "lat": 30.4575, "lon": 32.3499},
    {"id": "LOC_PANAMA_CANAL", "name": "Panama Canal", "country": "Panama", "lat": 9.0800, "lon": -79.6800},
    {"id": "LOC_STRAIT_MALACCA", "name": "Strait of Malacca", "country": "Malaysia", "lat": 2.5000, "lon": 101.5000},
    {"id": "LOC_STRAIT_HORMUZ", "name": "Strait of Hormuz", "country": "Iran", "lat": 26.5667, "lon": 56.2500},
    {"id": "LOC_CAPE_GOOD_HOPE", "name": "Cape of Good Hope", "country": "South Africa", "lat": -34.3568, "lon": 18.4740},
]

EVENTS = [
    {"title": "Typhoon Approaching South China Sea", "category": "WEATHER", "severity": 0.92, "locations": ["Port of Shenzhen", "Port of Hong Kong"]},
    {"title": "Suez Canal Vessel Grounding", "category": "LOGISTICS", "severity": 0.88, "locations": ["Suez Canal"]},
    {"title": "Shanghai COVID Lockdown Restrictions", "category": "PANDEMIC", "severity": 0.75, "locations": ["Port of Shanghai", "Foxconn Shenzhen"]},
    {"title": "EU Carbon Border Adjustment Mechanism", "category": "REGULATORY", "severity": 0.45, "locations": ["Port of Rotterdam", "Port of Hamburg", "Port of Antwerp-Bruges"]},
    {"title": "Semiconductor Fab Fire — Samsung", "category": "INDUSTRIAL_ACCIDENT", "severity": 0.82, "locations": ["Samsung Semiconductor"]},
    {"title": "Rare Earth Export Controls — China", "category": "GEOPOLITICAL", "severity": 0.78, "locations": ["CATL Battery", "Foxconn Shenzhen"]},
    {"title": "US West Coast Port Congestion", "category": "LOGISTICS", "severity": 0.65, "locations": ["Port of Los Angeles", "Port of Long Beach"]},
    {"title": "Strait of Malacca Piracy Alert", "category": "SECURITY", "severity": 0.55, "locations": ["Strait of Malacca", "Port of Singapore"]},
    {"title": "German Rail Strike — Cargo Delays", "category": "STRIKE", "severity": 0.50, "locations": ["Port of Hamburg", "DHL Leipzig Hub"]},
    {"title": "Taiwan Strait Military Exercises", "category": "GEOPOLITICAL", "severity": 0.90, "locations": ["TSMC", "Foxconn Materials"]},
    {"title": "Red Sea Houthi Shipping Attacks", "category": "SECURITY", "severity": 0.85, "locations": ["Suez Canal", "Jebel Ali Port"]},
    {"title": "India Monsoon Flooding — Mumbai Port", "category": "WEATHER", "severity": 0.70, "locations": ["Jawaharlal Nehru Port", "Wistron Bangalore"]},
    {"title": "Brazilian Port Workers Strike", "category": "STRIKE", "severity": 0.60, "locations": ["Port of Santos"]},
    {"title": "Earthquake Warning — Yokohama Region", "category": "NATURAL_DISASTER", "severity": 0.68, "locations": ["Port of Yokohama", "Toyota Motomachi Plant"]},
    {"title": "Panama Canal Drought Restrictions", "category": "WEATHER", "severity": 0.72, "locations": ["Panama Canal"]},
]

ROUTES = [
    # Raw materials → Suppliers
    ("SUP_BHP", "SUP_CATL", 12.0), ("SUP_BHP", "SUP_LG_ENERGY", 14.0),
    ("SUP_VALE", "SUP_BASF", 18.0), ("SUP_RIO_TINTO", "SUP_CATL", 15.0),
    ("SUP_RIO_TINTO", "SUP_PANASONIC_BAT", 10.0),
    # Suppliers → Factories
    ("SUP_TSMC", "FAC_FOXCONN_SZ", 3.0), ("SUP_TSMC", "FAC_FOXCONN_ZZ", 4.0),
    ("SUP_TSMC", "FAC_PEGATRON", 3.5), ("SUP_TSMC", "FAC_APPLE_CORK", 14.0),
    ("SUP_TSMC", "FAC_NVIDIA_TW", 1.0),
    ("SUP_SAMSUNG_SEMI", "FAC_SAMSUNG_VN", 5.0), ("SUP_SAMSUNG_SEMI", "FAC_FOXCONN_SZ", 6.0),
    ("SUP_SK_HYNIX", "FAC_SAMSUNG_VN", 4.0), ("SUP_SK_HYNIX", "FAC_FOXCONN_ZZ", 5.0),
    ("SUP_INTEL_CHANDLER", "FAC_APPLE_CORK", 12.0), ("SUP_INTEL_CHANDLER", "FAC_FOXCONN_SZ", 18.0),
    ("SUP_MICRON", "FAC_JABIL_PENANG", 14.0),
    ("SUP_CATL", "FAC_TESLA_SHANG", 2.0), ("SUP_CATL", "FAC_TESLA_BERLIN", 22.0),
    ("SUP_LG_ENERGY", "FAC_TESLA_AUSTIN", 18.0), ("SUP_LG_ENERGY", "FAC_HYUNDAI_ULSAN", 2.0),
    ("SUP_PANASONIC_BAT", "FAC_TESLA_SHANG", 7.0), ("SUP_PANASONIC_BAT", "FAC_TESLA_AUSTIN", 20.0),
    ("SUP_BOSCH_STUTT", "FAC_BMW_MUNICH", 1.5), ("SUP_BOSCH_STUTT", "FAC_VW_WOLFSBURG", 2.0),
    ("SUP_DENSO", "FAC_TOYOTA_AICHI", 1.0), ("SUP_DENSO", "FAC_HYUNDAI_ULSAN", 5.0),
    ("SUP_CONTINENTAL", "FAC_BMW_MUNICH", 2.5), ("SUP_CONTINENTAL", "FAC_VW_WOLFSBURG", 1.5),
    ("SUP_BASF", "FAC_BMW_MUNICH", 3.0), ("SUP_BASF", "FAC_TESLA_BERLIN", 2.0),
    ("SUP_DOW", "FAC_TESLA_AUSTIN", 3.0),
    ("SUP_CORNING", "FAC_FOXCONN_SZ", 16.0), ("SUP_CORNING", "FAC_SAMSUNG_VN", 18.0),
    ("SUP_MURATA", "FAC_FOXCONN_SZ", 5.0), ("SUP_MURATA", "FAC_PEGATRON", 4.0),
    ("SUP_TDK", "FAC_FOXCONN_ZZ", 5.5), ("SUP_TDK", "FAC_JABIL_PENANG", 6.0),
    ("SUP_FOXCONN_MAT", "FAC_FOXCONN_SZ", 3.0), ("SUP_FOXCONN_MAT", "FAC_FOXCONN_ZZ", 4.0),
    # Factories → Ports
    ("FAC_FOXCONN_SZ", "PORT_SHENZHEN", 0.5), ("FAC_FOXCONN_SZ", "PORT_HONG_KONG", 1.0),
    ("FAC_FOXCONN_ZZ", "PORT_SHANGHAI", 3.0),
    ("FAC_PEGATRON", "PORT_SHANGHAI", 0.5),
    ("FAC_FLEX_ZH", "PORT_SHENZHEN", 1.0),
    ("FAC_SAMSUNG_VN", "PORT_HONG_KONG", 4.0), ("FAC_SAMSUNG_VN", "PORT_SINGAPORE", 5.0),
    ("FAC_TESLA_SHANG", "PORT_SHANGHAI", 1.0),
    ("FAC_TESLA_BERLIN", "PORT_HAMBURG", 3.0),
    ("FAC_TESLA_AUSTIN", "PORT_LA", 5.0),
    ("FAC_TOYOTA_AICHI", "PORT_YOKOHAMA", 2.0),
    ("FAC_BMW_MUNICH", "PORT_HAMBURG", 4.0),
    ("FAC_VW_WOLFSBURG", "PORT_HAMBURG", 3.5),
    ("FAC_HYUNDAI_ULSAN", "PORT_BUSAN", 1.0),
    ("FAC_JABIL_PENANG", "PORT_TANJUNG", 1.5),
    ("FAC_WISTRON_BANG", "PORT_MUMBAI", 3.0),
    # Port-to-Port shipping lanes
    ("PORT_SHANGHAI", "PORT_LA", 14.0), ("PORT_SHANGHAI", "PORT_LONG_BEACH", 14.0),
    ("PORT_SHANGHAI", "PORT_SINGAPORE", 5.0), ("PORT_SHANGHAI", "PORT_BUSAN", 2.0),
    ("PORT_SHANGHAI", "PORT_ROTTERDAM", 28.0), ("PORT_SHANGHAI", "PORT_YOKOHAMA", 3.0),
    ("PORT_SHENZHEN", "PORT_SINGAPORE", 4.0), ("PORT_SHENZHEN", "PORT_LA", 15.0),
    ("PORT_SHENZHEN", "PORT_ROTTERDAM", 26.0),
    ("PORT_NINGBO", "PORT_LA", 13.0), ("PORT_NINGBO", "PORT_ROTTERDAM", 27.0),
    ("PORT_HONG_KONG", "PORT_SINGAPORE", 4.0), ("PORT_HONG_KONG", "PORT_LA", 16.0),
    ("PORT_HONG_KONG", "PORT_FELIXSTOWE", 26.0),
    ("PORT_SINGAPORE", "PORT_ROTTERDAM", 20.0), ("PORT_SINGAPORE", "PORT_DUBAI", 7.0),
    ("PORT_SINGAPORE", "PORT_MUMBAI", 6.0), ("PORT_SINGAPORE", "PORT_PIRAEUS", 16.0),
    ("PORT_BUSAN", "PORT_LA", 12.0), ("PORT_BUSAN", "PORT_LONG_BEACH", 12.0),
    ("PORT_BUSAN", "PORT_ROTTERDAM", 30.0),
    ("PORT_ROTTERDAM", "PORT_FELIXSTOWE", 1.0), ("PORT_ROTTERDAM", "PORT_HAMBURG", 1.5),
    ("PORT_ROTTERDAM", "PORT_ANTWERP", 0.5), ("PORT_ROTTERDAM", "PORT_SAVANNAH", 14.0),
    ("PORT_HAMBURG", "PORT_FELIXSTOWE", 2.0),
    ("PORT_ANTWERP", "PORT_FELIXSTOWE", 1.0), ("PORT_ANTWERP", "PORT_SAVANNAH", 15.0),
    ("PORT_LA", "PORT_LONG_BEACH", 0.2), ("PORT_LA", "PORT_SAVANNAH", 8.0),
    ("PORT_DUBAI", "PORT_MUMBAI", 3.0), ("PORT_DUBAI", "PORT_PIRAEUS", 9.0),
    ("PORT_DUBAI", "PORT_ROTTERDAM", 15.0),
    ("PORT_TANJUNG", "PORT_SINGAPORE", 0.5), ("PORT_TANJUNG", "PORT_ROTTERDAM", 21.0),
    ("PORT_LAEM_CHAB", "PORT_SINGAPORE", 3.0), ("PORT_LAEM_CHAB", "PORT_LA", 18.0),
    ("PORT_YOKOHAMA", "PORT_LA", 10.0), ("PORT_YOKOHAMA", "PORT_LONG_BEACH", 10.0),
    ("PORT_SANTOS", "PORT_ROTTERDAM", 16.0), ("PORT_SANTOS", "PORT_SAVANNAH", 12.0),
    ("PORT_PIRAEUS", "PORT_ROTTERDAM", 8.0), ("PORT_PIRAEUS", "PORT_HAMBURG", 9.0),
    # Strait/Canal chokepoints
    ("PORT_SINGAPORE", "LOC_STRAIT_MALACCA", 0.5),
    ("LOC_STRAIT_MALACCA", "PORT_MUMBAI", 5.0),
    ("LOC_STRAIT_MALACCA", "PORT_DUBAI", 7.0),
    ("PORT_DUBAI", "LOC_STRAIT_HORMUZ", 0.5),
    ("LOC_STRAIT_HORMUZ", "PORT_MUMBAI", 3.0),
    ("PORT_PIRAEUS", "LOC_SUEZ_CANAL", 2.0),
    ("LOC_SUEZ_CANAL", "PORT_DUBAI", 5.0),
    ("LOC_SUEZ_CANAL", "PORT_SINGAPORE", 12.0),
    ("PORT_ROTTERDAM", "LOC_SUEZ_CANAL", 8.0),
    ("PORT_SANTOS", "LOC_PANAMA_CANAL", 6.0),
    ("LOC_PANAMA_CANAL", "PORT_LA", 7.0),
    ("PORT_SAVANNAH", "LOC_PANAMA_CANAL", 5.0),
    # Ports → Warehouses & DCs
    ("PORT_LA", "WH_FEDEX_MEMPHIS", 4.0), ("PORT_LA", "DC_COSTCO_TRACY", 1.0),
    ("PORT_LONG_BEACH", "WH_AMAZON_KY", 5.0), ("PORT_LONG_BEACH", "WH_UPS_LOUISVILLE", 5.0),
    ("PORT_LONG_BEACH", "DC_WALMART_BENTON", 4.0),
    ("PORT_SAVANNAH", "WH_AMAZON_KY", 2.0), ("PORT_SAVANNAH", "WH_UPS_LOUISVILLE", 2.5),
    ("PORT_ROTTERDAM", "WH_MAERSK_ROTT", 0.5), ("PORT_ROTTERDAM", "WH_DHL_LEIP", 2.0),
    ("PORT_ROTTERDAM", "DC_NIKE_LAAKDAL", 1.0), ("PORT_ROTTERDAM", "DC_IKEA_ALMHULT", 3.0),
    ("PORT_HAMBURG", "WH_DHL_LEIP", 1.5), ("PORT_HAMBURG", "DC_BOSCH_BAMBERG", 2.0),
    ("PORT_ANTWERP", "DC_NIKE_LAAKDAL", 0.5), ("PORT_ANTWERP", "DC_ZARA_ARTEIJO", 4.0),
    ("PORT_FELIXSTOWE", "WH_AMAZON_UK", 1.5),
    ("PORT_SHANGHAI", "WH_COSCO_SHANG", 0.5), ("PORT_SHANGHAI", "DC_ALIBABA_HANGZ", 2.0),
    ("PORT_SHANGHAI", "DC_APPLE_SHENZ", 3.0),
    ("PORT_SHENZHEN", "DC_APPLE_SHENZ", 0.5),
    ("PORT_SINGAPORE", "WH_CEVA_SING", 0.5),
    ("PORT_BUSAN", "DC_SAMSUNG_SUWON", 2.0),
    ("PORT_YOKOHAMA", "DC_TOYOTA_NAGOYA", 1.5),
    ("PORT_MUMBAI", "FAC_WISTRON_BANG", 3.0),
    ("PORT_DUBAI", "WH_CMA_MARSEILLE", 8.0),
    # Warehouses → Distribution Centers
    ("WH_AMAZON_KY", "DC_WALMART_BENTON", 2.0),
    ("WH_FEDEX_MEMPHIS", "DC_WALMART_BENTON", 3.0),
    ("WH_UPS_LOUISVILLE", "DC_COSTCO_TRACY", 5.0),
    ("WH_DHL_LEIP", "DC_BOSCH_BAMBERG", 1.5),
    ("WH_DHL_LEIP", "DC_IKEA_ALMHULT", 3.0),
    ("WH_MAERSK_ROTT", "DC_NIKE_LAAKDAL", 1.0),
    ("WH_COSCO_SHANG", "DC_APPLE_SHENZ", 2.0),
    ("WH_COSCO_SHANG", "DC_ALIBABA_HANGZ", 1.5),
    ("WH_CEVA_SING", "FAC_JABIL_PENANG", 2.0),
    ("WH_DB_SCHENKER_MUC", "FAC_BMW_MUNICH", 0.5),
    ("WH_DB_SCHENKER_MUC", "DC_BOSCH_BAMBERG", 2.0),
]


def seed():
    client = Neo4jClient()
    print("🔗 Connected to Neo4j")

    # 1. Clear existing data
    print("🧹 Clearing existing graph data...")
    with client.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    # 2. Load schema
    print("📐 Loading schema constraints...")
    client.load_schema()

    # 3. Insert all nodes
    all_nodes = [
        ("Supplier", SUPPLIERS),
        ("Factory", FACTORIES),
        ("Port", PORTS),
        ("Warehouse", WAREHOUSES),
        ("DistributionCenter", DISTRIBUTION_CENTERS),
        ("Location", LOCATIONS),
    ]

    total_nodes = 0
    for label, nodes_list in all_nodes:
        for node in nodes_list:
            props = {k: v for k, v in node.items()}
            client.insert_node(label, props)
            total_nodes += 1
        print(f"  ✅ {len(nodes_list)} {label} nodes inserted")

    print(f"📊 Total nodes: {total_nodes}")

    # 4. Insert routes
    print("🔀 Inserting routes...")
    with client.driver.session() as session:
        for src, tgt, lead_time in ROUTES:
            session.run("""
                MATCH (a) WHERE a.id = $from_id
                MATCH (b) WHERE b.id = $to_id
                MERGE (a)-[r:ROUTES_TO]->(b)
                SET r.lead_time_days = $lead_time,
                    r.transport_mode = CASE 
                        WHEN $lead_time < 1 THEN 'truck'
                        WHEN $lead_time < 5 THEN 'rail_or_truck'
                        WHEN $lead_time < 10 THEN 'feeder_vessel'
                        ELSE 'ocean_vessel'
                    END,
                    r.reliability = $reliability
            """, from_id=src, to_id=tgt,
                lead_time=lead_time,
                reliability=round(random.uniform(0.75, 0.99), 2))
    print(f"  ✅ {len(ROUTES)} routes inserted")

    # 5. Insert events
    print("⚡ Inserting disruption events...")
    now = datetime.now()
    for event in EVENTS:
        event_data = {
            "id": str(uuid.uuid4()),
            "title": event["title"],
            "category": event["category"],
            "severity": event["severity"],
            "timestamp": (now - timedelta(hours=random.randint(1, 72))).isoformat(),
            "locations": event["locations"],
        }
        client.insert_event(event_data)
    print(f"  ✅ {len(EVENTS)} events inserted")

    # 6. Summary
    with client.driver.session() as session:
        node_count = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
        edge_count = session.run("MATCH ()-[r]->() RETURN count(r) as c").single()["c"]
        event_count = session.run("MATCH (e:Event) RETURN count(e) as c").single()["c"]

    print(f"""
╔══════════════════════════════════════════════════╗
║          ATLAS AI — Graph Seeded ✅              ║
╠══════════════════════════════════════════════════╣
║  Nodes:   {node_count:<6}                                ║
║  Routes:  {edge_count:<6}                                ║
║  Events:  {event_count:<6}                                ║
╚══════════════════════════════════════════════════╝
    """)

    client.close()


if __name__ == "__main__":
    seed()
