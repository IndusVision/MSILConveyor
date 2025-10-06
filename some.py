# import pandas as pd
# import random

# # Number of records
# NUM_RECORDS = 10000

# # Generate random order_number and clp_number
# records = []
# for _ in range(NUM_RECORDS):
#     order_number = random.randint(100000, 999999)  # 6-digit order number
#     clp_number = random.randint(100000, 999999)    # 6-digit clp number
#     records.append({
#         "order_number": order_number,
#         "clp_number": clp_number
#     })

# # Convert to DataFrame
# df = pd.DataFrame(records)

# # Save to CSV
# df.to_csv("generated_orders.csv", index=False)
# print("CSV file 'generated_orders.csv' created with 10,000 records.")


import requests

url = "http://localhost:8000/reports/compare/"
files = {"file": open("generated_orders.csv", "rb")}

response = requests.post(url, files=files)
print(response.json())
