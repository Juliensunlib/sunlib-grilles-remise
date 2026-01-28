"""
Test script to send an invoice email using different methods
"""
import os
from src.sellsy_client_v2 import SellsyClient

def test_send_invoice_email(invoice_id: int):
    """Test sending invoice email using different methods"""

    sellsy = SellsyClient(
        client_id=os.environ['SELLSY_CLIENT_ID'],
        client_secret=os.environ['SELLSY_CLIENT_SECRET']
    )

    print(f"\n{'='*60}")
    print(f"Testing email sending for invoice ID: {invoice_id}")
    print(f"{'='*60}\n")

    # Method 1: Try direct email endpoint
    print("Method 1: Direct email endpoint")
    print("-" * 40)
    try:
        url = f"https://api.sellsy.com/v2/invoices/{invoice_id}/email"
        response = sellsy._make_request('POST', url, json={})
        print(f"✅ Success with direct endpoint!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

    print()

    # Method 2: Try with /send endpoint
    print("Method 2: /send endpoint")
    print("-" * 40)
    try:
        url = f"https://api.sellsy.com/v2/invoices/{invoice_id}/send"
        response = sellsy._make_request('POST', url, json={})
        print(f"✅ Success with /send endpoint!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

    print()

    # Method 3: Try with /actions/send
    print("Method 3: /actions/send endpoint")
    print("-" * 40)
    try:
        url = f"https://api.sellsy.com/v2/invoices/{invoice_id}/actions/send"
        response = sellsy._make_request('POST', url, json={})
        print(f"✅ Success with /actions/send endpoint!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

    print()

    # Method 4: Get invoice details to see available actions
    print("Method 4: Checking invoice details")
    print("-" * 40)
    try:
        invoice = sellsy.get_invoice_by_id(invoice_id)
        print(f"Invoice found: {invoice.get('reference')}")
        print(f"Status: {invoice.get('status')}")
        print(f"Contact email: {invoice.get('third', {}).get('email')}")

        # Try to find any email-related fields
        if 'actions' in invoice:
            print(f"Available actions: {invoice['actions']}")
        if 'links' in invoice:
            print(f"Available links: {invoice['links']}")

    except Exception as e:
        print(f"❌ Failed to get invoice: {str(e)}")

    print()

    # Method 5: Try PATCH with email flag
    print("Method 5: PATCH with send_email flag")
    print("-" * 40)
    try:
        url = f"https://api.sellsy.com/v2/invoices/{invoice_id}"
        response = sellsy._make_request('PATCH', url, json={'send_email': True})
        print(f"✅ Success with PATCH!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

    print(f"\n{'='*60}")
    print("Testing complete!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_send_invoice_email.py <invoice_id>")
        print("Example: python test_send_invoice_email.py 14889880")
        sys.exit(1)

    invoice_id = int(sys.argv[1])
    test_send_invoice_email(invoice_id)
