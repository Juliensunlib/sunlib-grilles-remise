"""
Test script to send an invoice email using different methods
"""
import os
from src.sellsy_client_v2 import SellsyClientV2

def test_send_invoice_email(invoice_id: int):
    """Test sending invoice email using different methods"""

    sellsy = SellsyClientV2(
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
        response = sellsy._make_request('POST', f"/invoices/{invoice_id}/email", data={})
        print(f"✅ Success with direct endpoint!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

    print()

    # Method 2: Try with /send endpoint
    print("Method 2: /send endpoint")
    print("-" * 40)
    try:
        response = sellsy._make_request('POST', f"/invoices/{invoice_id}/send", data={})
        print(f"✅ Success with /send endpoint!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

    print()

    # Method 3: Try with /actions/send
    print("Method 3: /actions/send endpoint")
    print("-" * 40)
    try:
        response = sellsy._make_request('POST', f"/invoices/{invoice_id}/actions/send", data={})
        print(f"✅ Success with /actions/send endpoint!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")

    print()

    # Method 4: Get invoice details to see available actions
    print("Method 4: Checking invoice details")
    print("-" * 40)
    try:
        result = sellsy._make_request('GET', f"/invoices/{invoice_id}")
        invoice = result.get('data', {})
        print(f"Invoice found: {invoice.get('reference')}")
        print(f"Status: {invoice.get('status')}")

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
        response = sellsy._make_request('PATCH', f"/invoices/{invoice_id}", data={'send_email': True})
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
