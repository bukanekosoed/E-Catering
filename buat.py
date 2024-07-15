import requests

def get_midtrans_snap(order_id):
    snap_url = f"https://app.midtrans.com/snap/v1/transactions/{order_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic U0ItTWlkLXNlcnZlci16OEZTZkx6ZG5JX2E3aXFvVm9yQmlkY0o6TWFwaW5haDMxKys="
    }

    response = requests.get(snap_url, headers=headers)

    if response.status_code == 200:
        # Response JSON contains the Snap URL and other transaction details
        snap_response = response.json()
        return snap_response['redirect_url']  # This URL should be used to redirect user to Snap

    return None  # Handle error cases or invalid responses

# Usage example:
order_id = "LanggengCatering-030fc3c9-2024-07-08"
snap_url = get_midtrans_snap(order_id)

if snap_url:
    # Redirect user to the Snap Midtrans payment page
    print(f"Redirecting user to Midtrans payment page: {snap_url}")
    # In a web application, you would typically return a redirect response to this URL
else:
    print("Failed to retrieve Snap URL from Midtrans API")
