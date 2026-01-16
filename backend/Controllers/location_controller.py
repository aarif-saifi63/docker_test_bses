import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET
from flask import jsonify, request
import requests
from Controllers.api_key_master_controller import save_api_key_count
from Models.api_key_master_model import API_Key_Master


# GOOGLE_API_KEY = "AIzaSyDIgIhtp-mW25adeB_IHx-Du8CO7FdtT7w"
# MAX_WORKERS = 10

# def generate_google_maps_navigation_link(origin_lat, origin_lon, dest_lat, dest_lon, travel_mode="driving"):
#         return (
#             f"https://www.google.com/maps/dir/?api=1"
#             f"&origin={origin_lat},{origin_lon}"
#             f"&destination={dest_lat},{dest_lon}"
#             f"&travelmode={travel_mode}"
#         )


# def haversine(lat1, lon1, lat2, lon2):
#     """Calculate the great-circle distance between two points using the Haversine formula."""
#     R = 6371000  # Radius of Earth in meters
#     phi1 = math.radians(lat1)
#     phi2 = math.radians(lat2)
#     delta_phi = math.radians(lat2 - lat1)
#     delta_lambda = math.radians(lon2 - lon1)

#     a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

#     distance_meters = R * c
#     return round(distance_meters)

# def get_outlet_data():
#     data = request.json
#     latitude = data.get("latitude")
#     longitude = data.get("longitude")
#     filter_code = data.get("filter_code")

#     if not all([latitude, longitude, filter_code]):
#         return jsonify({"error": "Missing latitude, longitude, or filter_code"}), 400
    
#     record = API_Key_Master.find_one(api_name="BRPL Outlet Data")

#     # Extract values safely
#     outlet_headers = record.api_headers or {}
#     outlet_content_type = outlet_headers.get("Content-Type")
#     outlet_soap_action = outlet_headers.get("SOAPAction")

#     # SOAP_URL_OUTLET = "https://bsesbrpl.co.in:7860/GISServices/WebGISService.asmx"
#     # SOAP_ACTION_OUTLET = "http://tempuri.org/BRPL_Outlet"

#     SOAP_URL_OUTLET = record.api_url

#     SOAP_BODY_OUTLET = """<?xml version="1.0" encoding="utf-8"?>
#     <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
#                    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#     <soap:Body>
#         <BRPL_Outlet xmlns="http://tempuri.org/" />
#     </soap:Body>
#     </soap:Envelope>"""

#     # headers = {
#     #     "Content-Type": "text/xml",
#     #     "SOAPAction": SOAP_ACTION_OUTLET
#     # }

#     headers = {
#         "Content-Type": outlet_content_type,
#         "SOAPAction": outlet_soap_action
#     }

#     response = requests.post(SOAP_URL_OUTLET, data=SOAP_BODY_OUTLET, headers=headers)
#     response.raise_for_status()
#     response_text = response.text

#     save_api_key_count("Branches Nearby","BRPL Outlet Data", SOAP_BODY_OUTLET, response_text)

#     if response.status_code != 200:
#         return jsonify({"error": "Failed to fetch SOAP data"}), 500

#     namespaces = {
#         'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
#         'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1',
#         'msdata': 'urn:schemas-microsoft-com:xml-msdata'
#     }

#     root = ET.fromstring(response.content)
#     tables = root.findall(".//diffgr:diffgram/NewDataSet/Table", namespaces)

#     filtered_items = []

#     with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
#         futures = []

#         for table in tables:
#             facility = table.find("FACILITYCO")
#             if facility is not None and facility.text == filter_code:
#                 item = {child.tag: child.text for child in table}

#                 try:
#                     branch_lat = float(item["POINT_Y"])  # latitude
#                     branch_lon = float(item["POINT_X"])  # longitude

#                     future = executor.submit(
#                         get_distance_info, branch_lat, branch_lon,
#                         float(latitude), float(longitude), item
#                     )
#                     futures.append(future)

#                 except (ValueError, KeyError):
#                     continue

#         for future in as_completed(futures):
#             result = future.result()
#             if result:
#                 filtered_items.append(result)

#     # Sort by distance and take top 5
#     filtered_items.sort(key=lambda x: x["distance_meters"])
#     filtered_items = filtered_items[:5]

#     return jsonify({
#         "input_lon": longitude,
#         "input_lat": latitude,
#         "filter_code": filter_code,
#         "nearest_branches": filtered_items
#     })


# def get_distance_info(branch_lat, branch_lon, latitude, longitude, item):
#     """Compute distance using haversine formula and add navigation link."""
#     try:
#         distance_meters = haversine(latitude, longitude, branch_lat, branch_lon)
#         item["distance_meters"] = distance_meters
#         item["distance_km"] = f"{distance_meters / 1000:.2f} km"
#         item["navigation_link"] = generate_google_maps_navigation_link(
#             latitude, longitude, branch_lat, branch_lon
#         )
#         return item
#     except Exception as e:
#         print(f"Failed for: {branch_lat},{branch_lon} | Error: {e}")
#     return None
